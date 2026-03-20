"""
Methodology v2 - Multi-Agent Collaboration Development Methodology

Core classes for error classification, task lifecycle, and quality gates.
"""

from .core import MethodologyCore, MethodologyConfig
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

# Gap-filling modules (v3.0.1)
from .dashboard_cost_trend import CostTrendAnalyzer, CostSnapshot, CostTrend, CostForecast
from .failover_manager import FailoverManager, CircuitBreaker, ModelEndpoint, FailoverEvent
from .parallel_executor import ParallelExecutor, ParallelTask, Worker, ExecutionResult

__version__ = "4.3.0"

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
    # Gap-filling modules (v3.0.1)
    "CostTrendAnalyzer",
    "CostSnapshot",
    "CostTrend",
    "CostForecast",
    "FailoverManager",
    "CircuitBreaker",
    "ModelEndpoint",
    "FailoverEvent",
    "ParallelExecutor",
    "ParallelTask",
    "Worker",
    "ExecutionResult",

    # Multi-Agent Team (v3.1)
    "AgentTeam",
    "AgentDefinition",
    "AgentInstance",
    "AgentRole",
    "AgentCapability",
    "AgentPermission",
    "AgentTool",

    # Agent Communication
    "AgentCommunication",
    "AgentMessage",
    "HandoffRule",
    "Conversation",
    "ConflictRecord",
    "MessageType",
    "HandoffTrigger",

    # Agent State
    "StateManager",
    "AgentState",
    "AgentTask",
    "Artifact",
    "TaskStatus",

    # Project Layer (v3.2)
    "Project",
    "ProjectDatabase",

    # AgentCoordination (v3.3)
    "AgentRegistry",
    "AgentRegistration",
    "AgentStatus",
    "AgentType",
    "AgentMetadata",

    # MessageBus (v3.3)
    "MessageBus",
    "Envelope",
    "Subscription",
    "MessagePriority",
    "MessageType",

    # WorkflowGraph (v3.3)
    "WorkflowGraph",
    "WorkflowNode",
    "WorkflowEdge",
    "WorkflowExecution",
    "NodeStatus",
    "NodeType",

    # ApprovalFlow (v3.3)
    "ApprovalFlow",
    "ApprovalRule",
    "ApprovalStep",
    "ApprovalRequest",
    "ApprovalStatus",
    "ApprovalLevel",

    # Extensions (v4.0)
    # MCP Adapter
    "MCPAdapter",
    "MCPClient",
    "MCPConfig",
    "ServiceConnection",
    "ServiceStatus",

    # Cost Optimizer
    "CostOptimizer",
    "CostRecord",
    "CostAlert",
    "MODEL_PRICING",
    "TASK_MODEL_MAP",

    # Vertical Templates
    "CustomerServiceAgent",
    "LegalAgent",

    # Security Audit
    "SecurityAuditor",
    "APIKeyScanner",
    "SQLInjectionScanner",
    "DataLeakScanner",

    # LangChain Adapter
    "ChainMigrator",
    "MethodologyLLMWrapper",

    # Local Deployment
    "LocalDeploy",
    "OllamaManager",

    # Workflow Visualizer
    "WorkflowVisualizer",

    # Core (v4.1)
    "MethodologyCore",
    "MethodologyConfig",
    "create_pm_setup",
    "create_minimal_setup",
]

# Extensions Integration (v4.2)
from .extensions import Extensions, create_extensions

__all__ = [
    # ... (existing exports)
    "Extensions",
    "create_extensions",
]

# PM Improvements (v4.3)
from .cicd_integration import CICDIntegration, Pipeline, PipelineStep
from .multi_language import MultiLanguageSupport, Language, LanguageConfig
from .knowledge_base import KnowledgeBase, Pattern, BestPractice
from .agent_spawner import AgentSpawner, SpawnConfig, SpawnedAgent, SpawnPolicy
from .version_control import VersionControl, Version, Artifact

__all__ = [
    # ... (existing)
    "CICDIntegration",
    "Pipeline",
    "PipelineStep",
    "MultiLanguageSupport",
    "Language",
    "LanguageConfig",
    "KnowledgeBase",
    "Pattern",
    "BestPractice",
    "AgentSpawner",
    "SpawnConfig",
    "SpawnedAgent",
    "SpawnPolicy",
    "VersionControl",
    "Version",
    "Artifact",
]
