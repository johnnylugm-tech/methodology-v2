"""Tests for detection/metaqa.py."""
import pytest

import numpy as np

from detection.data_models import DriftScore, MetaQAResult, TokenDistribution
from detection.exceptions import BaselineNotFoundError
from detection.metaqa import (
    MetaQADetector,
    kl_divergence,
    sigmoid_scale,
    tokenize,
    compute_token_distribution,
)


class TestTokenize:
    def test_basic(self):
        tokens = tokenize("hello world")
        assert tokens == ["hello", "world"]

    def test_lowercase(self):
        tokens = tokenize("Hello World")
        assert tokens == ["hello", "world"]

    def test_empty_string(self):
        assert tokenize("") == []

    def test_whitespace_only(self):
        assert tokenize("   \n\t  ") == []


class TestComputeTokenDistribution:
    def test_empty_list(self):
        dist = compute_token_distribution([])
        assert dist.tokens == []
        assert dist.probabilities == []

    def test_single_text(self):
        dist = compute_token_distribution(["hello hello world"])
        assert "hello" in dist.tokens
        assert "world" in dist.tokens
        # hello appears twice -> 2/3, world appears once -> 1/3
        probs = dict(zip(dist.tokens, dist.probabilities))
        assert abs(probs["hello"] - 2/3) < 1e-6
        assert abs(probs["world"] - 1/3) < 1e-6

    def test_multiple_texts(self):
        dist = compute_token_distribution(["a b", "b c"])
        # a:1, b:2, c:1 -> total 4
        probs = dict(zip(dist.tokens, dist.probabilities))
        assert abs(probs["a"] - 0.25) < 1e-6
        assert abs(probs["b"] - 0.5) < 1e-6
        assert abs(probs["c"] - 0.25) < 1e-6


class TestKLDivergence:
    def test_identical_distributions(self):
        p = TokenDistribution(tokens=["a", "b"], probabilities=[0.5, 0.5], version="")
        q = TokenDistribution(tokens=["a", "b"], probabilities=[0.5, 0.5], version="")
        kl = kl_divergence(p, q)
        assert abs(kl) < 1e-6

    def test_different_distributions(self):
        p = TokenDistribution(tokens=["a", "b"], probabilities=[0.9, 0.1], version="")
        q = TokenDistribution(tokens=["a", "b"], probabilities=[0.1, 0.9], version="")
        kl = kl_divergence(p, q)
        assert kl > 0

    def test_missing_token_in_q(self):
        p = TokenDistribution(tokens=["a", "b"], probabilities=[0.5, 0.5], version="")
        q = TokenDistribution(tokens=["a"], probabilities=[1.0], version="")
        # b is missing from q, should use smoothing
        kl = kl_divergence(p, q)
        assert kl >= 0


class TestSigmoidScale:
    def test_zero(self):
        assert abs(sigmoid_scale(0.0, k=1.0, x0=0.0) - 0.5) < 1e-6

    def test_positive_large(self):
        # sigmoid(10) ~ 1
        assert sigmoid_scale(10.0, k=1.0, x0=0.0) > 0.99

    def test_negative_large(self):
        # sigmoid(-10) ~ 0
        assert sigmoid_scale(-10.0, k=1.0, x0=0.0) < 0.01

    def test_custom_k(self):
        # Higher k = steeper curve
        s1 = sigmoid_scale(0.0, k=0.5, x0=0.0)
        s2 = sigmoid_scale(0.0, k=2.0, x0=0.0)
        assert s1 == s2 == 0.5  # midpoint always 0.5

    def test_custom_x0(self):
        s1 = sigmoid_scale(1.0, k=1.0, x0=0.0)
        s2 = sigmoid_scale(1.0, k=1.0, x0=1.0)
        assert abs(s1 - 0.5) < abs(s2 - 0.5)


class TestMetaQADetectorInit:
    def test_default(self):
        detector = MetaQADetector()
        assert detector.baseline is None
        assert detector.baseline_version == ""
        assert detector.window_size == 100

    def test_custom_window_size(self):
        detector = MetaQADetector(window_size=50)
        assert detector.window_size == 50

    def test_with_baseline(self):
        baseline = {"the": 0.4, "a": 0.3, "to": 0.2, "of": 0.1}
        detector = MetaQADetector(baseline=baseline)
        assert detector.baseline is not None
        assert detector.baseline_version != ""


