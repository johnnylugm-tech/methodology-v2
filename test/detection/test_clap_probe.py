"""Tests for detection/clap_probe.py."""
import pytest
from unittest.mock import patch, MagicMock, Mock

import numpy as np

from detection.data_models import ProbeConfig, ProbeResult, ProbeType
from detection.exceptions import DataInsufficientError, ProbeError
from detection.clap_probe import ActivationProbe


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_logistic_regression():
    """Mock LogisticRegression class."""
    mock_lr = Mock()
    mock_instance = Mock()
    mock_instance.fit = Mock()
    mock_instance.predict = Mock(return_value=np.array([0]))
    mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]]))
    mock_instance.score = Mock(return_value=0.85)
    mock_lr.return_value = mock_instance
    return mock_lr, mock_instance


@pytest.fixture
def training_data():
    """Create synthetic training data."""
    np.random.seed(42)
    # 20 samples, 10 features
    X_real = np.random.randn(10, 10) * 0.5 + np.array([1.0] * 10)
    X_hall = np.random.randn(10, 10) * 0.5 + np.array([-1.0] * 10)
    X = np.vstack([X_real, X_hall])
    y = np.array([0] * 10 + [1] * 10)
    return [(X[i], y[i]) for i in range(len(X))]


@pytest.fixture
def probe_config():
    return ProbeConfig(
        model_type="llama-3.3",
        layer_idx=-1,
        probe_type=ProbeType.LOGISTIC_REGRESSION,
        threshold=0.5,
    )


# =============================================================================
# Tests
# =============================================================================

class TestActivationProbeInit:
    def test_supported_model_accepted(self):
        for model in ["llama-3.3", "qwen-2.5", "llama-2", "mistral"]:
            cfg = ProbeConfig(model_type=model)
            probe = ActivationProbe(cfg)
            assert probe.config.model_type == model

    def test_closed_source_model_accepted(self):
        for model in ["gpt-4", "gpt-3.5-turbo", "claude-3"]:
            cfg = ProbeConfig(model_type=model)
            probe = ActivationProbe(cfg)
            assert probe.config.model_type == model

    def test_unknown_model_raises(self):
        cfg = ProbeConfig(model_type="unknown-model")
        with pytest.raises(ProbeError, match="Unsupported model"):
            ActivationProbe(cfg)

    def test_is_fitted_initially_false(self, probe_config):
        probe = ActivationProbe(probe_config)
        assert probe.is_fitted is False


