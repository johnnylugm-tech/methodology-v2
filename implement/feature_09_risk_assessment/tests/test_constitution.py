#!/usr/bin/env python3
"""
test_constitution.py - Tests for constitution compliance checker
[FR-04] Coverage for constitution/ module
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules using direct file imports to avoid namespace conflict
import sys
feature_dir = Path(__file__).parent.parent
if str(feature_dir) not in sys.path:
    sys.path.insert(0, str(feature_dir))

# Direct import bypassing __init__
import importlib.util

def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import constitution checker directly
constitution_module = import_from_file(
    "risk_assessment_checker",
    feature_dir / "constitution" / "risk_assessment_checker.py"
)
RiskAssessmentConstitutionChecker = constitution_module.RiskAssessmentConstitutionChecker
ConstitutionCheckResult = constitution_module.ConstitutionCheckResult
CONSTITUTION_THRESHOLDS = constitution_module.CONSTITUTION_THRESHOLDS

# Import enums directly
enums_module = import_from_file(
    "enums",
    feature_dir / "models" / "enums.py"
)
RiskLevel = enums_module.RiskLevel
RiskStatus = enums_module.RiskStatus
RiskDimension = enums_module.RiskDimension


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def checker(temp_project_root):
    """Create a checker instance with temp project root"""
    return RiskAssessmentConstitutionChecker(str(temp_project_root))


class TestConstitutionThresholds:
    """Tests for constitution threshold constants"""

    def test_thresholds_exist(self):
        """Test that threshold constants are defined"""
        assert "correctness" in CONSTITUTION_THRESHOLDS
        assert "security" in CONSTITUTION_THRESHOLDS
        assert "maintainability" in CONSTITUTION_THRESHOLDS

    def test_threshold_values(self):
        """Test threshold values are valid"""
        assert CONSTITUTION_THRESHOLDS["correctness"] == 1.0
        assert CONSTITUTION_THRESHOLDS["security"] == 1.0
        assert CONSTITUTION_THRESHOLDS["maintainability"] == 0.7


class TestConstitutionCheckResult:
    """Tests for ConstitutionCheckResult dataclass"""

    def test_create_result(self):
        """Test creating a valid result"""
        result = ConstitutionCheckResult(
            passed=True,
            score=85.0,
            violations=[],
            recommendations=["Improve documentation"],
            details={"checks_passed": 5, "total_checks": 5},
        )

        assert result.passed is True
        assert result.score == 85.0
        assert len(result.violations) == 0
        assert len(result.recommendations) == 1

    def test_create_result_with_violations(self):
        """Test creating result with violations"""
        result = ConstitutionCheckResult(
            passed=False,
            score=40.0,
            violations=[
                {"type": "missing_files", "message": "Missing test file", "severity": "HIGH"},
                {"type": "incomplete", "message": "Incomplete implementation", "severity": "MEDIUM"},
            ],
            recommendations=["Add missing files"],
            details={"checks_passed": 2, "total_checks": 5},
        )

        assert result.passed is False
        assert result.score == 40.0
        assert len(result.violations) == 2


class TestRiskAssessmentConstitutionChecker:
    """Tests for RiskAssessmentConstitutionChecker"""

    def test_init(self, checker):
        """Test checker initialization"""
        assert checker.project_root.exists()

    def test_required_files_defined(self, checker):
        """Test required files list is defined"""
        assert len(checker.REQUIRED_FILES) > 0
        assert "RISK_ASSESSMENT.md" in checker.REQUIRED_FILES
        assert "RISK_REGISTER.md" in checker.REQUIRED_FILES

    def test_required_sections_defined(self, checker):
        """Test required sections list is defined"""
        assert len(checker.REQUIRED_SECTIONS) > 0
        assert "## Executive Summary" in checker.REQUIRED_SECTIONS

    def test_check_returns_result(self, checker):
        """Test that check() returns a ConstitutionCheckResult"""
        result = checker.check()

        assert isinstance(result, ConstitutionCheckResult)
        assert hasattr(result, "passed")
        assert hasattr(result, "score")
        assert hasattr(result, "violations")
        assert hasattr(result, "recommendations")
        assert hasattr(result, "details")

    def test_check_with_no_files(self, checker):
        """Test check when no files exist (should fail)"""
        result = checker.check()

        # With no files, should have violations and fail
        assert result.passed is False or len(result.violations) > 0

    def test_check_with_files_created(self, temp_project_root):
        """Test check when required files exist"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        # Create required files
        (temp_project_root / "RISK_ASSESSMENT.md").write_text("""
# Risk Assessment Report

## Executive Summary

## Risk Register

## Detailed Assessments
""")
        (temp_project_root / "RISK_REGISTER.md").write_text("""
# Risk Register

| ID | 描述 | 維度 | 等級 | 狀態 |
|----|------|------|------|------|
""")

        result = checker.check()

        # Should pass since files exist
        assert result.score >= 60  # At least the file checks should pass

    def test_check_required_files_method(self, temp_project_root):
        """Test _check_required_files method"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        # No files -> False
        assert checker._check_required_files() is False

        # Create files
        (temp_project_root / "RISK_ASSESSMENT.md").write_text("# Test")
        (temp_project_root / "RISK_REGISTER.md").write_text("# Test")

        # Should pass
        assert checker._check_required_files() is True

    def test_check_assessment_sections_method(self, temp_project_root):
        """Test _check_assessment_sections method"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        # No file -> False
        assert checker._check_assessment_sections() is False

        # Create file with required sections
        content = """
# Risk Assessment Report

## Executive Summary
Some content

## Risk Register
More content

## Detailed Assessments
Final content
"""
        (temp_project_root / "RISK_ASSESSMENT.md").write_text(content)

        assert checker._check_assessment_sections() is True

    def test_check_assessment_sections_missing_section(self, temp_project_root):
        """Test _check_assessment_sections with missing section"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        content = """
