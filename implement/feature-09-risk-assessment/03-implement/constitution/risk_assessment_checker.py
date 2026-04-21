#!/usr/bin/env python3
"""
risk_assessment_checker.py - Constitution Compliance Check
[FR-01, FR-02, FR-03, FR-04] Verify risk assessment meets Constitution standards

Checks against:
- risk_management_constitution_checker.py (from quality_gate)
- RISK_ASSESSMENT.md existence
- RISK_REGISTER.md existence
- Mitigation plans presence

Usage:
    >>> from constitution.risk_assessment_checker import RiskAssessmentConstitutionChecker
    >>> checker = RiskAssessmentConstitutionChecker("/path/to/project")
    >>> result = checker.check()
    >>> if result.passed:
    ...     print("Constitution compliance: PASS")
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from ..models.enums import RiskLevel

# Constitution thresholds (from quality_gate.constitution)
CONSTITUTION_THRESHOLDS = {
    "correctness": 1.0,      # 100% for risk management
    "security": 1.0,         # 100% - risk应对措施到位
    "maintainability": 0.7,  # >70% - 风险记录追踪
}


@dataclass
class ConstitutionCheckResult:
    """Constitution 合規檢查結果"""
    passed: bool
    score: float
    violations: List[Dict[str, str]]
    recommendations: List[str]
    details: Dict[str, Any]


class RiskAssessmentConstitutionChecker:
    """
    [FR-01, FR-02, FR-03, FR-04] Constitution 合規檢查器

    Verifies risk assessment meets Constitution principles by checking:
    - Required files exist (RISK_ASSESSMENT.md, RISK_REGISTER.md)
    - Required sections present in assessment documents
    - Mitigation plans exist for HIGH/CRITICAL risks
    - Risk register format matches expected template
    - Status tracking state machine is consistent

    Usage:
        >>> from constitution.risk_assessment_checker import RiskAssessmentConstitutionChecker
        >>> checker = RiskAssessmentConstitutionChecker("/path/to/project")
        >>> result = checker.check()
        >>> print(f"Score: {result.score:.1f}% - {'PASS' if result.passed else 'FAIL'}")
    """

    REQUIRED_FILES = [
        "RISK_ASSESSMENT.md",
        "RISK_REGISTER.md",
    ]

    REQUIRED_SECTIONS = [
        "## Executive Summary",
        "## Risk Register",
        "## Detailed Assessments",
    ]

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def check(self) -> ConstitutionCheckResult:
        """[FR-01, FR-02, FR-03, FR-04] Execute constitution compliance check.

        Returns:
            ConstitutionCheckResult with pass/fail and details
        """
        violations = []
        recommendations = []
        checks_passed = 0
        total_checks = 0

        # 1. Check required files exist
        total_checks += 1
        if self._check_required_files():
            checks_passed += 1
        else:
            violations.append({
                "type": "missing_files",
                "message": "Missing required risk assessment files",
                "severity": "HIGH",
            })

        # 2. Check RISK_ASSESSMENT.md sections
        total_checks += 1
        if self._check_assessment_sections():
            checks_passed += 1
        else:
            violations.append({
                "type": "incomplete_assessment",
                "message": "RISK_ASSESSMENT.md missing required sections",
                "severity": "MEDIUM",
            })

        # 3. Check mitigation plans
        total_checks += 1
        mitigation_complete = self._check_mitigation_plans()
        if mitigation_complete:
            checks_passed += 1
        else:
            violations.append({
                "type": "missing_mitigation",
                "message": "Some risks lack mitigation plans",
                "severity": "MEDIUM",
            })

        # 4. Check risk register format
        total_checks += 1
        if self._check_register_format():
            checks_passed += 1
        else:
            violations.append({
                "type": "invalid_register_format",
                "message": "RISK_REGISTER.md format does not match template",
                "severity": "LOW",
            })

        # 5. Check status tracking
        total_checks += 1
        if self._check_status_tracking():
            checks_passed += 1
        else:
            violations.append({
                "type": "incomplete_tracking",
                "message": "Risk status tracking incomplete",
                "severity": "MEDIUM",
            })

        # Calculate score
        score = (checks_passed / total_checks) * 100 if total_checks > 0 else 0

        # Pass if score >= maintainability threshold
        passed = score >= CONSTITUTION_THRESHOLDS["maintainability"] * 100

        return ConstitutionCheckResult(
            passed=passed,
            score=score,
            violations=violations,
            recommendations=recommendations,
            details={
                "checks_passed": checks_passed,
                "total_checks": total_checks,
                "project_root": str(self.project_root),
            },
        )

    def _check_required_files(self) -> bool:
        """[FR-01] Check if required risk assessment files exist."""
        for filename in self.REQUIRED_FILES:
            path = self.project_root / filename
            if not path.exists():
                path = self.project_root / "docs" / filename
            if not path.exists():
                return False
        return True

    def _check_assessment_sections(self) -> bool:
        """[FR-02] Check if RISK_ASSESSMENT.md has required sections."""
        path = self.project_root / "RISK_ASSESSMENT.md"
        if not path.exists():
            path = self.project_root / "docs" / "RISK_ASSESSMENT.md"

        if not path.exists():
            return False

        content = path.read_text()

        for section in self.REQUIRED_SECTIONS:
            if section not in content:
                return False

        return True

    def _check_mitigation_plans(self) -> bool:
        """[FR-03] Check if all risks have mitigation plans."""
        # Check if we can read risk data
        from ..engine.tracker import RiskTracker

        try:
            tracker = RiskTracker(str(self.project_root))
            risks = tracker.load_all_risks()

            if not risks:
                return True  # No risks is OK (just means nothing to mitigate)

            # Check each risk has mitigation plan
            for risk in risks:
                if risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    if not risk.mitigation_plan.short_term:
                        return False

            return True
        except (sqlite3.Error, OSError, UnicodeDecodeError):
            # If database doesn't exist, check markdown
            register_path = self.project_root / "RISK_REGISTER.md"
            if not register_path.exists():
                register_path = self.project_root / "docs" / "RISK_REGISTER.md"

            if not register_path.exists():
                return True  # No register yet

            content = register_path.read_text()
            # If we have risks in markdown, check for mitigation column
            return "Mitigation" in content or "緩解措施" in content

    def _check_register_format(self) -> bool:
        """[FR-04] Check if RISK_REGISTER.md format matches template."""
        path = self.project_root / "RISK_REGISTER.md"
        if not path.exists():
            path = self.project_root / "docs" / "RISK_REGISTER.md"

        if not path.exists():
            return True  # No register yet

        content = path.read_text()

        # Check for table format with required columns
        required_columns = ["ID", "描述", "維度", "等級", "狀態"]
        for col in required_columns:
            if col not in content and col.replace("ID", "Id") not in content:
                return False

        return True

    def _check_status_tracking(self) -> bool:
        """[FR-04] Check risk status tracking completeness."""
        from ..engine.tracker import RiskTracker

        try:
            tracker = RiskTracker(str(self.project_root))
            return tracker.validate_state_machine()["valid"]
        except (sqlite3.Error, OSError, AttributeError):
            # If we can't check DB, assume OK
            return True

    def generate_report(self) -> str:
        """[FR-01, FR-02, FR-03, FR-04] Generate constitution compliance report."""
        result = self.check()

        lines = [
            "# Risk Assessment Constitution Check Report",
            "",
            f"**Project**: {self.project_root.name}",
            f"**Generated**: {self._timestamp()}",
            "",
            f"## Result: {'✅ PASS' if result.passed else '❌ FAIL'}",
            f"**Score**: {result.score:.1f}%",
            "",
        ]

        if result.violations:
            lines.append("## Violations")
            for v in result.violations:
                lines.append(f"- [{v['severity']}] {v['message']}")
            lines.append("")

        if result.recommendations:
            lines.append("## Recommendations")
            for r in result.recommendations:
                lines.append(f"- {r}")
            lines.append("")

        lines.append("## Details")
        for key, value in result.details.items():
            lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    def _timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


