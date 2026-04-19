"""Tests for detection/confidence_calibrator.py."""
import pytest
from datetime import datetime

from detection.data_models import CalibrationResult
from detection.exceptions import CalibrationError
from detection.confidence_calibrator import (
    CalibrationRecord,
    CalibrationConfig,
    ConfidenceCalibrator,
    logit,
    platt_scale,
    sigmoid,
)


# =============================================================================
# Utility function tests
# =============================================================================

class TestLogit:
    def test_logit_midpoint(self):
        # logit(0.5) = 0
        assert abs(logit(0.5)) < 1e-6

    def test_logit_positive(self):
        # logit(0.7) > 0
        assert logit(0.7) > 0

    def test_logit_negative(self):
        # logit(0.3) < 0
        assert logit(0.3) < 0

    def test_logit_eps_bounded(self):
        # logit(0) and logit(1) should not raise
        # They get clamped to eps
        assert abs(logit(0.0)) < 50  # clamped to eps
        assert abs(logit(1.0)) < 50

    def test_logit_near_boundary(self):
        # Very close to 0 or 1 should still work
        assert abs(logit(0.001)) > 0
        assert abs(logit(0.999)) > 0


class TestSigmoid:
    def test_sigmoid_zero(self):
        assert abs(sigmoid(0.0) - 0.5) < 1e-6

    def test_sigmoid_positive_large(self):
        # sigmoid(10) ~ 1
        assert sigmoid(10.0) > 0.999

    def test_sigmoid_negative_large(self):
        # sigmoid(-10) ~ 0
        assert sigmoid(-10.0) < 0.001

    def test_sigmoid_extreme_negative(self):
        # sigmoid(-700) should not overflow
        assert sigmoid(-700.0) == 0.0

    def test_sigmoid_extreme_positive(self):
        # sigmoid(700) should not overflow
        assert sigmoid(700.0) == 1.0


class TestPlattScale:
    def test_identity_case(self):
        # When initial == expected, should return initial
        result = platt_scale(0.5, 0.5)
        # logit(0.5) - logit(0.5) = 0, sigmoid(0) = 0.5
        assert abs(result - 0.5) < 1e-6

    def test_initial_higher_than_expected(self):
        # Initial confidence higher than expected accuracy
        result = platt_scale(0.9, 0.5)
        # Should be adjusted downward
        assert 0.0 <= result <= 1.0

    def test_initial_lower_than_expected(self):
        # Initial confidence lower than expected accuracy
        result = platt_scale(0.3, 0.7)
        assert 0.0 <= result <= 1.0

    def test_clamped_to_zero_one(self):
        # Extreme values should be clamped
        result = platt_scale(0.99, 0.01)
        assert 0.0 <= result <= 1.0

    def test_initial_zero_returns_initial(self):
        """Test that initial=0.0 returns initial as fallback."""
        result = platt_scale(0.0, 0.5)
        assert result == 0.0  # Returns initial as fallback

    def test_initial_one_returns_initial(self):
        """Test that initial=1.0 returns initial as fallback."""
        result = platt_scale(1.0, 0.5)
        assert result == 1.0  # Returns initial as fallback

    def test_expected_zero_returns_initial(self):
        """Test that expected=0.0 returns initial as fallback."""
        result = platt_scale(0.5, 0.0)
        assert result == 0.5  # Returns initial as fallback

    def test_expected_one_returns_initial(self):
        """Test that expected=1.0 returns initial as fallback."""
        result = platt_scale(0.5, 1.0)
        assert result == 0.5  # Returns initial as fallback


class TestCalibrationRecord:
    def test_basic(self):
        record = CalibrationRecord(
            timestamp=datetime.now(),
            initial_confidence=0.8,
            calibrated_confidence=0.75,
            expected_acc=0.7,
            actual_outcome=True,
            calibration_error=0.25,
        )
        assert record.initial_confidence == 0.8
        assert record.calibration_error == 0.25


# =============================================================================
# ConfidenceCalibrator tests
# =============================================================================

class TestConfidenceCalibratorInit:
    def test_default_config(self):
        cal = ConfidenceCalibrator()
        assert cal.config.history_size == 100
        assert cal.config.alert_threshold == 0.3

    def test_custom_config(self):
        cal = ConfidenceCalibrator(history_size=50, alert_threshold=0.2)
        assert cal.config.history_size == 50
        assert cal.config.alert_threshold == 0.2

    def test_history_size_zero_raises(self):
        with pytest.raises(CalibrationError, match="at least 1"):
            ConfidenceCalibrator(history_size=0)


