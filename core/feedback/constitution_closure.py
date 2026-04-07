"""
Constitution Closure Verifier.

Provides re-verification of Constitution-sourced feedback by re-running
the Constitution check and confirming the specific rule_id is no longer
violated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .feedback import FeedbackStore

if TYPE_CHECKING:
    pass


class ConstitutionClosureVerifier:
    """
    Verifies that a Constitution-sourced feedback has been truly resolved.

    Uses the Constitution runner to re-check the artifact that originally
    triggered the violation and confirms the specific rule_id is no longer
    present in the results.
    """

    def __init__(
        self,
        feedback_store: FeedbackStore,
        constitution_runner: Any,  # Protocol / duck-typed; see below
    ) -> None:
        """
        Args:
            feedback_store: The FeedbackStore holding constitution feedback.
            constitution_runner: An object with a `.check(phase, artifact) -> dict`
                                 method returning {"violations": [{"rule_id", ...}, ...]}.
        """
        self.store = feedback_store
        self.runner = constitution_runner

    def verify(self, feedback_id: str, resolution_proof: dict[str, Any]) -> tuple[bool, str]:
        """
        Verify a constitution feedback has been resolved.

        Re-runs the Constitution check on the original artifact and confirms
        the specific rule_id violation is absent from the results.

        Args:
            feedback_id: ID of the constitution-sourced feedback to verify.
            resolution_proof: Dict that may contain additional context
                               (e.g. {"review_approved": True}).
                               Not required for the core verification — the
                               re-check is authoritative.

        Returns:
            (verified: bool, reason: str)
        """
        feedback = self.store.get(feedback_id)

        if feedback is None:
            return False, f"Feedback '{feedback_id}' not found in store."

        if feedback.source != "constitution":
            return False, f"Feedback '{feedback_id}' is not a constitution source (source={feedback.source})."

        phase = feedback.context.get("phase")
        artifact = feedback.context.get("artifact")

        if artifact is None:
            return False, "No artifact path in feedback context — cannot re-verify."

        # Re-run Constitution check
        try:
            result = self.runner.check(phase=phase, artifact=artifact)
        except Exception as exc:
            return False, f"Constitution runner failed: {exc}"

        violations: list[dict] = result.get("violations", [])
        rule_id = feedback.source_detail

        remaining = [v for v in violations if v.get("rule_id") == rule_id]

        if not remaining:
            return True, f"{rule_id} violation resolved — not present in re-check."
        else:
            first = remaining[0]
            return False, (
                f"{rule_id} still violated after resolution attempt: "
                f"{first.get('message', 'No message')}"
            )

    def verify_by_rule(
        self,
        rule_id: str,
        phase: int,
        artifact: str,
    ) -> tuple[bool, str]:
        """
        Direct verification of a specific rule_id against an artifact.

        Allows verification without an existing feedback item
        (e.g. for pre-commit checks).

        Args:
            rule_id: The rule to check (e.g. "HR-01").
            phase: Phase number.
            artifact: Path to the artifact to check.

        Returns:
            (verified: bool, reason: str)
        """
        try:
            result = self.runner.check(phase=phase, artifact=artifact)
        except Exception as exc:
            return False, f"Constitution runner failed: {exc}"

        violations: list[dict] = result.get("violations", [])
        remaining = [v for v in violations if v.get("rule_id") == rule_id]

        if not remaining:
            return True, f"{rule_id} not violated in {artifact}."
        else:
            return False, f"{rule_id} still violated: {remaining[0].get('message', 'No message')}"
