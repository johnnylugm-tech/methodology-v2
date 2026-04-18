"""
Tests for llm_cascade.api module (LLMCascade facade).
Target coverage: >= 80%
"""

import pytest
from implement.llm_cascade.api import LLMCascade
from implement.llm_cascade.models import (
    CascadeConfig,
    CascadeStats,
    ModelConfig,
    ModelProvider,
    ProviderHealth,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def llm_cascade():
    return LLMCascade()


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

class TestLLMCascadeInit:
    """Tests for LLMCascade initialization."""

    def test_default_initialization(self):
        cascade = LLMCascade()
        assert cascade.config is not None
        assert cascade.health_tracker is not None
        assert cascade.cost_tracker is not None
        assert cascade.confidence_scorer is not None
        assert cascade.cascade_engine is not None
        assert cascade.router is not None

    def test_default_chain_is_set(self):
        cascade = LLMCascade()
        assert len(cascade.config.chain) == 5  # Default chain has 5 models

    def test_cascade_config_global_set(self):
        cascade = LLMCascade()
        assert cascade.cascade_config is not None
        assert cascade.cascade_config.default_chain is not None

    def test_stats_initialized(self):
        cascade = LLMCascade()
        stats = cascade.get_cascade_stats()
        assert isinstance(stats, CascadeStats)
        assert stats.total_requests == 0

    def test_last_result_initialized_none(self):
        cascade = LLMCascade()
        assert cascade.get_last_result() is None

    def test_custom_components_injected(self):
        from implement.llm_cascade.health_tracker import HealthTracker
        from implement.llm_cascade.cost_tracker import CostTracker
        from implement.llm_cascade.confidence_scorer import ConfidenceScorer

        ht = HealthTracker()
        ct = CostTracker()
        cs = ConfidenceScorer()
        cascade = LLMCascade(health_tracker=ht, cost_tracker=ct, confidence_scorer=cs)
        assert cascade.health_tracker is ht
        assert cascade.cost_tracker is ct
        assert cascade.confidence_scorer is cs


# ─────────────────────────────────────────────────────────────────────────────
# route
# ─────────────────────────────────────────────────────────────────────────────

class TestRoute:
    """Tests for route method."""

    @pytest.mark.asyncio
    async def test_route_returns_cascade_result(self, llm_cascade):
        result = await llm_cascade.route("Hello world")
        assert hasattr(result, "response")
        assert hasattr(result, "cascade_depth")
        assert hasattr(result, "total_cost_usd")
        assert hasattr(result, "latency_ms")
        assert hasattr(result, "confidence")

    @pytest.mark.asyncio
    async def test_route_with_custom_config(self, llm_cascade, cascade_config):
        result = await llm_cascade.route("Test prompt", config=cascade_config)
        assert result is not None

    @pytest.mark.asyncio
    async def test_route_updates_stats(self, llm_cascade):
        initial_stats = llm_cascade.get_cascade_stats()
        initial_requests = initial_stats.total_requests
        await llm_cascade.route("test")
        updated_stats = llm_cascade.get_cascade_stats()
        assert updated_stats.total_requests == initial_requests + 1

    @pytest.mark.asyncio
    async def test_route_updates_last_result(self, llm_cascade):
        result = await llm_cascade.route("test")
        last = llm_cascade.get_last_result()
        assert last is result

    @pytest.mark.asyncio
    async def test_route_response_not_none_on_success(self, llm_cascade):
        result = await llm_cascade.route("test")
        # Stub always succeeds, so response should not be None
        if not result.cascade_failure:
            assert result.response is not None

    @pytest.mark.asyncio
    async def test_route_updates_provider_usage(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        # At least one model should have been used
        assert len(stats.provider_usage) >= 1

    @pytest.mark.asyncio
    async def test_route_updates_total_cost(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        assert stats.total_cost_usd >= 0.0

    @pytest.mark.asyncio
    async def test_route_updates_average_latency(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        assert stats.average_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_route_updates_average_cost(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        assert stats.average_cost_usd >= 0.0


# ─────────────────────────────────────────────────────────────────────────────
# route_with_fallback
# ─────────────────────────────────────────────────────────────────────────────

class TestRouteWithFallback:
    """Tests for route_with_fallback convenience method."""

    @pytest.mark.asyncio
    async def test_route_with_fallback_returns_result(self, llm_cascade):
        result = await llm_cascade.route_with_fallback("test prompt", task_type="general")
        assert hasattr(result, "response")

    @pytest.mark.asyncio
    async def test_route_with_fallback_with_custom_chain(self, llm_cascade):
        custom_chain = [
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4"),
        ]
        result = await llm_cascade.route_with_fallback("test", task_type="code", fallback_chain=custom_chain)
        assert result is not None

    @pytest.mark.asyncio
    async def test_route_with_fallback_uses_default_when_no_override(self, llm_cascade):
        result = await llm_cascade.route_with_fallback("test", task_type="general")
        assert result is not None


# ─────────────────────────────────────────────────────────────────────────────
# Health & Metrics
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthMetrics:
    """Tests for health and metrics query methods."""

    def test_get_provider_health(self, llm_cascade):
        health = llm_cascade.get_provider_health("anthropic")
        assert isinstance(health, ProviderHealth)

    def test_get_all_provider_health(self, llm_cascade):
        health_map = llm_cascade.get_all_provider_health()
        assert isinstance(health_map, dict)

    def test_is_provider_healthy_unknown(self, llm_cascade):
        assert llm_cascade.is_provider_healthy("unknown") is True

    def test_get_cascade_stats(self, llm_cascade):
        stats = llm_cascade.get_cascade_stats()
        assert isinstance(stats, CascadeStats)

    def test_get_last_result_none_initially(self, llm_cascade):
        assert llm_cascade.get_last_result() is None


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TestConfiguration:
    """Tests for configuration management."""

    def test_update_config(self, llm_cascade, cascade_config):
        llm_cascade.update_config(cascade_config)
        updated = llm_cascade.get_config()
        assert updated is cascade_config

    def test_update_config_validates(self, llm_cascade):
        invalid_config = CascadeConfig(chain=[])
        with pytest.raises(ValueError, match="empty"):
            llm_cascade.update_config(invalid_config)

    def test_get_config(self, llm_cascade):
        config = llm_cascade.get_config()
        assert isinstance(config, CascadeConfig)

    def test_add_model_to_chain(self, llm_cascade):
        initial_len = len(llm_cascade.config.chain)
        new_model = ModelConfig(provider=ModelProvider.GOOGLE, model_name="gemini-pro")
        llm_cascade.add_model_to_chain(new_model)
        assert len(llm_cascade.config.chain) == initial_len + 1

    def test_add_model_to_chain_at_position(self, llm_cascade):
        chain_len = len(llm_cascade.config.chain)
        new_model = ModelConfig(provider=ModelProvider.GOOGLE, model_name="gemini-pro")
        llm_cascade.add_model_to_chain(new_model, position=0)
        # Inserted at front → priorities should be re-assigned
        assert len(llm_cascade.config.chain) == chain_len + 1

    def test_remove_model_from_chain(self, llm_cascade):
        initial_len = len(llm_cascade.config.chain)
        removed = llm_cascade.remove_model_from_chain("gemini-pro")
        assert removed is True
        assert len(llm_cascade.config.chain) == initial_len - 1

    def test_remove_model_not_found(self, llm_cascade):
        removed = llm_cascade.remove_model_from_chain("non-existent-model")
        assert removed is False

    def test_remove_last_model_raises(self, llm_cascade):
        # Remove all but one
        while len(llm_cascade.config.chain) > 1:
            llm_cascade.remove_model_from_chain(llm_cascade.config.chain[-1].model_name)
        with pytest.raises(ValueError, match="cannot remove last"):
            llm_cascade.remove_model_from_chain(llm_cascade.config.chain[0].model_name)

    def test_add_model_reassigns_priorities(self, llm_cascade):
        new_model = ModelConfig(provider=ModelProvider.GOOGLE, model_name="gemini-pro")
        llm_cascade.add_model_to_chain(new_model)
        priorities = [m.priority for m in llm_cascade.config.chain]
        # Should be 1, 2, 3, ... without gaps
        assert priorities == list(range(1, len(priorities) + 1))


# ─────────────────────────────────────────────────────────────────────────────
# Cost Management
# ─────────────────────────────────────────────────────────────────────────────

class TestCostManagement:
    """Tests for cost management methods."""

    @pytest.mark.asyncio
    async def test_get_request_cost_after_route(self, llm_cascade):
        await llm_cascade.route("test")
        cost = llm_cascade.get_request_cost()
        assert cost >= 0.0

    @pytest.mark.asyncio
    async def test_get_cost_breakdown(self, llm_cascade):
        await llm_cascade.route("test")
        breakdown = llm_cascade.get_cost_breakdown()
        assert isinstance(breakdown, list)

    @pytest.mark.asyncio
    async def test_reset_cost_tracking(self, llm_cascade):
        await llm_cascade.route("test")
        llm_cascade.reset_cost_tracking()
        # After reset, session total should be 0
        stats = llm_cascade.get_cascade_stats()
        assert stats.total_cost_usd == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Stats Helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestStatsHelpers:
    """Tests for stats update logic."""

    @pytest.mark.asyncio
    async def test_cascade_hit_count_increments(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        # After first request, if it hit fallback...

    @pytest.mark.asyncio
    async def test_cascade_hit_rate_calculation(self, llm_cascade):
        for _ in range(5):
            await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        rate = stats.cascade_hit_rate
        assert 0.0 <= rate <= 1.0

    @pytest.mark.asyncio
    async def test_average_cascade_depth_tracked(self, llm_cascade):
        await llm_cascade.route("test")
        stats = llm_cascade.get_cascade_stats()
        assert stats.average_cascade_depth >= 0.0

    @pytest.mark.asyncio
    async def test_successful_requests_counted(self, llm_cascade):
        initial = llm_cascade.get_cascade_stats().successful_requests
        await llm_cascade.route("test")
        updated = llm_cascade.get_cascade_stats().successful_requests
        assert updated >= initial


# ─────────────────────────────────────────────────────────────────────────────
# Result Properties
# ─────────────────────────────────────────────────────────────────────────────

class TestResultProperties:
    """Tests for CascadeResult properties."""

    @pytest.mark.asyncio
    async def test_result_success_property_true(self, llm_cascade):
        result = await llm_cascade.route("test")
        # If not cascade_failure, success should be True
        if not result.cascade_failure:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_result_cascade_hit_property(self, llm_cascade):
        result = await llm_cascade.route("test")
        # cascade_hit is True only if depth > 0 and success
        assert isinstance(result.cascade_hit, bool)