class TestActivationProbeFit:
    def test_fit_too_few_samples(self, probe_config):
        probe = ActivationProbe(probe_config)
        small_data = [(np.zeros(10), 0) for _ in range(5)]
        with pytest.raises(DataInsufficientError, match="insufficient"):
            probe.fit(small_data)

    def test_fit_single_class_raises(self, probe_config):
        probe = ActivationProbe(probe_config)
        same_class_data = [(np.zeros(10), 1) for _ in range(15)]
        with pytest.raises(DataInsufficientError, match="both classes"):
            probe.fit(same_class_data)

    def test_fit_with_different_dimensions_succeeds(self, probe_config):
        """Fitting with consistent 2D data of any dimensionality succeeds."""
        probe = ActivationProbe(probe_config)
        # dim=5 works fine - sklearn accepts any 2D input
        data = [(np.zeros(5), 0) for _ in range(10)] + [(np.zeros(5), 1) for _ in range(10)]
        # Should not raise - fitting with consistent dims works
        result = probe.fit(data)
        assert probe.is_fitted is True
        assert isinstance(result, ProbeResult)

    @patch('detection.clap_probe.LogisticRegression')
    def test_fit_logistic_regression(self, mock_lr, probe_config, training_data):
        mock_instance = Mock()
        mock_instance.fit = Mock()
        mock_instance.predict = Mock(return_value=np.array([0, 1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        result = probe.fit(training_data)
        assert probe.is_fitted is True
        assert isinstance(result, ProbeResult)
        assert "accuracy" in result.metadata

    @patch('detection.clap_probe.LogisticRegression')
    def test_fit_linear_probe_type(self, mock_lr, training_data):
        mock_instance = Mock()
        mock_instance.fit = Mock()
        mock_instance.predict = Mock(return_value=np.array([0, 1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        cfg = ProbeConfig(model_type="llama-3.3", probe_type=ProbeType.LINEAR)
        probe = ActivationProbe(cfg)
        result = probe.fit(training_data)
        assert probe.is_fitted is True

    def test_fit_unsupported_probe_type(self, training_data):
        cfg = ProbeConfig(model_type="llama-3.3", probe_type=ProbeType.MLP)
        probe = ActivationProbe(cfg)
        with pytest.raises(ProbeError, match="not implemented"):
            probe.fit(training_data)


class TestActivationProbePredict:
    def test_predict_before_fit_raises(self, probe_config):
        probe = ActivationProbe(probe_config)
        with pytest.raises(ProbeError, match="must be trained"):
            probe.predict(np.zeros(10))

    @patch('detection.clap_probe.LogisticRegression')
    def test_predict_single_sample_1d(self, mock_lr, probe_config, training_data):
        # Build a mock that returns correct shapes for both fit() and predict()
        mock_instance = Mock()
        # During fit(): sklearn calls predict(X) with shape (20, 10)
        # and predict_proba(X) with shape (20, 10) -> needs (20, 2)
        # During predict(): probe calls predict(normalized) with shape (1, 10) -> (1,)
        # and predict_proba(normalized) with shape (1, 10) -> (1, 2)
        # side_effect handles different call shapes
        mock_instance.predict = Mock(side_effect=[
            np.array([0, 1] * 10),  # fit() context
            np.array([0]),           # predict() context - 1 sample
        ])
        mock_instance.predict_proba = Mock(side_effect=[
            np.array([[0.7, 0.3]] * 20),  # fit() context
            np.array([[0.7, 0.3]]),        # predict() context - 1 sample
        ])
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        hidden = np.random.randn(10)
        result = probe.predict(hidden)
        assert isinstance(result, ProbeResult)
        assert 0.0 <= result.p_hallucinate <= 1.0
        assert 0.0 <= result.confidence <= 1.0

    @patch('detection.clap_probe.LogisticRegression')
    def test_predict_single_sample_2d(self, mock_lr, probe_config, training_data):
        mock_instance = Mock()
        mock_instance.predict = Mock(side_effect=[
            np.array([0, 1] * 10),
            np.array([0]),
        ])
        mock_instance.predict_proba = Mock(side_effect=[
            np.array([[0.7, 0.3]] * 20),
            np.array([[0.7, 0.3]]),
        ])
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        hidden = np.random.randn(1, 10)
        result = probe.predict(hidden)
        assert isinstance(result, ProbeResult)

    @patch('detection.clap_probe.LogisticRegression')
    def test_predict_batch(self, mock_lr, probe_config, training_data):
        mock_instance = Mock()
        mock_instance.predict = Mock(side_effect=[
            np.array([0, 1] * 10),
            np.array([0, 1, 0, 1, 0]),  # 5 samples
        ])
        mock_instance.predict_proba = Mock(side_effect=[
            np.array([[0.7, 0.3]] * 20),
            np.array([[0.7, 0.3]] * 5),  # 5 samples
        ])
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        hidden = np.random.randn(5, 10)
        result = probe.predict(hidden)
        assert isinstance(result, ProbeResult)

    @patch('detection.clap_probe.LogisticRegression')
    def test_predict_wrong_dimensions(self, mock_lr, probe_config, training_data):
        mock_instance = Mock()
        mock_instance.fit = Mock()
        # Only called during fit()
        mock_instance.predict = Mock(return_value=np.array([0, 1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        # 3D array - should raise ProbeError for wrong dimensionality
        hidden = np.random.randn(5, 5, 5)
        with pytest.raises(ProbeError):
            probe.predict(hidden)


class TestActivationProbePredictFromLayer:
    def test_unsupported_model_for_extraction(self, probe_config):
        probe = ActivationProbe(probe_config)
        # Should raise since qwen hidden state extraction not implemented for qwen
        cfg = ProbeConfig(model_type="gpt-4")
        probe_gpt = ActivationProbe(cfg)
        with pytest.raises(ProbeError, match="not implemented"):
            probe_gpt.predict_from_layer(MagicMock(), layer_idx=-1)


class TestActivationProbeModelOperations:
    def test_get_config(self, probe_config):
        probe = ActivationProbe(probe_config)
        cfg = probe.get_config()
        assert cfg.model_type == "llama-3.3"
        assert cfg.layer_idx == -1

    def test_is_trained_false_before_fit(self, probe_config):
        probe = ActivationProbe(probe_config)
        assert probe.is_trained() is False

    @patch('detection.clap_probe.LogisticRegression')
    def test_is_trained_true_after_fit(self, mock_lr, probe_config, training_data):
        mock_instance = Mock()
        mock_instance.fit = Mock()
        mock_instance.predict = Mock(return_value=np.array([0, 1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        assert probe.is_trained() is True


class TestActivationProbeSaveLoad:
    def test_save_untrained_raises(self, probe_config):
        probe = ActivationProbe(probe_config)
        with pytest.raises(ProbeError, match="Cannot save untrained"):
            probe.save("/tmp/probe.pkl")

    def test_load_nonexistent_raises(self):
        with pytest.raises(ProbeError, match="not found"):
            ActivationProbe.load("/nonexistent/path.pkl")


class TestActivationProbeSupportedModels:
    def test_supported_open_weight_models(self):
        probe = ActivationProbe(ProbeConfig(model_type="llama-3.3"))
        assert "llama-3.3" in probe.SUPPORTED_OPEN_WEIGHT_MODELS

    def test_closed_source_models(self):
        probe = ActivationProbe(ProbeConfig(model_type="gpt-4"))
        assert "gpt-4" in probe.CLOSED_SOURCE_MODELS