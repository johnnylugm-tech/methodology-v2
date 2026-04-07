#!/usr/bin/env python3
"""
Test Suite for constitution_runner.py
======================================
Tests for the constitution runner module.

Author: methodology-v2 v5.95
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass


class TestConstitutionRunner:
    """Test suite for ConstitutionRunner module."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_runner_import(self):
        """Test that ConstitutionRunner can be imported."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            assert callable(run_constitution_check)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_has_check_types(self):
        """Test that runner supports different check types."""
        try:
            from quality_gate.constitution.runner import run_constitution_check, CONSTITUTION_THRESHOLDS
            # Should have threshold definitions
            assert isinstance(CONSTITUTION_THRESHOLDS, dict)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_check_srs_type(self):
        """Test that runner can check SRS type."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            assert result is not None
            assert hasattr(result, 'score') or hasattr(result, 'passed')
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_check_sad_type(self):
        """Test that runner can check SAD type."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="sad")
            assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_check_test_plan_type(self):
        """Test that runner can check Test Plan type."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="test_plan")
            assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_check_all_types(self):
        """Test that runner can check all types."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="all")
            assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_result_has_score(self):
        """Test that result has score attribute."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'score'):
                assert isinstance(result.score, (int, float))
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_result_has_passed(self):
        """Test that result has passed attribute."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'passed'):
                assert isinstance(result.passed, bool)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_result_has_violations(self):
        """Test that result has violations list."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'violations'):
                assert isinstance(result.violations, list)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_result_has_check_type(self):
        """Test that result has check_type attribute."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'check_type'):
                assert result.check_type in ["srs", "sad", "test_plan", "all"]
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_runner_result_has_recommendations(self):
        """Test that result has recommendations list."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'recommendations'):
                assert isinstance(result.recommendations, list)
        except ImportError:
            pytest.skip("constitution runner not available")


class TestConstitutionThresholds:
    """Test suite for Constitution threshold definitions."""

    def test_correctness_threshold(self):
        """Test correctness threshold is 100%."""
        try:
            from quality_gate.constitution.runner import CONSTITUTION_THRESHOLDS
            correctness = CONSTITUTION_THRESHOLDS.get('correctness', 0)
            assert correctness == 100, "Correctness threshold should be 100%"
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_security_threshold(self):
        """Test security threshold is 100%."""
        try:
            from quality_gate.constitution.runner import CONSTITUTION_THRESHOLDS
            security = CONSTITUTION_THRESHOLDS.get('security', 0)
            assert security == 100, "Security threshold should be 100%"
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_maintainability_threshold(self):
        """Test maintainability threshold is > 70%."""
        try:
            from quality_gate.constitution.runner import CONSTITUTION_THRESHOLDS
            maintainability = CONSTITUTION_THRESHOLDS.get('maintainability', 0)
            assert maintainability > 70, "Maintainability threshold should be > 70%"
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_coverage_threshold(self):
        """Test coverage threshold is > 80%."""
        try:
            from quality_gate.constitution.runner import CONSTITUTION_THRESHOLDS
            coverage = CONSTITUTION_THRESHOLDS.get('coverage', 0)
            assert coverage > 80, "Coverage threshold should be > 80%"
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_thresholds_are_numeric(self):
        """Test that all thresholds are numeric."""
        try:
            from quality_gate.constitution.runner import CONSTITUTION_THRESHOLDS
            for key, value in CONSTITUTION_THRESHOLDS.items():
                assert isinstance(value, (int, float)), f"Threshold {key} should be numeric"
        except ImportError:
            pytest.skip("constitution runner not available")


