#!/usr/bin/env python3
"""
Agent State - 共享狀態管理

LangGraph 風格的狀態傳遞系統
"""

import json
from typing import Dict, List, Optional, Any, Callable, TypeVar
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Artifact:
    """產出物"""
    id: str
    type: str  # "code", "document", "test", "design"
    name: str
    content: str
    format: str = "text"  # "text", "json", "markdown"
    metadata: Dict = field(default_factory=dict)
    created_by: str = None
    created_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def update(self, content: str):
        self.content = content
        self.version += 1
        self.metadata["last_updated"] = datetime.now().isoformat()


@dataclass
class AgentTask:
    """任務（帶狀態）"""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    
    # 負責人
    assigned_to: str = None
    created_by: str = None
    
    # 依賴
    depends_on: List[str] = field(default_factory=list)
    
    # 產出
    artifacts: List[Artifact] = field(default_factory=list)
    
    # 上下文
    context: Dict = field(default_factory=dict)
    
    # 結果
    result: Any = None
    error: str = None
    
    # 時間戳
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    estimated_duration_minutes: int = 30
    
    # 優先級
    priority: int = 0  # 越大越優先
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "depends_on": self.depends_on,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentState:
    """共享狀態"""
    # 任務
    tasks: Dict[str, AgentTask] = field(default_factory=dict)
    
    # 當前處理的任務
    current_task_id: str = None
    
    # Agent 上下文
    agent_context: Dict[str, Dict] = field(default_factory=dict)
    
    # 共享資料
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
    # 產出物
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    
    # 待批准
    pending_approvals: List[Dict] = field(default_factory=list)
    
    # 訊息
    messages: List[Dict] = field(default_factory=list)
    
    # 歷史（用於追蹤）
    history: List[Dict] = field(default_factory=list)
    
    # 版本（用於並發控制）
    version: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "current_task": self.current_task_id,
            "tasks_count": len(self.tasks),
            "artifacts_count": len(self.artifacts),
            "pending_approvals": len(self.pending_approvals),
            "messages_count": len(self.messages),
            "version": self.version,
        }


