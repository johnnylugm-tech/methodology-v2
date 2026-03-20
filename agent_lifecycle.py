#!/usr/bin/env python3
"""
Agent Lifecycle Viewer - Agent 生命週期視圖

視覺化 Agent 的完整生命週期：Spawn → Ready → Running → Idle → Terminated
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class AgentLifecycleState(Enum):
    """Agent 生命週期狀態"""
    SPAWNING = "spawning"      # 正在創建
    READY = "ready"            # 就緒待命
    RUNNING = "running"        # 執行任務中
    IDLE = "idle"              # 空閒等待
    WAITING = "waiting"        # 等待資源/依賴
    TERMINATED = "terminated"  # 已終止
    FAILED = "failed"          # 執行失敗


@dataclass
class LifecycleTransition:
    """狀態轉換記錄"""
    from_state: AgentLifecycleState
    to_state: AgentLifecycleState
    timestamp: datetime
    reason: str = ""
    task_id: str = None


@dataclass
class AgentLifecycleInfo:
    """Agent 生命週期資訊"""
    agent_id: str
    name: str
    role: str
    
    # 當前狀態
    current_state: AgentLifecycleState = AgentLifecycleState.SPAWNING
    
    # 時間戳
    spawned_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    ended_at: datetime = None
    
    # 當前任務
    current_task: str = None
    current_task_start: datetime = None
    
    # 統計
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_runtime: timedelta = field(default_factory=lambda: timedelta(0))
    
    # 狀態歷史
    transitions: List[LifecycleTransition] = field(default_factory=list)
    
    # 資源使用
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    
    @property
    def state_duration(self) -> timedelta:
        """當前狀態持續時間"""
        start = self.started_at or self.spawned_at
        if self.current_state == AgentLifecycleState.RUNNING:
            return datetime.now() - start
        elif self.ended_at:
            return self.ended_at - start
        return datetime.now() - start
    
    @property
    def uptime(self) -> str:
        """運行時間格式化"""
        delta = datetime.now() - self.spawned_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m"


class AgentLifecycleViewer:
    """
    Agent 生命週期視圖
    
    使用方式：
    
    ```python
    from methodology import AgentLifecycleViewer
    
    viewer = AgentLifecycleViewer()
    
    # 註冊 Agent
    viewer.register("dev-1", "Developer", "developer")
    
    # 更新狀態
    viewer.transition("dev-1", AgentLifecycleState.READY)
    viewer.transition("dev-1", AgentLifecycleState.RUNNING, task_id="task-123")
    
    # 獲取視圖
    view = viewer.get_lifecycle_view("dev-1")
    print(view)
    
    # 獲取所有 Agent 狀態
    status = viewer.get_all_status()
    print(status)
    
    # 生成 Mermaid 圖
    mermaid = viewer.to_mermaid()
    ```
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentLifecycleInfo] = {}
    
    def register(self, agent_id: str, name: str, role: str) -> AgentLifecycleInfo:
        """
        註冊新 Agent
        
        Args:
            agent_id: Agent ID
            name: Agent 名稱
            role: Agent 角色
            
        Returns:
            AgentLifecycleInfo 實例
        """
        info = AgentLifecycleInfo(
            agent_id=agent_id,
            name=name,
            role=role,
            current_state=AgentLifecycleState.SPAWNING,
            spawned_at=datetime.now()
        )
        
        self.agents[agent_id] = info
        
        # 記錄初始狀態
        self._record_transition(agent_id, None, AgentLifecycleState.SPAWNING, "Agent created")
        
        # 自動轉到 READY
        self.transition(agent_id, AgentLifecycleState.READY, "Initialization complete")
        
        return info
    
    def transition(self, agent_id: str, new_state: AgentLifecycleState,
                  reason: str = "", task_id: str = None) -> bool:
        """
        Agent 狀態轉換
        
        Args:
            agent_id: Agent ID
            new_state: 新狀態
            reason: 轉換原因
            task_id: 相關任務 ID
            
        Returns:
            是否成功
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        old_state = agent.current_state
        
        # 更新狀態
        agent.current_state = new_state
        
        # 記錄時間
        if new_state == AgentLifecycleState.RUNNING:
            agent.started_at = datetime.now()
            if task_id:
                agent.current_task = task_id
                agent.current_task_start = datetime.now()
        
        elif new_state == AgentLifecycleState.TERMINATED:
            agent.ended_at = datetime.now()
            agent.current_task = None
        
        elif new_state == AgentLifecycleState.FAILED:
            agent.ended_at = datetime.now()
            agent.tasks_failed += 1
            agent.current_task = None
        
        # 記錄轉換
        self._record_transition(agent_id, old_state, new_state, reason, task_id)
        
        return True
    
    def _record_transition(self, agent_id: str, from_state: AgentLifecycleState,
                         to_state: AgentLifecycleState, reason: str, task_id: str = None):
        """記錄狀態轉換"""
        transition = LifecycleTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(),
            reason=reason,
            task_id=task_id
        )
        self.agents[agent_id].transitions.append(transition)
    
    def task_started(self, agent_id: str, task_id: str, task_name: str):
        """任務開始"""
        self.transition(agent_id, AgentLifecycleState.RUNNING,
                       f"Starting task: {task_name}", task_id)
    
    def task_completed(self, agent_id: str, success: bool = True):
        """任務完成"""
        agent = self.agents.get(agent_id)
        if not agent:
            return
        
        if success:
            agent.tasks_completed += 1
            self.transition(agent_id, AgentLifecycleState.IDLE, "Task completed")
        else:
            agent.tasks_failed += 1
            self.transition(agent_id, AgentLifecycleState.FAILED, "Task failed")
        
        agent.current_task = None
        agent.current_task_start = None
    
    def terminate(self, agent_id: str, reason: str = "Normal shutdown"):
        """終止 Agent"""
        self.transition(agent_id, AgentLifecycleState.TERMINATED, reason)
    
    def get_lifecycle_view(self, agent_id: str) -> Dict:
        """
        取得 Agent 的完整生命週期視圖
        
        Args:
            agent_id: Agent ID
            
        Returns:
            生命週期視圖
        """
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "current_state": agent.current_state.value,
            "uptime": agent.uptime,
            "state_duration_seconds": agent.state_duration.total_seconds(),
            "current_task": agent.current_task,
            "tasks_completed": agent.tasks_completed,
            "tasks_failed": agent.tasks_failed,
            "transitions": [
                {
                    "from": t.from_state.value if t.from_state else "none",
                    "to": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "reason": t.reason
                }
                for t in agent.transitions[-10:]  # 最近 10 次
            ]
        }
    
    def get_all_status(self) -> Dict:
        """
        取得所有 Agent 的狀態概覽
        
        Returns:
            狀態概覽
        """
        states = {}
        for state in AgentLifecycleState:
            states[state.value] = []
        
        for agent_id, agent in self.agents.items():
            states[agent.current_state.value].append({
                "agent_id": agent_id,
                "name": agent.name,
                "role": agent.role,
                "task": agent.current_task,
                "uptime": agent.uptime
            })
        
        return {
            "total": len(self.agents),
            "by_state": {
                state.value: len(agents) 
                for state, agents in states.items()
            },
            "agents": states
        }
    
    def to_mermaid(self) -> str:
        """
        生成 Mermaid 狀態圖
        
        Returns:
            Mermaid 圖表代碼
        """
        lines = ["stateDiagram-v2"]
        lines.append("    [*] --> Spawning")
        lines.append("    Spawning --> Ready: Initialization complete")
        lines.append("    Ready --> Running: Task assigned")
        lines.append("    Running --> Idle: Task completed")
        lines.append("    Running --> Failed: Task failed")
        lines.append("    Idle --> Running: New task")
        lines.append("    Idle --> Terminated: Shutdown")
        lines.append("    Ready --> Terminated: Failed to start")
        lines.append("    Failed --> Ready: Retry")
        lines.append("    Ready --> Waiting: Waiting for resources")
        lines.append("    Waiting --> Ready: Resources available")
        
        # 添加當前狀態標記
        for agent_id, agent in self.agents.items():
            lines.append("")
            lines.append(f"    note right of {agent.agent_id}")
            lines.append(f"        Current: {agent.current_state.value}")
            lines.append(f"        Task: {agent.current_task or 'None'}")
            lines.append(f"        Completed: {agent.tasks_completed}")
            lines.append("    end note")
        
        return "\n".join(lines)
    
    def to_ascii_diagram(self) -> str:
        """
        生成 ASCII 狀態圖
        
        Returns:
            ASCII 圖表
        """
        lines = [
            "=" * 60,
            "Agent Lifecycle Diagram",
            "=" * 60,
            "",
            "  Spawning --> Ready --> Running --> Idle --> Terminated",
            "                |         |",
            "                v         v",
            "             Waiting   Failed --> Ready",
            "",
        ]
        
        # 當前狀態
        lines.append("Current Status:")
        lines.append("-" * 40)
        
        for agent_id, agent in self.agents.items():
            lines.append(f"  {agent.name} ({agent.role})")
            lines.append(f"    State: {agent.current_state.value}")
            lines.append(f"    Task: {agent.current_task or 'None'}")
            lines.append(f"    Uptime: {agent.uptime}")
            lines.append("")
        
        return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    viewer = AgentLifecycleViewer()
    
    # 註冊 Agents
    viewer.register("dev-1", "Backend Developer", "developer")
    viewer.register("dev-2", "Frontend Developer", "developer")
    viewer.register("test-1", "QA Engineer", "tester")
    
    # 模擬生命週期
    print("=== Agent Lifecycle Demo ===\n")
    
    # Dev-1 工作
    viewer.task_started("dev-1", "task-1", "Implement login API")
    print("Dev-1 started task-1")
    
    viewer.task_completed("dev-1", success=True)
    print("Dev-1 completed task-1, now idle")
    
    # Dev-2 工作
    viewer.task_started("dev-2", "task-2", "Build login UI")
    print("Dev-2 started task-2")
    
    # Test-1 等待
    viewer.transition("test-1", AgentLifecycleState.WAITING, "Waiting for dev-1")
    print("Test-1 waiting for resources")
    
    print("\n" + "=" * 40)
    print("ASCII Diagram:")
    print("=" * 40)
    print(viewer.to_ascii_diagram())
    
    print("\nMermaid Diagram:")
    print("=" * 40)
    print(viewer.to_mermaid())
    
    print("\nAll Status:")
    print("=" * 40)
    import json
    print(json.dumps(viewer.get_all_status(), indent=2, default=str))
