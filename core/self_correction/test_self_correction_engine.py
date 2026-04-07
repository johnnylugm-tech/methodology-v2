"""
Tests for SelfCorrectionEngine.
"""

import sys
from pathlib import Path

# Ensure core is on the path for imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

import pytest
from unittest.mock import MagicMock

from self_correction.self_correction_engine import (
    SelfCorrectionEngine,
    CorrectionResult,
)
from feedback.feedback import (
    FeedbackStore,
    StandardFeedback,
    FeedbackStatus,
)


@pytest.fixture
def store():
    """Create a fresh FeedbackStore for each test."""
    return FeedbackStore()


@pytest.fixture
def engine(store):
    """Create a SelfCorrectionEngine with a mock AI corrector."""
    mock_ai = MagicMock()
    mock_ai.correct.return_value = MagicMock(
        patched_code="# fixed code",
        confidence=0.75,
        explanation="Mock AI fix",
        similar_patches=[],
    )
    return SelfCorrectionEngine(feedback_store=store, ai_corrector=mock_ai)


@pytest.fixture
def sample_feedback(store):
    """Create a sample linter feedback item."""
    fb = StandardFeedback(
        id="fb-001",
        source="linter",
        source_detail="src/app.py",
        type="error",
        category="syntax",
        severity="high",
        title="Syntax error",
        description="Missing colon after function definition",
        context={"file_path": "src/app.py", "line": 10},
        timestamp="2024-01-01T00:00:00Z",
        sla_deadline="2024-01-02T00:00:00Z",
    )
    store.add(fb)
    return fb


