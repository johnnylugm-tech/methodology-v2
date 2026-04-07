"""
Tests for core.feedback.alert — UnifiedAlert.
"""

from datetime import datetime, timezone, timedelta

import pytest

from core.feedback.alert import DriftAlert, UnifiedAlert


class TestUnifiedAlertInit:
    """Sanity-check constructor / __post_init__."""

    def test_required_fields(self) -> None:
        ua = UnifiedAlert(
            source="constitution",
            source_detail="HR-01",
            severity="critical",
            title="Phase gate violated",
            message="Phase 2 before Phase 1",
        )
        assert ua.source == "constitution"
        assert ua.source_detail == "HR-01"
        assert ua.severity == "critical"
        assert ua.title == "Phase gate violated"
        assert ua.message == "Phase 2 before Phase 1"

    def test_defaults(self) -> None:
        ua = UnifiedAlert(source="linter", source_detail="E501")
        assert ua.alert_id.startswith("alert-")
        assert ua.timestamp is not None
        assert ua.category == "quality"
        assert ua.severity == "medium"
        assert ua.title == ""
        assert ua.message == ""
        assert ua.context == {}
        assert ua.recommended_action == ""
        assert ua.auto_fixable is False
        assert ua.sla_hours == 24

    def test_custom_sla_hours(self) -> None:
        ua = UnifiedAlert(
            source="bvs",
            source_detail="bv_001",
            severity="high",
            sla_hours=72,
        )
        assert ua.sla_hours == 72


class TestSlaDeadline:
    """SLA deadline is auto-computed in __post_init__."""

    def test_sla_deadline_auto_calculated(self) -> None:
        before = datetime.now(timezone.utc)
        ua = UnifiedAlert(
            source="constitution",
            source_detail="HR-01",
            severity="medium",
            sla_hours=24,
        )
        after = datetime.now(timezone.utc)

        sla_ts = datetime.fromisoformat(ua.sla_deadline.replace("Z", "+00:00"))
        expected_start = before + timedelta(hours=24)
        expected_end = after + timedelta(hours=24)

        # Allow 1-second drift for test execution time
        assert expected_start <= sla_ts <= expected_end

    def test_sla_respects_sla_hours_field(self) -> None:
        ua = UnifiedAlert(
            source="drift",
            source_detail="arch",
            severity="critical",
            sla_hours=4,
        )
        ts = datetime.fromisoformat(ua.timestamp.replace("Z", "+00:00"))
        deadline = datetime.fromisoformat(ua.sla_deadline.replace("Z", "+00:00"))
        delta = deadline - ts
        assert 0 <= delta.total_seconds() - (4 * 3600) < 2  # within 2s tolerance


class TestToFeedback:
    """to_feedback() produces a valid StandardFeedback-shaped dict."""

    def test_required_fields_in_output(self) -> None:
        ua = UnifiedAlert(
            source="constitution",
            source_detail="HR-01",
            severity="critical",
            title="Phase gate violated",
            message="Phase 2 before Phase 1",
        )
        fb = ua.to_feedback()

        assert fb["id"] == ua.alert_id
        assert fb["source"] == "constitution"
        assert fb["source_detail"] == "HR-01"
        assert fb["type"] == "alert"
        assert fb["category"] == "quality"
        assert fb["severity"] == "critical"
        assert fb["title"] == "Phase gate violated"
        assert fb["description"] == "Phase 2 before Phase 1"
        assert fb["status"] == "pending"
        assert fb["assignee"] is None
        assert fb["resolution"] is None
        assert fb["verified_at"] is None
        assert fb["related_feedbacks"] == []
        assert fb["recurrence_count"] == 0

    def test_context_includes_recommended_action_and_auto_fixable(self) -> None:
        ua = UnifiedAlert(
            source="linter",
            source_detail="E501",
            severity="high",
            recommended_action="Remove trailing whitespace",
            auto_fixable=True,
            context={"file": "main.py", "line": 42},
        )
        fb = ua.to_feedback()

        ctx = fb["context"]
        assert ctx["recommended_action"] == "Remove trailing whitespace"
        assert ctx["auto_fixable"] is True
        assert ctx["file"] == "main.py"
        assert ctx["line"] == 42

    def test_auto_fixable_affects_confidence(self) -> None:
        ua_fixable = UnifiedAlert(
            source="linter",
            source_detail="E501",
            auto_fixable=True,
        )
        ua_not_fixable = UnifiedAlert(
            source="linter",
            source_detail="E501",
            auto_fixable=False,
        )
        assert ua_fixable.to_feedback()["confidence"] == 0.95
        assert ua_not_fixable.to_feedback()["confidence"] == 0.8

    def test_tags_include_source_category_severity_and_unified_alert(self) -> None:
        ua = UnifiedAlert(
            source="bvs",
            source_detail="bv_001",
            category="security",
            severity="high",
        )
        fb = ua.to_feedback()
        assert fb["tags"] == ["bvs", "security", "high", "unified_alert"]

    def test_sla_deadline_matches_sla_hours(self) -> None:
        ua = UnifiedAlert(
            source="quality_gate",
            source_detail="QG-03",
            severity="low",
            sla_hours=168,
        )
        fb = ua.to_feedback()
        ts = datetime.fromisoformat(fb["timestamp"].replace("Z", "+00:00"))
        sla = datetime.fromisoformat(fb["sla_deadline"].replace("Z", "+00:00"))
        assert abs((sla - ts).total_seconds() - 168 * 3600) < 2


