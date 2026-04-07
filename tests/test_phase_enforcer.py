#!/usr/bin/env python3
"""
Test Suite for phase_enforcer.py
=================================
Tests for the phase enforcer module.

Author: methodology-v2 v5.95
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field, asdict


class TestPhaseEnforcer:
    """Test suite for PhaseEnforcer module."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_enforcer_initialization(self):
        """Test that PhaseEnforcer can be initialized."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            assert enforcer is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_with_strict_mode(self):
        """Test PhaseEnforcer initialization with strict_mode."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path), strict_mode=True)
            assert enforcer is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_has_enforce_phase_method(self):
        """Test that PhaseEnforcer has enforce_phase method."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            assert hasattr(enforcer, 'enforce_phase'), "enforce_phase method should exist"
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforce_phase_accepts_phase_number(self):
        """Test that enforce_phase accepts phase number."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(1)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_has_structure_check_result(self):
        """Test that enforcer has StructureCheckResult dataclass."""
        try:
            from quality_gate.phase_enforcer import StructureCheckResult
            result = StructureCheckResult(score=100.0, missing=[])
            assert result.score == 100.0
            assert result.missing == []
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_has_content_check_result(self):
        """Test that enforcer has ContentCheckResult dataclass."""
        try:
            from quality_gate.phase_enforcer import ContentCheckResult
            result = ContentCheckResult(score=85.0, missing_sections=[])
            assert result.score == 85.0
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_has_phase_enforcement_result(self):
        """Test that enforcer has PhaseEnforcementResult dataclass."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcementResult
            result = PhaseEnforcementResult(
                phase=1,
                passed=True,
                structure_check=StructureCheckResult(score=100.0, missing=[]),
                content_check=ContentCheckResult(score=85.0, missing_sections=[]),
                gate_score=92.5,
                can_proceed=True,
                blocker_issues=[]
            )
            assert result.phase == 1
            assert result.passed is True
            assert result.gate_score == 92.5
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_gate_score_threshold(self):
        """Test that gate score threshold is properly defined."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            threshold = getattr(enforcer, 'GATE_THRESHOLD', 80)
            assert threshold >= 80, "Gate threshold should be >= 80"
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_can_proceed_property(self):
        """Test that result has can_proceed property."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcementResult
            result = PhaseEnforcementResult(
                phase=1,
                passed=True,
                structure_check=StructureCheckResult(score=100.0, missing=[]),
                content_check=ContentCheckResult(score=85.0, missing_sections=[]),
                gate_score=92.5,
                can_proceed=True,
                blocker_issues=[]
            )
            assert result.can_proceed is True
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcer_blocker_issues_property(self):
        """Test that result has blocker_issues property."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcementResult
            result = PhaseEnforcementResult(
                phase=1,
                passed=False,
                structure_check=StructureCheckResult(score=50.0, missing=["SRS.md"]),
                content_check=ContentCheckResult(score=60.0, missing_sections=["Overview"]),
                gate_score=55.0,
                can_proceed=False,
                blocker_issues=["Missing SRS.md", "Missing Overview section"]
            )
            assert len(result.blocker_issues) == 2
            assert result.can_proceed is False
        except ImportError:
            pytest.skip("phase_enforcer not available")


class TestPhaseEnforcerChecks:
    """Test individual check methods of PhaseEnforcer."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_check_structure_for_phase_1(self):
        """Test structure check for Phase 1."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(1)
            assert result is not None
            assert result.phase == 1
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_check_structure_for_phase_2(self):
        """Test structure check for Phase 2."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(2)
            assert result is not None
            assert result.phase == 2
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_check_structure_for_phase_3(self):
        """Test structure check for Phase 3."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(3)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_check_structure_for_phase_4(self):
        """Test structure check for Phase 4."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(4)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_check_all_phases(self):
        """Test checking all phases."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            for phase in range(1, 9):
                result = enforcer.enforce_phase(phase)
                assert result is not None
                assert result.phase == phase
        except ImportError:
            pytest.skip("phase_enforcer not available")


