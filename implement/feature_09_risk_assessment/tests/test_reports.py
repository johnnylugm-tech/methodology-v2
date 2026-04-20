#!/usr/bin/env python3
"""
test_reports.py - Tests for report generators
[FR-04] Coverage for reports/ module
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules - conftest.py already adds feature dir to sys.path
from implement.feature_09_risk_assessment.reports.assessor_report import RiskAssessmentReportGenerator
from implement.feature_09_risk_assessment.reports.decision_gate_report import DecisionGateReportGenerator
from implement.feature_09_risk_assessment.engine.engine import DecisionGateResult
from implement.feature_09_risk_assessment.models.risk import Risk, RiskAssessmentResult, MitigationPlan
from implement.feature_09_risk_assessment.models.enums import RiskLevel, RiskStatus, RiskDimension, StrategyType


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestRiskAssessmentReportGenerator:
    """Tests for RiskAssessmentReportGenerator"""

    def test_init(self, temp_project_root):
        """Test generator initialization"""
        generator = RiskAssessmentReportGenerator(str(temp_project_root))
        assert generator.project_root == temp_project_root

    def test_generate_creates_files(self, temp_project_root):
        """Test that generate() creates report files"""
        generator = RiskAssessmentReportGenerator(str(temp_project_root))

        # Create risks - score is computed, not passed
        # RiskDimension: TECHNICAL, OPERATIONAL, EXTERNAL
        risk1 = Risk(
            title="Test Risk 1",
            description="A test risk",
            dimension=RiskDimension.TECHNICAL,
            probability=0.6,
            impact=4,
            detectability_factor=0.8,
            level=RiskLevel.HIGH,
            status=RiskStatus.OPEN,
            owner="Test Owner",
            mitigation="Test mitigation",
            mitigation_plan=MitigationPlan(
                immediate=["Action 1"],
                short_term=["Action 2"],
                long_term=["Action 3"],
                fallback=["Fallback action"],
            ),
            evidence=["Evidence 1"],
            strategy=StrategyType.MITIGATE,
        )
        risk2 = Risk(
            title="Test Risk 2",
            description="Another test risk",
            dimension=RiskDimension.OPERATIONAL,
            probability=0.4,
            impact=3,
            detectability_factor=1.0,
            level=RiskLevel.MEDIUM,
            status=RiskStatus.OPEN,
            owner="Test Owner",
            mitigation="Test mitigation",
            mitigation_plan=MitigationPlan(),
            evidence=[],
            strategy=StrategyType.MITIGATE,
        )

        result = RiskAssessmentResult(
            project_name="Test Project",
            phase=5,
            total_risks=2,
            risks=[risk1, risk2],
            average_score=0.45,
            recommendations=["Test recommendation"],
        )

        generator.generate(result)

        # Check files were created
        assert (temp_project_root / "RISK_ASSESSMENT.md").exists()
        assert (temp_project_root / "RISK_REGISTER.md").exists()

    def test_generate_assessment_report_content(self, temp_project_root):
        """Test assessment report content structure"""
        generator = RiskAssessmentReportGenerator(str(temp_project_root))

        risk = Risk(
            title="High Priority Risk",
            description="A critical test risk",
            dimension=RiskDimension.TECHNICAL,
            probability=0.6,
            impact=4,
            detectability_factor=0.8,
            level=RiskLevel.HIGH,
            status=RiskStatus.OPEN,
            owner="Owner",
            mitigation="Mitigation",
            mitigation_plan=MitigationPlan(),
            evidence=[],
            strategy=StrategyType.MITIGATE,
        )

        result = RiskAssessmentResult(
            project_name="Test Project",
            phase=5,
            total_risks=1,
            risks=[risk],
            average_score=0.55,
            recommendations=[],
        )

        generator._generate_assessment_report(result)

        content = (temp_project_root / "RISK_ASSESSMENT.md").read_text()

        # Check for required sections
        assert "# Risk Assessment Report" in content
        assert "## Executive Summary" in content
        assert "## Risk Register" in content
        assert "## Detailed Assessments" in content
        # Risk title is present
        assert "High Priority Risk" in content

    def test_level_icon(self, temp_project_root):
        """Test risk level icon mapping"""
        generator = RiskAssessmentReportGenerator(str(temp_project_root))

        assert generator._level_icon(RiskLevel.CRITICAL) == "🔴"
        assert generator._level_icon(RiskLevel.HIGH) == "🟠"
        assert generator._level_icon(RiskLevel.MEDIUM) == "🟡"
        assert generator._level_icon(RiskLevel.LOW) == "🟢"
        assert generator._level_icon(None) == "⚪"


class TestDecisionGateReportGenerator:
    """Tests for DecisionGateReportGenerator"""

    def test_init(self, temp_project_root):
        """Test generator initialization"""
        generator = DecisionGateReportGenerator(str(temp_project_root))
        assert generator.project_root == temp_project_root

    def test_generate_pass_result(self, temp_project_root):
        """Test generating report for PASS result"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        # PASS when can_proceed=True and no blockers
        result = DecisionGateResult(
            can_proceed=True,
            conditions=[],
            blockers=[],
            recommendations=["Run tests before proceeding"],
            assessed_at=datetime.now(),
        )

        report = generator.generate(result, next_phase=6)

        assert "# Phase 7 Decision Gate Report" in report
        assert "PASS" in report
        assert "can proceed" in report.lower()

    def test_generate_blocked_result(self, temp_project_root):
        """Test generating report for BLOCKED result"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        # BLOCKED when can_proceed=False
        result = DecisionGateResult(
            can_proceed=False,
            conditions=[],
            blockers=[
                "Critical risks not mitigated",
                "Missing sign-off",
            ],
            recommendations=["Mitigate all critical risks"],
            assessed_at=datetime.now(),
        )

        report = generator.generate(result, next_phase=6)

        assert "BLOCKED" in report
        assert "Critical risks not mitigated" in report

    def test_generate_conditional_pass(self, temp_project_root):
        """Test generating report for CONDITIONAL_PASS result"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        # CONDITIONAL_PASS when can_proceed=True but has blockers
        # OR when can_proceed=False with conditions (but no blockers first)
        result = DecisionGateResult(
            can_proceed=True,
            conditions=[
                "Review risk weekly",
                "Complete security audit by end of month",
            ],
            blockers=["Minor issue to track"],  # Has blockers so it's conditional
            recommendations=["Consider automating risk tracking"],
            assessed_at=datetime.now(),
        )

        report = generator.generate(result, next_phase=6)

        assert "CONDITIONAL PASS" in report
        assert "Review risk weekly" in report

    def test_status_badge(self, temp_project_root):
        """Test status badge mapping"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        assert "🟢" in generator._status_badge("PASS")
        assert "🟡" in generator._status_badge("CONDITIONAL_PASS")
        assert "🔴" in generator._status_badge("BLOCKED")

    def test_save(self, temp_project_root):
        """Test saving report to file"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        result = DecisionGateResult(
            can_proceed=True,
            conditions=[],
            blockers=[],
            recommendations=[],
            assessed_at=datetime.now(),
        )

        saved_path = generator.save(result, next_phase=6)

        assert saved_path.exists()
        assert "DecisionGate" in str(saved_path)

    def test_generate_with_risk_summary(self, temp_project_root):
        """Test that generate includes risk summary when tracker available"""
        generator = DecisionGateReportGenerator(str(temp_project_root))

        result = DecisionGateResult(
            can_proceed=True,
            conditions=[],
            blockers=[],
            recommendations=[],
            assessed_at=datetime.now(),
        )

        report = generator.generate(result, next_phase=6)

        # Report should include risk context section
        assert "Risk Context" in report or "risk" in report.lower()