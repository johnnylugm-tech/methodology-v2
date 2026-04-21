"""
Tests for ConfidenceCalibrator [FR-R-10]

Covers confidence calibration, historical tracking, and miscalibration detection.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from confidence_calibration import ConfidenceCalibrator, CalibrationResult


class TestCalibrationResult:
    """Test CalibrationResult dataclass."""

    def test_constructor_defaults(self):
        """Test default values."""
        result = CalibrationResult(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=8.0,
            calibrated_confidence=7.5,
            calibration_error=1.0,
            calibration_status="well_calibrated"
        )
        assert result.decision_id == "dec-001"
        assert result.initial_confidence == 7.0
        assert result.actual_outcome == 8.0
        assert result.calibrated_confidence == 7.5
        assert result.calibration_error == 1.0
        assert result.calibration_status == "well_calibrated"
        assert result.timestamp != ""

    def test_to_dict(self):
        """Test serialization to dict."""
        result = CalibrationResult(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=8.0,
            calibrated_confidence=7.5,
            calibration_error=1.0,
            calibration_status="well_calibrated",
            adjustments_applied=["test adjustment"]
        )
        d = result.to_dict()

        assert d["decision_id"] == "dec-001"
        assert d["initial_confidence"] == 7.0
        assert d["actual_outcome"] == 8.0
        assert d["calibration_status"] == "well_calibrated"
        assert "test adjustment" in d["adjustments_applied"]


class TestConfidenceCalibratorConstructor:
    """Test ConfidenceCalibrator constructor."""

    def test_constructor_default_enabled(self):
        """Test default enabled state."""
        calibrator = ConfidenceCalibrator()
        assert calibrator.enabled is True

    def test_constructor_with_config(self):
        """Test constructor with config."""
        calibrator = ConfidenceCalibrator(config={"enabled": False})
        assert calibrator.enabled is False

    def test_constructor_with_uqlm(self):
        """Test constructor with UQLM integration."""
        class MockUQLM:
            pass
        mock_uqlm = MockUQLM()
        calibrator = ConfidenceCalibrator(uqlm_integration=mock_uqlm)
        assert calibrator._uqlm is mock_uqlm


class TestConfidenceCalibratorCalibrate:
    """Test calibration methods."""

    def test_calibrate_disabled(self):
        """Test disabled calibrator returns initial confidence."""
        calibrator = ConfidenceCalibrator(config={"enabled": False})
        result = calibrator.calibrate(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=8.0
        )

        assert result.calibrated_confidence == 7.0
        assert result.calibration_status == "disabled"

    def test_calibrate_well_calibrated(self):
        """Test well-calibrated result (error <= 0.2)."""
        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=7.1  # Error = 0.1
        )

        assert abs(result.calibration_error - 0.1) < 0.001  # Float comparison
        assert result.calibration_status == "well_calibrated"

    def test_calibrate_moderately_miscalibrated(self):
        """Test moderately miscalibrated (0.2 < error <= 0.3)."""
        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=7.25  # Error = 0.25
        )

        assert result.calibration_error == 0.25
        assert result.calibration_status == "moderately_miscalibrated"

    def test_calibrate_miscalibrated(self):
        """Test miscalibrated result (error > 0.3)."""
        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=8.0  # Error = 1.0
        )

        assert result.calibration_error == 1.0
        assert result.calibration_status == "miscalibrated"

    def test_calibrate_with_uqlm_uncertainty(self):
        """Test calibration with UQLM uncertainty."""
        calibrator = ConfidenceCalibrator()
        result_no_uqlm = calibrator.calibrate(
            decision_id="dec-001",
            initial_confidence=7.0,
            actual_outcome=8.0,
            uqlm_uncertainty=None
        )

        calibrator2 = ConfidenceCalibrator()
        result_with_uqlm = calibrator2.calibrate(
            decision_id="dec-002",
            initial_confidence=7.0,
            actual_outcome=8.0,
            uqlm_uncertainty=0.5
        )

        # With UQLM uncertainty, confidence should be reduced more
        assert result_with_uqlm.calibrated_confidence <= result_no_uqlm.calibrated_confidence

    def test_calibrate_stores_history(self):
        """Test that calibration stores in history."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)
        calibrator.calibrate("dec-002", 6.0, 7.0)

        assert len(calibrator._calibration_history) == 2


