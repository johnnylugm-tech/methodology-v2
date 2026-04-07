"""
Constitution Feedback Adapter.

Converts Constitution HR-01~HR-15 and TH-01~TH-08 violations
into StandardFeedback items and routes them through the feedback loop.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .feedback import FeedbackStore, StandardFeedback
from .severity import calculate_severity
from .router import route_and_assign

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Severity mapping: rule_id → (impact_level, urgency_level)
# Numeric levels 1–5 mapped from severity strings.
# ---------------------------------------------------------------------------
# Mapping: severity string → numeric level (1=info/lowest, 5=critical/highest)
_SEVERITY_NUMERIC: dict[str, float] = {
    "info": 1.0,
    "low": 2.0,
    "medium": 3.0,
    "high": 4.0,
    "critical": 5.0,
}

# HR-01 ~ HR-15 and TH-01 ~ TH-08 severity mapping
# Format: rule_id → (impact_label, urgency_label)
CONSTITUTION_HR_SEVERITY: dict[str, tuple[str, str]] = {
    "HR-01": ("critical", "critical"),
    "HR-02": ("high", "high"),
    "HR-03": ("high", "high"),       # Phase order violated
    "HR-04": ("medium", "medium"),
    "HR-05": ("medium", "medium"),
    "HR-06": ("high", "high"),
    "HR-07": ("high", "critical"),   # Missing citation — urgency bumped to critical
    "HR-08": ("medium", "medium"),
    "HR-09": ("high", "high"),       # Claims not supported by citations
    "HR-10": ("high", "high"),       # Subagent isolation violated
    "HR-11": ("critical", "high"),
    "HR-12": ("medium", "medium"),  # A/B review threshold
    "HR-13": ("medium", "high"),    # Phase timeout — urgency bumped
    "HR-14": ("high", "high"),
    "HR-15": ("high", "high"),       # Artifact read before proceeding
    "TH-01": ("high", "high"),
    "TH-02": ("medium", "medium"),
    "TH-03": ("medium", "low"),
    "TH-04": ("low", "low"),
    "TH-05": ("medium", "medium"),
    "TH-06": ("low", "low"),
    "TH-07": ("medium", "medium"),  # Confidence calibration
    "TH-08": ("low", "low"),
}


class ConstitutionFeedbackAdapter:
    """
    Converts Constitution runner violations into StandardFeedback.

    Integrates with the feedback loop by:
    1. Converting violations to feedback with pre-configured severity
    2. Routing to the appropriate team via route_and_assign()
    3. Storing in the FeedbackStore
    """

    def __init__(self, feedback_store: FeedbackStore) -> None:
        self.store = feedback_store

    def on_constitution_check_complete(
        self,
        constitution_result: dict,
        phase: int,
        artifacts: dict | None = None,
    ) -> list[StandardFeedback]:
        """
        Called automatically when a Constitution check completes.

        Args:
            constitution_result: Output from the Constitution runner.
                                 Expected keys: {"violations": [{"rule_id", "message", "artifact", "line", ...}]}
            phase: Current Phase number.
            artifacts: Optional dict of artifact paths (e.g. {"spec": "/path/to/spec.md"}).

        Returns:
            List of StandardFeedback objects created and stored.
        """
        violations = constitution_result.get("violations", [])
        feedbacks: list[StandardFeedback] = []

        for v in violations:
            rule_id = v.get("rule_id", "unknown")

            impact_label, urgency_label = CONSTITUTION_HR_SEVERITY.get(
                rule_id, ("medium", "medium")
            )
            impact_num = _SEVERITY_NUMERIC.get(impact_label, 3.0)
            urgency_num = _SEVERITY_NUMERIC.get(urgency_label, 3.0)

            severity = calculate_severity(impact_num, urgency_num)

            feedback = StandardFeedback(
                id=self._generate_id(),
                source="constitution",
                source_detail=rule_id,
                type="violation",
                category="quality",
                severity=severity,
                title=f"Constitution violation: {rule_id}",
                description=v.get("message", "No description"),
                context={
                    "phase": phase,
                    "artifact": v.get("artifact"),
                    "line": v.get("line"),
                    "rule_id": rule_id,
                    **(artifacts or {}),
                },
                timestamp=self._now(),
                sla_deadline="",  # filled by route_and_assign
                status="pending",
                assignee=None,
                resolution=None,
                verified_at=None,
                related_feedbacks=[],
                recurrence_count=self._count_recurrence(rule_id),
                confidence=0.95,
                tags=["constitution", "hr-rule", rule_id],
            )

            # Add to store first, then route (route_and_assign calls store.update)
            self.store.add(feedback)
            team, deadline = route_and_assign(feedback, store=self.store)
            feedback.assignee = team
            feedback.sla_deadline = deadline

            feedbacks.append(feedback)

        return feedbacks

    def _count_recurrence(self, rule_id: str) -> int:
        """Count how many times this rule_id has already been recorded."""
        existing = [
            f for f in self.store.list_all()
            if f.source == "constitution" and f.source_detail == rule_id
        ]
        return len(existing)

    @staticmethod
    def _generate_id() -> str:
        return f"constitution-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
