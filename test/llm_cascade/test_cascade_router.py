"""
Tests for llm_cascade.cascade_router module.
Target coverage: >= 85%
"""

import pytest
from implement.llm_cascade.cascade_router import CascadeRouter
from implement.llm_cascade.confidence_scorer import ConfidenceScorer
from implement.llm_cascade.cost_tracker import CostTracker
from implement.llm_cascade.health_tracker import HealthTracker
from implement.llm_cascade.models import (
    CascadeConfig,
    CascadeResult,
    ModelConfig,
    ModelProvider,
    ProviderHealth,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def health_tracker():
    return HealthTracker(
        window_seconds=3600,
        rate_limit_cooldown_seconds=60.0,
        min_success_rate=0.8,
    )


@pytest.fixture
def cost_tracker():
    return CostTracker()


@pytest.fixture
def confidence_scorer():
    return ConfidenceScorer()


@pytest.fixture
def cascade_router(health_tracker, cost_tracker, confidence_scorer):
    return CascadeRouter(
        health_tracker=health_tracker,
        cost_tracker=cost_tracker,
        confidence_scorer=confidence_scorer,
    )


@pytest.fixture
def cascade_config():
    return CascadeConfig(
        chain=[
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-sonnet-4", priority=2),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=3),
        ],
        latency_budget_ms=10000,
        cost_cap_usd=0.50,
        confidence_threshold=0.7,
        timeout_per_call_ms=5000,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────

class TestCascadeRouterInit:
    """Tests for CascadeRouter initialization."""

    def test_default_initialization(self):
        router = CascadeRouter()
        assert router.health_tracker is not None
        assert router.cost_tracker is not None
        assert router.confidence_scorer is not None
        assert router.cascade_engine is not None

    def test_injected_dependencies(self, health_tracker, cost_tracker, confidence_scorer):
        router = CascadeRouter(
            health_tracker=health_tracker,
            cost_tracker=cost_tracker,
            confidence_scorer=confidence_scorer,
        )
        assert router.health_tracker is health_tracker
        assert router.cost_tracker is cost_tracker
        assert router.confidence_scorer is confidence_scorer

    def test_cascade_engine_wired(self, cascade_router):
        assert hasattr(cascade_router, "cascade_engine")
        assert cascade_router.cascade_engine is not None


# ─────────────────────────────────────────────────────────────────────────────
# route
# ─────────────────────────────────────────────────────────────────────────────

class TestRoute:
    """Tests for route method."""

    @pytest.mark.asyncio
    async def test_route_validates_config(self, cascade_router):
        config = CascadeConfig(chain=[])
        with pytest.raises(ValueError, match="empty"):
            await cascade_router.route("test prompt", config)

    @pytest.mark.asyncio
    async def test_route_returns_cascade_result(self, cascade_router, cascade_config):
        result = await cascade_router.route("test prompt", cascade_config)
        assert isinstance(result, CascadeResult)

    @pytest.mark.asyncio
    async def test_route_has_response_field(self, cascade_router, cascade_config):
        result = await cascade_router.route("test prompt", cascade_config)
        assert hasattr(result, "response")

    @pytest.mark.asyncio
    async def test_route_has_cascade_depth(self, cascade_router, cascade_config):
        result = await cascade_router.route("test prompt", cascade_config)
        assert hasattr(result, "cascade_depth")
        assert result.cascade_depth >= 0

    @pytest.mark.asyncio
    async def test_route_has_cost(self, cascade_router, cascade_config):
        result = await cascade_router.route("test prompt", cascade_config)
        assert hasattr(result, "total_cost_usd")

    @pytest.mark.asyncio
    async def test_route_has_attempt_history(self, cascade_router, cascade_config):
        result = await cascade_router.route("test prompt", cascade_config)
        assert hasattr(result, "attempt_history")
        assert isinstance(result.attempt_history, list)


# ─────────────────────────────────────────────────────────────────────────────
# select_model
# ─────────────────────────────────────────────────────────────────────────────

class TestSelectModel:
    """Tests for select_model method."""

    def test_select_model_returns_config(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
        ]
        health_map = {"anthropic": ProviderHealth(provider="anthropic", success_rate=1.0)}
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None
        assert selected.model_name == "claude-opus-4"

    def test_select_model_skips_unhealthy(self, cascade_router, health_tracker):
        """When primary is unhealthy, select_model should skip it.
        
        Note: select_model uses health_tracker.is_healthy(), not the health_map
        directly. So we must record failures in the health_tracker.
        """
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=2),
        ]
        # Record enough failures to make anthropic unhealthy (below 80% threshold)
        for _ in range(8):
            health_tracker.record_result("anthropic", latency_ms=500, success=False)
        for _ in range(2):
            health_tracker.record_result("anthropic", latency_ms=500, success=True)
        # openai is healthy (no failures recorded)
        
        health_map = {}
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None
        assert selected.model_name == "gpt-4o"  # Should skip unhealthy primary

    def test_select_model_skips_in_cooldown(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=2),
        ]
        from datetime import datetime, timedelta, timezone
        cooldown_health = ProviderHealth(
            provider="anthropic",
            success_rate=1.0,
            is_in_cooldown=True,
            cooldown_ends_at=datetime.now(timezone.utc) + timedelta(seconds=30),
        )
        health_map = {
            "anthropic": cooldown_health,
            "openai": ProviderHealth(provider="openai", success_rate=1.0),
        }
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None
        assert selected.model_name == "gpt-4o"

    def test_select_model_none_when_all_unhealthy(self, cascade_router, health_tracker):
        """When all providers in chain are unhealthy, select_model returns None.
        
        Note: is_healthy is called on health_tracker, so record failures.
        """
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
        ]
        # Record enough failures to make it unhealthy
        for _ in range(9):
            health_tracker.record_result("anthropic", latency_ms=500, success=False)
        for _ in range(1):
            health_tracker.record_result("anthropic", latency_ms=500, success=True)
        
        health_map = {}
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is None

    def test_select_model_unknown_provider_assumed_healthy(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
        ]
        health_map = {}  # No health data for "anthropic"
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None

    def test_select_model_respects_priority_order(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=2),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=1),
        ]
        health_map = {
            "anthropic": ProviderHealth(provider="anthropic", success_rate=1.0),
            "openai": ProviderHealth(provider="openai", success_rate=1.0),
        }
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None
        assert selected.priority == 1
        assert selected.model_name == "gpt-4o"

    def test_select_model_skips_high_latency(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=2),
        ]
        high_latency_health = ProviderHealth(provider="anthropic", success_rate=1.0, median_latency_ms=15000)
        low_latency_health = ProviderHealth(provider="openai", success_rate=1.0, median_latency_ms=500)
        health_map = {
            "anthropic": high_latency_health,
            "openai": low_latency_health,
        }
        selected = cascade_router.select_model(chain, health_map, 10000, 0.50)
        assert selected is not None
        assert selected.model_name == "gpt-4o"

    def test_select_model_skips_high_cost(self, cascade_router):
        chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o-mini", priority=2),
        ]
        health_map = {
            "anthropic": ProviderHealth(provider="anthropic", success_rate=1.0),
            "openai": ProviderHealth(provider="openai", success_rate=1.0),
        }
        selected = cascade_router.select_model(chain, health_map, 10000, 0.001)  # tiny budget
        assert selected is not None
        assert selected.model_name == "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────────────────────