class TestMetaQADetectorSetBaseline:
    def test_set_baseline_from_dict(self):
        detector = MetaQADetector()
        baseline = {"word1": 0.6, "word2": 0.4}
        detector._set_baseline_from_dict(baseline)
        assert detector.baseline is not None
        assert detector.baseline_version != ""


class TestMetaQADetectorUpdateBaseline:
    def test_update_baseline_empty(self):
        detector = MetaQADetector()
        detector.update_baseline([])
        # No baseline set yet
        assert detector.baseline is None

    def test_update_baseline_first_time(self):
        detector = MetaQADetector()
        detector.update_baseline(["hello world", "hello there"])
        assert detector.baseline is not None
        assert len(detector.baseline.tokens) > 0

    def test_update_baseline_merges(self):
        detector = MetaQADetector()
        detector.update_baseline(["word1 word2 word3"])
        baseline1 = dict(zip(detector.baseline.tokens, detector.baseline.probabilities))
        detector.update_baseline(["word2 word3 word4"])
        baseline2 = dict(zip(detector.baseline.tokens, detector.baseline.probabilities))
        # word1 should still be there with reduced probability
        assert "word1" in baseline2


class TestMetaQADetectorDetectDrift:
    def test_no_baseline_initializes_baseline(self):
        detector = MetaQADetector()
        result = detector.detect_drift(["hello world"])
        assert result.drift_score == 0.0
        assert detector.baseline is not None

    def test_no_outputs(self):
        detector = MetaQADetector(baseline={"a": 0.5, "b": 0.5})
        result = detector.detect_drift([])
        assert result.drift_score == 0.0
        assert result.drifted_tokens == []

    def test_drift_detected(self):
        detector = MetaQADetector()
        # Set baseline
        detector.update_baseline(["the cat sat on the mat"])
        # New distribution slightly different
        result = detector.detect_drift(["the dog ran in the park"])
        assert 0.0 <= result.drift_score <= 1.0

    def test_custom_window_size(self):
        detector = MetaQADetector(window_size=10)
        detector.update_baseline(["word"] * 20)
        result = detector.detect_drift(["word"] * 5, window_size=5)
        assert result.window_size == 5

    def test_drift_history_recorded(self):
        detector = MetaQADetector()
        detector.update_baseline(["baseline text"])
        initial_len = len(detector.drift_history)

        detector.detect_drift(["new text"])
        assert len(detector.drift_history) == initial_len + 1

    def test_drift_history_limit(self):
        detector = MetaQADetector()
        detector.update_baseline(["baseline"])
        # Add many drift detections
        for i in range(1050):
            detector.detect_drift([f"text {i}"])
        # Should be capped at 1000
        assert len(detector.drift_history) <= 1000


class TestMetaQADetectorFindDriftedTokens:
    def test_no_common_tokens(self):
        detector = MetaQADetector()
        baseline = TokenDistribution(tokens=["x", "y"], probabilities=[0.5, 0.5], version="")
        current = TokenDistribution(tokens=["a", "b"], probabilities=[0.5, 0.5], version="")
        drifted = detector._find_drifted_tokens(baseline, current)
        assert drifted == []

    def test_tokens_within_threshold(self):
        detector = MetaQADetector()
        # Same distribution
        dist = TokenDistribution(
            tokens=["a", "b", "c"],
            probabilities=[0.33, 0.33, 0.34],
            version="",
        )
        drifted = detector._find_drifted_tokens(dist, dist)
        assert drifted == []


class TestMetaQADetectorGetters:
    def test_get_drift_history_empty(self):
        detector = MetaQADetector()
        assert detector.get_drift_history() == []

    def test_get_drift_history_with_limit(self):
        detector = MetaQADetector()
        detector.update_baseline(["baseline"])
        for i in range(20):
            detector.detect_drift([f"text {i}"])
        history = detector.get_drift_history()
        assert len(history) == 20
        limited = detector.get_drift_history(limit=5)
        assert len(limited) == 5

    def test_clear_baseline(self):
        detector = MetaQADetector()
        detector.update_baseline(["text"])
        assert detector.baseline is not None
        detector.clear_baseline()
        assert detector.baseline is None
        assert detector.baseline_version == ""

    def test_get_baseline_none(self):
        detector = MetaQADetector()
        assert detector.get_baseline() is None

    def test_get_baseline_dict(self):
        detector = MetaQADetector()
        detector.update_baseline(["hello world"])
        baseline = detector.get_baseline()
        assert isinstance(baseline, dict)
        assert len(baseline) > 0
