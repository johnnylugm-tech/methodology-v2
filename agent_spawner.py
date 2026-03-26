#!/usr/bin/env python3
"""
Agent Spawner - Agent 標準化 Spawn 機制

標準化子 Agent 創建流程、數量限制、生命周期管理

参考 CrewAI 设计，新增 AgentPersona 支持
"""

import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


# ============================================================================
# CrewAI 风格 AgentPersona
# ============================================================================

@dataclass
class AgentPersona:
    """
    CrewAI 风格的 Agent 人格定义
    
    赋予 Agent 更丰富的角色内涵，而不仅仅是 role 名称
    """
    role: str           # "Researcher", "Writer", "Developer"
    goal: str           # "Find latest AI trends"
    backstory: str      # "You are a senior research analyst with 10 years experience..."
    
    def to_prompt(self) -> str:
        """转换为 LLM prompt"""
        return f"You are a {self.role}. Your goal is: {self.goal}. {self.backstory}"


# ============================================================================
# Spawn 策略
# ============================================================================

class SpawnPolicy(Enum):
    """Spawn 策略"""
    EAGER = "eager"           # 立即 spawn
    LAZY = "lazy"             # 延遲到需要時
    QUEUE = "queue"            # 排程 spawn
    CASCADING = "cascading"    # 級聯 spawn


class AgentState(Enum):
    """Agent 狀態"""
    PENDING = "pending"
    SPAWNING = "spawning"
    RUNNING = "running"
    IDLE = "idle"
    TERMINATED = "terminated"
    FAILED = "failed"


@dataclass
class SpawnConfig:
    """Spawn 配置"""
    max_agents: int = 10  # 最大 Agent 數
    max_per_role: Dict[str, int] = field(default_factory=lambda: {
        "developer": 5,
        "tester": 3,
        "reviewer": 2,
    })
    spawn_timeout: int = 60  # 秒
    idle_timeout: int = 300  # 秒
    retry_limit: int = 3


@dataclass
class SpawnRequest:
    """Spawn 請求"""
    role: str
    task_id: str
    task_description: str
    priority: int = 0
    policy: SpawnPolicy = SpawnPolicy.LAZY
    capabilities: List[str] = field(default_factory=list)
    
    # === CrewAI 风格新增 ===
    persona: Optional[AgentPersona] = None  # Agent 人格（可选）
    tools: List[Any] = field(default_factory=list)  # 工具列表（可选）


@dataclass
class SpawnedAgent:
    """已 Spawn 的 Agent"""
    agent_id: str
    role: str
    task_id: str
    state: AgentState
    spawned_at: datetime
    last_active: datetime
    parent_id: str = None


