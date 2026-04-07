"""
Quality Gate Core Module.

Provides AutoQualityGate — a configurable quality gate that runs a suite
of checks (linter, complexity, coverage, style) and returns structured results.
"""

from __future__ import annotations

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Result Structures
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    """
    A single quality violation found by a check.

    Attributes:
        check_type: One of 'linter', 'complexity', 'coverage', 'style'.
        rule_id: Identifier of the rule that was violated (e.g., 'E501', 'CC2').
        message: Human-readable description.
        file: File path where the violation occurred (or None for project-level).
        line: Line number (1-indexed), or None.
        column: Column number, or None.
        severity: 'error', 'warning', 'convention', or 'info'.
        extra: Additional context dict (e.g., {'cc': 12, 'threshold': 10}).
    """

    check_type: str
    rule_id: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None
    severity: str = "warning"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_type": self.check_type,
            "rule_id": self.rule_id,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "extra": self.extra,
        }


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

class BaseChecker:
    """Base class for individual quality checks."""

    name: str = "base"

    def run(self, artifacts: dict[str, Any]) -> list[Violation]:
        raise NotImplementedError


class LinterChecker(BaseChecker):
    """
    Mock linter checker.

    In production this would run ruff, pylint, or similar.
    Accepts artifacts with key 'linter_output' (list[dict]) or
    'files' (list of file paths to lint against a toy rule set).
    """

    name = "linter"

    # Toy rules for demonstration
    TOY_RULES = {
        "E501": ("line too long (max 120)", "convention"),
        "E303": ("too many blank lines", "warning"),
        "W0611": ("unused import", "warning"),
        "F401": ("imported but unused", "warning"),
        "E302": ("expected 2 blank lines", "convention"),
    }

    def run(self, artifacts: dict[str, Any]) -> list[Violation]:
        violations: list[Violation] = []
        linter_output = artifacts.get("linter_output", [])

        for entry in linter_output:
            rule_id = entry.get("rule", "UNKNOWN")
            level_from_tool = entry.get("severity", "warning")
            violations.append(
                Violation(
                    check_type="linter",
                    rule_id=rule_id,
                    message=entry.get("message", ""),
                    file=entry.get("file"),
                    line=entry.get("line"),
                    column=entry.get("column"),
                    severity=level_from_tool,
                    extra=entry.get("extra", {}),
                )
            )
        return violations


class ComplexityChecker(BaseChecker):
    """
    Cyclomatic complexity checker.

    Accepts artifacts with key 'functions' (list of {name, file, cc, lines}).
    Flags any function whose CC exceeds `threshold`.
    """

    name = "complexity"
    DEFAULT_THRESHOLD = 10

    def run(self, artifacts: dict[str, Any], threshold: int | None = None) -> list[Violation]:
        violations: list[Violation] = []
        threshold = threshold or self.DEFAULT_THRESHOLD
        functions = artifacts.get("functions", [])

        for func in functions:
            cc = func.get("cc", 0)
            if cc > threshold:
                violations.append(
                    Violation(
                        check_type="complexity",
                        rule_id=f"CC{threshold}p",
                        message=f"Function '{func.get('name', '?')}' has CC={cc} (threshold={threshold})",
                        file=func.get("file"),
                        line=func.get("start_line"),
                        severity="warning",
                        extra={"cc": cc, "threshold": threshold},
                    )
                )
        return violations


class CoverageChecker(BaseChecker):
    """
    Test coverage checker.

    Accepts artifacts with key 'coverage_report' ({total: float, files: dict}).
    Flags files below `min_coverage` %.
    """

    name = "coverage"
    DEFAULT_MIN_COVERAGE = 80.0

    def run(self, artifacts: dict[str, Any], min_coverage: float | None = None) -> list[Violation]:
        violations: list[Violation] = []
        min_coverage = min_coverage or self.DEFAULT_MIN_COVERAGE
        coverage_report = artifacts.get("coverage_report", {})

        total = coverage_report.get("total", 100.0)
        if total < min_coverage:
            violations.append(
                Violation(
                    check_type="coverage",
                    rule_id="COVERAGE",
                    message=f"Overall coverage {total:.1f}% is below minimum {min_coverage}%",
                    severity="warning",
                    extra={"coverage": total, "min_coverage": min_coverage},
                )
            )

        for file_entry in coverage_report.get("files", []):
            file_cov = file_entry.get("coverage", 100.0)
            if file_cov < min_coverage:
                violations.append(
                    Violation(
                        check_type="coverage",
                        rule_id="COVERAGE",
                        message=f"File {file_entry.get('file', '?')} coverage {file_cov:.1f}% below minimum {min_coverage}%",
                        file=file_entry.get("file"),
                        severity="warning",
                        extra={"coverage": file_cov, "min_coverage": min_coverage},
                    )
                )
        return violations


class StyleChecker(BaseChecker):
    """
    Style checker (toy).

    Accepts artifacts with key 'style_violations' (list of {file, line, message}).
    """

    name = "style"

    def run(self, artifacts: dict[str, Any]) -> list[Violation]:
        violations: list[Violation] = []
        for entry in artifacts.get("style_violations", []):
            violations.append(
                Violation(
                    check_type="style",
                    rule_id=entry.get("rule", "STYLE"),
                    message=entry.get("message", ""),
                    file=entry.get("file"),
                    line=entry.get("line"),
                    severity="info",
                    extra=entry.get("extra", {}),
                )
            )
        return violations


