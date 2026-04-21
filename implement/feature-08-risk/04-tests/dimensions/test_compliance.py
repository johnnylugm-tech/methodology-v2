"""
Tests for D8: ComplianceAssessor [FR-R-8]

Covers regulatory alignment, policy violations, audit trail, and data residency.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.compliance import ComplianceAssessor


class TestComplianceAssessorConstructor:
    """Test ComplianceAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = ComplianceAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D8"

    def test_constructor_has_regulatory_frameworks(self):
        """Test constructor initializes regulatory frameworks."""
        assessor = ComplianceAssessor()
        assert hasattr(assessor, 'REGULATORY_FRAMEWORKS')
        assert "GDPR" in assessor.REGULATORY_FRAMEWORKS
        assert "CCPA" in assessor.REGULATORY_FRAMEWORKS
        assert "HIPAA" in assessor.REGULATORY_FRAMEWORKS


class TestComplianceAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_full_regulatory_alignment(self):
        """Test full regulatory alignment is low risk."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [],
            "audit_trail_completeness": 1.0,
            "required_data_regions": []
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score == 0.0

    def test_assess_no_violations(self):
        """Test no policy violations."""
        context = {
            "regulatory_alignment_score": 0.9,
            "policy_violations": [],
            "audit_trail_completeness": 0.9,
            "required_data_regions": []
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_complete_audit_trail(self):
        """Test complete audit trail."""
        context = {
            "regulatory_alignment_score": 0.9,
            "policy_violations": [],
            "audit_trail_completeness": 1.0,
            "required_data_regions": []
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score < 0.15

    def test_assess_compliant_data_residency(self):
        """Test compliant data residency."""
        context = {
            "regulatory_alignment_score": 0.9,
            "policy_violations": [],
            "audit_trail_completeness": 0.9,
            "required_data_regions": ["US", "EU"],
            "data_region": "US"
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score < 0.2


class TestComplianceAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_zero_regulatory_alignment(self):
        """Test zero regulatory alignment is high risk."""
        context = {
            "regulatory_alignment_score": 0.0,
            "policy_violations": [],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.3

    def test_assess_zero_audit_trail(self):
        """Test zero audit trail completeness is high risk."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [],
            "audit_trail_completeness": 0.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.15

    def test_assess_critical_violation(self):
        """Test critical policy violation."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [{"severity": "critical", "description": "GDPR breach"}],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.3

    def test_assess_high_violation(self):
        """Test high severity policy violation."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [{"severity": "high", "description": "Policy breach"}],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.21

    def test_assess_medium_violation(self):
        """Test medium severity policy violation."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [{"severity": "medium", "description": "Minor violation"}],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert 0.1 <= score <= 0.15

    def test_assess_low_violation(self):
        """Test low severity policy violation."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [{"severity": "low", "description": "Trivial issue"}],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert 0.05 <= score <= 0.07

    def test_assess_multiple_violations(self):
        """Test multiple policy violations."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [
                {"severity": "high", "description": "Issue 1"},
                {"severity": "medium", "description": "Issue 2"},
                {"severity": "low", "description": "Issue 3"}
            ],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.3

    def test_assess_unknown_severity_violation(self):
        """Test unknown severity policy violation."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [{"severity": "unknown", "description": "Unknown issue"}],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        # Should use default severity weight of 0.3
        assert 0.08 <= score <= 0.1


class TestComplianceAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_no_residency_requirements(self):
        """Test no data residency requirements."""
        context = {
            "regulatory_alignment_score": 0.5,
            "policy_violations": [],
            "audit_trail_completeness": 0.5,
            "required_data_regions": []
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        # No residency requirements = no residency risk
        assert 0.0 <= score <= 0.5

    def test_assess_non_compliant_residency(self):
        """Test non-compliant data region without transfer compliance."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [],
            "audit_trail_completeness": 1.0,
            "required_data_regions": ["US", "EU"],
            "data_region": "RU",
            "cross_border_transfer_compliant": False
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        assert score >= 0.12

    def test_assess_non_compliant_with_transfer_compliance(self):
        """Test non-compliant region with cross-border transfer compliance."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [],
            "audit_trail_completeness": 1.0,
            "required_data_regions": ["US", "EU"],
            "data_region": "RU",
            "cross_border_transfer_compliant": True
        }
        assessor = ComplianceAssessor()
        score = assessor.assess(context)
        # Should be lower than non-compliant without transfer
        assert 0.04 <= score <= 0.05

    def test_assess_detect_policy_violations_method(self):
        """Test _detect_policy_violations method."""
        assessor = ComplianceAssessor()

        # No violations = 0.0
        assert assessor._detect_policy_violations({"policy_violations": []}) == 0.0

        # Critical = 1.0
        assert assessor._detect_policy_violations({
            "policy_violations": [{"severity": "critical"}]
        }) == 1.0

        # High = 0.7
        assert assessor._detect_policy_violations({
            "policy_violations": [{"severity": "high"}]
        }) == 0.7

        # Multiple violations capped at 1.0
        assert assessor._detect_policy_violations({
            "policy_violations": [
                {"severity": "critical"},
                {"severity": "critical"},
                {"severity": "critical"}
            ]
        }) == 1.0

    def test_assess_check_data_residency_requirements_method(self):
        """Test _check_data_residency_requirements method."""
        assessor = ComplianceAssessor()

        # No requirements = 0.0
        assert assessor._check_data_residency_requirements({
            "required_data_regions": []
        }) == 0.0

        # Compliant region = 0.0
        assert assessor._check_data_residency_requirements({
            "required_data_regions": ["US", "EU"],
            "data_region": "US"
        }) == 0.0

        # Non-compliant with transfer compliance = 0.3
        assert assessor._check_data_residency_requirements({
            "required_data_regions": ["US", "EU"],
            "data_region": "RU",
            "cross_border_transfer_compliant": True
        }) == 0.3

        # Non-compliant without transfer = 0.8
        assert assessor._check_data_residency_requirements({
            "required_data_regions": ["US", "EU"],
            "data_region": "RU",
            "cross_border_transfer_compliant": False
        }) == 0.8

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "regulatory_alignment_score": 0.85,
            "policy_violations": [
                {"severity": "medium", "description": "Issue 1"}
            ],
            "audit_trail_completeness": 0.9,
            "required_data_regions": ["US"],
            "data_region": "US",
            "applicable_frameworks": ["GDPR", "SOC2"]
        }
        assessor = ComplianceAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D8"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert len(result.evidence) >= 3
        assert isinstance(result.metadata, dict)
        assert "violation_count" in result.metadata
        assert "regulatory_frameworks" in result.metadata

    def test_assess_detailed_result_warns_on_violations(self):
        """Test detailed result warns on policy violations."""
        context = {
            "regulatory_alignment_score": 1.0,
            "policy_violations": [
                {"severity": "high", "description": "Issue 1"},
                {"severity": "medium", "description": "Issue 2"}
            ],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()
        result = assessor.assess_with_details(context)

        assert len(result.warnings) > 0
        assert "Policy violations: 2" in result.warnings

    def test_assess_all_alignment_scores(self):
        """Test all regulatory alignment scores."""
        context_base = {
            "policy_violations": [],
            "audit_trail_completeness": 1.0
        }
        assessor = ComplianceAssessor()

        scores = {}
        for alignment in [0.0, 0.3, 0.5, 0.7, 1.0]:
            context = {**context_base, "regulatory_alignment_score": alignment}
            scores[alignment] = assessor.assess(context)

        # Higher alignment should produce lower scores
        assert scores[0.0] > scores[1.0]
        assert scores[0.5] > scores[0.7]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