class AgentSpawner:
    """標準化 Spawn 管理器"""
    
    def __init__(self, config: SpawnConfig = None):
        self.config = config or SpawnConfig()
        
        # Spawned agents
        self.agents: Dict[str, SpawnedAgent] = {}
        
        # Queue
        self.queue: List[SpawnRequest] = []
        
        # Callbacks
        self.on_spawn: Callable = None
        self.on_terminate: Callable = None
        self.on_fail: Callable = None
    
    def request_spawn(self, request: SpawnRequest) -> bool:
        """
        請求 Spawn
        
        Args:
            request: Spawn 請求
            
        Returns:
            是否成功
        """
        # 檢查數量限制
        if not self._can_spawn(request.role):
            return False
        
        # 加入佇列
        self.queue.append(request)
        self.queue.sort(key=lambda r: -r.priority)
        
        # 如果是 EAGER 策略，立即 spawn
        if request.policy == SpawnPolicy.EAGER:
            return self._spawn_next(request.role)
        
        return True
    
    def _can_spawn(self, role: str) -> bool:
        """檢查是否可以 Spawn"""
        # 檢查總數
        active_count = sum(
            1 for a in self.agents.values()
            if a.state in [AgentState.RUNNING, AgentState.IDLE, AgentState.PENDING]
        )
        
        if active_count >= self.config.max_agents:
            return False
        
        # 檢查角色限制
        role_count = sum(
            1 for a in self.agents.values()
            if a.role == role and a.state != AgentState.TERMINATED
        )
        
        max_per_role = self.config.max_per_role.get(role, 5)
        if role_count >= max_per_role:
            return False
        
        return True
    
    def _spawn_next(self, role: str = None) -> Optional[str]:
        """Spawn 下一個"""
        # 找到最高優先級的請求
        request = None
        for i, req in enumerate(self.queue):
            if role and req.role != role:
                continue
            if self._can_spawn(req.role):
                request = self.queue.pop(i)
                break
        
        if not request:
            return None
        
        # 生成 Agent ID
        agent_id = f"agent-{request.role}-{len(self.agents) + 1}"
        
        # 建立 Agent
        agent = SpawnedAgent(
            agent_id=agent_id,
            role=request.role,
            task_id=request.task_id,
            state=AgentState.SPAWNING,
            spawned_at=datetime.now(),
            last_active=datetime.now(),
        )
        
        self.agents[agent_id] = agent
        
        # 模擬 Spawn 過程
        # 在實際系統中，這裡會呼叫 sessions_spawn
        try:
            # 觸發 Spawn 回調
            if self.on_spawn:
                self.on_spawn(agent)
            
            agent.state = AgentState.RUNNING
            agent.last_active = datetime.now()
            
            return agent_id
            
        except Exception as e:
            agent.state = AgentState.FAILED
            if self.on_fail:
                self.on_fail(agent, str(e))
            return None
    
    def spawn_with_retry(self, request: SpawnRequest) -> Optional[str]:
        """
        帶重試的 Spawn
        
        Args:
            request: Spawn 請求
            
        Returns:
            Agent ID 或 None
        """
        last_error = None
        
        for attempt in range(self.config.retry_limit):
            agent_id = self.request_spawn(request)
            
            if agent_id:
                return agent_id
            
            last_error = f"Attempt {attempt + 1} failed"
            time.sleep(1 * (attempt + 1))  # 指數退避
        
        return None
    
    def terminate(self, agent_id: str, reason: str = None) -> bool:
        """
        終止 Agent
        
        Args:
            agent_id: Agent ID
            reason: 終止原因
            
        Returns:
            是否成功
        """
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        agent.state = AgentState.TERMINATED
        
        if self.on_terminate:
            self.on_terminate(agent, reason)
        
        return True
    
    def terminate_idle_agents(self) -> int:
        """終止空閒的 Agent"""
        now = datetime.now()
        terminated = 0
        
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                idle_time = (now - agent.last_active).total_seconds()
                if idle_time > self.config.idle_timeout:
                    self.terminate(agent.agent_id, "Idle timeout")
                    terminated += 1
        
        return terminated
    
    def get_agent(self, agent_id: str) -> Optional[SpawnedAgent]:
        """取得 Agent"""
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role: str) -> List[SpawnedAgent]:
        """取得特定角色的所有 Agent"""
        return [
            a for a in self.agents.values()
            if a.role == role and a.state != AgentState.TERMINATED
        ]
    
    def get_available_agents(self, role: str = None) -> List[SpawnedAgent]:
        """取得可用的 Agent"""
        available = []
        
        for agent in self.agents.values():
            if agent.state != AgentState.RUNNING:
                continue
            
            if role and agent.role != role:
                continue
            
            # 檢查空閒時間
            idle_time = (datetime.now() - agent.last_active).total_seconds()
            if idle_time < 60:  # 60 秒內有活動
                available.append(agent)
        
        return available
    
    def update_activity(self, agent_id: str):
        """更新 Agent 活躍時間"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.last_active = datetime.now()
    
    def get_statistics(self) -> Dict:
        """取得統計"""
        total = len(self.agents)
        by_state = {}
        by_role = {}
        
        for agent in self.agents.values():
            state = agent.state.value
            by_state[state] = by_state.get(state, 0) + 1
            
            by_role[agent.role] = by_role.get(agent.role, 0) + 1
        
        return {
            "total_agents": total,
            "active": sum(1 for a in self.agents.values() 
                       if a.state in [AgentState.RUNNING, AgentState.IDLE]),
            "by_state": by_state,
            "by_role": by_role,
            "queue_size": len(self.queue),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        stats = self.get_statistics()
        
        report = f"""
# 🤖 Agent Spawner 報告

## 統計

