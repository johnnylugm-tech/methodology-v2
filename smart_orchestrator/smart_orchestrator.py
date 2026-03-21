#!/usr/bin/env python3
"""
Smart Orchestrator - 智能任務協調器

協調多個 AI Agent 協作完成複雜任務：
- 任務規劃與分解
- Agent 調度與分配
- 狀態管理
- 結果聚合

Reference:
- Microsoft Multi-Agent Orchestration
- Deloitte AI Agent Orchestration
- Multi-Agent Systems in 2025
"""
import asyncio
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from collections import deque


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class AgentStatus(Enum):
    """Agent 狀態"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class Task:
    """任務"""
    id: str
    name: str
    description: str
    agent_type: str  # 需要的 Agent 類型
    input_data: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    assigned_agent: str = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None


@dataclass
class Agent:
    """Agent"""
    id: str
    name: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_task: str = None
    capabilities: List[str] = field(default_factory=list)
    load: float = 0.0  # 0-1 代表負載


@dataclass
class ExecutionPlan:
    """執行計劃"""
    task_id: str
    agent_id: str
    estimated_time_ms: int
    priority: int = 0


@dataclass
class OrchestrationResult:
    """協調結果"""
    success: bool
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_time_ms: float
    results: Dict[str, Any]


class SmartOrchestrator:
    """智能任務協調器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.execution_queue: deque = deque()
        self.results: Dict[str, Any] = {}
        self.event_log: List[Dict] = []
    
    # ========== Agent 管理 ==========
    
    def register_agent(self, agent_id: str, name: str, agent_type: str, capabilities: List[str] = None):
        """註冊 Agent"""
        self.agents[agent_id] = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            capabilities=capabilities or []
        )
        self._log("agent_registered", {"agent_id": agent_id, "type": agent_type})
    
    def get_available_agent(self, agent_type: str) -> Optional[Agent]:
        """取得可用 Agent"""
        available = [
            a for a in self.agents.values()
            if a.agent_type == agent_type and a.status == AgentStatus.IDLE
        ]
        
        if not available:
            return None
        
        # 選擇負載最低的
        return min(available, key=lambda a: a.load)
    
    def get_agent_types(self) -> List[str]:
        """取得所有 Agent 類型"""
        return list(set(a.agent_type for a in self.agents.values()))
    
    # ========== Task 管理 ==========
    
    def create_task(
        self,
        name: str,
        description: str,
        agent_type: str,
        input_data: Dict = None,
        dependencies: List[str] = None
    ) -> str:
        """建立任務"""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = Task(
            id=task_id,
            name=name,
            description=description,
            agent_type=agent_type,
            input_data=input_data or {},
            dependencies=dependencies or []
        )
        self._log("task_created", {"task_id": task_id, "name": name})
        return task_id
    
    def add_tasks(self, tasks: List[Dict]) -> List[str]:
        """批量添加任務"""
        task_ids = []
        for t in tasks:
            task_ids.append(self.create_task(
                name=t["name"],
                description=t.get("description", ""),
                agent_type=t["agent_type"],
                input_data=t.get("input_data", {}),
                dependencies=t.get("dependencies", [])
            ))
        return task_ids
    
    def can_execute(self, task: Task) -> bool:
        """檢查任務是否可以執行"""
        if task.status != TaskStatus.PENDING:
            return False
        
        # 檢查依賴
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                continue
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    # ========== 執行 ==========
    
    async def execute(self, tasks: List[str] = None) -> OrchestrationResult:
        """執行任務"""
        start_time = datetime.now()
        
        # 如果沒有指定，執行所有 pending 任務
        if tasks is None:
            tasks = [t.id for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        
        completed = 0
        failed = 0
        
        while True:
            # 找到可執行的任務
            executable = [t for t in self.tasks.values() 
                        if t.id in tasks and self.can_execute(t)]
            
            if not executable:
                break
            
            # 限制並發數
            if len([a for a in self.agents.values() if a.status == AgentStatus.BUSY]) >= self.max_concurrent:
                await asyncio.sleep(0.1)
                continue
            
            # 分配任務
            for task in executable[:self.max_concurrent]:
                agent = self.get_available_agent(task.agent_type)
                
                if agent:
                    await self._execute_task(task, agent)
                    if task.status == TaskStatus.COMPLETED:
                        completed += 1
                    elif task.status == TaskStatus.FAILED:
                        failed += 1
                else:
                    # 沒有可用 Agent，等待
                    task.status = TaskStatus.WAITING
        
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return OrchestrationResult(
            success=failed == 0,
            total_tasks=len(tasks),
            completed_tasks=completed,
            failed_tasks=failed,
            total_time_ms=total_time,
            results=self.results
        )
    
    async def _execute_task(self, task: Task, agent: Agent):
        """執行單一任務"""
        task.status = TaskStatus.RUNNING
        task.assigned_agent = agent.id
        task.started_at = datetime.now()
        agent.status = AgentStatus.BUSY
        agent.current_task = task.id
        agent.load = min(1.0, agent.load + 0.3)
        
        self._log("task_started", {"task_id": task.id, "agent": agent.name})
        
        try:
            # 模擬執行（實際應該調用 Agent）
            await asyncio.sleep(0.1)  # 模擬執行時間
            
            # 這裡應該調用實際的 Agent 函數
            # result = await agent.func(task.input_data)
            
            # 模擬結果
            task.result = {"status": "ok", "task_id": task.id}
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.results[task.id] = task.result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            agent.status = AgentStatus.ERROR
        
        finally:
            agent.load = max(0, agent.load - 0.3)
            if agent.load == 0:
                agent.status = AgentStatus.IDLE
            agent.current_task = None
        
        self._log("task_completed", {
            "task_id": task.id, 
            "status": task.status.value
        })
    
    # ========== 工具 ==========
    
    def get_task_graph(self) -> Dict:
        """取得任務圖"""
        graph = {"nodes": [], "edges": []}
        
        for task in self.tasks.values():
            graph["nodes"].append({
                "id": task.id,
                "label": task.name,
                "status": task.status.value,
                "agent_type": task.agent_type
            })
            
            for dep in task.dependencies:
                graph["edges"].append({"from": dep, "to": task.id})
        
        return graph
    
    def get_status(self) -> Dict:
        """取得狀態"""
        return {
            "agents": {
                a.id: {"name": a.name, "status": a.status.value, "load": a.load}
                for a in self.agents.values()
            },
            "tasks": {
                t.id: {"name": t.name, "status": t.status.value}
                for t in self.tasks.values()
            },
            "queue_size": len(self.execution_queue)
        }
    
    def _log(self, event: str, data: Dict):
        """記錄事件"""
        self.event_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data
        })