class TestFromDriftAlert:
    """Factory method from_drift_alert() maps DriftAlert → UnifiedAlert."""

    def test_source_and_detail_mapped(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="high",
            message="Architecture drift detected in API layer",
            drift_score=0.78,
            recommended_action="Regenerate architecture definition",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.source == "drift_monitor"
        assert ua.source_detail == "architecture_drift"

    def test_category_is_architecture(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="medium",
            message="Drift",
            drift_score=0.5,
            recommended_action="Review",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.category == "architecture"

    def test_severity_preserved(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="critical",
            message="Drift",
            drift_score=0.9,
            recommended_action="Fix now",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.severity == "critical"

    def test_title_formatted(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="low",
            message="Minor drift",
            drift_score=0.2,
            recommended_action="Monitor",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.title == "Drift Alert: low"

    def test_context_includes_drift_score(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="high",
            message="Drift",
            drift_score=0.85,
            recommended_action="Regenerate",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.context["drift_score"] == 0.85

    def test_not_auto_fixable(self) -> None:
        da = DriftAlert(
            source="drift_monitor",
            severity="high",
            message="Drift",
            drift_score=0.8,
            recommended_action="Regenerate",
        )
        ua = UnifiedAlert.from_drift_alert(da)
        assert ua.auto_fixable is False

    def test_sla_hours_by_severity(self) -> None:
        cases = [
            ("critical", 4),
            ("high", 24),
            ("medium", 72),
            ("low", 168),
        ]
        for severity, expected_hours in cases:
            da = DriftAlert(
                source="drift_monitor",
                severity=severity,
                message="Drift",
                drift_score=0.5,
                recommended_action="Review",
            )
            ua = UnifiedAlert.from_drift_alert(da)
            assert ua.sla_hours == expected_hours, (
                f"Expected sla_hours={expected_hours} for severity={severity}, "
                f"got {ua.sla_hours}"
            )


class TestToDict:
    """to_dict() round-trips cleanly via dataclasses.asdict."""

    def test_roundtrip(self) -> None:
        ua = UnifiedAlert(
            source="test_failure",
            source_detail="test_api::test_health",
            category="quality",
            severity="high",
            title="API health check failed",
            message="Expected 200, got 503",
            context={"commit": "abc123"},
            recommended_action="Fix /health endpoint",
            auto_fixable=False,
            sla_hours=24,
        )
        d = ua.to_dict()
        assert d["source"] == "test_failure"
        assert d["source_detail"] == "test_api::test_health"
        assert d["category"] == "quality"
        assert d["severity"] == "high"
        assert d["title"] == "API health check failed"
        assert d["message"] == "Expected 200, got 503"
        assert d["context"]["commit"] == "abc123"
        # recommended_action / auto_fixable are top-level dataclass fields, not in context
        assert d["recommended_action"] == "Fix /health endpoint"
        assert d["auto_fixable"] is False
        assert d["sla_hours"] == 24
