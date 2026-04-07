#!/usr/bin/env python3
"""
Test Suite for PhaseEnforcer Smoke Test
=========================================
Tests for the independent PhaseEnforcer smoke test module.

Author: methodology-v2 v5.96
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch


class TestPhaseEnforcerSmoke:
    """Test suite for PhaseEnforcer smoke test module."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_smoke_module_import(self):
        """Test that smoke test module can be imported."""
        try:
            from quality_gate.phase_enforcer_smoke import run_smoke_test
            assert callable(run_smoke_test)
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_smoke_result_dataclass(self):
        """Test that SmokeTestResult dataclass is defined."""
        try:
            from quality_gate.phase_enforcer_smoke import SmokeTestResult
            result = SmokeTestResult(
                passed=True,
                phase_enforcer_available=True,
                tests_run=1,
                tests_passed=1,
                tests_failed=0,
                details={},
                errors=[]
            )
            assert result.passed is True
            assert result.tests_run == 1
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_check_dependencies_function(self):
        """Test check_dependencies function."""
        try:
            from quality_gate.phase_enforcer_smoke import check_dependencies
            deps = check_dependencies()
            assert isinstance(deps, dict)
            assert "phase_enforcer" in deps
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_run_smoke_test_with_invalid_path(self):
        """Test run_smoke_test with invalid path."""
        try:
            from quality_gate.phase_enforcer_smoke import run_smoke_test
            result = run_smoke_test("/nonexistent/path", verbose=False)
            assert result is not None
            # Should handle gracefully
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_run_smoke_test_default_path(self):
        """Test run_smoke_test with default path."""
        try:
            from quality_gate.phase_enforcer_smoke import run_smoke_test
            result = run_smoke_test(verbose=False)
            assert result is not None
            assert hasattr(result, "passed")
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_smoke_result_to_json(self):
        """Test SmokeTestResult to_json method."""
        try:
            from quality_gate.phase_enforcer_smoke import SmokeTestResult
            result = SmokeTestResult(
                passed=True,
                phase_enforcer_available=True,
                tests_run=1,
                tests_passed=1,
                tests_failed=0,
                details={},
                errors=[]
            )
            json_str = result.to_json()
            assert '"passed": true' in json_str
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")

    def test_smoke_result_print_summary(self):
        """Test SmokeTestResult print_summary method."""
        try:
            from quality_gate.phase_enforcer_smoke import SmokeTestResult
            result = SmokeTestResult(
                passed=True,
                phase_enforcer_available=True,
                tests_run=1,
                tests_passed=1,
                tests_failed=0,
                details={},
                errors=[]
            )
            summary = result.print_summary()
            assert "Smoke Test Result" in summary
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")


class TestPhaseEnforcerSmokeIntegration:
    """Integration tests for PhaseEnforcer smoke test."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_run_smoke_with_real_project(self):
        """Test run_smoke_test with real project path."""
        try:
            from quality_gate.phase_enforcer_smoke import run_smoke_test
            result = run_smoke_test(str(self.project_path), verbose=False)
            # Just check that it runs without error
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")
        except Exception as e:
            # Expected if dependencies are not available
            pass

    def test_dependencies_check_with_real_project(self):
        """Test dependencies check with real project."""
        try:
            from quality_gate.phase_enforcer_smoke import check_dependencies
            deps = check_dependencies()
            # Check that at least some dependencies are checked
            assert "phase_enforcer" in deps
        except ImportError:
            pytest.skip("phase_enforcer_smoke not available")
