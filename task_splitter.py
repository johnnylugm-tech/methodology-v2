#!/usr/bin/env python3
"""
Task Splitter - 任務自動分解

基於 agent-task-manager 整合
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """任務優先級"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    """任務"""
    id: str
    name: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    assignee: Optional[str] = None
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    output: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class TaskSplitter:
    """任務分解器"""
    
    def __init__(self):
        """初始化"""
        self.tasks: Dict[str, Task] = {}
        self.task_counter = 0
    
    def create_task(self, name: str, description: str, 
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   estimated_hours: float = 1.0) -> Task:
        """
        建立任務
        
        Args:
            name: 任務名稱
            description: 任務描述
            priority: 優先級
            estimated_hours: 預估時數
            
        Returns:
            Task
        """
        self.task_counter += 1
        task = Task(
            id=f"task-{self.task_counter:03d}",
            name=name,
            description=description,
            priority=priority,
            estimated_hours=estimated_hours
        )
        self.tasks[task.id] = task
        return task
    
    def add_dependency(self, task_id: str, depends_on: str):
        """
        添加依賴
        
        Args:
            task_id: 任務 ID
            depends_on: 依賴的任務 ID
        """
        if task_id in self.tasks and depends_on in self.tasks:
            self.tasks[task_id].dependencies.append(depends_on)
    
    def split_from_goal(self, goal: str) -> List[Task]:
        """
        從目標自動分解任務
        
        Args:
            goal: 目標描述
            
        Returns:
            任務列表
        """
        # 基於關鍵詞自動分類
        goal_lower = goal.lower()
        
        tasks = []
        
        # 研究階段
        if any(k in goal_lower for k in ["研究", "research", "分析", "analyze"]):
            tasks.append(self.create_task(
                name="調研與分析",
                description="收集資訊、分析需求",
                priority=TaskPriority.HIGH,
                estimated_hours=2.0
            ))
        
        # 設計階段
        if any(k in goal_lower for k in ["設計", "design", "規劃", "plan"]):
            tasks.append(self.create_task(
                name="系統設計",
                description="設計架構、規劃模組",
                priority=TaskPriority.HIGH,
                estimated_hours=3.0
            ))
        
        # 開發階段
        if any(k in goal_lower for k in ["開發", "develop", "實現", "implement", "寫", "build"]):
            tasks.append(self.create_task(
                name="開發實現",
                description="編碼、實現功能",
                priority=TaskPriority.CRITICAL,
                estimated_hours=8.0
            ))
        
        # 測試階段
        if any(k in goal_lower for k in ["測試", "test", "驗證", "verify"]):
            tasks.append(self.create_task(
                name="測試驗證",
                description="編寫測試、驗證功能",
                priority=TaskPriority.HIGH,
                estimated_hours=4.0
            ))
        
        # 文檔階段
        if any(k in goal_lower for k in ["文檔", "doc", "說明"]):
            tasks.append(self.create_task(
                name="文檔撰寫",
                description="撰寫使用文檔",
                priority=TaskPriority.MEDIUM,
                estimated_hours=2.0
            ))
        
        # 部署階段
        if any(k in goal_lower for k in ["部署", "deploy", "發布", "release"]):
            tasks.append(self.create_task(
                name="部署發布",
                description="部署上線、發布版本",
                priority=TaskPriority.HIGH,
                estimated_hours=1.0
            ))
        
        # 建立依賴關係
        for i in range(1, len(tasks)):
            self.add_dependency(tasks[i].id, tasks[i-1].id)
        
        return tasks
    
    def get_ready_tasks(self) -> List[Task]:
        """獲取可執行的任務（依賴都已完成）"""
        ready = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # 檢查依賴
            all_done = all(
                self.tasks.get(dep_id, Task("temp", "temp", "")).status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if all_done:
                ready.append(task)
        
        return ready
    
    def get_execution_order(self) -> List[Task]:
        """獲取執行順序"""
        order = []
        remaining = set(self.tasks.keys())
        
        while remaining:
            for task_id in list(remaining):
                task = self.tasks[task_id]
                
                # 檢查依賴
                deps_met = all(
                    dep_id not in remaining
                    for dep_id in task.dependencies
                )
                
                if deps_met:
                    order.append(task)
                    remaining.remove(task_id)
        
        return order
    
    def get_dag(self) -> Dict:
        """獲取 DAG 結構"""
        return {
            "nodes": [
                {
                    "id": t.id,
                    "label": t.name,
                    "status": t.status.value,
                    "priority": t.priority.value
                }
                for t in self.tasks.values()
            ],
            "edges": [
                {"from": dep, "to": tid}
                for tid, task in self.tasks.items()
                for dep in task.dependencies
            ]
        }
    
    def get_summary(self) -> Dict:
        """獲取摘要"""
        return {
            "total_tasks": len(self.tasks),
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
            "total_estimated_hours": sum(t.estimated_hours for t in self.tasks.values())
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    splitter = TaskSplitter()
    
    # 從目標分解
    goal = "開發一個 AI Agent 系統，需要研究、設計、開發、測試、部署"
    tasks = splitter.split_from_goal(goal)
    
    print("=== Task Splitter Demo ===\n")
    print(f"Goal: {goal}\n")
    
    for task in tasks:
        print(f"📋 {task.id}: {task.name}")
        print(f"   Description: {task.description}")
        print(f"   Priority: {task.priority.name}")
        print(f"   Estimated: {task.estimated_hours}h")
        print()
    
    print("=== Execution Order ===")
    for task in splitter.get_execution_order():
        print(f"{task.id}: {task.name}")
    
    print("\n=== Summary ===")
    summary = splitter.get_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")
