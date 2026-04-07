"""
JSON / Prometheus Export.

Exports dashboard metrics in formats suitable for Grafana / Prometheus.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .feedback import FeedbackStore, get_store
from .metrics import get_dashboard_metrics


# ---------------------------------------------------------------------------
# JSON Export
# ---------------------------------------------------------------------------

def export_to_json(
    store: FeedbackStore | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """
    Export dashboard data as a JSON-serializable dict.

    Suitable for feeding into Grafana SimpleJSON plugin or similar.

    Args:
        store: FeedbackStore to analyze. Uses global store if None.
        days: Time window in days for trend data.

    Returns:
        Dict with all dashboard metrics, ISO-8601 timestamps.
    """
    metrics = get_dashboard_metrics(store, days)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "time_window_days": days,
        "overview": {
            "total": metrics.total_feedback,
            "pending": metrics.pending,
            "resolved": metrics.resolved,
            "closed": metrics.closed,
            "resolution_rate": round(metrics.resolution_rate, 4),
            "avg_resolution_time_hours": round(metrics.avg_resolution_time_hours, 2),
        },
        "breakdowns": {
            "by_severity": metrics.by_severity,
            "by_source": metrics.by_source,
            "by_category": metrics.by_category,
            "by_status": metrics.by_status,
        },
        "sla": {
            "overdue_count": len(metrics.overdue),
            "at_risk_count": len(metrics.at_risk),
            "overdue": [_fb_summary(fb) for fb in metrics.overdue],
            "at_risk": [_fb_summary(fb) for fb in metrics.at_risk],
        },
        "recurring": metrics.recurring,
        "trend_daily": metrics.trend_daily,
        "workload": {
            "by_assignee": metrics.by_assignee,
        },
        "category_insights": metrics.category_insights,
    }


def _fb_summary(fb) -> dict[str, Any]:
    """Return a minimal dict for a StandardFeedback."""
    return {
        "id": fb.id,
        "source": fb.source,
        "source_detail": fb.source_detail,
        "category": fb.category,
        "severity": fb.severity,
        "title": fb.title,
        "status": fb.status,
        "assignee": fb.assignee,
        "timestamp": fb.timestamp,
        "sla_deadline": fb.sla_deadline,
        "recurrence_count": fb.recurrence_count,
    }


# ---------------------------------------------------------------------------
# Prometheus Export
# ---------------------------------------------------------------------------

def export_to_prometheus(
    store: FeedbackStore | None = None,
) -> list[dict[str, Any]]:
    """
    Export metrics in Prometheus exposition format.

    Each dict represents one line in the Prometheus text format:
        # HELP <name> <description>
        # TYPE <name> <type>
        <name>{<labels>} <value>

    Args:
        store: FeedbackStore to analyze. Uses global store if None.

    Returns:
        List of dicts with keys: name, type, description, labels, value.
    """
    metrics = get_dashboard_metrics(store)

    lines: list[dict[str, Any]] = []

    # Gauge metrics
    lines.append({
        "name": "feedback_total",
        "type": "gauge",
        "description": "Total number of feedback items",
        "labels": {},
        "value": float(metrics.total_feedback),
    })
    lines.append({
        "name": "feedback_pending",
        "type": "gauge",
        "description": "Number of pending feedback items",
        "labels": {},
        "value": float(metrics.pending),
    })
    lines.append({
        "name": "feedback_resolved",
        "type": "gauge",
        "description": "Number of resolved (closed+verified) feedback items",
        "labels": {},
        "value": float(metrics.resolved),
    })
    lines.append({
        "name": "feedback_closed",
        "type": "gauge",
        "description": "Number of closed feedback items",
        "labels": {},
        "value": float(metrics.closed),
    })
    lines.append({
        "name": "feedback_resolution_rate",
        "type": "gauge",
        "description": "Fraction of feedback that has been resolved (0-1)",
        "labels": {},
        "value": round(metrics.resolution_rate, 4),
    })
    lines.append({
        "name": "feedback_resolution_time_avg_hours",
        "type": "gauge",
        "description": "Average resolution time in hours",
        "labels": {},
        "value": round(metrics.avg_resolution_time_hours, 2),
    })
    lines.append({
        "name": "feedback_overdue_count",
        "type": "gauge",
        "description": "Number of feedback items past SLA deadline",
        "labels": {},
        "value": float(len(metrics.overdue)),
    })
    lines.append({
        "name": "feedback_at_risk_count",
        "type": "gauge",
        "description": "Number of feedback items approaching SLA deadline (within 24h)",
        "labels": {},
        "value": float(len(metrics.at_risk)),
    })

    # Breakdown metrics (labeled gauges)
    for sev, count in metrics.by_severity.items():
        lines.append({
            "name": "feedback_by_severity",
            "type": "gauge",
            "description": "Feedback count by severity",
            "labels": {"severity": sev},
            "value": float(count),
        })

    for source, count in metrics.by_source.items():
        lines.append({
            "name": "feedback_by_source",
            "type": "gauge",
            "description": "Feedback count by source",
            "labels": {"source": source},
            "value": float(count),
        })

    for cat, count in metrics.by_category.items():
        lines.append({
            "name": "feedback_by_category",
            "type": "gauge",
            "description": "Feedback count by category",
            "labels": {"category": cat},
            "value": float(count),
        })

    for status, count in metrics.by_status.items():
        lines.append({
            "name": "feedback_by_status",
            "type": "gauge",
            "description": "Feedback count by status",
            "labels": {"status": status},
            "value": float(count),
        })

    # Workload by assignee
    for assignee, count in metrics.by_assignee.items():
        lines.append({
            "name": "feedback_workload_by_assignee",
            "type": "gauge",
            "description": "Pending feedback count per assignee",
            "labels": {"assignee": assignee},
            "value": float(count),
        })

    return lines


def prometheus_text_format(lines: list[dict[str, Any]] | None = None, store: FeedbackStore | None = None) -> str:
    """
    Render metrics as Prometheus text exposition format string.

    Args:
        lines: Pre-computed list from export_to_prometheus(). If None, fetches from store.
        store: FeedbackStore to analyze (used when lines is None).

    Returns:
        Multiline string in Prometheus text format.
    """
    if lines is None:
        lines = export_to_prometheus(store)

    output_parts: list[str] = []
    for m in lines:
        labels_str = ""
        if m["labels"]:
            label_parts = [f'{k}="{v}"' for k, v in m["labels"].items()]
            labels_str = "{" + ",".join(label_parts) + "}"

        output_parts.append(f"# HELP {m['name']} {m['description']}")
        output_parts.append(f"# TYPE {m['name']} {m['type']}")
        output_parts.append(f"{m['name']}{labels_str} {m['value']}")

    return "\n".join(output_parts)
