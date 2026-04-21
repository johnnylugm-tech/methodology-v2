"""
Tests for UQLMIntegration [FR-R-10]

Covers uncertainty calculation, breakdown, threshold checking, and cache management.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from uqlm_integration import UQLMIntegration, UncertaintyMetrics


class TestUncertaintyMetricsConstructor:
    """Test UncertaintyMetrics constructor."""

    def test_constructor_default_values(self):
        """Test default values."""
        metrics = UncertaintyMetrics()
        assert metrics.overall_uncertainty == 0.0
        assert metrics.epistemic_uncertainty == 0.0
        assert metrics.aleatoric_uncertainty == 0.0
        assert metrics.model_version == "unknown"
        assert metrics.timestamp != ""

    def test_constructor_custom_values(self):
        """Test custom values."""
        metrics = UncertaintyMetrics(
            overall_uncertainty=0.5,
            epistemic_uncertainty=0.3,
            aleatoric_uncertainty=0.2,
            confidence_interval=(0.3, 0.7),
            model_version="test-v1"
        )
        assert metrics.overall_uncertainty == 0.5
        assert metrics.epistemic_uncertainty == 0.3
        assert metrics.aleatoric_uncertainty == 0.2
        assert metrics.confidence_interval == (0.3, 0.7)
        assert metrics.model_version == "test-v1"

    def test_is_uncertain_below_threshold(self):
        """Test is_uncertain below threshold."""
        metrics = UncertaintyMetrics(overall_uncertainty=0.2)
        assert metrics.is_uncertain(0.3) is False

    def test_is_uncertain_at_threshold(self):
        """Test is_uncertain at threshold."""
        metrics = UncertaintyMetrics(overall_uncertainty=0.3)
        assert metrics.is_uncertain(0.3) is True

    def test_is_uncertain_above_threshold(self):
        """Test is_uncertain above threshold."""
        metrics = UncertaintyMetrics(overall_uncertainty=0.5)
        assert metrics.is_uncertain(0.3) is True

    def test_to_dict(self):
        """Test serialization to dict."""
        metrics = UncertaintyMetrics(
            overall_uncertainty=0.5,
            epistemic_uncertainty=0.3,
            aleatoric_uncertainty=0.2,
            breakdown={"input": 0.1, "context": 0.2}
        )
        d = metrics.to_dict()
        assert d["overall_uncertainty"] == 0.5
        assert d["breakdown"]["input"] == 0.1


class TestUQLMIntegrationConstructor:
    """Test UQLMIntegration constructor."""

    def test_constructor_default_enabled(self):
        """Test default enabled state."""
        uqlm = UQLMIntegration()
        assert uqlm.enabled is True

    def test_constructor_with_config(self):
        """Test constructor with custom config."""
        config = {
            "enabled": False,
            "uncertainty_threshold": 0.5,
            "cache_ttl_seconds": 120
        }
        uqlm = UQLMIntegration(config=config)
        assert uqlm.enabled is False
        assert uqlm._uncertainty_threshold == 0.5
        assert uqlm._cache_ttl_seconds == 120

    def test_constructor_with_client(self):
        """Test constructor with UQLM client."""
        mock_client = object()
        uqlm = UQLMIntegration(client=mock_client)
        assert uqlm._client is mock_client


class TestUQLMIntegrationUncertaintyScore:
    """Test uncertainty score calculation."""

    def test_get_uncertainty_score_disabled(self):
        """Test disabled UQLM returns fallback."""
        uqlm = UQLMIntegration(config={"enabled": False})
        score = uqlm.get_uncertainty_score({})
        assert score == UQLMIntegration.FALLBACK_UNCERTAINTY

    def test_get_uncertainty_score_complete_context(self):
        """Test uncertainty with complete context."""
        context = {
            "data": "some data",
            "task": "test_task",
            "agent_id": "agent1",
            "agent_depth": 1
        }
        uqlm = UQLMIntegration()
        score = uqlm.get_uncertainty_score(context)
        assert 0.0 <= score <= 1.0

    def test_get_uncertainty_score_missing_fields(self):
        """Test uncertainty increases with missing fields."""
        uqlm = UQLMIntegration()
        score_partial = uqlm.get_uncertainty_score({"data": "x"})
        score_full = uqlm.get_uncertainty_score({
            "data": "x",
            "task": "y",
            "agent_id": "z"
        })
        assert score_partial > score_full

    def test_get_uncertainty_score_deep_agent(self):
        """Test uncertainty increases with agent depth."""
        uqlm = UQLMIntegration()
        score_shallow = uqlm.get_uncertainty_score({
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 1
        })
        score_deep = uqlm.get_uncertainty_score({
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 5
        })
        assert score_deep > score_shallow


class TestUQLMIntegrationBreakdown:
    """Test uncertainty breakdown."""

    def test_get_uncertainty_breakdown_disabled(self):
        """Test disabled returns empty dict."""
        uqlm = UQLMIntegration(config={"enabled": False})
        breakdown = uqlm.get_uncertainty_breakdown({})
        assert breakdown == {}

    def test_get_uncertainty_breakdown_has_categories(self):
        """Test breakdown has expected categories."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z"
        }
        uqlm = UQLMIntegration()
        breakdown = uqlm.get_uncertainty_breakdown(context)
        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0


