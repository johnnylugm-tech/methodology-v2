#!/usr/bin/env python3
"""
Checkpoint Manager - 狀態快照管理

功能：
- 定期快照 Agent 狀態
- 任務完成後自動儲存
- 快照查詢和恢復
- 快照清理策略

AI-native 實作，零額外負擔
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import uuid
import os
from pathlib import Path

class CheckpointStatus(Enum):
    """快照狀態"""
    ACTIVE = "active"           # 活躍快照
    COMMITTED = "committed"     # 已提交的快照
    OBSOLETE = "obsolete"      # 已廢棄

@dataclass
class Checkpoint:
    """快照數據結構"""
    checkpoint_id: str
    agent_id: str
    task_id: str
    state: Dict[str, Any]
    status: CheckpointStatus = CheckpointStatus.ACTIVE
    created_at: datetime = field(default=datetime.now)
    checkpoint_type: str = "auto"  # auto, manual, on_complete
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "checkpoint_type": self.checkpoint_type,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class CheckpointManager:
    """
    狀態快照管理器
    
    功能：
    - 快照儲存（記憶體 + 磁碟）
    - 快照恢復
    - 快照查詢
    - 自動清理
    """
    
    def __init__(self, storage_path: str = None, max_checkpoints: int = 100):
        self.storage_path = storage_path or "./checkpoints"
        self.max_checkpoints = max_checkpoints
        
        # 記憶體緩存
        self.checkpoints: Dict[str, Checkpoint] = {}
        
        # 索引
        self.agent_checkpoints: Dict[str, List[str]] = {}  # agent_id -> checkpoint_ids
        self.task_checkpoints: Dict[str, List[str]] = {}   # task_id -> checkpoint_ids
        
        # 創建存儲目錄
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 載入現有快照
        self._load_from_disk()
    
    def _get_checkpoint_path(self, checkpoint_id: str) -> str:
        return os.path.join(self.storage_path, f"{checkpoint_id}.json")
    
    def _load_from_disk(self):
        """從磁碟載入快照"""
        if not os.path.exists(self.storage_path):
            return
        
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                path = os.path.join(self.storage_path, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    cp = self._deserialize_checkpoint(data)
                    self.checkpoints[cp.checkpoint_id] = cp
                    self._update_index(cp)
                except Exception:
                    pass
    
    def _update_index(self, checkpoint: Checkpoint):
        """更新索引"""
        self.agent_checkpoints.setdefault(checkpoint.agent_id, []).append(checkpoint.checkpoint_id)
        self.task_checkpoints.setdefault(checkpoint.task_id, []).append(checkpoint.checkpoint_id)
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> dict:
        """序列化快照"""
        return {
            **checkpoint.to_dict(),
            "state": checkpoint.state
        }
    
    def _deserialize_checkpoint(self, data: dict) -> Checkpoint:
        """反序列化快照"""
        return Checkpoint(
            checkpoint_id=data["checkpoint_id"],
            agent_id=data["agent_id"],
            task_id=data["task_id"],
            state=data.get("state", {}),
            status=CheckpointStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            checkpoint_type=data.get("checkpoint_type", "auto"),
            metadata=data.get("metadata", {}),
        )
    
    def save(self, agent_id: str, task_id: str, state: Dict[str, Any], 
             checkpoint_type: str = "auto", metadata: Dict = None) -> str:
        """
        儲存快照
        
        Args:
            agent_id: Agent ID
            task_id: 任務 ID
            state: 當前狀態
            checkpoint_type: 快照類型 (auto, manual, on_complete)
            metadata: 額外元數據
        
        Returns:
            checkpoint_id: 快照 ID
        """
        checkpoint_id = f"ckpt-{uuid.uuid4().hex[:12]}"
        
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            agent_id=agent_id,
            task_id=task_id,
            state=state.copy(),
            checkpoint_type=checkpoint_type,
            metadata=metadata or {},
        )
        
        # 儲存到記憶體
        self.checkpoints[checkpoint_id] = checkpoint
        
        # 更新索引
        self._update_index(checkpoint)
        
        # 持久化到磁碟
        path = self._get_checkpoint_path(checkpoint_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._serialize_checkpoint(checkpoint), f, ensure_ascii=False, indent=2)
        
        # 清理舊快照
        self._cleanup_old_checkpoints(agent_id)
        
        return checkpoint_id
    
    def _cleanup_old_checkpoints(self, agent_id: str):
        """清理舊快照"""
        checkpoints = self.list_checkpoints(agent_id)
        if len(checkpoints) > self.max_checkpoints:
            # 刪除最舊的
            sorted_checkpoints = sorted(checkpoints, key=lambda x: x.created_at)
            for cp in sorted_checkpoints[:-self.max_checkpoints]:
                self.delete(cp.checkpoint_id)
    
    def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        恢復快照
        
        Args:
            checkpoint_id: 快照 ID
        
        Returns:
            狀態字典，如果快照不存在則返回 None
        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        if not checkpoint:
            # 嘗試從磁碟載入
            path = self._get_checkpoint_path(checkpoint_id)
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    checkpoint = self._deserialize_checkpoint(data)
                    self.checkpoints[checkpoint_id] = checkpoint
                except Exception:
                    return None
        
        return checkpoint.state if checkpoint else None
    
    def get_latest(self, agent_id: str) -> Optional[Checkpoint]:
        """取得最新快照"""
        checkpoints = self.list_checkpoints(agent_id)
        if not checkpoints:
            return None
        return max(checkpoints, key=lambda x: x.created_at)
    
    def list_checkpoints(self, agent_id: str) -> List[Checkpoint]:
        """列出 Agent 的所有快照"""
        checkpoint_ids = self.agent_checkpoints.get(agent_id, [])
        return [self.checkpoints[cid] for cid in checkpoint_ids if cid in self.checkpoints]
    
    def list_task_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """列出任務的所有快照"""
        checkpoint_ids = self.task_checkpoints.get(task_id, [])
        return [self.checkpoints[cid] for cid in checkpoint_ids if cid in self.checkpoints]
    
    def delete(self, checkpoint_id: str) -> bool:
        """刪除快照"""
        checkpoint = self.checkpoints.get(checkpoint_id)
        if not checkpoint:
            return False
        
        # 從記憶體刪除
        del self.checkpoints[checkpoint_id]
        
        # 從索引刪除
        if checkpoint.agent_id in self.agent_checkpoints:
            self.agent_checkpoints[checkpoint.agent_id].remove(checkpoint_id)
        if checkpoint.task_id in self.task_checkpoints:
            self.task_checkpoints[checkpoint.task_id].remove(checkpoint_id)
        
        # 從磁碟刪除
        path = self._get_checkpoint_path(checkpoint_id)
        if os.path.exists(path):
            os.remove(path)
        
        return True
    
    def get_status(self, agent_id: str) -> dict:
        """取得 Agent 的快照狀態"""
        checkpoints = self.list_checkpoints(agent_id)
        return {
            "agent_id": agent_id,
            "total_checkpoints": len(checkpoints),
            "latest": self.get_latest(agent_id).checkpoint_id if self.get_latest(agent_id) else None,
            "storage_path": self.storage_path,
        }
    
    def export_checkpoint(self, checkpoint_id: str) -> Optional[str]:
        """導出快照為 JSON 字符串"""
        checkpoint = self.checkpoints.get(checkpoint_id)
        if not checkpoint:
            return None
        return checkpoint.to_json()
    
    def import_checkpoint(self, json_str: str) -> Optional[str]:
        """從 JSON 導入快照"""
        try:
            data = json.loads(json_str)
            checkpoint = self._deserialize_checkpoint(data)
            checkpoint.checkpoint_id = f"ckpt-{uuid.uuid4().hex[:12]}"  # 新 ID
            self.checkpoints[checkpoint.checkpoint_id] = checkpoint
            self._update_index(checkpoint)
            path = self._get_checkpoint_path(checkpoint.checkpoint_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._serialize_checkpoint(checkpoint), f, ensure_ascii=False, indent=2)
            return checkpoint.checkpoint_id
        except Exception:
            return None


class SessionManager:
    """
    Session save/load 管理器
    
    功能：
    - 儲存完整 session state（messages, context, artifacts, metadata）
    - 還原完整 session state
    - 列出所有 saved sessions
    - 刪除指定 session
    """
    
    SESSIONS_DIR = Path(".methodology/sessions")
    
    def __init__(self):
        self.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    def save(self, session_id: str, state: dict) -> str:
        """
        儲存完整 session state
        
        Args:
            session_id: Session ID
            state: 完整 session 狀態（包含 messages, context, artifacts, metadata）
        
        Returns:
            儲存檔案路徑
        """
        path = self.SESSIONS_DIR / f"{session_id}.json"
        
        # 附加 metadata
        session_data = {
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            **state
        }
        
        path.write_text(json.dumps(session_data, indent=2, ensure_ascii=False))
        return str(path)
    
    def load(self, session_id: str) -> dict:
        """
        還原完整 session state
        
        Args:
            session_id: Session ID
        
        Returns:
            完整 session 狀態字典
        """
        path = self.SESSIONS_DIR / f"{session_id}.json"
        return json.loads(path.read_text())
    
    def list(self) -> list[dict]:
        """
        列出所有 saved sessions
        
        Returns:
            Session 列表（包含 id, path, size, saved_at）
        """
        sessions = []
        for p in self.SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text())
                sessions.append({
                    "id": p.stem,
                    "path": str(p),
                    "size": p.stat().st_size,
                    "saved_at": data.get("saved_at", "unknown")
                })
            except Exception:
                sessions.append({
                    "id": p.stem,
                    "path": str(p),
                    "size": p.stat().st_size,
                    "saved_at": "unknown"
                })
        return sorted(sessions, key=lambda x: x["id"])
    
    def delete(self, session_id: str) -> bool:
        """
        刪除指定 session
        
        Args:
            session_id: Session ID
        
        Returns:
            是否成功刪除
        """
        path = self.SESSIONS_DIR / f"{session_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False
    
    def exists(self, session_id: str) -> bool:
        """檢查 session 是否存在"""
        path = self.SESSIONS_DIR / f"{session_id}.json"
        return path.exists()
    
    def get_info(self, session_id: str) -> Optional[dict]:
        """取得 session 資訊"""
        path = self.SESSIONS_DIR / f"{session_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return {
                "id": session_id,
                "path": str(path),
                "size": path.stat().st_size,
                "saved_at": data.get("saved_at", "unknown"),
                "has_messages": "messages" in data,
                "has_context": "context" in data,
                "has_artifacts": "artifacts" in data,
                "has_metadata": "metadata" in data,
            }
        except Exception:
            return {
                "id": session_id,
                "path": str(path),
                "size": path.stat().st_size,
                "saved_at": "unknown"
            }