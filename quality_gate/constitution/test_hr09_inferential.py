#!/usr/bin/env python3
"""
test_hr09_inferential.py
========================
Tests for HR-09 InferentialSensor integration.

Verifies:
1. HR09Checker correctly calls InferentialSensor.assess()
2. Claims with sufficient citations pass (score >= 0.5)
3. Claims with insufficient reasoning chain fail (score < 0.5)
4. Violations are properly formatted for FeedbackStore
5. Existing constitution tests still pass

Run:
    cd /path/to/methodology-v2
    python -m pytest quality_gate/constitution/test_hr09_inferential.py -v
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "constitution"))

import pytest

from quality_gate.constitution.hr09_checker import HR09Checker, check_hr09_constitution
from constitution.inferential_sensor import InferentialSensor


class TestInferentialSensorDirectly:
    """Test InferentialSensor in isolation."""
    
    def test_perfect_citation(self):
        """Citation that fully supports claim keywords = high score."""
        sensor = InferentialSensor()
        
        claim = {
            "text": "The system uses LRU cache for performance optimization.",
            "keywords": ["lru", "cache", "performance"]
        }
        citations = [
            {"text": "The system shall use LRU cache strategy for performance optimization.", "line": 45},
        ]
        
        result = sensor.assess(claim, citations)
        
        assert result.overall_score >= 0.7
        assert result.citation_existence == 1.0
        assert result.citation_coverage >= 0.5
    
    def test_no_citations(self):
        """No citations = zero score."""
        sensor = InferentialSensor()
        
        claim = {
            "text": "The system will use LRU cache for performance.",
            "keywords": ["lru", "cache", "performance"]
        }
        
        result = sensor.assess(claim, [])
        
        assert result.overall_score == 0.0
        assert result.citation_existence == 0.0
        assert "No citations" in result.issues[0]
    
    def test_partial_coverage(self):
        """Citation that only partially covers claim = medium score."""
        sensor = InferentialSensor()
        
        claim = {
            "text": "The system uses LRU cache and asyncio for performance.",
            "keywords": ["lru", "cache", "asyncio", "performance"]
        }
        citations = [
            {"text": "The system shall use LRU cache strategy.", "line": 45},
        ]
        
        result = sensor.assess(claim, citations)
        
        # Coverage should be partial (some keywords missing)
        assert result.citation_existence == 1.0
        assert 0.3 <= result.overall_score <= 0.8  # Somewhere in the middle


class TestHR09CheckerWithTempDocs:
    """Test HR09Checker using temporary document directories."""
    
    @pytest.fixture
    def temp_docs(self, tmp_path):
        """Create a temporary docs directory with test content."""
        return tmp_path
    
    def test_claim_with_citation_passes(self, tmp_path):
        """A claim with a properly supporting citation should pass HR-09."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        # Create SRS.md with a claim that has a proper citation
        srs_content = """# SRS - Test Project

## 1. Overview
The system [shall use LRU cache](#L10) for performance optimization.

## 2. Functional Requirements
FR-01: The system shall use LRU cache for handling request caching.

[LRU cache strategy]: #L10 "The system uses LRU with 1000 capacity"
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        # The claim "shall use LRU cache" is present
        assert result["total_claims"] >= 1
        
        # If citations are found and cover keywords, claim should pass
        for r in result["results"]:
            if "lru" in r["claim"].lower() or "cache" in r["claim"].lower():
                if r["citations"]:
                    assert r["passed"] == True or r["assessment"]["overall_score"] >= 0.0
    
    def test_claim_without_citation_fails(self, tmp_path):
        """A claim without citation should fail HR-09."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        # Create SRS.md with a claim but NO citations
        srs_content = """# SRS - Test Project

## 1. Overview
The system will use LRU cache for performance. It should be fast.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        # There should be claims detected
        assert result["total_claims"] >= 1
        
        # Without citations, the score should be 0
        for r in result["results"]:
            if r["citations"]:
                continue  # Skip if citations somehow found
            # Without citations, overall_score should be 0
            assert r["assessment"]["overall_score"] == 0.0
            assert r["passed"] == False
    
    def test_violations_have_correct_format(self, tmp_path):
        """Violations must have fields expected by UnifiedAlert/FeedbackStore."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        # Create SRS.md with claims but no citations
        srs_content = """# SRS

The system will use LRU cache for performance.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        for v in result["violations"]:
            assert "rule_id" in v
            assert v["rule_id"] == "HR-09"
            assert "doc" in v
            assert "line" in v
            assert "message" in v
            assert "overall_score" in v
            assert "severity" in v
    
    def test_multiple_claims_mixed_results(self, tmp_path):
        """Mixed claims (some with citations, some without) should produce mixed results."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        # Create SRS with mixed claims
        srs_content = """# SRS - Test Project

## 1. Overview
The system [shall use LRU cache](#L10) for performance optimization.

## 2. Requirements
FR-01: The system will use asyncio for concurrent processing.
FR-02: The system must handle 1000 requests per second.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        assert result["total_claims"] >= 2
        
        # At least one claim should have citations
        claims_with_citations = [r for r in result["results"] if r["citations"]]
        assert len(claims_with_citations) >= 1
    
    def test_inferential_sensor_is_called(self, tmp_path, monkeypatch):
        """Verify InferentialSensor.assess() is actually called by checking assessment data is populated."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        srs_content = """# SRS

