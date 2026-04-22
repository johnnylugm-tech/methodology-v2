# detection/metaqa.py
"""FR-U-4: MetaQA Drift Detection.

This module implements MetaQA (Meta Question Answering) drift detection
for identifying model output distribution shifts.

Purpose:
    Detect when the model's output distribution changes significantly
    from a established baseline. Distribution drift can indicate:
    - Model degradation
    - Data distribution shift
    - Potential hallucinations

Algorithm:
    1. Compute token distribution over sliding window
    2. Calculate KL divergence: KL(baseline || current)
    3. Normalize to [0.0, 1.0] via sigmoid scaling
    4. Identify tokens with drift > 2σ from baseline

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

from detection.data_models import DriftScore, MetaQAResult, TokenDistribution


# =============================================================================
# Section 1: Tokenization Utilities
# =============================================================================


def tokenize(text: str) -> List[str]:
    """Simple word-level tokenization.

    Args:
        text: Input text string

    Returns:
        List of tokens
    """
    if not text:
        return []
    # Simple lowercase split on whitespace
    tokens = text.lower().split()
    return tokens


def compute_token_distribution(texts: List[str]) -> TokenDistribution:
    """Compute token probability distribution from texts.

    Args:
        texts: List of text strings

    Returns:
        TokenDistribution with tokens and probabilities
    """
    if not texts:
        return TokenDistribution(tokens=[], probabilities=[], version="")

    # Count all tokens
    all_tokens = []
    for text in texts:
        all_tokens.extend(tokenize(text))

    if not all_tokens:
        return TokenDistribution(tokens=[], probabilities=[], version="")

    counter = Counter(all_tokens)
    total = len(all_tokens)

    tokens = list(counter.keys())
    probabilities = [counter[t] / total for t in tokens]

    return TokenDistribution(
        tokens=tokens,
        probabilities=probabilities,
        version=datetime.now().isoformat(),
    )


def kl_divergence(
    p: TokenDistribution,
    q: TokenDistribution,
) -> float:
    """Compute KL divergence KL(p || q).

    KL(p || q) = Σ p_i * log(p_i / q_i)

    Args:
        p: Target distribution (true/baseline)
        q: Source distribution (current)

    Returns:
        KL divergence value
    """
    # Build lookup for q probabilities
    q_probs = dict(zip(q.tokens, q.probabilities))

    # Compute KL divergence
    divergence = 0.0
    for i, token in enumerate(p.tokens):
        p_prob = p.probabilities[i]
        q_prob = q_probs.get(token, 1e-10)  # Smoothing

        if p_prob > 0:
            divergence += p_prob * np.log(p_prob / q_prob)

    return divergence


def sigmoid_scale(x: float, k: float = 1.0, x0: float = 0.0) -> float:
    """Scale value to [0.0, 1.0] using sigmoid.

    Args:
        x: Input value
        k: Sigmoid steepness
        x0: Midpoint

    Returns:
        Scaled value in [0.0, 1.0]
    """
    return 1.0 / (1.0 + np.exp(-k * (x - x0)))


# =============================================================================
# Section 2: MetaQA Detector
# =============================================================================


class MetaQADetector:
    """MetaQA Drift Detection.

    Detects distribution drift in model outputs compared to a baseline.
    Used to identify when model behavior changes significantly.

    Attributes:
        baseline: Baseline token distribution
        baseline_version: Version identifier of baseline
        drift_history: Historical drift scores
        window_size: Default sliding window size

    Example:
        >>> detector = MetaQADetector()
        >>> detector.update_baseline(model_outputs)
        >>> result = detector.detect_drift(current_outputs)
        >>> print(result.drift_score)
        0.45
    """

    def __init__(
        self,
        baseline: Optional[Dict[str, float]] = None,
        window_size: int = 100,
    ) -> None:
        """Initialize MetaQADetector with optional baseline.

        Args:
            baseline: Optional baseline token distribution as dict
            window_size: Default sliding window size
        """
        self.window_size = window_size
        self.baseline: Optional[TokenDistribution] = None
        self.baseline_version: str = ""
        self.drift_history: List[DriftScore] = []

        if baseline:
            self._set_baseline_from_dict(baseline)

    def _set_baseline_from_dict(
        self,
        baseline: Dict[str, float],
    ) -> None:
        """Set baseline from dictionary.

        Args:
            baseline: Token -> probability dictionary
        """
        tokens = list(baseline.keys())
        probabilities = list(baseline.values())
        self.baseline = TokenDistribution(
            tokens=tokens,
            probabilities=probabilities,
            version=datetime.now().isoformat(),
        )
        self.baseline_version = self.baseline.version

    def update_baseline(
        self,
        model_outputs: List[str],
    ) -> None:
        """Update baseline distribution from model outputs.

        Args:
            model_outputs: List of model output strings
        """
        if not model_outputs:
            return

        # Compute new baseline
        new_baseline = compute_token_distribution(model_outputs)

        # If existing baseline exists, merge
        if self.baseline is not None:
            self.baseline = self._merge_distributions(
                self.baseline, new_baseline
            )
        else:
            self.baseline = new_baseline

        self.baseline_version = self.baseline.version

    def _merge_distributions(
        self,
        existing: TokenDistribution,
        new: TokenDistribution,
        alpha: float = 0.9,
    ) -> TokenDistribution:
        """Merge two distributions with exponential decay.

        Args:
            existing: Existing baseline distribution
            new: New distribution to merge
            alpha: Weight for existing (1-alpha for new)

        Returns:
            Merged TokenDistribution
        """
        # Build new distribution lookup
        new_lookup = dict(zip(new.tokens, new.probabilities))

        # Merge tokens
        all_tokens = set(existing.tokens) | set(new.tokens)

        merged_tokens = []
        merged_probs = []

        for token in all_tokens:
            p_existing = 0.0
            p_new = 0.0

            for i, t in enumerate(existing.tokens):
                if t == token:
                    p_existing = existing.probabilities[i]

            p_new = new_lookup.get(token, 0.0)

            merged_tokens.append(token)
            # Weighted merge
            merged_probs.append(alpha * p_existing + (1 - alpha) * p_new)

        # Renormalize
        total = sum(merged_probs)
        if total > 0:
            merged_probs = [p / total for p in merged_probs]

        return TokenDistribution(
            tokens=merged_tokens,
            probabilities=merged_probs,
            version=datetime.now().isoformat(),
        )

    def detect_drift(
        self,
        model_outputs: List[str],
        window_size: Optional[int] = None,
    ) -> MetaQAResult:
        """Detect drift from baseline distribution.

        Args:
            model_outputs: Current model outputs to evaluate
            window_size: Sliding window size (uses default if None)

        Returns:
            MetaQAResult with drift_score and drifted_tokens

        Raises:
            BaselineNotFoundError: If no baseline is initialized
        """
        if self.baseline is None:
            # First run: initialize baseline and return 0.0 drift
            self.update_baseline(model_outputs)
            return MetaQAResult(
                drift_score=0.0,
                drifted_tokens=[],
                kl_divergence=0.0,
                window_size=self.window_size,
                baseline_version=self.baseline_version,
            )

        if not model_outputs:
            return MetaQAResult(
                drift_score=0.0,
                drifted_tokens=[],
                kl_divergence=0.0,
                window_size=self.window_size,
                baseline_version=self.baseline_version,
            )

        window_size = window_size or self.window_size

        # Compute current distribution over window
        window_texts = model_outputs[:window_size]
        current = compute_token_distribution(window_texts)

        # Compute KL divergence
        kl_div = kl_divergence(self.baseline, current)

        # Normalize drift score using sigmoid scaling
        # Typical KL values range from 0 to ~10
        # We scale so that KL=2 corresponds to ~0.5 drift
        drift_score = sigmoid_scale(kl_div, k=0.5, x0=0.0)
        drift_score = max(0.0, min(1.0, drift_score))

        # Find drifted tokens (those > 2σ from baseline)
        drifted_tokens = self._find_drifted_tokens(
            self.baseline, current, threshold=2.0
        )

        # Record in history
        drift_record = DriftScore(
            score=drift_score,
            timestamp=datetime.now(),
            tokens=drifted_tokens,
            kl_div=kl_div,
        )
        self.drift_history.append(drift_record)

        # Limit history size
        max_history = 1000
        if len(self.drift_history) > max_history:
            self.drift_history = self.drift_history[-max_history:]

        return MetaQAResult(
            drift_score=drift_score,
            drifted_tokens=drifted_tokens,
            kl_divergence=kl_div,
            window_size=window_size,
            baseline_version=self.baseline_version,
        )

    def _find_drifted_tokens(
        self,
        baseline: TokenDistribution,
        current: TokenDistribution,
        threshold: float = 2.0,
    ) -> List[str]:
        """Find tokens with significant drift (> threshold σ).

        Args:
            baseline: Baseline distribution
            current: Current distribution
            threshold: Number of standard deviations

        Returns:
            List of token strings with significant drift
        """
        # Build baseline lookup
        base_lookup = dict(zip(baseline.tokens, baseline.probabilities))

        # Find common tokens
        common_tokens = set(baseline.tokens) & set(current.tokens)

        if not common_tokens:
            return []

        # Compute baseline statistics
        base_probs = np.array([base_lookup[t] for t in common_tokens])
        np.mean(base_probs)
        std = np.std(base_probs) + 1e-10  # Avoid division by zero

        # Find drifted tokens
        drifted = []
        current_lookup = dict(zip(current.tokens, current.probabilities))

        for token in common_tokens:
            base_prob = base_lookup[token]
            curr_prob = current_lookup.get(token, 0.0)

            # Compute z-score
            z_score = abs(curr_prob - base_prob) / std

            if z_score > threshold:
                drifted.append(token)

        return drifted

    def get_drift_history(
        self,
        limit: Optional[int] = None,
    ) -> List[DriftScore]:
        """Get historical drift scores.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of DriftScore records
        """
        if limit is None:
            return self.drift_history.copy()
        return self.drift_history[-limit:]

    def clear_baseline(self) -> None:
        """Clear baseline distribution."""
        self.baseline = None
        self.baseline_version = ""

    def get_baseline(self) -> Optional[Dict[str, float]]:
        """Get baseline as dictionary.

        Returns:
            Token -> probability dictionary or None
        """
        if self.baseline is None:
            return None
        return dict(zip(self.baseline.tokens, self.baseline.probabilities))
