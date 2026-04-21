"""
Tests for D6: CrossAgentLeakAssessor [FR-R-6]

Covers agent isolation level, shared state exposure, message sanitization, and authorization checks.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.cross_agent_leak import CrossAgentLeakAssessor


class TestCrossAgentLeakAssessorConstructor:
    """Test CrossAgentLeakAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = CrossAgentLeakAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D6"


class TestCrossAgentLeakAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_full_isolation_low_risk(self):
        """Test full agent isolation is low risk."""
        context = {
            "agent_isolation_level": 1.0,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert score < 0.1

    def test_assess_high_isolation(self):
        """Test high isolation level."""
        context = {
            "agent_isolation_level": 0.9,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_sanitized_messages(self):
        """Test sanitized messages reduce risk."""
        context_base = {
            "agent_isolation_level": 0.5,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()

        context_sanitized = {**context_base, "inter_agent_messages_sanitized": True}
        context_unsanitized = {**context_base, "inter_agent_messages_sanitized": False}

        score_sanitized = assessor.assess(context_sanitized)
        score_unsanitized = assessor.assess(context_unsanitized)

        assert score_sanitized < score_unsanitized

    def test_assess_authorization_checks(self):
        """Test authorization checks reduce risk."""
        context_base = {
            "agent_isolation_level": 0.5,
            "inter_agent_messages_sanitized": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()

        context_with_auth = {**context_base, "has_authorization_checks": True}
        context_without_auth = {**context_base, "has_authorization_checks": False}

        score_with = assessor.assess(context_with_auth)
        score_without = assessor.assess(context_without_auth)

        assert score_with < score_without

    def test_assess_no_shared_state_access(self):
        """Test no shared state access is low risk."""
        context = {
            "agent_isolation_level": 0.5,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert score < 0.2


class TestCrossAgentLeakAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_zero_isolation(self):
        """Test zero isolation is highest risk."""
        context = {
            "agent_isolation_level": 0.0,
            "inter_agent_messages_sanitized": False,
            "has_authorization_checks": False,
            "shared_state_access": ["state1", "state2", "state3"]
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert score >= 0.79

    def test_assess_no_sanitization_no_auth(self):
        """Test no sanitization and no auth is worst case."""
        context = {
            "agent_isolation_level": 0.0,
            "inter_agent_messages_sanitized": False,
            "has_authorization_checks": False,
            "shared_state_access": ["sensitive_data"]
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert score >= 0.73

    def test_assess_full_isolation_with_shared_state(self):
        """Test full isolation with shared state still has some risk."""
        context = {
            "agent_isolation_level": 1.0,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": ["state1", "state2", "state3"]
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        assert 0.0 <= score <= 0.4  # Some risk from shared state

    def test_assess_sensitive_shared_state_access(self):
        """Test sensitive shared state access increases risk."""
        context_base = {
            "agent_isolation_level": 0.5,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True
        }
        assessor = CrossAgentLeakAssessor()

        context_normal = {
            **context_base,
            "shared_state_access": ["state1", "state2"],
            "sensitive_shared_state_access": 0
        }
        context_sensitive = {
            **context_base,
            "shared_state_access": ["state1", "state2"],
            "sensitive_shared_state_access": 2
        }

        score_normal = assessor.assess(context_normal)
        score_sensitive = assessor.assess(context_sensitive)

        assert score_sensitive > score_normal

    def test_assess_many_shared_state_access(self):
        """Test many shared state accesses increase risk."""
        context = {
            "agent_isolation_level": 0.5,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"]
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context)
        # Should be elevated due to many shared state accesses
        assert score > 0.3


class TestCrossAgentLeakAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_all_isolation_levels(self):
        """Test all isolation levels."""
        context_base = {
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()

        scores = {}
        for level in [0.0, 0.25, 0.5, 0.75, 1.0]:
            context = {**context_base, "agent_isolation_level": level}
            scores[level] = assessor.assess(context)

        # Lower isolation should produce higher scores
        assert scores[0.0] > scores[1.0]
        assert scores[0.5] > scores[0.75]

    def test_assess_measure_shared_state_exposure_method(self):
        """Test _measure_shared_state_exposure method."""
        assessor = CrossAgentLeakAssessor()

        # No shared state = 0.0
        assert assessor._measure_shared_state_exposure({
            "shared_state_access": []
        }) == 0.0

        # Normal access = proportional to count
        score = assessor._measure_shared_state_exposure({
            "shared_state_access": ["s1", "s2", "s3"],
            "sensitive_shared_state_access": 0
        })
        assert 0.0 < score < 1.0

        # With sensitive access = higher
        score_sensitive = assessor._measure_shared_state_exposure({
            "shared_state_access": ["s1", "s2", "s3"],
            "sensitive_shared_state_access": 3
        })
        assert score_sensitive > score

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "agent_isolation_level": 0.7,
            "inter_agent_messages_sanitized": True,
            "has_authorization_checks": True,
            "shared_state_access": ["state1", "state2"]
        }
        assessor = CrossAgentLeakAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D6"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert len(result.evidence) >= 2
        assert isinstance(result.metadata, dict)
        assert "isolation_level" in result.metadata
        assert "shared_state_count" in result.metadata

    def test_assess_detailed_result_warns_low_isolation(self):
        """Test detailed result warns on low isolation."""
        context = {
            "agent_isolation_level": 0.3,
            "inter_agent_messages_sanitized": False,
            "has_authorization_checks": False,
            "shared_state_access": ["sensitive"]
        }
        assessor = CrossAgentLeakAssessor()
        result = assessor.assess_with_details(context)

        assert len(result.warnings) >= 3
        assert any("isolation" in w.lower() for w in result.warnings)

    def test_assess_isolation_only_factors(self):
        """Test that isolation is properly weighted."""
        # Perfect isolation, everything else bad
        context_perfect_isolation = {
            "agent_isolation_level": 1.0,
            "inter_agent_messages_sanitized": False,
            "has_authorization_checks": False,
            "shared_state_access": ["s1", "s2", "s3", "s4", "s5"]
        }
        assessor = CrossAgentLeakAssessor()
        score = assessor.assess(context_perfect_isolation)

        # Should still be moderate due to other factors
        assert score < 0.56

    def test_assess_no_messages_flag(self):
        """Test default when inter_agent_messages_sanitized not specified."""
        context = {
            "agent_isolation_level": 0.5,
            "has_authorization_checks": True,
            "shared_state_access": []
        }
        assessor = CrossAgentLeakAssessor()
        # Default should be True (sanitized)
        score = assessor.assess(context)
        assert score < 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
