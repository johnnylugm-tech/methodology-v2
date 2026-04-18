"""
Tests for llm_cascade.exceptions module.
Target coverage: 100%
"""

import pytest
from implement.llm_cascade.exceptions import (
    CascadeError,
    CascadeExhaustedError,
    ProviderRateLimitError,
    ConfidenceThresholdError,
    LatencyBudgetExceededError,
    CostBudgetExceededError,
    CascadeConfigurationError,
    AllModelsExhaustedError,
)


class TestCascadeError:
    """Tests for CascadeError base exception."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(CascadeError):
            raise CascadeError("test message")

    def test_message_attribute(self):
        err = CascadeError("test message")
        assert err.message == "test message"

    def test_details_default_empty(self):
        err = CascadeError("test")
        assert err.details == {}

    def test_details_can_be_set(self):
        err = CascadeError("test", details={"key": "value"})
        assert err.details == {"key": "value"}

    def test_inheritance_from_exception(self):
        err = CascadeError("test")
        assert isinstance(err, Exception)

    def test_str_contains_message(self):
        err = CascadeError("test error message")
        assert "test error message" in str(err)


class TestCascadeExhaustedError:
    """Tests for CascadeExhaustedError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(CascadeExhaustedError):
            raise CascadeExhaustedError()

    def test_default_message(self):
        err = CascadeExhaustedError()
        assert "exhausted" in err.message.lower()

    def test_custom_message(self):
        err = CascadeExhaustedError("custom exhausted message")
        assert err.message == "custom exhausted message"

    def test_inheritance_from_cascade_error(self):
        err = CascadeExhaustedError()
        assert isinstance(err, CascadeError)
        assert isinstance(err, Exception)

    def test_details_can_be_set(self):
        err = CascadeExhaustedError(details={"attempts": 3})
        assert err.details == {"attempts": 3}


class TestProviderRateLimitError:
    """Tests for ProviderRateLimitError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ProviderRateLimitError):
            raise ProviderRateLimitError("anthropic")

    def test_provider_attribute(self):
        err = ProviderRateLimitError("openai")
        assert err.provider == "openai"

    def test_default_message_includes_provider(self):
        err = ProviderRateLimitError("anthropic")
        assert "anthropic" in err.message
        assert "rate limit" in err.message.lower()

    def test_custom_message(self):
        err = ProviderRateLimitError("google", message="custom limit message")
        assert err.message == "custom limit message"

    def test_retry_after_seconds_default_none(self):
        err = ProviderRateLimitError("anthropic")
        assert err.retry_after_seconds is None

    def test_retry_after_seconds_can_be_set(self):
        err = ProviderRateLimitError("openai", retry_after_seconds=30.5)
        assert err.retry_after_seconds == 30.5

    def test_inheritance_from_cascade_error(self):
        err = ProviderRateLimitError("test")
        assert isinstance(err, CascadeError)

    def test_details_can_be_set(self):
        err = ProviderRateLimitError("test", details={"retry_after": 60})
        assert err.details == {"retry_after": 60}


class TestConfidenceThresholdError:
    """Tests for ConfidenceThresholdError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ConfidenceThresholdError):
            raise ConfidenceThresholdError(0.5, 0.7)

    def test_confidence_attribute(self):
        err = ConfidenceThresholdError(0.4, 0.8)
        assert err.confidence == 0.4

    def test_threshold_attribute(self):
        err = ConfidenceThresholdError(0.4, 0.8)
        assert err.threshold == 0.8

    def test_model_name_default_none(self):
        err = ConfidenceThresholdError(0.5, 0.7)
        assert err.model_name is None

    def test_model_name_can_be_set(self):
        err = ConfidenceThresholdError(0.5, 0.7, model_name="claude-opus-4")
        assert err.model_name == "claude-opus-4"

    def test_message_includes_confidence_and_threshold(self):
        err = ConfidenceThresholdError(0.5, 0.7)
        assert "0.5" in err.message or "0.500" in err.message
        assert "0.7" in err.message or "0.700" in err.message

    def test_message_includes_model_name_when_set(self):
        err = ConfidenceThresholdError(0.3, 0.8, model_name="gpt-4o")
        assert "gpt-4o" in err.message

    def test_inheritance_from_cascade_error(self):
        err = ConfidenceThresholdError(0.5, 0.7)
        assert isinstance(err, CascadeError)

    def test_details_can_be_set(self):
        err = ConfidenceThresholdError(0.5, 0.7, details={"depth": 2})
        assert err.details == {"depth": 2}


