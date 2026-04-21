"""
Feature #8: 8-Dimensional Risk Assessment Engine

This module provides comprehensive risk evaluation across 8 dimensions:
- D1: Data Privacy Risk
- D2: Injection Risk
- D3: Cost/Token Risk
- D4: UAF/CLAP Risk
- D5: Memory Poisoning Risk
- D6: Cross-Agent Leak Risk
- D7: Latency/SLO Risk
- D8: Compliance Risk
"""

__version__ = "1.0.0"

from .risk_assessment_engine import (
    RiskAssessmentEngine,
    RiskAssessmentResult,
    RiskLevel,
    RiskConfig,
)
from .decision_log import DecisionLog, DecisionInput, DecisionRecord
from .confidence_calibration import ConfidenceCalibrator, CalibrationResult
from .effort_tracker import EffortTracker, EffortMetrics
from .alert_manager import AlertManager, Alert, AlertType
from .uqlm_integration import UQLMIntegration

__all__ = [
    # Engine
    "RiskAssessmentEngine",
    "RiskAssessmentResult",
    "RiskLevel",
    "RiskConfig",
    # Decision Log
    "DecisionLog",
    "DecisionInput",
    "DecisionRecord",
    # Confidence
    "ConfidenceCalibrator",
    "CalibrationResult",
    # Effort
    "EffortTracker",
    "EffortMetrics",
    # Alerts
    "AlertManager",
    "Alert",
    "AlertType",
    # UQLM
    "UQLMIntegration",
]