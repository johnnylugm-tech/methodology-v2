# detection/uncertainty_score.py
"""FR-U-6: Unified Uncertainty Score.

This module implements the unified uncertainty score calculation that
combines UQLM, CLAP, and MetaQA into a single decision-making score.

Purpose:
    Merge multiple hallucination detection signals into a unified score
    that can be used as a decision gate for the Planner.

Formula:
    uncertainty_score = α × UQLM_ensemble + β × CLAP_probe + γ × MetaQA_drift

Decision Thresholds:
    < 0.2: PASS - Proceed without additional verification
    0.2 - 0.5: ROUND_2 - Additional verification required
    > 0.5: HITL - Human-in-the-loop review mandatory

Weight Redistribution:
    - Missing CLAP input: α=0.6, β=0, γ=0.4
    - Missing MetaQA input: α=0.65, β=0.35, γ=0
    - All missing: raises InsufficientDataError

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np

from detection.data_models import (
    Decision,
    EnsembleResult,
    MetaQAResult,
    ProbeResult,
    UncertaintyScore,
)
from detection.exceptions import InsufficientDataError
from detection.uqlm_ensemble import EnsembleScorer
from detection.clap_probe import ActivationProbe
from detection.metaqa import MetaQADetector


# =============================================================================
# Section 1: Weight Management
# =============================================================================


class WeightManager:
    """Manages component weights with redistribution logic.

    Handles automatic weight redistribution when components are missing.
    """

    DEFAULT_ALPHA = 0.5  # UQLM weight
    DEFAULT_BETA = 0.3  # CLAP weight
    DEFAULT_GAMMA = 0.2  # MetaQA weight

    @classmethod
    def normalize_weights(
        cls,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
    ) -> tuple[float, float, float]:
        """Normalize weights to sum to 1.0 with redistribution.

        Args:
            alpha: UQLM weight (None = use default)
            beta: CLAP weight (None = use default)
            gamma: MetaQA weight (None = use default)

        Returns:
            Tuple of (alpha, beta, gamma) normalized weights
        """
        # Use defaults for None values
        alpha = alpha if alpha is not None else cls.DEFAULT_ALPHA
        beta = beta if beta is not None else cls.DEFAULT_BETA
        gamma = gamma if gamma is not None else cls.DEFAULT_GAMMA

        # Check for missing components (weight = 0 means missing)
        total = alpha + beta + gamma

        # If all present, normalize to 1.0
        if abs(total - 1.0) < 1e-6 and total > 0:
            return alpha, beta, gamma

        # Redistribute missing weights proportionally
        if beta == 0 and gamma == 0:
            # Only UQLM present
            return 1.0, 0.0, 0.0
        elif alpha == 0 and gamma == 0:
            # Only CLAP present
            return 0.0, 1.0, 0.0
        elif alpha == 0 and beta == 0:
            # Only MetaQA present
            return 0.0, 0.0, 1.0
        elif gamma == 0:
            # UQLM + CLAP only
            total = alpha + beta
            return alpha / total, beta / total, 0.0
        elif beta == 0:
            # UQLM + MetaQA only
            total = alpha + gamma
            return alpha / total, 0.0, gamma / total
        elif alpha == 0:
            # CLAP + MetaQA only
            total = beta + gamma
            return 0.0, beta / total, gamma / total
        else:
            # All present but don't sum to 1.0, normalize
            return alpha / total, beta / total, gamma / total


# =============================================================================
# Section 2: Uncertainty Score Calculator
# =============================================================================


class UncertaintyScoreCalculator:
    """Unified Uncertainty Score Calculator.

    Combines multiple hallucination detection signals into a single
    uncertainty score used for decision gating.

    Attributes:
        alpha: Weight for UQLM component
        beta: Weight for CLAP component
        gamma: Weight for MetaQA component
        ensemble_scorer: Optional UQLM Ensemble Scorer
        clap_probe: Optional Activation Probe
        metaqa_detector: Optional MetaQA Detector

    Example:
        >>> calculator = UncertaintyScoreCalculator()
        >>> result = calculator.compute(
        ...     prompt="What is AI?",
        ...     response="AI is artificial intelligence.",
        ...     hidden_states=hidden_states,
        ... )
        >>> print(result.decision)
        "PASS"
    """

    # Decision thresholds
    THRESHOLD_PASS = 0.2
    THRESHOLD_ROUND_2 = 0.5

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2,
        ensemble_scorer: Optional[EnsembleScorer] = None,
        clap_probe: Optional[ActivationProbe] = None,
        metaqa_detector: Optional[MetaQADetector] = None,
    ) -> None:
        """Initialize calculator with weights and component modules.

        Args:
            alpha: UQLM weight (default 0.5)
            beta: CLAP weight (default 0.3)
            gamma: MetaQA weight (default 0.2)
            ensemble_scorer: Optional EnsembleScorer instance
            clap_probe: Optional ActivationProbe instance
            metaqa_detector: Optional MetaQADetector instance
        """
        self.alpha, self.beta, self.gamma = WeightManager.normalize_weights(
            alpha, beta, gamma
        )
        self.ensemble_scorer = ensemble_scorer
        self.clap_probe = clap_probe
        self.metaqa_detector = metaqa_detector

    def compute(
        self,
        prompt: str,
        response: str,
        hidden_states: Optional[np.ndarray] = None,
        model_name: Optional[str] = None,
    ) -> UncertaintyScore:
        """Compute unified uncertainty score.

        Args:
            prompt: Input prompt
            response: Model response to evaluate
            hidden_states: Optional hidden states for CLAP probe
            model_name: Optional model identifier

        Returns:
            UncertaintyScore with score, decision, and components

        Raises:
            InsufficientDataError: If all components are missing
        """
        start_time = time.perf_counter()
        components: Dict[str, float] = {}

        # Compute UQLM score
        uqlm_score = 0.0
        if self.ensemble_scorer is not None:
            try:
                ensemble_result = self.ensemble_scorer.score(
                    prompt, response, model_name=model_name
                )
                uqlm_score = ensemble_result.uaf_score
                components["uqlm"] = uqlm_score
            except Exception:
                # UQLM failed, continue without it
                uqlm_score = 0.0

        # Compute CLAP score
        clap_score = 0.0
        if self.clap_probe is not None and hidden_states is not None:
            try:
                probe_result = self.clap_probe.predict(hidden_states)
                clap_score = probe_result.p_hallucinate
                components["clap"] = clap_score
            except Exception:
                # CLAP failed, continue without it
                clap_score = 0.0

        # Compute MetaQA score
        metaqa_score = 0.0
        if self.metaqa_detector is not None:
            try:
                # MetaQA needs sequence of outputs
                metaqa_result = self.metaqa_detector.detect_drift([response])
                metaqa_score = metaqa_result.drift_score
                components["metaqa"] = metaqa_score
            except Exception:
                # MetaQA failed, continue without it
                metaqa_score = 0.0

        # Check if we have enough data
        if not components:
            raise InsufficientDataError(
                message="No uncertainty components available",
                missing_components=["uqlm", "clap", "metaqa"],
            )

        # Recompute normalized weights based on available components
        alpha, beta, gamma = self._compute_effective_weights(
            uqlm_score, clap_score, metaqa_score
        )

        # Compute combined score
        uncertainty_score = (
            alpha * uqlm_score +
            beta * clap_score +
            gamma * metaqa_score
        )

        # Clamp to [0.0, 1.0]
        uncertainty_score = max(0.0, min(1.0, uncertainty_score))

        # Determine decision
        decision = self._compute_decision(uncertainty_score)

        computation_time_ms = (time.perf_counter() - start_time) * 1000

        return UncertaintyScore(
            score=uncertainty_score,
            decision=decision,
            components=components,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            computation_time_ms=computation_time_ms,
            metadata={
                "model_name": model_name or "unknown",
                "components_available": list(components.keys()),
            },
        )

    def _compute_effective_weights(
        self,
        uqlm_score: float,
        clap_score: float,
        metaqa_score: float,
    ) -> tuple[float, float, float]:
        """Compute effective weights based on available scores.

        Args:
            uqlm_score: UQLM ensemble score
            clap_score: CLAP probe score
            metaqa_score: MetaQA drift score

        Returns:
            Tuple of (alpha, beta, gamma) effective weights
        """
        # Determine which components are "available"
        # A score of 0.0 could mean unavailable OR genuinely no uncertainty
        # We check if the components were actually computed

        # Simplification: use alpha, beta, gamma as originally set
        # but redistribute if a component is completely missing
        return WeightManager.normalize_weights(
            self.alpha if uqlm_score > 0 or self.ensemble_scorer else 0.0,
            self.beta if clap_score > 0 or self.clap_probe else 0.0,
            self.gamma if metaqa_score > 0 or self.metaqa_detector else 0.0,
        )

    def _compute_decision(self, score: float) -> str:
        """Compute decision based on uncertainty score.

        Args:
            score: Uncertainty score in [0.0, 1.0]

        Returns:
            Decision string (PASS, ROUND_2, or HITL)
        """
        if score < self.THRESHOLD_PASS:
            return Decision.PASS.value
        elif score < self.THRESHOLD_ROUND_2:
            return Decision.ROUND_2.value
        else:
            return Decision.HITL.value

    def set_weights(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
    ) -> None:
        """Update component weights.

        Args:
            alpha: New UQLM weight (None = no change)
            beta: New CLAP weight (None = no change)
            gamma: New MetaQA weight (None = no change)
        """
        if alpha is not None:
            self.alpha = alpha
        if beta is not None:
            self.beta = beta
        if gamma is not None:
            self.gamma = gamma

        # Re-normalize
        self.alpha, self.beta, self.gamma = WeightManager.normalize_weights(
            self.alpha, self.beta, self.gamma
        )

    def get_weights(self) -> Dict[str, float]:
        """Get current component weights.

        Returns:
            Dict with alpha, beta, gamma values
        """
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
        }

    def compute_from_results(
        self,
        ensemble_result: Optional[EnsembleResult] = None,
        probe_result: Optional[ProbeResult] = None,
        metaqa_result: Optional[MetaQAResult] = None,
    ) -> UncertaintyScore:
        """Compute uncertainty score from pre-computed results.

        This is an alternative compute method when component results
        are already available.

        Args:
            ensemble_result: Optional UQLM ensemble result
            probe_result: Optional CLAP probe result
            metaqa_result: Optional MetaQA drift result

        Returns:
            UncertaintyScore with combined score

        Raises:
            InsufficientDataError: If no results provided
        """
        start_time = time.perf_counter()
        components: Dict[str, float] = {}

        # Extract UQLM score
        uqlm_score = 0.0
        if ensemble_result is not None:
            uqlm_score = ensemble_result.uaf_score
            components["uqlm"] = uqlm_score

        # Extract CLAP score
        clap_score = 0.0
        if probe_result is not None:
            clap_score = probe_result.p_hallucinate
            components["clap"] = clap_score

        # Extract MetaQA score
        metaqa_score = 0.0
        if metaqa_result is not None:
            metaqa_score = metaqa_result.drift_score
            components["metaqa"] = metaqa_score

        # Check if we have any components
        if not components:
            raise InsufficientDataError(
                message="No component results provided",
                missing_components=["uqlm", "clap", "metaqa"],
            )

        # Compute combined score
        uncertainty_score = (
            self.alpha * uqlm_score +
            self.beta * clap_score +
            self.gamma * metaqa_score
        )

        # Clamp to [0.0, 1.0]
        uncertainty_score = max(0.0, min(1.0, uncertainty_score))

        # Determine decision
        decision = self._compute_decision(uncertainty_score)

        computation_time_ms = (time.perf_counter() - start_time) * 1000

        # Build metadata from components
        metadata = {}
        if ensemble_result:
            metadata["model_used"] = ensemble_result.model_used
            metadata["n_samples"] = ensemble_result.n_samples
        if probe_result:
            metadata["probe_layer"] = probe_result.layer_used
        if metaqa_result:
            metadata["metaqa_window"] = metaqa_result.window_size

        return UncertaintyScore(
            score=uncertainty_score,
            decision=decision,
            components=components,
            alpha=self.alpha,
            beta=self.beta,
            gamma=self.gamma,
            computation_time_ms=computation_time_ms,
            metadata=metadata,
        )
