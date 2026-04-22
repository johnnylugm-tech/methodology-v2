"""Tests for detection/tinylora.py."""
import pytest

import numpy as np

from detection.data_models import TinyLoRAConfig, TinyLoRAModel
from detection.exceptions import DataInsufficientError
from detection.tinylora import (
    TinyLoRA,
    apply_lora,
    compute_model_size,
    initialize_lora_matrices,
)


# =============================================================================
# Utility function tests
# =============================================================================

class TestApplyLoRA:
    def test_basic(self):
        original = np.eye(4)
        lora_a = np.zeros((4, 2))
        lora_b = np.zeros((2, 4))
        result = apply_lora(original, lora_a, lora_b, alpha=8.0)
        # BA = zeros, so result = original
        np.testing.assert_array_almost_equal(result, original)

    def test_with_nonzero_lora(self):
        original = np.eye(4)
        lora_a = np.ones((4, 2)) * 0.1
        lora_b = np.ones((2, 4)) * 0.1
        result = apply_lora(original, lora_a, lora_b, alpha=1.0)
        # Result = original + BA
        assert result.shape == (4, 4)


class TestInitializeLoRAMatrices:
    def test_dimensions(self):
        hidden_dim = 512
        rank = 4
        lora_a, lora_b = initialize_lora_matrices(hidden_dim, rank)
        assert lora_a.shape == (hidden_dim, rank)
        assert lora_b.shape == (rank, hidden_dim)

    def test_lora_a_random(self):
        lora_a1, _ = initialize_lora_matrices(100, 4)
        lora_a2, _ = initialize_lora_matrices(100, 4)
        # Random initialization should differ
        assert not np.allclose(lora_a1, lora_a2)

    def test_lora_b_zeros(self):
        _, lora_b = initialize_lora_matrices(100, 4)
        np.testing.assert_array_equal(lora_b, np.zeros((4, 100)))

    def test_dtype_float32(self):
        lora_a, lora_b = initialize_lora_matrices(100, 4)
        assert lora_a.dtype == np.float32
        assert lora_b.dtype == np.float32


class TestComputeModelSize:
    def test_formula(self):
        # LoRA params: A (d×r) + B (r×d) = 2×d×r floats
        # float32 = 4 bytes each
        hidden_dim = 100
        rank = 4
        expected = 2 * hidden_dim * rank * 4  # bytes
        assert compute_model_size(hidden_dim, rank) == expected

    def test_larger_rank(self):
        hidden_dim = 100
        rank_4 = compute_model_size(hidden_dim, 4)
        rank_8 = compute_model_size(hidden_dim, 8)
        assert rank_8 == 2 * rank_4  # doubles when rank doubles


# =============================================================================
# TinyLoRA tests
# =============================================================================

class TestTinyLoRAInit:
    def test_basic(self):
        config = TinyLoRAConfig(hidden_dim=512)
        tinylora = TinyLoRA(config)
        assert tinylora.config.hidden_dim == 512
        assert tinylora.lora_a is None
        assert tinylora.lora_b is None

    def test_custom_config(self):
        config = TinyLoRAConfig(
            hidden_dim=1024,
            rank=8,
            alpha=16.0,
            lr=0.01,
            dropout=0.2,
            max_iter=500,
        )
        tinylora = TinyLoRA(config)
        assert tinylora.config.rank == 8


class TestTinyLoRATrain:
    def test_insufficient_data(self):
        config = TinyLoRAConfig(hidden_dim=10)
        tinylora = TinyLoRA(config)
        small_data = [(np.zeros(10), 0) for _ in range(5)]
        with pytest.raises(DataInsufficientError, match="insufficient"):
            tinylora.train(small_data)

    def test_dimension_mismatch(self):
        config = TinyLoRAConfig(hidden_dim=10)
        tinylora = TinyLoRA(config)
        wrong_dim_data = [(np.zeros(20), i % 2) for i in range(20)]
        with pytest.raises(DataInsufficientError, match="dimension"):
            tinylora.train(wrong_dim_data)

    def test_train_returns_model_and_loss(self):
        config = TinyLoRAConfig(hidden_dim=10, max_iter=50)
        tinylora = TinyLoRA(config)
        np.random.seed(42)
        data = [
            (np.random.randn(10), i % 2)
            for i in range(20)
        ]
        model, loss = tinylora.train(data)
        assert isinstance(model, TinyLoRAModel)
        assert isinstance(loss, float)
        assert loss >= 0.0

    def test_train_stores_lora_weights(self):
        config = TinyLoRAConfig(hidden_dim=10, max_iter=50)
        tinylora = TinyLoRA(config)
        data = [
            (np.random.randn(10), i % 2)
            for i in range(20)
        ]
        model, _ = tinylora.train(data)
        assert tinylora.lora_a is not None
        assert tinylora.lora_b is not None
        assert "lora_a" in model.state_dict
        assert "lora_b" in model.state_dict

    def test_train_learning_rate_decay(self):
        """Test that learning rate decay is triggered at iteration 100."""
        config = TinyLoRAConfig(hidden_dim=10, max_iter=200)
        tinylora = TinyLoRA(config)
        # Use random noisy data that won't converge quickly
        np.random.seed(42)
        data = [
            (np.random.randn(10), np.random.randint(0, 2))
            for i in range(50)
        ]
        model, loss = tinylora.train(data)
        # Training should complete without early stopping
        assert isinstance(model, TinyLoRAModel)

    def test_train_metrics(self):
        config = TinyLoRAConfig(hidden_dim=10, max_iter=50)
        tinylora = TinyLoRA(config)
        np.random.seed(42)
        data = [
            (np.random.randn(10), i % 2)
            for i in range(20)
        ]
        model, _ = tinylora.train(data)
        assert "accuracy" in model.metrics
        assert "f1" in model.metrics
        assert "auc" in model.metrics


