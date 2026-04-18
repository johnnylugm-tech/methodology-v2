"""
Tests for llm_cascade.enums module.
Target coverage: 100%
"""

import pytest
from implement.llm_cascade.enums import (
    CascadeStateEnum,
    CascadeErrorType,
    ModelProvider,
    TriggerReason,
    ConfidenceComponent,
)


class TestCascadeStateEnum:
    """Tests for CascadeStateEnum."""

    def test_all_states_exist(self):
        assert hasattr(CascadeStateEnum, "IDLE")
        assert hasattr(CascadeStateEnum, "ROUTING")
        assert hasattr(CascadeStateEnum, "MODEL_CALL")
        assert hasattr(CascadeStateEnum, "CASCADE_CHECK")
        assert hasattr(CascadeStateEnum, "EXHAUSTED")

    def test_state_count(self):
        assert len(CascadeStateEnum) == 5

    def test_state_values_are_auto(self):
        for state in CascadeStateEnum:
            assert isinstance(state.value, int)

    def test_state_can_be_compared(self):
        assert CascadeStateEnum.IDLE == CascadeStateEnum.IDLE
        assert CascadeStateEnum.IDLE != CascadeStateEnum.ROUTING

    def test_state_from_value(self):
        assert CascadeStateEnum(1) == CascadeStateEnum.IDLE

    def test_state_name_property(self):
        assert CascadeStateEnum.IDLE.name == "IDLE"
        assert CascadeStateEnum.ROUTING.name == "ROUTING"


class TestCascadeErrorType:
    """Tests for CascadeErrorType."""

    def test_all_error_types_exist(self):
        assert hasattr(CascadeErrorType, "ALL_MODELS_FAILED")
        assert hasattr(CascadeErrorType, "ALL_MODELS_LOW_CONFIDENCE")
        assert hasattr(CascadeErrorType, "LATENCY_BUDGET_EXCEEDED")
        assert hasattr(CascadeErrorType, "COST_BUDGET_EXCEEDED")
        assert hasattr(CascadeErrorType, "NO_MODELS_AVAILABLE")

    def test_error_type_count(self):
        assert len(CascadeErrorType) == 5

    def test_error_type_values_are_auto(self):
        for et in CascadeErrorType:
            assert isinstance(et.value, int)


class TestModelProvider:
    """Tests for ModelProvider enum."""

    def test_all_providers_exist(self):
        assert hasattr(ModelProvider, "ANTHROPIC")
        assert hasattr(ModelProvider, "OPENAI")
        assert hasattr(ModelProvider, "GOOGLE")
        assert hasattr(ModelProvider, "CUSTOM")

    def test_provider_count(self):
        assert len(ModelProvider) == 4

    def test_provider_string_values(self):
        assert ModelProvider.ANTHROPIC.value == "anthropic"
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.GOOGLE.value == "google"
        assert ModelProvider.CUSTOM.value == "custom"

    def test_from_string_lowercase(self):
        assert ModelProvider.from_string("anthropic") == ModelProvider.ANTHROPIC
        assert ModelProvider.from_string("openai") == ModelProvider.OPENAI
        assert ModelProvider.from_string("google") == ModelProvider.GOOGLE

    def test_from_string_uppercase(self):
        assert ModelProvider.from_string("ANTHROPIC") == ModelProvider.ANTHROPIC
        assert ModelProvider.from_string("OPENAI") == ModelProvider.OPENAI

    def test_from_string_mixed_case(self):
        assert ModelProvider.from_string("Anthropic") == ModelProvider.ANTHROPIC
        assert ModelProvider.from_string("OpenAI") == ModelProvider.OPENAI

    def test_from_string_unknown_returns_custom(self):
        assert ModelProvider.from_string("unknown") == ModelProvider.CUSTOM
        assert ModelProvider.from_string("mistral") == ModelProvider.CUSTOM
        assert ModelProvider.from_string("") == ModelProvider.CUSTOM

    def test_from_string_by_name(self):
        # Unknown value but matches enum name
        assert ModelProvider.from_string("CUSTOM") == ModelProvider.CUSTOM


