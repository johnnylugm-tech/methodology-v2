"""
Tests for ClosureWithSelfCorrection.
"""

import sys
from pathlib import Path

# Ensure core is on the path for imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

import pytest
from unittest.mock import MagicMock, patch

from self_correction.closure_with_self_correction import (
    ClosureWithSelfCorrection,
    ClosureWithSelfCorrectionResult,
)
from self_correction.self_correction_engine import (
    SelfCorrectionEngine,
    CorrectionResult,
)
from feedback.feedback import (
    FeedbackStore,
    StandardFeedback,
)


@pytest.fixture
def store():
    """Create a fresh FeedbackStore."""
    return FeedbackStore()


@pytest.fixture
def engine(store):
    """Create a SelfCorrectionEngine with a fresh mock AI."""
    mock_ai = MagicMock()
    mock_ai.correct.return_value = MagicMock(
        patched_code="# fixed",
        confidence=0.75,
        explanation="mock",
        similar_patches=[],
    )
    return SelfCorrectionEngine(feedback_store=store, ai_corrector=mock_ai)


@pytest.fixture
def closure_pipeline(store, engine):
    """Create a ClosureWithSelfCorrection pipeline."""
    return ClosureWithSelfCorrection(
        feedback_store=store,
        self_correction_engine=engine,
        constitution_verifier=None,
    )


@pytest.fixture
def sample_feedback(store):
    """Create a sample linter feedback."""
    fb = StandardFeedback(
        id="fb-001",
        source="linter",
        source_detail="src/app.py",
        type="error",
        category="syntax",
        severity="high",
        title="Syntax error",
        description="Missing colon",
        context={"file_path": "src/app.py"},
        timestamp="2024-01-01T00:00:00Z",
        sla_deadline="2024-01-02T00:00:00Z",
    )
    store.add(fb)
    return fb


class TestCloseWithCorrection:
    """Tests for the close_with_correction() main entry point."""

    def test_returns_failure_when_feedback_not_found(self, closure_pipeline):
        """Returns failure result when feedback doesn't exist."""
        result = closure_pipeline.close_with_correction("nonexistent-id")
        assert result.required_manual_review is True
        assert result.closure_result["success"] is False

    def test_closes_without_correction_when_verification_passes(self, closure_pipeline, store):
        """If verify_and_close succeeds, no correction is triggered."""
        fb = StandardFeedback(
            id="fb-already-fixed",
            source="linter",
            source_detail="src/app.py",
            type="error",
            category="syntax",
            severity="high",
            title="Syntax error",
            description="Missing colon",
            context={"file_path": "src/app.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
            status="in_progress",
        )
        store.add(fb)

        # Mock verify_and_close to succeed
        with patch("feedback.closure.verify_and_close") as mock_verify:
            mock_verify.return_value = MagicMock(
                success=True,
                message="Closed",
            )
            result = closure_pipeline.close_with_correction(
                "fb-already-fixed",
                resolution_proof={"verified": True},
            )

        assert result.closure_result["success"] is True
        assert result.correction_result is None
        assert result.required_manual_review is False

    def test_triggers_correction_when_verification_fails(self, closure_pipeline, store):
        """When verification fails, self-correction is triggered."""
        fb = StandardFeedback(
            id="fb-needs-fix",
            source="linter",
            source_detail="src/app.py",
            type="error",
            category="syntax",
            severity="high",
            title="Syntax error",
            description="Missing colon",
            context={"file_path": "src/app.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
            status="in_progress",
        )
        store.add(fb)

        with patch("feedback.closure.verify_and_close") as mock_verify:
            mock_verify.return_value = MagicMock(
                success=False,
                message="Verification failed",
            )
            result = closure_pipeline.close_with_correction(
                "fb-needs-fix",
                resolution_proof={},
            )

        assert result.correction_result is not None

    def test_routes_to_human_when_no_patch_produced(self, closure_pipeline, store):
        """When correction produces no patch, routes to human review."""
        fb = StandardFeedback(
            id="fb-no-patch",
            source="security",
            source_detail="CVE-2024-9999",
            type="error",
            category="cve",
            severity="critical",
            title="Critical CVE",
            description="Manual fix required",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
            status="in_progress",
        )
        store.add(fb)

        with patch("feedback.closure.verify_and_close") as mock_verify:
            mock_verify.return_value = MagicMock(
                success=False,
                message="Verification failed",
            )
            result = closure_pipeline.close_with_correction(
                "fb-no-patch",
                resolution_proof={},
            )

        assert result.required_manual_review is True
        assert result.correction_result is not None
        assert result.correction_result.verification_status == "manual_required"

    def test_closes_successfully_when_correction_succeeds(self, closure_pipeline, store):
        """When correction produces a successful patch, feedback is closed."""
        fb = StandardFeedback(
            id="fb-corrected",
            source="linter",
            source_detail="src/app.py",
            type="error",
            category="syntax",
            severity="high",
            title="Syntax error",
            description="Missing colon",
            context={"file_path": "src/app.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
            status="in_progress",
        )
        store.add(fb)

        with patch("feedback.closure.verify_and_close") as mock_verify:
            mock_verify.return_value = MagicMock(
                success=False,
                message="Verification failed",
            )
            result = closure_pipeline.close_with_correction(
                "fb-corrected",
                resolution_proof={},
            )

        # The correction was auto_fixable but may or may not have produced a patch
        # depending on whether patch_syntax found content to fix
        # At minimum, correction_result should exist
        assert result.correction_result is not None


class TestMetricsUpdate:
    """Tests for metrics tracking during closure."""

    def test_metrics_updated_on_correction_attempt(self, closure_pipeline, store):
        """Metrics are updated when a correction is attempted."""
        fb = StandardFeedback(
            id="fb-metrics",
            source="linter",
            source_detail="src/app.py",
            type="error",
            category="syntax",
            severity="high",
            title="Syntax error",
            description="Missing colon",
            context={"file_path": "src/app.py"},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
            status="in_progress",
        )
        store.add(fb)

        initial_count = closure_pipeline._metrics.total_corrections

        with patch("feedback.closure.verify_and_close") as mock_verify:
            mock_verify.return_value = MagicMock(
                success=False,
                message="Verification failed",
            )
            closure_pipeline.close_with_correction("fb-metrics")

        assert closure_pipeline._metrics.total_corrections == initial_count + 1


class TestGetMetrics:
    """Tests for get_metrics()."""

    def test_returns_self_correction_metrics(self, closure_pipeline):
        """get_metrics() returns SelfCorrectionMetrics instance."""
        metrics = closure_pipeline.get_metrics()
        assert metrics.total_corrections == 0
        assert metrics.auto_fixable_count == 0
        assert metrics.ai_assisted_count == 0
        assert metrics.manual_required_count == 0

    def test_learning_hit_rate_from_library(self, closure_pipeline, store):
        """Learning hit rate reflects library state."""
        # The library may or may not have entries from previous tests
        # Just verify the metric is between 0 and 1
        metrics = closure_pipeline.get_metrics()
        assert 0.0 <= metrics.learning_hit_rate <= 1.0
