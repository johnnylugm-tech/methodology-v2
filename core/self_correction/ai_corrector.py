"""
AI-Assisted Correction Module.

Provides AI-powered code correction when auto-fix rules are insufficient.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from projects.methodology_v2.core.feedback.feedback import StandardFeedback
    from projects.methodology_v2.core.self_correction.correction_library import CorrectionEntry


@dataclass
class AICorrectionResult:
    """
    Result of an AI-assisted correction.

    Attributes:
        patched_code: The corrected code produced by the AI.
        confidence: Confidence score 0.0-1.0 in the correction.
        explanation: Human-readable explanation of the fix.
        similar_patches: List of similar past corrections from the library.
    """

    patched_code: str
    confidence: float
    explanation: str
    similar_patches: list[dict]


class AICorrectorProtocol(Protocol):
    """
    Protocol for AI correction providers.

    Implement this protocol to provide AI-powered code correction.
    """

    def correct(self, prompt: str) -> AICorrectionResult:
        """
        Generate a code correction based on a prompt.

        Args:
            prompt: The correction prompt describing the error and context.

        Returns:
            AICorrectionResult with the corrected code.
        """
        ...


class MockAICorrector:
    """
    Fallback AI corrector when no real AI is configured.

    Used when the self-correction engine is running without an AI provider.
    """

    def correct(self, prompt: str) -> AICorrectionResult:
        """
        Return a null correction indicating no AI is available.

        Args:
            prompt: The correction prompt (ignored).

        Returns:
            AICorrectionResult with None values and explanation.
        """
        return AICorrectionResult(
            patched_code="",
            confidence=0.0,
            explanation="No AI corrector configured — this correction requires manual intervention.",
            similar_patches=[],
        )


def build_ai_correction_prompt(
    feedback: StandardFeedback,
    history: list[CorrectionEntry],
) -> str:
    """
    Build an AI correction prompt from a feedback item and correction history.

    Constructs a detailed prompt describing the error and any similar
    corrections that were successfully applied in the past.

    Args:
        feedback: The feedback item that needs correction.
        history: List of similar past corrections from the library.

    Returns:
        A formatted prompt string for the AI corrector.
    """
    prompt_lines = [
        "## Error Information",
        f"Source: {feedback.source}",
        f"Type: {feedback.type}",
        f"Category: {feedback.category}",
        f"Title: {feedback.title}",
        f"Description: {feedback.description}",
        "",
        "## Context",
    ]

    # Add context fields if present
    if feedback.context:
        for key, value in feedback.context.items():
            prompt_lines.append(f"  {key}: {value}")

    if history:
        prompt_lines.extend([
            "",
            "## Historical Similar Corrections",
            "",
        ])
        for h in history:
            prompt_lines.extend([
                f"- Source: {h.source} / {h.source_detail}",
                f"  Category: {h.category}",
                f"  Confidence: {h.confidence} | Success: {h.success}",
                f"  Description: {h.error_description}",
                f"  Code: {h.patched_code[:200]}..." if len(h.patched_code) > 200 else f"  Code: {h.patched_code}",
                "",
            ])
    else:
        prompt_lines.extend([
            "",
            "## Historical Similar Corrections",
            "  (No similar corrections found in library)",
            "",
        ])

    prompt_lines.extend([
        "## Task",
        "Provide the corrected code that fixes this error.",
        "",
        "## Requirements",
        "- Output only the corrected code",
        "- Preserve the original code structure where possible",
        "- Ensure the fix addresses the root cause, not just the symptom",
    ])

    return "\n".join(prompt_lines)
