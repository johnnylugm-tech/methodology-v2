# detection/uqlm_ensemble.py
"""FR-U-1: UQLM Ensemble Scorer.

This module implements the UQLM (Uncertainty Quantification via Language Models)
ensemble scoring system that combines multiple uncertainty scorers into a
unified UAF (Uncertainty-Aware Framework) score.

Main Components:
    - EnsembleScorer: Main class for computing ensemble uncertainty scores
    - BaseScorer: Abstract base for individual scorers
    - SemanticEntropyScorer, SemanticDensityScorer, SelfConsistencyScorer:
      Concrete scorer implementations

Algorithm:
    1. Generate n_samples responses using model sampling
    2. Compute each scorer independently:
       - semantic_entropy: Measures variation in semantic content
       - semantic_density: Measures concept density in response
       - self_consistency: Measures consistency across samples
    3. Apply weights and compute: uaf_score = Σ(weight_i × score_i)
    4. Return normalized score in [0.0, 1.0]

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from detection.data_models import (
    EnsembleConfig,
    EnsembleResult,
    ScorerResult,
)
from detection.exceptions import UQLMError


# =============================================================================
# Section 1: Base Scorer Interface
# =============================================================================


class BaseScorer(ABC):
    """Abstract base class for uncertainty scorers.

    All scorers must implement the score() method which takes a prompt,
    response, and number of samples, returning a float score.

    Attributes:
        name: Unique identifier for this scorer
    """

    def __init__(self, name: str = None) -> None:
        """Initialize BaseScorer with optional name.

        Args:
            name: Unique identifier for the scorer (optional for subclasses)
        """
        if name is not None:
            self.name = name

    @abstractmethod
    def score(
        self,
        prompt: str,
        response: str,
        n_samples: int,
        **kwargs: Any,
    ) -> float:
        """Compute uncertainty score for prompt-response pair.

        Args:
            prompt: Input prompt to the model
            response: Model response to evaluate
            n_samples: Number of samples to use for scoring

        Returns:
            Float score in [0.0, 1.0] where higher = more uncertain
        """
        pass

    def __repr__(self) -> str:
        """Return string representation of scorer."""
        return f"{self.__class__.__name__}(name={self.name!r})"


# =============================================================================
# Section 2: Concrete Scorer Implementations
# =============================================================================


class SemanticEntropyScorer(BaseScorer):
    """Semantic Entropy scorer using token probability distribution.

    Computes entropy of token-level probabilities to measure semantic
    uncertainty. High entropy indicates the model is uncertain about
    which tokens to generate.

    Algorithm:
        1. Get token logits from model
        2. Convert to probabilities via softmax
        3. Compute entropy: H = -Σ(p * log(p))
        4. Normalize to [0.0, 1.0]
    """

    def __init__(self) -> None:
        """Initialize SemanticEntropyScorer."""
        super().__init__()
        self.name = "semantic_entropy"

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: int,
        **kwargs: Any,
    ) -> float:
        """Compute semantic entropy score.

        Args:
            prompt: Input prompt (unused for this scorer)
            response: Response to evaluate
            n_samples: Number of samples (unused)

        Returns:
            Entropy score normalized to [0.0, 1.0]
        """
        # Placeholder implementation
        # In production, this would call the model API
        # to get token-level probabilities
        if not response or len(response.strip()) == 0:
            return 1.0  # Maximum uncertainty for empty response

        # Simulate entropy calculation
        # Real implementation would use model logits
        response_len = len(response.split())
        # Longer responses with more varied words = higher entropy
        base_entropy = min(response_len / 100.0, 1.0)
        return base_entropy


class SemanticDensityScorer(BaseScorer):
    """Semantic Density scorer measuring concept concentration.

    Measures how many distinct concepts are present in the response
    relative to its length. High density suggests the response is
    information-rich, potentially more reliable.

    Algorithm:
        1. Tokenize response
        2. Count unique concept tokens
        3. Compute density = unique_tokens / total_tokens
        4. Convert to uncertainty: 1.0 - density
    """

    def __init__(self) -> None:
        """Initialize SemanticDensityScorer."""
        super().__init__()
        self.name = "semantic_density"

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: int,
        **kwargs: Any,
    ) -> float:
        """Compute semantic density score.

        Args:
            prompt: Input prompt (unused)
            response: Response to evaluate
            n_samples: Number of samples (unused)

        Returns:
            Density-based uncertainty score in [0.0, 1.0]
        """
        if not response or len(response.strip()) == 0:
            return 1.0

        tokens = response.lower().split()
        if len(tokens) == 0:
            return 1.0

        unique_tokens = len(set(tokens))
        total_tokens = len(tokens)

        # Compute density (0.0 to 1.0)
        density = unique_tokens / total_tokens if total_tokens > 0 else 0.0

        # Convert to uncertainty (high density = low uncertainty)
        uncertainty = 1.0 - density
        return uncertainty


class SelfConsistencyScorer(BaseScorer):
    """Self-Consistency scorer measuring answer stability.

    Measures how consistent the model's answers are across multiple
    sampling runs. If the same question gets different answers,
    the model is uncertain.

    Algorithm:
        1. Generate n_samples answers to the prompt
        2. Compare semantic similarity between answers
        3. Compute consistency = agreements / total_pairs
        4. Convert to uncertainty: 1.0 - consistency
    """

    def __init__(self) -> None:
        """Initialize SelfConsistencyScorer."""
        super().__init__()
        self.name = "self_consistency"

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: int,
        **kwargs: Any,
    ) -> float:
        """Compute self-consistency score.

        Args:
            prompt: Input prompt
            response: Primary response to evaluate
            n_samples: Number of samples for consistency check

        Returns:
            Consistency-based uncertainty score in [0.0, 1.0]
        """
        if not response or len(response.strip()) == 0:
            return 1.0

        if n_samples < 2:
            return 0.0  # Cannot compute consistency with < 2 samples

        # Placeholder: In production, generate n_samples responses
        # and compare semantic similarity
        #
        # Real implementation:
        # 1. Call model n times with same prompt
        # 2. Compute pairwise semantic similarity
        # 3. Average similarity -> consistency
        # 4. uncertainty = 1.0 - consistency

        # Simulate consistency check
        # Assume some base consistency based on response length
        response_words = set(response.lower().split())
        base_consistency = min(len(response_words) / 50.0, 1.0)

        return 1.0 - base_consistency


class TokenNLLEvaluator(BaseScorer):
    """Token-level Negative Log-Likelihood evaluator.

    Auxiliary scorer that computes average NLL across tokens.
    High NLL indicates the model assigns low probability to its
    own generated tokens = higher uncertainty.

    This is typically used as an auxiliary scorer, not in the
    main ensemble.
    """

    def __init__(self) -> None:
        """Initialize TokenNLLEvaluator."""
        super().__init__()
        self.name = "token_nll"

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: int,
        **kwargs: Any,
    ) -> float:
        """Compute token-level NLL score.

        Args:
            prompt: Input prompt
            response: Response to evaluate
            n_samples: Number of samples (unused)

        Returns:
            NLL-based uncertainty score in [0.0, 1.0]
        """
        if not response or len(response.strip()) == 0:
            return 1.0

        # Placeholder: In production, compute actual NLL
        # using model token probabilities
        tokens = response.split()
        if len(tokens) == 0:
            return 1.0

        # Simulate NLL (inverse of average token probability)
        avg_token_prob = 0.7  # Placeholder
        nll = -np.log(avg_token_prob + 1e-10)

        # Normalize to [0.0, 1.0] assuming max NLL ~ 10
        normalized_nll = min(nll / 10.0, 1.0)
        return normalized_nll


# =============================================================================
# Section 3: Scorer Factory
# =============================================================================


class ScorerFactory:
    """Factory for creating scorer instances by name.

    Provides a registry of available scorers and factory methods
    to create them by name string.
    """

    # Registry of scorer classes by name
    _SCORERS: Dict[str, type] = {
        "semantic_entropy": SemanticEntropyScorer,
        "semantic_density": SemanticDensityScorer,
        "self_consistency": SelfConsistencyScorer,
        "token_nll": TokenNLLEvaluator,
    }

    @classmethod
    def create(cls, name: str) -> BaseScorer:
        """Create a scorer instance by name.

        Args:
            name: Scorer name identifier

        Returns:
            Instance of the requested scorer

        Raises:
            ValueError: If scorer name is not registered
        """
        if name not in cls._SCORERS:
            available = list(cls._SCORERS.keys())
            raise ValueError(
                f"Unknown scorer: {name!r}. "
                f"Available: {available}"
            )
        return cls._SCORERS[name]()

    @classmethod
    def register(cls, name: str, scorer_class: type) -> None:
        """Register a new scorer class.

        Args:
            name: Unique identifier for the scorer
            scorer_class: Scorer class (must inherit from BaseScorer)
        """
        if not issubclass(scorer_class, BaseScorer):
            raise TypeError(
                f"Scorer class must inherit from BaseScorer, "
                f"got {scorer_class}"
            )
        cls._SCORERS[name] = scorer_class

    @classmethod
    def available_scorers(cls) -> List[str]:
        """Get list of available scorer names.

        Returns:
            List of registered scorer names
        """
        return list(cls._SCORERS.keys())


# =============================================================================
# Section 4: Ensemble Scorer
# =============================================================================


class EnsembleScorer:
    """UQLM Ensemble Scorer combining multiple uncertainty scorers.

    This is the main entry point for FR-U-1. It coordinates multiple
    scorer instances and combines their outputs into a single UAF score.

    Attributes:
        config: Ensemble configuration
        _scorers: Dict mapping scorer names to instances

    Example:
        >>> config = EnsembleConfig(
        ...     weights=[0.4, 0.3, 0.3],
        ...     scorers=["semantic_entropy", "semantic_density", "self_consistency"],
        ...     n_samples=5,
        ... )
        >>> scorer = EnsembleScorer(config)
        >>> result = scorer.score("What is AI?", "AI is artificial intelligence.")
        >>> print(result.uaf_score)
        0.35
    """

    def __init__(
        self,
        config: Optional[EnsembleConfig] = None,
    ) -> None:
        """Initialize EnsembleScorer with configuration.

        Args:
            config: Optional EnsembleConfig. If None, uses defaults.
        """
        self.config = config or EnsembleConfig()
        self._scorers: Dict[str, BaseScorer] = {}
        self._initialize_scorers()

    def _initialize_scorers(self) -> None:
        """Initialize scorer instances from config."""
        for name in self.config.scorers:
            try:
                self._scorers[name] = ScorerFactory.create(name)
            except ValueError:
                # Skip unknown scorers, log warning in production
                pass

    def add_scorer(
        self,
        name: str,
        scorer: BaseScorer,
    ) -> None:
        """Add a custom scorer to the ensemble.

        Args:
            name: Unique identifier for the scorer
            scorer: Scorer instance to add

        Raises:
            ValueError: If scorer with name already exists
        """
        if name in self._scorers:
            raise ValueError(f"Scorer {name!r} already exists")
        self._scorers[name] = scorer

    def remove_scorer(self, name: str) -> None:
        """Remove a scorer from the ensemble.

        Args:
            name: Name of scorer to remove

        Raises:
            KeyError: If scorer name not found
        """
        del self._scorers[name]

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> EnsembleResult:
        """Compute UQLM ensemble uncertainty score.

        This is the main method for computing the UAF score.
        It generates samples, runs each scorer, and combines
        results using configured weights.

        Args:
            prompt: Input prompt to the model
            response: Model response to evaluate
            n_samples: Number of samples (overrides config)
            model_name: Model identifier (overrides config)

        Returns:
            EnsembleResult with uaf_score and individual scorer results

        Raises:
            UQLMError: If all scorers fail or model API fails
        """
        start_time = time.perf_counter()

        # Use config defaults if not provided
        n_samples = n_samples or self.config.n_samples
        model_name = model_name or self.config.model_name

        # Handle empty response
        if not response or len(response.strip()) == 0:
            return self._empty_response_result(model_name, n_samples, start_time)

        # Compute individual scores
        scorer_results: List[ScorerResult] = []
        total_weighted_score = 0.0
        total_weight = 0.0

        for name, scorer in self._scorers.items():
            try:
                raw_score = scorer.score(prompt, response, n_samples)
                normalized_score = self._normalize_score(raw_score)
                scorer_results.append(
                    ScorerResult(
                        scorer_name=name,
                        raw_score=raw_score,
                        normalized_score=normalized_score,
                        metadata={"model": model_name},
                    )
                )

                # Find weight for this scorer
                if name in self.config.scorers:
                    idx = self.config.scorers.index(name)
                    weight = self.config.weights[idx]
                    total_weighted_score += weight * normalized_score
                    total_weight += weight

            except Exception as e:
                # Log error, continue with other scorers
                # In production, would use proper logging
                print(f"Scorer {name} failed: {e}")
                continue

        # Handle case where no scorers succeeded
        if not scorer_results:
            raise UQLMError(
                message="All scorers failed",
                model_name=model_name,
                scorer_names=list(self._scorers.keys()),
                details={"prompt": prompt, "response": response[:100]},
            )

        # Compute weighted average
        uaf_score = (
            total_weighted_score / total_weight if total_weight > 0
            else 0.5  # Default to medium uncertainty
        )

        # Clamp to [0.0, 1.0]
        uaf_score = max(0.0, min(1.0, uaf_score))

        computation_time_ms = (time.perf_counter() - start_time) * 1000

        return EnsembleResult(
            uaf_score=uaf_score,
            scorer_results=scorer_results,
            computation_time_ms=computation_time_ms,
            model_used=model_name,
            n_samples=n_samples,
        )

    def _empty_response_result(
        self,
        model_name: str,
        n_samples: int,
        start_time: float,
    ) -> EnsembleResult:
        """Create result for empty response (max uncertainty).

        Args:
            model_name: Model identifier
            n_samples: Number of samples
            start_time: Start time for latency calculation

        Returns:
            EnsembleResult with uaf_score = 1.0
        """
        computation_time_ms = (time.perf_counter() - start_time) * 1000
        return EnsembleResult(
            uaf_score=1.0,  # Maximum uncertainty
            scorer_results=[
                ScorerResult(
                    scorer_name=name,
                    raw_score=1.0,
                    normalized_score=1.0,
                    metadata={"empty_response": True},
                )
                for name in self._scorers.keys()
            ],
            computation_time_ms=computation_time_ms,
            model_used=model_name,
            n_samples=n_samples,
        )

    def _normalize_score(self, score: float) -> float:
        """Normalize raw score to [0.0, 1.0] range.

        Args:
            score: Raw score from scorer

        Returns:
            Normalized score clamped to [0.0, 1.0]
        """
        return max(0.0, min(1.0, score))

    async def async_score(
        self,
        prompt: str,
        response: str,
        n_samples: int = 5,
    ) -> EnsembleResult:
        """Async version of score() for batch processing.

        Args:
            prompt: Input prompt
            response: Response to evaluate
            n_samples: Number of samples

        Returns:
            EnsembleResult with UAF score

        Note:
            This is a placeholder for true async implementation.
            In production, would use asyncio for parallel scorer execution.
        """
        # Synchronous implementation for now
        return self.score(prompt, response, n_samples)

    def get_scorer(self, name: str) -> Optional[BaseScorer]:
        """Get scorer instance by name.

        Args:
            name: Scorer name identifier

        Returns:
            Scorer instance or None if not found
        """
        return self._scorers.get(name)

    def get_config(self) -> EnsembleConfig:
        """Get current configuration.

        Returns:
            Copy of current EnsembleConfig
        """
        return EnsembleConfig(
            weights=self.config.weights.copy(),
            scorers=self.config.scorers.copy(),
            n_samples=self.config.n_samples,
            temperature=self.config.temperature,
            model_name=self.config.model_name,
        )
