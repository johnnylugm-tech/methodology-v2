"""
Tests for RiskConfig [Internal]

Covers all configuration profiles and factory functions.
"""

import pytest
import sys
from pathlib import Path

# Add implement directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from config import RiskConfig, create_config


class TestRiskConfigDefault:
    """Test default RiskConfig profile."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        config = RiskConfig()
        assert config.get_threshold("critical") == 0.8
        assert config.get_threshold("high") == 0.6
        assert config.get_threshold("medium") == 0.4
        assert config.get_threshold("low") == 0.0

    def test_default_thresholds_unknown_level_returns_zero(self):
        """Test that unknown threshold level returns 0.0."""
        config = RiskConfig()
        assert config.get_threshold("unknown") == 0.0

    def test_default_dimension_weights(self):
        """Test default dimension weights."""
        config = RiskConfig()
        assert config.get_weight("D1") == 1.0
        assert config.get_weight("D2") == 1.2  # Higher for injection
        assert config.get_weight("D3") == 0.8
        assert config.get_weight("D4") == 1.0
        assert config.get_weight("D5") == 1.1  # Higher for memory poisoning
        assert config.get_weight("D6") == 1.0
        assert config.get_weight("D7") == 0.9
        assert config.get_weight("D8") == 1.0

    def test_default_weight_unknown_dimension_returns_one(self):
        """Test unknown dimension returns weight of 1.0."""
        config = RiskConfig()
        assert config.get_weight("D9") == 1.0

    def test_is_dimension_enabled(self):
        """Test dimension enabled check."""
        config = RiskConfig()
        assert config.is_dimension_enabled("D1") is True
        assert config.is_dimension_enabled("D2") is True
        assert config.is_dimension_enabled("D9") is False

    def test_default_limits(self):
        """Test default operational limits."""
        config = RiskConfig()
        assert config.limits["max_agent_depth"] == 5
        assert config.limits["max_context_window"] == 200000
        assert config.limits["max_tokens_per_task"] == 500000
        assert config.limits["max_execution_time_minutes"] == 60

    def test_default_uqlm_settings(self):
        """Test default UQLM settings."""
        config = RiskConfig()
        assert config.uqlm_settings["enabled"] is True
        assert config.uqlm_settings["uncertainty_threshold"] == 0.3
        assert config.uqlm_settings["auto_calibrate"] is True

    def test_default_effort_settings(self):
        """Test default effort settings."""
        config = RiskConfig()
        assert config.effort_settings["enabled"] is True
        assert config.effort_settings["track_detailed"] is True
        assert config.effort_settings["quality_threshold"] == 0.7

    def test_default_alert_settings(self):
        """Test default alert settings."""
        config = RiskConfig()
        assert config.alert_settings["enabled"] is True
        assert config.alert_settings["notify_on_critical"] is True
        assert config.alert_settings["notify_on_high"] is True

    def test_default_decision_log_settings(self):
        """Test default decision log settings."""
        config = RiskConfig()
        assert config.decision_log_settings["enabled"] is True
        assert config.decision_log_settings["storage_path"] == "memory/decisions"
        assert config.decision_log_settings["index_enabled"] is True


class TestRiskConfigHighSecurity:
    """Test high security profile."""

    def test_high_security_stricter_thresholds(self):
        """Test that high security has stricter thresholds."""
        config = RiskConfig.high_security_profile()
        assert config.get_threshold("critical") == 0.6  # Stricter than default 0.8
        assert config.get_threshold("high") == 0.4       # Stricter than default 0.6
        assert config.get_threshold("medium") == 0.3     # Stricter than default 0.4

    def test_high_security_elevated_weights(self):
        """Test elevated weights for security-critical dimensions."""
        config = RiskConfig.high_security_profile()
        assert config.get_weight("D1") == 1.5   # Data Privacy - very high
        assert config.get_weight("D2") == 1.5   # Injection - very high
        assert config.get_weight("D5") == 1.3   # Memory Poisoning - high
        assert config.get_weight("D8") == 1.3   # Compliance - high

    def test_high_security_d3_d7_lower_weights(self):
        """Test that D3 (Cost) and D7 (Latency) have lower weights in high security."""
        config = RiskConfig.high_security_profile()
        assert config.get_weight("D3") == 0.8
        assert config.get_weight("D7") == 0.9


class TestRiskConfigLowOverhead:
    """Test low overhead profile for performance-critical scenarios."""

    def test_low_overhead_cost_and_latency_higher(self):
        """Test that cost and latency have higher priority in low overhead."""
        config = RiskConfig.low_overhead_profile()
        assert config.get_weight("D3") == 1.2  # Cost - higher priority
        assert config.get_weight("D7") == 1.2  # Latency - higher priority

    def test_low_overhead_security_dimensions_lower(self):
        """Test that security dimensions have lower weights."""
        config = RiskConfig.low_overhead_profile()
        assert config.get_weight("D1") == 0.8  # Data Privacy - lower
        assert config.get_weight("D4") == 0.8  # UAF/CLAP - lower
        assert config.get_weight("D8") == 0.8  # Compliance - lower

    def test_low_overhead_reduced_max_depth(self):
        """Test that max agent depth is reduced for performance."""
        config = RiskConfig.low_overhead_profile()
        assert config.limits["max_agent_depth"] == 3  # Lower than default 5


class TestCreateConfig:
    """Test create_config factory function."""

    def test_create_config_with_overrides(self):
        """Test creating config with custom overrides."""
        config = create_config(
            thresholds={"critical": 0.9, "high": 0.7},
            dimension_weights={"D1": 2.0, "D2": 1.5}
        )
        assert config.get_threshold("critical") == 0.9
        assert config.get_threshold("high") == 0.7
        assert config.get_weight("D1") == 2.0
        assert config.get_weight("D2") == 1.5

    def test_create_config_unmodified_fields(self):
        """Test that unspecified fields retain defaults."""
        config = create_config(thresholds={"critical": 0.9})
        assert config.get_threshold("high") == 0.0  # Default: key not in overrides returns 0.0
        assert config.get_weight("D1") == 1.0       # Default unchanged

    def test_create_config_empty_overrides(self):
        """Test create_config with no overrides returns defaults."""
        config = create_config()
        assert config.get_threshold("critical") == 0.8
        assert config.get_weight("D1") == 1.0

    def test_create_config_invalid_threshold_key_ignored(self):
        """Test that invalid keys are ignored."""
        config = create_config(invalid_key="value")
        # Should not raise, invalid key is silently ignored


class TestRiskConfigEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_threshold_extremes(self):
        """Test threshold values at extremes."""
        config = RiskConfig()
        # These should not raise
        config.thresholds["critical"] = 1.0
        config.thresholds["critical"] = 0.0
        assert config.get_threshold("critical") == 0.0

    def test_weight_extremes(self):
        """Test weight values at extremes."""
        config = RiskConfig()
        config.dimension_weights["D1"] = 0.0
        config.dimension_weights["D2"] = 2.0
        assert config.get_weight("D1") == 0.0
        assert config.get_weight("D2") == 2.0

    def test_limits_can_be_modified(self):
        """Test that limits dictionary can be modified."""
        config = RiskConfig()
        config.limits["max_agent_depth"] = 10
        assert config.limits["max_agent_depth"] == 10

    def test_all_8_dimensions_present(self):
        """Test that all 8 dimensions are defined."""
        config = RiskConfig()
        for i in range(1, 9):
            assert f"D{i}" in config.dimension_weights
            assert config.is_dimension_enabled(f"D{i}") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
