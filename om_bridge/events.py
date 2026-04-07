"""
事件定義 - OmO + Methodology-v2 Bridge
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime


class OMEvents(str, Enum):
    """OmO 發布的事件"""
    TASK_STARTED = "om.task.started"
    TASK_COMPLETED = "om.task.completed"
    TASK_FAILED = "om.task.failed"
    AGENT_STATUS = "om.agent.status"


class V2Events(str, Enum):
    """Methodology-v2 發布的事件"""
    TASK_PLANNED = "v2.task.planned"
    SPRINT_STARTED = "v2.sprint.started"
    QUALITY_CHECK = "v2.quality.check"
    ERROR_CLASSIFIED = "v2.error.classified"


@dataclass
class Event:
    """事件結構"""
    event_type: str
    data: dict
    timestamp: datetime = None
    source: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class OMTaskData:
    """OmO 任務資料"""
    task_id: str
    instructions: str
    language: Optional[str] = None
    preferred_model: Optional[str] = None


@dataclass
class OMTaskCompletedData:
    """OmO 任務完成資料"""
    task_id: str
    code: str
    result: Any
    language: str = "python"


@dataclass
class V2TaskPlannedData:
    """v2 任務規劃資料"""
    task_id: str
    instructions: str
    preferred_model: str = "claude-3-opus"
    estimated_hours: float = 1.0


@dataclass
class V2QualityCheckData:
    """v2 品質檢查資料"""
    task_id: str
    passed: bool
    score: float
    issues: list = None


@dataclass
class V2ErrorClassifiedData:
    """v2 錯誤分類資料"""
    error: Exception
    level: str  # L1, L2, L3, L4
    action: str
    message: str = None


# 事件匯流排話題
ALL_EVENTS = list(OMEvents) + list(V2Events)

__all__ = [
    "OMEvents",
    "V2Events", 
    "Event",
    "OMTaskData",
    "OMTaskCompletedData",
    "V2TaskPlannedData",
    "V2QualityCheckData",
    "V2ErrorClassifiedData",
    "ALL_EVENTS"
]
