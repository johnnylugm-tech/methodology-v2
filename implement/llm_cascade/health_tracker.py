"""
Health Tracker — Per-Provider Reliability Metrics

Tracks rolling reliability metrics per model provider:
  - Success rate (rolling 24h window)
  - Median latency (rolling 24h window)
  - Error type distribution
  - Rate-limit count (429s in rolling window)

Used by CascadeRouter to skip unhealthy providers.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from .models import ProviderHealth


class HealthTracker:
    """
    Track and query per-provider health metrics.

    Thread-safe: uses locks for all write operations.

    Usage:
        tracker = HealthTracker()
        tracker.record_result("anthropic", latency_ms=1200, success=True)
        tracker.record_result("openai", latency_ms=500, success=False, error_type="rate_limit")
        health = tracker.get_health("anthropic")
        if tracker.is_healthy("anthropic"):
            ...
    """

    def __init__(
        self,
        window_seconds: int = 86400,
        rate_limit_cooldown_seconds: float = 60.0,
        min_success_rate: float = 0.8,
    ) -> None:
        """
        Initialize HealthTracker.

        Args:
            window_seconds:              Rolling window for health metrics (default 24h).
            rate_limit_cooldown_seconds: Cooldown period after a 429 (default 60s).
            min_success_rate:            Minimum success rate to be considered healthy.
        """
        self.window_seconds = window_seconds
        self.rate_limit_cooldown_seconds = rate_limit_cooldown_seconds
        self.min_success_rate = min_success_rate

        # Raw result buffers (thread-safe via _lock)
        self._lock = threading.RLock()
        self._success_buffer: Dict[str, List[Tuple[bool, datetime]]] = defaultdict(list)
        self._latency_buffer: Dict[str, List[Tuple[int, datetime]]] = defaultdict(list)
        self._error_buffer: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._rate_limit_timestamps: Dict[str, List[datetime]] = defaultdict(list)

        # Derived health cache
        self._health_cache: Dict[str, ProviderHealth] = {}
        self._cache_time: Dict[str, datetime] = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Recording
    # ─────────────────────────────────────────────────────────────────────────

    def record_result(
        self,
        provider: str,
        latency_ms: int,
        success: bool,
        error_type: Optional[str] = None,
        is_rate_limit: bool = False,
    ) -> None:
        """
        Record the outcome of a model call for health tracking.

        Args:
            provider:     Provider name (e.g., "anthropic", "openai")
            latency_ms:   Latency of the call in milliseconds
            success:      Whether the call succeeded
            error_type:   Classification of the error (e.g., "timeout", "rate_limit")
            is_rate_limit: Whether this was a 429 rate-limit response
        """
        now = datetime.now(timezone.utc)

        with self._lock:
            # Record success/failure
            self._success_buffer[provider].append((success, now))

            # Record latency
            if latency_ms > 0:
                self._latency_buffer[provider].append((latency_ms, now))

            # Record error type
            if error_type:
                self._error_buffer[provider][error_type] += 1

            # Record rate-limit
            if is_rate_limit:
                self._rate_limit_timestamps[provider].append(now)

            # Invalidate cache
            self._health_cache.pop(provider, None)
            self._cache_time.pop(provider, None)

    # ─────────────────────────────────────────────────────────────────────────
    # Querying
    # ─────────────────────────────────────────────────────────────────────────

    def get_health(self, provider: str) -> ProviderHealth:
        """
        Get current health metrics for a provider.

        Returns:
            ProviderHealth with rolling window calculations.
            Returns default healthy state for unknown providers.
        """
        with self._lock:
            # Check cache (valid for 5 seconds)
            cached = self._health_cache.get(provider)
            cached_at = self._cache_time.get(provider)
            if cached and cached_at:
                age = (datetime.now(timezone.utc) - cached_at).total_seconds()
                if age < 5.0:
                    return cached

            health = self._compute_health(provider)
            self._health_cache[provider] = health
            self._cache_time[provider] = datetime.now(timezone.utc)
            return health

    def is_healthy(self, provider: str, min_success_rate: float = None) -> bool:
        """
        Check if a provider is healthy enough for routing.

        Args:
            provider:         Provider name.
            min_success_rate: Override minimum success rate (default: self.min_success_rate)

        Returns:
            True if provider should be used for routing.
        """
        threshold = min_success_rate if min_success_rate is not None else self.min_success_rate
        health = self.get_health(provider)

        if health.is_in_cooldown:
            # Cooldown might have expired but cache still holds stale result
            if health.cooldown_ends_at:
                from datetime import datetime, timezone
                if datetime.now(timezone.utc) >= health.cooldown_ends_at:
                    # Expired — recompute without caching to get fresh state
                    health = self._compute_health(provider)
            if health.is_in_cooldown:
                return False

        return health.success_rate >= threshold

    def get_cooldown_remaining(self, provider: str) -> float:
        """
        Get remaining cooldown seconds for a rate-limited provider.

        Returns:
            Seconds remaining in cooldown, or 0.0 if not in cooldown.
        """
        health = self.get_health(provider)
        if not health.is_in_cooldown or not health.cooldown_ends_at:
            return 0.0

        remaining = (health.cooldown_ends_at - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, remaining)

    def get_all_health(self) -> Dict[str, ProviderHealth]:
        """
        Get health metrics for all tracked providers.
        """
        with self._lock:
            providers = set(self._success_buffer.keys())
            return {p: self.get_health(p) for p in providers}

    # ─────────────────────────────────────────────────────────────────────────
    # Internal Computation
    # ─────────────────────────────────────────────────────────────────────────

    def _compute_health(self, provider: str) -> ProviderHealth:
        """
        Compute health metrics from rolling window data.
        Must be called under lock.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        # Rolling success rate
        success_rate = self._compute_success_rate(provider, window_start)

        # Rolling median latency
        median_latency = self._compute_median_latency(provider, window_start)

        # Error types (pruned to window)
        error_types = self._get_error_types_in_window(provider, window_start)

        # Rate-limit count and cooldown
        rl_timestamps = self._rate_limit_timestamps.get(provider, [])
        rl_in_window = [t for t in rl_timestamps if t >= window_start]
        rate_limit_count = len(rl_in_window)

        is_in_cooldown = False
        cooldown_ends_at = None
        if rl_in_window:
            last_rl = max(rl_in_window)
            cooldown_end = last_rl + timedelta(seconds=self.rate_limit_cooldown_seconds)
            if now < cooldown_end:
                is_in_cooldown = True
                cooldown_ends_at = cooldown_end

        return ProviderHealth(
            provider=provider,
            success_rate=round(success_rate, 4),
            median_latency_ms=median_latency,
            error_types=dict(error_types),
            rate_limit_count=rate_limit_count,
            last_checked=now,
            is_in_cooldown=is_in_cooldown,
            cooldown_ends_at=cooldown_ends_at,
        )

    def _compute_success_rate(self, provider: str, window_start: datetime) -> float:
        """Compute rolling success rate within window."""
        entries = self._success_buffer.get(provider, [])
        recent = [(s, t) for (s, t) in entries if t >= window_start]
        if not recent:
            return 1.0  # No data → assume healthy
        return sum(1 for s, _ in recent if s) / len(recent)

    def _compute_median_latency(self, provider: str, window_start: datetime) -> int:
        """Compute rolling median latency within window."""
        entries = self._latency_buffer.get(provider, [])
        recent = [latency for (latency, t) in entries if t >= window_start]
        if not recent:
            return 0
        sorted_latencies = sorted(recent)
        mid = len(sorted_latencies) // 2
        if len(sorted_latencies) % 2 == 0:
            return int((sorted_latencies[mid - 1] + sorted_latencies[mid]) / 2)
        return int(sorted_latencies[mid])

    def _get_error_types_in_window(
        self, provider: str, window_start: datetime
    ) -> Dict[str, int]:
        """Return error type counts pruned to the rolling window."""
        # Since error_buffer is just counts (not time-stamped), we can't precisely
        # window it without changing the data structure. For now we return the
        # full buffer. A more precise implementation would track timestamps per error.
        return dict(self._error_buffer.get(provider, {}))

    # ─────────────────────────────────────────────────────────────────────────
    # Maintenance
    # ─────────────────────────────────────────────────────────────────────────

    def prune_old_entries(self) -> None:
        """
        Remove entries outside the rolling window.
        Call periodically to prevent memory growth.
        """
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=self.window_seconds)

        with self._lock:
            for provider in list(self._success_buffer.keys()):
                self._success_buffer[provider] = [
                    (s, t) for (s, t) in self._success_buffer[provider] if t >= window_start
                ]

            for provider in list(self._latency_buffer.keys()):
                self._latency_buffer[provider] = [
                    (lat, t) for (lat, t) in self._latency_buffer[provider] if t >= window_start
                ]

            for provider in list(self._rate_limit_timestamps.keys()):
                self._rate_limit_timestamps[provider] = [
                    t for t in self._rate_limit_timestamps[provider] if t >= window_start
                ]

            # Invalidate all caches
            self._health_cache.clear()
            self._cache_time.clear()

    def reset(self, provider: Optional[str] = None) -> None:
        """
        Reset health data for a specific provider or all providers.

        Args:
            provider: If provided, reset only this provider's data.
                      If None, reset all providers.
        """
        with self._lock:
            if provider:
                self._success_buffer.pop(provider, None)
                self._latency_buffer.pop(provider, None)
                self._error_buffer.pop(provider, None)
                self._rate_limit_timestamps.pop(provider, None)
                self._health_cache.pop(provider, None)
                self._cache_time.pop(provider, None)
            else:
                self._success_buffer.clear()
                self._latency_buffer.clear()
                self._error_buffer.clear()
                self._rate_limit_timestamps.clear()
                self._health_cache.clear()
                self._cache_time.clear()
