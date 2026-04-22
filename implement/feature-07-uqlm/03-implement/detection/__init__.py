# detection/__init__.py
"""Detection Layer - UQLM + Activation Probes for Hallucination Detection.

This module provides multi-dimensional hallucination detection through:
- UQLM Ensemble: uncertainty quantification via multiple scorers
- CLAP Probe: contrastive learning activation probes
- TinyLoRA: lightweight LoRA-based probes
- MetaQA Drift: model output distribution drift detection
- Gap Detection: AST-based implementation gap analysis
- Unified Score: combined uncertainty scoring
- Confidence Calibration: planner confidence alignment

Architecture:
    Layer 3: UQLM + Activation Probes (this module)
        ├── uqlm_ensemble.py      (FR-U-1)
        ├── clap_probe.py         (FR-U-2)
        ├── tinylora.py           (FR-U-3)
        ├── metaqa.py             (FR-U-4)
        ├── gap_detector.py       (FR-U-5)
        ├── uncertainty_score.py  (FR-U-6)
        ├── confidence_calibrator.py (FR-U-7)
        ├── data_models.py        (shared dataclasses)
        ├── enums.py              (type definitions)
        └── exceptions.py         (custom exceptions)
"""

from __future__ import annotations

# Version
__version__ = "1.0.0"

# Re-exports are not executable code - excluded from coverage
# They exist only for public API convenience
from typing import TYPE_CHECKING  # pragma: no cover

if TYPE_CHECKING:  # pragma: no cover
    from detection.data_models import (
        EnsembleConfig,
        EnsembleResult,
        ScorerResult,
        ProbeConfig,
        ProbeResult,
        TinyLoRAConfig,
        TinyLoRAModel,
        MetaQAResult,
        DriftScore,
        GapType,
        GapFinding,
        GapSummary,
        UncertaintyScore,
        CalibrationResult,
        CalibrationConfig,
    )
    from detection.exceptions import (
        UQLMError,
        ProbeError,
        DataInsufficientError,
        BaselineNotFoundError,
        CalibrationError,
        GapDetectionError,
    )
    from detection.uqlm_ensemble import EnsembleScorer
    from detection.clap_probe import ActivationProbe
    from detection.tinylora import TinyLoRA
    from detection.metaqa import MetaQADetector
    from detection.gap_detector import GapDetector
    from detection.uncertainty_score import UncertaintyScoreCalculator
    from detection.confidence_calibrator import ConfidenceCalibrator

__all__ = [  # pragma: no cover

    # Version
    "__version__",
    # Data Models - Configs
    "EnsembleConfig",
    "EnsembleResult",
    "ScorerResult",
    "ProbeConfig",
    "ProbeResult",
    "TinyLoRAConfig",
    "TinyLoRAModel",
    "MetaQAResult",
    "DriftScore",
    "GapType",
    "GapFinding",
    "GapSummary",
    "UncertaintyScore",
    "CalibrationResult",
    "CalibrationConfig",
    # Exceptions
    "UQLMError",
    "ProbeError",
    "DataInsufficientError",
    "BaselineNotFoundError",
    "CalibrationError",
    "GapDetectionError",
    # Classes
    "EnsembleScorer",
    "ActivationProbe",
    "TinyLoRA",
    "MetaQADetector",
    "GapDetector",
    "UncertaintyScoreCalculator",
    "ConfidenceCalibrator",
]
