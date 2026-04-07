"""
Dashboard Metrics.

Computes rich metrics from a FeedbackStore for dashboard consumption.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any

from .feedback import StandardFeedback, FeedbackStore, get_store
from .router import SLA_CONFIG


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DashboardMetrics:
    """Rich metrics structure for dashboard consumption."""

    # Overview
    total_feedback: int = 0
    pending: int = 0
    resolved: int = 0
    closed: int = 0

    # Rate indicators
    resolution_rate: float = 0.0
    avg_resolution_time_hours: float = 0.0

    # Breakdowns
    by_severity: dict[str, int] = field(default_factory=dict)
    by_source: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    by_status: dict[str, int] = field(default_factory=dict)

    # SLA status
    overdue: list[StandardFeedback] = field(default_factory=list)
    at_risk: list[StandardFeedback] = field(default_factory=list)

    # Recurring issues
    recurring: list[dict] = field(default_factory=list)

    # Trend (date -> count)
    trend_daily: dict[str, int] = field(default_factory=dict)

    # Team workload
    by_assignee: dict[str, int] = field(default_factory=dict)

    # Category insights
    category_insights: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON export."""
        return {
            "total_feedback": self.total_feedback,
            "pending": self.pending,
            "resolved": self.resolved,
            "closed": self.closed,
            "resolution_rate": round(self.resolution_rate, 4),
            "avg_resolution_time_hours": round(self.avg_resolution_time_hours, 2),
            "by_severity": self.by_severity,
            "by_source": self.by_source,
            "by_category": self.by_category,
            "by_status": self.by_status,
            "overdue": [fb.to_dict() for fb in self.overdue],
            "at_risk": [fb.to_dict() for fb in self.at_risk],
            "recurring": self.recurring,
            "trend_daily": self.trend_daily,
            "by_assignee": self.by_assignee,
            "category_insights": self.category_insights,
        }


# ---------------------------------------------------------------------------
# Insights generation
# ---------------------------------------------------------------------------

_SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "info": "🔵",
}

_CATEGORY_RECOMMENDATIONS: dict[str, str] = {
    "security": "Prioritize security feedback immediately. Consider emergency release.",
    "performance": "Profile the hot path. Latency issues compound over time.",
    "bug": "Write a failing test first. Reproduce the bug before fixing.",
    "code_quality": "Schedule refactoring sprint. Technical debt slows all future work.",
    "architecture": "Request arch review. Bad architecture compounds.",
    "compliance": "Escalate to compliance officer. Regulatory risk is non-negotiable.",
    "testing": "Increase test coverage. Every untested line is a liability.",
    "ux": "User test before changing. Assumptions about UX are expensive.",
    "documentation": "Update docs alongside code changes. Docs rot fast.",
    "operational": "Automate runbook steps. Operational toil scales poorly.",
}


def _compute_insights(
    by_category: dict[str, int],
    recurring: list[dict],
) -> dict[str, str]:
    """Generate a recommendation for each category."""
    insights: dict[str, str] = {}
    for cat in by_category:
        # Check if this category has recurring issues
        rec = next((r for r in recurring if r.get("category") == cat), None)
        if rec:
            insights[cat] = f"Recurring issue ({rec['count']}x). {rec.get('recommendation', _CATEGORY_RECOMMENDATIONS.get(cat, 'Investigate root cause.'))}"
        else:
            insights[cat] = _CATEGORY_RECOMMENDATIONS.get(cat, "Monitor and address normally.")
    return insights


# ---------------------------------------------------------------------------
# Main factory
# ---------------------------------------------------------------------------

