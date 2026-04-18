"""
Tests for llm_cascade.models module.
Target coverage: >= 90%
"""

import pytest
from datetime import datetime, timezone
from implement.llm_cascade.models import (
    ModelConfig,
    CascadeConfig,
    AttemptRecord,
    CascadeResult,
    ProviderHealth,
    AttemptCost,
    ModelPricing,
    ModelCallResult,
    CascadeState,
    CascadeStats,
    LLMCascadeConfig,
    CascadeStateEnum,
    ModelProvider,
    DEFAULT_MODEL_PRICING,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def model_config_anthropic():
    return ModelConfig(
        provider=ModelProvider.ANTHROPIC,
        model_name="claude-opus-4",
        api_key_ref="env",
        endpoint=None,
        max_tokens=4096,
        temperature=0.7,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        priority=1,
    )


@pytest.fixture
def model_config_openai():
    return ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o",
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        priority=2,
    )


@pytest.fixture
def cascade_config(model_config_anthropic, model_config_openai):
    return CascadeConfig(
        chain=[model_config_anthropic, model_config_openai],
        latency_budget_ms=10000,
        cost_cap_usd=0.50,
        confidence_threshold=0.7,
        timeout_per_call_ms=5000,
        rate_limit_cooldown_seconds=60.0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ModelConfig
# ─────────────────────────────────────────────────────────────────────────────


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_initialization(self, model_config_anthropic):
        assert model_config_anthropic.provider == ModelProvider.ANTHROPIC
        assert model_config_anthropic.model_name == "claude-opus-4"
        assert model_config_anthropic.api_key_ref == "env"
        assert model_config_anthropic.max_tokens == 4096
        assert model_config_anthropic.temperature == 0.7
        assert model_config_anthropic.priority == 1

    def test_default_values(self):
        cfg = ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")
        assert cfg.api_key_ref == "env"
        assert cfg.endpoint is None
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.7
        assert cfg.cost_per_1k_input == 0.0
        assert cfg.cost_per_1k_output == 0.0
        assert cfg.priority == 1

    def test_get_pricing_with_overrides(self, model_config_anthropic):
        input_cost, output_cost = model_config_anthropic.get_pricing()
        assert input_cost == 0.015
        assert output_cost == 0.075

    def test_get_pricing_without_overrides_uses_default(self):
        cfg = ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")
        input_cost, output_cost = cfg.get_pricing()
        assert input_cost == 0.015
        assert output_cost == 0.075

    def test_get_pricing_unknown_model_returns_zeros(self):
        cfg = ModelConfig(provider=ModelProvider.CUSTOM, model_name="unknown-model")
        input_cost, output_cost = cfg.get_pricing()
        assert input_cost == 0.0
        assert output_cost == 0.0

    def test_default_chain_returns_five_models(self):
        chain = ModelConfig.default_chain()
        assert len(chain) == 5
        names = [m.model_name for m in chain]
        assert "claude-opus-4" in names
        assert "claude-sonnet-4" in names
        assert "gpt-4o" in names
        assert "gpt-4o-mini" in names
        assert "gemini-pro" in names

    def test_default_chain_priorities_are_sequential(self):
        chain = ModelConfig.default_chain()
        priorities = [m.priority for m in chain]
        assert priorities == [1, 2, 3, 4, 5]


class TestCascadeConfig:
    """Tests for CascadeConfig dataclass."""

    def test_initialization(self, cascade_config):
        assert len(cascade_config.chain) == 2
        assert cascade_config.latency_budget_ms == 10000
        assert cascade_config.cost_cap_usd == 0.50
        assert cascade_config.confidence_threshold == 0.7
        assert cascade_config.timeout_per_call_ms == 5000
        assert cascade_config.rate_limit_cooldown_seconds == 60.0

    def test_default_values(self):
        cfg = CascadeConfig(chain=[])
        assert cfg.latency_budget_ms == 10000
        assert cfg.cost_cap_usd == 0.50
        assert cfg.confidence_threshold == 0.7
        assert cfg.timeout_per_call_ms == 5000
        assert cfg.rate_limit_cooldown_seconds == 60.0

    def test_validate_empty_chain_raises(self):
        cfg = CascadeConfig(chain=[])
        with pytest.raises(ValueError, match="empty"):
            cfg.validate()

    def test_validate_confidence_threshold_negative_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.confidence_threshold = -0.1
        with pytest.raises(ValueError, match="between 0 and 1"):
            cfg.validate()

    def test_validate_confidence_threshold_over_one_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.confidence_threshold = 1.5
        with pytest.raises(ValueError, match="between 0 and 1"):
            cfg.validate()

    def test_validate_cost_cap_zero_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.cost_cap_usd = 0.0
        with pytest.raises(ValueError, match="cost_cap_usd must be positive"):
            cfg.validate()

    def test_validate_cost_cap_negative_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.cost_cap_usd = -0.5
        with pytest.raises(ValueError, match="cost_cap_usd must be positive"):
            cfg.validate()

    def test_validate_latency_budget_zero_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.latency_budget_ms = 0
        with pytest.raises(ValueError, match="latency_budget_ms must be positive"):
            cfg.validate()

    def test_validate_timeout_zero_raises(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.timeout_per_call_ms = 0
        with pytest.raises(ValueError, match="timeout_per_call_ms must be positive"):
            cfg.validate()

    def test_validate_valid_config_passes(self, cascade_config):
        cascade_config.validate()  # Should not raise

    def test_validate_confidence_threshold_boundary_zero(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.confidence_threshold = 0.0
        cfg.validate()  # Should not raise

    def test_validate_confidence_threshold_boundary_one(self):
        cfg = CascadeConfig(chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")])
        cfg.confidence_threshold = 1.0
        cfg.validate()  # Should not raise


class TestAttemptRecord:
    """Tests for AttemptRecord dataclass."""

    def test_initialization(self):
        record = AttemptRecord(
            model_name="claude-opus-4",
            provider="anthropic",
            latency_ms=1500,
            success=True,
        )
        assert record.model_name == "claude-opus-4"
        assert record.provider == "anthropic"
        assert record.latency_ms == 1500
        assert record.success is True
        assert record.error_type is None
        assert record.http_status is None
        assert record.confidence is None
        assert record.cost_usd == 0.0
        assert record.input_tokens == 0
        assert record.output_tokens == 0
        assert record.escalated_reason is None

    def test_all_fields_initialization(self):
        now = datetime.now(timezone.utc)
        record = AttemptRecord(
            model_name="gpt-4o",
            provider="openai",
            latency_ms=800,
            success=False,
            error_type="rate_limit",
            http_status=429,
            confidence=0.65,
            cost_usd=0.012,
            input_tokens=500,
            output_tokens=150,
            escalated_reason="low_confidence",
            timestamp=now,
        )
        assert record.model_name == "gpt-4o"
        assert record.success is False
        assert record.error_type == "rate_limit"
        assert record.http_status == 429
        assert record.confidence == 0.65
        assert record.cost_usd == 0.012
        assert record.input_tokens == 500
        assert record.output_tokens == 150
        assert record.escalated_reason == "low_confidence"
        assert record.timestamp == now

    def test_to_dict(self):
        record = AttemptRecord(
            model_name="claude-opus-4",
            provider="anthropic",
            latency_ms=1200,
            success=True,
            confidence=0.85,
            cost_usd=0.018,
        )
        d = record.to_dict()
        assert d["model_name"] == "claude-opus-4"
        assert d["provider"] == "anthropic"
        assert d["latency_ms"] == 1200
        assert d["success"] is True
        assert d["confidence"] == 0.85
        assert d["cost_usd"] == 0.018
        assert "timestamp" in d


class TestCascadeResult:
    """Tests for CascadeResult dataclass."""

    def test_initialization_success(self):
        result = CascadeResult(
            response="Hello world",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.018,
            latency_ms=1200,
            confidence=0.85,
            attempt_history=[],
        )
        assert result.response == "Hello world"
        assert result.model_used == "claude-opus-4"
        assert result.cascade_depth == 0
        assert result.cascade_failure is False
        assert result.cascade_exhausted is False

    def test_initialization_failure(self):
        result = CascadeResult(
            response=None,
            model_used=None,
            cascade_depth=-1,
            total_cost_usd=0.025,
            latency_ms=8000,
            confidence=0.0,
            attempt_history=[],
            error="all_models_exhausted",
            cascade_failure=True,
            cascade_exhausted=True,
        )
        assert result.response is None
        assert result.cascade_failure is True

    def test_success_property_true(self):
        result = CascadeResult(
            response="test",
            model_used="gpt-4o",
            cascade_depth=1,
            total_cost_usd=0.01,
            latency_ms=500,
            confidence=0.8,
            attempt_history=[],
        )
        assert result.success is True

    def test_success_property_false_when_no_response(self):
        result = CascadeResult(
            response=None,
            model_used=None,
            cascade_depth=-1,
            total_cost_usd=0.0,
            latency_ms=0,
            confidence=0.0,
            attempt_history=[],
            cascade_failure=True,
        )
        assert result.success is False

    def test_cascade_hit_property_not_hit(self):
        result = CascadeResult(
            response="test",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.015,
            latency_ms=1000,
            confidence=0.9,
            attempt_history=[],
        )
        assert result.cascade_hit is False

    def test_cascade_hit_property_hit(self):
        result = CascadeResult(
            response="test",
            model_used="gpt-4o",
            cascade_depth=2,
            total_cost_usd=0.008,
            latency_ms=3000,
            confidence=0.75,
            attempt_history=[],
        )
        assert result.cascade_hit is True

    def test_cascade_hit_false_when_failed(self):
        result = CascadeResult(
            response=None,
            model_used=None,
            cascade_depth=-1,
            total_cost_usd=0.0,
            latency_ms=0,
            confidence=0.0,
            attempt_history=[],
            cascade_failure=True,
        )
        assert result.cascade_hit is False

    def test_to_dict(self):
        result = CascadeResult(
            response="test response",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.018,
            latency_ms=1500,
            confidence=0.88,
            attempt_history=[],
        )
        d = result.to_dict()
        assert d["response"] == "test response"
        assert d["model_used"] == "claude-opus-4"
        assert d["cascade_depth"] == 0
        assert d["success"] is True
        assert d["cascade_hit"] is False
        assert d["cascade_failure"] is False


class TestProviderHealth:
    """Tests for ProviderHealth dataclass."""

    def test_initialization(self):
        health = ProviderHealth(provider="anthropic")
        assert health.provider == "anthropic"
        assert health.success_rate == 1.0
        assert health.median_latency_ms == 0
        assert health.error_types == {}
        assert health.rate_limit_count == 0
        assert health.is_in_cooldown is False
        assert health.cooldown_ends_at is None

    def test_initialization_with_values(self):
        now = datetime.now(timezone.utc)
        health = ProviderHealth(
            provider="openai",
            success_rate=0.95,
            median_latency_ms=800,
            error_types={"timeout": 2, "rate_limit": 1},
            rate_limit_count=1,
            last_checked=now,
            is_in_cooldown=True,
            cooldown_ends_at=now,
        )
        assert health.success_rate == 0.95
        assert health.median_latency_ms == 800
        assert health.error_types == {"timeout": 2, "rate_limit": 1}
        assert health.is_in_cooldown is True

    def test_to_dict(self):
        health = ProviderHealth(provider="anthropic", success_rate=0.92, median_latency_ms=600)
        d = health.to_dict()
        assert d["provider"] == "anthropic"
        assert d["success_rate"] == 0.92
        assert d["median_latency_ms"] == 600


class TestAttemptCost:
    """Tests for AttemptCost dataclass."""

    def test_initialization(self):
        cost = AttemptCost(
            model_name="claude-opus-4",
            input_tokens=500,
            output_tokens=100,
            cost_usd=0.018,
        )
        assert cost.model_name == "claude-opus-4"
        assert cost.input_tokens == 500
        assert cost.output_tokens == 100
        assert cost.cost_usd == 0.018

    def test_timestamp_default_set(self):
        cost = AttemptCost(model_name="test", input_tokens=0, output_tokens=0, cost_usd=0.0)
        assert cost.timestamp is not None


class TestModelPricing:
    """Tests for ModelPricing dataclass."""

    def test_initialization(self):
        pricing = ModelPricing(
            provider="anthropic",
            model_name="claude-opus-4",
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        assert pricing.provider == "anthropic"
        assert pricing.model_name == "claude-opus-4"
        assert pricing.cost_per_1k_input == 0.015
        assert pricing.cost_per_1k_output == 0.075


class TestModelCallResult:
    """Tests for ModelCallResult dataclass."""

    def test_initialization_success(self):
        result = ModelCallResult(
            success=True,
            response="Hello",
            latency_ms=500,
            input_tokens=100,
            output_tokens=50,
        )
        assert result.success is True
        assert result.response == "Hello"
        assert result.error_type is None

    def test_initialization_failure(self):
        result = ModelCallResult(
            success=False,
            error_type="timeout",
            latency_ms=5000,
        )
        assert result.success is False
        assert result.error_type == "timeout"


class TestCascadeState:
    """Tests for CascadeState dataclass."""

    def test_initialization_default(self):
        state = CascadeState()
        assert state.state == CascadeStateEnum.IDLE
        assert state.current_depth == 0
        assert state.attempt_history == []
        assert state.total_latency_ms == 0
        assert state.total_cost_usd == 0.0

    def test_initialization_with_values(self):
        state = CascadeState(
            state=CascadeStateEnum.MODEL_CALL,
            current_depth=1,
            total_latency_ms=2000,
            total_cost_usd=0.025,
        )
        assert state.state == CascadeStateEnum.MODEL_CALL
        assert state.current_depth == 1


class TestCascadeStats:
    """Tests for CascadeStats dataclass."""

    def test_initialization(self):
        stats = CascadeStats()
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.cascade_hit_count == 0
        assert stats.cascade_hit_rate == 0.0
        assert stats.average_cascade_depth == 0.0

    def test_to_dict(self):
        stats = CascadeStats(total_requests=10, successful_requests=9)
        d = stats.to_dict()
        assert d["total_requests"] == 10
        assert d["successful_requests"] == 9


class TestLLMCascadeConfig:
    """Tests for LLMCascadeConfig dataclass."""

    def test_initialization_with_defaults(self):
        cfg = LLMCascadeConfig(default_chain=[])
        assert cfg.default_latency_budget_ms == 10000
        assert cfg.default_cost_cap_usd == 0.50
        assert cfg.default_confidence_threshold == 0.7
        assert cfg.default_timeout_per_call_ms == 5000
        assert cfg.health_window_seconds == 86400
        assert cfg.rate_limit_cooldown_seconds == 60.0
        assert cfg.min_provider_success_rate == 0.8
        assert cfg.enable_request_isolation is True

    def test_initialization_with_overrides(self):
        cfg = LLMCascadeConfig(
            default_chain=[],
            default_cost_cap_usd=1.00,
            default_confidence_threshold=0.8,
        )
        assert cfg.default_cost_cap_usd == 1.00
        assert cfg.default_confidence_threshold == 0.8


class TestDefaultModelPricing:
    """Tests for DEFAULT_MODEL_PRICING constant."""

    def test_all_expected_models_present(self):
        expected = ["claude-opus-4", "claude-sonnet-4", "gpt-4o", "gpt-4o-mini", "gemini-pro"]
        for model in expected:
            assert model in DEFAULT_MODEL_PRICING

    def test_pricing_format(self):
        for model, (input_price, output_price) in DEFAULT_MODEL_PRICING.items():
            assert input_price >= 0
            assert output_price >= 0
            assert isinstance(input_price, float)
            assert isinstance(output_price, float)

    def test_pricing_order(self):
        # input should be < output for all models (correct for AI pricing)
        for model, (input_price, output_price) in DEFAULT_MODEL_PRICING.items():
            assert input_price <= output_price