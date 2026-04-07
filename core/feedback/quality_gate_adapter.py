"""
QualityGate → Feedback Adapter.

Transforms AutoQualityGate violation results into StandardFeedback items
and submits them to the feedback loop.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .feedback import StandardFeedback, FeedbackStore
from .severity import calculate_severity

if TYPE_CHECKING:
    from ..quality_gate import Violation


# ---------------------------------------------------------------------------
# Severity Mapping
# ---------------------------------------------------------------------------

def _map_violation_to_severity(violation: dict[str, Any]) -> tuple[float, float]:
    """
    Map a QualityGate violation dict to (impact, urgency) scores.

    Scoring rationale:
    - Linter 'error'  → impact 4, urgency 4  (high/high → 'high')
    - Linter 'warning' → impact 3, urgency 3 (medium/medium → 'medium')
    - Linter 'convention' → impact 2, urgency 2 (low/low → 'low')
    - Complexity: impact scales with how far CC exceeds threshold
      (e.g., CC 15 vs threshold 10 → impact 4)
    - Coverage: impact grows with depth of shortfall
      (e.g., 50% vs 80% target → impact 4)
    - Style: always low (impact 1, urgency 2 → 'low')

    Returns:
        Tuple of (impact: float, urgency: float), each in [1, 5].
    """
    check_type = violation.get("check_type", "")
    severity_label = violation.get("severity", "warning")
    extra = violation.get("extra", {})

    if check_type == "linter":
        if severity_label == "error":
            return 4.0, 4.0
        elif severity_label == "warning":
            return 3.0, 3.0
        else:  # convention, info
            return 2.0, 2.0

    elif check_type == "complexity":
        cc = extra.get("cc", 0)
        threshold = extra.get("threshold", 10)
        overage = max(0, cc - threshold)
        # 1-5 scale: 0 over = 2, 5 over = 3, 10 over = 4, 15+ over = 5
        impact = min(5.0, 2.0 + overage * 0.2)
        urgency = 3.0  # complexity is usually non-critical but should be addressed
        return impact, urgency

    elif check_type == "coverage":
        coverage = extra.get("coverage", 100.0)
        min_cov = extra.get("min_coverage", 80.0)
        shortfall = max(0.0, min_cov - coverage)
        # 0% shortfall = impact 2, 30%+ shortfall = impact 5
        impact = min(5.0, 2.0 + shortfall * 0.1)
        urgency = 2.5 + (shortfall / 100.0) * 2.5  # urgency 2.5-5.0
        return impact, min(5.0, impact)

    elif check_type == "style":
        return 1.5, 1.5

    # Fallback
    return 2.5, 2.5


# ---------------------------------------------------------------------------
# Category Mapping
# ---------------------------------------------------------------------------

_VIOLATION_CATEGORY_MAP: dict[str, str] = {
    "linter":    "code_quality",
    "complexity": "architecture",
    "coverage":  "testing",
    "style":     "code_quality",
}


def _category_for(check_type: str) -> str:
    """Return the FeedbackCategory string for a check type."""
    return _VIOLATION_CATEGORY_MAP.get(check_type, "code_quality")


# ---------------------------------------------------------------------------
# SLA Deadline (hours) — mirrors SLA_CONFIG severity levels
# ---------------------------------------------------------------------------

_SEVERITY_SLA_HOURS: dict[str, int] = {
    "critical": 4,
    "high":     24,
    "medium":   72,
    "low":      168,
    "info":     720,
}


def _sla_deadline_for_severity(severity: str) -> str:
    hours = _SEVERITY_SLA_HOURS.get(severity, 72)
    deadline = datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=hours)
    return deadline.isoformat()


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class QualityGateFeedbackAdapter:
    """
    Converts QualityGate output into StandardFeedback and submits to the loop.

    Usage:
        store = FeedbackStore()
        adapter = QualityGateFeedbackAdapter(store)
        feedbacks = adapter.on_quality_gate_complete(
            gate_result=gate_result_dict,
            phase=2,
            artifacts={...},
        )
    """

    def __init__(self, feedback_store: FeedbackStore) -> None:
        self.store = feedback_store

    def on_quality_gate_complete(
        self,
        gate_result: dict[str, Any],
        phase: int,
        artifacts: dict[str, Any],
    ) -> list[StandardFeedback]:
        """
        Called when a QualityGate check completes.

        Transforms each violation in gate_result['violations'] into a
        StandardFeedback item, routes it, and stores it.

        Args:
            gate_result: The result dict from AutoQualityGate.check().
            phase: Current methodology phase.
            artifacts: The artifacts dict originally passed to check().

        Returns:
            List of StandardFeedback objects created.
        """
        violations = gate_result.get("violations", [])
        created: list[StandardFeedback] = []

        for violation in violations:
            fb = self._create_feedback_from_violation(violation, gate_result)
            if fb is None:
                continue

            # Add to store
            self.store.add(fb)

            # Route and assign — store.update sets assignee; re-fetch to return updated object
            from .router import route_and_assign

            team, deadline = route_and_assign(fb, store=self.store)
            fb = self.store.get(fb.id)  # re-fetch to get assignee set by route_and_assign
            if fb:
                fb.sla_deadline = deadline
            else:
                continue

            created.append(fb)

        return created

    def _create_feedback_from_violation(
        self,
        violation: dict[str, Any],
        gate_result: dict[str, Any],
    ) -> StandardFeedback | None:
        """
        Build a StandardFeedback from a single violation dict.

        Args:
            violation: One entry from gate_result['violations'].
            gate_result: Full gate result dict (for timestamp, phase).

        Returns:
            A populated StandardFeedback (unsaved), or None if skipped.
        """
        check_type = violation.get("check_type", "unknown")
        rule_id = violation.get("rule_id", "UNKNOWN")
        message = violation.get("message", "")
        file_path = violation.get("file")
        line = violation.get("line")
        severity_label = violation.get("severity", "warning")
        extra = violation.get("extra", {})

        # Skip 'info' severity style violations to reduce noise
        if check_type == "style" and severity_label == "info":
            return None

        # Compute impact/urgency → severity string
        impact, urgency = _map_violation_to_severity(violation)
        computed_severity = calculate_severity(impact, urgency)

        # Category
        category = _category_for(check_type)

        # Title: truncate message for readability
        title = message[:120] if message else f"{check_type}:{rule_id}"
        if len(message) > 120:
            title = message[:117] + "..."

        # Description
        description = (
            f"QualityGate [{check_type}] violation: {rule_id}\n"
            f"Phase: {gate_result.get('phase', '?')}\n"
            f"Message: {message}\n"
            f"File: {file_path or 'N/A'}  Line: {line or 'N/A'}"
        )

        # Source / source_detail
        source = "quality_gate"
        source_detail = f"{check_type}:{rule_id}"
        if file_path:
            source_detail += f":{file_path}"
            if line:
                source_detail += f":{line}"

        # Context
        context: dict[str, Any] = {
            "phase": gate_result.get("phase"),
            "gate_timestamp": gate_result.get("timestamp"),
            "check_type": check_type,
            "file": file_path,
            "line": line,
            "column": violation.get("column"),
            "rule_id": rule_id,
            "violation_severity": severity_label,
            "extra": extra,
            "gate_passed": gate_result.get("passed", False),
        }

        # Tags
        tags = [
            "quality-gate",
            check_type,
            severity_label,
        ]

        # SLA deadline (will be overridden by route_and_assign if called)
        sla_deadline = _sla_deadline_for_severity(computed_severity)

        fb = StandardFeedback(
            id=str(uuid.uuid4()),
            source=source,
            source_detail=source_detail,
            type=severity_label,
            category=category,
            severity=computed_severity,
            title=title,
            description=description,
            context=context,
            timestamp=datetime.now(timezone.utc).isoformat(),
            sla_deadline=sla_deadline,
            status="pending",
            tags=tags,
        )

        return fb
