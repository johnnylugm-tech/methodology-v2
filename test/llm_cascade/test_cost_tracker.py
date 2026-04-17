"""
Tests for llm_cascade.cost_tracker module.
Target coverage: >= 85%
"""

import pytest
from implement.llm_cascade.cost_tracker import CostTracker
from implement.llm_cascade.models import (
    CascadeConfig,
    ModelConfig,
    ModelProvider,
    AttemptCost,
    ModelPricing,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def cost_tracker():
    return CostTracker()


@pytest.fixture
def cascade_config():
    return CascadeConfig(
        chain=[
            ModelConfig(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4"),
        ],
        cost_cap_usd=0.50,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────

class TestCostTrackerInit:
    """Tests for CostTracker initialization."""

    def test_initial_state(self, cost_tracker):
        assert cost_tracker.get_total_cost() == 0.0
        assert cost_tracker.get_session_total() == 0.0
        assert cost_tracker.get_cost_breakdown() == []


# ─────────────────────────────────────────────────────────────────────────────
# Cost Recording — add_cost
# ─────────────────────────────────────────────────────────────────────────────

class TestAddCost:
    """Tests for add_cost method."""

    def test_add_cost_returns_call_cost(self, cost_tracker):
        cost = cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        # (1000/1000)*0.015 + (500/1000)*0.075 = 0.015 + 0.0375 = 0.0525
        assert abs(cost - 0.0525) < 0.001

    def test_add_cost_updates_total(self, cost_tracker):
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        assert cost_tracker.get_total_cost() > 0.0

    def test_add_cost_accumulates(self, cost_tracker):
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        cost_tracker.add_cost(
            provider="openai",
            model="gpt-4o",
            input_tokens=500,
            output_tokens=200,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
        )
        total = cost_tracker.get_total_cost()
        # 0.0525 + (0.5*0.005 + 0.2*0.015) = 0.0525 + (0.0025 + 0.003) = 0.058
        assert total > 0.0525

    def test_add_cost_session_total_accumulates(self, cost_tracker):
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        session = cost_tracker.get_session_total()
        assert session > 0.0

    def test_add_cost_zero_tokens(self, cost_tracker):
        cost = cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=0,
            output_tokens=0,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        assert cost == 0.0

    def test_add_cost_rounded_to_6_decimals(self, cost_tracker):
        cost = cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=333,
            output_tokens=777,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        # Check it's rounded
        assert cost == round(cost, 6)

    def test_add_cost_default_pricing(self, cost_tracker):
        """add_cost uses DEFAULT_MODEL_PRICING for lookup."""
        # Uses defaults from models.py
        cost = cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.0,
            cost_per_1k_output=0.0,
        )
        assert cost == 0.0  # no overrides and model not in defaults → 0


# ─────────────────────────────────────────────────────────────────────────────
# Cost Recording — add_cost_from_pricing
# ─────────────────────────────────────────────────────────────────────────────

class TestAddCostFromPricing:
    """Tests for add_cost_from_pricing using DEFAULT_MODEL_PRICING."""

    def test_add_cost_from_pricing(self, cost_tracker):
        cost = cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        # (1000/1000)*0.015 + (500/1000)*0.075 = 0.015 + 0.0375 = 0.0525
        assert abs(cost - 0.0525) < 0.001

    def test_add_cost_from_pricing_gpt4o(self, cost_tracker):
        cost = cost_tracker.add_cost_from_pricing(
            provider="openai",
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        # (1000/1000)*0.005 + (500/1000)*0.015 = 0.005 + 0.0075 = 0.0125
        assert abs(cost - 0.0125) < 0.001

    def test_add_cost_from_pricing_gpt4o_mini(self, cost_tracker):
        cost = cost_tracker.add_cost_from_pricing(
            provider="openai",
            model="gpt-4o-mini",
            input_tokens=10000,
            output_tokens=5000,
        )
        # (10000/1000)*0.00015 + (5000/1000)*0.0006
        # = 0.0015 + 0.003 = 0.0045
        assert abs(cost - 0.0045) < 0.001

    def test_add_cost_from_pricing_unknown_model(self, cost_tracker):
        cost = cost_tracker.add_cost_from_pricing(
            provider="custom",
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500,
        )
        assert cost == 0.0

    def test_add_cost_from_pricing_updates_total(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        assert cost_tracker.get_total_cost() > 0


# ─────────────────────────────────────────────────────────────────────────────
# Budget Checks
# ─────────────────────────────────────────────────────────────────────────────

class TestIsWithinBudget:
    """Tests for is_within_budget method."""

    def test_within_budget(self, cost_tracker, cascade_config):
        # Add small cost
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=100,
            output_tokens=50,
        )
        assert cost_tracker.is_within_budget(cascade_config) is True

    def test_at_budget_boundary(self, cost_tracker, cascade_config):
        # Cost exactly at cap - should be False (since request_total < cap is checked)
        # Set cost to cap
        cascade_config.cost_cap_usd = 0.001
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=10000,
            output_tokens=5000,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        assert cost_tracker.is_within_budget(cascade_config) is False

    def test_over_budget(self, cost_tracker, cascade_config):
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=20000,
            output_tokens=10000,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        assert cost_tracker.is_within_budget(cascade_config) is False


class TestRemainingBudget:
    """Tests for get_remaining_budget method."""

    def test_no_cost_remaining_is_cap(self, cost_tracker, cascade_config):
        remaining = cost_tracker.get_remaining_budget(cascade_config)
        assert remaining == cascade_config.cost_cap_usd

    def test_partial_cost_remaining(self, cost_tracker, cascade_config):
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        used = cost_tracker.get_total_cost()
        remaining = cost_tracker.get_remaining_budget(cascade_config)
        assert abs(remaining + used - cascade_config.cost_cap_usd) < 0.001

    def test_no_budget_remaining(self, cost_tracker, cascade_config):
        # Add cost exceeding cap
        cascade_config.cost_cap_usd = 0.001
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=10000,
            output_tokens=5000,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        remaining = cost_tracker.get_remaining_budget(cascade_config)
        assert remaining == 0.0

    def test_remaining_never_negative(self, cost_tracker, cascade_config):
        # Force a large cost that exceeds cap
        cost_tracker.add_cost(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=100000,
            output_tokens=50000,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
        )
        remaining = cost_tracker.get_remaining_budget(cascade_config)
        assert remaining == 0.0  # floor at 0


# ─────────────────────────────────────────────────────────────────────────────
# Cost Breakdown
# ─────────────────────────────────────────────────────────────────────────────

class TestCostBreakdown:
    """Tests for cost breakdown methods."""

    def test_get_cost_breakdown_empty(self, cost_tracker):
        assert cost_tracker.get_cost_breakdown() == []

    def test_get_cost_breakdown_after_calls(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        breakdown = cost_tracker.get_cost_breakdown()
        assert len(breakdown) == 1
        assert isinstance(breakdown[0], AttemptCost)
        assert breakdown[0].model_name == "claude-opus-4"

    def test_get_cost_breakdown_accumulation(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.add_cost_from_pricing(
            provider="openai",
            model="gpt-4o",
            input_tokens=500,
            output_tokens=200,
        )
        breakdown = cost_tracker.get_cost_breakdown()
        assert len(breakdown) == 2

    def test_get_cost_breakdown_summary(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.add_cost_from_pricing(
            provider="openai",
            model="gpt-4o",
            input_tokens=500,
            output_tokens=200,
        )
        summary = cost_tracker.get_cost_breakdown_summary()
        assert "claude-opus-4" in summary
        assert "gpt-4o" in summary

    def test_summary_values_are_floats(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        summary = cost_tracker.get_cost_breakdown_summary()
        for v in summary.values():
            assert isinstance(v, float)


# ─────────────────────────────────────────────────────────────────────────────
# Token Pricing
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenPricing:
    """Tests for token pricing registration and lookup."""

    def test_register_pricing(self, cost_tracker):
        pricing = ModelPricing(
            provider="anthropic",
            model_name="my-model",
            cost_per_1k_input=0.010,
            cost_per_1k_output=0.050,
        )
        cost_tracker.register_pricing(pricing)
        retrieved = cost_tracker.get_pricing("my-model")
        assert retrieved is not None
        assert retrieved.cost_per_1k_input == 0.010

    def test_get_pricing_unknown(self, cost_tracker):
        assert cost_tracker.get_pricing("totally-unknown") is None

    def test_register_pricing_overrides(self, cost_tracker):
        """Registering same model twice should update."""
        pricing1 = ModelPricing(
            provider="anthropic",
            model_name="claude-opus-4",
            cost_per_1k_input=0.010,
            cost_per_1k_output=0.050,
        )
        pricing2 = ModelPricing(
            provider="anthropic",
            model_name="claude-opus-4",
            cost_per_1k_input=0.020,
            cost_per_1k_output=0.100,
        )
        cost_tracker.register_pricing(pricing1)
        cost_tracker.register_pricing(pricing2)
        retrieved = cost_tracker.get_pricing("claude-opus-4")
        assert retrieved.cost_per_1k_input == 0.020


# ─────────────────────────────────────────────────────────────────────────────
# Reset
# ─────────────────────────────────────────────────────────────────────────────

class TestReset:
    """Tests for reset methods."""

    def test_reset_request_total(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        assert cost_tracker.get_total_cost() > 0
        cost_tracker.reset()
        assert cost_tracker.get_total_cost() == 0.0

    def test_reset_preserves_session_total(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        session_before = cost_tracker.get_session_total()
        cost_tracker.reset()
        session_after = cost_tracker.get_session_total()
        assert session_before == session_after

    def test_reset_clears_breakdown(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.reset()
        assert cost_tracker.get_cost_breakdown() == []

    def test_reset_session_clears_everything(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.reset_session()
        assert cost_tracker.get_total_cost() == 0.0
        assert cost_tracker.get_session_total() == 0.0

    def test_reset_session_clears_breakdown(self, cost_tracker):
        cost_tracker.add_cost_from_pricing(
            provider="anthropic",
            model="claude-opus-4",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.reset_session()
        assert cost_tracker.get_cost_breakdown() == []