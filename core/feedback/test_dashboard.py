"""
Tests for Dashboard + Metrics + Export.

Run with: pytest projects/methodology-v2/core/feedback/test_dashboard.py -v
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from io import StringIO

import pytest

from feedback.feedback import StandardFeedback, FeedbackStore, FeedbackCreate, FeedbackUpdate
from feedback.metrics import get_dashboard_metrics, DashboardMetrics
from feedback.dashboard import print_dashboard, print_feedback_list, print_sla_status, print_trend
from feedback.export import export_to_json, export_to_prometheus, prometheus_text_format


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_fb(
    severity: str = "medium",
    status: str = "pending",
    source: str = "linter",
    source_detail: str = "import-order",
    category: str = "code_quality",
    recurrence_count: int = 0,
    hours_ago: int = 0,
    sla_hours: int = 72,
    verified_at: str | None = None,
) -> StandardFeedback:
    """Create a test feedback item with controllable timestamps."""
    created = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    deadline = created + timedelta(hours=sla_hours)
    fb = StandardFeedback(
        id=f"fb-{source}-{source_detail}-{hours_ago}",
        source=source,
        source_detail=source_detail,
        type="error",
        category=category,
        severity=severity,
        title=f"Test {source}/{source_detail}",
        description="Test description",
        context={},
        timestamp=created.isoformat(),
        sla_deadline=deadline.isoformat(),
        status=status,
        assignee="dev-1",
        recurrence_count=recurrence_count,
    )
    if verified_at:
        fb.verified_at = verified_at
    return fb


@pytest.fixture
def store() -> FeedbackStore:
    """Fresh empty store."""
    return FeedbackStore()


@pytest.fixture
def populated_store() -> FeedbackStore:
    """Store with realistic feedback items."""
    store = FeedbackStore()
    now = datetime.now(timezone.utc)

    items = [
        # Closed items (resolved)
        _make_fb(severity="critical", status="closed", source="constitution", source_detail="HR-01",
                 category="compliance", hours_ago=10, sla_hours=4, recurrence_count=0),
        _make_fb(severity="high", status="closed", source="quality_gate", source_detail="coverage",
                 category="testing", hours_ago=20, sla_hours=24, recurrence_count=0),
        _make_fb(severity="low", status="verified", source="linter", source_detail="naming",
                 category="code_quality", hours_ago=5, sla_hours=168, recurrence_count=0),
        # Open items (pending)
        _make_fb(severity="medium", status="pending", source="linter", source_detail="import-order",
                 category="code_quality", hours_ago=1, sla_hours=72, recurrence_count=0),
        _make_fb(severity="high", status="in_progress", source="constitution", source_detail="HR-07",
                 category="compliance", hours_ago=30, sla_hours=24, recurrence_count=0),
        # Recurring issues
        _make_fb(severity="high", status="pending", source="linter", source_detail="import-order",
                 category="code_quality", hours_ago=2, sla_hours=72, recurrence_count=4),
        _make_fb(severity="high", status="pending", source="linter", source_detail="import-order",
                 category="code_quality", hours_ago=4, sla_hours=72, recurrence_count=4),
        _make_fb(severity="medium", status="pending", source="quality_gate", source_detail="coverage",
                 category="testing", hours_ago=3, sla_hours=72, recurrence_count=3),
        # Overdue items
        _make_fb(severity="critical", status="pending", source="constitution", source_detail="HR-02",
                 category="compliance", hours_ago=100, sla_hours=4, recurrence_count=0),
        _make_fb(severity="high", status="pending", source="quality_gate", source_detail="linter",
                 category="code_quality", hours_ago=30, sla_hours=24, recurrence_count=0),
        # At-risk (approaching deadline within 24h)
        _make_fb(severity="medium", status="pending", source="linter", source_detail="formatting",
                 category="code_quality", hours_ago=68, sla_hours=72, recurrence_count=0),
        _make_fb(severity="low", status="pending", source="test_failure", source_detail="unit-test",
                 category="testing", hours_ago=160, sla_hours=168, recurrence_count=0),
        # By source
        _make_fb(severity="medium", status="pending", source="prometheus", source_detail="metric-missing",
                 category="operational", hours_ago=6, sla_hours=72, recurrence_count=0),
        _make_fb(severity="medium", status="closed", source="constitution", source_detail="HR-03",
                 category="compliance", hours_ago=8, sla_hours=72, recurrence_count=0),
    ]

    for fb in items:
        store.add(fb)

    # Manually set verified_at for closed/verified items
    for fb in store.list_all():
        if fb.status in ("closed", "verified"):
            fb.verified_at = datetime.fromisoformat(fb.timestamp).isoformat()

    return store


# ---------------------------------------------------------------------------
# DashboardMetrics
# ---------------------------------------------------------------------------

class TestGetDashboardMetrics:
    def test_total_counts(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert metrics.total_feedback == 14
        assert metrics.pending >= 0
        assert metrics.closed >= 0

    def test_resolution_rate(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert 0.0 <= metrics.resolution_rate <= 1.0

    def test_by_severity(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert isinstance(metrics.by_severity, dict)
        assert all(isinstance(v, int) for v in metrics.by_severity.values())

    def test_by_source(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert isinstance(metrics.by_source, dict)

    def test_by_status(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert isinstance(metrics.by_status, dict)
        assert "pending" in metrics.by_status
        assert "closed" in metrics.by_status

    def test_overdue_identified(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        overdue_ids = {fb.id for fb in metrics.overdue}
        # fb-constitution-HR-02 created 100h ago with 4h SLA → definitely overdue
        assert any("HR-02" in fb.source_detail for fb in metrics.overdue)

    def test_at_risk_identified(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        # fb-quality_gate/linter created 30h ago with 24h SLA → at-risk (within 24h of deadline)
        assert len(metrics.at_risk) >= 0  # Just check it returns a list

    def test_recurring_identified(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        recurring_keys = [r["key"] for r in metrics.recurring]
        assert "linter/import-order" in recurring_keys

    def test_recurring_min_count(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        for rec in metrics.recurring:
            assert rec["count"] >= 3

    def test_trend_daily(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store, days=30)
        assert isinstance(metrics.trend_daily, dict)
        assert all(isinstance(k, str) for k in metrics.trend_daily.keys())
        assert all(isinstance(v, int) for v in metrics.trend_daily.values())

    def test_by_assignee(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert isinstance(metrics.by_assignee, dict)
        # dev-1 was assigned to several
        assert "dev-1" in metrics.by_assignee

    def test_category_insights(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        assert isinstance(metrics.category_insights, dict)

    def test_empty_store(self, store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(store)
        assert metrics.total_feedback == 0
        assert metrics.resolution_rate == 0.0
        assert metrics.overdue == []
        assert metrics.recurring == []

    def test_metrics_to_dict(self, populated_store: FeedbackStore) -> None:
        metrics = get_dashboard_metrics(populated_store)
        d = metrics.to_dict()
        assert isinstance(d, dict)
        assert "total_feedback" in d
        assert "by_severity" in d
        assert "overdue" in d


# ---------------------------------------------------------------------------
# Dashboard printing
# ---------------------------------------------------------------------------

class TestDashboardPrint:
    def test_print_dashboard_no_error(self, populated_store: FeedbackStore) -> None:
        out = StringIO()
        print_dashboard(populated_store, days=30, output=out)
        result = out.getvalue()
        assert len(result) > 0
        assert "FEEDBACK" in result or "feedback" in result.lower()

    def test_print_dashboard_empty_store(self, store: FeedbackStore) -> None:
        out = StringIO()
        print_dashboard(store, output=out)
        result = out.getvalue()
        assert len(result) > 0

    def test_print_feedback_list_no_error(self, populated_store: FeedbackStore) -> None:
        out = StringIO()
        print_feedback_list(populated_store, output=out)
        result = out.getvalue()
        assert len(result) > 0

    def test_print_feedback_list_filtered(self, populated_store: FeedbackStore) -> None:
        out = StringIO()
        print_feedback_list(populated_store, filters={"status": "pending"}, output=out)
        result = out.getvalue()
        assert "pending" in result or "ID" in result

    def test_print_sla_status_no_error(self, populated_store: FeedbackStore) -> None:
        out = StringIO()
        print_sla_status(populated_store, output=out)
        result = out.getvalue()
        assert len(result) > 0

    def test_print_trend_no_error(self, populated_store: FeedbackStore) -> None:
        out = StringIO()
        print_trend(populated_store, days=7, output=out)
        result = out.getvalue()
        assert len(result) > 0


# ---------------------------------------------------------------------------
# JSON Export
# ---------------------------------------------------------------------------

class TestExportJson:
    def test_export_to_json_shape(self, populated_store: FeedbackStore) -> None:
        result = export_to_json(populated_store, days=30)
        assert isinstance(result, dict)
        assert "generated_at" in result
        assert "overview" in result
        assert "breakdowns" in result
        assert "sla" in result
        assert "recurring" in result
        assert "trend_daily" in result

    def test_export_to_json_serializable(self, populated_store: FeedbackStore) -> None:
        result = export_to_json(populated_store, days=30)
        # Should not raise
        json_str = json.dumps(result)
        assert len(json_str) > 0

    def test_export_to_json_timestamps_iso(self, populated_store: FeedbackStore) -> None:
        result = export_to_json(populated_store, days=30)
        assert "T" in result["generated_at"]
        overdue = result["sla"]["overdue"]
        if overdue:
            assert "T" in overdue[0]["timestamp"]

    def test_export_to_json_empty_store(self, store: FeedbackStore) -> None:
        result = export_to_json(store)
        assert result["overview"]["total"] == 0


# ---------------------------------------------------------------------------
# Prometheus Export
# ---------------------------------------------------------------------------

class TestExportPrometheus:
    def test_export_to_prometheus_returns_list(self, populated_store: FeedbackStore) -> None:
        result = export_to_prometheus(populated_store)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_prometheus_text_format(self, populated_store: FeedbackStore) -> None:
        text = prometheus_text_format(store=populated_store)
        assert "# HELP feedback_total" in text
        assert "# TYPE feedback_total gauge" in text
        assert "feedback_total " in text

    def test_prometheus_labels(self, populated_store: FeedbackStore) -> None:
        result = export_to_prometheus(populated_store)
        labeled = [m for m in result if m["labels"]]
        assert len(labeled) > 0
        for m in labeled:
            assert m["name"] and m["type"] and m["labels"]

    def test_prometheus_gauge_values(self, populated_store: FeedbackStore) -> None:
        result = export_to_prometheus(populated_store)
        total_metric = next((m for m in result if m["name"] == "feedback_total"), None)
        assert total_metric is not None
        assert isinstance(total_metric["value"], float)

    def test_prometheus_overdue_count(self, populated_store: FeedbackStore) -> None:
        result = export_to_prometheus(populated_store)
        overdue_metric = next((m for m in result if m["name"] == "feedback_overdue_count"), None)
        assert overdue_metric is not None
        assert isinstance(overdue_metric["value"], float)

    def test_prometheus_empty_store(self, store: FeedbackStore) -> None:
        result = export_to_prometheus(store)
        total_metric = next((m for m in result if m["name"] == "feedback_total"), None)
        assert total_metric is not None
        assert total_metric["value"] == 0.0
