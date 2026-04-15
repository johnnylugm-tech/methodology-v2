"""
Ralph Mode - 任務長時監控模組

Ralph Mode 為長時任務提供狀態持久化、定時輪詢、階段狀態機和進度追蹤功能。
適用於需要長時間運行的批次任務監控。

Author: methodology-v2
Version: 1.0.0
"""

from .task_persistence import TaskState, TaskPersistence
from .scheduler import RalphScheduler, SchedulerConfig, SchedulerManager
from .state_machine import PhaseStateMachine, PhaseStatus
from .progress_tracker import RalphProgressTracker
from .schema_validator import SessionsSpawnLogValidator, ValidationResult, RalphSchemaError, ParsedEntry
from .alert_manager import AlertManager, AlertLevel, AlertMessage, get_default_manager, send_alert
from .task_parser import TaskOutputParser
from .output_verifier import OutputVerifier, VerificationResult
from .lifecycle import RalphLifecycleManager, EndReason, CheckResult

__all__ = [
    # Task State
    "TaskState",
    "TaskPersistence",
    # Scheduler
    "RalphScheduler",
    "SchedulerConfig",
    "SchedulerManager",
    # State Machine
    "PhaseStateMachine",
    "PhaseStatus",
    # Progress Tracker
    "RalphProgressTracker",
    # Schema Validator (v1.0)
    "SessionsSpawnLogValidator",
    "ValidationResult",
    "RalphSchemaError",
    "ParsedEntry",
    # Alert Manager (v1.0)
    "AlertManager",
    "AlertLevel",
    "AlertMessage",
    "get_default_manager",
    "send_alert",
    # Task Parser (v1.0)
    "TaskOutputParser",
    # Output Verifier (v1.0)
    "OutputVerifier",
    "VerificationResult",
    # Lifecycle Manager (v1.0)
    "RalphLifecycleManager",
    "EndReason",
    "CheckResult",
]

__version__ = "1.1.0"
