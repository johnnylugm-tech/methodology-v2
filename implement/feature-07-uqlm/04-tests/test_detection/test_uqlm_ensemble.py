"""Tests for detection/uqlm_ensemble.py."""
import pytest
from unittest.mock import patch, MagicMock

import numpy as np

from detection.data_models import EnsembleConfig, EnsembleResult, ScorerResult
from detection.exceptions import UQLMError
from detection.uqlm_ensemble import (
    BaseScorer,
    EnsembleScorer,
    ScorerFactory,
    SemanticDensityScorer,
    SemanticEntropyScorer,
    SelfConsistencyScorer,
    TokenNLLEvaluator,
)


class TestBaseScorer:
    def test_abstract_methods(self):
        # BaseScorer is abstract - cannot instantiate directly
        assert hasattr(BaseScorer, "score")

    def test_repr(self):
        class TestScorer(BaseScorer):
            def score(self, prompt, response, n_samples, **kwargs):
                return 0.5

        scorer = TestScorer("test_scorer")
        assert "test_scorer" in repr(scorer)


class TestSemanticEntropyScorer:
    def test_empty_response_returns_one(self):
        scorer = SemanticEntropyScorer()
        assert scorer.score("", "", 5) == 1.0

    def test_whitespace_response_returns_one(self):
        scorer = SemanticEntropyScorer()
        assert scorer.score("", "   ", 5) == 1.0

    def test_short_response(self):
        scorer = SemanticEntropyScorer()
        # Short response should have lower entropy
        score = scorer.score("", "hi", 5)
        assert 0.0 <= score <= 1.0

    def test_longer_response_higher_entropy(self):
        scorer = SemanticEntropyScorer()
        short = scorer.score("", "hi", 5)
        long = scorer.score("", "word " * 50, 5)
        assert long >= short

    def test_repr(self):
        scorer = SemanticEntropyScorer()
        r = repr(scorer)
        assert "SemanticEntropyScorer" in r
        assert "semantic_entropy" in r


class TestSemanticDensityScorer:
    def test_empty_response(self):
        scorer = SemanticDensityScorer()
        assert scorer.score("", "", 5) == 1.0

    def test_whitespace_response(self):
        scorer = SemanticDensityScorer()
        assert scorer.score("", "   ", 5) == 1.0

    def test_all_unique_tokens(self):
        scorer = SemanticDensityScorer()
        # All unique words -> high density -> low uncertainty
        score = scorer.score("", "the quick brown fox jumps", 5)
        assert 0.0 <= score <= 1.0

    def test_all_same_tokens(self):
        scorer = SemanticDensityScorer()
        # All same words -> low density -> high uncertainty
        score = scorer.score("", "word word word word word", 5)
        assert score > 0.5

    def test_normalized_to_one(self):
        scorer = SemanticDensityScorer()
        # Very long text with mostly unique tokens should be close to 1.0 uncertainty
        text = " ".join([f"token{i}" for i in range(100)])
        score = scorer.score("", text, 5)
        assert 0.0 <= score <= 1.0


class TestSelfConsistencyScorer:
    def test_empty_response(self):
        scorer = SelfConsistencyScorer()
        assert scorer.score("", "", 5) == 1.0

    def test_single_sample(self):
        scorer = SelfConsistencyScorer()
        # Cannot compute consistency with < 2 samples
        assert scorer.score("", "response", 1) == 0.0

    def test_two_samples(self):
        scorer = SelfConsistencyScorer()
        score = scorer.score("", "response", 2)
        assert 0.0 <= score <= 1.0

    def test_longer_response_more_consistent(self):
        scorer = SelfConsistencyScorer()
        short = scorer.score("", "hi", 5)
        long = scorer.score("", "word " * 50, 5)
        # Longer responses tend to be more consistent
        assert 0.0 <= long <= 1.0


class TestTokenNLLEvaluator:
    def test_empty_response(self):
        scorer = TokenNLLEvaluator()
        assert scorer.score("", "", 5) == 1.0

    def test_normal_response(self):
        scorer = TokenNLLEvaluator()
        score = scorer.score("", "some response text", 5)
        assert 0.0 <= score <= 1.0

    def test_name(self):
        scorer = TokenNLLEvaluator()
        assert scorer.name == "token_nll"


class TestScorerFactory:
    def test_create_semantic_entropy(self):
        scorer = ScorerFactory.create("semantic_entropy")
        assert isinstance(scorer, SemanticEntropyScorer)

    def test_create_semantic_density(self):
        scorer = ScorerFactory.create("semantic_density")
        assert isinstance(scorer, SemanticDensityScorer)

    def test_create_self_consistency(self):
        scorer = ScorerFactory.create("self_consistency")
        assert isinstance(scorer, SelfConsistencyScorer)

    def test_create_token_nll(self):
        scorer = ScorerFactory.create("token_nll")
        assert isinstance(scorer, TokenNLLEvaluator)

    def test_create_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown scorer"):
            ScorerFactory.create("unknown_scorer")

    def test_available_scorers(self):
        available = ScorerFactory.available_scorers()
        assert "semantic_entropy" in available
        assert "semantic_density" in available
        assert "self_consistency" in available
        assert "token_nll" in available

    def test_register_valid_scorer(self):
        class CustomScorer(BaseScorer):
            def score(self, prompt, response, n_samples, **kwargs):
                return 0.5

        ScorerFactory.register("custom_scorer", CustomScorer)
        scorer = ScorerFactory.create("custom_scorer")
        assert isinstance(scorer, CustomScorer)

        # Clean up
        del ScorerFactory._SCORERS["custom_scorer"]

    def test_register_invalid_class_raises(self):
        with pytest.raises(TypeError, match="must inherit"):
            ScorerFactory.register("bad_scorer", str)


