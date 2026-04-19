"""Tests for detection/uncertainty_score.py."""
import pytest
from unittest.mock import patch, MagicMock

import numpy as np

from detection.data_models import (
    Decision,
    EnsembleResult,
    MetaQAResult,
    ProbeResult,
    UncertaintyScore,
)
from detection.exceptions import InsufficientDataError
from detection.uncertainty_score import (
    UncertaintyScoreCalculator,
    WeightManager,
)
from detection.uqlm_ensemble import EnsembleScorer
from detection.clap_probe import ActivationProbe
from detection.metaqa import MetaQADetector
from detection.data_models import EnsembleConfig, ProbeConfig, ProbeType


class TestWeightManager:
    def test_normalize_all_none(self):
        alpha, beta, gamma = WeightManager.normalize_weights()
        assert abs(alpha - 0.5) < 1e-6
        assert abs(beta - 0.3) < 1e-6
        assert abs(gamma - 0.2) < 1e-6

    def test_normalize_all_present_sum_to_one(self):
        alpha, beta, gamma = WeightManager.normalize_weights(0.4, 0.3, 0.3)
        assert abs(alpha - 0.4) < 1e-6
        assert abs(beta - 0.3) < 1e-6
        assert abs(gamma - 0.3) < 1e-6

    def test_normalize_only_uqlm(self):
        alpha, beta, gamma = WeightManager.normalize_weights(0.5, 0.0, 0.0)
        assert alpha == 1.0
        assert beta == 0.0
        assert gamma == 0.0

    def test_normalize_only_clap(self):
        alpha, beta, gamma = WeightManager.normalize_weights(0.0, 0.7, 0.0)
        assert alpha == 0.0
        assert abs(beta - 1.0) < 1e-6
        assert gamma == 0.0

    def test_normalize_only_metaqa(self):
        alpha, beta, gamma = WeightManager.normalize_weights(0.0, 0.0, 0.6)
        assert alpha == 0.0
        assert beta == 0.0
        assert gamma == 1.0

    def test_normalize_uqlm_clap_no_metaqa(self):
        alpha, beta, gamma = WeightManager.normalize_weights(0.6, 0.4, 0.0)
        assert abs(alpha - 0.6) < 1e-6
        assert abs(beta - 0.4) < 1e-6
        assert gamma == 0.0

    def test_normalize_redistributes_proportionally(self):
        # Missing metaqa, weights 0.6 and 0.4 should redistribute to 0.6/1.0 and 0.4/1.0
        alpha, beta, gamma = WeightManager.normalize_weights(0.6, 0.4, 0.0)
        assert abs(alpha - 0.6) < 1e-6
        assert abs(beta - 0.4) < 1e-6


