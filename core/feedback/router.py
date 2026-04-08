"""
SLA + Routing Engine.

Routes feedback to appropriate teams and calculates SLA deadlines.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from .feedback import StandardFeedback, FeedbackStore, FeedbackUpdate, get_store


# ---------------------------------------------------------------------------
# SLA Configuration
# ---------------------------------------------------------------------------

@dataclass
class SLAConfig:
    """
    SLA timing configuration for a severity level.

    Attributes:
        response_hours: Max hours before first response.
        resolution_hours: Max hours before resolution.
        escalation_hours: Hours before escalating to next level.
    """

    response_hours: int
    resolution_hours: int
    escalation_hours: int


# hours for each severity level
SLA_CONFIG: dict[str, SLAConfig] = {
    "critical": SLAConfig(response_hours=1, resolution_hours=4, escalation_hours=2),
    "high":     SLAConfig(response_hours=4, resolution_hours=24, escalation_hours=8),
    "medium":   SLAConfig(response_hours=24, resolution_hours=72, escalation_hours=24),
    "low":      SLAConfig(response_hours=72, resolution_hours=168, escalation_hours=48),
    "info":     SLAConfig(response_hours=168, resolution_hours=720, escalation_hours=168),
}


# ---------------------------------------------------------------------------
# Routing Rules
# ---------------------------------------------------------------------------

@dataclass
class RoutingRule:
    """
    Routing rule mapping a category to a team.

    Attributes:
        category: Feedback category this rule applies to.
        team: Target team name.
        default_assignee: Fallback assignee within the team.
        severity_overrides: Override SLA for specific severities.
    """

    category: str
    team: str
    default_assignee: str | None = None
    severity_overrides: dict[str, SLAConfig] = field(default_factory=dict)


ROUTING_RULES: list[RoutingRule] = [
    RoutingRule(category="security",           team="security",       default_assignee="security-lead"),
    RoutingRule(category="performance",         team="backend",        default_assignee="perf-owner"),
    RoutingRule(category="bug",                 team="backend",        default_assignee="bug-triage"),
    RoutingRule(category="code_quality",       team="platform",       default_assignee="code-health"),
    RoutingRule(category="architecture",        team="platform",       default_assignee="arch-review"),
    RoutingRule(category="compliance",         team="security",       default_assignee="compliance-officer"),
    RoutingRule(category="testing",            team="qa",             default_assignee="qa-lead"),
    RoutingRule(category="operational",        team="ops",            default_assignee="ops-oncall"),
    RoutingRule(category="ux",                 team="design",         default_assignee="ux-lead"),
    RoutingRule(category="documentation",      team="platform",       default_assignee="docs-guardian"),
]


def _find_rule(category: str) -> RoutingRule | None:
    """Find the first routing rule matching the given category."""
    for rule in ROUTING_RULES:
        if rule.category == category:
            return rule
    return None


def _make_deadline(hours: int, from_time: datetime | None = None) -> str:
    """Create an ISO timestamp deadline N hours from now."""
    if from_time is None:
        from_time = datetime.now(timezone.utc)
    deadline = from_time + timedelta(hours=hours)
    return deadline.isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def route_and_assign(
    feedback: StandardFeedback,
    store: FeedbackStore | None = None,
) -> tuple[str, str]:
    """
    Route feedback to the appropriate team and compute SLA deadline.

    Args:
        feedback: The feedback item to route.
        store: Optional feedback store (uses global store if None).

    Returns:
        Tuple of (team_name, sla_deadline_iso).
    """
    if store is None:
        store = get_store()

    rule = _find_rule(feedback.category)

    if rule:
        team = rule.team
    else:
        team = "general"

    # Determine SLA config (severity override or default)
    if rule and feedback.severity in rule.severity_overrides:
        sla = rule.severity_overrides[feedback.severity]
    else:
        sla = SLA_CONFIG.get(feedback.severity, SLA_CONFIG["medium"])

    deadline = _make_deadline(sla.resolution_hours)

    # Update the feedback with team and deadline
    fb_updated = store.update(
        feedback.id,
        FeedbackUpdate(assignee=rule.default_assignee if rule else None),
    )
    # Return deadline; avoid direct mutation of the stored object
    return team, deadline


def get_pending_by_sla(
    hours_ahead: float = 0.0,
    store: FeedbackStore | None = None,
) -> list[StandardFeedback]:
    """
    Return all open feedback items whose SLA deadline has passed
    or will pass within `hours_ahead`.

    Args:
        hours_ahead: Include items expiring within this window.
                     0 = only already-expired. 24 = expiring within 24h.
        store: Optional feedback store (uses global store if None).

    Returns:
        List of feedback items with missed or upcoming SLA deadlines.
    """
    if store is None:
        store = get_store()

    now = datetime.now(timezone.utc)
    threshold = now + timedelta(hours=hours_ahead)

    overdue: list[StandardFeedback] = []
    for fb in store.list_open():
        if not fb.sla_deadline:
            continue
        try:
            deadline_dt = datetime.fromisoformat(fb.sla_deadline.replace("Z", "+00:00"))
        except ValueError:
            continue

        if hours_ahead == 0:
            # Strict overdue check
            if deadline_dt < now:
                overdue.append(fb)
        else:
            if deadline_dt < threshold:
                overdue.append(fb)

    return overdue


def sla_deadline_for(feedback: StandardFeedback) -> str:
    """Compute SLA deadline for a feedback item (no routing)."""
    sla = SLA_CONFIG.get(feedback.severity, SLA_CONFIG["medium"])
    return _make_deadline(sla.resolution_hours)


def team_for(category: str) -> str:
    """Look up the team for a category."""
    rule = _find_rule(category)
    return rule.team if rule else "general"


def response_deadline_for(feedback: StandardFeedback) -> str:
    """Compute first-response deadline for a feedback item."""
    sla = SLA_CONFIG.get(feedback.severity, SLA_CONFIG["medium"])
    return _make_deadline(sla.response_hours)