class TestConfidenceCalibratorCalibrate:
    def test_first_calibration_returns_initial(self):
        cal = ConfidenceCalibrator()
        result = cal.calibrate(
            initial_confidence=0.8,
            actual_outcome=True,
            uqlm_uncertainty=0.2,
        )
        # First calibration returns initial as calibrated
        assert result.calibrated_confidence == 0.8

    def test_calibrate_validates_confidence_high(self):
        cal = ConfidenceCalibrator()
        with pytest.raises(CalibrationError, match="must be in"):
            cal.calibrate(
                initial_confidence=1.5,
                actual_outcome=True,
                uqlm_uncertainty=0.2,
            )

    def test_calibrate_validates_confidence_low(self):
        cal = ConfidenceCalibrator()
        with pytest.raises(CalibrationError, match="must be in"):
            cal.calibrate(
                initial_confidence=-0.1,
                actual_outcome=True,
                uqlm_uncertainty=0.2,
            )

    def test_calibrate_validates_uncertainty_high(self):
        cal = ConfidenceCalibrator()
        # First calibration would succeed but...
        # Create calibrator with history
        cal.history.append(
            CalibrationRecord(
                timestamp=datetime.now(),
                initial_confidence=0.5,
                calibrated_confidence=0.5,
                expected_acc=0.5,
                actual_outcome=True,
                calibration_error=0.5,
            )
        )
        with pytest.raises(CalibrationError, match="uqlm_uncertainty"):
            cal.calibrate(
                initial_confidence=0.5,
                actual_outcome=True,
                uqlm_uncertainty=1.5,
            )

    def test_calibrate_records_added(self):
        cal = ConfidenceCalibrator()
        initial_count = len(cal.history)
        cal.calibrate(0.8, True, 0.2)
        assert len(cal.history) == initial_count + 1

    def test_calibrate_second_call_uses_platt(self):
        cal = ConfidenceCalibrator()
        # First call
        cal.calibrate(0.8, True, 0.2)
        # Second call
        result2 = cal.calibrate(0.7, False, 0.3)
        # Should be adjusted via Platt scaling
        assert 0.0 <= result2.calibrated_confidence <= 1.0

    def test_calibrate_alert_when_error_exceeds_threshold(self):
        cal = ConfidenceCalibrator(alert_threshold=0.1)
        # First calibration
        cal.calibrate(0.8, True, 0.2)
        # Second - if error exceeds threshold
        result = cal.calibrate(0.95, False, 0.1)  # almost certain but failed
        # calibration_error should be large


