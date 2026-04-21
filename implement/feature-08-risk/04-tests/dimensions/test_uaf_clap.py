"""
Tests for D4: UAFClapAssessor [FR-R-4]

Covers recursive agent depth, context growth, loop detection, and frame boundaries.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.uaf_clap import UAFClapAssessor


class TestUAFClapAssessorConstructor:
    """Test UAFClapAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = UAFClapAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D4"

    def test_constructor_default_max_depth(self):
        """Test default max depth is set."""
        assessor = UAFClapAssessor()
        assert assessor.DEFAULT_MAX_DEPTH == 5


class TestUAFClapAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_low_depth_low_risk(self):
        """Test low agent depth is low risk."""
        context = {
            "agent_depth": 1,
            "max_agent_depth": 5,
            "context_growth_rate": 0.05,
            "boundary_enforcement": "strict"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_moderate_depth(self):
        """Test moderate agent depth."""
        context = {
            "agent_depth": 3,
            "max_agent_depth": 5,
            "context_growth_rate": 0.1,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert 0.1 <= score <= 0.5

    def test_assess_strict_boundary_enforcement(self):
        """Test strict boundary enforcement reduces risk."""
        context_base = {
            "agent_depth": 3,
            "max_agent_depth": 5,
            "context_growth_rate": 0.1
        }
        assessor = UAFClapAssessor()

        context_weak = {**context_base, "boundary_enforcement": "weak"}
        context_strict = {**context_base, "boundary_enforcement": "strict"}

        score_weak = assessor.assess(context_weak)
        score_strict = assessor.assess(context_strict)

        assert score_strict < score_weak

    def test_assess_low_context_growth_rate(self):
        """Test low context growth rate."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "context_growth_rate": 0.05,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score < 0.3

    def test_assess_no_loops_detected(self):
        """Test no loops detected is low risk."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "agent_call_count": {"agent_a": 1, "agent_b": 1},
            "max_loop_calls": 3,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score < 0.3


class TestUAFClapAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_zero_depth(self):
        """Test zero agent depth."""
        context = {
            "agent_depth": 0,
            "max_agent_depth": 5,
            "boundary_enforcement": "strict"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score == 0.0

    def test_assess_zero_max_depth(self):
        """Test zero max depth."""
        context = {
            "agent_depth": 1,
            "max_agent_depth": 0,
            "boundary_enforcement": "strict"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        # Should handle div by zero
        assert 0.0 <= score <= 1.0

    def test_assess_depth_exceeds_max(self):
        """Test depth exceeds max (potential infinite loop)."""
        context = {
            "agent_depth": 10,
            "max_agent_depth": 5,
            "boundary_enforcement": "none"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score >= 0.44

    def test_assess_high_context_growth_rate(self):
        """Test high context growth rate (>50% per step)."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "context_growth_rate": 0.6,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score >= 0.46

    def test_assess_loop_exceeds_max(self):
        """Test agent call count exceeds max (loop detected)."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "agent_call_count": {"agent_a": 10},
            "max_loop_calls": 3,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        # Should detect loop and return high score
        assert score >= 0.41

    def test_assess_no_boundary_enforcement(self):
        """Test no boundary enforcement is highest risk."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "boundary_enforcement": "none"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert score >= 0.27

    def test_assess_empty_agent_call_count(self):
        """Test empty agent call count."""
        context = {
            "agent_depth": 1,
            "max_agent_depth": 5,
            "agent_call_count": {},
            "max_loop_calls": 3,
            "boundary_enforcement": "strict"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        assert 0.0 <= score <= 0.3

    def test_assess_all_context_growth_rates(self):
        """Test all context growth rate levels."""
        context_base = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "boundary_enforcement": "strict"
        }
        assessor = UAFClapAssessor()

        scores = {}
        for rate in [0.0, 0.05, 0.2, 0.4, 0.6]:
            context = {**context_base, "context_growth_rate": rate}
            scores[rate] = assessor.assess(context)

        # Higher rates should produce higher scores
        assert scores[0.0] < scores[0.6]


class TestUAFClapAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_all_boundary_enforcement_levels(self):
        """Test all boundary enforcement levels."""
        context_base = {
            "agent_depth": 3,
            "max_agent_depth": 5,
            "context_growth_rate": 0.1
        }
        assessor = UAFClapAssessor()

        scores = {}
        for level in ["none", "weak", "moderate", "strict"]:
            context = {**context_base, "boundary_enforcement": level}
            scores[level] = assessor.assess(context)

        assert scores["none"] > scores["weak"]
        assert scores["weak"] > scores["moderate"]
        assert scores["moderate"] > scores["strict"]

    def test_assess_multiple_agents_with_different_counts(self):
        """Test multiple agents with different call counts."""
        context = {
            "agent_depth": 2,
            "max_agent_depth": 5,
            "agent_call_count": {"agent_a": 1, "agent_b": 2, "agent_c": 5},
            "max_loop_calls": 3,
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        score = assessor.assess(context)
        # Should be elevated due to agent_c exceeding max
        assert score > 0.3

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "agent_depth": 4,
            "max_agent_depth": 5,
            "agent_call_count": {"agent_a": 2, "agent_b": 3},
            "boundary_enforcement": "moderate"
        }
        assessor = UAFClapAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D4"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert isinstance(result.metadata, dict)
        assert "depth_ratio" in result.metadata
        assert "call_counts" in result.metadata

    def test_assess_detailed_result_warns_on_depth_exceeded(self):
        """Test detailed result warns when depth exceeded."""
        context = {
            "agent_depth": 10,
            "max_agent_depth": 5,
            "agent_call_count": {},
            "boundary_enforcement": "none"
        }
        assessor = UAFClapAssessor()
        result = assessor.assess_with_details(context)

        assert any("DEPTH EXCEEDED" in w for w in result.warnings)

    def test_measure_context_growth_rate(self):
        """Test _measure_context_growth_rate method."""
        assessor = UAFClapAssessor()

        assert assessor._measure_context_growth_rate({"context_growth_rate": 0.0}) == 0.0
        assert assessor._measure_context_growth_rate({"context_growth_rate": 0.6}) == 1.0
        assert 0.0 < assessor._measure_context_growth_rate({"context_growth_rate": 0.2}) < 1.0

    def test_detect_loop_method(self):
        """Test _detect_loop method."""
        assessor = UAFClapAssessor()

        # No loop
        assert assessor._detect_loop({"agent_call_count": {}, "max_loop_calls": 3}) == 0.0

        # At threshold
        assert assessor._detect_loop({"agent_call_count": {"a": 3}, "max_loop_calls": 3}) == 0.6

        # Over threshold
        assert assessor._detect_loop({"agent_call_count": {"a": 5}, "max_loop_calls": 3}) == 1.0

    def test_evaluate_frame_boundaries_method(self):
        """Test _evaluate_frame_boundaries method."""
        assessor = UAFClapAssessor()

        assert assessor._evaluate_frame_boundaries({"boundary_enforcement": "none"}) == 1.0
        assert assessor._evaluate_frame_boundaries({"boundary_enforcement": "strict"}) == 0.0
        assert 0.0 < assessor._evaluate_frame_boundaries({"boundary_enforcement": "moderate"}) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
