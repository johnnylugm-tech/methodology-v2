"""
Methodology v2 - Multi-Agent Collaboration Development Methodology

Core classes for error classification, task lifecycle, and quality gates.
"""

__version__ = "6.00.0"

# Guard: if __package__ is None/empty, this is being imported as a top-level script
# (e.g., by pytest collecting tests). Use lazy loading via __getattr__.
if __package__ is None or __package__ == "":
    # Lazy loading - don't execute any imports that might fail
    def __getattr__(name):
        import importlib
        import sys

        # Mapping of names to their source modules
        _LAZY_IMPORTS = {
            # Core
            "MethodologyCore": ".core",
            "MethodologyConfig": ".core",
            # methodology_base
            "ErrorLevel": ".methodology_base",
            "ProcessType": ".methodology_base",
            "AlertLevel": ".methodology_base",
            "Error": ".methodology_base",
            "Task": ".methodology_base",
            "Agent": ".methodology_base",
            "ErrorClassifier": ".methodology_base",
            "ErrorHandler": ".methodology_base",
            "TaskLifecycle": ".methodology_base",
            "QualityGate": ".methodology_base",
            "Crew": ".methodology_base",
            "Monitor": ".methodology_base",
            "Methodology": ".methodology_base",
            # Dashboard
            "Dashboard": ".dashboard",
            # Quality Gate
            "AutoQualityGate": ".auto_quality_gate",
            "QualityReport": ".auto_quality_gate",
            "QualityIssue": ".auto_quality_gate",
            # Router
            "SmartRouter": ".smart_router",
            "TaskType": ".smart_router",
            "BudgetLevel": ".smart_router",
            "RoutingResult": ".smart_router",
            # Storage
            "Storage": ".storage",
            "Conversation": ".storage",
            "Message": ".storage",
            # OpenClaw
            "OpenClawAdapter": ".openclaw_adapter",
            "OpenClawConfig": ".openclaw_adapter",
            "AgentType": ".openclaw_adapter",
            "MultiAgentOrchestrator": ".openclaw_adapter",
            "create_musk_agent": ".openclaw_adapter",
            "create_researcher_agent": ".openclaw_adapter",
            "create_developer_agent": ".openclaw_adapter",
            # Task Splitter
            "TaskSplitter": ".task_splitter",
            "TaskStatus": ".task_splitter",
            "TaskPriority": ".task_splitter",
            # Task Splitter v2
            "TaskSplitterV2": ".task_splitter_v2",
            "TaskV2": ".task_splitter_v2",
            "Milestone": ".task_splitter_v2",
            # Doc Generator
            "DocGenerator": ".doc_generator",
            "DocItem": ".doc_generator",
            # Test Generator
            "TestGenerator": ".test_generator",
            "TestCase": ".test_generator",
            # Predictive Monitor
            "PredictiveMonitor": ".predictive_monitor",
            "MetricPoint": ".predictive_monitor",
            "Prediction": ".predictive_monitor",
            # Workflow Templates
            "WorkflowTemplates": ".workflow_templates",
            "WorkflowTemplate": ".workflow_templates",
            "WorkflowType": ".workflow_templates",
            "Sprint": ".workflow_templates",
            # Progress Dashboard
            "ProgressDashboard": ".progress_dashboard",
            "PSprint": ".progress_dashboard",
            "BacklogItem": ".progress_dashboard",
            # RBAC
            "RBAC": ".rbac",
            "User": ".rbac",
            "Role": ".rbac",
            "Permission": ".rbac",
            # Scheduler
            "Scheduler": ".scheduler",
            "Resource": ".scheduler",
            "ScheduledTask": ".scheduler",
            "SchedPriority": ".scheduler",
            # Cost Allocator
            "CostAllocator": ".cost_allocator",
            "CostEntry": ".cost_allocator",
            "Budget": ".cost_allocator",
            "CostType": ".cost_allocator",
            # Audit Logger
            "AuditLogger": ".audit_logger",
            "AuditEntry": ".audit_logger",
            "ActionType": ".audit_logger",
            "ResourceType": ".audit_logger",
            # Risk Dashboard
            "RiskDashboard": ".risk_dashboard",
            "Risk": ".risk_dashboard",
            "RiskLevel": ".risk_dashboard",
            "RiskCategory": ".risk_dashboard",
            # Delivery Manager
            "DeliveryManager": ".delivery_manager",
            "DeliveryItem": ".delivery_manager",
            "Version": ".delivery_manager",
            "DeliveryStatus": ".delivery_manager",
            # Gap-filling modules
            "CostTrendAnalyzer": ".dashboard_cost_trend",
            "CostSnapshot": ".dashboard_cost_trend",
            "CostTrend": ".dashboard_cost_trend",
            "CostForecast": ".dashboard_cost_trend",
            "FailoverManager": ".failover_manager",
            "CircuitBreaker": ".failover_manager",
            "ModelEndpoint": ".failover_manager",
            "FailoverEvent": ".failover_manager",
            "ParallelExecutor": ".parallel_executor",
            "ParallelTask": ".parallel_executor",
            "Worker": ".parallel_executor",
            "ExecutionResult": ".parallel_executor",
            # Extensions
            "Extensions": ".extensions",
            "create_extensions": ".extensions",
            # PM Improvements
            "CICDIntegration": ".cicd_integration",
            "Pipeline": ".cicd_integration",
            "PipelineStep": ".cicd_integration",
            "MultiLanguageSupport": ".multi_language",
            "Language": ".multi_language",
            "LanguageConfig": ".multi_language",
            "KnowledgeBase": ".knowledge_base",
            "Pattern": ".knowledge_base",
            "BestPractice": ".knowledge_base",
            "AgentSpawner": ".agent_spawner",
            "SpawnConfig": ".agent_spawner",
            "SpawnedAgent": ".agent_spawner",
            "SpawnPolicy": ".agent_spawner",
            "DeliveryTracker": ".delivery_tracker",
            # Phase 2
            "AgentLifecycleViewer": ".agent_lifecycle",
            "AgentLifecycleState": ".agent_lifecycle",
            "AgentLifecycleInfo": ".agent_lifecycle",
            "GanttChart": ".gantt_chart",
            "GanttTask": ".gantt_chart",
            "ResourceDashboard": ".resource_dashboard",
            "ResourceType": ".resource_dashboard",
            "ResourceStatus": ".resource_dashboard",
            "ResourceInfo": ".resource_dashboard",
            # Phase 3
            "SprintPlanner": ".sprint_planner",
            "Story": ".sprint_planner",
            "StoryStatus": ".sprint_planner",
            "StorySize": ".sprint_planner",
            "ExtensionConfigurator": ".extension_configurator",
            "ExtensionType": ".extension_configurator",
            "DataConnector": ".data_connector",
            "DataSourceType": ".data_connector",
            "PrometheusConnector": ".data_connector",
            "JiraConnector": ".data_connector",
            "OpenTelemetryConnector": ".data_connector",
            "DataSourceManager": ".data_connector",
            # Solutions A-E
            "AgentEvaluator": ".agent_evaluator",
            "HumanEvaluator": ".agent_evaluator",
            "EvaluationSuite": ".agent_evaluator",
            "EvaluationResult": ".agent_evaluator",
            "MetricType": ".agent_evaluator",
            "EvaluationStatus": ".agent_evaluator",
            "StructuredOutputEngine": ".structured_output",
            "OutputSchema": ".structured_output",
            "FieldDefinition": ".structured_output",
            "ParseResult": ".structured_output",
            "OutputFormat": ".structured_output",
            "ParseStrategy": ".structured_output",
            "DataQualityChecker": ".data_quality",
            "FieldProfile": ".data_quality",
            "QualityLevel": ".data_quality",
            "IssueType": ".data_quality",
            "EnterpriseHub": ".enterprise_hub",
            "Authenticator": ".enterprise_hub",
            "SlackMessenger": ".enterprise_hub",
            "TeamsMessenger": ".enterprise_hub",
            "AuthProvider": ".enterprise_hub",
            "LangGraphMigrationTool": ".langgraph_migrator",
            "MigrationResult": ".langgraph_migrator",
            "PatternMapping": ".langgraph_migrator",
            "ASTNode": ".langgraph_migrator",
            "NodeType": ".langgraph_migrator",
            # P2P Orchestrator
            "P2POrchestrator": ".p2p_orchestrator",
            "PeerAgent": ".p2p_orchestrator",
            "P2PMessage": ".p2p_orchestrator",
            "PendingRequest": ".p2p_orchestrator",
            "P2PError": ".p2p_orchestrator",
            # Traceability Matrix
            "TraceabilityMatrix": ".traceability_matrix",
            "TraceLink": ".traceability_matrix",
            "TraceStatus": ".traceability_matrix",
            "LinkType": ".traceability_matrix",
            "TraceabilityMixin": ".traceability_matrix",
            "get_traceability_matrix": ".traceability_matrix",
            "reset_traceability_matrix": ".traceability_matrix",
            # A/B Enforcer v2.0
            "ABEnforcerV2": ".ab_enforcer",
            "ABTaskLifecycle": ".ab_enforcer",
            "RestrictedAgentSpawner": ".ab_enforcer",
            "ABQualityGate": ".ab_enforcer",
            "get_ab_enforcer": ".ab_enforcer",
            "enforce_phase_complete": ".ab_enforcer",
            "enforce_tool_call": ".ab_enforcer",
            "enforce_quality_gate": ".ab_enforcer",
            "PermissionDenied": ".ab_enforcer",
            "SwapReviewError": ".ab_enforcer",
            "ReviewEvidenceRequired": ".ab_enforcer",
            # Legacy / Aliases
            "Artifact": ".delivery_tracker",
        }

        if name in _LAZY_IMPORTS:
            from importlib import import_module
            mod_name = _LAZY_IMPORTS[name]
            # Handle aliased imports
            if name in ("TaskSplitterV2",):
                mod = import_module(mod_name, package=__name__)
                return getattr(mod, name)
            elif name in ("TaskV2", "Milestone", "Task", "Version", "Story", "NodeType", "ResourceType", "TaskStatus", "LinkType", "TraceStatus"):
                # These might be defined in multiple modules - try direct import first
                try:
                    mod = import_module(mod_name, package=__name__)
                    return getattr(mod, name)
                except (ImportError, AttributeError):
                    pass
            mod = import_module(mod_name, package=__name__)
            return getattr(mod, name)

        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    # Concise __all__ covering all lazy-loaded names
    __all__ = [
        # Core
        "MethodologyCore", "MethodologyConfig", "Methodology",
        # methodology_base
        "ErrorLevel", "ProcessType", "AlertLevel", "Error", "Task", "Agent",
        "ErrorClassifier", "ErrorHandler", "TaskLifecycle", "QualityGate", "Crew", "Monitor",
        # Dashboard
        "Dashboard",
        # Quality Gate
        "AutoQualityGate", "QualityReport", "QualityIssue",
        # Router
        "SmartRouter", "TaskType", "BudgetLevel", "RoutingResult",
        # Storage
        "Storage", "Conversation", "Message",
        # OpenClaw
        "OpenClawAdapter", "OpenClawConfig", "AgentType", "MultiAgentOrchestrator",
        "create_musk_agent", "create_researcher_agent", "create_developer_agent",
        # Task Splitter
        "TaskSplitter", "TaskStatus", "TaskPriority",
        # Task Splitter v2
        "TaskSplitterV2", "TaskV2", "Milestone",
        # Doc Generator
        "DocGenerator", "DocItem",
        # Test Generator
        "TestGenerator", "TestCase",
        # Predictive Monitor
        "PredictiveMonitor", "MetricPoint", "Prediction",
        # Workflow Templates
        "WorkflowTemplates", "WorkflowTemplate", "WorkflowType", "Sprint",
        # Progress Dashboard
        "ProgressDashboard", "PSprint", "BacklogItem",
        # RBAC
        "RBAC", "User", "Role", "Permission",
        # Scheduler
        "Scheduler", "Resource", "ScheduledTask", "SchedPriority",
        # Cost Allocator
        "CostAllocator", "CostEntry", "Budget", "CostType",
        # Audit Logger
        "AuditLogger", "AuditEntry", "ActionType", "ResourceType",
        # Risk Dashboard
        "RiskDashboard", "Risk", "RiskLevel", "RiskCategory",
        # Delivery Manager
        "DeliveryManager", "DeliveryItem", "Version", "DeliveryStatus",
        # Gap-filling modules
        "CostTrendAnalyzer", "CostSnapshot", "CostTrend", "CostForecast",
        "FailoverManager", "CircuitBreaker", "ModelEndpoint", "FailoverEvent",
        "ParallelExecutor", "ParallelTask", "Worker", "ExecutionResult",
        # Extensions
        "Extensions", "create_extensions",
        # PM Improvements
        "CICDIntegration", "Pipeline", "PipelineStep",
        "MultiLanguageSupport", "Language", "LanguageConfig",
        "KnowledgeBase", "Pattern", "BestPractice",
        "AgentSpawner", "SpawnConfig", "SpawnedAgent", "SpawnPolicy",
        "DeliveryTracker", "Artifact",
        # Phase 2
        "AgentLifecycleViewer", "AgentLifecycleState", "AgentLifecycleInfo",
        "GanttChart", "GanttTask",
        "ResourceDashboard", "ResourceType", "ResourceStatus", "ResourceInfo",
        # Phase 3
        "SprintPlanner", "Story", "StoryStatus", "StorySize",
        "ExtensionConfigurator", "ExtensionType",
        "DataConnector", "DataSourceType",
        "PrometheusConnector", "JiraConnector", "OpenTelemetryConnector", "DataSourceManager",
        # Solutions A-E
        "AgentEvaluator", "HumanEvaluator", "EvaluationSuite", "EvaluationResult",
        "MetricType", "EvaluationStatus",
        "StructuredOutputEngine", "OutputSchema", "FieldDefinition", "ParseResult",
        "OutputFormat", "ParseStrategy",
        "DataQualityChecker", "FieldProfile", "QualityLevel", "IssueType",
        "EnterpriseHub", "Authenticator", "SlackMessenger", "TeamsMessenger", "AuthProvider",
        "LangGraphMigrationTool", "MigrationResult", "PatternMapping", "ASTNode", "NodeType",
        # P2P Orchestrator
        "P2POrchestrator", "PeerAgent", "P2PMessage", "PendingRequest", "P2PError",
        # Traceability Matrix
        "TraceabilityMatrix", "TraceLink", "TraceStatus", "LinkType",
        "TraceabilityMixin", "get_traceability_matrix", "reset_traceability_matrix",
        # A/B Enforcer v2.0
        "ABEnforcerV2", "ABTaskLifecycle", "RestrictedAgentSpawner", "ABQualityGate",
        "get_ab_enforcer", "enforce_phase_complete", "enforce_tool_call",
        "enforce_quality_gate", "PermissionDenied", "SwapReviewError", "ReviewEvidenceRequired",
    ]
