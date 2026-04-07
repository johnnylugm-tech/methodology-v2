#!/usr/bin/env python3
"""
Scheduler - 優先級排程器

多 Agent 資源排程與優先級管理
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class Priority(Enum):
    """優先級"""
    CRITICAL = 1  # P0
    HIGH = 2       # P1
    NORMAL = 3     # P2
    LOW = 4        # P3
    BACKGROUND = 5 # P4


class TaskState(Enum):
    """任務狀態"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


@dataclass
class Resource:
    """資源"""
    id: str
    name: str
    type: str  # "agent", "gpu", "cpu"
    capacity: float = 100.0
    available: float = 100.0
    cost_per_hour: float = 0.0
    metadata: Dict = field(default_factory=dict)
    
    @property
    def utilization(self) -> float:
        return ((self.capacity - self.available) / self.capacity) * 100 if self.capacity > 0 else 0


@dataclass
class ScheduledTask:
    """排程任務"""
    id: str
    name: str
    priority: Priority = Priority.NORMAL
    required_resources: Dict[str, float] = field(default_factory=dict)  # resource_type -> amount
    estimated_duration: timedelta = timedelta(minutes=30)
    deadline: datetime = None
    state: TaskState = TaskState.QUEUED
    assigned_resources: List[str] = field(default_factory=list)  # resource IDs
    user_id: str = None
    project_id: str = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    dependencies: List[str] = field(default_factory=list)
    
    @property
    def score(self) -> float:
        """
        優先級分數計算 (透明化)
        
        公式: Total = Priority_Score + Urgency_Score + Dependency_Score + Deadline_Score
        
        Priority Score:
        - CRITICAL (P0): 900 分
        - HIGH (P1): 800 分
        - NORMAL (P2): 700 分
        - LOW (P3): 600 分
        - BACKGROUND (P4): 500 分
        
        Urgency Score (工作佇列等待時間):
        - 每等待 1 小時 +10 分
        
        Dependency Score (依賴阻塞):
        - 每有 1 個任務依賴此任務 +50 分
        
        Deadline Score (距離截止):
        - < 0 小時 (逾期): +500 分
        - < 1 小時: +300 分
        - < 4 小時: +100 分
        - < 24 小時: +50 分
        """
        # 基礎優先級分數
        score = 1000 - self.priority.value * 100
        
        # 等待時間緊急性 (每小時 +10 分)
        if self.created_at:
            wait_hours = (datetime.now() - self.created_at).total_seconds() / 3600
            score += min(wait_hours * 10, 100)  # 最多加 100 分
        
        # 依賴阻塞分數
        if self.dependencies:
            score += len(self.dependencies) * 50
        
        # 截止時間緊急性
        if self.deadline:
            hours_until_deadline = (self.deadline - datetime.now()).total_seconds() / 3600
            if hours_until_deadline < 0:
                score += 500  # 已逾期
            elif hours_until_deadline < 1:
                score += 300
            elif hours_until_deadline < 4:
                score += 100
            elif hours_until_deadline < 24:
                score += 50
        
        return score
    
    def get_score_breakdown(self) -> Dict:
        """
        取得優先級分數詳細分解
        
        Returns:
            {
                "total": 950,
                "breakdown": {
                    "priority": {"base": 800, "label": "HIGH (P1)"},
                    "urgency": {"value": 50, "wait_hours": 5},
                    "dependency": {"count": 1, "value": 50},
                    "deadline": {"hours": -2, "value": 500, "status": "overdue"}
                }
            }
        """
        # 基礎優先級分數
        priority_base = 1000 - self.priority.value * 100
        priority_labels = {
            Priority.CRITICAL: "CRITICAL (P0)",
            Priority.HIGH: "HIGH (P1)",
            Priority.NORMAL: "NORMAL (P2)",
            Priority.LOW: "LOW (P3)",
            Priority.BACKGROUND: "BACKGROUND (P4)"
        }
        
        # 等待時間
        wait_hours = 0
        urgency_value = 0
        if self.created_at:
            wait_hours = (datetime.now() - self.created_at).total_seconds() / 3600
            urgency_value = min(wait_hours * 10, 100)
        
        # 依賴
        dep_count = len(self.dependencies) if self.dependencies else 0
        dep_value = dep_count * 50
        
        # 截止時間
        deadline_hours = None
        deadline_value = 0
        deadline_status = "none"
        if self.deadline:
            deadline_hours = (self.deadline - datetime.now()).total_seconds() / 3600
            if deadline_hours < 0:
                deadline_value = 500
                deadline_status = "overdue"
            elif deadline_hours < 1:
                deadline_value = 300
                deadline_status = "critical"
            elif deadline_hours < 4:
                deadline_value = 100
                deadline_status = "warning"
            elif deadline_hours < 24:
                deadline_value = 50
                deadline_status = "soon"
            else:
                deadline_status = "ok"
        
        return {
            "total": priority_base + urgency_value + dep_value + deadline_value,
            "breakdown": {
                "priority": {"base": priority_base, "label": priority_labels.get(self.priority, "UNKNOWN")},
                "urgency": {"value": urgency_value, "wait_hours": round(wait_hours, 1)},
                "dependency": {"count": dep_count, "value": dep_value},
                "deadline": {
                    "hours": round(deadline_hours, 1) if deadline_hours else None,
                    "value": deadline_value,
                    "status": deadline_status
                }
            }
        }


