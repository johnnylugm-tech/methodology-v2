"""
Integration tests for Constitution Feedback Adapter and Closure Verifier.

Tests:
 1. HR-01 violation → critical severity feedback
 2. HR-07 violation → high severity (impact=high, urgency=critical)
 3. Recurrence count increments correctly across multiple violations
 4. Closure verifier correctly detects resolved vs still-violating artifacts
"""

import pytest

from feedback.feedback import (
    StandardFeedback,
    FeedbackStore,
    FeedbackUpdate,
    reset_store,
    get_store,
)
from feedback.severity import calculate_severity
from feedback.constitution_adapter import (
    ConstitutionFeedbackAdapter,
    CONSTITUTION_HR_SEVERITY,
)
from feedback.constitution_closure import ConstitutionClosureVerifier


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_store():
    """Reset global store before each test."""
    reset_store()
    yield
    reset_store()


@pytest.fixture
def store():
    return get_store()


@pytest.fixture
def adapter(store: FeedbackStore):
    return ConstitutionFeedbackAdapter(feedback_store=store)


# ---------------------------------------------------------------------------
# Mock Constitution Runner for closure verification tests
# ---------------------------------------------------------------------------

class MockConstitutionRunner:
    """
    Duck-typed Constitution runner that returns controlled violation lists.
    """

    def __init__(self, violations_by_artifact: dict[str, list[dict]] | None = None) -> None:
        """
        Args:
            violations_by_artifact: Mapping of artifact path → list of violation dicts.
                                     Example:
                                     {
                                         "/path/to/spec.md": [
                                             {"rule_id": "HR-01", "message": "..."}
                                         ]
                                     }
        """
        self._violations = violations_by_artifact or {}

    def check(self, phase: int | None = None, artifact: str | None = None) -> dict:
        """Return violations for the given artifact, or empty list if clean."""
        if artifact is None:
            return {"violations": []}
        return {"violations": self._violations.get(artifact, [])}

    def add_violation(self, artifact: str, rule_id: str, message: str) -> None:
        """Dynamically add a violation to this runner's artifact map."""
        self._violations.setdefault(artifact, []).append({
            "rule_id": rule_id,
            "message": message,
            "artifact": artifact,
            "line": None,
        })


# ---------------------------------------------------------------------------
# Test 1: HR-01 → critical severity
# ---------------------------------------------------------------------------