# ---------------------------------------------------------------------------
# AutoQualityGate
# ---------------------------------------------------------------------------

class AutoQualityGate:
    """
    Multi-check quality gate.

    Runs a configurable set of checkers against artifacts and returns
    a unified result dict.

    Usage:
        gate = AutoQualityGate()
        result = gate.check(phase=2, artifacts={...})
    """

    DEFAULT_CHECKERS: list[BaseChecker] = [
        LinterChecker(),
        ComplexityChecker(),
        CoverageChecker(),
        StyleChecker(),
    ]

    def __init__(
        self,
        checkers: list[BaseChecker] | None = None,
        fail_fast: bool = False,
        feedback_store: Any = None,  # Optional FeedbackStore for auto-submission
    ) -> None:
        self.checkers = checkers or self.DEFAULT_CHECKERS
        self.fail_fast = fail_fast
        self._feedback_store = feedback_store
        self._feedback_adapter: Any = None  # lazy import

    def _get_feedback_adapter(self) -> Any:
        """Lazily import and create the QualityGateFeedbackAdapter."""
        if self._feedback_adapter is None and self._feedback_store is not None:
            # Resolve from core/ level (where feedback/ is a sibling)
            core_dir = Path(__file__).parent
            if str(core_dir) not in sys.path:
                sys.path.insert(0, str(core_dir))
            from feedback.quality_gate_adapter import QualityGateFeedbackAdapter
            self._feedback_adapter = QualityGateFeedbackAdapter(self._feedback_store)
        return self._feedback_adapter

    def check(self, *, phase: int, artifacts: dict[str, Any]) -> dict[str, Any]:
        """
        Run all configured checkers.

        Args:
            phase: Current methodology phase (used in result metadata).
            artifacts: Arbitrary artifact dict passed to each checker.
                       Expected keys: 'linter_output', 'functions', 'coverage_report',
                       'style_violations'.

        Returns:
            dict with keys:
                - phase: int
                - passed: bool
                - timestamp: ISO 8601
                - violations: list[dict]  (Violation.to_dict() format)
                - checks_run: list[str]
                - check_results: list[dict]
        """
        all_violations: list[dict[str, Any]] = []
        checks_run: list[str] = []
        check_results: list[dict[str, Any]] = []
        passed = True

        for checker in self.checkers:
            checks_run.append(checker.name)
            try:
                violations = checker.run(artifacts)
            except Exception as exc:
                violations = [
                    Violation(
                        check_type=checker.name,
                        rule_id="CHECKER_ERROR",
                        message=f"Checker '{checker.name}' raised: {exc}",
                        severity="error",
                    ).to_dict()
                ]
                passed = False
                check_results.append({"checker": checker.name, "error": str(exc)})
                if self.fail_fast:
                    break
            else:
                check_results.append({"checker": checker.name, "violations": len(violations)})
                for v in violations:
                    all_violations.append(v.to_dict())
                    if v.severity == "error":
                        passed = False
                        if self.fail_fast:
                            break

        # Determine overall pass/fail
        error_violations = [v for v in all_violations if v.get("severity") == "error"]
        passed = passed and len(error_violations) == 0

        result = {
            "phase": phase,
            "passed": passed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "violations": all_violations,
            "checks_run": checks_run,
            "check_results": check_results,
        }

        # === Auto-submit violations to FeedbackStore via UnifiedAlert ===
        if self._feedback_store and all_violations:
            try:
                from core.feedback.alert import UnifiedAlert
                from core.feedback.router import route_and_assign

                for v in all_violations:
                    sev = v.get("severity", "medium")
                    alert = UnifiedAlert(
                        source="quality_gate",
                        source_detail=f"{v.get('check_type', 'unknown')}/{v.get('rule_id', 'unknown')}",
                        category="code_quality",
                        severity={"error": "high", "warning": "medium", "convention": "low", "info": "low"}.get(sev, "medium"),
                        title=f"Quality Gate: {v.get('check_type', 'check')} {sev}",
                        message=v.get("message", ""),
                        context={"phase": phase, "violation": v},
                        recommended_action=f"Fix {v.get('check_type')} issue",
                        auto_fixable=sev in ["error", "warning"],
                        sla_hours={"error": 4, "warning": 24, "convention": 72, "info": 168}.get(sev, 24),
                    )
                    fb = alert.to_feedback()
                    self._feedback_store.add(fb)
                    # Route and assign to populate assignee + sla_deadline
                    team, deadline = route_and_assign(fb, store=self._feedback_store)
                    fb["assignee"] = team
                    fb["sla_deadline"] = deadline
            except Exception:
                # Don't let feedback failures break the gate
                pass

        return result

    def run(self, *, phase: int, artifacts: dict[str, Any]) -> dict[str, Any]:
        """Alias for check() — kept for backward compatibility."""
        return self.check(phase=phase, artifacts=artifacts)
