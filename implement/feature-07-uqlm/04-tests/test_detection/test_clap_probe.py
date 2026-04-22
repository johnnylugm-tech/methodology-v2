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

    def test_fit_1d_hidden_states_raises(self, probe_config):
        """Fitting with 1D hidden states should raise DataInsufficientError."""
        probe = ActivationProbe(probe_config)
        # Scalar hidden states (0D) - when stacked give 1D, not 2D
        data = [(np.array(0.5), 0) for _ in range(10)] + [(np.array(0.5), 1) for _ in range(10)]
        with pytest.raises(DataInsufficientError, match="2D arrays"):
            probe.fit(data)

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
        probe.fit(training_data)
        assert probe.is_fitted is True

    def test_fit_unsupported_probe_type(self, training_data):
        cfg = ProbeConfig(model_type="llama-3.3", probe_type=ProbeType.MLP)
        probe = ActivationProbe(cfg)
        with pytest.raises(ProbeError, match="not implemented"):
            probe.fit(training_data)

    @patch('detection.clap_probe.LogisticRegression', None)
    def test_fit_sklearn_unavailable_raises(self, probe_config, training_data):
        """Test that fit raises ProbeError when sklearn is not available."""
        probe = ActivationProbe(probe_config)
        with pytest.raises(ProbeError, match="sklearn is required"):
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
        ActivationProbe(probe_config)
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


class TestActivationProbeSklearnUnavailable:
    """Tests for when sklearn is not available (LogisticRegression = None)."""

    def test_fit_when_sklearn_unavailable_raises(self):
        """When sklearn unavailable, fit() should raise ProbeError."""
        import detection.clap_probe as clap_module
        original_lr = clap_module.LogisticRegression
        clap_module.LogisticRegression = None
        try:
            cfg = ProbeConfig(model_type="llama-3.3", probe_type=ProbeType.LOGISTIC_REGRESSION)
            probe = ActivationProbe(cfg)
            # The LogisticRegression class will be None when sklearn unavailable
            # When we try to instantiate LogisticRegression in fit(), it will fail
            # since None is not callable
            data = [(np.zeros(10), 0) for _ in range(10)] + [(np.zeros(10), 1) for _ in range(10)]
            with pytest.raises((DataInsufficientError, ProbeError, TypeError)):
                probe.fit(data)
        finally:
            clap_module.LogisticRegression = original_lr


