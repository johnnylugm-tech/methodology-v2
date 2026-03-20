#!/usr/bin/env python3
"""
Workflow Templates - 工作流程範本

內建 Scrum/Kanban 範本，PM 可直接使用
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class WorkflowType(Enum):
    """工作流程類型"""
    SCRUM = "scrum"
    KANBAN = "kanban"
    SPIKE = "spike"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """任務狀態"""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(Enum):
    """優先級"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Sprint:
    """衝刺 (Sprint)"""
    name: str
    goal: str
    start_date: datetime
    end_date: datetime
    tasks: List[str] = field(default_factory=list)
    status: str = "planning"  # planning, active, completed


@dataclass
class WorkflowTemplate:
    """工作流程範本"""
    name: str
    type: WorkflowType
    columns: List[Dict]
    sprints: List[Sprint] = field(default_factory=list)
    settings: Dict = field(default_factory=dict)


class WorkflowTemplates:
    """工作流程範本管理器"""

    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, WorkflowTemplate]:
        """載入預設範本"""
        return {
            "scrum": self._scrum_template(),
            "kanban": self._kanban_template(),
            "spike": self._spike_template(),
        }
    
    def _scrum_template(self) -> WorkflowTemplate:
        """Scrum 範本"""
        columns = [
            {"name": "Backlog", "status": TaskStatus.BACKLOG.value, "wip": -1},
            {"name": "Sprint Backlog", "status": TaskStatus.TODO.value, "wip": -1},
            {"name": "In Progress", "status": TaskStatus.IN_PROGRESS.value, "wip": 3},
            {"name": "In Review", "status": TaskStatus.IN_REVIEW.value, "wip": 2},
            {"name": "Done", "status": TaskStatus.DONE.value, "wip": -1},
        ]
        
        # 預設 2 週 Sprint
        today = datetime.now()
        sprints = [
            Sprint(
                name="Sprint 1",
                goal="完成核心功能",
                start_date=today,
                end_date=today + timedelta(days=14),
                status="planning"
            ),
            Sprint(
                name="Sprint 2",
                goal="完成次要功能",
                start_date=today + timedelta(days=14),
                end_date=today + timedelta(days=28),
                status="planning"
            ),
        ]
        
        settings = {
            "sprint_duration": 14,  # 天
            "daily_standup": True,
            "sprint_review": True,
            "retrospective": True,
            "velocity_tracking": True,
        }
        
        return WorkflowTemplate(
            name="Scrum",
            type=WorkflowType.SCRUM,
            columns=columns,
            sprints=sprints,
            settings=settings
        )
    
    def _kanban_template(self) -> WorkflowTemplate:
        """Kanban 範本"""
        columns = [
            {"name": "Backlog", "status": TaskStatus.BACKLOG.value, "wip": -1},
            {"name": "To Do", "status": TaskStatus.TODO.value, "wip": 5},
            {"name": "In Progress", "status": TaskStatus.IN_PROGRESS.value, "wip": 3},
            {"name": "In Review", "status": TaskStatus.IN_REVIEW.value, "wip": 2},
            {"name": "Done", "status": TaskStatus.DONE.value, "wip": -1},
        ]
        
        settings = {
            "wip_limits": True,
            "continuous_flow": True,
            "cycle_time_tracking": True,
            "cumulative_flow": True,
        }
        
        return WorkflowTemplate(
            name="Kanban",
            type=WorkflowType.KANBAN,
            columns=columns,
            settings=settings
        )
    
    def _spike_template(self) -> WorkflowTemplate:
        """Spike 範本 (研究/探索任務)"""
        columns = [
            {"name": "Research Backlog", "status": TaskStatus.BACKLOG.value, "wip": -1},
            {"name": "Investigating", "status": TaskStatus.IN_PROGRESS.value, "wip": 2},
            {"name": "Documenting", "status": TaskStatus.IN_REVIEW.value, "wip": 2},
            {"name": "Completed", "status": TaskStatus.DONE.value, "wip": -1},
        ]
        
        settings = {
            "timeboxing": True,
            "time_limit": 2,  # 天
            "documentation_required": True,
        }
        
        return WorkflowTemplate(
            name="Spike",
            type=WorkflowType.SPIKE,
            columns=columns,
            settings=settings
        )
    
    def get_template(self, name: str) -> Optional[WorkflowTemplate]:
        """取得範本"""
        return self.templates.get(name.lower())
    
    def list_templates(self) -> List[str]:
        """列出所有範本"""
        return list(self.templates.keys())
    
    def create_project(self, template_name: str, project_name: str) -> Dict:
        """建立專案"""
        template = self.get_template(template_name)
        if not template:
            return {"error": f"Template '{template_name}' not found"}
        
        project = {
            "name": project_name,
            "template": template_name,
            "created_at": datetime.now().isoformat(),
            "columns": template.columns,
            "tasks": [],
            "sprints": [
                {
                    "name": s.name,
                    "goal": s.goal,
                    "start_date": s.start_date.isoformat(),
                    "end_date": s.end_date.isoformat(),
                    "status": s.status,
                }
                for s in template.sprints
            ],
            "settings": template.settings,
        }
        
        return project
    
    def create_task(self, title: str, description: str = "", priority: int = 3) -> Dict:
        """建立任務"""
        return {
            "id": f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "title": title,
            "description": description,
            "status": TaskStatus.BACKLOG.value,
            "priority": priority,
            "assignee": None,
            "sprint": None,
            "story_points": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    templates = WorkflowTemplates()
    
    print("=== Available Templates ===")
    for name in templates.list_templates():
        template = templates.get_template(name)
        print(f"\n{name.upper()}:")
        print(f"  Type: {template.type.value}")
        print(f"  Columns: {[c['name'] for c in template.columns]}")
        print(f"  Settings: {template.settings}")
    
    # 建立專案
    print("\n=== Create Project ===")
    project = templates.create_project("scrum", "我的第一個專案")
    print(f"Project: {project['name']}")
    print(f"Template: {project['template']}")
    print(f"Sprints: {[s['name'] for s in project['sprints']]}")
    
    # 建立任務
    print("\n=== Create Task ===")
    task = templates.create_task("登入功能", "實作使用者登入", priority=2)
    print(f"Task: {task['id']} - {task['title']}")
    print(f"Status: {task['status']}")
