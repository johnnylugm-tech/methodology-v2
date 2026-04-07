"""
Base Protocol for Auto-Fix Strategies.

Defines the contract that all correction strategies must implement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from projects.methodology_v2.core.feedback.feedback import StandardFeedback


@dataclass
class PatchResult:
    """
    Result of a strategy's patch application.

    Attributes:
        success: Whether the patch was successfully applied.
        patched_code: The patched source code (or None if failed).
        confidence: Confidence score 0.0-1.0 in the correctness of the patch.
        message: Human-readable status message.
    """

    success: bool
    patched_code: str | None
    confidence: float
    message: str | None


class BaseStrategy(Protocol):
    """
    Protocol for auto-fix strategies.

    Each strategy knows:
    - Whether it can apply to a given feedback (`can_apply`)
    - How to apply the fix (`apply`)
    """

    def can_apply(self, feedback: StandardFeedback) -> bool:
        """
        Check whether this strategy can handle the given feedback.

        Args:
            feedback: The feedback item to evaluate.

        Returns:
            True if this strategy can apply, False otherwise.
        """
        ...

    def apply(self, feedback: StandardFeedback, context: dict) -> PatchResult:
        """
        Apply this strategy's fix to the feedback.

        Args:
            feedback: The feedback item triggering the correction.
            context: Additional context (e.g., file content, error details).

        Returns:
            PatchResult with patched code (if successful) or failure reason.
        """
        ...