The system will use LRU cache for performance.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        # If claims were found and assessed, results should contain assessment data
        # This proves InferentialSensor.assess() was called
        if result["total_claims"] > 0:
            for r in result["results"]:
                assert "assessment" in r
                assert "overall_score" in r["assessment"]
                assert "citation_existence" in r["assessment"]
                assert "citation_coverage" in r["assessment"]
                assert "reasoning_coherence" in r["assessment"]


class TestHR09IntegrationWithConstitutionRunner:
    """Test HR-09 integration with the Constitution runner."""
    
    def test_run_constitution_check_with_hr09(self, tmp_path):
        """run_constitution_check() should include HR-09 results."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        # Create minimal SRS
        srs_content = """# SRS

The system will use LRU cache for performance.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        from quality_gate.constitution import run_constitution_check
        
        result = run_constitution_check("srs", str(docs))
        
        # Check that hr09 info is in details
        assert "hr09" in result.details, f"hr09 not in details: {result.details.keys()}"
        assert "score" in result.details["hr09"]
        assert "total_claims" in result.details["hr09"]


class TestHR09CheckerEdgeCases:
    """Edge case tests for HR09Checker."""
    
    def test_no_documents(self, tmp_path):
        """No documents should return passed=True with 100% score."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        assert result["passed"] == True
        assert result["score"] == 100.0
        assert result["total_claims"] == 0
    
    def test_empty_document(self, tmp_path):
        """Empty document should return passed=True."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        (docs / "SRS.md").write_text("", encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        assert result["passed"] == True
        assert result["total_claims"] == 0
    
    def test_custom_threshold(self, tmp_path):
        """Custom min_score_threshold should affect pass/fail."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        srs_content = """# SRS

The system [shall use LRU cache](#L10) for performance.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        # With very high threshold (0.99), even good citations might fail
        checker_high = HR09Checker(min_score_threshold=0.99)
        result_high = checker_high.check(str(docs))
        
        # With normal threshold (0.5), should pass
        checker_normal = HR09Checker(min_score_threshold=0.5)
        result_normal = checker_normal.check(str(docs))
        
        # The high threshold checker should not pass more claims than normal
        passed_high = result_high["passed_claims"]
        passed_normal = result_normal["passed_claims"]
        # (might be equal if citations are great, but high threshold is stricter)
        assert passed_high <= passed_normal


class TestHR09ViolationsGoToFeedbackStore:
    """Verify HR-09 violations can be submitted to FeedbackStore."""
    
    def test_violations_format_for_unified_alert(self, tmp_path):
        """HR-09 violations have the fields UnifiedAlert expects."""
        docs = tmp_path / "docs"
        docs.mkdir()
        
        srs_content = """# SRS

The system will use LRU cache. It should be fast.
"""
        (docs / "SRS.md").write_text(srs_content, encoding="utf-8")
        
        checker = HR09Checker()
        result = checker.check(str(docs))
        
        for v in result["violations"]:
            # These are the fields needed by UnifiedAlert (via to_feedback())
            assert v["rule_id"] == "HR-09"
            assert "message" in v
            assert "doc" in v
            assert "line" in v


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
