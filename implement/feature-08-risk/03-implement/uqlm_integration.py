"""
UQLM Integration [FR-R-10]

Interface for Uncertainty Quantification Layer (UQLM) integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class UncertaintyMetrics:
    """
    Uncertainty metrics from UQLM.

    Attributes:
        overall_uncertainty: Overall uncertainty score (0.0-1.0)
        epistemic_uncertainty: Epistemic (knowledge-based) uncertainty
        aleatoric_uncertainty: Aleatoric (random) uncertainty
        confidence_interval: Tuple of (lower, upper) bounds
        breakdown: Category-level uncertainty breakdown
        model_version: UQLM model version used
        timestamp: When uncertainty was calculated
    """

    overall_uncertainty: float = 0.0
    epistemic_uncertainty: float = 0.0
    aleatoric_uncertainty: float = 0.0
    confidence_interval: tuple[float, float] = (0.0, 1.0)
    breakdown: dict[str, float] = field(default_factory=dict)
    model_version: str = "unknown"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def is_uncertain(self, threshold: float = 0.3) -> bool:
        """Check if uncertainty exceeds threshold."""
        return self.overall_uncertainty >= threshold

    def to_dict(self) -> dict:
        return {
            "overall_uncertainty": self.overall_uncertainty,
            "epistemic_uncertainty": self.epistemic_uncertainty,
            "aleatoric_uncertainty": self.aleatoric_uncertainty,
            "confidence_interval": list(self.confidence_interval),
            "breakdown": self.breakdown,
            "model_version": self.model_version,
            "timestamp": self.timestamp,
        }


class UQLMIntegration:
    """
    Interface for UQLM (Uncertainty Quantification Layer) integration.

    [FR-R-10]

    Provides:
    - Uncertainty score calculation
    - Uncertainty breakdown by category
    - Historical calibration data
    - Integration with confidence calibration
    """

    # Fallback uncertainty when UQLM is unavailable
    FALLBACK_UNCERTAINTY = 0.5

    def __init__(self, config: dict = None, client=None):
        """
        Initialize UQLMIntegration.

        Args:
            config: Configuration dictionary with UQLM settings
            client: Optional UQLM client instance
        """
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        self._client = client
        self._uncertainty_threshold = self._config.get("uncertainty_threshold", 0.3)

        # Cache for uncertainty calculations
        self._uncertainty_cache: dict[str, UncertaintyMetrics] = {}
        self._cache_ttl_seconds = self._config.get("cache_ttl_seconds", 60)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get_uncertainty_score(self, context: dict) -> float:
        """
        Get uncertainty score from UQLM.

        Args:
            context: Assessment context

        Returns:
            Uncertainty score in range [0.0, 1.0] where 0 = certain, 1 = highly uncertain
        """
        if not self._enabled:
            return self.FALLBACK_UNCERTAINTY

        try:
            metrics = self._calculate_uncertainty(context)
            return metrics.overall_uncertainty
        except Exception as e:
            logger.warning(f"UQLM uncertainty calculation failed: {e}")
            return self.FALLBACK_UNCERTAINTY

    def get_uncertainty_breakdown(self, context: dict) -> dict[str, float]:
        """
        Get detailed uncertainty breakdown by category.

        Args:
            context: Assessment context

        Returns:
            Dict mapping category names to uncertainty scores
        """
        if not self._enabled:
            return {}

        try:
            metrics = self._calculate_uncertainty(context)
            return metrics.breakdown
        except Exception as e:
            logger.warning(f"UQLM breakdown calculation failed: {e}")
            return {}

    def get_uncertainty_metrics(self, context: dict) -> UncertaintyMetrics:
        """
        Get full uncertainty metrics.

        Args:
            context: Assessment context

        Returns:
            UncertaintyMetrics with all available data
        """
        if not self._enabled:
            return UncertaintyMetrics(overall_uncertainty=self.FALLBACK_UNCERTAINTY)

        try:
            return self._calculate_uncertainty(context)
        except Exception as e:
            logger.warning(f"UQLM metrics calculation failed: {e}")
            return UncertaintyMetrics(overall_uncertainty=self.FALLBACK_UNCERTAINTY)

    def _calculate_uncertainty(self, context: dict) -> UncertaintyMetrics:
        """
        Calculate uncertainty using UQLM client.

        Args:
            context: Assessment context

        Returns:
            UncertaintyMetrics
        """
        # Check cache
        cache_key = self._get_cache_key(context)
        if cache_key in self._uncertainty_cache:
            cached = self._uncertainty_cache[cache_key]
            # Check if cache is still valid
            try:
                cached_time = datetime.fromisoformat(cached.timestamp)
                age = (datetime.utcnow() - cached_time).total_seconds()
                if age < self._cache_ttl_seconds:
                    return cached
            except Exception:
                pass

        # Use client if available, otherwise compute directly
        if self._client:
            result = self._client.calculate_uncertainty(context)
        else:
            result = self._compute_direct(context)

        metrics = UncertaintyMetrics(
            overall_uncertainty=result.get("overall", self.FALLBACK_UNCERTAINTY),
            epistemic_uncertainty=result.get("epistemic", 0.0),
            aleatoric_uncertainty=result.get("aleatoric", 0.0),
            confidence_interval=tuple(result.get("confidence_interval", [0.0, 1.0])),
            breakdown=result.get("breakdown", {}),
            model_version=result.get("model_version", "direct"),
        )

        # Cache result
        self._uncertainty_cache[cache_key] = metrics
        return metrics

    def _compute_direct(self, context: dict) -> dict:
        """
        Compute uncertainty directly when no UQLM client is available.

        Uses heuristics based on context properties.

        Args:
            context: Assessment context

        Returns:
            Uncertainty dict
        """
        uncertainty = 0.0
        breakdown = {}

        # Factor 1: Input completeness
        required_fields = ["data", "task", "agent_id"]
        missing = sum(1 for f in required_fields if f not in context)
        input_uncertainty = missing / len(required_fields) * 0.3
        uncertainty += input_uncertainty
        breakdown["input_completeness"] = input_uncertainty

        # Factor 2: Context length (shorter context = more uncertainty)
        context_length = len(str(context))
        if context_length < 100:
            length_uncertainty = 0.2
        elif context_length < 1000:
            length_uncertainty = 0.1
        else:
            length_uncertainty = 0.05
        uncertainty += length_uncertainty
        breakdown["context_length"] = length_uncertainty

        # Factor 3: Agent depth
        agent_depth = context.get("agent_depth", 1)
        if agent_depth > 3:
            depth_uncertainty = min(0.3, (agent_depth - 3) * 0.1)
        else:
            depth_uncertainty = 0.0
        uncertainty += depth_uncertainty
        breakdown["agent_depth"] = depth_uncertainty

        # Factor 4: Historical calibration error
        hist_error = context.get("historical_calibration_error", 0.0)
        calibration_uncertainty = hist_error * 0.2
        uncertainty += calibration_uncertainty
        breakdown["calibration"] = calibration_uncertainty

        # Normalize to 0-1 range
        uncertainty = min(1.0, uncertainty)

        # Split into epistemic (knowledge) and aleatoric (random)
        epistemic = uncertainty * 0.6
        aleatoric = uncertainty * 0.4

        return {
            "overall": uncertainty,
            "epistemic": epistemic,
            "aleatoric": aleatoric,
            "confidence_interval": [max(0.0, uncertainty - 0.1), min(1.0, uncertainty + 0.1)],
            "breakdown": breakdown,
            "model_version": "direct-compute",
        }

    def _get_cache_key(self, context: dict) -> str:
        """Generate cache key from context."""
        # Use task_id and agent_id for cache key
        key_parts = [
            context.get("task_id", ""),
            context.get("agent_id", ""),
            str(context.get("agent_depth", 0)),
        ]
        return "|".join(key_parts)

    def get_calibration_data(self, decision_id: str) -> Optional[dict]:
        """
        Retrieve historical calibration data for a specific decision.

        Args:
            decision_id: Decision to look up

        Returns:
            Calibration data dict if available, None otherwise
        """
        # In a full implementation, this would query UQLM's calibration store
        # For now, return None as calibration is handled by ConfidenceCalibrator
        return None

    def check_uncertainty_threshold(self, context: dict) -> bool:
        """
        Check if uncertainty exceeds configured threshold.

        Args:
            context: Assessment context

        Returns:
            True if uncertainty > threshold, False otherwise
        """
        uncertainty = self.get_uncertainty_score(context)
        return uncertainty > self._uncertainty_threshold

    def get_confidence_adjustment(self, context: dict) -> float:
        """
        Get confidence adjustment factor based on uncertainty.

        Args:
            context: Assessment context

        Returns:
            Adjustment factor to apply to confidence scores
        """
        uncertainty = self.get_uncertainty_score(context)

        # Higher uncertainty = larger negative adjustment
        # Max adjustment of 20% of confidence score
        adjustment = uncertainty * 0.2
        return adjustment

    def clear_cache(self) -> None:
        """Clear the uncertainty cache."""
        self._uncertainty_cache = {}

    def get_statistics(self) -> dict:
        """Get UQLM integration statistics."""
        return {
            "enabled": self._enabled,
            "uncertainty_threshold": self._uncertainty_threshold,
            "cache_size": len(self._uncertainty_cache),
            "client_connected": self._client is not None,
        }

    def set_threshold(self, threshold: float) -> None:
        """Update uncertainty threshold."""
        self._uncertainty_threshold = max(0.0, min(1.0, threshold))

    def enable(self) -> None:
        """Enable UQLM integration."""
        self._enabled = True

    def disable(self) -> None:
        """Disable UQLM integration (use fallback)."""
        self._enabled = False