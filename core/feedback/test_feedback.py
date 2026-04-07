"""
Unit tests for feedback.py — StandardFeedback dataclass and FeedbackStore.
"""

import pytest
from feedback.feedback import (
    StandardFeedback,
    FeedbackStore,
    FeedbackCreate,
    FeedbackUpdate,
    FeedbackStatus,
    reset_store,
    get_store,
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
    source_detail="src/app.py:12",
    severity="high",
    category="code_quality",
    **kwargs,
) -> StandardFeedback:
    defaults = dict(
        type="error",
        title="Linter violation",
        description="Trailing whitespace detected",
        context={"file": "src/app.py", "line": 12},
        timestamp="2025-01-01T00:00:00+00:00",
        sla_deadline="2025-01-02T00:00:00+00:00",
    )
    defaults.update(kwargs)
    return StandardFeedback(
        id=id,
        source=source,
        source_detail=source_detail,
        type=defaults.pop("type"),
        category=category,
        severity=severity,
        title=defaults.pop("title"),
        description=defaults.pop("description"),
        context=defaults.pop("context"),
        timestamp=defaults.pop("timestamp"),
        sla_deadline=defaults.pop("sla_deadline"),
        **defaults,
    )


class TestStandardFeedbackDataclass:
    def test_to_dict_roundtrip(self):
        fb = make_feedback()
        d = fb.to_dict()
        restored = StandardFeedback.from_dict(d)
        assert restored.id == fb.id
        assert restored.source == fb.source
        assert restored.severity == fb.severity

    def test_default_values(self):
        fb = make_feedback(
            id="test",
            status="pending",
            assignee=None,
            resolution=None,
            verified_at=None,
            related_feedbacks=[],
            recurrence_count=0,
            confidence=1.0,
            tags=[],
        )
        assert fb.status == "pending"
        assert fb.assignee is None


class TestFeedbackStore:
    def test_add_and_get(self, store):
        fb = make_feedback()
        store.add(fb)
        assert store.get(fb.id) is not None
        assert store.get(fb.id).id == fb.id

    def test_get_missing_returns_none(self, store):
        assert store.get("nonexistent") is None

    def test_list_by_source(self, store):
        store.add(make_feedback(id="f1", source="linter"))
        store.add(make_feedback(id="f2", source="linter"))
        store.add(make_feedback(id="f3", source="test_failure"))
        linter_list = store.list_by_source("linter")
        assert len(linter_list) == 2

    def test_list_by_status(self, store):
        store.add(make_feedback(id="f1", status="pending"))
        store.add(make_feedback(id="f2", status="closed"))
        assert len(store.list_by_status("pending")) == 1
        assert len(store.list_by_status("closed")) == 1

    def test_list_open(self, store):
        store.add(make_feedback(id="f1", status="pending"))
        store.add(make_feedback(id="f2", status="closed"))
        store.add(make_feedback(id="f3", status="in_progress"))
        open_items = store.list_open()
        assert len(open_items) == 2

    def test_update(self, store):
        fb = make_feedback()
        store.add(fb)
        result = store.update(fb.id, FeedbackUpdate(status="in_progress", assignee="alice"))
        assert result is not None
        assert result.status == "in_progress"
        assert result.assignee == "alice"

    def test_update_preserves_other_fields(self, store):
        fb = make_feedback()
        store.add(fb)
        store.update(fb.id, FeedbackUpdate(status="in_progress"))
        updated = store.get(fb.id)
        assert updated.title == fb.title
        assert updated.severity == fb.severity

    def test_delete(self, store):
        fb = make_feedback()
        store.add(fb)
        assert store.delete(fb.id) is True
        assert store.get(fb.id) is None

    def test_delete_missing_returns_false(self, store):
        assert store.delete("nonexistent") is False

    def test_len(self, store):
        store.add(make_feedback(id="a"))
        store.add(make_feedback(id="b"))
        assert len(store) == 2