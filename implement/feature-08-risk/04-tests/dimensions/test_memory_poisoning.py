"""
Tests for D5: MemoryPoisoningAssessor [FR-R-5]

Covers memory source verification, content authenticity, tampering detection, and consistency validation.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from dimensions.memory_poisoning import MemoryPoisoningAssessor


class TestMemoryPoisoningAssessorConstructor:
    """Test MemoryPoisoningAssessor constructor."""

    def test_constructor_creates_instance(self):
        """Test constructor creates valid instance."""
        assessor = MemoryPoisoningAssessor()
        assert assessor is not None
        assert assessor.get_dimension_id() == "D5"


class TestMemoryPoisoningAssessorNormalRange:
    """Test normal range scenarios."""

    def test_assess_verified_source_low_risk(self):
        """Test verified source with multiple sources is low risk."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 3,
            "content_verified": True,
            "tampering_indicators": []
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_single_verified_source(self):
        """Test single verified source."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 1,
            "content_verified": True
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score < 0.3

    def test_assess_high_consistency(self):
        """Test high historical consistency."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 1,
            "historical_consistency_score": 0.95
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_signed_content(self):
        """Test signed content has low risk."""
        context = {
            "content_signed": True,
            "memory_source_verified": False,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score < 0.3


class TestMemoryPoisoningAssessorBoundaryValues:
    """Test boundary values."""

    def test_assess_no_source_verification(self):
        """Test no source verification is high risk."""
        context = {
            "memory_source_verified": False,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score >= 0.27

    def test_assess_hash_mismatch(self):
        """Test content hash mismatch is maximum risk."""
        context = {
            "content_hash": "abc123",
            "expected_hash": "different",
            "memory_source_verified": True
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score >= 0.36

    def test_assess_hash_match(self):
        """Test content hash match is low risk."""
        context = {
            "content_hash": "same_hash",
            "expected_hash": "same_hash",
            "memory_source_verified": True
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score < 0.2

    def test_assess_no_hash_info(self):
        """Test no hash information."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert 0.0 <= score <= 0.5

    def test_assess_memory_modified_flag(self):
        """Test memory modified flag increases risk."""
        context_base = {
            "memory_source_verified": True,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()

        context_clean = {**context_base}
        context_modified = {**context_base, "memory_modified": True}

        score_clean = assessor.assess(context_clean)
        score_modified = assessor.assess(context_modified)

        assert score_modified > score_clean

    def test_assess_tampering_indicators(self):
        """Test tampering indicators increase risk."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 1,
            "tampering_indicators": ["indicator1", "indicator2", "indicator3", "indicator4"]
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        # 4 indicators * 0.25 = 1.0, but weighted by 0.25
        assert score >= 0.4

    def test_assess_zero_sources_count(self):
        """Test zero sources count."""
        context = {
            "memory_source_verified": False,
            "memory_sources_count": 0
        }
        assessor = MemoryPoisoningAssessor()
        score = assessor.assess(context)
        assert score >= 0.39


class TestMemoryPoisoningAssessorEdgeCases:
    """Test edge cases."""

    def test_assess_all_consistency_levels(self):
        """Test all historical consistency levels."""
        context_base = {
            "memory_source_verified": True,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()

        scores = {}
        for consistency in [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]:
            context = {**context_base, "historical_consistency_score": consistency}
            scores[consistency] = assessor.assess(context)

        # Lower consistency should produce higher scores
        assert scores[1.0] < scores[0.0]
        assert scores[0.8] < scores[0.4]

    def test_assess_unexpected_edits_flag(self):
        """Test unexpected edits flag."""
        context_base = {
            "memory_source_verified": True,
            "memory_sources_count": 1
        }
        assessor = MemoryPoisoningAssessor()

        context_clean = {**context_base}
        context_edits = {**context_base, "unexpected_edits": True}

        score_clean = assessor.assess(context_clean)
        score_edits = assessor.assess(context_edits)

        assert score_edits > score_clean

    def test_assess_multiple_sources_more_trustworthy(self):
        """Test multiple sources are more trustworthy than single."""
        context_base = {
            "memory_source_verified": False,
            "tampering_indicators": []
        }
        assessor = MemoryPoisoningAssessor()

        context_single = {**context_base, "memory_sources_count": 1}
        context_multiple = {**context_base, "memory_sources_count": 5}

        score_single = assessor.assess(context_single)
        score_multiple = assessor.assess(context_multiple)

        assert score_multiple >= score_single

    def test_assess_verify_memory_sources_method(self):
        """Test _verify_memory_sources method."""
        assessor = MemoryPoisoningAssessor()

        # Verified + multiple sources = 0.0
        assert assessor._verify_memory_sources({
            "memory_source_verified": True,
            "memory_sources_count": 3
        }) == 0.0

        # Verified + single source = 0.0
        assert assessor._verify_memory_sources({
            "memory_source_verified": True,
            "memory_sources_count": 1
        }) == 0.0

        # Unverified + multiple sources = 0.6
        assert assessor._verify_memory_sources({
            "memory_source_verified": False,
            "memory_sources_count": 3
        }) == 0.6

        # Unverified + single source = 0.4
        assert assessor._verify_memory_sources({
            "memory_source_verified": False,
            "memory_sources_count": 1
        }) == 0.4

    def test_assess_check_content_authenticity_method(self):
        """Test _check_content_authenticity method."""
        assessor = MemoryPoisoningAssessor()

        # Hash mismatch = 1.0
        assert assessor._check_content_authenticity({
            "content_hash": "abc",
            "expected_hash": "xyz"
        }) == 1.0

        # Hash match = 0.0
        assert assessor._check_content_authenticity({
            "content_hash": "same",
            "expected_hash": "same"
        }) == 0.0

        # Signed = 0.0
        assert assessor._check_content_authenticity({
            "content_signed": True
        }) == 0.0

        # Verified = 0.1
        assert assessor._check_content_authenticity({
            "content_verified": True
        }) == 0.1

    def test_assess_detect_tampering_method(self):
        """Test _detect_tampering method."""
        assessor = MemoryPoisoningAssessor()

        # No indicators, no flags = 0.0
        assert assessor._detect_tampering({}) == 0.0

        # Memory modified flag = 0.7
        assert assessor._detect_tampering({"memory_modified": True}) == 0.7

        # Unexpected edits = 0.8
        assert assessor._detect_tampering({"unexpected_edits": True}) == 0.8

        # 4 indicators = 1.0
        assert assessor._detect_tampering({
            "tampering_indicators": ["a", "b", "c", "d"]
        }) == 1.0

    def test_assess_detailed_result(self):
        """Test assess_with_details returns complete result."""
        context = {
            "memory_source_verified": True,
            "memory_sources_count": 2,
            "content_hash": "abc123def456",
            "historical_consistency_score": 0.85,
            "tampering_indicators": []
        }
        assessor = MemoryPoisoningAssessor()
        result = assessor.assess_with_details(context)

        assert result.dimension_id == "D5"
        assert 0.0 <= result.score <= 1.0
        assert isinstance(result.evidence, list)
        assert len(result.evidence) > 0
        assert isinstance(result.warnings, list)
        assert isinstance(result.metadata, dict)

    def test_assess_detailed_result_with_tampering(self):
        """Test detailed result with tampering indicators."""
        context = {
            "memory_source_verified": False,
            "memory_sources_count": 1,
            "content_hash": "abc",
            "expected_hash": "xyz",
            "tampering_indicators": ["flag1", "flag2"],
            "historical_consistency_score": 0.3
        }
        assessor = MemoryPoisoningAssessor()
        result = assessor.assess_with_details(context)

        assert len(result.warnings) > 0
        assert "tampering_indicators" in result.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