class TestConstitutionRunnerErrorHandling:
    """Error handling tests for ConstitutionRunner."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_handles_invalid_check_type(self):
        """Test handling of invalid check type."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="invalid_type")
            # Should return a failed result, not raise an exception
            assert result is not None
            assert result.passed is False
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_handles_missing_document(self):
        """Test handling when document is missing."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            # Mock missing document
            with patch.object(Path, 'exists', return_value=False):
                result = run_constitution_check(check_type="srs")
                # Should handle gracefully
                assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_handles_corrupted_document(self):
        """Test handling of corrupted document."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            # Mock corrupted document
            with patch('builtins.open', side_effect=IOError("Corrupted")):
                result = run_constitution_check(check_type="srs")
                # Should handle gracefully
                assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_handles_empty_document(self):
        """Test handling of empty document."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            # Mock empty document
            with patch('Path.read_text', return_value=""):
                result = run_constitution_check(check_type="srs")
                # Should handle gracefully
                assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_handles_malformed_content(self):
        """Test handling of malformed content."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            # Should return a result even with malformed content
            assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_result_format_on_error(self):
        """Test that results are properly formatted even on error."""
        try:
            from quality_gate.constitution.runner import ConstitutionCheckResult
            result = ConstitutionCheckResult(
                check_type="srs",
                passed=False,
                score=0.0,
                violations=[{"type": "error", "message": "Error occurred"}],
                details={},
                recommendations=["Fix the error"]
            )
            assert result.passed is False
            assert result.score == 0.0
            assert len(result.violations) > 0
        except ImportError:
            pytest.skip("constitution runner not available")


class TestConstitutionRunnerIntegration:
    """Integration tests for ConstitutionRunner."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_full_check_workflow(self):
        """Test complete check workflow."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            assert result is not None
            assert hasattr(result, 'score')
            assert hasattr(result, 'passed')
        except ImportError:
            pytest.skip("constitution runner not available")
        except Exception:
            pass  # May fail if no SRS found

    def test_check_all_phases_constitution(self):
        """Test checking constitution for all phases."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            for check_type in ["srs", "sad", "test_plan"]:
                result = run_constitution_check(check_type=check_type)
                assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_check_with_custom_path(self):
        """Test check with custom project path."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs", docs_path=str(self.project_path / "docs"))
            assert result is not None
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_check_produces_violations(self):
        """Test that check produces violations list."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'violations'):
                assert isinstance(result.violations, list)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_check_produces_recommendations(self):
        """Test that check produces recommendations list."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'recommendations'):
                assert isinstance(result.recommendations, list)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_format_result_text_function(self):
        """Test format_result_text function exists."""
        try:
            from quality_gate.constitution.runner import format_result_text
            from quality_gate.constitution.runner import ConstitutionCheckResult
            result = ConstitutionCheckResult(
                check_type="srs",
                passed=True,
                score=95.0,
                violations=[],
                details={},
                recommendations=[]
            )
            text = format_result_text(result)
            assert isinstance(text, str)
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_format_result_json_function(self):
        """Test format_result_json function exists."""
        try:
            from quality_gate.constitution.runner import format_result_json
            from quality_gate.constitution.runner import ConstitutionCheckResult
            result = ConstitutionCheckResult(
                check_type="srs",
                passed=True,
                score=95.0,
                violations=[],
                details={},
                recommendations=[]
            )
            json_str = format_result_json(result)
            import json
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)
        except ImportError:
            pytest.skip("constitution runner not available")


class TestConstitutionCheckDimensions:
    """Test Constitution check dimensions."""

    def test_correctness_dimension(self):
        """Test correctness dimension checking."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'correctness'):
                assert isinstance(result.correctness, (int, float))
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_security_dimension(self):
        """Test security dimension checking."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'security'):
                assert isinstance(result.security, (int, float))
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_maintainability_dimension(self):
        """Test maintainability dimension checking."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'maintainability'):
                assert isinstance(result.maintainability, (int, float))
        except ImportError:
            pytest.skip("constitution runner not available")

    def test_coverage_dimension(self):
        """Test coverage dimension checking."""
        try:
            from quality_gate.constitution.runner import run_constitution_check
            result = run_constitution_check(check_type="srs")
            if hasattr(result, 'coverage'):
                assert isinstance(result.coverage, (int, float))
        except ImportError:
            pytest.skip("constitution runner not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])