else:
    # Normal import path (package context)
    from .core import MethodologyCore, MethodologyConfig
    from .methodology_base import (
        ErrorLevel, ProcessType, AlertLevel, Error, Task, Agent,
        ErrorClassifier, ErrorHandler, TaskLifecycle, QualityGate, Crew, Monitor, Methodology,
    )
    from .dashboard import Dashboard
    from .auto_quality_gate import AutoQualityGate, QualityReport, QualityIssue
    from .smart_router import SmartRouter, TaskType, BudgetLevel, RoutingResult
    from .storage import Storage, Conversation, Message
    from .openclaw_adapter import (
        OpenClawAdapter, OpenClawConfig, AgentType, MultiAgentOrchestrator,
        create_musk_agent, create_researcher_agent, create_developer_agent
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
    from .dashboard_cost_trend import CostTrendAnalyzer, CostSnapshot, CostTrend, CostForecast
    from .failover_manager import FailoverManager, CircuitBreaker, ModelEndpoint, FailoverEvent
    from .parallel_executor import ParallelExecutor, ParallelTask, Worker, ExecutionResult
    from .extensions import Extensions, create_extensions
    from .cicd_integration import CICDIntegration, Pipeline, PipelineStep
    from .multi_language import MultiLanguageSupport, Language, LanguageConfig
    from .knowledge_base import KnowledgeBase, Pattern, BestPractice
    from .agent_spawner import AgentSpawner, SpawnConfig, SpawnedAgent, SpawnPolicy
    from .delivery_tracker import DeliveryTracker, Version as Version2, Artifact
    from .agent_lifecycle import AgentLifecycleViewer, AgentLifecycleState, AgentLifecycleInfo
    from .gantt_chart import GanttChart, GanttTask, TaskStatus as GanttTaskStatus
    from .resource_dashboard import ResourceDashboard, ResourceType, ResourceStatus, ResourceInfo
    from .sprint_planner import SprintPlanner, Story, StoryStatus, StorySize
    from .extension_configurator import ExtensionConfigurator, ExtensionType
    from .data_connector import (
        DataConnector, DataSourceType,
        PrometheusConnector, JiraConnector, OpenTelemetryConnector, DataSourceManager
    )
    from .agent_evaluator import (
        AgentEvaluator, HumanEvaluator, TestCase as EvalTestCase, EvaluationSuite,
        EvaluationResult, MetricType, EvaluationStatus,
    )
    from .structured_output import (
        StructuredOutputEngine, OutputSchema, FieldDefinition, ParseResult,
        OutputFormat, ParseStrategy,
    )
    from .data_quality import (
        DataQualityChecker, QualityReport as DQQualityReport, FieldProfile,
        QualityIssue as DQQualityIssue, QualityLevel, IssueType,
    )
    from .enterprise_hub import (
        EnterpriseHub, Authenticator, AuditLogger as HubAuditLogger, SlackMessenger,
        TeamsMessenger, User as HubUser, AuditEntry as HubAuditEntry, AuthProvider,
    )
    from .langgraph_migrator import (
        LangGraphMigrationTool, MigrationResult, PatternMapping, ASTNode, NodeType,
    )
    from .p2p_orchestrator import (
        P2POrchestrator, PeerAgent, P2PMessage, PendingRequest, P2PError,
    )
    from .traceability_matrix import (
        TraceabilityMatrix, TraceLink, TraceStatus, LinkType,
        TraceabilityMixin, get_traceability_matrix, reset_traceability_matrix,
    )
    from .ab_enforcer import (
        ABEnforcerV2, ABTaskLifecycle, RestrictedAgentSpawner, ABQualityGate,
        get_ab_enforcer, enforce_phase_complete, enforce_tool_call,
        enforce_quality_gate, PermissionDenied, SwapReviewError, ReviewEvidenceRequired,
    )

    # A unified __all__ covering everything
    __all__ = [
        # Core
        "MethodologyCore", "MethodologyConfig", "Methodology",
        # methodology_base
        "ErrorLevel", "ProcessType", "AlertLevel", "Error", "Task", "Agent",
        "ErrorClassifier", "ErrorHandler", "TaskLifecycle", "QualityGate", "Crew", "Monitor",
        # Dashboard
        "Dashboard",
        # Quality Gate
        "AutoQualityGate", "QualityReport", "QualityIssue",
        # Router
        "SmartRouter", "TaskType", "BudgetLevel", "RoutingResult",
        # Storage
        "Storage", "Conversation", "Message",
        # OpenClaw
        "OpenClawAdapter", "OpenClawConfig", "AgentType", "MultiAgentOrchestrator",
        "create_musk_agent", "create_researcher_agent", "create_developer_agent",
        # Task Splitter
        "TaskSplitter", "TaskStatus", "TaskPriority",
        # Task Splitter v2
        "TaskSplitterV2", "TaskV2", "Milestone",
        # Doc Generator
        "DocGenerator", "DocItem",
        # Test Generator
        "TestGenerator", "TestCase",
        # Predictive Monitor
        "PredictiveMonitor", "MetricPoint", "Prediction",
        # Workflow Templates
        "WorkflowTemplates", "WorkflowTemplate", "WorkflowType", "Sprint",
        # Progress Dashboard
        "ProgressDashboard", "PSprint", "BacklogItem",
        # RBAC
        "RBAC", "User", "Role", "Permission",
        # Scheduler
        "Scheduler", "Resource", "ScheduledTask", "SchedPriority",
        # Cost Allocator
        "CostAllocator", "CostEntry", "Budget", "CostType",
        # Audit Logger
        "AuditLogger", "AuditEntry", "ActionType", "ResourceType",
        # Risk Dashboard
        "RiskDashboard", "Risk", "RiskLevel", "RiskCategory",
        # Delivery Manager
        "DeliveryManager", "DeliveryItem", "Version", "DeliveryStatus",
        # Gap-filling modules
        "CostTrendAnalyzer", "CostSnapshot", "CostTrend", "CostForecast",
        "FailoverManager", "CircuitBreaker", "ModelEndpoint", "FailoverEvent",
        "ParallelExecutor", "ParallelTask", "Worker", "ExecutionResult",
        # Extensions
        "Extensions", "create_extensions",
        # PM Improvements
        "CICDIntegration", "Pipeline", "PipelineStep",
        "MultiLanguageSupport", "Language", "LanguageConfig",
        "KnowledgeBase", "Pattern", "BestPractice",
        "AgentSpawner", "SpawnConfig", "SpawnedAgent", "SpawnPolicy",
        "DeliveryTracker", "Artifact",
        # Phase 2
        "AgentLifecycleViewer", "AgentLifecycleState", "AgentLifecycleInfo",
        "GanttChart", "GanttTask",
        "ResourceDashboard", "ResourceType", "ResourceStatus", "ResourceInfo",
        # Phase 3
        "SprintPlanner", "Story", "StoryStatus", "StorySize",
        "ExtensionConfigurator", "ExtensionType",
        "DataConnector", "DataSourceType",
        "PrometheusConnector", "JiraConnector", "OpenTelemetryConnector", "DataSourceManager",
        # Solutions A-E
        "AgentEvaluator", "HumanEvaluator", "EvaluationSuite", "EvaluationResult",
        "MetricType", "EvaluationStatus",
        "StructuredOutputEngine", "OutputSchema", "FieldDefinition", "ParseResult",
        "OutputFormat", "ParseStrategy",
        "DataQualityChecker", "FieldProfile", "QualityLevel", "IssueType",
        "EnterpriseHub", "Authenticator", "AuditLogger", "SlackMessenger", "TeamsMessenger",
        "User", "AuditEntry", "AuthProvider",
        "LangGraphMigrationTool", "MigrationResult", "PatternMapping", "ASTNode", "NodeType",
        # P2P Orchestrator
        "P2POrchestrator", "PeerAgent", "P2PMessage", "PendingRequest", "P2PError",
        # Traceability Matrix
        "TraceabilityMatrix", "TraceLink", "TraceStatus", "LinkType",
        "TraceabilityMixin", "get_traceability_matrix", "reset_traceability_matrix",
        # A/B Enforcer v2.0
        "ABEnforcerV2", "ABTaskLifecycle", "RestrictedAgentSpawner", "ABQualityGate",
        "get_ab_enforcer", "enforce_phase_complete", "enforce_tool_call",
        "enforce_quality_gate", "PermissionDenied", "SwapReviewError", "ReviewEvidenceRequired",
    ]