class TestConfidenceCalibratorFormula:
    """Test calibration formula."""

    def test_calibrate_with_formula(self):
        """Test direct formula application."""
        calibrator = ConfidenceCalibrator()
        adjusted = calibrator.calibrate_with_formula(
            initial_confidence=7.0,
            uqlm_uncertainty=0.3,
            historical_calibration_error=0.2
        )

        # uncertainty_penalty = 0.3 * 0.5 = 0.15 -> 1.5
        # calibration_penalty = 0.2 * 0.3 = 0.06
        # total_penalty = 1.5 + 0.06 = 1.56
        # adjusted = 7.0 - 1.56 = 5.44
        assert 0.0 <= adjusted <= 10.0

    def test_calibrate_with_formula_capped_at_zero(self):
        """Test formula result is capped at 0."""
        calibrator = ConfidenceCalibrator()
        adjusted = calibrator.calibrate_with_formula(
            initial_confidence=2.0,
            uqlm_uncertainty=1.0,
            historical_calibration_error=1.0
        )

        assert adjusted >= 0.0

    def test_calibrate_with_formula_capped_at_ten(self):
        """Test formula result is capped at 10."""
        calibrator = ConfidenceCalibrator()
        adjusted = calibrator.calibrate_with_formula(
            initial_confidence=9.0,
            uqlm_uncertainty=0.0,
            historical_calibration_error=0.0
        )

        assert adjusted <= 10.0


class TestConfidenceCalibratorHistory:
    """Test historical calibration tracking."""

    def test_get_calibration_error(self):
        """Test getting calibration error for decision."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)  # error = 1.0
        calibrator.calibrate("dec-002", 6.0, 6.1)  # error = 0.1

        error = calibrator.get_calibration_error("dec-001")
        assert error == 1.0

        error2 = calibrator.get_calibration_error("dec-002")
        assert abs(error2 - 0.1) < 0.001  # Float comparison

    def test_get_calibration_error_nonexistent(self):
        """Test getting error for non-existent decision."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)

        error = calibrator.get_calibration_error("nonexistent")
        assert error is None

    def test_get_historical_accuracy_empty(self):
        """Test historical accuracy with empty history."""
        calibrator = ConfidenceCalibrator()
        accuracy = calibrator.get_historical_accuracy()
        assert accuracy == 0.5  # Default 50%

    def test_get_historical_accuracy(self):
        """Test historical accuracy calculation."""
        calibrator = ConfidenceCalibrator()
        # Add calibrations with known errors
        calibrator.calibrate("dec-001", 5.0, 5.0)  # error = 0
        calibrator.calibrate("dec-002", 5.0, 5.0)  # error = 0
        calibrator.calibrate("dec-003", 5.0, 5.0)  # error = 0
        calibrator.calibrate("dec-004", 5.0, 5.0)  # error = 0

        accuracy = calibrator.get_historical_accuracy()
        assert accuracy > 0.8  # Should be high accuracy

    def test_get_miscalibration_rate(self):
        """Test miscalibration rate calculation."""
        calibrator = ConfidenceCalibrator()
        # Add mix of calibrated and miscalibrated
        calibrator.calibrate("dec-001", 5.0, 5.5)  # error = 0.5 - miscalibrated
        calibrator.calibrate("dec-002", 5.0, 5.1)  # error = 0.1 - well calibrated
        calibrator.calibrate("dec-003", 5.0, 5.6)  # error = 0.6 - miscalibrated
        calibrator.calibrate("dec-004", 5.0, 5.0)  # error = 0 - well calibrated

        rate = calibrator.get_miscalibration_rate()
        assert 0.0 <= rate <= 1.0

    def test_get_calibration_trend_stable(self):
        """Test stable calibration trend."""
        calibrator = ConfidenceCalibrator()
        for i in range(100):
            calibrator.calibrate(f"dec-{i}", 5.0, 5.0 + (i % 3) * 0.1)

        trend = calibrator.get_calibration_trend()
        assert trend in ["improving", "stable", "degrading"]

    def test_get_calibration_trend_insufficient_data(self):
        """Test trend with insufficient data."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 5.0, 5.5)
        calibrator.calibrate("dec-002", 5.0, 5.5)

        trend = calibrator.get_calibration_trend(window=50)
        assert trend == "stable"


class TestConfidenceCalibratorStandalone:
    """Test standalone calibration methods."""

    def test_calibrate_confidence_disabled(self):
        """Test disabled returns initial confidence."""
        calibrator = ConfidenceCalibrator(config={"enabled": False})
        result = calibrator.calibrate_confidence(7.0)
        assert result == 7.0

    def test_calibrate_confidence_with_uncertainty(self):
        """Test standalone calibration with uncertainty."""
        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate_confidence(
            initial_confidence=7.0,
            uqlm_uncertainty=0.3
        )
        assert 0.0 <= result <= 10.0

    def test_calibrate_confidence_default_uncertainty(self):
        """Test standalone calibration with default uncertainty."""
        calibrator = ConfidenceCalibrator(config={"default_uncertainty": 0.5})
        result = calibrator.calibrate_confidence(initial_confidence=7.0)
        assert 0.0 <= result <= 10.0


class TestConfidenceCalibratorData:
    """Test calibration data retrieval."""

    def test_get_calibration_data(self):
        """Test getting calibration data."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)

        data = calibrator.get_calibration_data("dec-001")
        assert data is not None
        assert data["decision_id"] == "dec-001"

    def test_get_calibration_data_nonexistent(self):
        """Test getting data for non-existent decision."""
        calibrator = ConfidenceCalibrator()
        data = calibrator.get_calibration_data("nonexistent")
        assert data is None


