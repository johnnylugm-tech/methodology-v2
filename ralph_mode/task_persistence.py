"""
Ralph Mode - 任務持久化模組

Ralph Mode 為長時任務提供狀態持久化機制，確保任務中斷後能恢復執行。
適用於需要長時間運行的批次任務監控。

Author: methodology-v2
Version: 1.0.0
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any
from pathlib import Path

# Framework Enforcement
try:
    from methodology import FrameworkEnforcer
    _FRAMEWORK_OK = True
except ImportError:
    _FRAMEWORK_OK = False


@dataclass
class TaskState:
    """
    任務狀態資料類
    
    Attributes:
        task_id: 任務唯一識別碼
        status: 任務狀態 (pending, running, paused, completed, failed)
        current_phase: 當前任務階段
        progress: 進度百分比 (0-100)
        last_check: 最後檢查時間 (ISO 格式)
        metadata: 額外元資料
        created_at: 建立時間
        updated_at: 更新時間
    """
    task_id: str
    status: str = "pending"
    current_phase: str = "init"
    progress: float = 0.0
    last_check: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """初始化時間戳"""
        now = datetime.now().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
        if self.last_check is None:
            self.last_check = now

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskState":
        """從字典建立實例"""
        return cls(**data)


class TaskPersistence:
    """
    任務持久化管理器
    
    使用 JSON 檔案實現任務狀態的持久化，支援任務的保存與恢復。
    
    Example:
        >>> persistence = TaskPersistence()
        >>> state = TaskState(task_id="task-001", status="running", current_phase="run_batch")
        >>> persistence.save_state(state)
        >>> loaded = persistence.load_state("task-001")
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化持久化管理器
        
        Args:
            storage_dir: 儲存目錄路徑，預設為 .ralph/tasks
        """
        if storage_dir is None:
            storage_dir = os.path.join(os.getcwd(), ".ralph", "tasks")
        
        self.storage_dir = Path(storage_dir)
        self.state_file = self.storage_dir / "states.json"
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """確保儲存目錄存在"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化狀態檔案（如果不存在）
        if not self.state_file.exists():
            self._save_all_states({})

    def _load_all_states(self) -> Dict[str, Any]:
        """載入所有任務狀態"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_all_states(self, states: Dict[str, Any]) -> None:
        """儲存所有任務狀態"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(states, f, indent=2, ensure_ascii=False)

    def save_state(self, state: TaskState) -> bool:
        """
        保存任務狀態
        
        Args:
            state: TaskState 實例
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 更新時間戳
            state.updated_at = datetime.now().isoformat()
            state.last_check = datetime.now().isoformat()

            # 載入現有狀態
            all_states = self._load_all_states()
            
            # 更新狀態
            all_states[state.task_id] = state.to_dict()
            
            # 儲存
            self._save_all_states(all_states)
            return True

        except Exception as e:
            print(f"[Ralph] 保存狀態失敗: {e}")
            return False

    def load_state(self, task_id: str) -> Optional[TaskState]:
        """
        載入任務狀態
        
        Args:
            task_id: 任務 ID
        
        Returns:
            TaskState 或 None（如果不存在）
        """
        try:
            all_states = self._load_all_states()
            
            if task_id not in all_states:
                return None
            
            return TaskState.from_dict(all_states[task_id])

        except Exception as e:
            print(f"[Ralph] 載入狀態失敗: {e}")
            return None

    def delete_state(self, task_id: str) -> bool:
        """
        刪除任務狀態
        
        Args:
            task_id: 任務 ID
        
        Returns:
            bool: 刪除是否成功
        """
        try:
            all_states = self._load_all_states()
            
            if task_id in all_states:
                del all_states[task_id]
                self._save_all_states(all_states)
            
            return True

        except Exception as e:
            print(f"[Ralph] 刪除狀態失敗: {e}")
            return False

    def list_tasks(self, status: Optional[str] = None) -> list:
        """
        列出所有任務
        
        Args:
            status: 可選的狀態過濾
        
        Returns:
            TaskState 列表
        """
        all_states = self._load_all_states()
        tasks = [TaskState.from_dict(s) for s in all_states.values()]
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        return tasks

    def update_progress(self, task_id: str, progress: float) -> bool:
        """
        更新任務進度
        
        Args:
            task_id: 任務 ID
            progress: 進度值 (0-100)
        
        Returns:
            bool: 更新是否成功
        """
        state = self.load_state(task_id)
        if state is None:
            return False
        
        state.progress = max(0.0, min(100.0, progress))
        return self.save_state(state)