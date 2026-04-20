#!/usr/bin/env python3
"""
assessor_report.py - Risk Assessment Report Generator
[FR-01, FR-02, FR-03, FR-04] Generate human-readable assessment reports
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from models.risk import Risk, RiskAssessmentResult
from models.enums import RiskLevel, RiskStatus, RiskDimension


class RiskAssessmentReportGenerator:
    """
    [FR-01, FR-02, FR-03, FR-04] Generate risk assessment reports

    Generates:
    - RISK_ASSESSMENT.md
    - RISK_REGISTER.md
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

    def generate(self, result: RiskAssessmentResult) -> None:
        """
        生成風險評估報告

        Args:
            result: RiskAssessmentResult from engine.assess()
        """
        # Generate RISK_ASSESSMENT.md
        self._generate_assessment_report(result)

        # Generate RISK_REGISTER.md
        self._generate_register(result.risks)

    def _generate_assessment_report(self, result: RiskAssessmentResult) -> None:
        """生成 RISK_ASSESSMENT.md"""
        lines = [
            "# Risk Assessment Report",
            "",
            f"**Project**: {result.project_name}",
            f"**Generated**: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Phase**: Phase {result.phase}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Total Risks**: {result.total_risks}",
            f"- **Critical**: {result.critical_count} | **High**: {result.high_count} | "
            f"**Medium**: {result.medium_count} | **Low**: {result.low_count}",
            f"- **Average Score**: {result.average_score:.3f}",
            "",
            "### Status Distribution",
            f"- Open: {result.open_count}",
            f"- Closed: {result.closed_count}",
            "",
        ]

        # Risk level legend
        lines.extend([
            "### Risk Level Legend",
            "| Level | Score Range | Description |",
            "|-------|-------------|-------------|",
            "| 🔴 CRITICAL | >= 0.7 | Immediate attention required |",
            "| 🟠 HIGH | 0.5-0.69 | Dedicated resources needed |",
            "| 🟡 MEDIUM | 0.3-0.49 | Scheduled remediation |",
            "| 🟢 LOW | < 0.3 | Monitor in backlog |",
            "",
        ])

        # Risk register table
        lines.extend([
            "## Risk Register",
            "",
            "| ID | Title | Dimension | Level | Score | Status | Owner |",
            "|----|-------|-----------|-------|-------|--------|-------|",
        ])

        for risk in sorted(result.risks, key=lambda r: r.score, reverse=True):
            level_icon = self._level_icon(risk.level)
            lines.append(
                f"| {risk.id} | {risk.title[:40]} | {risk.dimension.value.upper()} | "
                f"{level_icon} {risk.level.value.upper()} | {risk.score:.3f} | "
                f"{risk.status.value.upper()} | {risk.owner or '-'} |"
            )

        lines.append("")

        # Detailed assessments
        lines.extend([
            "## Detailed Assessments",
            "",
        ])

        for risk in sorted(result.risks, key=lambda r: r.score, reverse=True):
            lines.extend(self._format_risk_detail(risk))

        # Recommendations
        if result.recommendations:
            lines.extend([
                "## Recommendations",
                "",
            ])
            for rec in result.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        # Write file
        output_path = self.project_root / "RISK_ASSESSMENT.md"
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _generate_register(self, risks: List[Risk]) -> None:
        """生成 RISK_REGISTER.md"""
        lines = [
            "# Risk Register",
            "",
            f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Decision Gate 確認",
            "",
            "| ID | 風險描述 | 維度 | 等級 | 概率 | 影響 | 緩解措施 | 狀態 |",
            "|----|----------|------|------|------|------|---------|------|",
        ]

        for risk in risks:
            prob_pct = f"{risk.probability * 100:.0f}%"
            lines.append(
                f"| {risk.id} | {risk.title[:30]} | {risk.dimension.value} | "
                f"{risk.level.value.upper()} | {prob_pct} | {risk.impact} | "
                f"{risk.mitigation[:30] if risk.mitigation else '-'} | {risk.status.value} |"
            )

        lines.append("")

        # Decision Gate section
        lines.extend([
            "## Decision Gate 確認",
            "",
            "| 風險 ID | 決策 | 確認人 | session_id | 日期 |",
            "|---------|------|--------|------------|------|",
            "",
            "---",
            "*本文件由 Risk Assessment Engine 自動生成*",
        ])

        output_path = self.project_root / "RISK_REGISTER.md"
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _format_risk_detail(self, risk: Risk) -> List[str]:
        """格式化單一風險的詳細資訊"""
        level_icon = self._level_icon(risk.level)

        lines = [
            f"### {risk.id}: {risk.title}",
            "",
            f"- **Dimension**: {risk.dimension.value.upper()}",
            f"- **Probability**: {risk.probability:.2f} ({risk.probability * 100:.0f}%)",
            f"- **Impact**: {risk.impact}/5",
            f"- **Score**: {risk.score:.3f}",
            f"- **Level**: {level_icon} {risk.level.value.upper()}",
            f"- **Status**: {risk.status.value.upper()}",
            f"- **Strategy**: {risk.strategy.value.upper()}",
            "",
            f"**Description**: {risk.description}",
            "",
        ]

        if risk.evidence:
            lines.append("**Evidence**:")
            for e in risk.evidence:
                lines.append(f"- {e}")
            lines.append("")

        if risk.mitigation_plan:
            plan = risk.mitigation_plan
            lines.append("**Mitigation Plan**:")

            if plan.immediate:
                lines.append("- Immediate (24h):")
                for a in plan.immediate:
                    lines.append(f"  - {a}")

            if plan.short_term:
                lines.append("- Short-term (1 week):")
                for a in plan.short_term:
                    lines.append(f"  - {a}")

            if plan.long_term:
                lines.append("- Long-term (1 month):")
                for a in plan.long_term:
                    lines.append(f"  - {a}")

            if plan.fallback:
                lines.append("- Fallback:")
                for a in plan.fallback:
                    lines.append(f"  - {a}")

            lines.append("")

        lines.append(f"**Created**: {risk.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Updated**: {risk.updated_at.strftime('%Y-%m-%d %H:%M')}")

        if risk.closed_at:
            lines.append(f"**Closed**: {risk.closed_at.strftime('%Y-%m-%d %H:%M')}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    def _level_icon(self, level: RiskLevel) -> str:
        """返回風險等級的表情符號"""
        icons = {
            RiskLevel.CRITICAL: "🔴",
            RiskLevel.HIGH: "🟠",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.LOW: "🟢",
        }
        return icons.get(level, "⚪")