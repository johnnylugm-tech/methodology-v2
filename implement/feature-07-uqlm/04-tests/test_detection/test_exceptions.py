"""Tests for detection/exceptions.py."""

from detection.exceptions import (
    BaselineNotFoundError,
    CalibrationError,
    DataInsufficientError,
    DetectionError,
    GapDetectionError,
    InsufficientDataError,
    ProbeError,
    UQLMError,
)


class TestDetectionError:
    def test_init_default(self):
        err = DetectionError("test message")
        assert err.message == "test message"
        assert err.component == "detection"
        assert err.details == {}

    def test_init_with_details(self):
        err = DetectionError("test", component="test_comp", details={"key": "val"})
        assert err.message == "test"
        assert err.component == "test_comp"
        assert err.details == {"key": "val"}

    def test_str_without_details(self):
        err = DetectionError("msg", component="comp")
        assert "comp" in str(err)
        assert "msg" in str(err)

    def test_str_with_details(self):
        err = DetectionError("msg", component="comp", details={"a": 1})
        s = str(err)
        assert "comp" in s
        assert "msg" in s
        assert "a" in s

    def test_inherits_from_exception(self):
        err = DetectionError("test")
        assert isinstance(err, Exception)


class TestUQLMError:
    def test_init_defaults(self):
        err = UQLMError("test message")
        assert err.message == "test message"
        assert err.component == "UQLMEnsemble"
        assert err.model_name == ""
        assert err.scorer_names == []
        assert err.retry_count == 0

    def test_init_full(self):
        err = UQLMError(
            "test",
            model_name="gpt-4",
            scorer_names=["se", "sd"],
            retry_count=3,
            details={"key": "val"},
        )
        assert err.model_name == "gpt-4"
        assert err.scorer_names == ["se", "sd"]
        assert err.retry_count == 3
        assert err.details == {"key": "val"}

    def test_str_includes_model(self):
        err = UQLMError("msg", model_name="gpt-4")
        assert "gpt-4" in str(err)

    def test_str_includes_scorers(self):
        err = UQLMError("msg", scorer_names=["a", "b"])
        assert "a" in str(err)
        assert "b" in str(err)

    def test_str_includes_retries(self):
        err = UQLMError("msg", retry_count=5)
        assert "5" in str(err)

    def test_inherits_from_detection_error(self):
        err = UQLMError("test")
        assert isinstance(err, DetectionError)


class TestProbeError:
    def test_init_defaults(self):
        err = ProbeError("test")
        assert err.message == "test"
        assert err.component == "ActivationProbe"
        assert err.model_type == ""
        assert err.layer_idx == -1
        assert err.probe_type == ""

    def test_init_full(self):
        err = ProbeError(
            "test",
            model_type="llama-3.3",
            layer_idx=5,
            probe_type="logistic_regression",
            details={"k": "v"},
        )
        assert err.model_type == "llama-3.3"
        assert err.layer_idx == 5
        assert err.probe_type == "logistic_regression"

    def test_str_includes_model(self):
        err = ProbeError("msg", model_type="llama-3.3")
        assert "llama-3.3" in str(err)

    def test_str_includes_layer(self):
        err = ProbeError("msg", layer_idx=10)
        s = str(err)
        assert "10" in s

    def test_inherits_from_detection_error(self):
        err = ProbeError("test")
        assert isinstance(err, DetectionError)


class TestDataInsufficientError:
    def test_init_defaults(self):
        err = DataInsufficientError("test")
        assert err.message == "test"
        assert err.component == "DataValidation"
        assert err.provided_count == 0
        assert err.required_count == 10
        assert err.data_type == "training"

    def test_init_full(self):
        err = DataInsufficientError(
            "test",
            provided_count=5,
            required_count=20,
            data_type="validation",
            details={"k": "v"},
        )
        assert err.provided_count == 5
        assert err.required_count == 20
        assert err.data_type == "validation"

    def test_str_includes_counts(self):
        err = DataInsufficientError("msg", provided_count=3, required_count=10)
        s = str(err)
        assert "3" in s
        assert "10" in s

    def test_inherits_from_detection_error(self):
        err = DataInsufficientError("test")
        assert isinstance(err, DetectionError)


class TestBaselineNotFoundError:
    def test_init_defaults(self):
        err = BaselineNotFoundError("test")
        assert err.message == "test"
        assert err.component == "MetaQA"
        assert err.baseline_version == ""
        assert err.window_size == 0

    def test_init_full(self):
        err = BaselineNotFoundError(
            "test",
            baseline_version="v1",
            window_size=100,
            details={"k": "v"},
        )
        assert err.baseline_version == "v1"
        assert err.window_size == 100

    def test_str_includes_version(self):
        err = BaselineNotFoundError("msg", baseline_version="v2.0")
        assert "v2.0" in str(err)

    def test_str_includes_window(self):
        err = BaselineNotFoundError("msg", window_size=50)
        s = str(err)
        assert "50" in s

    def test_inherits_from_detection_error(self):
        err = BaselineNotFoundError("test")
        assert isinstance(err, DetectionError)


class TestCalibrationError:
    def test_init_defaults(self):
        err = CalibrationError("test")
        assert err.message == "test"
        assert err.component == "Calibration"
        assert err.confidence_value == -1.0
        assert err.outcome_value is False

    def test_init_full(self):
        err = CalibrationError(
            "test",
            confidence_value=1.5,
            outcome_value=True,
            details={"k": "v"},
        )
        assert err.confidence_value == 1.5
        assert err.outcome_value is True

    def test_str_includes_confidence(self):
        err = CalibrationError("msg", confidence_value=0.8)
        assert "0.8" in str(err)

    def test_inherits_from_detection_error(self):
        err = CalibrationError("test")
        assert isinstance(err, DetectionError)


class TestGapDetectionError:
    def test_init_defaults(self):
        err = GapDetectionError("test")
        assert err.message == "test"
        assert err.component == "GapDetector"
        assert err.file_path == ""
        assert err.line_number == 0
        assert err.error_type == ""

    def test_init_full(self):
        err = GapDetectionError(
            "test",
            file_path="/path/file.py",
            line_number=42,
            error_type="syntax",
            details={"k": "v"},
        )
        assert err.file_path == "/path/file.py"
        assert err.line_number == 42
        assert err.error_type == "syntax"

    def test_str_includes_file(self):
        err = GapDetectionError("msg", file_path="test.py")
        assert "test.py" in str(err)

    def test_str_includes_line(self):
        err = GapDetectionError("msg", line_number=10)
        assert "10" in str(err)

    def test_str_includes_error_type(self):
        err = GapDetectionError("msg", error_type="parse")
        assert "parse" in str(err)

    def test_inherits_from_detection_error(self):
        err = GapDetectionError("test")
        assert isinstance(err, DetectionError)


class TestInsufficientDataError:
    def test_init_defaults(self):
        err = InsufficientDataError("test")
        assert err.message == "test"
        assert err.component == "UncertaintyScore"
        assert err.missing_components == []
        assert err.provided_components == []

    def test_init_full(self):
        err = InsufficientDataError(
            "test",
            missing_components=["uqlm", "clap"],
            provided_components=["metaqa"],
            details={"k": "v"},
        )
        assert err.missing_components == ["uqlm", "clap"]
        assert err.provided_components == ["metaqa"]

    def test_str_includes_missing(self):
        err = InsufficientDataError("msg", missing_components=["a", "b"])
        s = str(err)
        assert "a" in s
        assert "b" in s

    def test_inherits_from_detection_error(self):
        err = InsufficientDataError("test")
        assert isinstance(err, DetectionError)
