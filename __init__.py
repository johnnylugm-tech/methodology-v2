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
from .smart_router import SmartRouter, TaskType, BudgetLevel, RoutingResult
from .storage import Storage, Conversation, Message
from .openclaw_adapter import (
    OpenClawAdapter, 
    OpenClawConfig, 
    AgentType,
    MultiAgentOrchestrator,
    create_musk_agent,
    create_researcher_agent,
    create_developer_agent
)

__version__ = "2.5.0"

__all__ = [
    # Core
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
    # Dashboard
    "Dashboard",
    # Quality Gate
    "AutoQualityGate",
    "QualityReport",
    "QualityIssue",
    # Router
    "SmartRouter",
    "TaskType",
    "BudgetLevel",
    "RoutingResult",
    # Storage
    "Storage",
    "Conversation",
    "Message",
    # OpenClaw
    "OpenClawAdapter",
    "OpenClawConfig",
    "AgentType",
    "MultiAgentOrchestrator",
    "create_musk_agent",
    "create_researcher_agent",
    "create_developer_agent",
]
