#!/usr/bin/env python3
"""
Task Splitter v2 - 增強版任務分解

支援 DAG 依賴關係、里程碑設定
"""

import json
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    """任務優先級"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class MilestoneStatus(Enum):
    """里程碑狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AT_RISK = "at_risk"
    DELAYED = "delayed"


@dataclass
class Task:
    """任務"""
    id: str
    name: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: float = 1.0
    dependencies: List[str] = field(default_factory=list)  # 任務依賴
    assignee: str = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    
    # 新增：里程碑
    milestone: str = None
    
    # 新增：估計時間範圍
    min_hours: float = None
    max_hours: float = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.name,
            "estimated_hours": self.estimated_hours,
            "dependencies": self.dependencies,
            "assignee": self.assignee,
            "tags": self.tags,
            "milestone": self.milestone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class Milestone:
    """里程碑"""
    id: str
    name: str
    description: str = ""
    target_date: datetime = None
    tasks: List[str] = field(default_factory=list)  # 任務 ID 列表
    status: MilestoneStatus = MilestoneStatus.PENDING
    completion: float = 0.0  # 0-100%
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "tasks": self.tasks,
            "status": self.status.value,
            "completion": self.completion,
        }


class DAG:
    """有向無環圖 (Directed Acyclic Graph)"""
    
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, List[str]] = {}  # node -> dependencies
    
    def add_node(self, node_id: str):
        """新增節點"""
        self.nodes.add(node_id)
        if node_id not in self.edges:
            self.edges[node_id] = []
    
    def add_edge(self, from_node: str, to_node: str):
        """新增邊 (from_node 依賴 to_node)"""
        self.add_node(from_node)
        self.add_node(to_node)
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """取得節點的依賴"""
        return self.edges.get(node_id, [])
    
    def get_dependents(self, node_id: str) -> List[str]:
        """取得依賴此節點的節點"""
        dependents = []
        for node, deps in self.edges.items():
            if node_id in deps:
                dependents.append(node)
        return dependents
    
    def topological_sort(self) -> List[str]:
        """拓撲排序 (Kahn's algorithm)"""
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for dep in self.edges.get(node, []):
                in_degree[node] += 1
        
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for dependent in self.get_dependents(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        return result
    
    def has_cycle(self) -> bool:
        """檢查是否有循環依賴"""
        visited = set()
        rec_stack = set()
        
        def visit(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for dep in self.edges.get(node, []):
                if dep not in visited:
                    if visit(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if visit(node):
                    return True
        return False


class TaskSplitter:
    """任務分解器 (增強版)"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.milestones: Dict[str, Milestone] = {}
        self.dag = DAG()
        self.project_name: str = ""
        self.start_date: datetime = None
    
    def set_project(self, name: str, start_date: datetime = None):
        """設定專案"""
        self.project_name = name
        self.start_date = start_date or datetime.now()
    
    def add_task(self, name: str, description: str = "", 
                 priority: TaskPriority = TaskPriority.MEDIUM,
                 estimated_hours: float = 1.0,
                 dependencies: List[str] = None,
                 milestone: str = None) -> str:
        """新增任務"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            priority=priority,
            estimated_hours=estimated_hours,
            dependencies=dependencies or [],
            milestone=milestone,
        )
        
        self.tasks[task_id] = task
        self.dag.add_node(task_id)
        
        # 新增依賴邊
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.dag.add_edge(task_id, dep_id)
        
        # 加入里程碑
        if milestone and milestone in self.milestones:
            self.milestones[milestone].tasks.append(task_id)
        
        # 更新任務狀態
        self._update_task_status(task_id)
        
        return task_id
    
    def add_milestone(self, name: str, target_date: datetime = None,
                     description: str = "") -> str:
        """新增里程碑"""
        milestone_id = f"milestone-{uuid.uuid4().hex[:8]}"
        
        milestone = Milestone(
            id=milestone_id,
            name=name,
            target_date=target_date,
            description=description,
        )
        
        self.milestones[milestone_id] = milestone
        return milestone_id
    
    def _update_task_status(self, task_id: str):
        """更新任務狀態"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return
        
        # 檢查依賴是否都已完成
        deps = self.dag.get_dependencies(task_id)
        if not deps:
            task.status = TaskStatus.READY
        else:
            all_deps_completed = all(
                self.tasks.get(dep_id, Task(id=dep_id, name="", status=TaskStatus.PENDING)).status == TaskStatus.COMPLETED
                for dep_id in deps
            )
            
            if all_deps_completed:
                task.status = TaskStatus.READY
            else:
                task.status = TaskStatus.BLOCKED
    
    def update_task_status(self, task_id: str, status: TaskStatus):
        """更新任務狀態"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        task.status = status
        
        if status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            # 更新依賴此任務的任務狀態
            for dep_id in self.dag.get_dependents(task_id):
                self._update_task_status(dep_id)
        
        # 更新里程碑進度
        self._update_milestone_progress()
    
    def _update_milestone_progress(self):
        """更新里程碑進度"""
        for milestone in self.milestones.values():
            if not milestone.tasks:
                continue
            
            completed = sum(
                1 for task_id in milestone.tasks
                if self.tasks.get(task_id, Task(id=task_id, name="", status=TaskStatus.PENDING)).status == TaskStatus.COMPLETED
            )
            milestone.completion = (completed / len(milestone.tasks)) * 100
            
            if milestone.completion == 100:
                milestone.status = MilestoneStatus.COMPLETED
            elif milestone.completion > 0:
                milestone.status = MilestoneStatus.IN_PROGRESS
    
    def split_from_goal(self, goal: str) -> List[Task]:
        """從目標自動拆分任務"""
        self.tasks.clear()
        self.milestones.clear()
        self.dag = DAG()
        
        # 簡單的關鍵詞分析
        goal_lower = goal.lower()
        
        tasks = []
        
        # 根據目標類型生成任務
        if any(k in goal_lower for k in ["系統", "平台", "系統開發"]):
            tasks = self._generate_system_tasks(goal)
        elif any(k in goal_lower for k in ["網站", "web", "前端", "後端"]):
            tasks = self._generate_web_tasks(goal)
        elif any(k in goal_lower for k in ["api", "服務", "接口"]):
            tasks = self._generate_api_tasks(goal)
        elif any(k in goal_lower for k in ["ai", "機器學習", "模型"]):
            tasks = self._generate_ai_tasks(goal)
        else:
            tasks = self._generate_generic_tasks(goal)
        
        # 新增任務到系統
        task_ids = []
        for task_data in tasks:
            task_id = self.add_task(**task_data)
            task_ids.append(task_id)
        
        return [self.tasks[tid] for tid in task_ids]
    
    def _generate_system_tasks(self, goal: str) -> List[Dict]:
        """生成系統開發任務"""
        return [
            {"name": "需求分析", "description": f"分析 {goal} 的需求", "priority": TaskPriority.HIGH, "estimated_hours": 4},
            {"name": "系統設計", "description": "系統架構設計", "priority": TaskPriority.HIGH, "estimated_hours": 8, "dependencies": []},
            {"name": "資料庫設計", "description": "資料庫模型設計", "priority": TaskPriority.HIGH, "estimated_hours": 4, "dependencies": []},
            {"name": "API 開發", "description": "後端 API 開發", "priority": TaskPriority.MEDIUM, "estimated_hours": 16, "dependencies": []},
            {"name": "前端開發", "description": "前端介面開發", "priority": TaskPriority.MEDIUM, "estimated_hours": 16, "dependencies": []},
            {"name": "測試", "description": "單元測試和整合測試", "priority": TaskPriority.MEDIUM, "estimated_hours": 8, "dependencies": []},
            {"name": "部署", "description": "部署上線", "priority": TaskPriority.LOW, "estimated_hours": 2, "dependencies": []},
        ]
    
    def _generate_web_tasks(self, goal: str) -> List[Dict]:
        """生成 Web 開發任務"""
        return [
            {"name": "需求分析", "priority": TaskPriority.HIGH, "estimated_hours": 3},
            {"name": "UI/UX 設計", "priority": TaskPriority.HIGH, "estimated_hours": 8},
            {"name": "前端開發", "priority": TaskPriority.MEDIUM, "estimated_hours": 20},
            {"name": "後端開發", "priority": TaskPriority.MEDIUM, "estimated_hours": 20},
            {"name": "測試", "priority": TaskPriority.MEDIUM, "estimated_hours": 8},
            {"name": "部署", "priority": TaskPriority.LOW, "estimated_hours": 2},
        ]
    
    def _generate_api_tasks(self, goal: str) -> List[Dict]:
        """生成 API 開發任務"""
        return [
            {"name": "需求分析", "priority": TaskPriority.HIGH, "estimated_hours": 2},
            {"name": "API 設計", "priority": TaskPriority.HIGH, "estimated_hours": 4},
            {"name": "認證機制", "priority": TaskPriority.MEDIUM, "estimated_hours": 4},
            {"name": "業務邏輯", "priority": TaskPriority.MEDIUM, "estimated_hours": 16},
            {"name": "錯誤處理", "priority": TaskPriority.MEDIUM, "estimated_hours": 4},
            {"name": "文件生成", "priority": TaskPriority.LOW, "estimated_hours": 2},
            {"name": "測試", "priority": TaskPriority.MEDIUM, "estimated_hours": 8},
        ]
    
    def _generate_ai_tasks(self, goal: str) -> List[Dict]:
        """生成 AI 專案任務"""
        return [
            {"name": "資料收集", "priority": TaskPriority.HIGH, "estimated_hours": 8},
            {"name": "資料處理", "priority": TaskPriority.HIGH, "estimated_hours": 8},
            {"name": "模型訓練", "priority": TaskPriority.HIGH, "estimated_hours": 24},
            {"name": "模型評估", "priority": TaskPriority.MEDIUM, "estimated_hours": 4},
            {"name": "部署模型", "priority": TaskPriority.MEDIUM, "estimated_hours": 4},
            {"name": "API 整合", "priority": TaskPriority.MEDIUM, "estimated_hours": 8},
        ]
    
    def _generate_generic_tasks(self, goal: str) -> List[Dict]:
        """生成通用任務"""
        return [
            {"name": "規劃", "priority": TaskPriority.HIGH, "estimated_hours": 2},
            {"name": "執行", "priority": TaskPriority.MEDIUM, "estimated_hours": 8},
            {"name": "檢討", "priority": TaskPriority.LOW, "estimated_hours": 2},
        ]
    
    def get_execution_order(self) -> List[Task]:
        """取得執行順序 (根據依賴)"""
        sorted_ids = self.dag.topological_sort()
        return [self.tasks[tid] for tid in sorted_ids if tid in self.tasks]
    
    def get_ready_tasks(self) -> List[Task]:
        """取得可執行的任務"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.READY]
    
    def get_milestone_summary(self) -> Dict:
        """取得里程碑摘要"""
        return {
            "total": len(self.milestones),
            "completed": sum(1 for m in self.milestones.values() if m.status == MilestoneStatus.COMPLETED),
            "in_progress": sum(1 for m in self.milestones.values() if m.status == MilestoneStatus.IN_PROGRESS),
            "at_risk": sum(1 for m in self.milestones.values() if m.status == MilestoneStatus.AT_RISK),
        }
    
    def get_summary(self) -> Dict:
        """取得摘要"""
        return {
            "project": self.project_name,
            "total_tasks": len(self.tasks),
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "ready": sum(1 for t in self.tasks.values() if t.status == TaskStatus.READY),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "blocked": sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED),
            "total_hours": sum(t.estimated_hours for t in self.tasks.values()),
            "milestones": self.get_milestone_summary(),
        }
    
    def to_json(self) -> str:
        """轉換為 JSON"""
        return json.dumps({
            "project": self.project_name,
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "milestones": [m.to_dict() for m in self.milestones.values()],
            "summary": self.get_summary(),
        }, indent=2, ensure_ascii=False)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    splitter = TaskSplitter()
    splitter.set_project("AI 系統開發")
    
    # 新增里程碑
    m1 = splitter.add_milestone("MVP 完成", datetime.now() + timedelta(days=7), "第一版發布")
    m2 = splitter.add_milestone("Beta 發布", datetime.now() + timedelta(days=14), "Beta 測試")
    
    # 拆分任務
    tasks = splitter.split_from_goal("開發一個 AI 系統")
    
    # 設定里程碑
    for task in tasks[:3]:
        task.milestone = m1
    for task in tasks[3:]:
        task.milestone = m2
    
    print("=== Tasks ===")
    for task in splitter.get_execution_order():
        deps = ", ".join(task.dependencies) if task.dependencies else "None"
        print(f"{task.id}: {task.name} ({task.status.value})")
        print(f"  Priority: {task.priority.name}")
        print(f"  Hours: {task.estimated_hours}")
        print(f"  Dependencies: {deps}")
        print()
    
    print("=== Summary ===")
    summary = splitter.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    print("\n=== Ready to Execute ===")
    for task in splitter.get_ready_tasks():
        print(f"✅ {task.name}")