def get_dashboard_metrics(
    store: FeedbackStore | None = None,
    days: int = 30,
) -> DashboardMetrics:
    """
    Compute full dashboard metrics from a feedback store.

    Args:
        store: FeedbackStore to analyze. Uses global store if None.
        days: Number of past days to consider for trends (not a hard filter
              on other metrics — all feedback is included in totals).

    Returns:
        DashboardMetrics instance.
    """
    if store is None:
        store = get_store()

    all_fb = store.list_all()
    now = datetime.now(timezone.utc)

    # Filter to time window for trend calculation
    window_start = now - timedelta(days=days)

    # ---- Counts ----------------------------------------------------------
    closed = [fb for fb in all_fb if fb.status == "closed"]
    verified = [fb for fb in all_fb if fb.status == "verified"]
    resolved = closed + verified
    open_items = [fb for fb in all_fb if fb.status not in ("closed", "verified")]

    pending = len([fb for fb in open_items if fb.status == "pending"])

    total = len(all_fb)
    resolution_rate = len(resolved) / total if total > 0 else 0.0

    # ---- Avg resolution time --------------------------------------------
    resolution_times: list[float] = []
    for fb in resolved:
        if fb.verified_at and fb.timestamp:
            try:
                created = datetime.fromisoformat(fb.timestamp.replace("Z", "+00:00"))
                resolved_dt = datetime.fromisoformat(fb.verified_at.replace("Z", "+00:00"))
                delta = (resolved_dt - created).total_seconds()
                resolution_times.append(delta)
            except ValueError:
                pass

    avg_resolution_seconds = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
    avg_resolution_hours = avg_resolution_seconds / 3600.0

    # ---- By dimension ----------------------------------------------------
    by_severity: dict[str, int] = defaultdict(int)
    by_source: dict[str, int] = defaultdict(int)
    by_category: dict[str, int] = defaultdict(int)
    by_status: dict[str, int] = defaultdict(int)

    for fb in all_fb:
        by_severity[fb.severity] += 1
        by_source[fb.source] += 1
        by_category[fb.category] += 1
        by_status[fb.status] += 1

    # ---- SLA: overdue + at-risk ------------------------------------------
    overdue: list[StandardFeedback] = []
    at_risk: list[StandardFeedback] = []

    for fb in open_items:
        if not fb.sla_deadline:
            continue
        try:
            deadline_dt = datetime.fromisoformat(fb.sla_deadline.replace("Z", "+00:00"))
        except ValueError:
            continue

        if deadline_dt < now:
            overdue.append(fb)
        elif deadline_dt < now + timedelta(hours=24):
            at_risk.append(fb)

    # ---- Recurring issues (>= 3 occurrences) ----------------------------
    # Key by (source, source_detail, category) → count + feedback ids
    recurring_map: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "ids": [], "title": "", "category": ""}
    )

    for fb in all_fb:
        if fb.recurrence_count >= 3:
            key = (fb.source, fb.source_detail, fb.category)
            recurring_map[key]["count"] += fb.recurrence_count
            recurring_map[key]["ids"].append(fb.id)
            if not recurring_map[key]["title"]:
                recurring_map[key]["title"] = fb.title
            if not recurring_map[key]["category"]:
                recurring_map[key]["category"] = fb.category

    recurring: list[dict] = []
    for key, val in recurring_map.items():
        source, source_detail, _ = key
        if val["count"] >= 3:
            rec_type = f"{source}/{source_detail}"
            if "import-order" in source_detail or "import_order" in source_detail:
                recommendation = "Batch fix: run automation to correct all import ordering violations."
            elif "coverage" in source_detail:
                recommendation = "Add targeted tests to raise coverage on this module."
            elif "naming" in source_detail:
                recommendation = "Enforce naming convention via pre-commit hook."
            elif "format" in source_detail or "formatting" in source_detail:
                recommendation = "Run formatter on entire codebase."
            else:
                recommendation = "Investigate root cause — likely needs systemic fix, not per-instance patching."

            recurring.append({
                "key": rec_type,
                "source": source,
                "source_detail": source_detail,
                "count": val["count"],
                "title": val["title"],
                "recommendation": recommendation,
            })

    # Sort descending by count
    recurring.sort(key=lambda x: x["count"], reverse=True)

    # ---- Daily trend ----------------------------------------------------
    trend_daily: dict[str, int] = defaultdict(int)
    for fb in all_fb:
        try:
            created = datetime.fromisoformat(fb.timestamp.replace("Z", "+00:00"))
            if created >= window_start:
                date_str = created.strftime("%Y-%m-%d")
                trend_daily[date_str] += 1
        except ValueError:
            pass

    # Fill in missing dates with 0
    current = window_start.date()
    end = now.date()
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        if date_str not in trend_daily:
            trend_daily[date_str] = 0
        current += timedelta(days=1)

    # ---- Team workload --------------------------------------------------
    by_assignee: dict[str, int] = defaultdict(int)
    for fb in open_items:
        if fb.assignee:
            by_assignee[fb.assignee] += 1

    # ---- Category insights ---------------------------------------------
    category_insights = _compute_insights(dict(by_category), recurring)

    return DashboardMetrics(
        total_feedback=total,
        pending=pending,
        resolved=len(resolved),
        closed=len(closed),
        resolution_rate=resolution_rate,
        avg_resolution_time_hours=avg_resolution_hours,
        by_severity=dict(by_severity),
        by_source=dict(by_source),
        by_category=dict(by_category),
        by_status=dict(by_status),
        overdue=overdue,
        at_risk=at_risk,
        recurring=recurring,
        trend_daily=dict(sorted(trend_daily.items())),
        by_assignee=dict(by_assignee),
        category_insights=category_insights,
    )
