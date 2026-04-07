"""
Unit tests for closure.py — verification and closure mechanism.
"""

import pytest
from datetime import datetime, timezone, timedelta

from feedback.feedback import StandardFeedback, FeedbackStore, reset_store, get_store
from feedback.closure import (
    verify_and_close,
    reopen_feedback,
    get_metrics,
    VerificationResult,
    ClosureResult,
)


@pytest.fixture
def store():
    reset_store()
    s = get_store()
    yield s
    reset_store()


def make_feedback(
    id="fb-1",
    source="linter",
    severity="high",
    category="code_quality",
    status="in_progress",
    sla_deadline=None,
) -> StandardFeedback:
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    return StandardFeedback(
        id=id,
        source=source,
        source_detail="src/app.py:12",
        type="error",
        category=category,
        severity=severity,
        title="Test feedback",
        description="Test description",
        context={},
        timestamp=past.isoformat(),
        sla_deadline=sla_deadline or (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        status=status,
    )


class TestVerifyAndClose:
    def test_feedback_not_found(self, store):
        result = verify_and_close("nonexistent-id", {}, store=store)
        assert result.success is False
        assert "not found" in result.message

    def test_linter_verification_passes_with_clean_files(self, store):
        fb = make_feedback(source="linter")
        store.add(fb)
        proof = {
            "files_clean": ["src/app.py"],
            "linter_command": "ruff check src/app.py",
            "exit_code": 0,
        }
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is True
        assert result.verification_result is not None
        assert result.verification_result.passed is True

    def test_linter_verification_fails_without_files_clean(self, store):
        fb = make_feedback(source="linter")
        store.add(fb)
        proof = {"files_clean": [], "exit_code": 1}
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is False
        assert result.verification_result.passed is False

    def test_test_failure_verification(self, store):
        fb = make_feedback(source="test_failure", category="testing")
        store.add(fb)
        proof = {
            "tests_passed": ["test_login_success"],
            "test_suite": "tests/test_auth.py",
            "exit_code": 0,
        }
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is True

    def test_constitution_verification(self, store):
        fb = make_feedback(source="constitution", category="compliance")
        store.add(fb)
        proof = {
            "violations_fixed": ["bias-in-hiring", "transparency"],
            "review_approved": True,
            "policy_version": "v2.1",
        }
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is True

    def test_drift_detector_verification(self, store):
        fb = make_feedback(source="drift_detector", category="architecture")
        store.add(fb)
        proof = {
            "drift_score_before": 0.8,
            "drift_score_after": 0.1,
            "reference_version": "v1.0",
        }
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is True

    def test_drift_detector_verification_fails_if_not_improved(self, store):
        fb = make_feedback(source="drift_detector", category="architecture")
        store.add(fb)
        proof = {
            "drift_score_before": 0.5,
            "drift_score_after": 0.6,
            "reference_version": "v1.0",
        }
        result = verify_and_close(fb.id, proof, store=store)
        assert result.success is False

    def test_generic_verification_requires_explicit_flag(self, store):
        fb = make_feedback(source="user_report")
        store.add(fb)
        result = verify_and_close(fb.id, {}, store=store)
        assert result.success is False

        proof_with_flag = {"verified": True, "resolution_summary": "Fixed manually"}
        result2 = verify_and_close(fb.id, proof_with_flag, store=store)
        assert result2.success is True


class TestReopenFeedback:
    def test_reopen_increments_recurrence(self, store):
        fb = make_feedback(id="reopen-test", status="closed")
        store.add(fb)
        from feedback.feedback import FeedbackUpdate
        store.update(fb.id, FeedbackUpdate(status="closed"))

        # Reopen
        reopened = reopen_feedback(fb.id, store)
        assert reopened is not None
        assert reopened.recurrence_count == 1
        assert reopened.status == "in_progress"

    def test_reopen_twice_increments_twice(self, store):
        fb = make_feedback(id="reopen-test-2", status="closed")
        store.add(fb)
        reopen_feedback(fb.id, store)
        reopen_feedback(fb.id, store)
        fb2 = store.get(fb.id)
        assert fb2.recurrence_count == 2


class TestGetMetrics:
    def test_empty_store(self, store):
        metrics = get_metrics(store=store)
        assert metrics["total_feedback"] == 0
        assert metrics["resolution_rate"] == 0

    def test_counts_all_statuses(self, store):
        store.add(StandardFeedback(
            id="m1", source="linter", source_detail="a.py", type="error",
            category="code_quality", severity="low", title="t1", description="d",
            context={}, timestamp=datetime.now(timezone.utc).isoformat(),
            sla_deadline=datetime.now(timezone.utc).isoformat(), status="closed",
        ))
        store.add(StandardFeedback(
            id="m2", source="linter", source_detail="b.py", type="error",
            category="code_quality", severity="high", title="t2", description="d",
            context={}, timestamp=datetime.now(timezone.utc).isoformat(),
            sla_deadline=datetime.now(timezone.utc).isoformat(), status="pending",
        ))
        metrics = get_metrics(store=store)
        assert metrics["total_feedback"] == 2
        assert metrics["by_status"]["closed"] == 1
        assert metrics["by_status"]["pending"] == 1

    def test_resolution_time_hours(self, store):
        created = datetime.now(timezone.utc) - timedelta(hours=5)
        closed_fb = StandardFeedback(
            id="rt1", source="linter", source_detail="x.py", type="error",
            category="code_quality", severity="medium", title="t", description="d",
            context={}, timestamp=created.isoformat(),
            sla_deadline=datetime.now(timezone.utc).isoformat(),
            status="closed",
            verified_at=datetime.now(timezone.utc).isoformat(),
        )
        store.add(closed_fb)
        metrics = get_metrics(store=store)
        assert metrics["resolution_time_avg_hours"] > 0