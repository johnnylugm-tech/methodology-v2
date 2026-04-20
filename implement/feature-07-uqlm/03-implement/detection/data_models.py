# detection/data_models.py
"""Data models for Layer 3: UQLM + Activation Probes.

This module defines all shared dataclasses used across the detection layer.
All models use type hints and are compatible with Python 3.9+.

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple

import numpy as np


# =============================================================================
# Section 1: Enums
# =============================================================================


class GapType(Enum):
    """Types of implementation gaps detected by GapDetector.

    Attributes:
        BASE64_VS_AES: Mixed cryptographic usage (Base64 vs AES)
        TEST_TODO_FLOOD: Spammed test.todo() assertions
        EMPTY_CATCH: Empty exception handler blocks
        HARDCODED_SECRETS: Hardcoded credentials or API keys
    """

    BASE64_VS_AES = "base64_vs_aes"
    TEST_TODO_FLOOD = "test_todo_flood"
    EMPTY_CATCH = "empty_catch"
    HARDCODED_SECRETS = "hardcoded_secrets"


class GapSeverity(Enum):
    """Severity levels for implementation gaps.

    Attributes:
        CRITICAL: Immediate security or correctness risk
        HIGH: Significant issue requiring attention
        MEDIUM: Moderate issue, should be addressed
        LOW: Minor issue or code smell
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Decision(Enum):
    """Decision outcomes from UncertaintyScore.

    Attributes:
        PASS: Proceed to next step without additional verification
        ROUND_2: Additional verification required before proceeding
        HITL: Human-in-the-loop review mandatory
    """

    PASS = "PASS"
    ROUND_2 = "ROUND_2"
    HITL = "HITL"


class ProbeType(Enum):
    """Types of activation probes supported.

    Attributes:
        LOGISTIC_REGRESSION: Linear probe using logistic regression
        LINEAR: Simple linear probe
        MLP: Multi-layer perceptron probe
        TINYLORA: Lightweight LoRA-based probe
    """

    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR = "linear"
    MLP = "mlp"
    TINYLORA = "tinylora"


# =============================================================================
# Section 2: UQLM Ensemble Models (FR-U-1)
# =============================================================================


@dataclass
class EnsembleConfig:
    """Configuration for UQLM Ensemble Scorer.

    Attributes:
        weights: Weights for each scorer [semantic_entropy, semantic_density,
                 self_consistency]. Must sum to 1.0.
        scorers: List of scorer names to use in ensemble
        n_samples: Number of samples for self-consistency checking
        temperature: Sampling temperature for model calls
        model_name: Default model identifier for scoring
    """

    weights: List[float] = field(
        default_factory=lambda: [0.4, 0.3, 0.3]
    )
    scorers: List[str] = field(
        default_factory=lambda: [
            "semantic_entropy",
            "semantic_density",
            "self_consistency",
        ]
    )
    n_samples: int = 5
    temperature: float = 0.7
    model_name: str = "gpt-3.5-turbo"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if len(self.weights) != len(self.scorers):
            raise ValueError(
                f"Weights count ({len(self.weights)}) must match "
                f"scorers count ({len(self.scorers)})"
            )
        if abs(sum(self.weights) - 1.0) > 1e-6:
            raise ValueError(
                f"Weights must sum to 1.0, got {sum(self.weights)}"
            )


@dataclass
class ScorerResult:
    """Result from an individual uncertainty scorer.

    Attributes:
        scorer_name: Name identifier for the scorer
        raw_score: Raw score from scorer computation
        normalized_score: Score normalized to [0.0, 1.0] range
        metadata: Additional computation metadata (latency, tokens, etc.)
    """

    scorer_name: str
    raw_score: float
    normalized_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """Result from UQLM Ensemble Scorer.

    Attributes:
        uaf_score: Weighted ensemble score in [0.0, 1.0]
        scorer_results: List of individual scorer results
        computation_time_ms: Time taken for computation in milliseconds
        model_used: Model identifier used for scoring
        n_samples: Number of samples generated
    """

    uaf_score: float
    scorer_results: List[ScorerResult]
    computation_time_ms: float
    model_used: str
    n_samples: int


# =============================================================================
# Section 3: CLAP Probe Models (FR-U-2)
# =============================================================================


@dataclass
class ProbeConfig:
    """Configuration for Activation Probe.

    Attributes:
        model_type: Model identifier (llama-3.3, qwen-2.5, gpt-4)
        layer_idx: Target attention layer index (-1 for last layer)
        probe_type: Type of probe to use (logistic_regression, linear, mlp)
        threshold: Decision threshold for binary classification
    """

    model_type: str
    layer_idx: int = -1
    probe_type: ProbeType = ProbeType.LOGISTIC_REGRESSION
    threshold: float = 0.5


@dataclass
class ProbeResult:
    """Result from Activation Probe prediction.

    Attributes:
        p_hallucinate: Probability of hallucination in [0.0, 1.0]
        confidence: Prediction confidence in [0.0, 1.0]
        layer_used: Which layer index was used for prediction
        model_type: Model type used for hidden state extraction
        metadata: Additional prediction metadata
    """

    p_hallucinate: float
    confidence: float
    layer_used: int
    model_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Section 4: TinyLoRA Models (FR-U-3)
# =============================================================================