class TestClassify:
    """Tests for the _classify method."""

    def test_auto_fixable_linter_syntax(self, engine, store):
        """(linter, syntax) is auto_fixable."""
        fb = StandardFeedback(
            id="test-1",
            source="linter",
            source_detail="file.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_linter_unused_import(self, engine, store):
        """(linter, unused-import) is auto_fixable."""
        fb = StandardFeedback(
            id="test-2",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="unused-import",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_linter_unused_variable(self, engine, store):
        """(linter, unused-variable) is auto_fixable."""
        fb = StandardFeedback(
            id="test-3",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="unused-variable",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_linter_format(self, engine, store):
        """(linter, format) is auto_fixable."""
        fb = StandardFeedback(
            id="test-4",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="format",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_linter_pep8(self, engine, store):
        """(linter, pep8) is auto_fixable."""
        fb = StandardFeedback(
            id="test-5",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="pep8",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_complexity_cc_high(self, engine, store):
        """(complexity, cc_high) is auto_fixable."""
        fb = StandardFeedback(
            id="test-6",
            source="complexity",
            source_detail="func",
            type="warning",
            category="cc_high",
            severity="medium",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_coverage_gap(self, engine, store):
        """(coverage, gap) is auto_fixable."""
        fb = StandardFeedback(
            id="test-7",
            source="coverage",
            source_detail="test_app.py",
            type="info",
            category="gap",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_auto_fixable_test_failure_import(self, engine, store):
        """(test_failure, import) is auto_fixable."""
        fb = StandardFeedback(
            id="test-8",
            source="test_failure",
            source_detail="import",
            type="error",
            category="testing",
            severity="high",
            title="t",
            description="ModuleNotFoundError: No module named 'foo'",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "auto_fixable"

    def test_ai_assisted_linter_logic(self, engine, store):
        """(linter, logic) is ai_assisted."""
        fb = StandardFeedback(
            id="test-9",
            source="linter",
            source_detail="file.py",
            type="error",
            category="logic",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "ai_assisted"

    def test_ai_assisted_quality_gate_drift(self, engine, store):
        """(quality_gate, drift) is ai_assisted."""
        fb = StandardFeedback(
            id="test-10",
            source="quality_gate",
            source_detail="arch.py",
            type="error",
            category="drift",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "ai_assisted"

    def test_ai_assisted_constitution_hr07(self, engine, store):
        """(constitution, HR-07) is ai_assisted."""
        fb = StandardFeedback(
            id="test-11",
            source="constitution",
            source_detail="HR-07",
            type="error",
            category="HR-07",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "ai_assisted"

    def test_ai_assisted_constitution_hr09(self, engine, store):
        """(constitution, HR-09) is ai_assisted."""
        fb = StandardFeedback(
            id="test-12",
            source="constitution",
            source_detail="HR-09",
            type="error",
            category="HR-09",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "ai_assisted"

    def test_manual_required_security_cve(self, engine, store):
        """(security, cve) is manual_required."""
        fb = StandardFeedback(
            id="test-13",
            source="security",
            source_detail="CVE-2024-1234",
            type="error",
            category="cve",
            severity="critical",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "manual_required"

    def test_manual_required_drift_detector_critical(self, engine, store):
        """(drift_detector, critical) is manual_required."""
        fb = StandardFeedback(
            id="test-14",
            source="drift_detector",
            source_detail="critical",
            type="error",
            category="critical",
            severity="critical",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "manual_required"

    def test_manual_required_constitution_hr01(self, engine, store):
        """(constitution, HR-01) is manual_required."""
        fb = StandardFeedback(
            id="test-15",
            source="constitution",
            source_detail="HR-01",
            type="error",
            category="HR-01",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._classify(fb) == "manual_required"


class TestCorrect:
    """Tests for the correct() main entry point."""

    def test_correct_not_found(self, engine):
        """Returns failure result when feedback not found."""
        result = engine.correct("nonexistent-id")
        assert result.feedback_id == "nonexistent-id"
        assert result.verification_status == "failed"
        assert result.correction_log[0]["result"] == "feedback_not_found"

    def test_correct_auto_fixable_syntax(self, engine, store):
        """Auto-fixable syntax error uses patch_syntax strategy."""
        fb = StandardFeedback(
            id="test-syntax",
            source="linter",
            source_detail="/tmp/test.py",
            type="error",
            category="syntax",
            severity="high",
            title="Syntax error",
            description="Missing colon",
            context={
                "file_path": "/tmp/test.py",
                "file_content": "def foo()\n    pass\n",
                "error_message": "expected ':'",
            },
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        result = engine.correct("test-syntax")
        assert result.auto_fixable is True
        assert result.strategy == "patch_syntax"
        assert result.feedback_id == "test-syntax"

    def test_correct_auto_fixable_unused_import(self, engine, store):
        """Auto-fixable unused import uses isort_autofix strategy."""
        fb = StandardFeedback(
            id="test-import",
            source="linter",
            source_detail="/tmp/test.py",
            type="warning",
            category="unused-import",
            severity="low",
            title="Unused import",
            description="import os is unused",
            context={
                "file_path": "/tmp/test.py",
                "file_content": "import os\n\ndef main():\n    pass\n",
            },
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        result = engine.correct("test-import")
        assert result.auto_fixable is True
        assert result.strategy == "isort_autofix"

    def test_correct_ai_assisted(self, engine, store):
        """AI-assisted corrections use the mock AI corrector."""
        fb = StandardFeedback(
            id="test-ai",
            source="linter",
            source_detail="/tmp/test.py",
            type="error",
            category="logic",
            severity="high",
            title="Logic error",
            description="Complex logic issue",
            context={"file_path": "/tmp/test.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        result = engine.correct("test-ai")
        assert result.auto_fixable is False
        assert result.strategy == "ai_assisted"
        assert result.verification_status == "pending_review"

    def test_correct_manual_required(self, engine, store):
        """Manual-required corrections return manual_required status."""
        fb = StandardFeedback(
            id="test-manual",
            source="security",
            source_detail="CVE-2024-9999",
            type="error",
            category="cve",
            severity="critical",
            title="Security vulnerability",
            description="Critical CVE",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        result = engine.correct("test-manual")
        assert result.verification_status == "manual_required"
        assert result.auto_fixable is False
        assert result.strategy is None


class TestAutoFixStrategies:
    """Tests that _auto_fix routes to correct strategies."""

    def test_routes_to_remove_unused_for_unused_variable(self, engine, store):
        """Unused variable routes to remove_unused strategy."""
        fb = StandardFeedback(
            id="test-unused-var",
            source="linter",
            source_detail="/tmp/test.py",
            type="warning",
            category="unused-variable",
            severity="low",
            title="Unused variable",
            description="Variable 'x' is unused",
            context={
                "file_path": "/tmp/test.py",
                "file_content": "x = 1\n\ndef foo():\n    pass\n",
            },
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        result = engine.correct("test-unused-var")
        assert result.strategy == "remove_unused"


class TestAIAssistedFix:
    """Tests for AI-assisted correction."""

    def test_ai_corrector_is_called(self, engine, store):
        """AI corrector is called for ai_assisted feedback."""
        fb = StandardFeedback(
            id="test-ai-called",
            source="linter",
            source_detail="/tmp/test.py",
            type="error",
            category="logic",
            severity="high",
            title="Logic error",
            description="Complex logic issue",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        engine.correct("test-ai-called")
        engine.ai_corrector.correct.assert_called_once()

    def test_ai_corrector_receives_prompt_with_feedback_details(self, engine, store):
        """AI corrector receives a prompt containing feedback info."""
        fb = StandardFeedback(
            id="test-ai-prompt",
            source="linter",
            source_detail="/tmp/test.py",
            type="error",
            category="logic",
            severity="high",
            title="Logic error",
            description="A logic error occurred",
            context={"file_path": "/tmp/test.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        engine.correct("test-ai-prompt")
        call_args = engine.ai_corrector.correct.call_args[0][0]
        assert "linter" in call_args
        assert "logic" in call_args


class TestVerify:
    """Tests for the _verify method."""

    def test_verify_accepts_nonempty_patch(self, engine):
        """_verify returns True for non-empty patched code."""
        fb = StandardFeedback(
            id="test-verify",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="format",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._verify(fb, "def foo():\n    pass\n") is True

    def test_verify_rejects_empty_patch(self, engine):
        """_verify returns False for empty patched code."""
        fb = StandardFeedback(
            id="test-verify-empty",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="format",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._verify(fb, "") is False
        assert engine._verify(fb, "   ") is False

    def test_verify_accepts_valid_syntax_for_syntax_error(self, engine):
        """_verify accepts valid Python for syntax category."""
        fb = StandardFeedback(
            id="test-verify-syntax",
            source="linter",
            source_detail="file.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._verify(fb, "def foo():\n    pass\n") is True

    def test_verify_rejects_invalid_syntax_for_syntax_error(self, engine):
        """_verify rejects invalid Python for syntax category."""
        fb = StandardFeedback(
            id="test-verify-bad-syntax",
            source="linter",
            source_detail="file.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert engine._verify(fb, "def foo()\n    pass\n") is False


class TestRecordResult:
    """Tests for _record_result."""

    def test_result_appended_to_history(self, engine, store):
        """Correction results are appended to correction_history."""
        fb = StandardFeedback(
            id="test-record",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="unused-variable",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        store.add(fb)

        engine.correct("test-record")
        assert len(engine.correction_history) == 1
        assert engine.correction_history[0].feedback_id == "test-record"
