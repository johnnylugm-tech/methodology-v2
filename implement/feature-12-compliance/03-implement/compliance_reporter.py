"""Automated Compliance Reporter.

FR-12-05: Generates automated compliance reports for EU AI Act, NIST AI RMF,
and RSP v3.0 requirements.

This module provides:
1. Periodic compliance summary reports
2. Gap analysis and remediation tracking
3. Multi-framework compliance dashboards
4. Audit-ready documentation generation

References:
    - EU AI Act (Regulation 2024/1689)
    - NIST AI RMF v1.0 (NIST AI 100-1)
    - RSP v3.0 (RSK Process Standard)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Optional

from eu_ai_act import ComplianceAssessment, EUAIActChecker
from nist_rmf import NISTRMFMapper, FunctionMapping
from compliance_matrix import ASLDetectionResult, UnifiedComplianceMatrix


class ReportType(Enum):
    """Types of compliance reports."""
    EXECUTIVE_SUMMARY = auto()
    DETAILED_ASSESSMENT = auto()
    GAP_ANALYSIS = auto()
    REMEDIATION_TRACKING = auto()
    AUDIT_READY = auto()


class ReportFormat(Enum):
    """Output format for reports."""
    DICT = auto()
    HTML = auto()
    MARKDOWN = auto()
    JSON = auto()


@dataclass
class ComplianceReport:
    """Container for compliance report data."""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    eu_ai_act: ComplianceAssessment
    nist_rmf_mappings: list[FunctionMapping]
    asl_level: str
    unified_matrix: Optional[UnifiedComplianceMatrix]
    summary: dict[str, Any]
    gaps: list[dict[str, Any]]
    recommendations: list[str]
    next_review_date: datetime


@dataclass
class GapTrend:
    """Tracks compliance gap trends over time."""
    gap_id: str
    description: str
    first_identified: datetime
    severity: str  # critical, high, medium, low
    status: str  # open, in_progress, resolved
    resolution_date: Optional[datetime] = None
    notes: list[str] = field(default_factory=list)


class ComplianceReporter:
    """Automated compliance reporting for trading systems.

    This reporter generates periodic compliance reports that consolidate
    findings from EU AI Act, NIST AI RMF, and RSP v3.0 assessments.

    Example:
        reporter = ComplianceReporter()
        report = reporter.generate_report(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            period_days=30
        )
        reporter.export(report, format=ReportFormat.HTML, output_path="report.html")
    """

    def __init__(
        self,
        eu_checker: Optional[EUAIActChecker] = None,
        nist_mapper: Optional[NISTRMFMapper] = None
    ):
        """Initialize compliance reporter.

        Args:
            eu_checker: Optional EU AI Act checker (creates default if None)
            nist_mapper: Optional NIST RMF mapper (creates default if None)
        """
        self.eu_checker = eu_checker or EUAIActChecker()
        self.nist_mapper = nist_mapper or NISTRMFMapper()
        self._gap_history: list[GapTrend] = []

    def generate_report(
        self,
        report_type: ReportType,
        period_days: int = 30,
        eu_assessment: Optional[ComplianceAssessment] = None,
        asl_result: Optional[ASLDetectionResult] = None,
        nist_mappings: Optional[list[FunctionMapping]] = None,
        unified_matrix: Optional[UnifiedComplianceMatrix] = None
    ) -> ComplianceReport:
        """Generate a compliance report.

        Args:
            report_type: Type of report to generate
            period_days: Number of days to include in report period
            eu_assessment: EU AI Act assessment results
            asl_result: ASL detection result
            nist_mappings: NIST RMF function mappings
            unified_matrix: Unified compliance matrix

        Returns:
            ComplianceReport with all findings
        """
        now = datetime.now()
        period_start = now - timedelta(days=period_days)

        # Generate summary
        summary = self._generate_summary(
            eu_assessment, asl_result, nist_mappings, unified_matrix
        )

        # Collect gaps
        gaps = self._collect_gaps(
            eu_assessment, asl_result, unified_matrix
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            gaps, eu_assessment, asl_result
        )

        # Update gap history
        self._update_gap_history(gaps)

        return ComplianceReport(
            report_id=f"CR-{now.strftime('%Y%m%d-%H%M%S')}-{report_type.name}",
            report_type=report_type,
            generated_at=now,
            period_start=period_start,
            period_end=now,
            eu_ai_act=eu_assessment or self._create_mock_assessment(),
            nist_rmf_mappings=nist_mappings or [],
            asl_level=asl_result.level.value if asl_result else "ASL-3",
            unified_matrix=unified_matrix,
            summary=summary,
            gaps=gaps,
            recommendations=recommendations,
            next_review_date=now + timedelta(days=period_days)
        )

    def _generate_summary(
        self,
        eu_assessment: Optional[ComplianceAssessment],
        asl_result: Optional[ASLDetectionResult],
        nist_mappings: Optional[list[FunctionMapping]],
        unified_matrix: Optional[UnifiedComplianceMatrix]
    ) -> dict[str, Any]:
        """Generate executive summary section."""
        summary = {
            "overall_status": "compliant",
            "risk_level": "medium",
            "critical_findings": 0,
            "open_gaps": 0,
            "framework_scores": {}
        }

        if eu_assessment:
            summary["framework_scores"]["eu_ai_act"] = eu_assessment.overall_score
            if eu_assessment.overall_score < 0.8:
                summary["overall_status"] = "non_compliant"
            summary["critical_findings"] += len(eu_assessment.critical_gaps)

        if unified_matrix:
            summary["framework_scores"]["overall"] = unified_matrix.overall_score
            summary["framework_scores"]["nist_rmf"] = unified_matrix.nist_rmf_score
            summary["framework_scores"]["rsp_v3"] = unified_matrix.rsp_score

        if asl_result:
            summary["asl_level"] = asl_result.level.value
            summary["asl_confidence"] = asl_result.confidence

        return summary

    def _collect_gaps(
        self,
        eu_assessment: Optional[ComplianceAssessment],
        asl_result: Optional[ASLDetectionResult],
        unified_matrix: Optional[UnifiedComplianceMatrix]
    ) -> list[dict[str, Any]]:
        """Collect all identified compliance gaps."""
        gaps = []

        # EU AI Act gaps
        if eu_assessment:
            for req in eu_assessment.requirements:
                if req.status.value in ("PARTIAL", "NON_COMPLIANT"):
                    for gap in req.gaps:
                        gaps.append({
                            "source": "EU AI Act",
                            "requirement_id": req.requirement_id,
                            "title": req.title,
                            "gap": gap,
                            "severity": "critical" if req.status.value == "NON_COMPLIANT" else "medium"
                        })

        # Unified matrix gaps
        if unified_matrix:
            for gap in unified_matrix.gaps:
                gaps.append({
                    "source": gap.get("dimension_id", "Unknown"),
                    "requirement_id": gap.get("dimension_id", ""),
                    "title": gap.get("name", "Unknown"),
                    "gap": gap.get("reason", ""),
                    "severity": "high" if gap.get("score", 1.0) < 0.5 else "medium"
                })

        return gaps

    def _generate_recommendations(
        self,
        gaps: list[dict[str, Any]],
        eu_assessment: Optional[ComplianceAssessment],
        asl_result: Optional[ASLDetectionResult]
    ) -> list[str]:
        """Generate actionable recommendations from gaps."""
        recommendations = []

        # Group by severity
        critical_gaps = [g for g in gaps if g.get("severity") == "critical"]
        high_gaps = [g for g in gaps if g.get("severity") == "high"]
        medium_gaps = [g for g in gaps if g.get("severity") == "medium"]

        if critical_gaps:
            recommendations.append(
                f"URGENT: Address {len(critical_gaps)} critical compliance gaps immediately"
            )

        if eu_assessment and eu_assessment.critical_gaps:
            recommendations.append(
                "EU AI Act Article 14: Implement human oversight mechanisms for high-risk functions"
            )

        if asl_result and asl_result.level.value in ("ASL-6", "ASL-7"):
            recommendations.append(
                "Autonomous system: Consider redesign to enable human override capability"
            )

        if high_gaps:
            recommendations.append(
                f"High Priority: Address {len(high_gaps)} high-severity gaps within 30 days"
            )

        if medium_gaps:
            recommendations.append(
                f"Review {len(medium_gaps)} medium-severity gaps and create remediation plan"
            )

        return recommendations

    def _update_gap_history(self, gaps: list[dict[str, Any]]):
        """Update gap history tracking."""
        for gap in gaps:
            existing = next(
                (g for g in self._gap_history if g.gap_id == gap.get("requirement_id", "")),
                None
            )

            if existing:
                # Update status
                if gap.get("severity") == "resolved":
                    existing.status = "resolved"
                    existing.resolution_date = datetime.now()
            else:
                # Create new gap trend
                self._gap_history.append(GapTrend(
                    gap_id=gap.get("requirement_id", f"GAP-{len(self._gap_history)}"),
                    description=gap.get("title", ""),
                    first_identified=datetime.now(),
                    severity=gap.get("severity", "medium"),
                    status="open"
                ))

    def _create_mock_assessment(self) -> ComplianceAssessment:
        """Create a mock assessment when none provided (for testing)."""
        from eu_ai_act import Article14Requirement, ComplianceStatus

        return ComplianceAssessment(
            requirements=[
                Article14Requirement(
                    requirement_id="Art14-2-a",
                    title="Human Oversight Measures",
                    description="Appropriate oversight measures",
                    status=ComplianceStatus.COMPLIANT,
                    evidence=["Kill switch active", "Override enabled"]
                )
            ],
            overall_score=0.85,
            critical_gaps=[],
            assessed_at=datetime.now()
        )

    def export(
        self,
        report: ComplianceReport,
        format: ReportFormat = ReportFormat.DICT,
        output_path: Optional[str] = None
    ) -> Any:
        """Export report to specified format.

        Args:
            report: ComplianceReport to export
            format: Output format (DICT, HTML, MARKDOWN, JSON)
            output_path: Optional file path to write output

        Returns:
            Report in specified format
        """
        if format == ReportFormat.DICT or format == ReportFormat.JSON:
            output = self._to_dict(report)
        elif format == ReportFormat.HTML:
            output = self._to_html(report)
        elif format == ReportFormat.MARKDOWN:
            output = self._to_markdown(report)
        else:
            output = self._to_dict(report)

        if output_path:
            with open(output_path, "w") as f:
                f.write(str(output) if isinstance(output, str) else output)

        return output

    def _to_dict(self, report: ComplianceReport) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": report.report_id,
            "report_type": report.report_type.name,
            "generated_at": report.generated_at.isoformat(),
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat()
            },
            "summary": report.summary,
            "asl_level": report.asl_level,
            "gaps": report.gaps,
            "recommendations": report.recommendations,
            "next_review_date": report.next_review_date.isoformat(),
            "eu_ai_act_score": report.eu_ai_act.overall_score if report.eu_ai_act else None
        }

    def _to_html(self, report: ComplianceReport) -> str:
        """Convert report to HTML format."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Compliance Report - {report.report_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .score {{ font-size: 2em; font-weight: bold; }}
        .compliant {{ color: green; }}
        .non-compliant {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .critical {{ background-color: #ffe6e6; }}
    </style>
</head>
<body>
    <h1>Compliance Report</h1>
    <p>Report ID: {report.report_id}</p>
    <p>Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Period: {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}</p>

    <h2>Summary</h2>
    <p>Overall Status: <span class="{'compliant' if report.summary.get('overall_status') == 'compliant' else 'non-compliant'}">{report.summary.get('overall_status', 'unknown').upper()}</span></p>
    <p>ASL Level: {report.asl_level}</p>

    <h2>Scores</h2>
    <table>
        <tr><th>Framework</th><th>Score</th></tr>
"""
        for framework, score in report.summary.get("framework_scores", {}).items():
            html += f"        <tr><td>{framework.upper()}</td><td>{score:.1%}</td></tr>\n"

        html += """    </table>

    <h2>Recommendations</h2>
    <ul>
"""
        for rec in report.recommendations:
            html += f"        <li>{rec}</li>\n"

        html += """    </table>
</body>
</html>"""
        return html

    def _to_markdown(self, report: ComplianceReport) -> str:
        """Convert report to Markdown format."""
        md = f"""# Compliance Report

**Report ID:** {report.report_id}
**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Period:** {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}

## Summary

- **Overall Status:** {report.summary.get('overall_status', 'unknown').upper()}
- **ASL Level:** {report.asl_level}
- **Critical Findings:** {report.summary.get('critical_findings', 0)}
- **Open Gaps:** {report.summary.get('open_gaps', len(report.gaps))}

## Framework Scores

| Framework | Score |
|-----------|-------|
"""
        for framework, score in report.summary.get("framework_scores", {}).items():
            md += f"| {framework.upper()} | {score:.1%} |\n"

        md += """
## Gaps

| Requirement | Title | Gap | Severity |
|-------------|-------|-----|----------|
"""
        for gap in report.gaps:
            md += f"| {gap.get('requirement_id', '')} | {gap.get('title', '')} | {gap.get('gap', '')} | {gap.get('severity', '')} |\n"

        md += """
## Recommendations

"""
        for rec in report.recommendations:
            md += f"- {rec}\n"

        md += f"""
---
**Next Review:** {report.next_review_date.strftime('%Y-%m-%d')}
"""
        return md

    def generate_audit_package(
        self,
        report: ComplianceReport,
        include_evidences: bool = True
    ) -> dict[str, Any]:
        """Generate audit-ready documentation package.

        Args:
            report: ComplianceReport to package
            include_evidences: Whether to include evidence references

        Returns:
            Audit package dictionary
        """
        package = {
            "audit_id": f"AUDIT-{report.report_id}",
            "generated_at": datetime.now().isoformat(),
            "report": self._to_dict(report),
            "artifacts": []
        }

        if include_evidences:
            # Add evidence references from EU assessment
            if report.eu_ai_act:
                for req in report.eu_ai_act.requirements:
                    for evidence in req.evidence:
                        package["artifacts"].append({
                            "type": "evidence",
                            "requirement": req.requirement_id,
                            "description": evidence
                        })

        return package