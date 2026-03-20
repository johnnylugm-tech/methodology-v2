#!/usr/bin/env python3
"""
Progress Dashboard - 進度儀表板

支援 Sprint/Backlog/Burndown Chart
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class Sprint:
    """衝刺"""
    id: str
    name: str
    goal: str
    start_date: datetime
    end_date: datetime
    capacity: float = 100.0  # 總容量 (story points)
    tasks: List[str] = field(default_factory=list)
    status: str = "planning"  # planning, active, completed
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days
    
    @property
    def days_remaining(self) -> int:
        remaining = (self.end_date - datetime.now()).days
        return max(0, remaining)


@dataclass
class BacklogItem:
    """待辦清單項目"""
    id: str
    title: str
    description: str = ""
    story_points: float = 1.0
    priority: int = 3  # 1=highest, 5=lowest
    labels: List[str] = field(default_factory=list)
    assignee: str = None
    sprint_id: str = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def priority_label(self) -> str:
        labels = {1: "Critical", 2: "High", 3: "Medium", 4: "Low", 5: "Nice-to-have"}
        return labels.get(self.priority, "Unknown")


@dataclass 
class DailySnapshot:
    """每日快照 (用於 Burndown)"""
    date: datetime
    remaining_points: float
    completed_points: float
    ideal_remaining: float


class ProgressDashboard:
    """進度儀表板"""
    
    def __init__(self):
        self.sprints: Dict[str, Sprint] = {}
        self.backlog: Dict[str, BacklogItem] = {}
        self.current_sprint_id: str = None
        self.snapshots: List[DailySnapshot] = []
        self.completed_points_history: List[float] = []
        self.ideal_burndown: List[float] = []
    
    # ==================== Sprint Management ====================
    
    def create_sprint(self, name: str, goal: str, 
                     start_date: datetime = None,
                     end_date: datetime = None,
                     capacity: float = 100.0) -> str:
        """建立 Sprint"""
        sprint_id = f"sprint-{len(self.sprints) + 1}"
        
        if start_date is None:
            start_date = datetime.now()
        if end_date is None:
            end_date = start_date + timedelta(days=14)  # 預設 2 週
        
        sprint = Sprint(
            id=sprint_id,
            name=name,
            goal=goal,
            start_date=start_date,
            end_date=end_date,
            capacity=capacity,
        )
        
        self.sprints[sprint_id] = sprint
        
        if self.current_sprint_id is None:
            self.current_sprint_id = sprint_id
        
        # 重新計算理想燃盡線
        self._calculate_ideal_burndown(sprint)
        
        return sprint_id
    
    def start_sprint(self, sprint_id: str) -> bool:
        """開始 Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint or sprint.status == "active":
            return False
        
        sprint.status = "active"
        self.current_sprint_id = sprint_id
        
        # 初始化當天快照
        self._take_snapshot()
        
        return True
    
    def complete_sprint(self, sprint_id: str) -> Dict:
        """完成 Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {"error": "Sprint not found"}
        
        sprint.status = "completed"
        
        # 計算 Sprint 統計
        completed = self.get_sprint_completed_points(sprint_id)
        remaining = self.get_sprint_remaining_points(sprint_id)
        velocity = self.get_sprint_velocity(sprint_id)
        
        return {
            "sprint_id": sprint_id,
            "name": sprint.name,
            "completed_points": completed,
            "remaining_points": remaining,
            "velocity": velocity,
            "status": "completed"
        }
    
    def _calculate_ideal_burndown(self, sprint: Sprint):
        """計算理想燃盡線"""
        total_points = self.get_sprint_total_points(sprint.id)
        days = sprint.duration_days
        
        self.ideal_burndown = []
        for i in range(days + 1):
            remaining = total_points * (1 - i / days)
            self.ideal_burndown.append(remaining)
    
    # ==================== Backlog Management ====================
    
    def add_to_backlog(self, title: str, description: str = "",
                      story_points: float = 1.0, priority: int = 3) -> str:
        """加入待辦清單"""
        item_id = f"item-{len(self.backlog) + 1}"
        
        item = BacklogItem(
            id=item_id,
            title=title,
            description=description,
            story_points=story_points,
            priority=priority,
        )
        
        self.backlog[item_id] = item
        return item_id
    
    def add_item_to_sprint(self, item_id: str, sprint_id: str) -> bool:
        """將項目加入 Sprint"""
        item = self.backlog.get(item_id)
        sprint = self.sprints.get(sprint_id)
        
        if not item or not sprint:
            return False
        
        # 從舊 Sprint 移除
        if item.sprint_id:
            old_sprint = self.sprints.get(item.sprint_id)
            if old_sprint and item_id in old_sprint.tasks:
                old_sprint.tasks.remove(item_id)
        
        # 加入新 Sprint
        item.sprint_id = sprint_id
        sprint.tasks.append(item_id)
        
        return True
    
    def prioritize_backlog(self) -> List[BacklogItem]:
        """取得優先排序的待辦"""
        return sorted(
            [item for item in self.backlog.values() if item.sprint_id is None],
            key=lambda x: (x.priority, x.created_at)
        )
    
    # ==================== Sprint Statistics ====================
    
    def get_sprint_total_points(self, sprint_id: str) -> float:
        """取得 Sprint 總點數"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return 0
        
        return sum(
            self.backlog.get(item_id, BacklogItem(id=item_id, title="", story_points=0)).story_points
            for item_id in sprint.tasks
        )
    
    def get_sprint_completed_points(self, sprint_id: str) -> float:
        """取得已完成點數"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return 0
        
        return sum(
            self.backlog.get(item_id, BacklogItem(id=item_id, title="", story_points=0)).story_points
            for item_id in sprint.tasks
            if self.backlog.get(item_id) and self._is_item_completed(item_id)
        )
    
    def get_sprint_remaining_points(self, sprint_id: str) -> float:
        """取得剩餘點數"""
        total = self.get_sprint_total_points(sprint_id)
        completed = self.get_sprint_completed_points(sprint_id)
        return total - completed
    
    def get_sprint_velocity(self, sprint_id: str) -> float:
        """取得 Sprint 速度 (已完成 / 總容量)"""
        sprint = self.sprints.get(sprint_id)
        if not sprint or sprint.capacity == 0:
            return 0
        
        completed = self.get_sprint_completed_points(sprint_id)
        return (completed / sprint.capacity) * 100
    
    def _is_item_completed(self, item_id: str) -> bool:
        """檢查項目是否完成"""
        # 在真實系統中會有狀態追蹤
        # 這裡用隨機模擬
        import random
        return random.choice([True, False])
    
    # ==================== Burndown Chart ====================
    
    def _take_snapshot(self):
        """拍攝每日快照"""
        if not self.current_sprint_id:
            return
        
        remaining = self.get_sprint_remaining_points(self.current_sprint_id)
        total = self.get_sprint_total_points(self.current_sprint_id)
        completed = total - remaining
        
        snapshot = DailySnapshot(
            date=datetime.now(),
            remaining_points=remaining,
            completed_points=completed,
            ideal_remaining=self.ideal_burndown[len(self.snapshots)] if len(self.ideal_burndown) > len(self.snapshots) else 0,
        )
        
        self.snapshots.append(snapshot)
    
    def get_burndown_data(self, sprint_id: str = None) -> Dict:
        """取得燃盡圖數據"""
        sprint_id = sprint_id or self.current_sprint_id
        sprint = self.sprints.get(sprint_id)
        
        if not sprint:
            return {}
        
        return {
            "sprint_name": sprint.name,
            "start_date": sprint.start_date.isoformat(),
            "end_date": sprint.end_date.isoformat(),
            "days_elapsed": sprint.duration_days - sprint.days_remaining,
            "days_remaining": sprint.days_remaining,
            "total_points": self.get_sprint_total_points(sprint_id),
            "completed_points": self.get_sprint_completed_points(sprint_id),
            "remaining_points": self.get_sprint_remaining_points(sprint_id),
            "velocity": self.get_sprint_velocity(sprint_id),
            "ideal_burndown": self.ideal_burndown,
            "actual_burndown": [s.remaining_points for s in self.snapshots],
        }
    
    # ==================== Dashboard Views ====================
    
    def get_sprint_board(self, sprint_id: str = None) -> Dict:
        """取得 Sprint Board 視圖"""
        sprint_id = sprint_id or self.current_sprint_id
        sprint = self.sprints.get(sprint_id)
        
        if not sprint:
            return {}
        
        # 按狀態分組
        todo = []
        in_progress = []
        done = []
        
        for item_id in sprint.tasks:
            item = self.backlog.get(item_id)
            if not item:
                continue
            
            item_dict = {
                "id": item.id,
                "title": item.title,
                "story_points": item.story_points,
                "priority": item.priority_label,
                "assignee": item.assignee,
            }
            
            # 模擬狀態分配
            if self._is_item_completed(item_id):
                done.append(item_dict)
            elif len(in_progress) < 3:
                in_progress.append(item_dict)
            else:
                todo.append(item_dict)
        
        return {
            "sprint": {
                "id": sprint.id,
                "name": sprint.name,
                "status": sprint.status,
                "days_remaining": sprint.days_remaining,
                "capacity": sprint.capacity,
            },
            "columns": {
                "todo": {"count": len(todo), "points": sum(i["story_points"] for i in todo), "items": todo},
                "in_progress": {"count": len(in_progress), "points": sum(i["story_points"] for i in in_progress), "items": in_progress},
                "done": {"count": len(done), "points": sum(i["story_points"] for i in done), "items": done},
            },
            "summary": {
                "total_points": self.get_sprint_total_points(sprint_id),
                "completed": len(done),
                "in_progress": len(in_progress),
                "todo": len(todo),
                "velocity": self.get_sprint_velocity(sprint_id),
            }
        }
    
    def get_backlog_view(self) -> Dict:
        """取得 Backlog 視圖"""
        prioritized = self.prioritize_backlog()
        
        return {
            "total_items": len(prioritized),
            "total_points": sum(item.story_points for item in prioritized),
            "by_priority": {
                str(i): {
                    "count": sum(1 for item in prioritized if item.priority == i),
                    "points": sum(item.story_points for item in prioritized if item.priority == i),
                }
                for i in range(1, 6)
            },
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "story_points": item.story_points,
                    "priority": item.priority_label,
                    "created_at": item.created_at.isoformat(),
                }
                for item in prioritized
            ]
        }
    
    def generate_report(self) -> str:
        """生成進度報告"""
        if not self.current_sprint_id:
            return "No active sprint"
        
        sprint = self.sprints[self.current_sprint_id]
        board = self.get_sprint_board()
        burndown = self.get_burndown_data()
        
        report = f"""
