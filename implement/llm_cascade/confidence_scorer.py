"""
Confidence Scorer — Output Quality Assessment for LLM Cascade

Computes a normalized confidence score (0.0–1.0) on model output.
Used to detect low-quality or malformed responses and trigger escalation.

Scoring Dimensions (weights from ARCHITECTURE.md Section 2.5):
  entropy       → 0.30  Token-level entropy (random-looking text → low confidence)
  repetition    → 0.25  Repetition ratio (stuck in loop → low confidence)
  length        → 0.20  Length sanity (truncated/suspicious → low confidence)
  parse_validity→ 0.25  Structural validity (malformed JSON/code → low confidence)
"""

from __future__ import annotations

import json
import math
from collections import Counter
from typing import Dict, Optional

from .enums import ConfidenceComponent


class ConfidenceScorer:
    """
    Score model output quality for cascade escalation decisions.

    The overall confidence score is a weighted combination of four
    independent dimension scores, each ranging from 0.0 to 1.0.

    Usage:
        scorer = ConfidenceScorer()
        confidence = scorer.score(output_text, task_type="general")
        # confidence < config.confidence_threshold → escalate to next model
    """

    # Weights from ARCHITECTURE.md Section 2.5
    WEIGHT_ENTROPY: float = 0.30
    WEIGHT_REPETITION: float = 0.25
    WEIGHT_LENGTH: float = 0.20
    WEIGHT_PARSE_VALIDITY: float = 0.25

    def __init__(
        self,
        weights: Optional[Dict[ConfidenceComponent, float]] = None,
    ) -> None:
        """
        Initialize ConfidenceScorer.

        Args:
            weights: Optional override weights per component.
                     Defaults to ARCHITECTURE.md values.
        """
        if weights:
            self._weights = weights
        else:
            self._weights = {
                ConfidenceComponent.ENTROPY: self.WEIGHT_ENTROPY,
                ConfidenceComponent.REPETITION: self.WEIGHT_REPETITION,
                ConfidenceComponent.LENGTH: self.WEIGHT_LENGTH,
                ConfidenceComponent.PARSE_VALIDITY: self.WEIGHT_PARSE_VALIDITY,
            }

    def score(self, output: str, task_type: str = "general") -> float:
        """
        Compute the overall confidence score for model output.

        Args:
            output:    The model's response text.
            task_type: One of "general", "code", "json", "xml", "text".
                       Affects length_score and parse_validity_score thresholds.

        Returns:
            A float in [0.0, 1.0]. Higher = more confident the output is high quality.
            Scores below ~0.5 typically indicate problematic output.
        """
        entropy_score = self._entropy_score(output)
        repetition_score = self._repetition_score(output)
        length_score = self._length_score(output, task_type)
        parse_score = self._parse_validity_score(output, task_type)

        weighted = (
            entropy_score * self._weights[ConfidenceComponent.ENTROPY]
            + repetition_score * self._weights[ConfidenceComponent.REPETITION]
            + length_score * self._weights[ConfidenceComponent.LENGTH]
            + parse_score * self._weights[ConfidenceComponent.PARSE_VALIDITY]
        )

        return round(weighted, 3)

    # ─────────────────────────────────────────────────────────────────────────
    # Dimension Scorers
    # ─────────────────────────────────────────────────────────────────────────

    def _entropy_score(self, output: str) -> float:
        """
        Token-level entropy: high entropy → random/uncertain → low confidence.

        Normalized so that uniform distribution over vocabulary → score 0.0,
        and single token repeated → score 1.0.
        """
        if not output.strip():
            return 0.0

        tokens = output.split()
        if len(tokens) < 2:
            return 0.5  # Not enough data to assess entropy

        freq = Counter(tokens)
        probs = [count / len(tokens) for count in freq.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)

        # Max entropy for vocab size V is log2(V)
        max_entropy = math.log2(len(freq) + 1)
        normalized = min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0

        # Invert: high entropy → low confidence
        return round(1.0 - normalized, 3)

    def _repetition_score(self, output: str) -> float:
        """
        Detect repetition loops. High repetition → low confidence.

        Looks for n-grams (n=3..10) repeated 3+ times.
        If repetition_ratio > 0.3, penalize heavily.
        """
        if len(output) < 50:
            return 1.0  # Too short to meaningfully assess

        text = output
        # Sliding window: check for repeated n-grams
        for n in range(3, min(10, len(text) // 5)):
            ngrams = [text[i : i + n] for i in range(len(text) - n + 1)]
            if not ngrams:
                continue
            ngram_counts = Counter(ngrams)
            repeated = sum(1 for c in ngram_counts.values() if c >= 3)
            if not ngram_counts:
                continue
            repetition_ratio = repeated / len(ngram_counts)
            if repetition_ratio > 0.3:
                # Penalize: repetition_ratio of 0.5 → score of 0.0
                penalty = repetition_ratio * 2
                return round(max(0.0, 1.0 - penalty), 3)

        return 1.0

    def _length_score(self, output: str, task_type: str) -> float:
        """
        Length sanity check based on task type.
        Too short → truncated/refused. Too long → suspicious.
        """
        length = len(output)

        if task_type == "general":
            if length < 20:
                return 0.2   # Suspiciously short — truncated or refused
            if length < 100:
                return 0.6   # Possibly incomplete
            if length > 50000:
                return 0.5   # Suspiciously long
            return 1.0

        elif task_type == "code":
            if length < 10:
                return 0.1   # Barely any code
            if output.count("```") == 1:
                return 0.5   # Unclosed code block
            return 1.0

        elif task_type == "json":
            # JSON length scoring is dominated by parse validity
            if length < 5:
                return 0.1
            return 1.0

        elif task_type == "xml":
            if length < 10:
                return 0.1
            return 1.0

        return 1.0  # Default: no length penalty

    def _parse_validity_score(self, output: str, task_type: str) -> float:
        """
        Check structural validity of structured outputs (JSON, code, XML).
        """
        stripped = output.strip()

        # JSON validity
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                json.loads(output)
                return 1.0
            except (json.JSONDecodeError, ValueError):
                return 0.0

        # Markdown code blocks
        code_block_count = output.count("```")
        if code_block_count >= 2:
            # Well-formed: even number of ``` delimiters
            if code_block_count % 2 == 0:
                return 0.9
            else:
                return 0.3  # Unclosed code block
        elif code_block_count == 1:
            return 0.3  # Unclosed

        # XML-like structures
        if stripped.startswith("<") and not stripped.startswith("<?xml"):
            # Check for closing tags or self-closing
            if "</" not in output and "/>" not in output:
                return 0.2  # Likely unclosed tag
            if "</" not in output:
                return 0.3

        # Default: unstructured text gets moderate confidence
        return 0.8

    # ─────────────────────────────────────────────────────────────────────────
    # Per-Component Scores (for debugging / transparency)
    # ─────────────────────────────────────────────────────────────────────────

    def score_components(self, output: str, task_type: str = "general") -> Dict[str, float]:
        """
        Return individual component scores for debugging.

        Returns:
            Dict mapping component name to score (0.0–1.0).
        """
        return {
            "entropy": round(self._entropy_score(output), 3),
            "repetition": round(self._repetition_score(output), 3),
            "length": round(self._length_score(output, task_type), 3),
            "parse_validity": round(self._parse_validity_score(output, task_type), 3),
        }