# 便捷函數
async def orchestrate_workflow(
    workflow: Dict[str, Any],
    agents: Dict[str, Callable]
) -> OrchestrationResult:
    """
    協調工作流
    
    Example:
    workflow = {
        "tasks": [
            {"name": "research", "agent_type": "researcher"},
            {"name": "analyze", "agent_type": "analyst", "dependencies": ["research"]},
            {"name": "write", "agent_type": "writer", "dependencies": ["analyze"]},
        ]
    }
    
    agents = {
        "researcher": researcher_agent,
        "analyst": analyst_agent,
        "writer": writer_agent,
    }
    """
    orchestrator = SmartOrchestrator()
    
    # 註冊 agents
    for agent_type, func in agents.items():
        orchestrator.register_agent(
            agent_id=agent_type,
            name=agent_type.capitalize(),
            agent_type=agent_type
        )
    
    # 添加任務
    orchestrator.add_tasks(workflow.get("tasks", []))
    
    # 執行
    return await orchestrator.execute()


# 測試
if __name__ == "__main__":
    async def test():
        print("=== Smart Orchestrator Test ===")
        
        # 創建協調器
        orchestrator = SmartOrchestrator(max_concurrent=2)
        
        # 註冊 Agents
        orchestrator.register_agent("researcher", "研究 Agent", "research")
        orchestrator.register_agent("analyst", "分析 Agent", "analysis")
        orchestrator.register_agent("writer", "寫作 Agent", "writing")
        
        # 建立任務
        task1 = orchestrator.create_task(
            "研究 AI 趨勢", "研究最新 AI 趨勢", "research"
        )
        
        task2 = orchestrator.create_task(
            "分析數據", "分析研究結果", "analysis",
            dependencies=[task1]
        )
        
        task3 = orchestrator.create_task(
            "撰寫報告", "撰寫最終報告", "writing",
            dependencies=[task2]
        )
        
        print(f"任務數: {len(orchestrator.tasks)}")
        
        # 執行
        result = await orchestrator.execute()
        
        print(f"\n結果:")
        print(f"  成功: {result.success}")
        print(f"  完成: {result.completed_tasks}/{result.total_tasks}")
        print(f"  時間: {result.total_time_ms:.2f}ms")
        
        print(f"\n狀態:")
        print(orchestrator.get_status())
    
    asyncio.run(test())
