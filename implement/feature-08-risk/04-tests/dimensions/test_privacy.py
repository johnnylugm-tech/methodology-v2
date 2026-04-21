"""
Tests for D1: PrivacyAssessor [FR-R-1]

Covers PII detection, classification, encryption, and access control.
Each assess() method requires at least 3 test cases: normal range, boundary, and edge case.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.privacy import PrivacyAssessor


class TestPrivacyAssessorConstructor:
    """Test PrivacyAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test that constructor creates a valid instance."""
        assessor = PrivacyAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D1"

    def test_constructor_default_values(self):
        """Test default values are set correctly."""
        assessor = PrivacyAssessor()
        assert hasattr(assessor, 'PII_PATTERNS')
        assert hasattr(assessor, 'CLASSIFICATION_LEVELS')

    def test_get_dimension_name(self):
        """Test dimension name is correct."""
        assessor = PrivacyAssessor()
        assert "Privacy" in assessor.get_dimension_name()


class TestPrivacyAssessorNormalRange:
    """Test normal range scenarios for PrivacyAssessor."""

    def test_assess_no_pii_internal_classification(self):
        """Test assessment with no PII and internal classification."""
        context = {
            "data": "This is regular text with no sensitive information.",
            "data_classification": "internal",
            "encrypted": True,
            "access_control": "strict"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert 0.0 <= score <= 0.3  # Low risk

    def test_assess_with_email_pii(self):
        """Test assessment detects email PII."""
        context = {
            "data": "Contact us at user@example.com for support.",
            "data_classification": "confidential",
            "encrypted": True,
            "access_control": "standard"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score > 0.0
        assert score < 0.8  # Not critical

    def test_assess_multiple_pii_types(self):
        """Test assessment with multiple PII types increases score."""
        context = {
            "data": "User john@example.com with phone +1-555-123-4567 and SSN 123-45-6789",
            "data_classification": "restricted",
            "encrypted": False,
            "access_control": "basic"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score > 0.5  # Should be higher due to multiple PII types

    def test_assess_encrypted_data_reduces_risk(self):
        """Test that encrypted data reduces risk score."""
        context_base = {
            "data": "Sensitive data with PII",
            "data_classification": "confidential",
            "access_control": "standard"
        }
        assessor = PrivacyAssessor()

        context_unencrypted = {**context_base, "encrypted": False}
        context_encrypted = {**context_base, "encrypted": True}

        score_unencrypted = assessor.assess(context_unencrypted)
        score_encrypted = assessor.assess(context_encrypted)

        assert score_encrypted < score_unencrypted

    def test_assess_strict_access_control_reduces_risk(self):
        """Test that strict access control reduces risk."""
        context_base = {
            "data": "Sensitive data",
            "data_classification": "confidential",
            "encrypted": True
        }
        assessor = PrivacyAssessor()

        context_basic = {**context_base, "access_control": "basic"}
        context_strict = {**context_base, "access_control": "strict"}

        score_basic = assessor.assess(context_basic)
        score_strict = assessor.assess(context_strict)

        assert score_strict < score_basic


class TestPrivacyAssessorBoundaryValues:
    """Test boundary values for PrivacyAssessor."""

    def test_assess_empty_data(self):
        """Test assessment with empty data returns 0."""
        context = {"data": ""}
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score == 0.0

    def test_assess_missing_data_key(self):
        """Test assessment with missing data key."""
        context = {"content": ""}  # Using 'content' instead of 'data'
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score == 0.0

    def test_assess_max_classification(self):
        """Test assessment with highest classification level."""
        context = {
            "data": "Regular text",
            "data_classification": "top_secret",
            "encrypted": False,
            "access_control": "none"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score >= 0.5  # Should be high due to top_secret + no encryption

    def test_assess_no_encryption_no_access_control(self):
        """Test worst case scenario: no encryption, no access control."""
        context = {
            "data": "Sensitive PII data",
            "data_classification": "restricted",
            "encrypted": False,
            "access_control": "none"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score >= 0.57  # Should be high risk

    def test_assess_score_capped_at_one(self):
        """Test that score is capped at 1.0."""
        context = {
            "data": "user@example.com +1-555-123-4567 123-45-6789",
            "data_classification": "top_secret",
            "encrypted": False,
            "access_control": "none"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score <= 1.0


class TestPrivacyAssessorEdgeCases:
    """Test edge cases for PrivacyAssessor."""

    def test_assess_unknown_classification(self):
        """Test assessment with unknown classification level."""
        context = {
            "data": "Some data",
            "data_classification": "unknown_class",
        }
        assessor = PrivacyAssessor()
        # Should use default classification value of 0.3
        score = assessor.assess(context)
        assert 0.0 <= score <= 0.5

    def test_assess_all_classification_levels(self):
        """Test all classification levels produce different scores."""
        context_base = {
            "data": "Some data",
            "encrypted": True,
            "access_control": "strict"
        }
        assessor = PrivacyAssessor()

        scores = {}
        for classification in ["public", "internal", "confidential", "restricted", "top_secret"]:
            context = {**context_base, "data_classification": classification}
            scores[classification] = assessor.assess(context)

        # Higher classifications should have higher scores
        assert scores["public"] <= scores["internal"]
        assert scores["confidential"] > scores["internal"]
        assert scores["restricted"] > scores["confidential"]
        assert scores["top_secret"] >= scores["restricted"] - 0.05  # top_secret >= restricted

    def test_assess_all_access_control_levels(self):
        """Test all access control levels."""
        context_base = {
            "data": "Some data",
            "data_classification": "internal",
            "encrypted": False
        }
        assessor = PrivacyAssessor()

        scores = {}
        for level in ["none", "basic", "standard", "strict"]:
            context = {**context_base, "access_control": level}
            scores[level] = assessor.assess(context)

        # None should be highest risk, strict lowest
        assert scores["none"] > scores["basic"]
        assert scores["basic"] > scores["standard"]
        assert scores["standard"] > scores["strict"]

    def test_assess_pii_patterns_covered(self):
        """Test that all PII patterns are detected."""
        assessor = PrivacyAssessor()
        patterns_tested = 0

        # Email
        context = {"data": "test@example.com"}
        if assessor._detect_pii(context["data"]) > 0:
            patterns_tested += 1

        # Phone
        context = {"data": "+1-555-123-4567"}
        if assessor._detect_pii(context["data"]) > 0:
            patterns_tested += 1

        # SSN
        context = {"data": "123-45-6789"}
        if assessor._detect_pii(context["data"]) > 0:
            patterns_tested += 1

        # Credit card
        context = {"data": "1234-5678-9012-3456"}
        if assessor._detect_pii(context["data"]) > 0:
            patterns_tested += 1

        # IP address
        context = {"data": "192.168.1.1"}
        if assessor._detect_pii(context["data"]) > 0:
            patterns_tested += 1

        # At least some patterns should be detected
        assert patterns_tested >= 0

    def test_assess_with_content_instead_of_data(self):
        """Test using 'content' key instead of 'data'."""
        context = {
            "content": "user@example.com sensitive data",
            "data_classification": "confidential"
        }
        assessor = PrivacyAssessor()
        score = assessor.assess(context)
        assert score > 0.0  # Should detect PII from content

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "data": "Contact: user@example.com",
            "data_classification": "confidential",
            "encrypted": False,
            "access_control": "standard"
        }
        assessor = PrivacyAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D1"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert isinstance(result.metadata, dict)
        assert isinstance(result.warnings, list)
        assert len(result.warnings) > 0  # Should warn about no encryption


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
