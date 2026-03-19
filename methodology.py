#!/usr/bin/env python3
"""
Methodology v2 - Multi-Agent Collaboration Development Methodology

Core classes for error classification, task lifecycle, and quality gates.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import time


class ErrorLevel(Enum):
    """錯誤等級"""
    L1 = "L1"  # 輸入錯誤
    L2 = "L2"  # 工具錯誤
    L3 = "L3"  # 執行錯誤
    L4 = "L4"  # 系統錯誤


class ProcessType(Enum):
    """Agent 協作模式"""
    SEQUENTIAL = "sequential"  # 串聯
    PARALLEL = "parallel"     # 並行
    HIERARCHICAL = "hierarchical"  # 階層


class AlertLevel(Enum):
    """警報等級"""
    CRITICAL = "critical"  # 健康 < 25
    WARNING = "warning"   # 健康 < 50
    INFO = "info"        # 健康 < 75


@dataclass
class Error:
    """錯誤"""
    message: str
    level: ErrorLevel
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict = field(default_factory=dict)


@dataclass
class Task:
    """任務"""
    id: str
    description: str
    agent_id: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Any = None
    error: Optional[Error] = None


@dataclass
class Agent:
    """Agent"""
    id: str
    role: str
    name: str
    status: str = "idle"  # idle, running, failed
    health_score: int = 100


# ============================================================================
# Error Classifier
# ============================================================================

class ErrorClassifier:
    """錯誤分類器"""
    
    # 錯誤模式對應
    PATTERNS = {
        ErrorLevel.L1: [
            "invalid input",
            "missing parameter",
            "format error",
            "validation error",
        ],
        ErrorLevel.L2: [
            "timeout",
            "connection error",
            "rate limit",
            "api error",
        ],
        ErrorLevel.L3: [
            "execution failed",
            "memory error",
            "timeout after",
            "runtime error",
        ],
        ErrorLevel.L4: [
            "system error",
            "out of memory",
            "disk full",
            "critical failure",
        ],
    }
    
    def classify(self, error: Exception) -> ErrorLevel:
        """分類錯誤"""
        msg = str(error).lower()
        
        for level, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if pattern in msg:
                    return level
        
        return ErrorLevel.L3  # 默認為 L3
    
    def classify_by_type(self, error_type: str) -> ErrorLevel:
        """根據錯誤類型分類"""
        error_type = error_type.lower()
        
        if "value" in error_type or "type" in error_type:
            return ErrorLevel.L1
        elif "timeout" in error_type or "connection" in error_type:
            return ErrorLevel.L2
        elif "runtime" in error_type or "execution" in error_type:
            return ErrorLevel.L3
        else:
            return ErrorLevel.L4


# ============================================================================
# Error Handler
# ============================================================================

class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.handlers = {
            ErrorLevel.L1: self._handle_l1,
            ErrorLevel.L2: self._handle_l2,
            ErrorLevel.L3: self._handle_l3,
            ErrorLevel.L4: self._handle_l4,
        }
    
    def handle(self, error: Exception, level: ErrorLevel = None) -> Any:
        """處理錯誤"""
        if level is None:
            level = self.classifier.classify(error)
        
        return self.handlers[level](error)
    
    def _handle_l1(self, error: Exception) -> Any:
        """L1: 立即返回錯誤"""
        return {"error": str(error), "level": "L1", "action": "return"}
    
    def _handle_l2(self, error: Exception) -> Any:
        """L2: 重試 3 次"""
        for attempt in range(3):
            try:
                # 重試邏輯
                return {"attempt": attempt + 1, "success": True}
            except Exception:
                if attempt == 2:
                    return {"error": str(error), "level": "L2", "action": "retry_failed"}
        return {"error": str(error), "level": "L2", "action": "max_retries"}
    
    def _handle_l3(self, error: Exception) -> Any:
        """L3: 降級處理"""
        return {"error": str(error), "level": "L3", "action": "fallback"}
    
    def _handle_l4(self, error: Exception) -> Any:
        """L4: 熔斷 + 警報"""
        return {"error": str(error), "level": "L4", "action": "circuit_break"}


# ============================================================================
# Task Lifecycle
# ============================================================================

class TaskLifecycle:
    """任務生命週期"""
    
    PHASES = ["需求", "規劃", "執行", "協調", "品質", "完成"]
    
    def __init__(self):
        self.current_phase = 0
    
    def execute(self, task: Task) -> Task:
        """執行任務"""
        task.status = "running"
        
        for phase in self.PHASES:
            self.current_phase += 1
            # 模擬各階段處理
            pass
        
        task.status = "completed"
        return task
    
    def get_phase(self) -> str:
        """獲取當前階段"""
        if self.current_phase < len(self.PHASES):
            return self.PHASES[self.current_phase]
        return "完成"


# ============================================================================
# Quality Gate
# ============================================================================

class QualityGate:
    """品質把關"""
    
    def __init__(self):
        self.checks = []
    
    def add_check(self, name: str, func: Callable) -> None:
        """新增檢查"""
        self.checks.append({"name": name, "func": func})
    
    def check(self, result: Any) -> bool:
        """檢查結果"""
        for check in self.checks:
            if not check["func"](result):
                return False
        return True
    
    def check_default(self, result: Any) -> bool:
        """預設檢查"""
        return result is not None and not isinstance(result, Exception)


# ============================================================================
# Crew (Agent 協作)
# ============================================================================

class Crew:
    """Agent 團隊"""
    
    def __init__(self, agents: List[Agent], process: str = "sequential"):
        self.agents = agents
        self.process = ProcessType(process)
        self.tasks: List[Task] = []
    
    def add_task(self, task: Task) -> None:
        """新增任務"""
        self.tasks.append(task)
    
    def kickoff(self) -> List[Task]:
        """執行"""
        if self.process == ProcessType.SEQUENTIAL:
            return self._execute_sequential()
        elif self.process == ProcessType.PARALLEL:
            return self._execute_parallel()
        else:
            return self._execute_hierarchical()
    
    def _execute_sequential(self) -> List[Task]:
        """串聯執行"""
        results = []
        for task in self.tasks:
            task.status = "completed"
            results.append(task)
        return results
    
    def _execute_parallel(self) -> List[Task]:
        """並行執行"""
        for task in self.tasks:
            task.status = "completed"
        return self.tasks
    
    def _execute_hierarchical(self) -> List[Task]:
        """階層執行"""
        # 簡化實現
        return self._execute_sequential()


# ============================================================================
# Monitor
# ============================================================================

class Monitor:
    """監控"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.alerts: List[Dict] = []
    
    def register_agent(self, agent: Agent) -> None:
        """註冊 Agent"""
        self.agents[agent.id] = agent
    
    def get_health_score(self, agent_id: str) -> int:
        """獲取健康評分"""
        agent = self.agents.get(agent_id)
        return agent.health_score if agent else 0
    
    def check_alerts(self) -> List[Dict]:
        """檢查警報"""
        self.alerts = []
        
        for agent in self.agents.values():
            if agent.health_score < 25:
                self.alerts.append({
                    "level": AlertLevel.CRITICAL,
                    "agent": agent.id,
                    "message": f"Agent {agent.id} health critical"
                })
            elif agent.health_score < 50:
                self.alerts.append({
                    "level": AlertLevel.WARNING,
                    "agent": agent.id,
                    "message": f"Agent {agent.id} health low"
                })
        
        return self.alerts


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Example usage
    
    # 1. Error Classification
    classifier = ErrorClassifier()
    level = classifier.classify_by_type("ValueError")
    print(f"Error level: {level.value}")
    
    # 2. Error Handling
    handler = ErrorHandler()
    result = handler.handle(ValueError("invalid input"))
    print(f"Handle result: {result}")
    
    # 3. Quality Gate
    gate = QualityGate()
    result = gate.check_default({"data": "test"})
    print(f"Quality check: {result}")
    
    # 4. Crew
    agents = [
        Agent(id="a1", role="dev", name="Developer"),
        Agent(id="a2", role="reviewer", name="Reviewer"),
    ]
    crew = Crew(agents, process="sequential")
    print(f"Crew process: {crew.process.value}")
    
    # 5. Monitor
    monitor = Monitor()
    monitor.register_agent(Agent(id="agent-001", role="coder", name="Coder", health_score=85))
    health = monitor.get_health_score("agent-001")
    print(f"Health score: {health}")