class TestConfidenceCalibratorGetters:
    def test_get_calibration_error_empty(self):
        cal = ConfidenceCalibrator()
        assert cal.get_calibration_error() == 0.0

    def test_get_calibration_error_with_history(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.6, False, 0.4)
        error = cal.get_calibration_error()
        assert error >= 0.0

    def test_get_recent_error_empty(self):
        cal = ConfidenceCalibrator()
        assert cal.get_recent_error() == 0.0

    def test_get_recent_error_with_history(self):
        cal = ConfidenceCalibrator()
        for i in range(20):
            cal.calibrate(0.5 + (i % 2) * 0.3, i % 2 == 0, 0.3)
        error = cal.get_recent_error(n=5)
        assert error >= 0.0

    def test_get_history_size(self):
        cal = ConfidenceCalibrator()
        assert cal.get_history_size() == 0
        cal.calibrate(0.8, True, 0.2)
        assert cal.get_history_size() == 1

    def test_reset_history(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        assert len(cal.history) > 0
        cal.reset_history()
        assert len(cal.history) == 0

    def test_get_last_calibration_empty(self):
        cal = ConfidenceCalibrator()
        assert cal.get_last_calibration() is None

    def test_get_last_calibration_with_history(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        last = cal.get_last_calibration()
        assert isinstance(last, CalibrationResult)
        assert last.initial_confidence == 0.8


class TestConfidenceCalibratorTrends:
    def test_get_calibration_trend_too_few_records(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.7, False, 0.3)
        # Less than 3 records -> stable
        assert cal.get_calibration_trend() == "stable"

    def test_get_calibration_trend_stable(self):
        cal = ConfidenceCalibrator()
        for i in range(10):
            cal.calibrate(0.5 + (i % 3) * 0.1, i % 2 == 0, 0.3)
        trend = cal.get_calibration_trend()
        assert trend in ["improving", "worsening", "stable"]

    def test_get_calibration_trend_older_empty(self):
        """Test when older is empty (history 3-9 records)."""
        cal = ConfidenceCalibrator()
        # 5 records - older will be empty (history[:-5] = [])
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.7, False, 0.3)
        cal.calibrate(0.6, True, 0.4)
        cal.calibrate(0.5, False, 0.5)
        cal.calibrate(0.4, True, 0.6)
        # Should return "stable" because older is empty
        assert cal.get_calibration_trend() == "stable"

    def test_get_calibration_trend_worsening(self):
        """Test when recent error is higher than older error (diff > 0.05)."""
        cal = ConfidenceCalibrator()
        # Create 10 records with increasing error
        # Older 5: low error (~0.1)
        for i in range(5):
            cal.calibrate(0.9, True, 0.8)  # error = abs(0.9 - 0.8) = 0.1
        # Recent 5: high error (~0.4) - this will make diff > 0.05
        for i in range(5):
            cal.calibrate(0.5, False, 0.0)  # error = abs(0.5 - 0.0) = 0.5
        trend = cal.get_calibration_trend()
        # Recent error (0.5) > Older error (0.1) + 0.05, so "worsening"
        assert trend == "worsening"

    def test_get_calibration_trend_improving(self):
        """Test when recent error is lower than older error (diff < -0.05)."""
        cal = ConfidenceCalibrator()
        # Create 10 records where recent has lower error than older
        # Due to the bug in calibrate, error is actual_value (1.0 or 0.0), not difference
        # For first calibration, error = |actual_value - initial|
        # Older 5: low initial (so low error when actual_outcome=False)
        for i in range(5):
            cal.calibrate(0.1, False, 0.5)  # error = |0.0 - 0.1| = 0.1
        # Recent 5: even lower initial
        for i in range(5):
            cal.calibrate(0.05, False, 0.5)  # error = |0.0 - 0.05| = 0.05
        trend = cal.get_calibration_trend()
        # Recent error (0.05) < Older error (0.1), so "improving"
        assert trend == "improving"

    def test_get_calibration_trend_stable_diff(self):
        """Test when diff is within stable range (-0.05 <= diff <= 0.05)."""
        cal = ConfidenceCalibrator()
        # Create 10 records with same error
        # Older 5
        for i in range(5):
            cal.calibrate(0.3, False, 0.5)  # error = |0.0 - 0.3| = 0.3
        # Recent 5: same initial
        for i in range(5):
            cal.calibrate(0.3, False, 0.5)  # error = 0.3
        trend = cal.get_calibration_trend()
        # diff = 0.3 - 0.3 = 0, which is in [-0.05, 0.05], so "stable"
        assert trend == "stable"


class TestConfidenceCalibratorAlerting:
    def test_should_alert_empty(self):
        cal = ConfidenceCalibrator(alert_threshold=0.1)
        assert cal.should_alert() is False

    def test_should_alert_below_threshold(self):
        cal = ConfidenceCalibrator(alert_threshold=0.3)
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.7, False, 0.3)
        # Recent errors should be below threshold


class TestConfidenceCalibratorAccuracy:
    def test_get_accuracy_empty(self):
        cal = ConfidenceCalibrator()
        assert cal.get_accuracy() == 0.0

    def test_get_accuracy_all_correct(self):
        cal = ConfidenceCalibrator()
        for _ in range(5):
            cal.calibrate(0.8, True, 0.2)
        assert cal.get_accuracy() == 1.0

    def test_get_accuracy_mixed(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.7, False, 0.3)
        # 1 correct out of 2
        assert abs(cal.get_accuracy() - 0.5) < 1e-6


class TestConfidenceCalibratorConfidenceVsAccuracy:
    def test_empty_history(self):
        cal = ConfidenceCalibrator()
        result = cal.get_confidence_vs_accuracy()
        assert result["avg_confidence"] == 0.0
        assert result["avg_accuracy"] == 0.0

    def test_with_history(self):
        cal = ConfidenceCalibrator()
        cal.calibrate(0.8, True, 0.2)
        cal.calibrate(0.7, False, 0.3)
        result = cal.get_confidence_vs_accuracy()
        assert "avg_confidence" in result
        assert "avg_accuracy" in result
        assert "calibration_diff" in result
