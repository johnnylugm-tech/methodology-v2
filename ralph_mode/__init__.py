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
]

__version__ = "1.0.0"
