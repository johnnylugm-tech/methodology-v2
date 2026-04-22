"""Tests for detection/data_models.py."""
import pytest
from datetime import datetime

import numpy as np

from detection.data_models import (
    CalibrationConfig,
    CalibrationResult,
    DriftScore,
    EnsembleConfig,
    EnsembleResult,
    GapFinding,
    GapSummary,
    GapType,
    HiddenStateBatch,
    MetaQAResult,
    ProbeConfig,
    ProbeResult,
    ProbeType,
    ScorerResult,
    TokenDistribution,
    TrainingSample,
    TrainingData,
    TinyLoRAConfig,
    TinyLoRAModel,
    UncertaintyScore,
)


# =============================================================================
# Enum tests already covered in test_enums.py
# =============================================================================


class TestEnsembleConfig:
    def test_default_values(self):
        cfg = EnsembleConfig()
        assert cfg.weights == [0.4, 0.3, 0.3]
        assert cfg.scorers == ["semantic_entropy", "semantic_density", "self_consistency"]
        assert cfg.n_samples == 5
        assert cfg.temperature == 0.7
        assert cfg.model_name == "gpt-3.5-turbo"

    def test_valid_config(self):
        cfg = EnsembleConfig(
            weights=[0.5, 0.3, 0.2],
            scorers=["a", "b", "c"],
            n_samples=10,
            temperature=0.5,
            model_name="gpt-4",
        )
        assert cfg.weights == [0.5, 0.3, 0.2]
        assert cfg.n_samples == 10

    def test_weights_mismatch_scorers_raises(self):
        with pytest.raises(ValueError, match="must match"):
            EnsembleConfig(weights=[0.5, 0.5], scorers=["a", "b", "c"])

    def test_weights_dont_sum_to_one_raises(self):
        with pytest.raises(ValueError, match="must sum to 1.0"):
            EnsembleConfig(weights=[0.1, 0.2, 0.3], scorers=["a", "b", "c"])

    def test_weights_close_to_one_is_valid(self):
        cfg = EnsembleConfig(weights=[0.333333, 0.333334, 0.333333], scorers=["a", "b", "c"])
        assert abs(sum(cfg.weights) - 1.0) < 1e-6


class TestScorerResult:
    def test_basic(self):
        result = ScorerResult(
            scorer_name="se",
            raw_score=0.5,
            normalized_score=0.5,
        )
        assert result.scorer_name == "se"
        assert result.raw_score == 0.5
        assert result.normalized_score == 0.5
        assert result.metadata == {}

    def test_with_metadata(self):
        result = ScorerResult(
            scorer_name="se",
            raw_score=0.5,
            normalized_score=0.5,
            metadata={"latency_ms": 100},
        )
        assert result.metadata["latency_ms"] == 100


class TestEnsembleResult:
    def test_basic(self):
        result = EnsembleResult(
            uaf_score=0.3,
            scorer_results=[],
            computation_time_ms=10.5,
            model_used="gpt-4",
            n_samples=5,
        )
        assert result.uaf_score == 0.3
        assert result.computation_time_ms == 10.5
        assert result.model_used == "gpt-4"
        assert result.n_samples == 5


class TestProbeConfig:
    def test_defaults(self):
        cfg = ProbeConfig(model_type="llama-3.3")
        assert cfg.model_type == "llama-3.3"
        assert cfg.layer_idx == -1
        assert cfg.probe_type == ProbeType.LOGISTIC_REGRESSION
        assert cfg.threshold == 0.5

    def test_full(self):
        cfg = ProbeConfig(
            model_type="gpt-4",
            layer_idx=10,
            probe_type=ProbeType.MLP,
            threshold=0.7,
        )
        assert cfg.layer_idx == 10
        assert cfg.probe_type == ProbeType.MLP


class TestProbeResult:
    def test_basic(self):
        result = ProbeResult(
            p_hallucinate=0.25,
            confidence=0.85,
            layer_used=-1,
            model_type="llama-3.3",
        )
        assert result.p_hallucinate == 0.25
        assert result.confidence == 0.85
        assert result.layer_used == -1
        assert result.metadata == {}

    def test_with_metadata(self):
        result = ProbeResult(
            p_hallucinate=0.1,
            confidence=0.9,
            layer_used=5,
            model_type="llama-3.3",
            metadata={"normalized": True},
        )
        assert result.metadata["normalized"] is True


class TestTinyLoRAConfig:
    def test_required_hidden_dim(self):
        cfg = TinyLoRAConfig(hidden_dim=4096)
        assert cfg.hidden_dim == 4096
        assert cfg.rank == 4
        assert cfg.alpha == 8.0
        assert cfg.lr == 0.001
        assert cfg.dropout == 0.1
        assert cfg.max_iter == 1000

    def test_custom_values(self):
        cfg = TinyLoRAConfig(
            hidden_dim=2048,
            rank=8,
            alpha=16.0,
            lr=0.01,
            dropout=0.2,
            max_iter=500,
        )
        assert cfg.rank == 8
        assert cfg.alpha == 16.0
        assert cfg.lr == 0.01


class TestTinyLoRAModel:
    def test_basic(self):
        cfg = TinyLoRAConfig(hidden_dim=4096)
        model = TinyLoRAModel(
            config=cfg,
            state_dict={"lora_a": np.zeros((4096, 4)), "lora_b": np.zeros((4, 4096))},
            training_loss=0.05,
            metrics={"accuracy": 0.9, "f1": 0.85},
        )
        assert model.config.hidden_dim == 4096
        assert model.training_loss == 0.05
        assert model.metrics["accuracy"] == 0.9


