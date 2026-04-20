"""Gap Report Generation Module.

Generates structured gap reports in JSON and Markdown formats.
Outputs gap_report.json and gap_summary.md.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from gap_detector.parser import ParsedSpec
from gap_detector.scanner import ScannedCode
from gap_detector.detector import Gap, GapSummary


@dataclass
class ReportPaths:
    """Paths to generated report files.

    Attributes:
        json_path: Path to gap_report.json
        md_path: Path to gap_summary.md
    """

    json_path: str
    md_path: str


@dataclass
class GapReportJSON:
    """JSON report structure.

    Attributes:
        generated_at: ISO8601 timestamp
        spec_file: Path to SPEC.md
        implement_dir: Path to implement/
        summary: Gap summary statistics
        gaps: List of gaps
        spec_features_count: Number of spec features
        code_items_count: Number of code items
    """

    generated_at: str
    spec_file: str
    implement_dir: str
    summary: dict
    gaps: list[dict]
    spec_features_count: int
    code_items_count: int


class GapReporter:
    """Reporter for generating gap reports.

    Generates JSON and Markdown reports from gap detection results.

    Attributes:
        gaps: List of detected gaps
        spec: Parsed specification
        code: Scanned code
        output_dir: Directory for output files
    """

    def __init__(
        self,
        gaps: list[Gap],
        spec: ParsedSpec,
        code: ScannedCode,
        output_dir: str = "reports/"
    ) -> None:
        """Initialize the reporter.

        Args:
            gaps: List of detected gaps
            spec: Parsed specification
            code: Scanned code
            output_dir: Directory for output files
        """
        self.gaps = gaps
        self.spec = spec
        self.code = code
        self.output_dir = output_dir

    def generate(self) -> ReportPaths:
        """Generate all reports.

        Returns:
            ReportPaths: Paths to generated files
        """
        # Create output directory
        output_path = Path(self.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate JSON report
        json_path = output_path / "gap_report.json"
        self._generate_json(json_path)

        # Generate Markdown summary
        md_path = output_path / "gap_summary.md"
        self._generate_markdown(md_path)

        return ReportPaths(
            json_path=str(json_path),
            md_path=str(md_path)
        )

    def _generate_json(self, output_path: Path) -> None:
        """Generate JSON report.

        Args:
            output_path: Path for JSON output
        """
        summary = self._compute_summary()

        spec_features_count = len(self.spec.feature_items)
        code_items_count = sum(len(m.items) for m in self.code.modules)

        report = {
            "generated_at": datetime.now().isoformat(),
            "spec_file": getattr(self.spec.metadata, 'title', 'Unknown'),
            "implement_dir": "implement/",
            "summary": {
                "total_gaps": summary.total_gaps,
                "missing": summary.missing,
                "incomplete": summary.incomplete,
                "orphaned": summary.orphaned,
                "critical": summary.critical,
                "major": summary.major,
                "minor": summary.minor,
                "parsing_success_rate": self.spec.parse_stats.parse_success_rate,
                "scan_coverage_rate": self.code.scan_stats.scan_coverage_rate,
                "gap_detection_accuracy": None
            },
            "gaps": [
                self._gap_to_dict(gap) for gap in self.gaps
            ],
            "spec_features_count": spec_features_count,
            "code_items_count": code_items_count
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_markdown(self, output_path: Path) -> None:
        """Generate Markdown summary report.

        Args:
            output_path: Path for Markdown output
        """
        summary = self._compute_summary()

        lines = [
            "# Gap Summary Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Spec:** {getattr(self.spec.metadata, 'title', 'Unknown')}",
            "",
            "## Overview",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Gaps | {summary.total_gaps} |",
            f"| MISSING | {summary.missing} |",
            f"| INCOMPLETE | {summary.incomplete} |",
            f"| ORPHANED | {summary.orphaned} |",
            f"| Critical | {summary.critical} |",
            f"| Major | {summary.major} |",
            f"| Minor | {summary.minor} |",
            "",
            "## Statistics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Parsing Success Rate | {self.spec.parse_stats.parse_success_rate * 100:.1f}% |",
            f"| Scan Coverage Rate | {self.code.scan_stats.scan_coverage_rate * 100:.1f}% |",
            f"| Spec Features | {len(self.spec.feature_items)} |",
            f"| Code Items | {sum(len(m.items) for m in self.code.modules)} |",
            "",
        ]

        # MISSING gaps section
        missing_gaps = [g for g in self.gaps if g.gap_type == "MISSING"]
        if missing_gaps:
            lines.extend([
                "## Missing Features (Critical/Major)",
                "",
                "| Feature | Location | Severity | Reason |",
                "|---------|----------|----------|--------|",
            ])
            for gap in missing_gaps:
                lines.append(
                    f"| {gap.spec_item or 'N/A'} | {gap.spec_location or 'N/A'} | "
                    f"{gap.severity} | {gap.reason[:50]}... |"
                )
            lines.append("")

        # INCOMPLETE gaps section
        incomplete_gaps = [g for g in self.gaps if g.gap_type == "INCOMPLETE"]
        if incomplete_gaps:
            lines.extend([
                "## Incomplete Features",
                "",
                "| Feature | Code | Location | Severity | Reason |",
                "|---------|------|----------|----------|--------|",
            ])
            for gap in incomplete_gaps:
                lines.append(
                    f"| {gap.spec_item or 'N/A'} | {gap.code_item or 'N/A'} | "
                    f"{gap.code_location or 'N/A'} | {gap.severity} | {gap.reason[:40]}... |"
                )
            lines.append("")

        # ORPHANED gaps section
        orphaned_gaps = [g for g in self.gaps if g.gap_type == "ORPHANED"]
        if orphaned_gaps:
            lines.extend([
                "## Orphaned Code (No Spec)",
                "",
                "| Code Item | Location | Reason |",
                "|-----------|----------|--------|",
            ])
            for gap in orphaned_gaps[:10]:  # Limit to 10
                lines.append(
                    f"| {gap.code_item or 'N/A'} | {gap.code_location or 'N/A'} | "
                    f"{gap.reason[:50]}... |"
                )
            if len(orphaned_gaps) > 10:
                lines.append(f"| ... and {len(orphaned_gaps) - 10} more | | |")
            lines.append("")

        # Recommended actions section
        lines.extend([
            "## Recommended Actions",
            "",
        ])

        if missing_gaps:
            critical_missing = [g for g in missing_gaps if g.severity == "critical"]
            if critical_missing:
                lines.append("### Critical Priority")
                for gap in critical_missing:
                    lines.append(f"- **{gap.spec_item}**: {gap.recommended_action}")
                lines.append("")

            major_missing = [g for g in missing_gaps if g.severity == "major"]
            if major_missing:
                lines.append("### Major Priority")
                for gap in major_missing:
                    lines.append(f"- **{gap.spec_item}**: {gap.recommended_action}")
                lines.append("")

        if incomplete_gaps:
            lines.append("### Incomplete Features")
            for gap in incomplete_gaps:
                lines.append(f"- **{gap.spec_item}** ({gap.code_item}): {gap.recommended_action}")
            lines.append("")

        if orphaned_gaps:
            lines.append("### Orphaned Code Review")
            for gap in orphaned_gaps[:5]:
                lines.append(f"- **{gap.code_item}**: {gap.recommended_action}")

        lines.append("")
        lines.append("---")
        lines.append("*Report generated by Gap Detection Agent*")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _compute_summary(self) -> GapSummary:
        """Compute summary statistics from gaps.

        Returns:
            GapSummary: Summary statistics
        """
        summary = GapSummary()
        summary.total_gaps = len(self.gaps)

        for gap in self.gaps:
            if gap.gap_type == "MISSING":
                summary.missing += 1
            elif gap.gap_type == "INCOMPLETE":
                summary.incomplete += 1
            elif gap.gap_type == "ORPHANED":
                summary.orphaned += 1

            if gap.severity == "critical":
                summary.critical += 1
            elif gap.severity == "major":
                summary.major += 1
            elif gap.severity == "minor":
                summary.minor += 1

        return summary

    def _gap_to_dict(self, gap: Gap) -> dict:
        """Convert a Gap to a dictionary.

        Args:
            gap: Gap object

        Returns:
            dict: Dictionary representation
        """
        return {
            "gap_type": gap.gap_type,
            "spec_item": gap.spec_item,
            "code_item": gap.code_item,
            "spec_location": gap.spec_location,
            "code_location": gap.code_location,
            "severity": gap.severity,
            "reason": gap.reason,
            "recommended_action": gap.recommended_action,
            "downstream_missing": gap.downstream_missing
        }
