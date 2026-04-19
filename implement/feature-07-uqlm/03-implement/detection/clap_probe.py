# detection/clap_probe.py
"""FR-U-2: CLAP Activation Probe.

This module implements Contrastive Learning with Activation Probes (CLAP)
for hallucination detection in open-weight models.

Purpose:
    Use activation probes on hidden states to detect hallucination patterns.
    The probe is trained on labeled hidden states to predict hallucination
    probability from the model's internal representations.

Supported Models:
    - llama-3.3, qwen-2.5: Full activation probe support
    - gpt-4, claude-3: Fallback to logprobs + self-consistency

Algorithm:
    1. Extract hidden states from target attention layer
    2. Normalize states (L2 norm)
    3. Apply trained probe: p_hallucinate = probe.predict_proba(states)[:, 1]
    4. Return probability and confidence

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
except ImportError:
    LogisticRegression = None

from detection.data_models import (
    ProbeConfig,
    ProbeResult,
    ProbeType,
    TrainingData,
)
from detection.exceptions import (
    DataInsufficientError,
    ProbeError,
)


# =============================================================================
# Section 1: Activation Probe
# =============================================================================


class ActivationProbe:
    """CLAP Activation Probe for hallucination detection.

    Uses trained probes on hidden states to predict hallucination
    probability. Supports multiple probe types and model architectures.

    Attributes:
        config: Probe configuration
        model: Trained sklearn model (LogisticRegression or similar)
        is_fitted: Whether probe has been trained

    Example:
        >>> config = ProbeConfig(model_type="llama-3.3", layer_idx=-1)
        >>> probe = ActivationProbe(config)
        >>> probe.fit(training_data)
        >>> result = probe.predict(hidden_states)
        >>> print(result.p_hallucinate)
        0.23
    """

    # Supported model types for activation probes
    SUPPORTED_OPEN_WEIGHT_MODELS = {"llama-3.3", "qwen-2.5", "llama-2", "mistral"}

    # Models that require fallback to logprobs
    CLOSED_SOURCE_MODELS = {"gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2"}

    def __init__(
        self,
        config: ProbeConfig,
    ) -> None:
        """Initialize ActivationProbe with configuration.

        Args:
            config: ProbeConfig with model_type, layer_idx, probe_type, threshold

        Raises:
            ProbeError: If model type is not supported
        """
        self.config = config
        self.model: Optional[LogisticRegression] = None
        self.is_fitted = False

        # Validate model type
        if config.model_type not in self.SUPPORTED_OPEN_WEIGHT_MODELS:
            if config.model_type not in self.CLOSED_SOURCE_MODELS:
                raise ProbeError(
                    message=f"Unsupported model type: {config.model_type}",
                    model_type=config.model_type,
                    probe_type=config.probe_type.value,
                )

    def fit(
        self,
        training_data: TrainingData,
    ) -> ProbeResult:
        """Train the activation probe on labeled hidden states.

        Args:
            training_data: List of (hidden_state, label) tuples where
                          label is 0 for real content and 1 for hallucination

        Returns:
            ProbeResult with training metrics

        Raises:
            DataInsufficientError: If training data < 10 samples
            ProbeError: If training fails
        """
        if len(training_data) < 10:
            raise DataInsufficientError(
                message="Training data insufficient for probe training",
                provided_count=len(training_data),
                required_count=10,
                data_type="training",
            )

        # Check sklearn availability
        if LogisticRegression is None:
            raise ProbeError(
                message="sklearn is required for CLAP probe but is not installed",
                model_type=self.config.model_type,
            )

        # Check label distribution
        labels = [label for _, label in training_data]
        unique_labels = set(labels)
        if len(unique_labels) < 2:
            raise DataInsufficientError(
                message="Training data must contain both classes",
                provided_count=len(training_data),
                required_count=2,
                data_type="label_variation",
            )

        # Unpack training data
        X = np.array([hs for hs, _ in training_data])
        y = np.array([label for _, label in training_data])

        # Validate dimensions
        if X.ndim != 2:
            raise DataInsufficientError(
                message="Hidden states must be 2D arrays",
                provided_count=X.ndim,
                required_count=2,
                data_type="hidden_state_dimensions",
            )

        # Initialize model based on probe type
        if self.config.probe_type == ProbeType.LOGISTIC_REGRESSION:
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                solver="lbfgs",
            )
        elif self.config.probe_type == ProbeType.LINEAR:
            # Linear probe via LogisticRegression with no regularization
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                solver="lbfgs",
                C=1e10,  # Very weak regularization
            )
        else:
            raise ProbeError(
                message=f"Probe type {self.config.probe_type} not implemented",
                probe_type=self.config.probe_type.value,
            )

        # Train model
        try:
            self.model.fit(X, y)
            self.is_fitted = True
        except Exception as e:
            raise ProbeError(
                message=f"Probe training failed: {e}",
                model_type=self.config.model_type,
                probe_type=self.config.probe_type.value,
            )

        # Compute training metrics
        train_accuracy = self.model.score(X, y)

        # Predict on training set for additional metrics
        y_pred = self.model.predict(X)
        y_prob = self.model.predict_proba(X)

        # Compute F1 and AUC if possible
        metrics: Dict[str, float] = {"accuracy": train_accuracy}

        try:
            from sklearn.metrics import f1_score, roc_auc_score

            f1 = f1_score(y, y_pred, zero_division=0)
            metrics["f1"] = f1

            if len(unique_labels) == 2:
                auc = roc_auc_score(y, y_prob[:, 1])
                metrics["auc"] = auc
        except ImportError:
            pass

        return ProbeResult(
            p_hallucinate=float(np.mean(y_prob[:, 1])),
            confidence=float(np.mean(np.max(y_prob, axis=1))),
            layer_used=self.config.layer_idx,
            model_type=self.config.model_type,
            metadata={"training_samples": len(training_data), **metrics},
        )

    def predict(
        self,
        hidden_states: np.ndarray,
    ) -> ProbeResult:
        """Predict hallucination probability from hidden states.

        Args:
            hidden_states: Hidden states array (shape: [batch, hidden_dim])
                         or (shape: [hidden_dim]) for single sample

        Returns:
            ProbeResult with p_hallucinate, confidence, and layer_used

        Raises:
            ProbeError: If probe not trained or prediction fails
        """
        if not self.is_fitted or self.model is None:
            raise ProbeError(
                message="Probe must be trained before prediction",
                model_type=self.config.model_type,
                probe_type=self.config.probe_type.value,
            )

        # Handle single sample (1D array)
        if hidden_states.ndim == 1:
            hidden_states = hidden_states.reshape(1, -1)

        # Validate dimensions
        if hidden_states.ndim != 2:
            raise ProbeError(
                message=f"Hidden states must be 2D, got {hidden_states.ndim}D",
                model_type=self.config.model_type,
            )

        # Normalize hidden states (L2 norm)
        norms = np.linalg.norm(hidden_states, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normalized_states = hidden_states / norms

        try:
            # Predict probabilities
            proba = self.model.predict_proba(normalized_states)
            predictions = self.model.predict(normalized_states)

            # Extract hallucination probability (class 1)
            p_hallucinate = float(proba[0, 1]) if len(proba) == 1 else float(np.mean(proba[:, 1]))
            confidence = float(np.mean(np.max(proba, axis=1)))

            return ProbeResult(
                p_hallucinate=p_hallucinate,
                confidence=confidence,
                layer_used=self.config.layer_idx,
                model_type=self.config.model_type,
                metadata={
                    "normalized": True,
                    "sample_count": len(hidden_states),
                },
            )

        except Exception as e:
            raise ProbeError(
                message=f"Prediction failed: {e}",
                model_type=self.config.model_type,
            )

    def predict_from_layer(
        self,
        model_output: Any,
        layer_idx: Optional[int] = None,
    ) -> ProbeResult:
        """Extract hidden states from model output and predict.

        Args:
            model_output: Raw model output (depends on model type)
            layer_idx: Override layer index (uses config default if None)

        Returns:
            ProbeResult with prediction

        Raises:
            ProbeError: If hidden state extraction fails
        """
        layer_idx = layer_idx if layer_idx is not None else self.config.layer_idx

        try:
            # Extract hidden states based on model type
            if self.config.model_type in {"llama-3.3", "llama-2", "mistral"}:
                hidden_states = self._extract_from_huggingface(model_output, layer_idx)
            elif self.config.model_type == "qwen-2.5":
                hidden_states = self._extract_from_qwen(model_output, layer_idx)
            else:
                raise ProbeError(
                    message=f"Hidden state extraction not implemented for {self.config.model_type}",
                    model_type=self.config.model_type,
                )

            return self.predict(hidden_states)

        except Exception as e:
            raise ProbeError(
                message=f"Hidden state extraction failed: {e}",
                model_type=self.config.model_type,
                layer_idx=layer_idx,
            )

    def _extract_from_huggingface(
        self,
        model_output: Any,
        layer_idx: int,
    ) -> np.ndarray:
        """Extract hidden states from HuggingFace model output.

        Args:
            model_output: HuggingFace model output object
            layer_idx: Layer index to extract

        Returns:
            Hidden states as numpy array
        """
        # Handle different output formats
        if hasattr(model_output, "hidden_states"):
            # Return hidden states tuple/list
            hidden_states_list = model_output.hidden_states
            if layer_idx == -1:
                layer_idx = len(hidden_states_list) - 1
            return hidden_states_list[layer_idx].numpy()
        elif hasattr(model_output, "last_hidden_state"):
            # Direct hidden states
            return model_output.last_hidden_state.numpy()
        else:
            raise ProbeError(
                message="Model output does not contain hidden states",
                model_type=self.config.model_type,
            )

    def _extract_from_qwen(
        self,
        model_output: Any,
        layer_idx: int,
    ) -> np.ndarray:
        """Extract hidden states from Qwen model output.

        Args:
            model_output: Qwen model output object
            layer_idx: Layer index to extract

        Returns:
            Hidden states as numpy array
        """
        # Qwen uses similar structure to HuggingFace
        return self._extract_from_huggingface(model_output, layer_idx)

    def save(
        self,
        path: str,
    ) -> None:
        """Save trained probe to disk.

        Args:
            path: File path to save probe

        Raises:
            ProbeError: If probe not trained or save fails
        """
        if not self.is_fitted:
            raise ProbeError(
                message="Cannot save untrained probe",
                model_type=self.config.model_type,
            )

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(path, "wb") as f:
                pickle.dump(
                    {
                        "model": self.model,
                        "config": self.config,
                        "is_fitted": self.is_fitted,
                    },
                    f,
                )
        except Exception as e:
            raise ProbeError(
                message=f"Failed to save probe: {e}",
                model_type=self.config.model_type,
            )

    @classmethod
    def load(
        cls,
        path: str,
    ) -> "ActivationProbe":
        """Load trained probe from disk.

        Args:
            path: File path to load probe from

        Returns:
            Loaded ActivationProbe instance

        Raises:
            ProbeError: If load fails
        """
        path = Path(path)
        if not path.exists():
            raise ProbeError(
                message=f"Probe file not found: {path}",
            )

        try:
            with open(path, "rb") as f:
                data = pickle.load(f)

            probe = cls(data["config"])
            probe.model = data["model"]
            probe.is_fitted = data["is_fitted"]
            return probe

        except Exception as e:
            raise ProbeError(
                message=f"Failed to load probe: {e}",
            )

    def get_config(self) -> ProbeConfig:
        """Get current probe configuration.

        Returns:
            Copy of current ProbeConfig
        """
        return ProbeConfig(
            model_type=self.config.model_type,
            layer_idx=self.config.layer_idx,
            probe_type=self.config.probe_type,
            threshold=self.config.threshold,
        )

    def is_trained(self) -> bool:
        """Check if probe has been trained.

        Returns:
            True if probe is trained and ready for prediction
        """
        return self.is_fitted and self.model is not None
