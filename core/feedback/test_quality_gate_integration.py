"""
Integration tests for QualityGate → Feedback Loop.

Validates that AutoQualityGate violations are correctly transformed into
StandardFeedback items and stored with proper severity, status, and SLA.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure core/ is on the path
CORE = Path(__file__).parent.parent
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

import unittest

from feedback.feedback import FeedbackStore
from feedback.severity import calculate_severity
from core.quality_gate import AutoQualityGate, Violation
from quality_gate.feedback_hook import AutoQualityGateWithFeedback
from feedback.quality_gate_adapter import QualityGateFeedbackAdapter


class TestQualityGateAdapter(unittest.TestCase):
    """Tests for QualityGateFeedbackAdapter."""

    def setUp(self) -> None:
        self.store = FeedbackStore()
        self.adapter = QualityGateFeedbackAdapter(self.store)

    # ------------------------------------------------------------------
    # Linter violation tests
    # ------------------------------------------------------------------

    def test_linter_error_produces_high_severity_feedback(self) -> None:
        """Linter 'error' violation → impact 4, urgency 4 → 'high' severity."""
        gate_result = {
            "phase": 2,
            "passed": False,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "E999",
                    "message": "Syntax error: invalid syntax",
                    "file": "src/main.py",
                    "line": 10,
                    "column": 5,
                    "severity": "error",
                    "extra": {},
                }
            ],
            "checks_run": ["linter"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=2,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        fb = feedbacks[0]
        self.assertEqual(fb.source, "quality_gate")
        self.assertIn("linter:E999", fb.source_detail)
        self.assertEqual(fb.category, "code_quality")
        self.assertEqual(fb.type, "error")
        self.assertEqual(fb.severity, "high")
        self.assertEqual(fb.status, "pending")
        self.assertIsNotNone(fb.sla_deadline)
        self.assertEqual(fb.context["phase"], 2)
        self.assertEqual(fb.context["check_type"], "linter")
        self.assertEqual(fb.context["file"], "src/main.py")
        self.assertEqual(fb.context["line"], 10)
        # Verify stored in store
        stored = self.store.get(fb.id)
        self.assertIsNotNone(stored)

    def test_linter_warning_produces_medium_severity_feedback(self) -> None:
        """Linter 'warning' violation → impact 3, urgency 3 → 'medium' severity."""
        gate_result = {
            "phase": 1,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "W0611",
                    "message": "Unused import os",
                    "file": "src/utils.py",
                    "line": 3,
                    "column": 1,
                    "severity": "warning",
                    "extra": {},
                }
            ],
            "checks_run": ["linter"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=1,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        fb = feedbacks[0]
        self.assertEqual(fb.severity, "medium")
        self.assertEqual(fb.type, "warning")
        self.assertIn("utils.py", fb.source_detail)

    def test_linter_convention_produces_low_severity_feedback(self) -> None:
        """Linter 'convention' violation → impact 2, urgency 2 → 'low' severity."""
        gate_result = {
            "phase": 2,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "E501",
                    "message": "line too long (max 120 characters)",
                    "file": "src/main.py",
                    "line": 5,
                    "column": 121,
                    "severity": "convention",
                    "extra": {},
                }
            ],
            "checks_run": ["linter"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=2,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(feedbacks[0].severity, "low")

    # ------------------------------------------------------------------
    # Complexity violation tests
    # ------------------------------------------------------------------

    def test_complexity_violation_maps_to_architecture_category(self) -> None:
        """Complexity violation → category architecture, severity based on CC."""
        gate_result = {
            "phase": 3,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "complexity",
                    "rule_id": "CC10p",
                    "message": "Function 'process' has CC=15 (threshold=10)",
                    "file": "src/core.py",
                    "line": 42,
                    "severity": "warning",
                    "extra": {"cc": 15, "threshold": 10},
                }
            ],
            "checks_run": ["complexity"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=3,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        fb = feedbacks[0]
        self.assertEqual(fb.category, "architecture")
        self.assertEqual(fb.context["check_type"], "complexity")
        self.assertEqual(fb.context["extra"]["cc"], 15)
        # CC 15 vs threshold 10 → overage 5 → impact ~3.0 → medium
        self.assertIn(fb.severity, ("medium", "high"))

    def test_high_complexity_violation_high_severity(self) -> None:
        """Very high CC (e.g., 30) → impact 5 → 'high' severity."""
        gate_result = {
            "phase": 4,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "complexity",
                    "rule_id": "CC10p",
                    "message": "Function 'handle_all' has CC=30",
                    "file": "src/main.py",
                    "line": 1,
                    "severity": "warning",
                    "extra": {"cc": 30, "threshold": 10},
                }
            ],
            "checks_run": ["complexity"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=4,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        # CC 30, threshold 10 → overage 20 → impact min(5.0, 2+4) = 5.0 → high
        self.assertEqual(feedbacks[0].severity, "high")

    # ------------------------------------------------------------------
    # Coverage gap tests
    # ------------------------------------------------------------------

    def test_coverage_violation_maps_to_testing_category(self) -> None:
        """Coverage violation → category testing."""
        gate_result = {
            "phase": 2,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "coverage",
                    "rule_id": "COVERAGE",
                    "message": "Overall coverage 60.0% is below minimum 80%",
                    "file": None,
                    "line": None,
                    "severity": "warning",
                    "extra": {"coverage": 60.0, "min_coverage": 80.0},
                }
            ],
            "checks_run": ["coverage"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=2,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        fb = feedbacks[0]
        self.assertEqual(fb.category, "testing")
        # 20% shortfall → impact ~4.0, urgency ~3.0 → medium
        self.assertIn(fb.severity, ("medium", "high"))

    # ------------------------------------------------------------------
    # Style violation tests
    # ------------------------------------------------------------------

    def test_style_violation_low_severity(self) -> None:
        """Style violation → category code_quality, low severity."""
        gate_result = {
            "phase": 1,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "style",
                    "rule_id": "IMPORT_ORDER",
                    "message": "Imports should be placed at the top of the file",
                    "file": "src/main.py",
                    "line": 20,
                    "severity": "info",
                    "extra": {},
                }
            ],
            "checks_run": ["style"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=1,
            artifacts={},
        )

        # Style 'info' violations are filtered out
        self.assertEqual(len(feedbacks), 0)

    def test_style_warning_violation_creates_feedback(self) -> None:
        """Style 'warning' level → creates feedback with low severity."""
        gate_result = {
            "phase": 1,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "style",
                    "rule_id": "NAMING",
                    "message": "Function name should use snake_case",
                    "file": "src/main.py",
                    "line": 5,
                    "severity": "warning",
                    "extra": {},
                }
            ],
            "checks_run": ["style"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=1,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(feedbacks[0].severity, "low")

    # ------------------------------------------------------------------
    # Severity matrix integration tests
    # ------------------------------------------------------------------

    def test_severity_matrix_boundaries(self) -> None:
        """Verify calculate_severity returns correct labels at matrix boundaries."""
        self.assertEqual(calculate_severity(1.0, 1.0), "info")
        self.assertEqual(calculate_severity(1.0, 5.0), "medium")
        self.assertEqual(calculate_severity(5.0, 1.0), "medium")
        self.assertEqual(calculate_severity(5.0, 5.0), "critical")
        self.assertEqual(calculate_severity(3.0, 3.0), "medium")
        self.assertEqual(calculate_severity(4.0, 4.0), "high")

    # ------------------------------------------------------------------
    # Store integration tests
    # ------------------------------------------------------------------

    def test_multiple_violations_all_stored(self) -> None:
        """All violations produce feedback and are stored."""
        gate_result = {
            "phase": 2,
            "passed": False,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "E999",
                    "message": "Syntax error",
                    "file": "a.py",
                    "line": 1,
                    "severity": "error",
                    "extra": {},
                },
                {
                    "check_type": "linter",
                    "rule_id": "W0611",
                    "message": "Unused import",
                    "file": "b.py",
                    "line": 2,
                    "severity": "warning",
                    "extra": {},
                },
                {
                    "check_type": "complexity",
                    "rule_id": "CC10p",
                    "message": "CC=12",
                    "file": "c.py",
                    "line": 3,
                    "severity": "warning",
                    "extra": {"cc": 12, "threshold": 10},
                },
            ],
            "checks_run": ["linter", "complexity"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=2,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 3)
        # All should be in store
        for fb in feedbacks:
            stored = self.store.get(fb.id)
            self.assertIsNotNone(stored, f"Feedback {fb.id} not found in store")
            self.assertEqual(stored.status, "pending")
            self.assertIsNotNone(stored.sla_deadline)

    def test_sla_deadline_is_iso_format(self) -> None:
        """SLA deadline must be a valid ISO 8601 timestamp string."""
        gate_result = {
            "phase": 1,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "W0611",
                    "message": "Unused import",
                    "file": "x.py",
                    "line": 1,
                    "severity": "warning",
                    "extra": {},
                }
            ],
            "checks_run": ["linter"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=1,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        deadline = feedbacks[0].sla_deadline
        # Should parse as ISO without error
        from datetime import datetime
        parsed = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        self.assertIsInstance(parsed, datetime)

    def test_feedback_assignee_set_by_route_and_assign(self) -> None:
        """After routing, feedback should have an assignee and updated sla_deadline."""
        gate_result = {
            "phase": 2,
            "passed": True,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "violations": [
                {
                    "check_type": "linter",
                    "rule_id": "E501",
                    "message": "Line too long",
                    "file": "src/main.py",
                    "line": 5,
                    "severity": "convention",
                    "extra": {},
                }
            ],
            "checks_run": ["linter"],
            "check_results": [],
        }

        feedbacks = self.adapter.on_quality_gate_complete(
            gate_result=gate_result,
            phase=2,
            artifacts={},
        )

        self.assertEqual(len(feedbacks), 1)
        fb = feedbacks[0]
        # code_quality → team "platform", default_assignee "code-health"
        self.assertEqual(fb.assignee, "code-health")


class TestAutoQualityGateWithFeedback(unittest.TestCase):
    """Tests for the AutoQualityGateWithFeedback hook."""

    def setUp(self) -> None:
        self.store = FeedbackStore()

    def test_check_with_store_creates_feedback(self) -> None:
        """AutoQualityGateWithFeedback.check() automatically creates feedback."""
        gate = AutoQualityGateWithFeedback(feedback_store=self.store)

        artifacts = {
            "linter_output": [
                {
                    "rule": "E999",
                    "message": "Syntax error",
                    "file": "main.py",
                    "line": 1,
                    "severity": "error",
                    "extra": {},
                }
            ]
        }

        result = gate.check(phase=3, artifacts=artifacts)

        self.assertFalse(result["passed"])
        self.assertEqual(len(result["violations"]), 1)
        # Feedback should be in store
        stored = self.store.list_by_source("quality_gate")
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].context["phase"], 3)
        self.assertEqual(stored[0].type, "error")

    def test_no_store_no_error(self) -> None:
        """Gate without a feedback_store still runs and returns results."""
        gate = AutoQualityGateWithFeedback()  # no store
        result = gate.check(
            phase=1,
            artifacts={"linter_output": [{"rule": "E501", "message": "Long line", "file": "x.py", "line": 1, "severity": "warning", "extra": {}}]},
        )
        self.assertTrue(result["passed"])  # only warnings, no errors

    def test_complexity_violation_auto_submitted(self) -> None:
        """Complexity violations are auto-submitted to store (gate passes with warnings)."""
        gate = AutoQualityGateWithFeedback(feedback_store=self.store)

        artifacts = {
            "functions": [
                {"name": "handle_everything", "file": "core.py", "start_line": 10, "cc": 20}
            ]
        }

        result = gate.check(phase=4, artifacts=artifacts)

        # Complexity violations are 'warning' severity → gate still passes (only errors fail)
        self.assertTrue(result["passed"])
        stored = self.store.list_by_source("quality_gate")
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].category, "architecture")

    def test_gate_passed_no_error_violations_still_feedback_for_warnings(self) -> None:
        """Gate 'passed' (no errors) but with warnings → feedback still created."""
        gate = AutoQualityGateWithFeedback(feedback_store=self.store)

        artifacts = {
            "linter_output": [
                {"rule": "W0611", "message": "Unused import", "file": "x.py", "line": 1, "severity": "warning", "extra": {}}
            ]
        }

        result = gate.check(phase=1, artifacts=artifacts)

        # Passed = no error-level violations; warnings don't fail the gate
        self.assertTrue(result["passed"])
        stored = self.store.list_by_source("quality_gate")
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].severity, "medium")


class TestViolationToSeverityMapping(unittest.TestCase):
    """Unit tests for _map_violation_to_severity."""

    def test_linter_error_impact_urgency(self) -> None:
        from feedback.quality_gate_adapter import _map_violation_to_severity
        impact, urgency = _map_violation_to_severity({
            "check_type": "linter",
            "severity": "error",
            "extra": {},
        })
        self.assertEqual(impact, 4.0)
        self.assertEqual(urgency, 4.0)
        self.assertEqual(calculate_severity(impact, urgency), "high")

    def test_linter_warning_impact_urgency(self) -> None:
        from feedback.quality_gate_adapter import _map_violation_to_severity
        impact, urgency = _map_violation_to_severity({
            "check_type": "linter",
            "severity": "warning",
            "extra": {},
        })
        self.assertEqual(impact, 3.0)
        self.assertEqual(urgency, 3.0)
        self.assertEqual(calculate_severity(impact, urgency), "medium")

    def test_complexity_moderate_overage(self) -> None:
        from feedback.quality_gate_adapter import _map_violation_to_severity
        impact, urgency = _map_violation_to_severity({
            "check_type": "complexity",
            "severity": "warning",
            "extra": {"cc": 15, "threshold": 10},
        })
        # overage=5, impact=2+1=3
        self.assertAlmostEqual(impact, 3.0, places=1)

    def test_coverage_deep_shortfall(self) -> None:
        from feedback.quality_gate_adapter import _map_violation_to_severity
        impact, urgency = _map_violation_to_severity({
            "check_type": "coverage",
            "severity": "warning",
            "extra": {"coverage": 40.0, "min_coverage": 80.0},
        })
        # shortfall=40, impact=2+4=6 → clamped to 5
        self.assertEqual(impact, 5.0)


if __name__ == "__main__":
    unittest.main()