class StateManager:
    """狀態管理器"""
    
    def __init__(self):
        self.state = AgentState()
        self.listeners: List[Callable] = []
        self.lock = threading.RLock()
    
    def update_state(self, updates: Dict):
        """更新狀態"""
        with self.lock:
            for key, value in updates.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)
            
            self.state.version += 1
            
            # 記錄歷史
            self.state.history.append({
                "timestamp": datetime.now().isoformat(),
                "version": self.state.version,
                "updates": list(updates.keys()),
            })
            
            # 通知監聽器
            self._notify()
    
    def get_state(self) -> AgentState:
        """取得當前狀態"""
        return self.state
    
    def add_task(self, task: AgentTask) -> str:
        """新增任務"""
        with self.lock:
            self.state.tasks[task.id] = task
            self.state.version += 1
            
            self._record_change("task_added", {"task_id": task.id})
            
            return task.id
    
    def update_task(self, task_id: str, updates: Dict) -> bool:
        """更新任務"""
        with self.lock:
            task = self.state.tasks.get(task_id)
            if not task:
                return False
            
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            self.state.version += 1
            
            self._record_change("task_updated", {"task_id": task_id, "updates": list(updates.keys())})
            
            return True
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """取得任務"""
        return self.state.tasks.get(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[AgentTask]:
        """取得特定狀態的任務"""
        return [t for t in self.state.tasks.values() if t.status == status]
    
    def get_tasks_by_agent(self, agent_id: str) -> List[AgentTask]:
        """取得特定 Agent 的任務"""
        return [t for t in self.state.tasks.values() if t.assigned_to == agent_id]
    
    def get_ready_tasks(self, agent_id: str = None) -> List[AgentTask]:
        """取得可以開始的任務"""
        ready = []
        
        for task in self.state.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # 檢查依賴
            deps_ready = all(
                self.state.tasks.get(dep_id) and 
                self.state.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
            
            if not deps_ready:
                continue
            
            # 如果指定了 agent，檢查是否匹配
            if agent_id and task.assigned_to and task.assigned_to != agent_id:
                continue
            
            ready.append(task)
        
        # 按優先級排序
        ready.sort(key=lambda t: -t.priority)
        
        return ready
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """指派任務"""
        return self.update_task(task_id, {
            "assigned_to": agent_id,
            "status": TaskStatus.IN_PROGRESS,
            "started_at": datetime.now()
        })
    
    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """完成任務"""
        task = self.state.tasks.get(task_id)
        if not task:
            return False
        
        # 更新任務
        self.update_task(task_id, {
            "status": TaskStatus.COMPLETED,
            "result": result,
            "completed_at": datetime.now()
        })
        
        # 記錄產出
        if result:
            artifact = Artifact(
                id=f"artifact-{task_id}",
                type="result",
                name=f"Result of {task_id}",
                content=str(result),
                created_by=task.assigned_to
            )
            self.add_artifact(artifact)
        
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """任務失敗"""
        return self.update_task(task_id, {
            "status": TaskStatus.FAILED,
            "error": error
        })
    
    def add_artifact(self, artifact: Artifact) -> str:
        """新增產出物"""
        with self.lock:
            self.state.artifacts[artifact.id] = artifact
            self.state.version += 1
            
            self._record_change("artifact_added", {"artifact_id": artifact.id})
            
            return artifact.id
    
    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """取得產出物"""
        return self.state.artifacts.get(artifact_id)
    
    def update_shared_data(self, key: str, value: Any):
        """更新共享資料"""
        with self.lock:
            self.state.shared_data[key] = value
            self.state.version += 1
            
            self._record_change("shared_data_updated", {"key": key})
    
    def get_shared_data(self, key: str) -> Any:
        """取得共享資料"""
        return self.state.shared_data.get(key)
    
    def add_message(self, from_agent: str, to_agent: str,
                  content: str, msg_type: str = "message"):
        """新增訊息"""
        with self.lock:
            self.state.messages.append({
                "from": from_agent,
                "to": to_agent,
                "content": content,
                "type": msg_type,
                "timestamp": datetime.now().isoformat()
            })
            
            self.state.version += 1
    
    def request_approval(self, task_id: str, approver: str,
                         reason: str, context: Dict = None) -> str:
        """請求審批"""
        approval_id = f"approval-{len(self.state.pending_approvals) + 1}"
        
        with self.lock:
            self.state.pending_approvals.append({
                "id": approval_id,
                "task_id": task_id,
                "approver": approver,
                "reason": reason,
                "context": context or {},
                "status": "pending",
                "created_at": datetime.now().isoformat()
            })
            
            self.state.version += 1
            
            self._record_change("approval_requested", {"approval_id": approval_id})
            
            return approval_id
    
    def approve(self, approval_id: str, approved: bool = True,
               comment: str = None) -> bool:
        """審批"""
        with self.lock:
            for approval in self.state.pending_approvals:
                if approval["id"] == approval_id:
                    approval["status"] = "approved" if approved else "rejected"
                    approval["resolved_at"] = datetime.now().isoformat()
                    approval["comment"] = comment
                    
                    self.state.version += 1
                    
                    self._record_change("approval_resolved", {
                        "approval_id": approval_id,
                        "approved": approved
                    })
                    
                    return True
            
            return False
    
    def _record_change(self, change_type: str, data: Dict):
        """記錄變更"""
        self.state.history.append({
            "timestamp": datetime.now().isoformat(),
            "change_type": change_type,
            "data": data,
            "version": self.state.version
        })
    
    def _notify(self):
        """通知監聽器"""
        for listener in self.listeners:
            try:
                listener(self.state)
            except Exception as e:
                logger.debug(f"Listener callback failed: {e}")
    
    def register_listener(self, listener: Callable):
        """註冊監聽器"""
        self.listeners.append(listener)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """取得歷史"""
        return self.state.history[-limit:]
    
    def get_snapshot(self) -> Dict:
        """取得快照"""
        return {
            "state": self.state.to_dict(),
            "tasks": [t.to_dict() for t in self.state.tasks.values()],
            "artifacts": {
                k: {
                    "id": a.id,
                    "type": a.type,
                    "name": a.name,
                    "version": a.version,
                    "created_by": a.created_by,
                }
                for k, a in self.state.artifacts.items()
            },
            "pending_approvals": len(self.state.pending_approvals),
            "history_count": len(self.state.history),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        snapshot = self.get_snapshot()
        
        by_status = defaultdict(int)
        for task in self.state.tasks.values():
            by_status[task.status.value] += 1
        
        report = f"""
# 📊 Agent State 報告

## 快照

| 指標 | 數值 |
|------|------|
| 總任務數 | {snapshot['state']['tasks_count']} |
| 產出物 | {snapshot['state']['artifacts_count']} |
| 待審批 | {snapshot['pending_approvals']} |
| 版本 | {snapshot['state']['version']} |

---

## 任務狀態分佈

| 狀態 | 數量 |
|------|------|
"""
        
        for status, count in sorted(by_status.items()):
            report += f"| {status} | {count} |\n"
        
        report += f"""

## 待審批

"""
        
        for approval in self.state.pending_approvals:
            if approval["status"] == "pending":
                report += f"- [{approval['id']}] {approval['reason']} (請求者: {approval['approver']})\n"
        
        return report

        return report
    
    # ==================== 持久化 ====================
    
    def save(self, path: str = "~/.methodology/agent_state.json"):
        """保存 Agent 狀態到檔案"""
        import json
        import os
        
        path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {
            "tasks": {
                tid: {
                    "id": t.id,
                    "description": t.description,
                    "status": t.status.value,
                    "assigned_to": t.assigned_to,
                    "priority": t.priority,
                    "created_at": t.created_at.isoformat(),
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "result": t.result,
                    "error": t.error,
                }
                for tid, t in self.state.tasks.items()
            },
            "artifacts": dict(self.state.artifacts),
            "shared_data": dict(self.state.shared_data),
            "approvals": [
                {
                    "id": a.id,
                    "task_id": a.task_id,
                    "approver": a.approver,
                    "reason": a.reason,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                    "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
                }
                for a in self.state.approvals
            ],
            "version": self.state.version,
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: str = "~/.methodology/agent_state.json") -> bool:
        """從檔案載入 Agent 狀態"""
        import json
        import os
        
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return False
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 恢復 tasks
        self.state.tasks = {
            tid: AgentTask(
                id=tdata["id"],
                description=tdata["description"],
                status=TaskStatus(tdata["status"]),
                assigned_to=tdata.get("assigned_to"),
                priority=tdata.get("priority", 3),
                created_at=datetime.fromisoformat(tdata["created_at"]),
                started_at=datetime.fromisoformat(tdata["started_at"]) if tdata.get("started_at") else None,
                completed_at=datetime.fromisoformat(tdata["completed_at"]) if tdata.get("completed_at") else None,
                result=tdata.get("result"),
                error=tdata.get("error"),
            )
            for tid, tdata in data.get("tasks", {}).items()
        }
        
        # 恢復 artifacts
        self.state.artifacts = dict(data.get("artifacts", {}))
        
        # 恢復 shared_data
        self.state.shared_data = dict(data.get("shared_data", {}))
        
        # 恢復 approvals
        self.state.approvals = [
            Approval(
                id=adata["id"],
                task_id=adata["task_id"],
                approver=adata["approver"],
                reason=adata["reason"],
                status=ApprovalStatus(adata["status"]),
                created_at=datetime.fromisoformat(adata["created_at"]),
                reviewed_at=datetime.fromisoformat(adata["reviewed_at"]) if adata.get("reviewed_at") else None,
            )
            for adata in data.get("approvals", [])
        ]
        
        # 恢復 version
        self.state.version = data.get("version", 1)
        
        return True

