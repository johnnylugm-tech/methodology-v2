#!/usr/bin/env python3
"""
Sprint Planner - PM 友善介面

支援 Sprint/Backlog/Story Point/Burndown Chart
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class StoryStatus(Enum):
    """Story 狀態"""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REMOVED = "removed"


class StorySize(Enum):
    """Story Size (Story Points)"""
    XS = 1   # 1 point
    S = 2     # 2 points
    M = 3     # 3 points
    L = 5     # 5 points
    XL = 8    # 8 points
    XXL = 13  # 13 points


@dataclass
class Story:
    """User Story"""
    id: str
    title: str
    description: str = ""
    
    # 估算
    size: StorySize = StorySize.M
    actual_hours: float = 0.0
    
    # 狀態
    status: StoryStatus = StoryStatus.BACKLOG
    
    # 分配
    assignee: str = ""
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    
    # Sprint
    sprint_id: str = None
    
    @property
    def points(self) -> int:
        return self.size.value
    
    @property
    def is_completed(self) -> bool:
        return self.status == StoryStatus.DONE


@dataclass 
class Sprint:
    """Sprint"""
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    
    # 目標
    goal: str = ""
    
    # 容量
    capacity_points: int = 0
    velocity: float = 0.0  # 實際速度
    
    # 狀態
    is_active: bool = False
    is_completed: bool = False
    
    # 掛鉤
    stories: List[str] = field(default_factory=list)  # story IDs
    
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days
    
    @property
    def remaining_days(self) -> int:
        if self.is_completed:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days)


class SprintPlanner:
    """
    Sprint Planner - PM 友善介面
    
    使用方式：
    
    ```python
    from methodology import SprintPlanner
    
    planner = SprintPlanner()
    
    # 建立 Sprint
    sprint = planner.create_sprint(
        name="Sprint 1",
        start="2026-03-20",
        end="2026-04-02",
        goal="完成用戶登入功能",
        capacity=30  # 30 points
    )
    
    # 加入 Stories
    planner.add_story("作為用戶，我想登入系統", size="M", assignee="John")
    planner.add_story("作為用戶，我想註冊帳號", size="L", assignee="John")
    
    # 分配到 Sprint
    planner.assign_to_sprint(story_id="story-1", sprint_id="sprint-1")
    
    # 開始 Sprint
    planner.start_sprint("sprint-1")
    
    # 更新 Story 狀態
    planner.update_story_status("story-1", StoryStatus.IN_PROGRESS)
    planner.update_story_status("story-1", StoryStatus.DONE)
    
    # 生成報告
    print(planner.generate_sprint_report("sprint-1"))
    print(planner.generate_burndown_chart("sprint-1"))
    ```
    """
    
    def __init__(self):
        self.sprints: Dict[str, Sprint] = {}
        self.stories: Dict[str, Story] = {}
        self.sprint_counter: int = 0
        self.story_counter: int = 0
    
    def create_sprint(self, name: str, start_date: str, end_date: str,
                     goal: str = "", capacity: int = 30) -> Sprint:
        """
        建立 Sprint
        
        Args:
            name: Sprint 名稱
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            goal: Sprint 目標
            capacity: 容量 (story points)
            
        Returns:
            Sprint 實例
        """
        self.sprint_counter += 1
        sprint_id = f"sprint-{self.sprint_counter}"
        
        sprint = Sprint(
            id=sprint_id,
            name=name,
            start_date=datetime.strptime(start_date, "%Y-%m-%d"),
            end_date=datetime.strptime(end_date, "%Y-%m-%d"),
            goal=goal,
            capacity_points=capacity
        )
        
        self.sprints[sprint_id] = sprint
        return sprint
    
    def add_story(self, title: str, description: str = "",
                 size: str = "M", assignee: str = "") -> Story:
        """
        新增 Story 到 Backlog
        
        Args:
            title: Story 標題
            description: 詳細描述
            size: Story Size (XS/S/M/L/XL/XXL)
            assignee: 負責人
            
        Returns:
            Story 實例
        """
        self.story_counter += 1
        story_id = f"story-{self.story_counter}"
        
        story = Story(
            id=story_id,
            title=title,
            description=description,
            size=StorySize[size.upper()],
            assignee=assignee,
            status=StoryStatus.BACKLOG
        )
        
        self.stories[story_id] = story
        return story
    
    def assign_to_sprint(self, story_id: str, sprint_id: str) -> bool:
        """將 Story 分配到 Sprint"""
        story = self.stories.get(story_id)
        sprint = self.sprints.get(sprint_id)
        
        if not story or not sprint:
            return False
        
        # 如果已在其他 Sprint，先移除
        if story.sprint_id:
            old_sprint = self.sprints.get(story.sprint_id)
            if old_sprint and story_id in old_sprint.stories:
                old_sprint.stories.remove(story_id)
        
        # 分配到新 Sprint
        sprint.stories.append(story_id)
        story.sprint_id = sprint_id
        story.status = StoryStatus.TODO
        
        return True
    
    def start_sprint(self, sprint_id: str) -> bool:
        """開始 Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return False
        
        sprint.is_active = True
        
        # 所有 TODO 的 Story 設為 IN_PROGRESS
        for story_id in sprint.stories:
            story = self.stories.get(story_id)
            if story and story.status == StoryStatus.TODO:
                story.status = StoryStatus.IN_PROGRESS
                story.started_at = datetime.now()
        
        return True
    
    def complete_sprint(self, sprint_id: str) -> Dict:
        """完成 Sprint"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {}
        
        sprint.is_active = False
        sprint.is_completed = True
        
        # 計算速度
        completed_points = 0
        for story_id in sprint.stories:
            story = self.stories.get(story_id)
            if story and story.status == StoryStatus.DONE:
                completed_points += story.points
        
        sprint.velocity = completed_points
        
        return {
            "sprint_id": sprint_id,
            "completed_points": completed_points,
            "capacity_points": sprint.capacity_points,
            "completion_rate": (completed_points / sprint.capacity_points * 100) if sprint.capacity_points > 0 else 0
        }
    
    def update_story_status(self, story_id: str, status: StoryStatus) -> bool:
        """更新 Story 狀態"""
        story = self.stories.get(story_id)
        if not story:
            return False
        
        old_status = story.status
        story.status = status
        
        if status == StoryStatus.IN_PROGRESS and old_status != StoryStatus.IN_PROGRESS:
            story.started_at = datetime.now()
        
        if status == StoryStatus.DONE:
            story.completed_at = datetime.now()
        
        return True
    
    def get_backlog(self) -> List[Story]:
        """取得 Backlog (未分配 Sprint 的 Stories)"""
        return [
            story for story in self.stories.values()
            if story.sprint_id is None and story.status != StoryStatus.REMOVED
        ]
    
    def get_sprint_stories(self, sprint_id: str) -> List[Story]:
        """取得 Sprint 的所有 Stories"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return []
        
        return [
            self.stories[sid] for sid in sprint.stories
            if sid in self.stories
        ]
    
    def get_sprint_summary(self, sprint_id: str) -> Dict:
        """取得 Sprint 摘要"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {}
        
        stories = self.get_sprint_stories(sprint_id)
        
        by_status = {}
        for s in stories:
            by_status[s.status.value] = by_status.get(s.status.value, 0) + s.points
        
        total_points = sum(s.points for s in stories)
        completed_points = sum(s.points for s in stories if s.is_completed)
        
        return {
            "sprint": {
                "id": sprint.id,
                "name": sprint.name,
                "goal": sprint.goal,
                "is_active": sprint.is_active,
                "is_completed": sprint.is_completed,
            },
            "capacity": sprint.capacity_points,
            "total_points": total_points,
            "completed_points": completed_points,
            "remaining_points": total_points - completed_points,
            "completion_rate": (completed_points / total_points * 100) if total_points > 0 else 0,
            "by_status": by_status,
            "remaining_days": sprint.remaining_days
        }
    
    def generate_burndown_chart(self, sprint_id: str) -> Dict:
        """
        生成 Burndown Chart 數據
        
        Returns:
            燃盡圖數據
        """
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return {}
        
        stories = self.get_sprint_stories(sprint_id)
        total_points = sum(s.points for s in stories)
        
        # 計算理想線
        days = sprint.duration_days
        ideal_burndown = []
        for i in range(days + 1):
            remaining = total_points - (total_points / days * i)
            ideal_burndown.append(max(0, remaining))
        
        # 計算實際線 (根據完成的 Story)
        actual_burndown = []
        current = total_points
        
        for i in range(days + 1):
            date = sprint.start_date + timedelta(days=i)
            
            # 檢查這天完成的 Story
            for story in stories:
                if story.completed_at and story.completed_at.date() == date.date():
                    current -= story.points
            
            actual_burndown.append(max(0, current))
        
        return {
            "sprint_name": sprint.name,
            "total_points": total_points,
            "ideal_burndown": ideal_burndown,
            "actual_burndown": actual_burndown,
            "days": days,
            "labels": [
                (sprint.start_date + timedelta(days=i)).strftime("%m/%d")
                for i in range(days + 1)
            ]
        }
    
    def generate_velocity_chart(self) -> Dict:
        """生成 Velocity Chart 數據"""
        velocities = []
        
        for sprint in self.sprints.values():
            if sprint.is_completed:
                velocities.append({
                    "sprint": sprint.name,
                    "velocity": sprint.velocity,
                    "capacity": sprint.capacity_points,
                    "date": sprint.end_date.strftime("%Y-%m-%d")
                })
        
        # 計算平均速度
        if velocities:
            avg_velocity = sum(v['velocity'] for v in velocities) / len(velocities)
        else:
            avg_velocity = 0
        
        return {
            "sprints": velocities,
            "average_velocity": avg_velocity,
            "total_sprints": len(velocities)
        }
    
    def generate_sprint_report(self, sprint_id: str) -> str:
        """生成 Sprint 報告"""
        sprint = self.sprints.get(sprint_id)
        if not sprint:
            return "Sprint not found"
        
        summary = self.get_sprint_summary(sprint_id)
        stories = self.get_sprint_stories(sprint_id)
        
        lines = [
            "=" * 60,
            f"SPRINT REPORT: {sprint.name}",
            "=" * 60,
            "",
            f"Goal: {sprint.goal}",
            f"Duration: {sprint.duration_days} days",
            f"Remaining: {sprint.remaining_days} days",
            "",
            "SUMMARY:",
            f"  Total Points: {summary['total_points']}",
            f"  Completed: {summary['completed_points']} ({summary['completion_rate']:.0f}%)",
            f"  Remaining: {summary['remaining_points']}",
            f"  Capacity: {summary['capacity']}",
            "",
            "BY STATUS:",
        ]
        
        for status, points in summary['by_status'].items():
            lines.append(f"  {status}: {points} points")
        
        lines.append("")
        lines.append("STORIES:")
        lines.append("-" * 60)
        
        for story in sorted(stories, key=lambda s: s.status.value):
            status_icon = {
                StoryStatus.TODO: "[ ]",
                StoryStatus.IN_PROGRESS: "[→]",
                StoryStatus.DONE: "[✓]",
            }.get(story.status, "[?]")
            
            lines.append(f"  {status_icon} {story.title}")
            lines.append(f"       Size: {story.size.name} ({story.points} pts)")
            if story.assignee:
                lines.append(f"       Assignee: {story.assignee}")
        
        return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    planner = SprintPlanner()
    
    # 建立 Sprint
    sprint = planner.create_sprint(
        name="Sprint 1",
        start="2026-03-20",
        end="2026-04-02",
        goal="完成用戶登入功能",
        capacity=30
    )
    
    # 加入 Stories
    planner.add_story("用戶登入", "作為用戶，我想登入系統", size="M", assignee="Alice")
    planner.add_story("用戶註冊", "作為用戶，我想註冊新帳號", size="L", assignee="Bob")
    planner.add_story("密碼重置", "作為用戶，我想重置密碼", size="M", assignee="Alice")
    planner.add_story("記住登入", "作為用戶，我想記住登入狀態", size="S", assignee="Charlie")
    planner.add_story("第三方登入", "作為用戶，我想用 Google 登入", size="XL", assignee="Bob")
    
    # 分配
    for i in range(1, 5):
        planner.assign_to_sprint(f"story-{i}", "sprint-1")
    
    # 開始 Sprint
    planner.start_sprint("sprint-1")
    
    # 假裝完成一些
    planner.update_story_status("story-1", StoryStatus.DONE)
    planner.update_story_status("story-2", StoryStatus.DONE)
    planner.update_story_status("story-3", StoryStatus.IN_PROGRESS)
    
    # 生成報告
    print(planner.generate_sprint_report("sprint-1"))
    
    print("\n" + "=" * 60)
    print("Burndown Chart:")
    print("=" * 60)
    import json
    print(json.dumps(planner.generate_burndown_chart("sprint-1"), indent=2))
