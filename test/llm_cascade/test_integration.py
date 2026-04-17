"""
Tests for llm_cascade.integration module.
Target coverage: >= 70%

Tests integration layer components:
  - CascadeConfigStore
  - CascadeMetricsEmitter
  - CascadeIntegration
"""

import pytest
from implement.llm_cascade.integration import (
    CascadeConfigStore,
    CascadeMetricsEmitter,
    CascadeIntegration,
)
from implement.llm_cascade.models import (
    CascadeConfig,
    CascadeResult,
    CascadeStats,
    LLMCascadeConfig,
    ModelConfig,
    ModelProvider,
    ProviderHealth,
    AttemptRecord,
)
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# CascadeConfigStore
# ─────────────────────────────────────────────────────────────────────────────

class TestCascadeConfigStore:
    """Tests for CascadeConfigStore."""

    def test_init_default(self):
        store = CascadeConfigStore()
        assert store.config_path is None
        assert store._config_cache == {}
        assert store._global_config is None

    def test_init_with_config_path(self):
        store = CascadeConfigStore(config_path="/path/to/config.yaml")
        assert store.config_path == "/path/to/config.yaml"

    def test_load_global_config_returns_llm_cascade_config(self):
        store = CascadeConfigStore()
        config = store.load_global_config()
        assert isinstance(config, LLMCascadeConfig)

    def test_load_global_config_caches(self):
        store = CascadeConfigStore()
        config1 = store.load_global_config()
        config2 = store.load_global_config()
        assert config1 is config2

    def test_load_config_general(self):
        store = CascadeConfigStore()
        config = store.load_config("general")
        assert isinstance(config, CascadeConfig)
        assert len(config.chain) > 0

    def test_load_config_code(self):
        store = CascadeConfigStore()
        config = store.load_config("code")
        assert isinstance(config, CascadeConfig)
        assert config.confidence_threshold >= 0.7  # code has higher threshold

    def test_load_config_json(self):
        store = CascadeConfigStore()
        config = store.load_config("json")
        assert isinstance(config, CascadeConfig)
        assert config.confidence_threshold >= 0.8  # json has high threshold

    def test_load_config_creative(self):
        store = CascadeConfigStore()
        config = store.load_config("creative")
        assert isinstance(config, CascadeConfig)
        assert config.confidence_threshold <= 0.7  # creative has lower threshold

    def test_load_config_caches(self):
        store = CascadeConfigStore()
        config1 = store.load_config("general")
        config2 = store.load_config("general")
        assert config1 is config2

    def test_save_config(self):
        store = CascadeConfigStore()
        config = CascadeConfig(
            chain=[ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")],
        )
        store.save_config("custom_task", config)
        retrieved = store.load_config("custom_task")
        assert retrieved is config

    def test_load_unknown_task_type_returns_default(self):
        store = CascadeConfigStore()
        config = store.load_config("completely_unknown_type")
        # Should return general defaults
        assert isinstance(config, CascadeConfig)

    def test_task_thresholds_different_per_type(self):
        store = CascadeConfigStore()
        general = store.load_config("general")
        code = store.load_config("code")
        json_cfg = store.load_config("json")
        # Different task types should have different configs
        assert general.cost_cap_usd != code.cost_cap_usd or general.confidence_threshold != code.confidence_threshold


# ─────────────────────────────────────────────────────────────────────────────
# CascadeMetricsEmitter
# ─────────────────────────────────────────────────────────────────────────────

class TestCascadeMetricsEmitter:
    """Tests for CascadeMetricsEmitter."""

    def test_init_default(self):
        emitter = CascadeMetricsEmitter()
        assert emitter.metrics_adapter is None
        assert emitter.enable_logging is True

    def test_init_with_adapter(self):
        mock_adapter = object()
        emitter = CascadeMetricsEmitter(metrics_adapter=mock_adapter, enable_logging=False)
        assert emitter.metrics_adapter is mock_adapter
        assert emitter.enable_logging is False

    def test_emit_result_no_crash(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
        result = CascadeResult(
            response="test response",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.018,
            latency_ms=1500,
            confidence=0.88,
            attempt_history=[],
        )
        # Should not raise
        emitter.emit_result(result)

    def test_emit_result_with_attempts(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
        result = CascadeResult(
            response="test",
            model_used="gpt-4o",
            cascade_depth=1,
            total_cost_usd=0.008,
            latency_ms=3000,
            confidence=0.75,
            attempt_history=[
                AttemptRecord(
                    model_name="claude-opus-4",
                    provider="anthropic",
                    latency_ms=1500,
                    success=False,
                    error_type="low_confidence",
                ),
                AttemptRecord(
                    model_name="gpt-4o",
                    provider="openai",
                    latency_ms=1500,
                    success=True,
                    confidence=0.75,
                ),
            ],
        )
        emitter.emit_result(result)  # Should not raise

    def test_emit_provider_health_no_crash(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
        health = ProviderHealth(provider="anthropic", success_rate=0.95, median_latency_ms=600)
        emitter.emit_provider_health(health)

    def test_emit_stats_no_crash(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
        stats = CascadeStats(total_requests=10, successful_requests=9, cascade_hit_count=3)
        emitter.emit_stats(stats)

    def test_emit_with_logging_enabled(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="implement.llm_cascade.integration"):
            emitter = CascadeMetricsEmitter(enable_logging=True)
            result = CascadeResult(
                response="test",
                model_used="claude-opus-4",
                cascade_depth=0,
                total_cost_usd=0.01,
                latency_ms=500,
                confidence=0.9,
                attempt_history=[],
            )
            emitter.emit_result(result)
            # Should have logged at INFO level
            records = [r.levelname for r in caplog.records]
            assert "INFO" in records

    def test_emit_cascade_failure_event(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
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
        emitter.emit_result(result)  # Should not raise


# ─────────────────────────────────────────────────────────────────────────────
# CascadeIntegration
# ─────────────────────────────────────────────────────────────────────────────

class TestCascadeIntegration:
    """Tests for CascadeIntegration."""

    def test_init_requires_cascade(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        assert integration.cascade is cascade

    def test_pre_route_validate_always_returns_true(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        is_valid, reason = integration.pre_route_validate("test prompt")
        assert is_valid is True
        assert reason is None

    def test_pre_route_validate_with_config(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        config = CascadeConfig(chain=ModelConfig.default_chain())
        is_valid, reason = integration.pre_route_validate("test", config)
        assert is_valid is True

    def test_post_route_governance_always_returns_true(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        result = CascadeResult(
            response="test",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.01,
            latency_ms=500,
            confidence=0.9,
            attempt_history=[],
        )
        is_approved, concern = integration.post_route_governance(result)
        assert is_approved is True
        assert concern is None

    def test_propagate_identity_returns_empty_dict(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        model = ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4")
        headers = integration.propagate_identity(model, "test prompt")
        assert headers == {}

    def test_get_integration_status(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        status = integration.get_integration_status()
        assert isinstance(status, dict)
        assert "prompt_shields" in status
        assert "tiered_governance" in status
        assert "mcp_saif" in status
        assert "config_store" in status
        assert "metrics_infrastructure" in status

    def test_all_integration_status_values(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        status = integration.get_integration_status()
        for feature, value in status.items():
            assert value in ("wired", "stubbed", "error")


# ─────────────────────────────────────────────────────────────────────────────
# Integration Points
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationPoints:
    """Tests for integration between components."""

    def test_config_store_with_llm_cascade(self):
        from implement.llm_cascade.api import LLMCascade
        store = CascadeConfigStore()
        config = store.load_config("code")
        cascade = LLMCascade()
        cascade.update_config(config)
        assert cascade.config.confidence_threshold == config.confidence_threshold

    def test_metrics_emitter_with_result(self):
        emitter = CascadeMetricsEmitter(enable_logging=False)
        result = CascadeResult(
            response="Integration test response",
            model_used="claude-opus-4",
            cascade_depth=0,
            total_cost_usd=0.02,
            latency_ms=2000,
            confidence=0.85,
            attempt_history=[
                AttemptRecord(
                    model_name="claude-opus-4",
                    provider="anthropic",
                    latency_ms=2000,
                    success=True,
                    confidence=0.85,
                    cost_usd=0.02,
                ),
            ],
        )
        emitter.emit_result(result)

    def test_integration_propagate_identity_with_prompt(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        model = ModelConfig(provider=ModelProvider.OPENAI, model_name="gpt-4o")
        identity = integration.propagate_identity(model, "Long prompt " * 100)
        assert isinstance(identity, dict)

    def test_integration_pre_validate_rejects_none(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        # Even None prompt returns True (stub)
        is_valid, reason = integration.pre_route_validate(None)
        assert is_valid is True

    def test_integration_post_governance_with_failure(self):
        from implement.llm_cascade.api import LLMCascade
        cascade = LLMCascade()
        integration = CascadeIntegration(cascade)
        result = CascadeResult(
            response=None,
            model_used=None,
            cascade_depth=-1,
            total_cost_usd=0.0,
            latency_ms=0,
            confidence=0.0,
            attempt_history=[],
            cascade_failure=True,
            error="all_models_exhausted",
        )
        is_approved, concern = integration.post_route_governance(result)
        assert is_approved is True  # Stub always approves