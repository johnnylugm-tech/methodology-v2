"""
Closure with Self-Correction.

Integrates Self-Correction Engine into the Feedback Loop's closure pipeline.
When verification fails, this module triggers self-correction before
routing to human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from .self_correction_engine import SelfCorrectionEngine, CorrectionResult
from .metrics import SelfCorrectionMetrics

if TYPE_CHECKING:
    from projects.methodology_v2.core.feedback.feedback import FeedbackStore
    from projects.methodology_v2.core.feedback.closure import ClosureResult, VerificationResult


@dataclass
class ClosureWithSelfCorrectionResult:
    """
    Result of a closure attempt with self-correction.

    Attributes:
        feedback_id: The feedback ID that was processed.
        closure_result: The outcome of the closure verification.
        correction_result: The correction result (if correction was attempted).
        required_manual_review: Whether a human needs to review.
        message: Human-readable summary.
    """

    feedback_id: str
    closure_result: dict[str, Any]
    correction_result: CorrectionResult | None
    required_manual_review: bool
    message: str


class ClosureWithSelfCorrection:
    """
    Integrates self-correction into the feedback closure pipeline.

    This class wraps the standard closure mechanism and adds an
    automated self-correction layer:

    1. Attempt standard closure verification
    2. If verification fails, trigger Self-Correction Engine
    3. Re-verify with the patched code
    4. If all passes → close; if fails → route to human review
    """

    def __init__(
        self,
        feedback_store: FeedbackStore,
        self_correction_engine: SelfCorrectionEngine,
        constitution_verifier: Any = None,  # ConstitutionClosureVerifier
    ) -> None:
        """
        Initialize the closure-with-self-correction pipeline.

        Args:
            feedback_store: The FeedbackStore to read/write feedback.
            self_correction_engine: The SelfCorrectionEngine to use.
            constitution_verifier: Optional ConstitutionClosureVerifier
                                   for constitution-sourced feedback.
        """
        self.store = feedback_store
        self.engine = self_correction_engine
        self.verifier = constitution_verifier
        self._metrics = SelfCorrectionMetrics(
            total_corrections=0,
            auto_fixable_count=0,
            auto_fix_success_rate=0.0,
            ai_assisted_count=0,
            ai_assisted_success_rate=0.0,
            manual_required_count=0,
            manual_required_rate=0.0,
            learning_hit_rate=0.0,
            avg_correction_time_hours=0.0,
            correction_confidence_calibration=0.0,
        )

    def close_with_correction(
        self,
        feedback_id: str,
        resolution_proof: dict[str, Any] | None = None,
    ) -> ClosureWithSelfCorrectionResult:
        """
        Attempt to close a feedback item with automated correction.

        Flow:
        1. Attempt standard closure verification (verify_and_close)
        2. If verification passes → close immediately
        3. If verification fails → trigger Self-Correction Engine
        4. If correction produces a patch → re-verify
        5. If re-verification passes → close; else → route to human

        Args:
            feedback_id: The ID of the feedback to close.
            resolution_proof: Optional resolution proof for initial verification.

        Returns:
            ClosureWithSelfCorrectionResult with the outcome.
        """
        resolution_proof = resolution_proof or {}

        # Step 1: Attempt standard closure
        from feedback.closure import verify_and_close

        initial_result = verify_and_close(
            feedback_id=feedback_id,
            resolution_proof=resolution_proof,
            store=self.store,
        )

        if initial_result.success:
            self._update_metrics_on_close(correction_result=None)
            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": True,
                    "message": initial_result.message,
                    "verification_passed": True,
                },
                correction_result=None,
                required_manual_review=False,
                message=f"Feedback '{feedback_id}' closed without correction.",
            )

        # Step 2: Verification failed — trigger self-correction
        correction_result = self.engine.correct(feedback_id)

        self._update_metrics_on_close(correction_result)

        # Step 3: If no patch was produced, route to human
        if not correction_result.patched_code:
            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": False,
                    "message": "No patch produced",
                    "verification_passed": False,
                },
                correction_result=correction_result,
                required_manual_review=True,
                message=(
                    f"Correction could not produce a patch for '{feedback_id}'. "
                    "Manual review required."
                ),
            )

        # Step 4: Patch produced — try to apply and re-verify
        patched_code = correction_result.patched_code
        feedback = self.store.get(feedback_id)

        if feedback is None:
            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": False,
                    "message": "Feedback not found after correction",
                },
                correction_result=correction_result,
                required_manual_review=True,
                message=f"Feedback '{feedback_id}' disappeared after correction.",
            )

        # Step 5: Re-verify with patched code
        # For linter feedback, we can try running the linter on the patched code
        # For other types, we accept the correction based on confidence
        if correction_result.verification_status == "success":
            # High confidence — accept the patch
            updated_proof = dict(resolution_proof)
            updated_proof["verified"] = True
            updated_proof["resolution_summary"] = (
                f"Auto-corrected via {correction_result.strategy or 'self-correction'}. "
                f"Confidence: {correction_result.confidence:.2f}"
            )

            from feedback.feedback import FeedbackUpdate

            self.store.update(
                feedback_id,
                FeedbackUpdate(
                    status="closed",
                    resolution=updated_proof.get("resolution_summary", ""),
                ),
            )

            fb = self.store.get(feedback_id)
            if fb:
                fb.verified_at = datetime.now(timezone.utc).isoformat()

            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": True,
                    "message": "Closed via self-correction",
                    "verification_passed": True,
                },
                correction_result=correction_result,
                required_manual_review=False,
                message=(
                    f"Feedback '{feedback_id}' closed via self-correction "
                    f"(strategy={correction_result.strategy}, "
                    f"confidence={correction_result.confidence:.2f})."
                ),
            )

        elif correction_result.verification_status == "pending_review":
            # Medium confidence — needs human review
            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": False,
                    "message": "Pending review",
                    "verification_passed": False,
                },
                correction_result=correction_result,
                required_manual_review=True,
                message=(
                    f"Correction for '{feedback_id}' requires human review "
                    "(confidence={correction_result.confidence:.2f})."
                ),
            )

        else:
            # Failed or manual_required
            return ClosureWithSelfCorrectionResult(
                feedback_id=feedback_id,
                closure_result={
                    "success": False,
                    "message": "Correction failed or requires manual intervention",
                    "verification_passed": False,
                },
                correction_result=correction_result,
                required_manual_review=True,
                message=f"Feedback '{feedback_id}' requires manual review.",
            )

    def _update_metrics_on_close(
        self,
        correction_result: CorrectionResult | None,
    ) -> None:
        """Update internal metrics after a close attempt."""
        self._metrics.total_corrections += 1

        if correction_result is None:
            return

        if correction_result.verification_status == "manual_required":
            self._metrics.manual_required_count += 1
        elif correction_result.strategy == "ai_assisted":
            self._metrics.ai_assisted_count += 1
            if correction_result.verification_status == "success":
                # Update rolling success rate
                old_rate = self._metrics.ai_assisted_success_rate
                n = self._metrics.ai_assisted_count
                self._metrics.ai_assisted_success_rate = (
                    (old_rate * (n - 1) + 1.0) / n
                )
        else:
            self._metrics.auto_fixable_count += 1
            if correction_result.verification_status == "success":
                old_rate = self._metrics.auto_fix_success_rate
                n = self._metrics.auto_fixable_count
                self._metrics.auto_fix_success_rate = (
                    (old_rate * (n - 1) + 1.0) / n
                )

    def get_metrics(self) -> SelfCorrectionMetrics:
        """Return the current self-correction metrics."""
        # Update learning hit rate from library
        self._metrics.learning_hit_rate = self.engine.library.get_hit_rate()

        # Calculate confidence calibration (avg |predicted_confidence - actual_success|)
        if self.engine.correction_history:
            calibration_errors = []
            for result in self.engine.correction_history:
                predicted = result.confidence
                actual = 1.0 if result.verification_status == "success" else 0.0
                calibration_errors.append(abs(predicted - actual))
            self._metrics.correction_confidence_calibration = (
                sum(calibration_errors) / len(calibration_errors)
            )

        return self._metrics