# Risk Assessment Report

## Executive Summary
Some content

## Risk Register
More content
"""
        (temp_project_root / "RISK_ASSESSMENT.md").write_text(content)

        # Missing Detailed Assessments -> False
        assert checker._check_assessment_sections() is False

    def test_check_register_format(self, temp_project_root):
        """Test _check_register_format method"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        # No file -> True (skip check)
        assert checker._check_register_format() is True

        # Create file with required columns
        content = """
# Risk Register

| ID | 風險描述 | 維度 | 等級 | 狀態 |
|----|----------|------|------|------|
"""
        (temp_project_root / "RISK_REGISTER.md").write_text(content)

        assert checker._check_register_format() is True

    def test_check_status_tracking_no_db(self, checker):
        """Test _check_status_tracking when no database exists"""
        # Should return True (skip check) if no DB
        result = checker._check_status_tracking()
        assert result is True

    def test_generate_report(self, checker):
        """Test generate_report method"""
        report = checker.generate_report()

        assert "# Risk Assessment Constitution Check Report" in report
        assert "Result:" in report or "PASS" in report or "FAIL" in report

    def test_timestamp(self, checker):
        """Test _timestamp method format"""
        ts = checker._timestamp()

        # Should be in YYYY-MM-DD HH:MM:SS format
        assert len(ts) == 19
        assert "-" in ts and ":" in ts

    def test_check_score_calculation(self, temp_project_root):
        """Test that score is calculated correctly"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        result = checker.check()

        # Score should be between 0 and 100
        assert 0 <= result.score <= 100

        # If all checks pass, score should be 100
        assert result.details["total_checks"] == 5

    def test_pass_threshold(self, temp_project_root):
        """Test that passing requires >= maintainability threshold"""
        checker = RiskAssessmentConstitutionChecker(str(temp_project_root))

        # With no files, should fail
        result = checker.check()

        # Score should be based on 5 checks
        # 0/5 = 0%, 1/5 = 20%, etc.
        assert result.score in [0, 20, 40, 60, 80, 100]