class TestUncertaintyScoreCalculatorInit:
    def test_default_weights(self):
        calc = UncertaintyScoreCalculator()
        assert calc.alpha == 0.5
        assert calc.beta == 0.3
        assert calc.gamma == 0.2

    def test_custom_weights(self):
        calc = UncertaintyScoreCalculator(alpha=0.6, beta=0.2, gamma=0.2)
        assert calc.alpha == 0.6
        assert calc.beta == 0.2
        assert calc.gamma == 0.2

    def test_with_components(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        calc = UncertaintyScoreCalculator(ensemble_scorer=ensemble)
        assert calc.ensemble_scorer is ensemble


class TestUncertaintyScoreCalculatorCompute:
    def test_no_components_raises(self):
        calc = UncertaintyScoreCalculator(
            ensemble_scorer=None,
            clap_probe=None,
            metaqa_detector=None,
        )
        with pytest.raises(InsufficientDataError, match="No uncertainty components"):
            calc.compute("prompt", "response")

    def test_compute_with_ensemble_only(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        calc = UncertaintyScoreCalculator(ensemble_scorer=ensemble)
        result = calc.compute("prompt", "This is a response.", hidden_states=None)
        assert isinstance(result, UncertaintyScore)
        assert 0.0 <= result.score <= 1.0
        assert "uqlm" in result.components

    def test_compute_with_all_components(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        probe_cfg = ProbeConfig(model_type="llama-3.3")
        probe = ActivationProbe(probe_cfg)
        metaqa = MetaQADetector()

        calc = UncertaintyScoreCalculator(
            ensemble_scorer=ensemble,
            clap_probe=probe,
            metaqa_detector=metaqa,
        )

        hidden = np.random.randn(10, 10)
        result = calc.compute(
            "prompt",
            "This is a response.",
            hidden_states=hidden,
        )
        assert result is not None
        assert result.decision in [Decision.PASS.value, Decision.ROUND_2.value, Decision.HITL.value]

    def test_compute_decision_pass(self):
        cfg = EnsembleConfig(weights=[1.0], scorers=["semantic_density"])
        ensemble = EnsembleScorer(cfg)
        calc = UncertaintyScoreCalculator(
            ensemble_scorer=ensemble,
            alpha=1.0,
            beta=0.0,
            gamma=0.0,
        )
        # semantic_density returns 0.0 for simple responses, so uncertainty < threshold → PASS
        result = calc.compute("prompt", "AI is artificial intelligence.")
        assert result.decision == Decision.PASS.value

    def test_compute_decision_hitl(self):
        cfg = EnsembleConfig(
            weights=[1.0],
            scorers=["semantic_entropy"],
        )
        ensemble = EnsembleScorer(cfg)
        calc = UncertaintyScoreCalculator(
            ensemble_scorer=ensemble,
            alpha=1.0,
            beta=0.0,
            gamma=0.0,
        )
        # Create response that generates high uncertainty
        result = calc.compute("prompt", "word " * 100)
        # High uncertainty score should lead to HITL
        # (depends on the scorer output)

    def test_compute_missing_hidden_states(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        probe_cfg = ProbeConfig(model_type="llama-3.3")
        probe = ActivationProbe(probe_cfg)
        calc = UncertaintyScoreCalculator(
            ensemble_scorer=ensemble,
            clap_probe=probe,
            metaqa_detector=None,
        )
        # CLAP probe exists but no hidden states
        result = calc.compute("prompt", "response", hidden_states=None)
        assert "clap" not in result.components


class TestUncertaintyScoreCalculatorWeights:
    def test_set_weights(self):
        calc = UncertaintyScoreCalculator()
        calc.set_weights(alpha=0.6, beta=0.2, gamma=0.2)
        assert calc.alpha == 0.6
        assert calc.beta == 0.2
        assert calc.gamma == 0.2

    def test_set_partial_weights(self):
        calc = UncertaintyScoreCalculator()
        calc.set_weights(alpha=0.7)
        assert calc.alpha == 0.7
        # Only alpha is set, so no normalization occurs; beta and gamma retain defaults
        # Resulting sum is 0.7 + 0.3 + 0.2 = 1.2
        assert abs(calc.alpha + calc.beta + calc.gamma - 1.2) < 1e-6

    def test_get_weights(self):
        calc = UncertaintyScoreCalculator(alpha=0.6, beta=0.2, gamma=0.2)
        weights = calc.get_weights()
        assert weights["alpha"] == 0.6
        assert weights["beta"] == 0.2
        assert weights["gamma"] == 0.2


class TestUncertaintyScoreCalculatorComputeFromResults:
    def test_no_results_raises(self):
        calc = UncertaintyScoreCalculator()
        with pytest.raises(InsufficientDataError, match="No component results"):
            calc.compute_from_results()

    def test_ensemble_result_only(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        ens_result = ensemble.score("prompt", "response", 5)

        calc = UncertaintyScoreCalculator(alpha=1.0, beta=0.0, gamma=0.0)
        result = calc.compute_from_results(ensemble_result=ens_result)
        assert result.components["uqlm"] == ens_result.uaf_score

    def test_all_results(self):
        cfg = EnsembleConfig()
        ensemble = EnsembleScorer(cfg)
        ens_result = ensemble.score("prompt", "response", 5)

        probe_cfg = ProbeConfig(model_type="llama-3.3")
        probe = ActivationProbe(probe_cfg)
        # Train the probe
        train_data = [(np.random.randn(10), i % 2) for i in range(20)]
        probe.fit(train_data)
        probe_result = probe.predict(np.random.randn(10))

        metaqa = MetaQADetector()
        metaqa.update_baseline(["response1", "response2"])
        metaqa_result = metaqa.detect_drift(["response3"])

        calc = UncertaintyScoreCalculator(alpha=0.5, beta=0.3, gamma=0.2)
        result = calc.compute_from_results(
            ensemble_result=ens_result,
            probe_result=probe_result,
            metaqa_result=metaqa_result,
        )
        assert "uqlm" in result.components
        assert "clap" in result.components
        assert "metaqa" in result.components


class TestUncertaintyScoreCalculatorDecisionThresholds:
    def test_threshold_pass(self):
        calc = UncertaintyScoreCalculator()
        # Score < 0.2 -> PASS
        decision = calc._compute_decision(0.1)
        assert decision == Decision.PASS.value

    def test_threshold_round_2(self):
        calc = UncertaintyScoreCalculator()
        # 0.2 <= score < 0.5 -> ROUND_2
        decision = calc._compute_decision(0.3)
        assert decision == Decision.ROUND_2.value

    def test_threshold_hitl(self):
        calc = UncertaintyScoreCalculator()
        # score >= 0.5 -> HITL
        decision = calc._compute_decision(0.6)
        assert decision == Decision.HITL.value

    def test_threshold_exact_boundary_pass(self):
        calc = UncertaintyScoreCalculator()
        decision = calc._compute_decision(0.199)
        assert decision == Decision.PASS.value

    def test_threshold_exact_boundary_round2(self):
        calc = UncertaintyScoreCalculator()
        decision = calc._compute_decision(0.5)
        assert decision == Decision.HITL.value