class TestLatencyBudgetExceededError:
    """Tests for LatencyBudgetExceededError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(LatencyBudgetExceededError):
            raise LatencyBudgetExceededError(15000, 10000)

    def test_elapsed_ms_attribute(self):
        err = LatencyBudgetExceededError(12000, 10000)
        assert err.elapsed_ms == 12000

    def test_budget_ms_attribute(self):
        err = LatencyBudgetExceededError(12000, 10000)
        assert err.budget_ms == 10000

    def test_message_includes_both_values(self):
        err = LatencyBudgetExceededError(15000, 10000)
        assert "15000" in err.message
        assert "10000" in err.message

    def test_inheritance_from_cascade_error(self):
        err = LatencyBudgetExceededError(0, 0)
        assert isinstance(err, CascadeError)

    def test_details_can_be_set(self):
        err = LatencyBudgetExceededError(15000, 10000, details={"models_tried": 2})
        assert err.details == {"models_tried": 2}


class TestCostBudgetExceededError:
    """Tests for CostBudgetExceededError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(CostBudgetExceededError):
            raise CostBudgetExceededError(0.60, 0.50)

    def test_total_cost_usd_attribute(self):
        err = CostBudgetExceededError(0.75, 0.50)
        assert err.total_cost_usd == 0.75

    def test_cap_usd_attribute(self):
        err = CostBudgetExceededError(0.75, 0.50)
        assert err.cap_usd == 0.50

    def test_message_includes_costs(self):
        err = CostBudgetExceededError(0.60, 0.50)
        assert "0.60" in err.message
        assert "0.50" in err.message
        assert "$" in err.message

    def test_inheritance_from_cascade_error(self):
        err = CostBudgetExceededError(0.5, 0.3)
        assert isinstance(err, CascadeError)

    def test_details_can_be_set(self):
        err = CostBudgetExceededError(0.60, 0.50, details={"requests": 5})
        assert err.details == {"requests": 5}


class TestCascadeConfigurationError:
    """Tests for CascadeConfigurationError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(CascadeConfigurationError):
            raise CascadeConfigurationError("invalid chain")

    def test_message_prepended_with_prefix(self):
        err = CascadeConfigurationError("chain is empty")
        assert "Configuration error" in err.message
        assert "chain is empty" in err.message

    def test_inheritance_from_cascade_error(self):
        err = CascadeConfigurationError("test")
        assert isinstance(err, CascadeError)

    def test_details_can_be_set(self):
        err = CascadeConfigurationError("test", details={"field": "chain"})
        assert err.details == {"field": "chain"}


class TestAllModelsExhaustedError:
    """Tests for AllModelsExhaustedError."""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AllModelsExhaustedError):
            raise AllModelsExhaustedError()

    def test_attempt_count_default_zero(self):
        err = AllModelsExhaustedError()
        assert err.attempt_count == 0

    def test_attempt_count_can_be_set(self):
        err = AllModelsExhaustedError(attempt_count=5)
        assert err.attempt_count == 5

    def test_message_includes_attempt_count(self):
        err = AllModelsExhaustedError(attempt_count=3)
        assert "3" in err.message
        assert "exhausted" in err.message.lower()

    def test_inheritance_from_cascade_exhausted_error(self):
        err = AllModelsExhaustedError()
        assert isinstance(err, CascadeExhaustedError)
        assert isinstance(err, CascadeError)
        assert isinstance(err, Exception)

    def test_details_can_be_set(self):
        err = AllModelsExhaustedError(details={"last_error": "timeout"})
        assert err.details == {"last_error": "timeout"}