class TestHR01SeverityMapping:
    """
    HR-01 is mapped to ("critical", "critical").
    calculate_severity(5.0, 5.0) → "critical"
    """

    def test_hr01_maps_to_critical_impact_and_urgency(self):
        impact_label, urgency_label = CONSTITUTION_HR_SEVERITY["HR-01"]
        assert impact_label == "critical"
        assert urgency_label == "critical"

    def test_hr01_produces_critical_severity(self):
        # _SEVERITY_NUMERIC["critical"] == 5.0
        from feedback.constitution_adapter import _SEVERITY_NUMERIC

        impact_label, urgency_label = CONSTITUTION_HR_SEVERITY["HR-01"]
        impact_num = _SEVERITY_NUMERIC[impact_label]
        urgency_num = _SEVERITY_NUMERIC[urgency_label]

        severity = calculate_severity(impact_num, urgency_num)
        assert severity == "critical"

    def test_adapter_hr01_violation_creates_critical_feedback(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        constitution_result = {
            "violations": [
                {
                    "rule_id": "HR-01",
                    "message": "Key result missing from spec",
                    "artifact": "/project/spec.md",
                    "line": 42,
                }
            ]
        }

        feedbacks = adapter.on_constitution_check_complete(
            constitution_result=constitution_result,
            phase=1,
            artifacts={"spec": "/project/spec.md"},
        )

        assert len(feedbacks) == 1
        fb = feedbacks[0]
        assert fb.source == "constitution"
        assert fb.source_detail == "HR-01"
        assert fb.severity == "critical"
        assert fb.type == "violation"
        assert fb.category == "quality"
        assert "HR-01" in fb.tags
        assert "constitution" in fb.tags
        assert fb.context["phase"] == 1
        assert fb.context["artifact"] == "/project/spec.md"
        assert fb.context["line"] == 42


# ---------------------------------------------------------------------------
# Test 2: HR-07 → high severity (high impact, critical urgency)
# ---------------------------------------------------------------------------

class TestHR07SeverityMapping:
    """
    HR-07 is mapped to ("high", "critical").
    Missing citation → urgency bumped to critical.
    """

    def test_hr07_maps_to_high_impact_critical_urgency(self):
        impact_label, urgency_label = CONSTITUTION_HR_SEVERITY["HR-07"]
        assert impact_label == "high"
        assert urgency_label == "critical"

    def test_hr07_produces_critical_severity(self):
        """
        HR-07 → ("high", "critical")
        _SEVERITY_NUMERIC["high"] = 4.0  → row index 3
        _SEVERITY_NUMERIC["critical"] = 5.0 → col index 4
        SEVERITY_MATRIX[3][4] = "critical"
        So HR-07 → "critical" severity (high impact × critical urgency).
        """
        from feedback.constitution_adapter import _SEVERITY_NUMERIC

        impact_label, urgency_label = CONSTITUTION_HR_SEVERITY["HR-07"]
        impact_num = _SEVERITY_NUMERIC[impact_label]
        urgency_num = _SEVERITY_NUMERIC[urgency_label]

        severity = calculate_severity(impact_num, urgency_num)
        assert severity == "critical"

    def test_adapter_hr07_violation_creates_critical_severity_feedback(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        """
        HR-07 ("high", "critical") yields "critical" severity.
        """
        constitution_result = {
            "violations": [
                {
                    "rule_id": "HR-07",
                    "message": "Claim not supported by citation",
                    "artifact": "/project/spec.md",
                    "line": 10,
                }
            ]
        }

        feedbacks = adapter.on_constitution_check_complete(
            constitution_result=constitution_result,
            phase=2,
        )

        assert len(feedbacks) == 1
        fb = feedbacks[0]
        assert fb.source_detail == "HR-07"
        assert fb.severity == "critical"
        assert fb.status == "pending"


# ---------------------------------------------------------------------------
# Test 3: Recurrence count
# ---------------------------------------------------------------------------

class TestRecurrenceCount:
    """Recurrence count increments each time the same rule_id is recorded."""

    def test_first_occurrence_recurrence_is_zero(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        constitution_result = {
            "violations": [{"rule_id": "HR-04", "message": "Minor issue"}]
        }
        feedbacks = adapter.on_constitution_check_complete(
            constitution_result, phase=1
        )
        assert feedbacks[0].recurrence_count == 0

    def test_second_occurrence_recurrence_is_one(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        constitution_result_1 = {
            "violations": [{"rule_id": "HR-04", "message": "Issue 1"}]
        }
        constitution_result_2 = {
            "violations": [{"rule_id": "HR-04", "message": "Issue 2"}]
        }

        feedbacks_1 = adapter.on_constitution_check_complete(
            constitution_result_1, phase=1
        )
        feedbacks_2 = adapter.on_constitution_check_complete(
            constitution_result_2, phase=2
        )

        assert feedbacks_1[0].recurrence_count == 0
        assert feedbacks_2[0].recurrence_count == 1

    def test_three_different_rules_all_have_zero_recurrence(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        constitution_result = {
            "violations": [
                {"rule_id": "HR-01", "message": "A"},
                {"rule_id": "HR-02", "message": "B"},
                {"rule_id": "HR-03", "message": "C"},
            ]
        }
        feedbacks = adapter.on_constitution_check_complete(
            constitution_result, phase=1
        )
        assert len(feedbacks) == 3
        for fb in feedbacks:
            assert fb.recurrence_count == 0

    def test_mixed_rules_recurrence_counts_correctly(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        """HR-01 appears twice, HR-02 once → HR-01 second occurrence has count=1."""
        result_a = {"violations": [{"rule_id": "HR-01", "message": "A"}]}
        result_b = {"violations": [{"rule_id": "HR-02", "message": "B"}]}
        result_c = {"violations": [{"rule_id": "HR-01", "message": "C"}]}

        fbs_a = adapter.on_constitution_check_complete(result_a, phase=1)
        fbs_b = adapter.on_constitution_check_complete(result_b, phase=1)
        fbs_c = adapter.on_constitution_check_complete(result_c, phase=1)

        hr01_first = next(fb for fb in fbs_a if fb.source_detail == "HR-01")
        hr02_first = next(fb for fb in fbs_b if fb.source_detail == "HR-02")
        hr01_second = next(fb for fb in fbs_c if fb.source_detail == "HR-01")

        assert hr01_first.recurrence_count == 0
        assert hr02_first.recurrence_count == 0
        assert hr01_second.recurrence_count == 1


# ---------------------------------------------------------------------------
# Test 4: Closure verification
# ---------------------------------------------------------------------------

class TestConstitutionClosureVerifier:
    """ConstitutionClosureVerifier correctly detects resolved vs un-resolved."""

    def test_verifier_rejects_non_constitution_feedback(
        self,
        store: FeedbackStore,
    ):
        runner = MockConstitutionRunner()
        verifier = ConstitutionClosureVerifier(store, runner)

        # Manually add a non-constitution feedback
        fb = StandardFeedback(
            id="fb-not-constitution",
            source="linter",
            source_detail="src/app.py:1",
            type="error",
            category="code_quality",
            severity="high",
            title="Lint error",
            description="Trailing whitespace",
            context={},
            timestamp="2025-01-01T00:00:00+00:00",
            sla_deadline="2025-01-02T00:00:00+00:00",
        )
        store.add(fb)

        verified, reason = verifier.verify("fb-not-constitution", {})
        assert verified is False
        assert "not a constitution source" in reason

    def test_verifier_rejects_missing_feedback(
        self,
        store: FeedbackStore,
    ):
        runner = MockConstitutionRunner()
        verifier = ConstitutionClosureVerifier(store, runner)

        verified, reason = verifier.verify("nonexistent-id", {})
        assert verified is False
        assert "not found" in reason

    def test_verifier_passes_when_violation_resolved(
        self,
        store: FeedbackStore,
    ):
        # Artifact was violating HR-01 when feedback was created.
        # Now runner returns no violations → resolved.
        runner = MockConstitutionRunner(
            violations_by_artifact={
                "/project/spec.md": [],  # clean now
            }
        )
        verifier = ConstitutionClosureVerifier(store, runner)

        fb = StandardFeedback(
            id="constitution-hr01",
            source="constitution",
            source_detail="HR-01",
            type="violation",
            category="quality",
            severity="critical",
            title="Constitution violation: HR-01",
            description="Key result missing",
            context={"phase": 1, "artifact": "/project/spec.md"},
            timestamp="2025-01-01T00:00:00+00:00",
            sla_deadline="2025-01-02T00:00:00+00:00",
            status="pending",
            assignee="platform",
        )
        store.add(fb)

        verified, reason = verifier.verify("constitution-hr01", {})
        assert verified is True
        assert "resolved" in reason.lower()

    def test_verifier_fails_when_violation_still_present(
        self,
        store: FeedbackStore,
    ):
        # Artifact still has HR-01 violation
        runner = MockConstitutionRunner(
            violations_by_artifact={
                "/project/spec.md": [
                    {
                        "rule_id": "HR-01",
                        "message": "Key result still missing",
                        "artifact": "/project/spec.md",
                    }
                ],
            }
        )
        verifier = ConstitutionClosureVerifier(store, runner)

        fb = StandardFeedback(
            id="constitution-hr01-still-violated",
            source="constitution",
            source_detail="HR-01",
            type="violation",
            category="quality",
            severity="critical",
            title="Constitution violation: HR-01",
            description="Key result missing",
            context={"phase": 1, "artifact": "/project/spec.md"},
            timestamp="2025-01-01T00:00:00+00:00",
            sla_deadline="2025-01-02T00:00:00+00:00",
            status="pending",
            assignee="platform",
        )
        store.add(fb)

        verified, reason = verifier.verify("constitution-hr01-still-violated", {})
        assert verified is False
        assert "HR-01" in reason
        assert "still violated" in reason

    def test_verifier_verifies_correct_specific_rule_id(
        self,
        store: FeedbackStore,
    ):
        """
        Artifact has HR-02 and HR-03 violations, but HR-01 is clean.
        Verifying HR-01 should pass; verifying HR-02 should fail.
        """
        runner = MockConstitutionRunner(
            violations_by_artifact={
                "/project/spec.md": [
                    {"rule_id": "HR-02", "message": "HR-02 still violated"},
                    {"rule_id": "HR-03", "message": "HR-03 still violated"},
                ],
            }
        )
        verifier = ConstitutionClosureVerifier(store, runner)

        fb_hr01 = StandardFeedback(
            id="fb-hr01",
            source="constitution",
            source_detail="HR-01",
            type="violation",
            category="quality",
            severity="critical",
            title="HR-01",
            description="desc",
            context={"phase": 1, "artifact": "/project/spec.md"},
            timestamp="2025-01-01T00:00:00+00:00",
            sla_deadline="2025-01-02T00:00:00+00:00",
        )
        fb_hr02 = StandardFeedback(
            id="fb-hr02",
            source="constitution",
            source_detail="HR-02",
            type="violation",
            category="quality",
            severity="high",
            title="HR-02",
            description="desc",
            context={"phase": 1, "artifact": "/project/spec.md"},
            timestamp="2025-01-01T00:00:00+00:00",
            sla_deadline="2025-01-02T00:00:00+00:00",
        )
        store.add(fb_hr01)
        store.add(fb_hr02)

        verified_hr01, reason_hr01 = verifier.verify("fb-hr01", {})
        verified_hr02, reason_hr02 = verifier.verify("fb-hr02", {})

        assert verified_hr01 is True
        assert verified_hr02 is False
        assert "HR-02" in reason_hr02

    def test_verify_by_rule_direct_check(
        self,
        store: FeedbackStore,
    ):
        """verify_by_rule allows checking without an existing feedback item."""
        runner = MockConstitutionRunner(
            violations_by_artifact={
                "/project/spec.md": [
                    {"rule_id": "HR-07", "message": "Missing citation"},
                ],
            }
        )
        verifier = ConstitutionClosureVerifier(store, runner)

        verified_clean, reason_clean = verifier.verify_by_rule(
            rule_id="HR-01",
            phase=1,
            artifact="/project/spec.md",
        )
        assert verified_clean is True
        assert "HR-01 not violated" in reason_clean

        verified_violated, reason_violated = verifier.verify_by_rule(
            rule_id="HR-07",
            phase=1,
            artifact="/project/spec.md",
        )
        assert verified_violated is False
        assert "HR-07 still violated" in reason_violated

    def test_feedback_status_and_assignee_set_after_adapter_runs(
        self,
        adapter: ConstitutionFeedbackAdapter,
        store: FeedbackStore,
    ):
        """Routing should populate assignee and sla_deadline."""
        constitution_result = {
            "violations": [
                {"rule_id": "HR-11", "message": "A/B review threshold violated"},
            ]
        }

        feedbacks = adapter.on_constitution_check_complete(
            constitution_result, phase=1
        )

        assert len(feedbacks) == 1
        fb = feedbacks[0]
        # category="quality" routes to platform team (from ROUTING_RULES)
        # severity="critical" → SLA 4h
        assert fb.assignee is not None
        assert fb.sla_deadline != ""
        # Status should remain pending (route_and_assign only sets assignee/deadline)
        assert fb.status == "pending"


# ---------------------------------------------------------------------------
# Test 5: All HR rules have valid severity mapping
# ---------------------------------------------------------------------------

class TestAllHRRulesMapped:
    """Verify every HR and TH rule has a valid severity entry."""

    @pytest.mark.parametrize("rule_id", list(CONSTITUTION_HR_SEVERITY.keys()))
    def test_all_rules_mappable(self, rule_id: str):
        from feedback.constitution_adapter import _SEVERITY_NUMERIC

        impact_label, urgency_label = CONSTITUTION_HR_SEVERITY[rule_id]
        assert impact_label in _SEVERITY_NUMERIC
        assert urgency_label in _SEVERITY_NUMERIC

        severity = calculate_severity(
            _SEVERITY_NUMERIC[impact_label],
            _SEVERITY_NUMERIC[urgency_label],
        )
        assert severity in ("info", "low", "medium", "high", "critical")
