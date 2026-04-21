"""
Tests for D7: LatencyAssessor [FR-R-7]

Covers SLO violations, queue depth, timeout configuration, and performance degradation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.latency import LatencyAssessor


class TestLatencyAssessorConstructor:
    """Test LatencyAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = LatencyAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D7"

    def test_constructor_default_slo_target(self):
        """Test default SLO target is set."""
        assessor = LatencyAssessor()
        assert assessor.DEFAULT_SLO_TARGET_MS == 2000


class TestLatencyAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_under_slo_target(self):
        """Test latency under SLO target is low risk."""
        context = {
            "current_latency_ms": 1000,
            "slo_target_ms": 2000,
            "queue_depth": 10,
            "max_queue": 100,
            "timeout_configured": True,
            "timeout_ms": 3000,
            "performance_degradation": False
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score < 0.3

    def test_assess_low_queue_depth(self):
        """Test low queue depth."""
        context = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "queue_depth": 10,
            "max_queue": 100,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score < 0.3

    def test_assess_proper_timeout_config(self):
        """Test proper timeout configuration reduces risk."""
        context_base = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "queue_depth": 50,
            "max_queue": 100
        }
        assessor = LatencyAssessor()

        context_good_timeout = {**context_base, "timeout_configured": True, "timeout_ms": 3000}
        context_no_timeout = {**context_base, "timeout_configured": False}

        score_good = assessor.assess(context_good_timeout)
        score_no = assessor.assess(context_no_timeout)

        assert score_good < score_no

    def test_assess_no_degradation(self):
        """Test no performance degradation."""
        context = {
            "current_latency_ms": 1800,
            "slo_target_ms": 2000,
            "performance_degradation": False
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score < 0.4


class TestLatencyAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_zero_latency(self):
        """Test zero latency."""
        context = {
            "current_latency_ms": 0,
            "slo_target_ms": 2000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score == 0.2

    def test_assess_zero_slo_target(self):
        """Test zero SLO target."""
        context = {
            "current_latency_ms": 100,
            "slo_target_ms": 0
        }
        assessor = LatencyAssessor()
        with pytest.raises(ZeroDivisionError):
            assessor.assess(context)

    def test_assess_exactly_at_slo_target(self):
        """Test exactly at SLO target is no violation."""
        context = {
            "current_latency_ms": 2000,
            "slo_target_ms": 2000,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score < 0.3

    def test_assess_slight_slo_violation(self):
        """Test slight SLO violation."""
        context = {
            "current_latency_ms": 2200,
            "slo_target_ms": 2000,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score > 0.0

    def test_assess_double_slo_violation(self):
        """Test double SLO violation is high risk."""
        context = {
            "current_latency_ms": 4000,
            "slo_target_ms": 2000,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score >= 0.4

    def test_assess_full_queue(self):
        """Test full queue depth."""
        context = {
            "current_latency_ms": 1000,
            "slo_target_ms": 2000,
            "queue_depth": 100,
            "max_queue": 100,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score >= 0.2

    def test_assess_timeout_below_slo(self):
        """Test timeout below SLO target."""
        context = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "timeout_configured": True,
            "timeout_ms": 1500
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        # Should be higher risk due to tight timeout
        assert score >= 0.13


class TestLatencyAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_no_timeout_configured(self):
        """Test no timeout configured is high risk."""
        context = {
            "current_latency_ms": 1000,
            "slo_target_ms": 2000,
            "timeout_configured": False
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score >= 0.2

    def test_assess_degradation_detected(self):
        """Test performance degradation detection."""
        context_base = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()

        context_no_deg = {**context_base, "performance_degradation": False, "degradation_trend": 0}
        context_deg = {**context_base, "performance_degradation": True, "degradation_trend": 30}

        score_no_deg = assessor.assess(context_no_deg)
        score_deg = assessor.assess(context_deg)

        assert score_deg > score_no_deg

    def test_assess_high_degradation_trend(self):
        """Test high degradation trend."""
        context = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "performance_degradation": True,
            "degradation_trend": 50
        }
        assessor = LatencyAssessor()
        score = assessor.assess(context)
        assert score >= 0.35

    def test_assess_configure_timeouts_method(self):
        """Test _configure_timeouts method."""
        assessor = LatencyAssessor()

        # No timeout = 0.0
        assert assessor._configure_timeouts({
            "timeout_configured": False
        }) == 0.0

        # Timeout at SLO target = 1.0
        assert assessor._configure_timeouts({
            "timeout_configured": True,
            "timeout_ms": 2000,
            "slo_target_ms": 2000
        }) == 1.0

        # Timeout below SLO = lower score
        score = assessor._configure_timeouts({
            "timeout_configured": True,
            "timeout_ms": 1000,
            "slo_target_ms": 2000
        })
        assert score < 1.0

    def test_assess_detect_performance_degradation_method(self):
        """Test _detect_performance_degradation method."""
        assessor = LatencyAssessor()

        # No degradation = 0.0
        assert assessor._detect_performance_degradation({
            "performance_degradation": False
        }) == 0.0

        # 50% degradation = 1.0
        assert assessor._detect_performance_degradation({
            "performance_degradation": True,
            "degradation_trend": 50
        }) == 1.0

        # 25% degradation = 0.5
        assert assessor._detect_performance_degradation({
            "performance_degradation": True,
            "degradation_trend": 25
        }) == 0.5

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "current_latency_ms": 2500,
            "slo_target_ms": 2000,
            "queue_depth": 75,
            "max_queue": 100,
            "performance_degradation": True,
            "degradation_trend": 15
        }
        assessor = LatencyAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D7"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert len(result.evidence) >= 3
        assert isinstance(result.metadata, dict)
        assert "latency_ratio" in result.metadata

    def test_assess_detailed_result_warns_on_slo_violation(self):
        """Test detailed result warns on SLO violation."""
        context = {
            "current_latency_ms": 3000,
            "slo_target_ms": 2000,
            "queue_depth": 50,
            "max_queue": 100
        }
        assessor = LatencyAssessor()
        result = assessor.assess_with_details(context)

        assert len(result.warnings) > 0
        assert any("SLO" in w or "overrun" in w.lower() for w in result.warnings)

    def test_assess_detailed_result_warns_on_degradation(self):
        """Test detailed result warns on performance degradation."""
        context = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "performance_degradation": True,
            "degradation_trend": 20
        }
        assessor = LatencyAssessor()
        result = assessor.assess_with_details(context)

        assert any("degradation" in w.lower() for w in result.warnings)

    def test_assess_all_queue_depths(self):
        """Test all queue depth levels."""
        context_base = {
            "current_latency_ms": 1500,
            "slo_target_ms": 2000,
            "max_queue": 100,
            "timeout_configured": True,
            "timeout_ms": 3000
        }
        assessor = LatencyAssessor()

        scores = {}
        for depth in [0, 25, 50, 75, 100]:
            context = {**context_base, "queue_depth": depth}
            scores[depth] = assessor.assess(context)

        # Higher queue should produce higher scores
        assert scores[0] < scores[100]
        assert scores[50] < scores[100]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
