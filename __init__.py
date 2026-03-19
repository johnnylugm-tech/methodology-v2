"""
Methodology v2 - Multi-Agent Collaboration Development Methodology

Core classes for error classification, task lifecycle, and quality gates.
"""

from .methodology import (
    ErrorLevel,
    ProcessType,
    AlertLevel,
    Error,
    Task,
    Agent,
    ErrorClassifier,
    ErrorHandler,
    TaskLifecycle,
    QualityGate,
    Crew,
    Monitor,
)
from .dashboard import Dashboard
from .auto_quality_gate import AutoQualityGate, QualityReport, QualityIssue

__version__ = "2.3.0"

__all__ = [
    "ErrorLevel",
    "ProcessType", 
    "AlertLevel",
    "Error",
    "Task",
    "Agent",
    "ErrorClassifier",
    "ErrorHandler",
    "TaskLifecycle",
    "QualityGate",
    "Crew",
    "Monitor",
    "Dashboard",
    "AutoQualityGate",
    "QualityReport",
    "QualityIssue",
]
