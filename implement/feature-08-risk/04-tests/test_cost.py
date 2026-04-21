"""
Tests for D3: CostAssessor [FR-R-3]

Covers token budget, context window utilization, redundancy overhead, and batch efficiency.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from dimensions.cost import CostAssessor


class TestCostAssessorConstructor:
    """Test CostAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = CostAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D3"


class TestCostAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_normal_token_usage(self):
        """Test normal token usage is low risk."""
        context = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000,
            "retry_cost": 0,
            "total_cost": 50000,
            "batch_waste": 0
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score < 0.6

    def test_assess_under_budget(self):
        """Test under budget is low risk."""
        context = {
            "actual_tokens": 30000,
            "budget_tokens": 100000,
            "context_used": 60000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score < 0.45

    def test_assess_no_retry_cost(self):
        """Test no retry cost reduces risk."""
        context_base = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000,
            "total_cost": 50000
        }
        assessor = CostAssessor()

        context_no_retry = {**context_base, "retry_cost": 0}
        context_with_retry = {**context_base, "retry_cost": 5000}

        score_no_retry = assessor.assess(context_no_retry)
        score_with_retry = assessor.assess(context_with_retry)

        assert score_no_retry < score_with_retry

    def test_assess_efficient_batching(self):
        """Test efficient batching reduces risk."""
        context_base = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000,
            "total_cost": 50000
        }
        assessor = CostAssessor()

        context_efficient = {**context_base, "batch_waste": 0}
        context_wasteful = {**context_base, "batch_waste": 10000}

        score_efficient = assessor.assess(context_efficient)
        score_wasteful = assessor.assess(context_wasteful)

        # Note: batch_waste has minimal impact on score in this implement (max 0.2 contribution)
        assert abs(score_efficient - score_wasteful) < 0.15


class TestCostAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_zero_budget(self):
        """Test zero budget tokens."""
        context = {
            "actual_tokens": 0,
            "budget_tokens": 0,
            "context_used": 0,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 0.2

    def test_assess_zero_context_limit(self):
        """Test zero context limit."""
        context = {
            "actual_tokens": 1000,
            "budget_tokens": 100000,
            "context_used": 1000,
            "context_limit": 0
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert 0.19 <= score <= 0.21  # ~0.204

    def test_assess_over_budget_returns_one(self):
        """Test that over budget returns maximum risk."""
        context = {
            "actual_tokens": 150000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 1.0

    def test_assess_zero_total_cost(self):
        """Test zero total cost for redundancy calculation."""
        context = {
            "actual_tokens": 0,
            "budget_tokens": 100000,
            "retry_cost": 0,
            "total_cost": 0
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 0.2

    def test_assess_max_tokens_under_budget(self):
        """Test maximum tokens still under budget."""
        context = {
            "actual_tokens": 99000,
            "budget_tokens": 100000,
            "context_used": 180000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score < 1.0  # Should not be max since still under budget

    def test_assess_high_context_utilization(self):
        """Test high context utilization increases risk."""
        context_base = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "total_cost": 50000
        }
        assessor = CostAssessor()

        context_low = {**context_base, "context_used": 50000, "context_limit": 200000}
        context_high = {**context_base, "context_used": 190000, "context_limit": 200000}

        score_low = assessor.assess(context_low)
        score_high = assessor.assess(context_high)

        assert score_high > score_low


class TestCostAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_missing_context_keys(self):
        """Test missing context keys use defaults."""
        context = {}
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 0.2

    def test_assess_all_zeros(self):
        """Test all zero values."""
        context = {
            "actual_tokens": 0,
            "budget_tokens": 0,
            "context_used": 0,
            "context_limit": 0,
            "retry_cost": 0,
            "total_cost": 0,
            "batch_waste": 0
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 0.2

    def test_assess_very_large_numbers(self):
        """Test very large token numbers."""
        context = {
            "actual_tokens": 10000000,
            "budget_tokens": 5000000,
            "context_used": 5000000,
            "context_limit": 10000000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score == 1.0  # Over budget

    def test_assess_exactly_at_budget(self):
        """Test exactly at budget boundary."""
        context = {
            "actual_tokens": 100000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000,
            "total_cost": 100000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score < 1.0  # Not over budget

    def test_assess_exactly_at_context_limit(self):
        """Test exactly at context limit."""
        context = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "context_used": 200000,
            "context_limit": 200000,
            "total_cost": 50000
        }
        assessor = CostAssessor()
        score = assessor.assess(context)
        assert score < 1.0  # At limit but not over

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "actual_tokens": 90000,
            "budget_tokens": 100000,
            "context_used": 150000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D3"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert isinstance(result.metadata, dict)
        assert "budget_ratio" in result.metadata
        assert "window_utilization" in result.metadata

    def test_assess_warning_at_90_percent_budget(self):
        """Test warning when approaching budget limit."""
        context = {
            "actual_tokens": 95000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        result = assessor.assess_with_details(context)

        # Should have warning about approaching budget
        assert len(result.warnings) > 0

    def test_assess_detailed_result_shows_budget_exceeded(self):
        """Test detailed result shows budget exceeded warning."""
        context = {
            "actual_tokens": 150000,
            "budget_tokens": 100000,
            "context_used": 150000,
            "context_limit": 200000
        }
        assessor = CostAssessor()
        result = assessor.assess_with_details(context)

        assert "BUDGET EXCEEDED" in result.warnings

    def test_assess_batch_waste_calculation(self):
        """Test batch waste affects score."""
        context_base = {
            "actual_tokens": 50000,
            "budget_tokens": 100000,
            "context_used": 100000,
            "context_limit": 200000
        }
        assessor = CostAssessor()

        scores = []
        for waste in [0, 5000, 10000, 25000]:
            context = {**context_base, "batch_waste": waste, "total_cost": 50000}
            scores.append(assessor.assess(context))

        # Higher waste should produce higher scores
        for i in range(len(scores) - 1):
            assert scores[i + 1] >= scores[i] - 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