class TestActivationProbeFitExceptions:
    """Tests for fit() exception handling."""

    @patch('detection.clap_probe.LogisticRegression')
    def test_fit_training_failure(self, mock_lr, probe_config, training_data):
        """Test that fit() raises ProbeError when model.fit() fails."""
        mock_instance = Mock()
        mock_instance.fit = Mock(side_effect=RuntimeError("Training failed"))
        mock_instance.predict = Mock(return_value=np.array([0, 1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        with pytest.raises(ProbeError, match="Training failed"):
            probe.fit(training_data)

    @patch('detection.clap_probe.LogisticRegression')
    def test_fit_auc_calculation(self, mock_lr, probe_config, training_data):
        """Test that fit() computes AUC when sklearn.metrics is available."""
        mock_instance = Mock()
        mock_instance.fit = Mock()
        # Must return arrays with correct shape (20,) for y and (20,) for y_pred
        mock_instance.predict = Mock(return_value=np.array([0] * 10 + [1] * 10))
        mock_instance.predict_proba = Mock(return_value=np.array([[0.7, 0.3]] * 20))
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        result = probe.fit(training_data)
        assert isinstance(result, ProbeResult)


class TestActivationProbePredictExceptions:
    """Tests for predict() exception handling."""

    @patch('detection.clap_probe.LogisticRegression')
    def test_predict_exception(self, mock_lr, probe_config, training_data):
        """Test that predict() raises ProbeError when model.predict_proba fails."""
        mock_instance = Mock()
        mock_instance.fit = Mock()
        mock_instance.predict = Mock(side_effect=[
            np.array([0] * 10 + [1] * 10),
            RuntimeError("Predict failed")
        ])
        mock_instance.predict_proba = Mock(side_effect=[
            np.array([[0.7, 0.3]] * 20),
            RuntimeError("Predict failed")
        ])
        mock_instance.score = Mock(return_value=0.85)
        mock_lr.return_value = mock_instance

        probe = ActivationProbe(probe_config)
        probe.fit(training_data)
        hidden = np.random.randn(10)
        with pytest.raises(ProbeError, match="Prediction failed"):
            probe.predict(hidden)


class TestActivationProbeExtractHidden:
    """Tests for _extract_from_huggingface and _extract_from_qwen."""

    def test_extract_from_huggingface_with_hidden_states(self, probe_config):
        """Test extraction when model_output has hidden_states attribute."""
        probe = ActivationProbe(probe_config)
        mock_layer = MagicMock()
        mock_layer.numpy = MagicMock(return_value=np.array([[1.0, 2.0]]))
        mock_output = MagicMock()
        mock_output.hidden_states = (mock_layer,)
        result = probe._extract_from_huggingface(mock_output, layer_idx=0)
        assert isinstance(result, np.ndarray)

    def test_extract_from_huggingface_with_last_hidden_state(self, probe_config):
        """Test extraction when model_output has last_hidden_state attribute."""
        probe = ActivationProbe(probe_config)
        mock_output = MagicMock()
        mock_output.last_hidden_state = MagicMock()
        mock_output.last_hidden_state.numpy = MagicMock(return_value=np.array([[1.0, 2.0]]))
        del mock_output.hidden_states
        result = probe._extract_from_huggingface(mock_output, layer_idx=0)
        assert isinstance(result, np.ndarray)

    def test_extract_from_huggingface_missing_both(self, probe_config):
        """Test extraction when model_output has neither hidden_states nor last_hidden_state."""
        probe = ActivationProbe(probe_config)
        class NoHiddenStatesOutput:
            pass
        mock_output = NoHiddenStatesOutput()
        with pytest.raises(ProbeError, match="does not contain hidden states"):
            probe._extract_from_huggingface(mock_output, layer_idx=0)

    def test_extract_from_huggingface_layer_idx_minus_one(self, probe_config):
        """Test extraction when layer_idx=-1 (last layer)."""
        probe = ActivationProbe(probe_config)
        mock_layer = MagicMock()
        mock_layer.numpy = MagicMock(return_value=np.array([[1.0, 2.0]]))
        mock_output = MagicMock()
        mock_output.hidden_states = (mock_layer, mock_layer, mock_layer)
        result = probe._extract_from_huggingface(mock_output, layer_idx=-1)
        assert isinstance(result, np.ndarray)

    def test_extract_from_qwen_delegates_to_huggingface(self, probe_config):
        """Test that _extract_from_qwen delegates to _extract_from_huggingface."""
        probe = ActivationProbe(probe_config)
        mock_layer = MagicMock()
        mock_layer.numpy = MagicMock(return_value=np.array([[1.0, 2.0]]))
        mock_output = MagicMock()
        mock_output.hidden_states = (mock_layer,)
        result = probe._extract_from_qwen(mock_output, layer_idx=0)
        assert isinstance(result, np.ndarray)


class TestActivationProbePredictFromLayerUnknown:
    """Tests for predict_from_layer with unknown/closed-source models."""

    def test_predict_from_layer_with_closed_source_model(self):
        """Test that closed-source models raise error in predict_from_layer."""
        cfg = ProbeConfig(model_type="gpt-4")
        probe = ActivationProbe(cfg)
        with pytest.raises(ProbeError, match="not implemented"):
            probe.predict_from_layer(MagicMock(), layer_idx=-1)


class TestActivationProbeSaveLoadRoundtrip:
    """Tests for save/load roundtrip and exception handling."""

    def test_load_pickle_exception(self, tmp_path):
        """Test that load() raises ProbeError when pickle.load fails."""
        # Create a corrupted pickle file directly
        save_path = tmp_path / "corrupted_probe.pkl"
        with open(save_path, "wb") as f:
            f.write(b"This is not a valid pickle file")

        with pytest.raises(ProbeError, match="Failed to load"):
            ActivationProbe.load(str(save_path))