| 指標 | 數值 |
|------|------|
| 總 Agent 數 | {stats['total_agents']} |
| 活躍 | {stats['active']} |
| 佇列大小 | {stats['queue_size']} |

---

## 按狀態

| 狀態 | 數量 |
|------|------|
"""
        
        for state, count in stats['by_state'].items():
            report += f"| {state} | {count} |\n"
        
        report += f"""

## 按角色

| 角色 | 數量 |
|------|------|
"""
        
        for role, count in stats['by_role'].items():
            report += f"| {role} | {count} |\n"
        
        return report


# ============================================================================
# spawn_with_persona - 帶人格的 Spawn
# ============================================================================

def _role_to_persona(role: str) -> str:
    """根據 role 自動選擇對應的 AgentPersona"""
    mapping = {
        "developer": "developer",
        "dev": "developer",
        "coder": "developer",
        "architect": "architect",
        "design": "architect",
        "reviewer": "reviewer",
        "review": "reviewer",
        "qa": "qa",
        "tester": "qa",
        "test": "qa",
        "pm": "pm",
        "product": "pm",
        "manager": "pm",
        "devops": "devops",
        "ops": "devops",
        "deployment": "devops",
    }
    return mapping.get(role.lower(), "developer")  # 預設為 developer


def spawn_with_persona(
    role: str,
    task: str,
    persona_type: str = None,
    **kwargs
) -> str:
    """
    Spawn Agent 並預設套用 AgentPersona

    Args:
        role: Agent 角色 (developer, reviewer, qa, etc.)
        task: 任務描述
        persona_type: 人格類型 (developer, architect, qa, pm, devops, reviewer)
        **kwargs: 其他 sessions_spawn 參數

    Returns:
        session_key: 新建的 session key
    """
    from agent_personas import generate_persona_prompt

    # 1. 如果有指定 persona_type，使用它
    if persona_type:
        system_prompt = generate_persona_prompt(persona_type, task)
    else:
        # 2. 否則根據 role 自動選擇預設人格
        persona_type = _role_to_persona(role)
        system_prompt = generate_persona_prompt(persona_type, task)

    # 3. 帶入 system_prompt 呼叫 sessions_spawn
    # 注意：這裡呼叫底層的 sessions_spawn（需由外部框架提供）
    # 如果沒有 sessions_spawn，則模擬返回一個 session key
    try:
        from openclaw import sessions_spawn
        return sessions_spawn(
            task=task,
            system_prompt=system_prompt,
            **kwargs
        )
    except ImportError:
        # Fallback: 返回模擬的 session key
        import uuid
        session_key = f"session-{role}-{uuid.uuid4().hex[:8]}"
        print(f"[spawn_with_persona] Simulated spawn: {session_key}")
        print(f"  role: {role}, persona: {persona_type}")
        print(f"  task: {task[:100]}..." if len(task) > 100 else f"  task: {task}")
        print(f"  system_prompt: {system_prompt[:200]}..." if len(system_prompt) > 200 else f"  system_prompt: {system_prompt}")
        return session_key


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    spawner = AgentSpawner()
    
    print("=== Spawn Requests ===")
    
    # 測試 Spawn
    request1 = SpawnRequest(
        role="developer",
        task_id="task-1",
        task_description="開發登入功能",
        priority=2,
        policy=SpawnPolicy.EAGER
    )
    
    request2 = SpawnRequest(
        role="tester",
        task_id="task-2",
        task_description="測試登入功能",
        priority=1,
        policy=SpawnPolicy.LAZY
    )
    
    agent1 = spawner.spawn_with_retry(request1)
    print(f"Spawned developer: {agent1}")
    
    agent2 = spawner.request_spawn(request2)
    print(f"Spawned tester: {agent2}")
    
    # 更新活躍
    spawner.update_activity(agent1)
    
    # 統計
    print("\n=== Statistics ===")
    stats = spawner.get_statistics()
    print(f"Total: {stats['total_agents']}")
    print(f"By role: {stats['by_role']}")
    print(f"Queue: {stats['queue_size']}")
    
    # 終止
    print("\n=== Terminate ===")
    spawner.terminate(agent1, "Task completed")
    print(f"Terminated: {agent1}")
    
    print("\n=== Report ===")
    print(spawner.generate_report())