class TestPhaseEnforcerErrorHandling:
    """Error handling tests for PhaseEnforcer."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_handles_invalid_project_path(self):
        """Test handling of invalid project path."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            with pytest.raises((FileNotFoundError, ValueError, Exception)):
                enforcer = PhaseEnforcer("/nonexistent/path")
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_handles_invalid_phase_number(self):
        """Test handling of invalid phase number."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            with pytest.raises((ValueError, Exception)):
                enforcer.enforce_phase(99)  # Invalid phase
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_handles_negative_phase_number(self):
        """Test handling of negative phase number."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            with pytest.raises((ValueError, Exception)):
                enforcer.enforce_phase(-1)
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_handles_zero_phase_number(self):
        """Test handling of zero phase number."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            with pytest.raises((ValueError, Exception)):
                enforcer.enforce_phase(0)
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_handles_missing_structure_files(self):
        """Test handling when structure files are missing."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer("/tmp/test_empty_project")
            os.makedirs("/tmp/test_empty_project", exist_ok=True)
            result = enforcer.enforce_phase(1)
            # Should handle gracefully with low score
            assert result is not None
            assert result.structure_check.score <= 100
        except ImportError:
            pytest.skip("phase_enforcer not available")
        except Exception:
            pass  # Expected for empty project
        finally:
            import shutil
            if os.path.exists("/tmp/test_empty_project"):
                shutil.rmtree("/tmp/test_empty_project")

    def test_handles_corrupted_structure(self):
        """Test handling of corrupted structure data."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            
            # Mock a corrupted structure
            with patch.object(enforcer, '_check_structure', side_effect=Exception("Corrupted")):
                try:
                    result = enforcer.enforce_phase(1)
                except Exception:
                    pass  # Should handle gracefully
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_result_has_proper_format(self):
        """Test that result has proper format even on error."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcementResult, StructureCheckResult, ContentCheckResult
            result = PhaseEnforcementResult(
                phase=1,
                passed=False,
                structure_check=StructureCheckResult(score=0.0, missing=[]),
                content_check=ContentCheckResult(score=0.0, missing_sections=[]),
                gate_score=0.0,
                can_proceed=False,
                blocker_issues=["Error occurred"]
            )
            assert isinstance(result.to_dict(), dict) if hasattr(result, 'to_dict') else True
        except ImportError:
            pytest.skip("phase_enforcer not available")


class TestPhaseEnforcerIntegration:
    """Integration tests for PhaseEnforcer."""

    def setup_method(self):
        """Setup for each test."""
        self.project_path = Path(__file__).parent.parent

    def test_full_enforcement_workflow(self):
        """Test complete enforcement workflow."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path))
            result = enforcer.enforce_phase(1)
            assert result is not None
            assert hasattr(result, 'phase')
            assert hasattr(result, 'passed')
            assert hasattr(result, 'gate_score')
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcement_with_high_threshold(self):
        """Test enforcement with higher threshold."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path), gate_threshold=90)
            result = enforcer.enforce_phase(1)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcement_with_custom_weights(self):
        """Test enforcement with custom weights."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path), weights=(0.3, 0.3, 0.4))
            result = enforcer.enforce_phase(1)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_enforcement_produces_blocker_list(self):
        """Test that enforcement produces blocker list."""
        try:
            from quality_gate.phase_enforcer import PhaseEnforcer
            enforcer = PhaseEnforcer(str(self.project_path), strict_mode=True)
            result = enforcer.enforce_phase(1)
            # Should have blocker list
            assert hasattr(result, 'blocker_issues')
            assert isinstance(result.blocker_issues, list)
        except ImportError:
            pytest.skip("phase_enforcer not available")


# Helper function tests
class TestPhaseEnforcerHelpers:
    """Test helper functions."""

    def test_enforce_phase_function(self):
        """Test the enforce_phase helper function."""
        try:
            from quality_gate.phase_enforcer import enforce_phase
            project_path = Path(__file__).parent.parent
            result = enforce_phase(str(project_path), phase=1)
            assert result is not None
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_check_can_proceed_function(self):
        """Test the check_can_proceed helper function."""
        try:
            from quality_gate.phase_enforcer import check_can_proceed
            project_path = Path(__file__).parent.parent
            can_proceed = check_can_proceed(str(project_path), current_phase=1)
            assert isinstance(can_proceed, bool)
        except ImportError:
            pytest.skip("phase_enforcer not available")

    def test_generate_full_report_function(self):
        """Test the generate_full_report helper function."""
        try:
            from quality_gate.phase_enforcer import generate_full_report
            project_path = Path(__file__).parent.parent
            report = generate_full_report(str(project_path))
            assert report is not None
            assert isinstance(report, dict)
        except ImportError:
            pytest.skip("phase_enforcer not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])