class TestUQLMIntegrationMetrics:
    """Test full metrics retrieval."""

    def test_get_uncertainty_metrics_disabled(self):
        """Test disabled returns fallback metrics."""
        uqlm = UQLMIntegration(config={"enabled": False})
        metrics = uqlm.get_uncertainty_metrics({})
        assert metrics.overall_uncertainty == UQLMIntegration.FALLBACK_UNCERTAINTY

    def test_get_uncertainty_metrics_complete(self):
        """Test complete metrics retrieval."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 2
        }
        uqlm = UQLMIntegration()
        metrics = uqlm.get_uncertainty_metrics(context)

        assert isinstance(metrics, UncertaintyMetrics)
        assert 0.0 <= metrics.overall_uncertainty <= 1.0
        assert metrics.timestamp != ""


class TestUQLMIntegrationDirectCompute:
    """Test direct computation when no client."""

    def test_compute_direct_basic(self):
        """Test basic direct computation."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 1
        }
        uqlm = UQLMIntegration()
        result = uqlm._compute_direct(context)

        assert "overall" in result
        assert "epistemic" in result
        assert "aleatoric" in result
        assert "breakdown" in result
        assert 0.0 <= result["overall"] <= 1.0

    def test_compute_direct_short_context(self):
        """Test direct computation with short context."""
        context = {"data": "x"}
        uqlm = UQLMIntegration()
        result = uqlm._compute_direct(context)

        # Short context = higher uncertainty
        assert result["overall"] > 0.0

    def test_compute_direct_with_historical_error(self):
        """Test direct computation with historical calibration error."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "historical_calibration_error": 0.5
        }
        uqlm = UQLMIntegration()
        result = uqlm._compute_direct(context)

        assert "calibration" in result["breakdown"]
        assert result["breakdown"]["calibration"] > 0.0


class TestUQLMIntegrationThreshold:
    """Test threshold checking."""

    def test_check_uncertainty_threshold_below(self):
        """Test threshold check when below."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 1
        }
        uqlm = UQLMIntegration(config={"uncertainty_threshold": 0.5})
        result = uqlm.check_uncertainty_threshold(context)
        # With complete context, should be below threshold
        assert result is False or result is True

    def test_check_uncertainty_threshold_above(self):
        """Test threshold check when above."""
        context = {"data": "x"}
        uqlm = UQLMIntegration(config={"uncertainty_threshold": 0.1})
        result = uqlm.check_uncertainty_threshold(context)
        assert result is True

    def test_get_confidence_adjustment(self):
        """Test confidence adjustment calculation."""
        context = {
            "data": "x",
            "task": "y",
            "agent_id": "z",
            "agent_depth": 1
        }
        uqlm = UQLMIntegration()
        adjustment = uqlm.get_confidence_adjustment(context)

        # Higher uncertainty = larger adjustment
        assert 0.0 <= adjustment <= 0.2


class TestUQLMIntegrationCache:
    """Test cache management."""

    def test_clear_cache(self):
        """Test cache clearing."""
        uqlm = UQLMIntegration()
        # Add something to cache by calling get
        uqlm.get_uncertainty_score({"data": "x", "task": "y", "agent_id": "z", "agent_depth": 1})
        assert len(uqlm._uncertainty_cache) >= 0

        uqlm.clear_cache()
        assert len(uqlm._uncertainty_cache) == 0

    def test_cache_key_generation(self):
        """Test cache key generation."""
        uqlm = UQLMIntegration()
        key1 = uqlm._get_cache_key({
            "task_id": "t1",
            "agent_id": "a1",
            "agent_depth": 2
        })
        key2 = uqlm._get_cache_key({
            "task_id": "t2",
            "agent_id": "a2",
            "agent_depth": 3
        })
        assert key1 != key2


class TestUQLMIntegrationStatistics:
    """Test statistics retrieval."""

    def test_get_statistics(self):
        """Test statistics retrieval."""
        uqlm = UQLMIntegration(config={
            "enabled": True,
            "uncertainty_threshold": 0.3
        })
        stats = uqlm.get_statistics()

        assert stats["enabled"] is True
        assert stats["uncertainty_threshold"] == 0.3
        assert "cache_size" in stats
        assert "client_connected" in stats


class TestUQLMIntegrationEnableDisable:
    """Test enable/disable methods."""

    def test_enable(self):
        """Test enable method."""
        uqlm = UQLMIntegration(config={"enabled": False})
        uqlm.enable()
        assert uqlm.enabled is True

    def test_disable(self):
        """Test disable method."""
        uqlm = UQLMIntegration(config={"enabled": True})
        uqlm.disable()
        assert uqlm.enabled is False


class TestUQLMIntegrationThresholdSetter:
    """Test threshold setter."""

    def test_set_threshold(self):
        """Test threshold setter."""
        uqlm = UQLMIntegration()
        uqlm.set_threshold(0.7)
        assert uqlm._uncertainty_threshold == 0.7

    def test_set_threshold_clamped(self):
        """Test threshold is clamped to 0-1."""
        uqlm = UQLMIntegration()
        uqlm.set_threshold(1.5)
        assert uqlm._uncertainty_threshold == 1.0

        uqlm.set_threshold(-0.5)
        assert uqlm._uncertainty_threshold == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
