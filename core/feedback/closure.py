"""
Closure + Verification Mechanism.

Handles verification of feedback resolution before closing, with
source-specific verification strategies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .feedback import StandardFeedback, FeedbackStore, get_store, FeedbackStatus


# ---------------------------------------------------------------------------
# Result Types
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    """Outcome of a verification check."""

    passed: bool
    message: str
    details: dict[str, Any] | None = None


@dataclass
class ClosureResult:
    """Outcome of a close operation."""

    success: bool
    feedback_id: str
    verification_result: VerificationResult | None = None
    message: str = ""


# ---------------------------------------------------------------------------
# Source-Specific Verification Strategies
# ---------------------------------------------------------------------------

def _verify_constitution(
    feedback: StandardFeedback,
    resolution_proof: dict[str, Any],
) -> VerificationResult:
    """
    Verify constitution compliance feedback.

    Requires evidence that the constitutional violation has been corrected
    and a review has been performed.
    """
    violations_fixed = resolution_proof.get("violations_fixed", [])
    review_approved = resolution_proof.get("review_approved", False)
    policy_version = resolution_proof.get("policy_version", "")

    if not violations_fixed:
        return VerificationResult(
            passed=False,
            message="No violations marked as fixed. Constitution feedback requires explicit violation resolution.",
            details={"violations_fixed": violations_fixed},
        )

    if not review_approved:
        return VerificationResult(
            passed=False,
            message="Review approval missing. Constitutional changes require sign-off.",
            details={"review_approved": review_approved},
        )

    return VerificationResult(
        passed=True,
        message=f"Constitution compliance verified. {len(violations_fixed)} violation(s) resolved. Policy: {policy_version}",
        details={
            "violations_fixed": len(violations_fixed),
            "review_approved": review_approved,
            "policy_version": policy_version,
        },
    )


def _verify_linter(
    feedback: StandardFeedback,
    resolution_proof: dict[str, Any],
) -> VerificationResult:
    """
    Verify linter feedback.

    Requires the linter to pass on the affected file(s) or lines.
    """
    files_clean = resolution_proof.get("files_clean", [])
    linter_command = resolution_proof.get("linter_command", "")
    exit_code = resolution_proof.get("exit_code", -1)

    if not files_clean:
        return VerificationResult(
            passed=False,
            message="No file clean-up confirmed. Linter feedback requires the file to pass linting.",
            details={"files_clean": files_clean},
        )

    if exit_code != 0 and exit_code != -1:
        return VerificationResult(
            passed=False,
            message=f"Linter still failing (exit code {exit_code}). Run: {linter_command}",
            details={"exit_code": exit_code, "linter_command": linter_command},
        )

    return VerificationResult(
        passed=True,
        message=f"Linter verified clean. {len(files_clean)} file(s) passed.",
        details={"files_clean": files_clean, "exit_code": exit_code},
    )


def _verify_test_failure(
    feedback: StandardFeedback,
    resolution_proof: dict[str, Any],
) -> VerificationResult:
    """
    Verify test failure feedback.

    Requires the failing test(s) to pass now.
    """
    tests_passed = resolution_proof.get("tests_passed", [])
    test_suite = resolution_proof.get("test_suite", "")
    exit_code = resolution_proof.get("exit_code", -1)

    if not tests_passed:
        return VerificationResult(
            passed=False,
            message="No tests confirmed passing. Test failure feedback requires the test to pass.",
            details={"tests_passed": tests_passed},
        )

    if exit_code != 0 and exit_code != -1:
        return VerificationResult(
            passed=False,
            message=f"Test suite still failing (exit code {exit_code}).",
            details={"exit_code": exit_code, "test_suite": test_suite},
        )

    return VerificationResult(
        passed=True,
        message=f"Test failure verified resolved. {len(tests_passed)} test(s) now passing.",
        details={"tests_passed": tests_passed, "test_suite": test_suite},
    )


def _verify_drift_detector(
    feedback: StandardFeedback,
    resolution_proof: dict[str, Any],
) -> VerificationResult:
    """
    Verify drift detector feedback.

    Requires confirmation that the implementation now matches the reference
    architecture.
    """
    drift_score_before = resolution_proof.get("drift_score_before", 1.0)
    drift_score_after = resolution_proof.get("drift_score_after", 0.0)
    reference_version = resolution_proof.get("reference_version", "")

    if drift_score_after >= drift_score_before:
        return VerificationResult(
            passed=False,
            message=(
                f"Drift score not improved ({drift_score_after} >= {drift_score_before}). "
                "Implementation still diverges from reference."
            ),
            details={
                "drift_score_before": drift_score_before,
                "drift_score_after": drift_score_after,
            },
        )

    return VerificationResult(
        passed=True,
        message=(
            f"Architecture drift verified resolved. "
            f"Score improved: {drift_score_before} → {drift_score_after}. "
            f"Reference: {reference_version}"
        ),
        details={
            "drift_score_before": drift_score_before,
            "drift_score_after": drift_score_after,
            "reference_version": reference_version,
        },
    )


def _verify_generic(
    feedback: StandardFeedback,
    resolution_proof: dict[str, Any],
) -> VerificationResult:
    """
    Generic fallback verification for sources without a specific strategy.

    Requires resolution_proof to contain a truthy "verified" key or
    "resolution_confirmed" key.
    """
    verified = resolution_proof.get("verified", False) or resolution_proof.get("resolution_confirmed", False)

    if not verified:
        return VerificationResult(
            passed=False,
            message="No explicit verification provided. Provide 'verified': true in resolution_proof.",
            details={"provided_proof_keys": list(resolution_proof.keys())},
        )

    return VerificationResult(
        passed=True,
        message="Resolution verified (generic).",
        details={"resolution_confirmed": True},
    )


# Map source → verification function
_VERIFICATION_STRATEGIES: dict[str, Any] = {
    "constitution":     _verify_constitution,
    "linter":           _verify_linter,
    "test_failure":     _verify_test_failure,
    "drift_detector":   _verify_drift_detector,
}


def _get_verifier(source: str):
    """Return the verification function for a source, or generic fallback."""
    return _VERIFICATION_STRATEGIES.get(source, _verify_generic)


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def verify_and_close(
    feedback_id: str,
    resolution_proof: dict[str, Any],
    store: FeedbackStore | None = None,
    self_correction_engine: Any = None,  # Optional SelfCorrectionEngine for auto-correction
) -> ClosureResult:
    """
    Verify a feedback item's resolution and close it if verification passes.

    Args:
        feedback_id: ID of the feedback to close.
        resolution_proof: Source-specific evidence that the issue is resolved.
        store: Optional feedback store (uses global store if None).
        self_correction_engine: Optional SelfCorrectionEngine — if provided and
            verification fails, self-correction is automatically triggered.

    Returns:
        ClosureResult with success status and verification details.
    """
    if store is None:
        store = get_store()

    feedback = store.get(feedback_id)
    if feedback is None:
        return ClosureResult(
            success=False,
            feedback_id=feedback_id,
            message=f"Feedback '{feedback_id}' not found.",
        )

    verifier = _get_verifier(feedback.source)
    verification_result = verifier(feedback, resolution_proof)

    now_iso = datetime.now(timezone.utc).isoformat()

    if verification_result.passed:
        # Close the feedback
        from .feedback import FeedbackUpdate

        store.update(
            feedback_id,
            FeedbackUpdate(
                status="closed",
                resolution=resolution_proof.get("resolution_summary", ""),
            ),
        )
        # Create a new dict with verified_at set, instead of mutating the object
        closed_fb = store.get(feedback_id)
        if closed_fb:
            from dataclasses import asdict
            fb_dict = asdict(closed_fb)
            fb_dict["verified_at"] = now_iso
            return ClosureResult(
                success=True,
                feedback_id=feedback_id,
                verification_result=verification_result,
                message=f"Feedback '{feedback_id}' closed and verified.",
            )
        return ClosureResult(
            success=True,
            feedback_id=feedback_id,
            verification_result=verification_result,
            message=f"Feedback '{feedback_id}' closed.",
        )
    else:
        # Verification failed — try self-correction if engine provided
        if self_correction_engine is not None:
            from .feedback import FeedbackUpdate

            # Trigger self-correction
            correction_result = self_correction_engine.correct(feedback_id)

            if correction_result.verification_status == "success":
                # Self-correction succeeded — update status to verified
                store.update(
                    feedback_id,
                    FeedbackUpdate(status="verified"),
                )
                # Create a new dict with verified_at set, instead of mutating the object
                verified_fb = store.get(feedback_id)
                if verified_fb:
                    from dataclasses import asdict
                    fb_dict = asdict(verified_fb)
                    fb_dict["verified_at"] = now_iso

                return ClosureResult(
                    success=True,
                    feedback_id=feedback_id,
                    verification_result=verification_result,
                    message=(
                        f"Feedback '{feedback_id}' verified via self-correction "
                        f"(strategy={correction_result.strategy}, "
                        f"confidence={correction_result.confidence:.2f})."
                    ),
                )
            elif correction_result.verification_status == "pending_review":
                # AI-assisted, needs human review
                store.update(
                    feedback_id,
                    FeedbackUpdate(status="pending_human_review"),
                )
                return ClosureResult(
                    success=False,
                    feedback_id=feedback_id,
                    verification_result=verification_result,
                    message=(
                        f"Self-correction for '{feedback_id}' requires human review "
                        f"(confidence={correction_result.confidence:.2f})."
                    ),
                )
            else:
                # Failed or manual_required — reopen for manual handling
                _reopen_feedback(feedback_id, store)
                return ClosureResult(
                    success=False,
                    feedback_id=feedback_id,
                    verification_result=verification_result,
                    message=(
                        f"Verification failed for '{feedback_id}'. "
                        f"Self-correction also failed (strategy={correction_result.strategy}). "
                        "Feedback has been reopened for manual review. "
                        f"Reason: {verification_result.message}"
                    ),
                )
        else:
            # No self-correction engine — just reopen
            _reopen_feedback(feedback_id, store)
            return ClosureResult(
                success=False,
                feedback_id=feedback_id,
                verification_result=verification_result,
                message=(
                    f"Verification failed for '{feedback_id}'. "
                    "Feedback has been reopened. "
                    f"Reason: {verification_result.message}"
                ),
            )


def _reopen_feedback(
    feedback_id: str,
    store: FeedbackStore | None = None,
) -> StandardFeedback | None:
    """
    Reopen a closed/verified feedback item back to 'in_progress'.

    Increments recurrence_count to signal this is a re-opened issue.
    """
    if store is None:
        store = get_store()

    fb = store.get(feedback_id)
    if fb is None:
        return None

    from .feedback import FeedbackUpdate

    # Build updated data instead of mutating the object
    updated_recurrence = fb.recurrence_count + 1
    store.update(feedback_id, FeedbackUpdate(status="in_progress", related_feedbacks=fb.related_feedbacks))

    # Return a copy, not the mutated object
    updated = store.get(feedback_id)
    if updated:
        # Create a new instance with incremented recurrence_count
        from .feedback import StandardFeedback
        from dataclasses import asdict
        updated_dict = asdict(updated)
        updated_dict["recurrence_count"] = updated_recurrence
        return StandardFeedback(**updated_dict)
    return None


def reopen_feedback(
    feedback_id: str,
    store: FeedbackStore | None = None,
) -> StandardFeedback | None:
    """
    Public API for reopening feedback.

    Alias for _reopen_feedback with optional store parameter.
    """
    return _reopen_feedback(feedback_id, store)


def get_metrics(
    store: FeedbackStore | None = None,
    since_iso: str | None = None,
) -> dict[str, Any]:
    """
    Compute resolution metrics over the feedback store.

    Args:
        store: Optional feedback store (uses global store if None).
        since_iso: ISO timestamp string; only count feedback created after this time.
                  If None, count all.

    Returns:
        Dict with resolution_time_avg, resolution_rate, by_severity, by_status.
    """
    if store is None:
        store = get_store()

    all_fb = store.list_all()

    # Filter by time window if provided
    if since_iso:
        try:
            since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
            all_fb = [
                fb
                for fb in all_fb
                if datetime.fromisoformat(fb.timestamp.replace("Z", "+00:00")) >= since_dt
            ]
        except ValueError:
            pass  # ignore malformed timestamp

    total = len(all_fb)
    closed = [fb for fb in all_fb if fb.status == "closed"]
    verified = [fb for fb in all_fb if fb.status == "verified"]
    open_items = [fb for fb in all_fb if fb.status not in ("closed", "verified")]

    # Resolution rate: closed or verified / total
    resolution_rate = (len(closed) + len(verified)) / total if total > 0 else 0.0

    # Average resolution time (for closed/verified items with valid timestamps)
    resolution_times: list[float] = []
    for fb in closed + verified:
        if fb.verified_at and fb.timestamp:
            try:
                created = datetime.fromisoformat(fb.timestamp.replace("Z", "+00:00"))
                resolved = datetime.fromisoformat(fb.verified_at.replace("Z", "+00:00"))
                delta = (resolved - created).total_seconds()
                resolution_times.append(delta)
            except ValueError:
                pass

    resolution_time_avg = sum(resolution_times) / len(resolution_times) if resolution_times else 0.0

    # Breakdown by severity
    by_severity: dict[str, dict[str, int]] = {}
    for fb in all_fb:
        by_severity.setdefault(fb.severity, {"total": 0, "closed": 0, "open": 0})
        by_severity[fb.severity]["total"] += 1
        if fb.status in ("closed", "verified"):
            by_severity[fb.severity]["closed"] += 1
        else:
            by_severity[fb.severity]["open"] += 1

    # Breakdown by status
    by_status: dict[str, int] = {}
    for fb in all_fb:
        by_status[fb.status] = by_status.get(fb.status, 0) + 1

    # Breakdown by source
    by_source: dict[str, dict[str, int]] = {}
    for fb in all_fb:
        by_source.setdefault(fb.source, {"total": 0, "closed": 0})
        by_source[fb.source]["total"] += 1
        if fb.status in ("closed", "verified"):
            by_source[fb.source]["closed"] += 1

    return {
        "total_feedback": total,
        "closed": len(closed),
        "verified": len(verified),
        "open": len(open_items),
        "resolution_rate": round(resolution_time_avg, 4),
        "resolution_time_avg_seconds": round(resolution_time_avg, 2),
        "resolution_time_avg_hours": round(resolution_time_avg / 3600, 2),
        "by_severity": by_severity,
        "by_status": by_status,
        "by_source": by_source,
    }