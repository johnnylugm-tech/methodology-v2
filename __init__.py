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
from .task_splitter import TaskSplitter, Task, TaskStatus, TaskPriority
from .task_splitter_v2 import TaskSplitter as TaskSplitterV2, Task as TaskV2, Milestone
from .doc_generator import DocGenerator, DocItem
from .test_generator import TestGenerator, TestCase
from .predictive_monitor import PredictiveMonitor, MetricPoint, Prediction
from .workflow_templates import WorkflowTemplates, WorkflowTemplate, WorkflowType, Sprint
from .progress_dashboard import ProgressDashboard, Sprint as PSprint, BacklogItem
from .rbac import RBAC, User, Role, Permission
from .scheduler import Scheduler, Resource, ScheduledTask, Priority as SchedPriority
from .cost_allocator import CostAllocator, CostEntry, Budget, CostType
from .audit_logger import AuditLogger, AuditEntry, ActionType, ResourceType
from .risk_dashboard import RiskDashboard, Risk, RiskLevel, RiskCategory
from .delivery_manager import DeliveryManager, DeliveryItem, Version, DeliveryStatus

__version__ = "3.0.0"

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
    # Task Splitter
    "TaskSplitter",
    "TaskStatus",
    "TaskPriority",
    # Task Splitter v2 (DAG + Milestones)
    "TaskSplitterV2",
    "TaskV2",
    "Milestone",
    # Doc Generator
    "DocGenerator",
    "DocItem",
    # Test Generator
    "TestGenerator",
    "TestCase",
    # Predictive Monitor
    "PredictiveMonitor",
    "MetricPoint",
    "Prediction",
    # Workflow Templates (Phase 1)
    "WorkflowTemplates",
    "WorkflowTemplate",
    "WorkflowType",
    "Sprint",
    # Progress Dashboard (Phase 1)
    "ProgressDashboard",
    "PSprint",
    "BacklogItem",
    # RBAC (Phase 2)
    "RBAC",
    "User",
    "Role",
    "Permission",
    # Scheduler (Phase 2)
    "Scheduler",
    "Resource",
    "ScheduledTask",
    "SchedPriority",
    # Cost Allocator (Phase 2)
    "CostAllocator",
    "CostEntry",
    "Budget",
    "CostType",
    # Audit Logger (Phase 3)
    "AuditLogger",
    "AuditEntry",
    "ActionType",
    "ResourceType",
    # Risk Dashboard (Phase 3)
    "RiskDashboard",
    "Risk",
    "RiskLevel",
    "RiskCategory",
    # Delivery Manager (Phase 3)
    "DeliveryManager",
    "DeliveryItem",
    "Version",
    "DeliveryStatus",
]
