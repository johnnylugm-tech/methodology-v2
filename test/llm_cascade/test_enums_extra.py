"""
Tests for enums TriggerReason and ConfidenceComponent coverage.
Target: reach 100% on enums.py
"""

import pytest
from implement.llm_cascade.enums import (
    TriggerReason,
    ConfidenceComponent,
)


class TestTriggerReason:
    """Tests for TriggerReason from_http_status and from_error_type methods."""

    def test_from_http_status_429(self):
        assert TriggerReason.from_http_status(429) == TriggerReason.RATE_LIMIT

    def test_from_http_status_500(self):
        assert TriggerReason.from_http_status(500) == TriggerReason.SERVER_ERROR

    def test_from_http_status_502(self):
        assert TriggerReason.from_http_status(502) == TriggerReason.SERVER_ERROR

    def test_from_http_status_503(self):
        assert TriggerReason.from_http_status(503) == TriggerReason.SERVER_ERROR

    def test_from_http_status_400(self):
        assert TriggerReason.from_http_status(400) == TriggerReason.API_ERROR

    def test_from_http_status_404(self):
        assert TriggerReason.from_http_status(404) == TriggerReason.API_ERROR

    def test_from_error_type_rate_limit(self):
        assert TriggerReason.from_error_type("rate_limit") == TriggerReason.RATE_LIMIT

    def test_from_error_type_rate_limit_429(self):
        assert TriggerReason.from_error_type("rate_limit_429") == TriggerReason.RATE_LIMIT

    def test_from_error_type_timeout(self):
        assert TriggerReason.from_error_type("timeout_error") == TriggerReason.TIMEOUT

    def test_from_error_type_server_error(self):
        assert TriggerReason.from_error_type("server_error_500") == TriggerReason.SERVER_ERROR

    def test_from_error_type_api_error(self):
        assert TriggerReason.from_error_type("api_error") == TriggerReason.API_ERROR

    def test_from_error_type_none(self):
        assert TriggerReason.from_error_type(None) == TriggerReason.MALFORMED_RESPONSE

    def test_from_error_type_unknown(self):
        assert TriggerReason.from_error_type("unknown_error") == TriggerReason.MALFORMED_RESPONSE


class TestConfidenceComponent:
    """Tests for ConfidenceComponent weight property."""

    def test_weight_entropy(self):
        assert ConfidenceComponent.ENTROPY.weight == 0.30

    def test_weight_repetition(self):
        assert ConfidenceComponent.REPETITION.weight == 0.25

    def test_weight_length(self):
        assert ConfidenceComponent.LENGTH.weight == 0.20

    def test_weight_parse_validity(self):
        assert ConfidenceComponent.PARSE_VALIDITY.weight == 0.25


class TestModelProvider:
    """Tests for ModelProvider.from_string method."""

    def test_from_string_anthropic(self):
        from implement.llm_cascade.enums import ModelProvider
        assert ModelProvider.from_string("anthropic") == ModelProvider.ANTHROPIC

    def test_from_string_openai(self):
        from implement.llm_cascade.enums import ModelProvider
        assert ModelProvider.from_string("openai") == ModelProvider.OPENAI

    def test_from_string_google(self):
        from implement.llm_cascade.enums import ModelProvider
        assert ModelProvider.from_string("google") == ModelProvider.GOOGLE

    def test_from_string_case_insensitive(self):
        from implement.llm_cascade.enums import ModelProvider
        assert ModelProvider.from_string("ANTHROPIC") == ModelProvider.ANTHROPIC
        assert ModelProvider.from_string("OpenAI") == ModelProvider.OPENAI

    def test_from_string_unknown_returns_custom(self):
        from implement.llm_cascade.enums import ModelProvider
        assert ModelProvider.from_string("unknown_provider") == ModelProvider.CUSTOM