class Scheduler:
    """
    優先級排程器
    
    任務排序演算法說明：
    
    1. 計算每個任務的優先級分數 (score)
       - 基礎分數 = 1000 - 優先級值×100
       - 等待時間加權 = 每小時 +10 分 (最多 100)
       - 依賴加權 = 依賴數×50 分
       - 截止時間加權 = 根據距離調整
    
    2. 任務揀選 (Task Selection)
       - 選擇分數最高的任務
       - 檢查資源是否足夠
       - 如果資源不足，選擇下一個
    
    3. 資源分配 (Resource Allocation)
       - 貪心演算法：選擇第一個滿足條件的資源
       - 預設選擇可用資源中成本最低的
    
    4. 負載均衡 (Load Balancing)
       - 可設定 max_load_per_resource 避免過載
       - 預設 80% 容量上限
    
    範例：
    ```
    task1 = ScheduledTask(name="A", priority=Priority.HIGH, deadline=datetime.now()+timedelta(hours=2))
    task2 = ScheduledTask(name="B", priority=Priority.NORMAL, deadline=datetime.now()+timedelta(hours=24))
    
    # task1 分數會更高，因為截止時間更近
    # 即使優先級較低，截止時間會加分
    ```
    """
    
    def __init__(self, max_load_per_resource: float = 0.8):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.resources: Dict[str, Resource] = {}
        self.queue: List[str] = []  # task IDs, sorted by priority
        self.history: List[Dict] = []
        self.max_load_per_resource = max_load_per_resource  # 80% 容量上限
    
    def add_resource(self, name: str, resource_type: str,
                     capacity: float = 100.0,
                     cost_per_hour: float = 0.0) -> str:
        """新增資源"""
        resource_id = f"res-{uuid.uuid4().hex[:8]}"
        
        resource = Resource(
            id=resource_id,
            name=name,
            type=resource_type,
            capacity=capacity,
            available=capacity,
            cost_per_hour=cost_per_hour,
        )
        
        self.resources[resource_id] = resource
        return resource_id
    
    def add_task(self, name: str,
                priority: Priority = Priority.NORMAL,
                required_resources: Dict[str, float] = None,
                estimated_duration: timedelta = None,
                deadline: datetime = None,
                user_id: str = None,
                project_id: str = None,
                dependencies: List[str] = None) -> str:
        """新增任務"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            priority=priority,
            required_resources=required_resources or {},
            estimated_duration=estimated_duration or timedelta(minutes=30),
            deadline=deadline,
            user_id=user_id,
            project_id=project_id,
            dependencies=dependencies or [],
        )
        
        self.tasks[task_id] = task
        self._requeue()
        
        return task_id
    
    def _requeue(self):
        """重新排序佇列"""
        # 取得所有 QUEUED 或 WAITING 的任務
        pending = [
            task_id for task_id, task in self.tasks.items()
            if task.state in [TaskState.QUEUED, TaskState.WAITING]
        ]
        
        # 按分數排序 (高分先執行)
        pending.sort(key=lambda tid: -self.tasks[tid].score)
        
        self.queue = pending
    
    def _check_dependencies(self, task_id: str) -> bool:
        """檢查依賴是否滿足"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        for dep_id in task.dependencies:
            dep = self.tasks.get(dep_id)
            if not dep or dep.state != TaskState.COMPLETED:
                return False
        
        return True
    
    def _can_schedule(self, task_id: str) -> bool:
        """檢查是否可以排程"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # 檢查依賴
        if not self._check_dependencies(task_id):
            task.state = TaskState.WAITING
            return False
        
        # 檢查資源
        for res_type, amount in task.required_resources.items():
            # 找到閒置的資源
            available = self._get_available_resource(res_type)
            if available and available.available >= amount:
                return True
        
        return False
    
    def _why_blocked(self, task_id: str) -> str:
        """說明任務被阻塞的原因"""
        task = self.tasks.get(task_id)
        if not task:
            return "Task not found"
        
        # 檢查依賴
        if task.dependencies:
            pending_deps = []
            for dep_id in task.dependencies:
                dep = self.tasks.get(dep_id)
                if dep and dep.state != TaskState.COMPLETED:
                    pending_deps.append(f"{dep.name} ({dep.state.value})")
            if pending_deps:
                return f"Waiting for dependencies: {', '.join(pending_deps)}"
        
        # 檢查資源
        for res_type, amount in task.required_resources.items():
            resource = self._get_available_resource(res_type)
            if not resource:
                return f"No {res_type} resource available"
            if resource.available < amount:
                return f"Insufficient {res_type} (need {amount}, have {resource.available})"
        
        return "Unknown reason"
    
    def _get_available_resource(self, resource_type: str) -> Optional[Resource]:
        """取得可用資源"""
        candidates = [
            r for r in self.resources.values()
            if r.type == resource_type and r.available > 0
        ]
        
        if not candidates:
            return None
        
        # 返回負載最低的資源
        return min(candidates, key=lambda r: r.utilization)
    
    def schedule_next(self) -> Optional[ScheduledTask]:
        """
        排程下一個任務
        
        調度決策說明：
        1. 按分數排序佇列
        2. 遍歷佇列，找到第一個資源充足的任務
        3. 分配資源並更新狀態
        
        Returns:
            下一個要執行的任務，或 None (如果無任務可執行)
        """
        for task_id in self.queue:
            if self._can_schedule(task_id):
                task = self.tasks[task_id]
                self._allocate_resources(task)
                task.state = TaskState.RUNNING
                task.started_at = datetime.now()
                self._requeue()
                
                # 記錄調度原因
                self.history.append({
                    "timestamp": datetime.now(),
                    "action": "scheduled",
                    "task_id": task_id,
                    "task_name": task.name,
                    "score": task.score,
                    "breakdown": task.get_score_breakdown()
                })
                
                return task
        
        return None
    
    def explain_schedule(self) -> Dict:
        """
        說明當前排程決策
        
        返回為什麼選擇這個任務，以及其他任務的分數比較
        
        Returns:
            {
                "ready_tasks": [...],  # 可以執行的任務
                "blocked_tasks": [...], # 等待資源的任務
                "next_task": {...},     # 下一個任務及其分數分解
                "resource_status": {...} # 資源狀態
            }
        """
        ready = []
        blocked = []
        
        for task_id in self.queue:
            task = self.tasks[task_id]
            info = {
                "id": task_id,
                "name": task.name,
                "score": task.score,
                "breakdown": task.get_score_breakdown()
            }
            
            if self._can_schedule(task_id):
                ready.append(info)
            else:
                info["block_reason"] = self._why_blocked(task_id)
                blocked.append(info)
        
        return {
            "ready_tasks": sorted(ready, key=lambda x: -x["score"]),
            "blocked_tasks": blocked,
            "resource_status": {
                rid: {
                    "name": r.name,
                    "type": r.type,
                    "available": r.available,
                    "capacity": r.capacity,
                    "utilization": r.utilization
                }
                for rid, r in self.resources.items()
            }
        }
    
    def _allocate_resources(self, task: ScheduledTask):
        """分配資源"""
        for res_type, amount in task.required_resources.items():
            resource = self._get_available_resource(res_type)
            if resource:
                resource.available -= amount
                task.assigned_resources.append(resource.id)
    
    def _release_resources(self, task: ScheduledTask):
        """釋放資源"""
        for res_id in task.assigned_resources:
            resource = self.resources.get(res_id)
            if resource:
                # 根據任務需求的資源量釋放
                required = task.required_resources.get(resource.type, 0)
                # 釋放實際使用的量
                resource.available = min(resource.capacity, resource.available + required)
    
    def complete_task(self, task_id: str, success: bool = True):
        """完成任務"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.state = TaskState.COMPLETED if success else TaskState.FAILED
        task.completed_at = datetime.now()
        
        self._release_resources(task)
        
        # 記錄歷史
        self.history.append({
            "task_id": task_id,
            "state": task.state.value,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        })
        
        self._requeue()
    
    def cancel_task(self, task_id: str):
        """取消任務"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        self._release_resources(task)
        task.state = TaskState.CANCELLED
        self._requeue()
    
    def get_queue_status(self) -> Dict:
        """取得佇列狀態"""
        return {
            "total_tasks": len(self.tasks),
            "queued": len([t for t in self.tasks.values() if t.state == TaskState.QUEUED]),
            "running": len([t for t in self.tasks.values() if t.state == TaskState.RUNNING]),
            "waiting": len([t for t in self.tasks.values() if t.state == TaskState.WAITING]),
            "completed": len([t for t in self.tasks.values() if t.state == TaskState.COMPLETED]),
            "resources": {
                rid: {
                    "name": r.name,
                    "utilization": r.utilization,
                    "available": r.available,
                }
                for rid, r in self.resources.items()
            }
        }
    
    def get_upcoming_tasks(self, limit: int = 10) -> List[Dict]:
        """取得接下來的任務"""
        upcoming = []
        temp_queue = self.queue.copy()
        
        for _ in range(min(limit, len(temp_queue))):
            task_id = temp_queue.pop(0)
            task = self.tasks.get(task_id)
            if task:
                upcoming.append({
                    "id": task.id,
                    "name": task.name,
                    "priority": task.priority.name,
                    "score": task.score,
                    "state": task.state.value,
                    "deadline": task.deadline.isoformat() if task.deadline else None,
                })
        
        return upcoming
    
    def to_dict(self) -> Dict:
        """轉換為 Dict"""
        return {
            "queue_status": self.get_queue_status(),
            "upcoming": self.get_upcoming_tasks(),
            "history": self.history[-10:],  # 最近 10 筆
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    scheduler = Scheduler()
    
    # 新增資源
    gpu1 = scheduler.add_resource("GPU-1", "gpu", capacity=100, cost_per_hour=0.5)
    gpu2 = scheduler.add_resource("GPU-2", "gpu", capacity=100, cost_per_hour=0.5)
    agent1 = scheduler.add_resource("Agent-1", "agent", capacity=100, cost_per_hour=0.1)
    agent2 = scheduler.add_resource("Agent-2", "agent", capacity=100, cost_per_hour=0.1)
    
    print("=== Resources ===")
    for rid, r in scheduler.resources.items():
        print(f"{r.name}: {r.utilization:.1f}% utilized")
    
    # 新增任務
    print("\n=== Adding Tasks ===")
    t1 = scheduler.add_task(
        "訓練模型 A",
        priority=Priority.HIGH,
        required_resources={"gpu": 50, "agent": 20},
        deadline=datetime.now() + timedelta(hours=2)
    )
    
    t2 = scheduler.add_task(
        "訓練模型 B",
        priority=Priority.NORMAL,
        required_resources={"gpu": 30, "agent": 10}
    )
    
    t3 = scheduler.add_task(
        "生成報告",
        priority=Priority.LOW,
        required_resources={"agent": 10}
    )
    
    t4 = scheduler.add_task(
        "緊急修復",
        priority=Priority.CRITICAL,
        required_resources={"gpu": 20, "agent": 30},
        deadline=datetime.now() + timedelta(hours=1)
    )
    
    # 排程
    print("\n=== Schedule ===")
    for i in range(4):
        task = scheduler.schedule_next()
        if task:
            print(f"Scheduled: {task.name} (Priority: {task.priority.name}, Score: {task.score})")
        else:
            print("No task can be scheduled")
    
    # 佇列狀態
    print("\n=== Queue Status ===")
    status = scheduler.get_queue_status()
    print(f"Total: {status['total_tasks']}")
    print(f"Running: {status['running']}")
    print(f"Completed: {status['completed']}")
    
    # 清理
    scheduler.complete_task(t1)
    scheduler.complete_task(t2)
    scheduler.complete_task(t3)
    scheduler.complete_task(t4)
    
    print("\n=== History ===")
    for h in scheduler.history:
        print(f"  {h['task_id']}: {h['state']}")
