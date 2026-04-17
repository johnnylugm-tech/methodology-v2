"""
LLM Cascade API — Main Facade

Unified interface for multi-model routing with automatic fallback.
Provides route(), health inspection, stats, and config management.

See ARCHITECTURE.md Section 6 for full API specification.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .cascade_engine import CascadeEngine
from .cascade_router import CascadeRouter
from .confidence_scorer import ConfidenceScorer
from .cost_tracker import CostTracker
from .enums import CascadeStateEnum
from .health_tracker import HealthTracker
from .models import (
    AttemptCost,
    CascadeConfig,
    CascadeResult,
    CascadeStats,
    LLMCascadeConfig,
    ModelConfig,
    ProviderHealth,
    ModelCallResult,
)


class LLMCascade:
    """
    Main LLM Cascade facade.

    Provides a unified interface for multi-model routing with automatic fallback.
    The cascade chain is tried in priority order until a successful, high-confidence
    response is obtained, or all models are exhausted.

    Usage:
        # Basic usage
        cascade = LLMCascade()
        result = await cascade.route("Hello, world")

        # With custom config
        config = CascadeConfig(chain=ModelConfig.default_chain())
        result = await cascade.route("Explain quantum computing", config=config)

        # With task-specific chain override
        result = await cascade.route_with_fallback(
            prompt, task_type="code",
            fallback_chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")]
        )

        # Health inspection
        health = cascade.get_provider_health("anthropic")
        stats = cascade.get_cascade_stats()
    """

    def __init__(
        self,
        config: Optional[CascadeConfig] = None,
        health_tracker: Optional[HealthTracker] = None,
        cost_tracker: Optional[CostTracker] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
        cascade_config: Optional[LLMCascadeConfig] = None,
    ) -> None:
        """
        Initialize LLMCascade.

        Args:
            config:           CascadeConfig for routing (default chain if None).
            health_tracker:   HealthTracker instance (created if None).
            cost_tracker:     CostTracker instance (created if None).
            confidence_scorer: ConfidenceScorer instance (created if None).
            cascade_config:   Global LLMCascadeConfig (for defaults and settings).
        """
        # Default config from default chain
        self.config = config or CascadeConfig(chain=ModelConfig.default_chain())

        # Components
        self.health_tracker = health_tracker or HealthTracker()
        self.cost_tracker = cost_tracker or CostTracker()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.cascade_engine = CascadeEngine(
            health_tracker=self.health_tracker,
            cost_tracker=self.cost_tracker,
            confidence_scorer=self.confidence_scorer,
        )
        self.router = CascadeRouter(
            health_tracker=self.health_tracker,
            cost_tracker=self.cost_tracker,
            confidence_scorer=self.confidence_scorer,
        )

        # Global config
        self.cascade_config = cascade_config or LLMCascadeConfig(
            default_chain=ModelConfig.default_chain()
        )

        # Aggregate stats (in-memory, reset on restart)
        self._stats = CascadeStats()

        # Last result (for debugging / inspection)
        self._last_result: Optional[CascadeResult] = None

    # ─────────────────────────────────────────────────────────────────────────
    # Core Routing
    # ─────────────────────────────────────────────────────────────────────────

    async def route(
        self,
        prompt: str,
        config: Optional[CascadeConfig] = None,
    ) -> CascadeResult:
        """
        Route a prompt through the cascade chain.

        Args:
            prompt: The input prompt to route.
            config:  Optional CascadeConfig override. Uses self.config if None.

        Returns:
            CascadeResult — a successful response or an exhausted result.
            Check result.success to determine outcome.
        """
        effective_config = config or self.config
        result = await self.router.route(prompt, effective_config)
        self._last_result = result
        self._update_stats(result)
        return result

    async def route_with_fallback(
        self,
        prompt: str,
        task_type: str,
        fallback_chain: Optional[List[ModelConfig]] = None,
    ) -> CascadeResult:
        """
        Convenience method: route with a task-type-specific chain override.

        Args:
            prompt:         The input prompt.
            task_type:      Task type hint ("general", "code", "json", etc.).
                            Passed to ConfidenceScorer for quality assessment.
            fallback_chain: Override chain for this request. If None, uses default.
        """
        if fallback_chain:
            config = CascadeConfig(chain=fallback_chain)
        else:
            config = self.config
        return await self.route(prompt, config=config)

    # ─────────────────────────────────────────────────────────────────────────
    # Health & Metrics
    # ─────────────────────────────────────────────────────────────────────────

    def get_provider_health(self, provider: str) -> ProviderHealth:
        """
        Get health metrics for a provider.

        Args:
            provider: Provider name (e.g., "anthropic", "openai").

        Returns:
            ProviderHealth with rolling metrics.
        """
        return self.health_tracker.get_health(provider)

    def get_all_provider_health(self) -> Dict[str, ProviderHealth]:
        """
        Get health metrics for all providers.

        Returns:
            Dict mapping provider name → ProviderHealth.
        """
        return self.health_tracker.get_all_health()

    def is_provider_healthy(self, provider: str) -> bool:
        """Check if a provider is currently healthy enough for routing."""
        return self.health_tracker.is_healthy(provider)

    def get_cascade_stats(self) -> CascadeStats:
        """
        Get aggregate cascade statistics.

        Returns:
            CascadeStats with session-level metrics.
        """
        return self._stats

    def get_last_result(self) -> Optional[CascadeResult]:
        """
        Get the result of the last cascade request (for debugging).
        """
        return self._last_result

    # ─────────────────────────────────────────────────────────────────────────
    # Configuration
    # ─────────────────────────────────────────────────────────────────────────

    def update_config(self, config: CascadeConfig) -> None:
        """
        Update the active cascade configuration.

        Args:
            config: New CascadeConfig. Validation runs immediately.
        """
        config.validate()
        self.config = config

    def get_config(self) -> CascadeConfig:
        """Get the current cascade configuration."""
        return self.config

    def add_model_to_chain(
        self,
        model: ModelConfig,
        position: Optional[int] = None,
    ) -> None:
        """
        Add a model to the cascade chain.

        Args:
            model:    ModelConfig to add.
            position: Index to insert at. If None, appends at end (lowest priority).
        """
        chain = list(self.config.chain)
        if position is None:
            chain.append(model)
        else:
            chain.insert(position, model)
        # Re-assign priorities
        for i, m in enumerate(chain):
            m.priority = i + 1
        self.config = CascadeConfig(
            chain=chain,
            latency_budget_ms=self.config.latency_budget_ms,
            cost_cap_usd=self.config.cost_cap_usd,
            confidence_threshold=self.config.confidence_threshold,
            timeout_per_call_ms=self.config.timeout_per_call_ms,
            rate_limit_cooldown_seconds=self.config.rate_limit_cooldown_seconds,
        )

    def remove_model_from_chain(self, model_name: str) -> bool:
        """
        Remove a model from the cascade chain by name.

        Args:
            model_name: Name of the model to remove.

        Returns:
            True if removed, False if not found.
        """
        chain = [m for m in self.config.chain if m.model_name != model_name]
        if len(chain) == len(self.config.chain):
            return False
        if not chain:
            raise ValueError("cannot remove last model from chain")
        # Re-assign priorities
        for i, m in enumerate(chain):
            m.priority = i + 1
        self.config = CascadeConfig(
            chain=chain,
            latency_budget_ms=self.config.latency_budget_ms,
            cost_cap_usd=self.config.cost_cap_usd,
            confidence_threshold=self.config.confidence_threshold,
            timeout_per_call_ms=self.config.timeout_per_call_ms,
            rate_limit_cooldown_seconds=self.config.rate_limit_cooldown_seconds,
        )
        return True

    # ─────────────────────────────────────────────────────────────────────────
    # Cost Management
    # ─────────────────────────────────────────────────────────────────────────

    def get_request_cost(self) -> float:
        """
        Get total cost for the last cascade request.

        Returns:
            Cost in USD.
        """
        if self._last_result:
            return self._last_result.total_cost_usd
        return self.cost_tracker.get_total_cost()

    def get_cost_breakdown(self) -> List[AttemptCost]:
        """
        Get per-attempt cost breakdown for the last request.
        """
        return self.cost_tracker.get_cost_breakdown()

    def reset_cost_tracking(self) -> None:
        """Reset cost tracking counters (session total only)."""
        self.cost_tracker.reset_session()

    # ─────────────────────────────────────────────────────────────────────────
    # Stats Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _update_stats(self, result: CascadeResult) -> None:
        """
        Update aggregate stats after a cascade result.
        """
        stats = self._stats
        stats.total_requests += 1

        if result.success:
            stats.successful_requests += 1

        if result.cascade_hit:
            stats.cascade_hit_count += 1

        # Average cascade depth
        total_depth = (
            stats.average_cascade_depth * (stats.total_requests - 1)
            + result.cascade_depth
        )
        stats.average_cascade_depth = total_depth / stats.total_requests

        # Average latency
        total_latency = (
            stats.average_latency_ms * (stats.total_requests - 1)
            + result.latency_ms
        )
        stats.average_latency_ms = int(total_latency / stats.total_requests)

        # Average cost
        total_cost = (
            stats.average_cost_usd * (stats.total_requests - 1)
            + result.total_cost_usd
        )
        stats.average_cost_usd = total_cost / stats.total_requests
        stats.total_cost_usd += result.total_cost_usd

        # Cascade hit rate
        stats.cascade_hit_rate = (
            stats.cascade_hit_count / stats.total_requests
            if stats.total_requests > 0 else 0.0
        )

        # Provider usage
        for record in result.attempt_history:
            stats.provider_usage[record.model_name] = (
                stats.provider_usage.get(record.model_name, 0) + 1
            )