class TestMetaQAResult:
    def test_basic(self):
        result = MetaQAResult(
            drift_score=0.35,
            drifted_tokens=["token1", "token2"],
            kl_divergence=1.2,
            window_size=100,
            baseline_version="v1.0",
        )
        assert result.drift_score == 0.35
        assert result.drifted_tokens == ["token1", "token2"]
        assert result.kl_divergence == 1.2
        assert result.window_size == 100


class TestDriftScore:
    def test_basic(self):
        ts = datetime.now()
        result = DriftScore(
            score=0.4,
            timestamp=ts,
            tokens=["a", "b"],
            kl_div=0.8,
        )
        assert result.score == 0.4
        assert result.timestamp == ts
        assert result.kl_div == 0.8


class TestGapFinding:
    def test_basic(self):
        finding = GapFinding(
            gap_type=GapType.HARDCODED_SECRETS,
            file_path="/path/file.py",
            line_number=42,
            severity="CRITICAL",
            description="Hardcoded secret found",
        )
        assert finding.gap_type == GapType.HARDCODED_SECRETS
        assert finding.file_path == "/path/file.py"
        assert finding.line_number == 42
        assert finding.severity == "CRITICAL"
        assert finding.code_snippet == ""
        assert finding.suggestion == ""

    def test_full(self):
        finding = GapFinding(
            gap_type=GapType.EMPTY_CATCH,
            file_path="test.py",
            line_number=10,
            severity="HIGH",
            description="Empty catch",
            code_snippet="except: pass",
            suggestion="Add logging",
        )
        assert finding.code_snippet == "except: pass"
        assert finding.suggestion == "Add logging"


class TestGapSummary:
    def test_basic(self):
        summary = GapSummary(
            total_files=5,
            total_findings=3,
            by_type={GapType.EMPTY_CATCH: 2, GapType.HARDCODED_SECRETS: 1},
            by_severity={"HIGH": 2, "CRITICAL": 1},
            findings=[],
        )
        assert summary.total_files == 5
        assert summary.total_findings == 3
        assert summary.by_type[GapType.EMPTY_CATCH] == 2


class TestUncertaintyScore:
    def test_basic(self):
        score = UncertaintyScore(
            score=0.3,
            decision="PASS",
            components={"uqlm": 0.3, "clap": 0.2},
            alpha=0.5,
            beta=0.3,
            gamma=0.2,
            computation_time_ms=15.0,
        )
        assert score.score == 0.3
        assert score.decision == "PASS"
        assert score.components["uqlm"] == 0.3
        assert score.alpha == 0.5
        assert score.beta == 0.3

    def test_with_metadata(self):
        score = UncertaintyScore(
            score=0.5,
            decision="ROUND_2",
            components={},
            alpha=0.5,
            beta=0.3,
            gamma=0.2,
            computation_time_ms=10.0,
            metadata={"model_name": "gpt-4"},
        )
        assert score.metadata["model_name"] == "gpt-4"


class TestCalibrationConfig:
    def test_defaults(self):
        cfg = CalibrationConfig()
        assert cfg.history_size == 100
        assert cfg.alert_threshold == 0.3

    def test_custom(self):
        cfg = CalibrationConfig(history_size=50, alert_threshold=0.2)
        assert cfg.history_size == 50
        assert cfg.alert_threshold == 0.2


class TestCalibrationResult:
    def test_basic(self):
        ts = datetime.now()
        result = CalibrationResult(
            initial_confidence=0.8,
            calibrated_confidence=0.75,
            actual_outcome=True,
            calibration_error=0.25,
            alert=False,
            timestamp=ts,
        )
        assert result.initial_confidence == 0.8
        assert result.calibrated_confidence == 0.75
        assert result.actual_outcome is True
        assert result.calibration_error == 0.25
        assert result.alert is False


class TestTokenDistribution:
    def test_basic(self):
        dist = TokenDistribution(
            tokens=["a", "b", "c"],
            probabilities=[0.5, 0.3, 0.2],
            version="v1",
        )
        assert dist.tokens == ["a", "b", "c"]
        assert dist.probabilities == [0.5, 0.3, 0.2]
        assert dist.version == "v1"

    def test_empty(self):
        dist = TokenDistribution(tokens=[], probabilities=[], version="")
        assert dist.tokens == []


class TestHiddenStateBatch:
    def test_basic(self):
        states = np.random.randn(4, 512)
        batch = HiddenStateBatch(
            states=states,
            layer_idx=-1,
            model_type="llama-3.3",
        )
        assert batch.states.shape == (4, 512)
        assert batch.layer_idx == -1
        assert batch.model_type == "llama-3.3"


class TestTrainingSample:
    def test_basic(self):
        hs = np.random.randn(512)
        sample = TrainingSample(hidden_state=hs, label=1)
        assert sample.hidden_state.shape == (512,)
        assert sample.label == 1

    def test_label_values(self):
        sample0 = TrainingSample(hidden_state=np.zeros(10), label=0)
        sample1 = TrainingSample(hidden_state=np.zeros(10), label=1)
        assert sample0.label == 0
        assert sample1.label == 1


class TestTypeAliases:
    def test_training_data_type(self):
        # TrainingData = List[Tuple[np.ndarray, int]]
        data: TrainingData = [(np.zeros(10), 0), (np.ones(10), 1)]
        assert len(data) == 2
        assert data[0][1] == 0
        assert data[1][1] == 1
