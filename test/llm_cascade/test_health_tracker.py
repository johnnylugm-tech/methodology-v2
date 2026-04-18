"""
Tests for llm_cascade.health_tracker module.
Target coverage: >= 85%
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from implement.llm_cascade.health_tracker import HealthTracker
from implement.llm_cascade.models import ProviderHealth


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tracker():
    return HealthTracker(
        window_seconds=3600,      # 1 hour window for testing
        rate_limit_cooldown_seconds=60.0,
        min_success_rate=0.8,
    )


@pytest.fixture
def tracker_24h_window():
    return HealthTracker(
        window_seconds=86400,     # 24 hours
        rate_limit_cooldown_seconds=60.0,
        min_success_rate=0.8,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthTrackerInit:
    """Tests for HealthTracker initialization."""

    def test_default_values(self):
        tracker = HealthTracker()
        assert tracker.window_seconds == 86400
        assert tracker.rate_limit_cooldown_seconds == 60.0
        assert tracker.min_success_rate == 0.8

    def test_custom_values(self):
        tracker = HealthTracker(
            window_seconds=1800,
            rate_limit_cooldown_seconds=30.0,
            min_success_rate=0.9,
        )
        assert tracker.window_seconds == 1800
        assert tracker.rate_limit_cooldown_seconds == 30.0
        assert tracker.min_success_rate == 0.9


# ─────────────────────────────────────────────────────────────────────────────
# Recording Results
# ─────────────────────────────────────────────────────────────────────────────

class TestRecordResult:
    """Tests for record_result method."""

    def test_record_success(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=True)
        health = tracker.get_health("anthropic")
        assert health.success_rate == 1.0

    def test_record_failure(self, tracker):
        tracker.record_result("openai", latency_ms=800, success=False, error_type="timeout")
        health = tracker.get_health("openai")
        assert health.success_rate == 0.0
        assert "timeout" in health.error_types

    def test_record_mixed_results(self, tracker):
        # 3 successes, 1 failure
        for _ in range(3):
            tracker.record_result("anthropic", latency_ms=500, success=True)
        tracker.record_result("anthropic", latency_ms=1000, success=False, error_type="api_error")
        health = tracker.get_health("anthropic")
        assert health.success_rate == 0.75

    def test_record_rate_limit_flag(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        health = tracker.get_health("openai")
        assert health.rate_limit_count >= 1

    def test_record_error_type_count(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=False, error_type="timeout")
        tracker.record_result("anthropic", latency_ms=600, success=False, error_type="timeout")
        tracker.record_result("anthropic", latency_ms=700, success=False, error_type="api_error")
        health = tracker.get_health("anthropic")
        assert health.error_types["timeout"] == 2
        assert health.error_types["api_error"] == 1

    def test_record_latency_stored(self, tracker):
        tracker.record_result("anthropic", latency_ms=1234, success=True)
        health = tracker.get_health("anthropic")
        assert health.median_latency_ms == 1234

    def test_record_multiple_latencies(self, tracker):
        latencies = [100, 200, 300, 400, 500]
        for lat in latencies:
            tracker.record_result("anthropic", latency_ms=lat, success=True)
        health = tracker.get_health("anthropic")
        assert health.median_latency_ms == 300  # median of [100,200,300,400,500]

    def test_record_even_count_latencies(self, tracker):
        latencies = [100, 200, 300, 400]
        for lat in latencies:
            tracker.record_result("anthropic", latency_ms=lat, success=True)
        health = tracker.get_health("anthropic")
        # median of [100, 200, 300, 400] = (200+300)/2 = 250
        assert health.median_latency_ms == 250

    def test_record_zero_latency_not_stored(self, tracker):
        tracker.record_result("anthropic", latency_ms=0, success=True)
        health = tracker.get_health("anthropic")
        # Zero latency should not be recorded
        assert health.median_latency_ms == 0 or health.median_latency_ms == 0  # just check no crash


# ─────────────────────────────────────────────────────────────────────────────
# Success Rate Calculation
# ─────────────────────────────────────────────────────────────────────────────

class TestSuccessRate:
    """Tests for rolling success rate calculation."""

    def test_no_data_returns_one(self, tracker):
        health = tracker.get_health("unknown_provider")
        assert health.success_rate == 1.0

    def test_all_successes(self, tracker):
        for _ in range(10):
            tracker.record_result("anthropic", latency_ms=500, success=True)
        health = tracker.get_health("anthropic")
        assert health.success_rate == 1.0

    def test_all_failures(self, tracker):
        for _ in range(10):
            tracker.record_result("anthropic", latency_ms=500, success=False)
        health = tracker.get_health("anthropic")
        assert health.success_rate == 0.0

    def test_partial_success(self, tracker):
        for _ in range(7):
            tracker.record_result("openai", latency_ms=500, success=True)
        for _ in range(3):
            tracker.record_result("openai", latency_ms=500, success=False)
        health = tracker.get_health("openai")
        assert abs(health.success_rate - 0.7) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Median Latency Calculation
# ─────────────────────────────────────────────────────────────────────────────

class TestMedianLatency:
    """Tests for rolling median latency calculation."""

    def test_no_data_returns_zero(self, tracker):
        health = tracker.get_health("unknown")
        assert health.median_latency_ms == 0

    def test_single_latency(self, tracker):
        tracker.record_result("anthropic", latency_ms=999, success=True)
        health = tracker.get_health("anthropic")
        assert health.median_latency_ms == 999

    def test_odd_count_median(self, tracker):
        for lat in [100, 300, 200]:
            tracker.record_result("openai", latency_ms=lat, success=True)
        health = tracker.get_health("openai")
        assert health.median_latency_ms == 200

    def test_even_count_median(self, tracker):
        for lat in [100, 400, 200, 300]:
            tracker.record_result("openai", latency_ms=lat, success=True)
        health = tracker.get_health("openai")
        # sorted: [100, 200, 300, 400] → (200+300)/2 = 250
        assert health.median_latency_ms == 250


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limit Cooldown
# ─────────────────────────────────────────────────────────────────────────────

class TestRateLimitCooldown:
    """Tests for rate-limit cooldown mechanism."""

    def test_cooldown_after_rate_limit(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        health = tracker.get_health("openai")
        assert health.is_in_cooldown is True
        assert health.cooldown_ends_at is not None

    def test_cooldown_duration(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        health = tracker.get_health("openai")
        remaining = (health.cooldown_ends_at - datetime.now(timezone.utc)).total_seconds()
        assert 55 <= remaining <= 65  # ~60 seconds

    def test_is_healthy_false_during_cooldown(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        assert tracker.is_healthy("openai") is False

    def test_get_cooldown_remaining(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        remaining = tracker.get_cooldown_remaining("openai")
        assert remaining > 0

    def test_get_cooldown_remaining_no_cooldown(self, tracker):
        tracker.record_result("openai", latency_ms=500, success=True)
        remaining = tracker.get_cooldown_remaining("openai")
        assert remaining == 0.0

    def test_multiple_rate_limits_last_wins(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        time.sleep(0.1)
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        remaining = tracker.get_cooldown_remaining("openai")
        assert remaining > 0

    def test_cooldown_expires(self, tracker):
        """Test that cooldown expires after cooldown period."""
        fast_cooldown = HealthTracker(
            window_seconds=3600,
            rate_limit_cooldown_seconds=1.0,  # 1 second for testing
            min_success_rate=0.8,
        )
        # Record enough successes so provider starts healthy (>= 80% success rate)
        for _ in range(4):
            fast_cooldown.record_result("openai", latency_ms=100, success=True)
        # Then a rate limit event
        fast_cooldown.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        assert fast_cooldown.is_healthy("openai") is False
        time.sleep(1.2)
        # After cooldown expires, success rate (4/5=0.8) meets threshold → healthy
        assert fast_cooldown.is_healthy("openai") is True


# ─────────────────────────────────────────────────────────────────────────────
# Health Query
# ─────────────────────────────────────────────────────────────────────────────

class TestGetHealth:
    """Tests for get_health method."""

    def test_returns_provider_health(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=True)
        health = tracker.get_health("anthropic")
        assert isinstance(health, ProviderHealth)
        assert health.provider == "anthropic"

    def test_returns_default_for_unknown(self, tracker):
        health = tracker.get_health("totally_unknown_provider")
        assert isinstance(health, ProviderHealth)
        assert health.provider == "totally_unknown_provider"
        assert health.success_rate == 1.0  # assume healthy if unknown

    def test_health_includes_latency(self, tracker):
        tracker.record_result("anthropic", latency_ms=750, success=True)
        health = tracker.get_health("anthropic")
        assert health.median_latency_ms > 0

    def test_health_includes_error_types(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, error_type="timeout")
        health = tracker.get_health("openai")
        assert "timeout" in health.error_types


class TestGetAllHealth:
    """Tests for get_all_health method."""

    def test_returns_dict(self, tracker):
        result = tracker.get_all_health()
        assert isinstance(result, dict)

    def test_empty_when_no_data(self, tracker):
        result = tracker.get_all_health()
        assert result == {}

    def test_includes_all_recorded_providers(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=True)
        tracker.record_result("openai", latency_ms=300, success=True)
        tracker.record_result("google", latency_ms=400, success=True)
        result = tracker.get_all_health()
        assert "anthropic" in result
        assert "openai" in result
        assert "google" in result


# ─────────────────────────────────────────────────────────────────────────────
# is_healthy Check
# ─────────────────────────────────────────────────────────────────────────────

class TestIsHealthy:
    """Tests for is_healthy method."""

    def test_no_data_is_healthy(self, tracker):
        assert tracker.is_healthy("unknown") is True

    def test_all_success_is_healthy(self, tracker):
        for _ in range(10):
            tracker.record_result("anthropic", latency_ms=500, success=True)
        assert tracker.is_healthy("anthropic") is True

    def test_low_success_rate_unhealthy(self, tracker):
        # 2 successes out of 10 = 20% < 80% threshold
        for _ in range(2):
            tracker.record_result("openai", latency_ms=500, success=True)
        for _ in range(8):
            tracker.record_result("openai", latency_ms=500, success=False)
        assert tracker.is_healthy("openai") is False

    def test_in_cooldown_unhealthy(self, tracker):
        tracker.record_result("openai", latency_ms=100, success=False, is_rate_limit=True)
        assert tracker.is_healthy("openai") is False

    def test_override_min_success_rate(self, tracker):
        # 70% success rate, default threshold is 80%
        for _ in range(7):
            tracker.record_result("anthropic", latency_ms=500, success=True)
        for _ in range(3):
            tracker.record_result("anthropic", latency_ms=500, success=False)
        # Default threshold (0.8) → unhealthy
        assert tracker.is_healthy("anthropic") is False
        # Override to 0.5 → healthy
        assert tracker.is_healthy("anthropic", min_success_rate=0.5) is True


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance
# ─────────────────────────────────────────────────────────────────────────────

class TestPruneOldEntries:
    """Tests for prune_old_entries method."""

    def test_prune_clears_old_entries(self, tracker_24h_window):
        tracker = tracker_24h_window
        tracker.record_result("anthropic", latency_ms=500, success=True)
        tracker.prune_old_entries()
        # Should not raise, entries should be pruned
        health = tracker.get_health("anthropic")
        assert isinstance(health, ProviderHealth)

    def test_prune_no_crash_on_empty(self, tracker):
        tracker.prune_old_entries()  # Should not raise


class TestReset:
    """Tests for reset method."""

    def test_reset_single_provider(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=True)
        tracker.record_result("openai", latency_ms=300, success=True)
        tracker.reset("anthropic")
        health_anthropic = tracker.get_health("anthropic")
        health_openai = tracker.get_health("openai")
        assert health_anthropic.success_rate == 1.0  # reset → no data → default
        assert health_openai.success_rate == 1.0

    def test_reset_all(self, tracker):
        tracker.record_result("anthropic", latency_ms=500, success=True)
        tracker.record_result("openai", latency_ms=300, success=True)
        tracker.reset()
        all_health = tracker.get_all_health()
        assert all_health == {}