class TestTriggerReason:
    """Tests for TriggerReason enum."""

    def test_all_reasons_exist(self):
        expected = [
            "API_ERROR", "TIMEOUT", "RATE_LIMIT", "SERVER_ERROR",
            "MALFORMED_RESPONSE", "LOW_CONFIDENCE", "LATENCY_BUDGET_EXCEEDED",
            "COST_BUDGET_EXCEEDED", "PROVIDER_UNHEALTHY", "ALL_MODELS_EXHAUSTED",
        ]
        for name in expected:
            assert hasattr(TriggerReason, name), f"Missing: {name}"

    def test_trigger_reason_count(self):
        assert len(TriggerReason) == 10

    def test_trigger_reason_string_values(self):
        assert TriggerReason.API_ERROR.value == "api_error"
        assert TriggerReason.TIMEOUT.value == "timeout"
        assert TriggerReason.RATE_LIMIT.value == "rate_limit"
        assert TriggerReason.SERVER_ERROR.value == "server_error"
        assert TriggerReason.MALFORMED_RESPONSE.value == "malformed_response"
        assert TriggerReason.LOW_CONFIDENCE.value == "low_confidence"
        assert TriggerReason.LATENCY_BUDGET_EXCEEDED.value == "latency_budget_exceeded"
        assert TriggerReason.COST_BUDGET_EXCEEDED.value == "cost_budget_exceeded"
        assert TriggerReason.PROVIDER_UNHEALTHY.value == "provider_unhealthy"
        assert TriggerReason.ALL_MODELS_EXHAUSTED.value == "all_models_exhausted"

    def test_from_http_status_429(self):
        assert TriggerReason.from_http_status(429) == TriggerReason.RATE_LIMIT

    def test_from_http_status_500(self):
        assert TriggerReason.from_http_status(500) == TriggerReason.SERVER_ERROR

    def test_from_http_status_502(self):
        assert TriggerReason.from_http_status(502) == TriggerReason.SERVER_ERROR

    def test_from_http_status_503(self):
        assert TriggerReason.from_http_status(503) == TriggerReason.SERVER_ERROR

    def test_from_http_status_599(self):
        assert TriggerReason.from_http_status(599) == TriggerReason.SERVER_ERROR

    def test_from_http_status_400(self):
        assert TriggerReason.from_http_status(400) == TriggerReason.API_ERROR

    def test_from_http_status_401(self):
        assert TriggerReason.from_http_status(401) == TriggerReason.API_ERROR

    def test_from_http_status_200(self):
        assert TriggerReason.from_http_status(200) == TriggerReason.API_ERROR

    def test_from_error_type_none(self):
        assert TriggerReason.from_error_type(None) == TriggerReason.MALFORMED_RESPONSE

    def test_from_error_type_rate_limit_string(self):
        assert TriggerReason.from_error_type("rate_limit") == TriggerReason.RATE_LIMIT
        assert TriggerReason.from_error_type("RATE_LIMIT") == TriggerReason.RATE_LIMIT

    def test_from_error_type_timeout_string(self):
        assert TriggerReason.from_error_type("timeout") == TriggerReason.TIMEOUT
        assert TriggerReason.from_error_type("TIMEOUT") == TriggerReason.TIMEOUT

    def test_from_error_type_server_error_string(self):
        assert TriggerReason.from_error_type("server_error") == TriggerReason.SERVER_ERROR

    def test_from_error_type_api_error_string(self):
        assert TriggerReason.from_error_type("api_error") == TriggerReason.API_ERROR

    def test_from_error_type_unknown(self):
        assert TriggerReason.from_error_type("something_unusual") == TriggerReason.MALFORMED_RESPONSE


class TestConfidenceComponent:
    """Tests for ConfidenceComponent enum."""

    def test_all_components_exist(self):
        assert hasattr(ConfidenceComponent, "ENTROPY")
        assert hasattr(ConfidenceComponent, "REPETITION")
        assert hasattr(ConfidenceComponent, "LENGTH")
        assert hasattr(ConfidenceComponent, "PARSE_VALIDITY")

    def test_component_count(self):
        assert len(ConfidenceComponent) == 4

    def test_component_string_values(self):
        assert ConfidenceComponent.ENTROPY.value == "entropy"
        assert ConfidenceComponent.REPETITION.value == "repetition"
        assert ConfidenceComponent.LENGTH.value == "length"
        assert ConfidenceComponent.PARSE_VALIDITY.value == "parse_validity"

    def test_entropy_weight(self):
        assert ConfidenceComponent.ENTROPY.weight == 0.30

    def test_repetition_weight(self):
        assert ConfidenceComponent.REPETITION.weight == 0.25

    def test_length_weight(self):
        assert ConfidenceComponent.LENGTH.weight == 0.20

    def test_parse_validity_weight(self):
        assert ConfidenceComponent.PARSE_VALIDITY.weight == 0.25

    def test_weights_sum_to_one(self):
        total = (
            ConfidenceComponent.ENTROPY.weight
            + ConfidenceComponent.REPETITION.weight
            + ConfidenceComponent.LENGTH.weight
            + ConfidenceComponent.PARSE_VALIDITY.weight
        )
        assert abs(total - 1.0) < 1e-9

    def test_all_weights_are_positive(self):
        for comp in ConfidenceComponent:
            assert comp.weight > 0
            assert comp.weight < 1