@dataclass
class TinyLoRAConfig:
    """Configuration for TinyLoRA Lightweight Probe.

    Attributes:
        hidden_dim: Dimension of hidden states
        rank: LoRA rank (rank of A and B matrices)
        alpha: LoRA alpha scaling factor
        lr: Learning rate for training
        dropout: Dropout probability
        max_iter: Maximum training iterations
    """

    hidden_dim: int
    rank: int = 4
    alpha: float = 8.0
    lr: float = 0.001
    dropout: float = 0.1
    max_iter: int = 1000


@dataclass
class TinyLoRAModel:
    """Trained TinyLoRA probe model ready for inference.

    Attributes:
        config: Configuration used for training
        state_dict: Dictionary of LoRA weight matrices
        training_loss: Final training loss value
        metrics: Training metrics (accuracy, f1, auc)
    """

    config: TinyLoRAConfig
    state_dict: Dict[str, np.ndarray]
    training_loss: float
    metrics: Dict[str, float]


# =============================================================================
# Section 5: MetaQA Drift Models (FR-U-4)
# =============================================================================


@dataclass
class MetaQAResult:
    """Result from MetaQA Drift Detection.

    Attributes:
        drift_score: Distribution drift magnitude in [0.0, 1.0]
        drifted_tokens: List of tokens with significant drift
        kl_divergence: KL divergence from baseline distribution
        window_size: Sliding window size used for calculation
        baseline_version: Version/timestamp of baseline being compared
    """

    drift_score: float
    drifted_tokens: List[str]
    kl_divergence: float
    window_size: int
    baseline_version: str


@dataclass
class DriftScore:
    """Historical drift score with timestamp.

    Attributes:
        score: Drift score value
        timestamp: When this score was computed
        tokens: Tokens that drifted at this point
        kl_div: KL divergence value
    """

    score: float
    timestamp: datetime
    tokens: List[str]
    kl_div: float


# =============================================================================
# Section 6: Gap Detection Models (FR-U-5)
# =============================================================================


@dataclass
class GapFinding:
    """Detected implementation gap in source code.

    Attributes:
        gap_type: Type of gap detected
        file_path: File path where gap was found
        line_number: Line number in source file
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        description: Human-readable description of the gap
        code_snippet: Relevant source code snippet
        suggestion: Suggested fix or remediation
    """

    gap_type: GapType
    file_path: str
    line_number: int
    severity: str
    description: str
    code_snippet: str = ""
    suggestion: str = ""


@dataclass
class GapSummary:
    """Summary of gap detection scan across multiple files.

    Attributes:
        total_files: Number of files scanned
        total_findings: Total number of gaps found
        by_type: Count of findings grouped by GapType
        by_severity: Count of findings grouped by severity
        findings: List of all GapFinding objects
    """

    total_files: int
    total_findings: int
    by_type: Dict[GapType, int]
    by_severity: Dict[str, int]
    findings: List[GapFinding]


# =============================================================================
# Section 7: Unified Score Models (FR-U-6)
# =============================================================================


@dataclass
class UncertaintyScore:
    """Unified uncertainty score combining multiple detection methods.

    Attributes:
        score: Combined uncertainty score in [0.0, 1.0]
        decision: Decision outcome (PASS, ROUND_2, HITL)
        components: Individual component scores (uqlm, clap, metaqa)
        alpha: Weight for UQLM component
        beta: Weight for CLAP component
        gamma: Weight for MetaQA component
        computation_time_ms: Total computation time in milliseconds
        metadata: Additional computation details
    """

    score: float
    decision: str
    components: Dict[str, float]
    alpha: float
    beta: float
    gamma: float
    computation_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Section 8: Calibration Models (FR-U-7)
# =============================================================================


@dataclass
class CalibrationConfig:
    """Configuration for Confidence Calibration.

    Attributes:
        history_size: Maximum number of calibration records to keep
        alert_threshold: Calibration error threshold for alerts
    """

    history_size: int = 100
    alert_threshold: float = 0.3


@dataclass
class CalibrationResult:
    """Result from Confidence Calibration.

    Attributes:
        initial_confidence: Planner's original stated confidence
        calibrated_confidence: Adjusted confidence after calibration
        actual_outcome: True outcome (True=success, False=failure)
        calibration_error: Absolute deviation from actual outcome
        alert: Whether calibration error exceeds threshold
        timestamp: When calibration was performed
    """

    initial_confidence: float
    calibrated_confidence: float
    actual_outcome: bool
    calibration_error: float
    alert: bool
    timestamp: datetime


# =============================================================================
# Section 9: Internal Data Models
# =============================================================================


@dataclass
class TokenDistribution:
    """Token probability distribution for drift detection.

    Attributes:
        tokens: List of token strings
        probabilities: Corresponding probabilities
        version: Distribution version identifier
    """

    tokens: List[str]
    probabilities: List[float]
    version: str = ""


@dataclass
class HiddenStateBatch:
    """Batch of hidden states for probe inference.

    Attributes:
        states: 2D numpy array (batch_size, hidden_dim)
        layer_idx: Source layer index
        model_type: Model identifier
    """

    states: np.ndarray
    layer_idx: int
    model_type: str


@dataclass
class TrainingSample:
    """Single training sample for probe training.

    Attributes:
        hidden_state: Hidden state numpy array
        label: Binary label (0=real, 1=hallucination)
    """

    hidden_state: np.ndarray
    label: int


# =============================================================================
# Type Aliases
# =============================================================================

# Type alias for training data format
TrainingData = List[Tuple[np.ndarray, int]]

# Type alias for scorer callable
ScorerCallable = callable([[str, str, int], float])

# Type alias for metadata dict
Metadata = Dict[str, Any]