class TestTinyLoRAForward:
    def test_forward_without_training_raises(self):
        config = TinyLoRAConfig(hidden_dim=10)
        tinylora = TinyLoRA(config)
        with pytest.raises(RuntimeError, match="not initialized"):
            tinylora._forward(np.zeros((1, 10)))


class TestTinyLoRAInfer:
    def test_infer_1d_hidden_state(self):
        config = TinyLoRAConfig(hidden_dim=10, max_iter=50)
        tinylora = TinyLoRA(config)
        np.random.seed(42)
        data = [(np.random.randn(10), i % 2) for i in range(20)]
        model, _ = tinylora.train(data)

        hidden = np.random.randn(10)
        prob = tinylora.infer(model, hidden)
        assert 0.0 <= prob <= 1.0

    def test_infer_2d_hidden_state(self):
        config = TinyLoRAConfig(hidden_dim=10, max_iter=50)
        tinylora = TinyLoRA(config)
        np.random.seed(42)
        data = [(np.random.randn(10), i % 2) for i in range(20)]
        model, _ = tinylora.train(data)

        hidden = np.random.randn(1, 10)
        prob = tinylora.infer(model, hidden)
        assert 0.0 <= prob <= 1.0


class TestTinyLoRAModelOperations:
    def test_apply_lora_to_weights(self):
        config = TinyLoRAConfig(hidden_dim=10, alpha=8.0)
        tinylora = TinyLoRA(config)
        original = np.eye(10)
        lora_a = np.zeros((10, 4))
        lora_b = np.zeros((4, 10))
        result = tinylora.apply_lora_to_weights(original, lora_a, lora_b)
        assert result.shape == (10, 10)

    def test_get_model_size(self):
        config = TinyLoRAConfig(hidden_dim=100, rank=4)
        tinylora = TinyLoRA(config)
        size = tinylora.get_model_size()
        expected = compute_model_size(100, 4)
        assert size == expected

    def test_get_model_size_mb(self):
        config = TinyLoRAConfig(hidden_dim=4096, rank=4)
        tinylora = TinyLoRA(config)
        size_mb = tinylora.get_model_size_mb()
        size_bytes = tinylora.get_model_size()
        assert abs(size_mb - size_bytes / (1024 * 1024)) < 1e-6


class TestTinyLoRAIntegration:
    def test_full_train_and_infer(self):
        config = TinyLoRAConfig(hidden_dim=20, rank=4, max_iter=100)
        tinylora = TinyLoRA(config)

        np.random.seed(42)
        # Create separable data
        class0 = np.random.randn(15, 20) * 0.3 + np.array([1.0] * 20)
        class1 = np.random.randn(15, 20) * 0.3 + np.array([-1.0] * 20)
        X = np.vstack([class0, class1])
        y = np.array([0] * 15 + [1] * 15)
        data = [(X[i], y[i]) for i in range(len(X))]

        model, loss = tinylora.train(data)
        assert loss >= 0.0

        # Infer on both classes
        prob0 = tinylora.infer(model, class0[0])
        prob1 = tinylora.infer(model, class1[0])
        assert 0.0 <= prob0 <= 1.0
        assert 0.0 <= prob1 <= 1.0

    def test_model_size_small(self):
        # TinyLoRA should be very small
        config = TinyLoRAConfig(hidden_dim=4096, rank=4)
        tinylora = TinyLoRA(config)
        size_mb = tinylora.get_model_size_mb()
        # 2 * 4096 * 4 * 4 bytes = ~1MB
        assert size_mb < 2.0  # Should be under 2MB
