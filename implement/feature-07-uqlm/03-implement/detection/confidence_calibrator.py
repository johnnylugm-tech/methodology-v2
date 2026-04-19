# detection/confidence_calibrator.py
"""FR-U-7: Confidence Calibration.

This module implements confidence calibration for the Planner to ensure
that stated confidence aligns with actual outcomes.

Purpose:
    Calibrate the Planner's confidence scores based on actual results,
    using UQLM uncertainty as a reference signal.

Algorithm:
    1. Compute expected accuracy from UQLM: expected_acc = 1 - uqlm_uncertainty
    2. Apply Platt scaling: calibrated = sigmoid(logit(initial) - logit(expected))
    3. Compute error: calibration_error = |calibrated - actual_outcome|
    4. Alert if calibration_error > 0.3

Platt Scaling:
    A calibration method that adjusts confidence scores to better match
    actual accuracy rates using logistic regression transformation.

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, List, Optional

from detection.data_models import CalibrationConfig, CalibrationResult
from detection.exceptions import CalibrationError


# =============================================================================
# Section 1: Platt Scaling Utilities
# =============================================================================


def logit(p: float, eps: float = 1e-7) -> float:
    """Compute logit (inverse sigmoid) function.

    logit(p) = log(p / (1 - p))

    Args:
        p: Probability in (0, 1)
        eps: Small value to avoid log(0)

    Returns:
        Logit value

    Raises:
        CalibrationError: If p is outside (0, 1)
    """
    p = max(eps, min(1.0 - eps, p))
    return math.log(p / (1.0 - p))


def sigmoid(x: float) -> float:
    """Compute sigmoid function.

    sigmoid(x) = 1 / (1 + exp(-x))

    Args:
        x: Input value

    Returns:
        Sigmoid value in (0, 1)
    """
    # Prevent overflow
    if x <= -700:
        return 0.0
    if x >= 700:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def platt_scale(
    initial: float,
    expected: float,
) -> float:
    """Apply Platt scaling for calibration.

    calibrated = sigmoid(logit(initial) - logit(expected))

    This adjusts the initial confidence by accounting for the
    expected accuracy based on UQLM uncertainty.

    Args:
        initial: Initial confidence in [0.0, 1.0]
        expected: Expected accuracy in [0.0, 1.0]

    Returns:
        Calibrated confidence in [0.0, 1.0]
    """
    try:
        # Validate inputs are in valid range (0, 1) exclusive
        # This validation can fail and trigger CalibrationError
        if not (0.0 < initial < 1.0):
            raise CalibrationError(
                message=f"Initial confidence {initial} is out of valid range (0, 1)",
                confidence_value=initial,
            )
        if not (0.0 < expected < 1.0):
            raise CalibrationError(
                message=f"Expected accuracy {expected} is out of valid range (0, 1)",
                confidence_value=expected,
            )

        initial_logit = logit(initial)
        expected_logit = logit(expected)
        calibrated_logit = initial_logit - expected_logit
        calibrated = sigmoid(calibrated_logit)
        return max(0.0, min(1.0, calibrated))
    except CalibrationError:
        # If calibration fails, return initial as fallback
        return initial


# =============================================================================
# Section 2: Calibration Record
# =============================================================================


@dataclass
class CalibrationRecord:
    """Single calibration record for history tracking.

    Attributes:
        timestamp: When calibration was performed
        initial_confidence: Planner's stated confidence
        calibrated_confidence: Adjusted confidence
        expected_acc: Expected accuracy from UQLM
        actual_outcome: True outcome (True=success, False=failure)
        calibration_error: Absolute error
    """

    timestamp: datetime
    initial_confidence: float
    calibrated_confidence: float
    expected_acc: float
    actual_outcome: bool
    calibration_error: float


# =============================================================================
# Section 3: Confidence Calibrator
# =============================================================================


class ConfidenceCalibrator:
    """Confidence Calibration for Planner.

    Tracks calibration history and adjusts planner confidence scores
    to better match actual outcomes over time.

    Attributes:
        config: Calibration configuration
        history: Deque of CalibrationRecord objects

    Example:
        >>> calibrator = ConfidenceCalibrator()
        >>> result = calibrator.calibrate(
        ...     initial_confidence=0.8,
        ...     actual_outcome=True,
        ...     uqlm_uncertainty=0.2,
        ... )
        >>> print(result.calibrated_confidence)
        0.75
    """

    def __init__(
        self,
        history_size: int = 100,
        alert_threshold: float = 0.3,
    ) -> None:
        """Initialize calibrator with history size limit.

        Args:
            history_size: Maximum number of calibration records to keep
            alert_threshold: Calibration error threshold for alerts
        """
        if history_size < 1:
            raise CalibrationError(
                message="history_size must be at least 1",
                confidence_value=float(history_size),
            )

        self.config = CalibrationConfig(
            history_size=history_size,
            alert_threshold=alert_threshold,
        )
        self.history: Deque[CalibrationRecord] = deque(maxlen=history_size)

    def calibrate(
        self,
        initial_confidence: float,
        actual_outcome: bool,
        uqlm_uncertainty: float,
    ) -> CalibrationResult:
        """Calibrate confidence based on actual outcome.

        Args:
            initial_confidence: Planner's stated confidence in [0.0, 1.0]
            actual_outcome: True outcome (True=success, False=failure)
            uqlm_uncertainty: UQLM uncertainty score in [0.0, 1.0]

        Returns:
            CalibrationResult with calibrated confidence

        Raises:
            CalibrationError: If confidence is not in [0.0, 1.0]
        """
        # Validate inputs
        if not 0.0 <= initial_confidence <= 1.0:
            raise CalibrationError(
                message="initial_confidence must be in [0.0, 1.0]",
                confidence_value=initial_confidence,
            )

        if not 0.0 <= uqlm_uncertainty <= 1.0:
            raise CalibrationError(
                message="uqlm_uncertainty must be in [0.0, 1.0]",
                confidence_value=uqlm_uncertainty,
            )

        # First calibration: return initial as calibrated
        if len(self.history) == 0:
            calibrated_confidence = initial_confidence
            calibration_error = (
                abs(1.0 if actual_outcome else 0.0 - calibrated_confidence)
            )
            alert = calibration_error > self.config.alert_threshold

            record = CalibrationRecord(
                timestamp=datetime.now(),
                initial_confidence=initial_confidence,
                calibrated_confidence=calibrated_confidence,
                expected_acc=1.0 - uqlm_uncertainty,
                actual_outcome=actual_outcome,
                calibration_error=calibration_error,
            )
            self.history.append(record)

            return CalibrationResult(
                initial_confidence=initial_confidence,
                calibrated_confidence=calibrated_confidence,
                actual_outcome=actual_outcome,
                calibration_error=calibration_error,
                alert=alert,
                timestamp=record.timestamp,
            )

        # Compute expected accuracy from UQLM
        expected_acc = 1.0 - uqlm_uncertainty

        # Apply Platt scaling
        calibrated_confidence = platt_scale(initial_confidence, expected_acc)

        # Compute calibration error
        actual_value = 1.0 if actual_outcome else 0.0
        calibration_error = abs(calibrated_confidence - actual_value)

        # Determine alert
        alert = calibration_error > self.config.alert_threshold

        # Create record
        record = CalibrationRecord(
            timestamp=datetime.now(),
            initial_confidence=initial_confidence,
            calibrated_confidence=calibrated_confidence,
            expected_acc=expected_acc,
            actual_outcome=actual_outcome,
            calibration_error=calibration_error,
        )
        self.history.append(record)

        return CalibrationResult(
            initial_confidence=initial_confidence,
            calibrated_confidence=calibrated_confidence,
            actual_outcome=actual_outcome,
            calibration_error=calibration_error,
            alert=alert,
            timestamp=record.timestamp,
        )

    def get_calibration_error(self) -> float:
        """Get historical calibration error.

        Computes average calibration error across all history records.

        Returns:
            Average calibration error in [0.0, 1.0]
        """
        if not self.history:
            return 0.0

        total_error = sum(r.calibration_error for r in self.history)
        return total_error / len(self.history)

    def get_recent_error(self, n: int = 10) -> float:
        """Get calibration error for recent n records.

        Args:
            n: Number of recent records to consider

        Returns:
            Average recent calibration error
        """
        if not self.history:
            return 0.0

        recent = list(self.history)[-n:]
        total_error = sum(r.calibration_error for r in recent)
        return total_error / len(recent)

    def get_history_size(self) -> int:
        """Get number of calibration records in history.

        Returns:
            Number of records
        """
        return len(self.history)

    def reset_history(self) -> None:
        """Reset calibration history."""
        self.history.clear()

    def get_last_calibration(self) -> Optional[CalibrationResult]:
        """Get the most recent calibration result.

        Returns:
            Most recent CalibrationResult or None if history empty
        """
        if not self.history:
            return None

        last = self.history[-1]
        return CalibrationResult(
            initial_confidence=last.initial_confidence,
            calibrated_confidence=last.calibrated_confidence,
            actual_outcome=last.actual_outcome,
            calibration_error=last.calibration_error,
            alert=last.calibration_error > self.config.alert_threshold,
            timestamp=last.timestamp,
        )

    def get_calibration_trend(self) -> str:
        """Get trend of calibration error over time.

        Returns:
            Trend string: "improving", "worsening", or "stable"
        """
        if len(self.history) < 3:
            return "stable"

        recent = list(self.history)[-5:]
        older = list(self.history)[-10:-5] if len(self.history) >= 10 else list(self.history)[:-5]

        if not older:
            return "stable"

        recent_error = sum(r.calibration_error for r in recent) / len(recent)
        older_error = sum(r.calibration_error for r in older) / len(older)

        diff = recent_error - older_error

        if diff < -0.05:
            return "improving"
        elif diff > 0.05:
            return "worsening"
        else:
            return "stable"

    def should_alert(self) -> bool:
        """Check if alert should fire based on recent calibrations.

        Returns:
            True if recent calibration error exceeds threshold
        """
        recent_error = self.get_recent_error(n=5)
        return recent_error > self.config.alert_threshold

    def get_accuracy(self) -> float:
        """Get overall accuracy based on calibration history.

        Computes what fraction of predictions were correct.

        Returns:
            Accuracy in [0.0, 1.0]
        """
        if not self.history:
            return 0.0

        correct = sum(1 for r in self.history if r.actual_outcome)
        return correct / len(self.history)

    def get_confidence_vs_accuracy(self) -> dict:
        """Get relationship between confidence and accuracy.

        Returns:
            Dict with avg_confidence, avg_accuracy, calibration_diff
        """
        if not self.history:
            return {
                "avg_confidence": 0.0,
                "avg_accuracy": 0.0,
                "calibration_diff": 0.0,
            }

        avg_confidence = sum(r.calibrated_confidence for r in self.history) / len(self.history)
        avg_accuracy = self.get_accuracy()

        return {
            "avg_confidence": avg_confidence,
            "avg_accuracy": avg_accuracy,
            "calibration_diff": abs(avg_confidence - avg_accuracy),
        }
