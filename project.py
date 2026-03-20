#!/usr/bin/env python3
"""
Project - 統一專案抽象層

整合所有模組，提供統一的專案管理和持久化
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import os


class ProjectDatabase:
    """專案資料庫"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser("~/.methodology/projects.db")
        self._init_db()
    
    def _init_db(self):
        """初始化資料庫"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 專案表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        """)
        
        # 任務表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                description TEXT,
                status TEXT,
                assigned_to TEXT,
                priority INTEGER,
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 成本表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                user_id TEXT,
                cost_type TEXT,
                amount REAL,
                model TEXT,
                tokens INTEGER,
                description TEXT,
                timestamp TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 審計日誌表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                user_id TEXT,
                action TEXT,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                timestamp TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 交付物表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliverables (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT,
                version TEXT,
                status TEXT,
                author TEXT,
                created_at TEXT,
                released_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # 團隊成員表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT,
                role TEXT,
                email TEXT,
                created_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        """執行 SQL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        result = cursor.lastrowid
        conn.close()
        return result
    
    def fetch(self, query: str, params: tuple = ()) -> List:
        """查詢"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result


@dataclass
class Project:
    """統一專案"""
    id: str
    name: str
    description: str = ""
    
    # 創建者
    created_by: str = "system"
    
    # 時間戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 元數據
    metadata: Dict = field(default_factory=dict)
    
    # 資料庫
    _db: ProjectDatabase = None
    
    # 整合的模組
    _state_manager: Any = None
    _team: Any = None
    _communication: Any = None
    _audit: Any = None
    
    @classmethod
    def create(cls, name: str, description: str = "",
               created_by: str = "system", db_path: str = None) -> "Project":
        """建立專案"""
        project_id = f"proj-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        project = cls(
            id=project_id,
            name=name,
            description=description,
            created_by=created_by,
        )
        
        # 初始化資料庫
        project._db = ProjectDatabase(db_path)
        
        # 保存到資料庫
        project._db.execute(
            """INSERT INTO projects (id, name, description, created_at, updated_at, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (project.id, project.name, project.description,
             project.created_at.isoformat(), project.updated_at.isoformat(),
             json.dumps(project.metadata))
        )
        
        return project
    
    @classmethod
    def load(cls, project_id: str, db_path: str = None) -> Optional["Project"]:
        """載入專案"""
        db = ProjectDatabase(db_path)
        
        rows = db.fetch("SELECT * FROM projects WHERE id = ?", (project_id,))
        if not rows:
            return None
        
        row = rows[0]
        project = cls(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            created_at=datetime.fromisoformat(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
            metadata=json.loads(row[5]) if row[5] else {},
        )
        project._db = db
        
        return project
    
    @classmethod
    def list_all(cls, db_path: str = None) -> List["Project"]:
        """列出所有專案"""
        db = ProjectDatabase(db_path)
        
        rows = db.fetch("SELECT id FROM projects ORDER BY created_at DESC")
        
        projects = []
        for row in rows:
            project = cls.load(row[0], db_path)
            if project:
                projects.append(project)
        
        return projects
    
    def save(self):
        """保存專案"""
        self.updated_at = datetime.now()
        self._db.execute(
            """UPDATE projects SET name = ?, description = ?, updated_at = ?, metadata = ?
               WHERE id = ?""",
            (self.name, self.description, self.updated_at.isoformat(),
             json.dumps(self.metadata), self.id)
        )
    
    def delete(self):
        """刪除專案"""
        self._db.execute("DELETE FROM tasks WHERE project_id = ?", (self.id,))
        self._db.execute("DELETE FROM costs WHERE project_id = ?", (self.id,))
        self._db.execute("DELETE FROM audit_log WHERE project_id = ?", (self.id,))
        self._db.execute("DELETE FROM deliverables WHERE project_id = ?", (self.id,))
        self._db.execute("DELETE FROM team_members WHERE project_id = ?", (self.id,))
        self._db.execute("DELETE FROM projects WHERE id = ?", (self.id,))
    
    # ==================== 任務管理 ====================
    
    def add_task(self, description: str, assigned_to: str = None,
                priority: int = 0) -> str:
        """新增任務"""
        task_id = f"task-{len(self.list_tasks()) + 1}"
        now = datetime.now().isoformat()
        
        self._db.execute(
            """INSERT INTO tasks (id, project_id, description, status, assigned_to, priority, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, self.id, description, "pending", assigned_to, priority, now, now)
        )
        
        self._log("create", "task", task_id, {"description": description})
        
        return task_id
    
    def list_tasks(self, status: str = None) -> List[Dict]:
        """列出任務"""
        if status:
            rows = self._db.fetch(
                "SELECT * FROM tasks WHERE project_id = ? AND status = ? ORDER BY priority DESC",
                (self.id, status)
            )
        else:
            rows = self._db.fetch(
                "SELECT * FROM tasks WHERE project_id = ? ORDER BY priority DESC",
                (self.id,)
            )
        
        return [
            {
                "id": r[0],
                "description": r[2],
                "status": r[3],
                "assigned_to": r[4],
                "priority": r[5],
                "created_at": r[6],
                "updated_at": r[7],
                "completed_at": r[8],
            }
            for r in rows
        ]
    
    def complete_task(self, task_id: str):
        """完成任務"""
        now = datetime.now().isoformat()
        self._db.execute(
            "UPDATE tasks SET status = ?, completed_at = ?, updated_at = ? WHERE id = ?",
            ("completed", now, now, task_id)
        )
        self._log("complete", "task", task_id)
    
    def fail_task(self, task_id: str, error: str):
        """標記任務失敗"""
        now = datetime.now().isoformat()
        self._db.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            ("failed", now, task_id)
        )
        self._log("fail", "task", task_id, {"error": error})
    
    # ==================== 成本管理 ====================
    
    def add_cost(self, user_id: str, cost_type: str, amount: float,
                model: str = None, tokens: int = 0, description: str = ""):
        """記錄成本"""
        now = datetime.now().isoformat()
        
        self._db.execute(
            """INSERT INTO costs (project_id, user_id, cost_type, amount, model, tokens, description, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.id, user_id, cost_type, amount, model, tokens, description, now)
        )
        
        self._log("create", "cost", str(amount), {"user_id": user_id, "type": cost_type})
    
    def get_costs(self, days: int = 30) -> Dict:
        """取得成本"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        rows = self._db.fetch(
            "SELECT * FROM costs WHERE project_id = ? AND timestamp >= ?",
            (self.id, cutoff)
        )
        
        total = sum(r[4] for r in rows)  # amount column
        
        by_user = {}
        by_type = {}
        
        for r in rows:
            user = r[2]
            cost_type = r[3]
            
            by_user[user] = by_user.get(user, 0) + r[4]
            by_type[cost_type] = by_type.get(cost_type, 0) + r[4]
        
        return {
            "total": total,
            "count": len(rows),
            "by_user": by_user,
            "by_type": by_type,
        }
    
    # ==================== 審計日誌 ====================
    
    def _log(self, action: str, resource_type: str, resource_id: str,
            details: Dict = None):
        """記錄審計日誌"""
        now = datetime.now().isoformat()
        
        self._db.execute(
            """INSERT INTO audit_log (project_id, user_id, action, resource_type, resource_id, details, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (self.id, self.created_by, action, resource_type, resource_id,
             json.dumps(details or {}), now)
        )
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """取得審計日誌"""
        rows = self._db.fetch(
            """SELECT * FROM audit_log WHERE project_id = ? 
               ORDER BY timestamp DESC LIMIT ?""",
            (self.id, limit)
        )
        
        return [
            {
                "id": r[0],
                "user_id": r[2],
                "action": r[3],
                "resource_type": r[4],
                "resource_id": r[5],
                "details": json.loads(r[6]) if r[6] else {},
                "timestamp": r[7],
            }
            for r in rows
        ]
    
    # ==================== 交付物管理 ====================
    
    def add_deliverable(self, name: str, author: str, version: str = "1.0.0") -> str:
        """新增交付物"""
        deliverable_id = f"del-{len(self.list_deliverables()) + 1}"
        now = datetime.now().isoformat()
        
        self._db.execute(
            """INSERT INTO deliverables (id, project_id, name, version, status, author, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (deliverable_id, self.id, name, version, "draft", author, now)
        )
        
        self._log("create", "deliverable", deliverable_id, {"name": name})
        
        return deliverable_id
    
    def list_deliverables(self) -> List[Dict]:
        """列出交付物"""
        rows = self._db.fetch(
            "SELECT * FROM deliverables WHERE project_id = ? ORDER BY created_at DESC",
            (self.id,)
        )
        
        return [
            {
                "id": r[0],
                "name": r[2],
                "version": r[3],
                "status": r[4],
                "author": r[5],
                "created_at": r[6],
                "released_at": r[7],
            }
            for r in rows
        ]
    
    def release_deliverable(self, deliverable_id: str):
        """發布交付物"""
        now = datetime.now().isoformat()
        
        self._db.execute(
            "UPDATE deliverables SET status = ?, released_at = ? WHERE id = ?",
            ("released", now, deliverable_id)
        )
        
        self._log("release", "deliverable", deliverable_id)
    
    # ==================== 團隊管理 ====================
    
    def add_team_member(self, name: str, role: str, email: str = "") -> str:
        """新增團隊成員"""
        member_id = f"member-{len(self.list_team_members()) + 1}"
        now = datetime.now().isoformat()
        
        self._db.execute(
            """INSERT INTO team_members (id, project_id, name, role, email, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (member_id, self.id, name, role, email, now)
        )
        
        self._log("create", "team_member", member_id, {"name": name, "role": role})
        
        return member_id
    
    def list_team_members(self) -> List[Dict]:
        """列出團隊成員"""
        rows = self._db.fetch(
            "SELECT * FROM team_members WHERE project_id = ?",
            (self.id,)
        )
        
        return [
            {
                "id": r[0],
                "name": r[2],
                "role": r[3],
                "email": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]
    
    # ==================== 統計 ====================
    
    def get_summary(self) -> Dict:
        """取得專案摘要"""
        tasks = self.list_tasks()
        completed = len([t for t in tasks if t["status"] == "completed"])
        failed = len([t for t in tasks if t["status"] == "failed"])
        pending = len([t for t in tasks if t["status"] == "pending"])
        
        costs = self.get_costs()
        deliverables = self.list_deliverables()
        members = self.list_team_members()
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tasks": {
                "total": len(tasks),
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "completion_rate": (completed / len(tasks) * 100) if tasks else 0,
            },
            "costs": {
                "total": costs["total"],
                "count": costs["count"],
            },
            "deliverables": len(deliverables),
            "team_members": len(members),
        }
    
    def generate_report(self) -> str:
        """生成專案報告"""
        summary = self.get_summary()
        recent_tasks = self.list_tasks()[:5]
        recent_audit = self.get_audit_log(10)
        
        report = f"""
# 📊 專案報告: {self.name}

## 基本資訊

| 項目 | 數值 |
|------|------|
| ID | {self.id} |
| 建立時間 | {self.created_at.strftime('%Y-%m-%d %H:%M')} |
| 更新時間 | {self.updated_at.strftime('%Y-%m-%d %H:%M')} |

---

## 任務統計

| 指標 | 數值 |
|------|------|
| 總任務 | {summary['tasks']['total']} |
| 已完成 | {summary['tasks']['completed']} |
| 失敗 | {summary['tasks']['failed']} |
| 待處理 | {summary['tasks']['pending']} |
| 完成率 | {summary['tasks']['completion_rate']:.1f}% |

---

## 成本統計

| 指標 | 數值 |
|------|------|
| 總成本 | ${summary['costs']['total']:.4f} |
| 記錄數 | {summary['costs']['count']} |

---

## 交付物

- 總數: {summary['deliverables']}

## 團隊

- 成員數: {summary['team_members']}

---

## 最近活動

"""
        
        for log in recent_audit[:5]:
            report += f"- [{log['timestamp']}] {log['action']} {log['resource_type']}\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import tempfile
    
    # 使用臨時資料庫
    db_path = f"{tempfile.gettempdir()}/test_project.db"
    
    print("=== Create Project ===")
    project = Project.create("AI 客服系統", "開發智能客服系統", db_path=db_path)
    print(f"Created: {project.id} - {project.name}")
    
    print("\n=== Add Tasks ===")
    t1 = project.add_task("設計系統架構", priority=3)
    t2 = project.add_task("實作用戶認證", assigned_to="dev-1", priority=2)
    t3 = project.add_task("實作聊天功能", priority=2)
    print(f"Added tasks: {t1}, {t2}, {t3}")
    
    print("\n=== Complete Task ===")
    project.complete_task(t1)
    print(f"Completed: {t1}")
    
    print("\n=== Add Costs ===")
    project.add_cost("dev-1", "api_call", 0.05, "gpt-4o", 1000)
    project.add_cost("dev-1", "api_call", 0.02, "claude", 500)
    project.add_cost("dev-2", "compute", 0.10)
    print("Costs added")
    
    print("\n=== Add Team Members ===")
    project.add_team_member("小明", "developer", "xiaoming@example.com")
    project.add_team_member("小美", "pm", "xiaomei@example.com")
    print("Team members added")
    
    print("\n=== Add Deliverable ===")
    d1 = project.add_deliverable("API 文檔", "小明")
    project.release_deliverable(d1)
    print("Deliverable added and released")
    
    print("\n=== Project Summary ===")
    summary = project.get_summary()
    print(f"Tasks: {summary['tasks']}")
    print(f"Costs: ${summary['costs']['total']:.4f}")
    print(f"Team: {summary['team_members']} members")
    
    print("\n=== Report ===")
    print(project.generate_report())
    
    print("\n=== Load Project ===")
    loaded = Project.load(project.id, db_path=db_path)
    print(f"Loaded: {loaded.name}")
    print(f"Tasks: {len(loaded.list_tasks())}")
    print(f"Audit log: {len(loaded.get_audit_log())} entries")
    
    print("\n=== List All Projects ===")
    projects = Project.list_all(db_path=db_path)
    print(f"Total projects: {len(projects)}")
    
    # 清理
    import os
    os.unlink(db_path)
