"""
Self-Correction Engine.

Feedback Loop closure action — attempts to automatically fix detected issues
when verification fails.
"""

from .self_correction_engine import (
    SelfCorrectionEngine,
    CorrectionResult,
)
from .correction_library import CorrectionLibrary, CorrectionEntry
from .ai_corrector import (
    AICorrectorProtocol,
    AICorrectionResult,
    MockAICorrector,
    build_ai_correction_prompt,
)
from .closure_with_self_correction import ClosureWithSelfCorrection
from .metrics import SelfCorrectionMetrics

__all__ = [
    "SelfCorrectionEngine",
    "CorrectionResult",
    "CorrectionLibrary",
    "CorrectionEntry",
    "AICorrectorProtocol",
    "AICorrectionResult",
    "MockAICorrector",
    "build_ai_correction_prompt",
    "ClosureWithSelfCorrection",
    "SelfCorrectionMetrics",
]
