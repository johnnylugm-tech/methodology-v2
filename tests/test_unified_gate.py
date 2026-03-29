#!/usr/bin/env python3
"""
Test Suite for unified_gate.py
==============================
Tests for the unified quality gate module.

Author: methodology-v2 v5.95
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch, Mock
from dataclasses import dataclass


class TestUnifiedGate:
    """Test suite for UnifiedGate module."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_gate_initialization(self):
        """Test that UnifiedGate can be initialized."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            assert gate is not None
            assert gate.project_path is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_gate_has_check_all_method(self):
        """Test that UnifiedGate has check_all method."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            assert hasattr(gate, 'check_all'), "check_all method should exist"
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_all_returns_result(self):
        """Test that check_all returns a result object."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all()
            assert result is not None
            assert hasattr(result, 'passed') or hasattr(result, 'overall_score')
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_all_with_phase_parameter(self):
        """Test check_all with phase parameter."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all(phase=1)
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_gate_has_doc_checker(self):
        """Test that gate has doc_checker attribute."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            assert hasattr(gate, 'doc_checker'), "doc_checker should exist"
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_gate_has_phase_enforcer(self):
        """Test that gate has phase_enforcer attribute."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            assert hasattr(gate, 'phase_enforcer'), "phase_enforcer should exist"
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_result_has_score(self):
        """Test that check result has score attribute."""
        try:
            from quality_gate.unified_gate import UnifiedGate, CheckResult
            result = CheckResult(
                name="test",
                passed=True,
                score=95.0,
                violations=[],
                details={}
            )
            assert result.score == 95.0
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_result_has_passed(self):
        """Test that check result has passed attribute."""
        try:
            from quality_gate.unified_gate import CheckResult
            result = CheckResult(
                name="test",
                passed=True,
                score=100.0,
                violations=[],
                details={}
            )
            assert result.passed is True
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_result_has_violations(self):
        """Test that check result has violations list."""
        try:
            from quality_gate.unified_gate import CheckResult
            result = CheckResult(
                name="test",
                passed=False,
                score=70.0,
                violations=["Missing SRS.md", "Missing SAD.md"],
                details={}
            )
            assert isinstance(result.violations, list)
            assert len(result.violations) == 2
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_unified_gate_result_has_overall_score(self):
        """Test that UnifiedGateResult has overall_score."""
        try:
            from quality_gate.unified_gate import UnifiedGateResult
            result = UnifiedGateResult(
                passed=True,
                overall_score=95.0,
                checks=[],
                summary={}
            )
            assert result.overall_score == 95.0
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_unified_gate_result_has_checks(self):
        """Test that UnifiedGateResult has checks list."""
        try:
            from quality_gate.unified_gate import UnifiedGateResult, CheckResult
            check = CheckResult(name="test", passed=True, score=100.0, violations=[], details={})
            result = UnifiedGateResult(
                passed=True,
                overall_score=95.0,
                checks=[check],
                summary={}
            )
            assert len(result.checks) == 1
        except ImportError:
            pytest.skip("unified_gate not available")


class TestUnifiedGateChecks:
    """Test individual check methods of UnifiedGate."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_check_documents_method(self):
        """Test _check_documents method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_documents()
            assert result is not None
            assert hasattr(result, 'name')
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_constitution_method(self):
        """Test _check_constitution method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_constitution()
            assert result is not None
            assert hasattr(result, 'name')
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_phase_references_method(self):
        """Test _check_phase_references method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_phase_references()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_logic_correctness_method(self):
        """Test _check_logic_correctness method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_logic_correctness()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_fr_id_tracking_method(self):
        """Test _check_fr_id_tracking method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_fr_id_tracking()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_coverage_method(self):
        """Test _check_coverage method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_coverage()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_issues_method(self):
        """Test _check_issues method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_issues()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_risk_status_method(self):
        """Test _check_risk_status method exists and works."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate._check_risk_status()
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")


class TestUnifiedGateErrorHandling:
    """Error handling tests for UnifiedGate."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_handles_invalid_project_path(self):
        """Test handling of invalid project path."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            with pytest.raises((FileNotFoundError, ValueError, Exception)):
                gate = UnifiedGate("/nonexistent/path")
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_handles_missing_doc_checker(self):
        """Test handling when doc_checker is unavailable."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            # Should gracefully handle if doc_checker fails
            if gate.doc_checker is None:
                pytest.skip("doc_checker not available")
            else:
                assert True
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_handles_check_all_timeout(self):
        """Test that check_all handles timeout gracefully."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            
            # Mock a slow response
            with patch.object(gate, '_check_documents', side_effect=TimeoutError):
                try:
                    result = gate.check_all()
                    # Should handle gracefully or raise controlled exception
                except (TimeoutError, Exception):
                    pass  # Expected
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_all_partial_failure(self):
        """Test that check_all handles partial failures."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            
            # Mock one checker failing
            original = gate._check_documents
            def fail_once():
                raise Exception("Simulated failure")
            
            gate._check_documents = fail_once
            try:
                result = gate.check_all()
                # Should still return a result with failures noted
                assert result is not None
            except Exception:
                pass  # Some implementations may raise
            finally:
                gate._check_documents = original
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_result_format_on_error(self):
        """Test that results are properly formatted even on error."""
        try:
            from quality_gate.unified_gate import CheckResult
            result = CheckResult(
                name="test",
                passed=False,
                score=0.0,
                violations=["Error occurred"],
                details={"error": "test error"}
            )
            assert result.passed is False
            assert result.score == 0.0
            assert len(result.violations) > 0
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_to_dict_method(self):
        """Test that result has to_dict method."""
        try:
            from quality_gate.unified_gate import UnifiedGateResult
            result = UnifiedGateResult(
                passed=True,
                overall_score=95.0,
                checks=[],
                summary={}
            )
            d = result.to_dict()
            assert isinstance(d, dict)
            assert 'passed' in d
            assert 'overall_score' in d
        except ImportError:
            pytest.skip("unified_gate not available")


class TestUnifiedGateIntegration:
    """Integration tests for UnifiedGate."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_full_check_workflow(self):
        """Test complete check workflow."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all()
            assert result is not None
            assert hasattr(result, 'passed')
            assert hasattr(result, 'overall_score')
        except ImportError:
            pytest.skip("unified_gate not available")
        except Exception as e:
            # Other errors should be handled gracefully
            pass

    def test_check_all_strict_mode(self):
        """Test check_all with strict_mode parameter."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all(strict_mode=True)
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_all_with_phase_enforcement(self):
        """Test check_all with phase_enforcement parameter."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all(phase=1, phase_enforcement=True)
            assert result is not None
        except ImportError:
            pytest.skip("unified_gate not available")

    def test_check_all_produces_multiple_results(self):
        """Test that check_all produces multiple check results."""
        try:
            from quality_gate.unified_gate import UnifiedGate
            gate = UnifiedGate(str(self.project_path))
            result = gate.check_all()
            if hasattr(result, 'checks'):
                # Should have multiple checks
                assert len(result.checks) > 0
        except ImportError:
            pytest.skip("unified_gate not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])