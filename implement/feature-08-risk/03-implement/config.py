"""
Risk Assessment Configuration

Provides typed configuration for risk thresholds, dimension weights, and limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskConfig:
    """
    Configuration for the Risk Assessment Engine.

    Attributes:
        thresholds: Risk level thresholds (critical, high, medium, low)
        dimension_weights: Per-dimension weights for composite scoring
        uqlm_settings: UQLM integration configuration
        effort_settings: Effort tracking configuration
        alert_settings: Alert system configuration
        limits: Operational limits (max depth, context window, etc.)
    """

    # Thresholds for risk levels
    thresholds: dict[str, float] = field(default_factory=lambda: {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.0,
    })

    # Dimension weights (default all 1.0)
    dimension_weights: dict[str, float] = field(default_factory=lambda: {
        "D1": 1.0,  # Data Privacy
        "D2": 1.2,  # Injection (higher weight)
        "D3": 0.8,  # Cost
        "D4": 1.0,  # UAF/CLAP
        "D5": 1.1,  # Memory Poisoning (higher)
        "D6": 1.0,  # Cross-Agent Leak
        "D7": 0.9,  # Latency
        "D8": 1.0,  # Compliance
    })

    # UQLM integration settings
    uqlm_settings: dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "uncertainty_threshold": 0.3,
        "auto_calibrate": True,
    })

    # Effort tracking settings
    effort_settings: dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "track_detailed": True,
        "quality_threshold": 0.7,
    })

    # Alert settings
    alert_settings: dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "notify_on_critical": True,
        "notify_on_high": True,
    })

    # Operational limits
    limits: dict[str, int] = field(default_factory=lambda: {
        "max_agent_depth": 5,
        "max_context_window": 200000,
        "max_tokens_per_task": 500000,
        "max_execution_time_minutes": 60,
    })

    # Decision log settings
    decision_log_settings: dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "storage_path": "memory/decisions",
        "index_enabled": True,
    })

    def get_threshold(self, level: str) -> float:
        """Get threshold for a given risk level."""
        return self.thresholds.get(level, 0.0)

    def get_weight(self, dimension: str) -> float:
        """Get weight for a given dimension."""
        return self.dimension_weights.get(dimension, 1.0)

    def is_dimension_enabled(self, dimension: str) -> bool:
        """Check if a dimension is enabled for assessment."""
        return dimension in self.dimension_weights

    @classmethod
    def default_profile(cls) -> RiskConfig:
        """Create a default configuration profile."""
        return cls()

    @classmethod
    def high_security_profile(cls) -> RiskConfig:
        """Create a high-security profile with stricter thresholds."""
        config = cls()
        config.thresholds = {
            "critical": 0.6,
            "high": 0.4,
            "medium": 0.3,
            "low": 0.0,
        }
        config.dimension_weights = {
            "D1": 1.5,  # Data Privacy - very high
            "D2": 1.5,  # Injection - very high
            "D3": 0.8,
            "D4": 1.2,
            "D5": 1.3,  # Memory Poisoning - high
            "D6": 1.2,
            "D7": 0.9,
            "D8": 1.3,  # Compliance - high
        }
        return config

    @classmethod
    def low_overhead_profile(cls) -> RiskConfig:
        """Create a low-overhead profile for performance-critical scenarios."""
        config = cls()
        config.dimension_weights = {
            "D1": 0.8,
            "D2": 1.0,
            "D3": 1.2,  # Cost - higher priority
            "D4": 0.8,
            "D5": 0.9,
            "D6": 1.0,
            "D7": 1.2,  # Latency - higher priority
            "D8": 0.8,
        }
        config.limits["max_agent_depth"] = 3
        return config


def create_config(**overrides) -> RiskConfig:
    """
    Create a RiskConfig with overrides.

    Usage:
        config = create_config(
            thresholds={"critical": 0.9, "high": 0.7},
            dimension_weights={"D1": 2.0, "D2": 1.5}
        )
    """
    defaults = RiskConfig()
    for key, value in overrides.items():
        if hasattr(defaults, key):
            setattr(defaults, key, value)
    return defaults