# 📊 Sprint 進度報告

## {sprint.name}

**狀態**: {sprint.status}
**目標**: {sprint.goal}
**時間**: {sprint.start_date.strftime('%Y-%m-%d')} ~ {sprint.end_date.strftime('%Y-%m-%d')}
**剩餘**: {sprint.days_remaining} 天

---

## 📈 統計

| 指標 | 數值 |
|------|------|
| 總點數 | {burndown.get('total_points', 0)} |
| 已完成 | {burndown.get('completed_points', 0)} |
| 剩餘 | {burndown.get('remaining_points', 0)} |
| 速度 | {burndown.get('velocity', 0):.1f}% |

---

## 📋 Board 概覽

- 🔵 To Do: {board['summary']['todo']} 項
- 🟡 In Progress: {board['summary']['in_progress']} 項  
- ✅ Done: {board['summary']['completed']} 項

---

## 🎯 里程碑

- 預計完成: {sprint.end_date.strftime('%Y-%m-%d')}
- 預測: {'⚠️ 可能延期' if burndown.get('remaining_points', 0) > burndown.get('ideal_burndown', [0])[-1] else '✅ 正常'}
"""
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    dashboard = ProgressDashboard()
    
    # 建立 Sprint
    sprint_id = dashboard.create_sprint(
        name="Sprint 1",
        goal="完成核心功能",
        capacity=50
    )
    dashboard.start_sprint(sprint_id)
    
    # 加入項目
    for i in range(8):
        item_id = dashboard.add_to_backlog(
            title=f"功能 {i+1}",
            story_points=3 if i % 2 == 0 else 5,
            priority=(i % 3) + 1
        )
        dashboard.add_item_to_sprint(item_id, sprint_id)
    
    # 顯示 Board
    print("=== Sprint Board ===")
    board = dashboard.get_sprint_board()
    print(f"Sprint: {board['sprint']['name']}")
    print(f"Status: {board['sprint']['status']}")
    print(f"\nColumns:")
    for col, data in board['columns'].items():
        print(f"  {col}: {data['count']} items, {data['points']} points")
    
    # Burndown
    print("\n=== Burndown Data ===")
    burndown = dashboard.get_burndown_data()
    print(f"Total: {burndown.get('total_points')}")
    print(f"Completed: {burndown.get('completed_points')}")
    print(f"Remaining: {burndown.get('remaining_points')}")
    print(f"Velocity: {burndown.get('velocity'):.1f}%")
    
    # Report
    print("\n=== Report ===")
    print(dashboard.generate_report())