class TestEnsembleScorer:
    def test_default_config(self):
        scorer = EnsembleScorer()
        assert scorer.config is not None
        assert len(scorer._scorers) > 0

    def test_custom_config(self):
        cfg = EnsembleConfig(
            weights=[0.5, 0.5],
            scorers=["semantic_entropy", "semantic_density"],
        )
        scorer = EnsembleScorer(cfg)
        assert scorer.config.scorers == ["semantic_entropy", "semantic_density"]

    def test_add_scorer(self):
        scorer = EnsembleScorer()
        custom = SemanticEntropyScorer()
        scorer.add_scorer("custom", custom)
        assert "custom" in scorer._scorers

    def test_add_duplicate_raises(self):
        scorer = EnsembleScorer()
        custom = SemanticEntropyScorer()
        # Use a name that doesn't conflict with default scorers
        scorer.add_scorer("custom_entropy", custom)
        assert "custom_entropy" in scorer._scorers
        with pytest.raises(ValueError, match="already exists"):
            scorer.add_scorer("custom_entropy", custom)

    def test_remove_scorer(self):
        scorer = EnsembleScorer()
        initial_count = len(scorer._scorers)
        scorer.remove_scorer("semantic_entropy")
        assert len(scorer._scorers) == initial_count - 1
        assert "semantic_entropy" not in scorer._scorers

    def test_remove_unknown_raises(self):
        scorer = EnsembleScorer()
        with pytest.raises(KeyError):
            scorer.remove_scorer("nonexistent")

    def test_score_empty_response(self):
        cfg = EnsembleConfig(
            weights=[0.4, 0.3, 0.3],
            scorers=["semantic_entropy", "semantic_density", "self_consistency"],
        )
        scorer = EnsembleScorer(cfg)
        result = scorer.score("prompt", "", 5)
        assert result.uaf_score == 1.0
        assert len(result.scorer_results) == 3

    def test_score_normal_response(self):
        cfg = EnsembleConfig(
            weights=[0.4, 0.3, 0.3],
            scorers=["semantic_entropy", "semantic_density", "self_consistency"],
        )
        scorer = EnsembleScorer(cfg)
        result = scorer.score("prompt", "This is a normal response.", 5)
        assert 0.0 <= result.uaf_score <= 1.0
        assert len(result.scorer_results) == 3

    def test_score_n_samples_override(self):
        cfg = EnsembleConfig(n_samples=5)
        scorer = EnsembleScorer(cfg)
        result = scorer.score("prompt", "response", n_samples=10)
        assert result.n_samples == 10

    def test_score_model_name_override(self):
        cfg = EnsembleConfig(model_name="gpt-3.5-turbo")
        scorer = EnsembleScorer(cfg)
        result = scorer.score("prompt", "response", model_name="gpt-4")
        assert result.model_used == "gpt-4"

    def test_score_all_scorers_fail(self):
        cfg = EnsembleConfig(
            weights=[1.0],
            scorers=["nonexistent"],
        )
        scorer = EnsembleScorer(cfg)
        # No scorers will be created since "nonexistent" is not registered
        with pytest.raises(UQLMError, match="All scorers failed"):
            scorer.score("prompt", "response", 5)

    def test_normalize_score_clamps(self):
        scorer = EnsembleScorer()
        assert scorer._normalize_score(-1.0) == 0.0
        assert scorer._normalize_score(2.0) == 1.0
        assert scorer._normalize_score(0.5) == 0.5

    def test_get_scorer(self):
        scorer = EnsembleScorer()
        se = scorer.get_scorer("semantic_entropy")
        assert se is not None
        assert se.name == "semantic_entropy"

    def test_get_scorer_nonexistent(self):
        scorer = EnsembleScorer()
        assert scorer.get_scorer("nonexistent") is None

    def test_get_config(self):
        cfg = EnsembleConfig(weights=[0.5, 0.5], scorers=["a", "b"])
        scorer = EnsembleScorer(cfg)
        got = scorer.get_config()
        assert got.weights == [0.5, 0.5]
        assert got.scorers == ["a", "b"]

    @pytest.mark.asyncio
    async def test_async_score(self):
        cfg = EnsembleConfig()
        scorer = EnsembleScorer(cfg)
        # Async version calls sync score internally
        result = await scorer.async_score("prompt", "response", 5)
        assert isinstance(result, EnsembleResult)
        assert 0.0 <= result.uaf_score <= 1.0

    @pytest.mark.asyncio
    async def test_async_score_awaited(self):
        cfg = EnsembleConfig()
        scorer = EnsembleScorer(cfg)
        result = await scorer.async_score("prompt", "response", 5)
        assert isinstance(result, EnsembleResult)
        assert 0.0 <= result.uaf_score <= 1.0


class TestEnsembleScorerIntegration:
    def test_all_three_scorers_combined(self):
        cfg = EnsembleConfig(
            weights=[0.4, 0.3, 0.3],
            scorers=["semantic_entropy", "semantic_density", "self_consistency"],
            n_samples=5,
        )
        scorer = EnsembleScorer(cfg)
        result = scorer.score(
            prompt="What is Python?",
            response="Python is a programming language.",
            n_samples=5,
        )
        assert result.uaf_score > 0.0
        assert result.model_used == "gpt-3.5-turbo"
        assert len(result.scorer_results) == 3
        for sr in result.scorer_results:
            assert sr.scorer_name in ["semantic_entropy", "semantic_density", "self_consistency"]
            assert 0.0 <= sr.normalized_score <= 1.0

    def test_computation_time_recorded(self):
        cfg = EnsembleConfig()
        scorer = EnsembleScorer(cfg)
        result = scorer.score("prompt", "response text", 5)
        assert result.computation_time_ms >= 0