# Health & Status
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthStatus:
    """Tests for health and status query methods."""

    def test_get_health(self, cascade_router):
        health = cascade_router.get_health("anthropic")
        assert isinstance(health, ProviderHealth)
        assert health.provider == "anthropic"

    def test_get_all_health(self, cascade_router):
        health_map = cascade_router.get_all_health()
        assert isinstance(health_map, dict)

    def test_is_healthy_unknown(self, cascade_router):
        assert cascade_router.is_healthy("totally_unknown") is True

    def test_is_healthy_known_healthy(self, cascade_router, health_tracker):
        health_tracker.record_result("anthropic", latency_ms=500, success=True)
        for _ in range(9):
            health_tracker.record_result("anthropic", latency_ms=500, success=True)
        assert cascade_router.is_healthy("anthropic") is True

    def test_is_healthy_unhealthy(self, cascade_router, health_tracker):
        for _ in range(3):
            health_tracker.record_result("anthropic", latency_ms=500, success=True)
        for _ in range(7):
            health_tracker.record_result("anthropic", latency_ms=500, success=False)
        assert cascade_router.is_healthy("anthropic") is False

    def test_get_cooldown_remaining_no_cooldown(self, cascade_router):
        remaining = cascade_router.get_cooldown_remaining("anthropic")
        assert remaining == 0.0

    def test_get_cooldown_remaining_with_cooldown(self, cascade_router, health_tracker):
        health_tracker.record_result("anthropic", latency_ms=100, success=False, is_rate_limit=True)
        remaining = cascade_router.get_cooldown_remaining("anthropic")
        assert remaining > 0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestEstimateModelCost:
    """Tests for _estimate_model_cost helper."""

    def test_returns_positive(self, cascade_router):
        model = ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")
        est = cascade_router._estimate_model_cost(model)
        assert est >= 0.0

    def test_returns_float(self, cascade_router):
        model = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o")
        est = cascade_router._estimate_model_cost(model)
        assert isinstance(est, float)

    def test_different_models_different_costs(self, cascade_router):
        model1 = ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")
        model2 = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o-mini")
        est1 = cascade_router._estimate_model_cost(model1)
        est2 = cascade_router._estimate_model_cost(model2)
        # gpt-4o-mini should be cheaper than claude-opus-4
        assert est2 < est1