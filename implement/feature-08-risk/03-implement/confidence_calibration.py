"""
Confidence Calibration [FR-R-10]

Calibrates confidence scores against actual outcomes, integrates with UQLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable
import statistics


@dataclass
class CalibrationResult:
    """
    Result of confidence calibration.

    Attributes:
        decision_id: The decision being calibrated
        initial_confidence: Original confidence score
        actual_outcome: Observed outcome score
        calibrated_confidence: Adjusted confidence score
        calibration_error: Absolute error between initial and outcome
        calibration_status: "well_calibrated", "moderately_miscalibrated", "miscalibrated"
        adjustments_applied: List of adjustments made
        timestamp: When calibration was performed
    """

    decision_id: str
    initial_confidence: float
    actual_outcome: float
    calibrated_confidence: float
    calibration_error: float
    calibration_status: str
    adjustments_applied: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "initial_confidence": self.initial_confidence,
            "actual_outcome": self.actual_outcome,
            "calibrated_confidence": self.calibrated_confidence,
            "calibration_error": self.calibration_error,
            "calibration_status": self.calibration_status,
            "adjustments_applied": self.adjustments_applied,
            "timestamp": self.timestamp,
        }


class ConfidenceCalibrator:
    """
    Calibrates confidence scores using historical accuracy data and UQLM uncertainty.

    [FR-R-10]

    Calibration Error thresholds:
    - Well-Calibrated: ≤ 0.2
    - Moderately Miscalibrated: 0.2 < error ≤ 0.3
    - Miscalibrated: > 0.3
    """

    WELL_CALIBRATED_THRESHOLD = 0.2
    MODERATELY_MISCALIBRATED_THRESHOLD = 0.3

    def __init__(self, uqlm_integration=None, config: dict = None):
        """
        Initialize ConfidenceCalibrator.

        Args:
            uqlm_integration: Optional UQLM integration for uncertainty metrics
            config: Configuration dictionary
        """
        self._uqlm = uqlm_integration
        self._config = config or {}
        self._calibration_history: list[CalibrationResult] = []
        self._enabled = self._config.get("enabled", True)

        # Historical calibration error for adaptive adjustment
        self._avg_calibration_error = 0.0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def calibrate(
        self,
        decision_id: str,
        initial_confidence: float,
        actual_outcome: float,
        uqlm_uncertainty: Optional[float] = None
    ) -> CalibrationResult:
        """
        Calibrate confidence for a decision.

        Args:
            decision_id: Unique decision identifier
            initial_confidence: Original confidence (0.0-10.0)
            actual_outcome: Observed outcome score (0.0-10.0)
            uqlm_uncertainty: Optional uncertainty from UQLM (0.0-1.0)

        Returns:
            CalibrationResult with adjusted scores
        """
        if not self._enabled:
            return CalibrationResult(
                decision_id=decision_id,
                initial_confidence=initial_confidence,
                actual_outcome=actual_outcome,
                calibrated_confidence=initial_confidence,
                calibration_error=0.0,
                calibration_status="disabled",
            )

        # Calculate calibration error
        calibration_error = abs(initial_confidence - actual_outcome)

        # Determine calibration status
        if calibration_error <= self.WELL_CALIBRATED_THRESHOLD:
            status = "well_calibrated"
        elif calibration_error <= self.MODERATELY_MISCALIBRATED_THRESHOLD:
            status = "moderately_miscalibrated"
        else:
            status = "miscalibrated"

        # Apply adjustments
        adjustments = []
        calibrated_confidence = initial_confidence

        # UQLM uncertainty adjustment
        if uqlm_uncertainty is not None:
            uncertainty_penalty = uqlm_uncertainty * 0.5
            calibrated_confidence -= uncertainty_penalty * 10
            adjustments.append(f"UQLM uncertainty penalty: -{uncertainty_penalty * 10:.2f}")

        # Historical calibration error adjustment
        if self._avg_calibration_error > 0:
            calibration_penalty = self._avg_calibration_error * 0.3
            calibrated_confidence -= calibration_penalty
            adjustments.append(f"Historical calibration penalty: -{calibration_penalty:.2f}")

        # Clip to valid range
        calibrated_confidence = max(0.0, min(10.0, calibrated_confidence))

        result = CalibrationResult(
            decision_id=decision_id,
            initial_confidence=initial_confidence,
            actual_outcome=actual_outcome,
            calibrated_confidence=calibrated_confidence,
            calibration_error=calibration_error,
            calibration_status=status,
            adjustments_applied=adjustments,
        )

        # Store in history
        self._calibration_history.append(result)

        # Update average calibration error
        self._update_avg_calibration_error()

        return result

    def calibrate_with_formula(
        self,
        initial_confidence: float,
        uqlm_uncertainty: float,
        historical_calibration_error: float
    ) -> float:
        """
        Apply calibration formula directly.

        Formula from SPEC.md:
            adjusted = initial_confidence - (uncertainty_penalty + calibration_penalty) * 10

        Args:
            initial_confidence: Original confidence (0.0-10.0)
            uqlm_uncertainty: UQLM uncertainty (0.0-1.0)
            historical_calibration_error: Average calibration error from past decisions

        Returns:
            Adjusted confidence score
        """
        uncertainty_penalty = uqlm_uncertainty * 0.5
        calibration_penalty = historical_calibration_error * 0.3

        adjusted = initial_confidence - (uncertainty_penalty + calibration_penalty) * 10
        return max(0.0, min(10.0, adjusted))

    def _update_avg_calibration_error(self) -> None:
        """Update average calibration error from history."""
        if not self._calibration_history:
            return

        recent = self._calibration_history[-50:]  # Last 50 calibrations
        self._avg_calibration_error = statistics.mean(r.calibration_error for r in recent)

    def get_calibration_error(self, decision_id: str) -> Optional[float]:
        """
        Get calibration error for a specific decision.

        Args:
            decision_id: Decision to look up

        Returns:
            Calibration error if found, None otherwise
        """
        for result in reversed(self._calibration_history):
            if result.decision_id == decision_id:
                return result.calibration_error
        return None

    def get_historical_accuracy(self, window: int = 100) -> float:
        """
        Calculate historical accuracy based on calibration history.

        Args:
            window: Number of recent calibrations to consider

        Returns:
            Average accuracy (inverse of calibration error, scaled 0-1)
        """
        if not self._calibration_history:
            return 0.5  # Default 50%

        recent = self._calibration_history[-window:]
        avg_error = statistics.mean(r.calibration_error for r in recent)

        # Convert error to accuracy (0 error = 1.0 accuracy, 10 error = 0.0 accuracy)
        accuracy = 1.0 - (avg_error / 10.0)
        return max(0.0, min(1.0, accuracy))

    def get_miscalibration_rate(self, window: int = 100) -> float:
        """
        Get rate of miscalibrated decisions.

        Args:
            window: Number of recent calibrations to consider

        Returns:
            Fraction of decisions that are miscalibrated
        """
        if not self._calibration_history:
            return 0.0

        recent = self._calibration_history[-window:]
        miscalibrated = sum(1 for r in recent if r.calibration_status == "miscalibrated")
        return miscalibrated / len(recent)

    def get_calibration_trend(self, window: int = 50) -> str:
        """
        Get calibration trend direction.

        Args:
            window: Number of recent calibrations to compare

        Returns:
            "improving", "stable", or "degrading"
        """
        if len(self._calibration_history) < window:
            return "stable"

        recent = self._calibration_history[-window:]
        older = self._calibration_history[-window*2:-window] if len(self._calibration_history) >= window * 2 else recent

        recent_avg = statistics.mean(r.calibration_error for r in recent)
        older_avg = statistics.mean(r.calibration_error for r in older) if older != recent else recent_avg

        if recent_avg < older_avg * 0.9:
            return "improving"
        elif recent_avg > older_avg * 1.1:
            return "degrading"
        return "stable"

    def calibrate_confidence(
        self,
        initial_confidence: float,
        uqlm_uncertainty: Optional[float] = None
    ) -> float:
        """
        Standalone confidence calibration without a specific decision.

        Useful for pre-assessment calibration.

        Args:
            initial_confidence: Original confidence (0.0-10.0)
            uqlm_uncertainty: Optional UQLM uncertainty (0.0-1.0)

        Returns:
            Adjusted confidence score
        """
        if not self._enabled:
            return initial_confidence

        uncertainty = uqlm_uncertainty if uqlm_uncertainty is not None else self._get_default_uncertainty()

        return self.calibrate_with_formula(
            initial_confidence=initial_confidence,
            uqlm_uncertainty=uncertainty,
            historical_calibration_error=self._avg_calibration_error
        )

    def _get_default_uncertainty(self) -> float:
        """Get default uncertainty when UQLM is unavailable."""
        return self._config.get("default_uncertainty", 0.5)

    def get_calibration_data(self, decision_id: str) -> Optional[dict]:
        """
        Retrieve calibration data for a specific decision.

        Args:
            decision_id: Decision to look up

        Returns:
            Calibration data dict if found, None otherwise
        """
        for result in reversed(self._calibration_history):
            if result.decision_id == decision_id:
                return result.to_dict()
        return None

    def get_statistics(self) -> dict:
        """Get calibration statistics summary."""
        if not self._calibration_history:
            return {
                "total_calibrations": 0,
                "avg_calibration_error": 0.0,
                "miscalibration_rate": 0.0,
                "trend": "stable",
                "enabled": self._enabled,
            }

        return {
            "total_calibrations": len(self._calibration_history),
            "avg_calibration_error": self._avg_calibration_error,
            "miscalibration_rate": self.get_miscalibration_rate(),
            "trend": self.get_calibration_trend(),
            "historical_accuracy": self.get_historical_accuracy(),
            "enabled": self._enabled,
        }

    def export_history(self, limit: int = 1000) -> list[dict]:
        """Export calibration history for analysis."""
        return [r.to_dict() for r in self._calibration_history[-limit:]]

    def reset_history(self) -> None:
        """Clear calibration history."""
        self._calibration_history = []
        self._avg_calibration_error = 0.0