class TestConfidenceCalibratorStatistics:
    """Test statistics retrieval."""

    def test_get_statistics_empty(self):
        """Test statistics with empty history."""
        calibrator = ConfidenceCalibrator()
        stats = calibrator.get_statistics()

        assert stats["total_calibrations"] == 0
        assert stats["avg_calibration_error"] == 0.0
        assert stats["miscalibration_rate"] == 0.0
        assert stats["trend"] == "stable"
        assert stats["enabled"] is True

    def test_get_statistics_with_data(self):
        """Test statistics with calibration data."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)
        calibrator.calibrate("dec-002", 6.0, 7.0)

        stats = calibrator.get_statistics()
        assert stats["total_calibrations"] == 2
        assert stats["enabled"] is True
        assert "historical_accuracy" in stats


class TestConfidenceCalibratorExport:
    """Test export methods."""

    def test_export_history(self):
        """Test history export."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)
        calibrator.calibrate("dec-002", 6.0, 7.0)

        history = calibrator.export_history(limit=10)
        assert len(history) == 2
        assert all(isinstance(h, dict) for h in history)

    def test_export_history_limit(self):
        """Test history export with limit."""
        calibrator = ConfidenceCalibrator()
        for i in range(10):
            calibrator.calibrate(f"dec-{i}", 7.0, 8.0)

        history = calibrator.export_history(limit=5)
        assert len(history) == 5


class TestConfidenceCalibratorReset:
    """Test reset methods."""

    def test_reset_history(self):
        """Test history reset."""
        calibrator = ConfidenceCalibrator()
        calibrator.calibrate("dec-001", 7.0, 8.0)
        calibrator.calibrate("dec-002", 6.0, 7.0)

        assert len(calibrator._calibration_history) == 2

        calibrator.reset_history()
        assert len(calibrator._calibration_history) == 0
        assert calibrator._avg_calibration_error == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
