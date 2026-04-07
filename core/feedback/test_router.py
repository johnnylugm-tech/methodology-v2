"""
Unit tests for router.py — SLA configuration and routing engine.
"""

import pytest
from datetime import datetime, timezone, timedelta

from feedback.feedback import StandardFeedback, FeedbackStore, reset_store, get_store
from feedback.router import (
    SLA_CONFIG,
    ROUTING_RULES,
    SLAConfig,
    RoutingRule,
    route_and_assign,
    get_pending_by_sla,
    sla_deadline_for,
    team_for,
)


@pytest.fixture
def store():
    reset_store()
    s = get_store()
    yield s
    reset_store()


def make_feedback(
    id="fb-1",
    category="bug",
    severity="high",
    sla_deadline=None,
    status="pending",
) -> StandardFeedback:
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    future = datetime.now(timezone.utc) + timedelta(hours=24)
    return StandardFeedback(
        id=id,
        source="linter",
        source_detail="src/app.py:12",
        type="error",
        category=category,
        severity=severity,
        title="Test feedback",
        description="Test description",
        context={},
        timestamp=past.isoformat(),
        sla_deadline=sla_deadline or future.isoformat(),
        status=status,
    )


class TestSLAConfig:
    def test_all_severity_levels_defined(self):
        for sev in ("critical", "high", "medium", "low", "info"):
            assert sev in SLA_CONFIG
            cfg = SLA_CONFIG[sev]
            assert cfg.response_hours > 0
            assert cfg.resolution_hours > 0
            assert cfg.escalation_hours > 0

    def test_critical_fastest(self):
        crit = SLA_CONFIG["critical"]
        low = SLA_CONFIG["low"]
        assert crit.response_hours < low.response_hours
        assert crit.resolution_hours < low.resolution_hours


class TestRoutingRules:
    def test_all_categories_unique(self):
        categories = [r.category for r in ROUTING_RULES]
        assert len(categories) == len(set(categories))

    def test_known_category(self):
        team = team_for("bug")
        assert team == "backend"

    def test_unknown_category(self):
        team = team_for("nonexistent-category")
        assert team == "general"


class TestSlaDeadlineFor:
    def test_returns_iso_string(self):
        fb = make_feedback()
        deadline = sla_deadline_for(fb)
        # Should be parseable as ISO
        datetime.fromisoformat(deadline.replace("Z", "+00:00"))

    def test_different_severities_different_deadlines(self):
        short = sla_deadline_for(make_feedback(severity="critical"))
        long = sla_deadline_for(make_feedback(severity="low"))
        short_dt = datetime.fromisoformat(short.replace("Z", "+00:00"))
        long_dt = datetime.fromisoformat(long.replace("Z", "+00:00"))
        assert short_dt < long_dt


class TestRouteAndAssign:
    def test_routes_security_to_security_team(self, store):
        fb = make_feedback(category="security", severity="high")
        store.add(fb)
        team, deadline = route_and_assign(fb, store)
        assert team == "security"
        assert len(deadline) > 0

    def test_unknown_category_routes_to_general(self, store):
        fb = make_feedback(category="nonexistent-cat")
        store.add(fb)
        team, _ = route_and_assign(fb, store)
        assert team == "general"

    def test_deadline_is_future_iso(self, store):
        fb = make_feedback()
        store.add(fb)
        _, deadline = route_and_assign(fb, store)
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        assert deadline_dt > datetime.now(timezone.utc)


class TestGetPendingBySla:
    def test_empty_store_returns_empty(self, store):
        assert get_pending_by_sla(store=store) == []

    def test_non_overdue_not_returned(self, store):
        future = datetime.now(timezone.utc) + timedelta(hours=48)
        fb = make_feedback(sla_deadline=future.isoformat())
        store.add(fb)
        overdue = get_pending_by_sla(hours_ahead=0.0, store=store)
        assert len(overdue) == 0

    def test_overdue_returned(self, store):
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        fb = make_feedback(sla_deadline=past.isoformat())
        store.add(fb)
        overdue = get_pending_by_sla(hours_ahead=0.0, store=store)
        assert len(overdue) == 1
        assert overdue[0].id == fb.id

    def test_upcoming_within_window(self, store):
        in_2_hours = datetime.now(timezone.utc) + timedelta(hours=2)
        fb = make_feedback(sla_deadline=in_2_hours.isoformat())
        store.add(fb)
        overdue = get_pending_by_sla(hours_ahead=4.0, store=store)
        assert len(overdue) == 1