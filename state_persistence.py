#!/usr/bin/env python3
"""
State Persistence - 狀態持久化

支援：
- SQLite (單機)
- Redis (分散式)  
- 檔案系統 (簡單部署)

功能：
- Session 狀態儲存
- 併發鎖定
- 狀態恢復
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import sqlite3
import uuid
import os
import time

class StorageBackend(Enum):
    """存儲後端"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    REDIS = "redis"
    FILE = "file"

@dataclass
class Session:
    """Session 數據結構"""
    session_id: str
    agent_id: str
    state: Dict[str, Any]
    status: str = "active"  # active, locked, completed
    created_at: datetime = field(default=datetime.now)
    updated_at: datetime = field(default=datetime.now)
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "state": self.state,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "locked_by": self.locked_by,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "metadata": self.metadata,
        }

class StatePersistence:
    """
    狀態持久化系統
    
    支援多種後端：
    - Memory: 開發/測試
    - SQLite: 單機部署
    - Redis: 分散式部署
    - File: 簡單部署
    """
    
    def __init__(self, backend: StorageBackend = StorageBackend.SQLITE, config: Dict = None):
        self.backend = backend
        self.config = config or {}
        self.sessions: Dict[str, Session] = {}
        
        if backend == StorageBackend.SQLITE:
            self._init_sqlite()
        elif backend == StorageBackend.REDIS:
            self._init_redis()
        elif backend == StorageBackend.FILE:
            self._init_file()
        else:
            pass  # Memory only
    
    def _init_sqlite(self):
        """初始化 SQLite"""
        db_path = self.config.get("db_path", "./data/sessions.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                state TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                updated_at TEXT,
                locked_by TEXT,
                locked_at TEXT,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        # 載入現有 sessions
        self._load_sessions()
    
    def _load_sessions(self):
        """從 SQLite 載入 sessions"""
        if not hasattr(self, 'db_path'):
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions")
        for row in cursor.fetchall():
            session = Session(
                session_id=row[0],
                agent_id=row[1],
                state=json.loads(row[2]) if row[2] else {},
                status=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                locked_by=row[6],
                locked_at=datetime.fromisoformat(row[7]) if row[7] else None,
                metadata=json.loads(row[8]) if row[8] else {},
            )
            self.sessions[session.session_id] = session
        conn.close()
    
    def _init_redis(self):
        """初始化 Redis"""
        import redis
        host = self.config.get("redis_host", "localhost")
        port = self.config.get("redis_port", 6379)
        self.redis_client = redis.Redis(host=host, port=port, decode_responses=True)
    
    def _init_file(self):
        """初始化檔案系統"""
        self.storage_path = self.config.get("storage_path", "./data/sessions")
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_state(self, session_id: str, agent_id: str, state: Dict[str, Any], 
                   metadata: Dict = None) -> bool:
        """
        儲存 Session 狀態
        
        Args:
            session_id: Session ID
            agent_id: Agent ID
            state: 狀態字典
            metadata: 額外元數據
        
        Returns:
            bool: 是否成功
        """
        now = datetime.now()
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.state = state
            session.updated_at = now
            session.metadata = metadata or session.metadata
        else:
            session = Session(
                session_id=session_id,
                agent_id=agent_id,
                state=state,
                metadata=metadata or {},
            )
            self.sessions[session_id] = session
        
        # 持久化
        if self.backend == StorageBackend.SQLITE:
            return self._save_to_sqlite(session)
        elif self.backend == StorageBackend.REDIS:
            return self._save_to_redis(session)
        elif self.backend == StorageBackend.FILE:
            return self._save_to_file(session)
        
        return True
    
    def _save_to_sqlite(self, session: Session) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions 
            (session_id, agent_id, state, status, created_at, updated_at, locked_by, locked_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.session_id,
            session.agent_id,
            json.dumps(session.state, ensure_ascii=False),
            session.status,
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            session.locked_by,
            session.locked_at.isoformat() if session.locked_at else None,
            json.dumps(session.metadata, ensure_ascii=False),
        ))
        conn.commit()
        conn.close()
        return True
    
    def _save_to_redis(self, session: Session) -> bool:
        key = f"session:{session.session_id}"
        self.redis_client.set(key, json.dumps(session.to_dict(), ensure_ascii=False))
        return True
    
    def _save_to_file(self, session: Session) -> bool:
        path = os.path.join(self.storage_path, f"{session.session_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        載入 Session 狀態
        
        Args:
            session_id: Session ID
        
        Returns:
            狀態字典，如果不存在則返回 None
        """
        session = self.sessions.get(session_id)
        if not session:
            # 嘗試從後端載入
            if self.backend == StorageBackend.SQLITE:
                session = self._load_from_sqlite(session_id)
            elif self.backend == StorageBackend.REDIS:
                session = self._load_from_redis(session_id)
            elif self.backend == StorageBackend.FILE:
                session = self._load_from_file(session_id)
        
        return session.state if session else None
    
    def _load_from_sqlite(self, session_id: str) -> Optional[Session]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        session = Session(
            session_id=row[0],
            agent_id=row[1],
            state=json.loads(row[2]) if row[2] else {},
            status=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            locked_by=row[6],
            locked_at=datetime.fromisoformat(row[7]) if row[7] else None,
            metadata=json.loads(row[8]) if row[8] else {},
        )
        self.sessions[session_id] = session
        return session
    
    def _load_from_redis(self, session_id: str) -> Optional[Session]:
        key = f"session:{session_id}"
        data = self.redis_client.get(key)
        if not data:
            return None
        d = json.loads(data)
        session = Session(
            session_id=d["session_id"],
            agent_id=d["agent_id"],
            state=d.get("state", {}),
            status=d.get("status", "active"),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            locked_by=d.get("locked_by"),
            locked_at=datetime.fromisoformat(d["locked_at"]) if d.get("locked_at") else None,
            metadata=d.get("metadata", {}),
        )
        self.sessions[session_id] = session
        return session
    
    def _load_from_file(self, session_id: str) -> Optional[Session]:
        path = os.path.join(self.storage_path, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            d = json.load(f)
        session = Session(
            session_id=d["session_id"],
            agent_id=d["agent_id"],
            state=d.get("state", {}),
            status=d.get("status", "active"),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            locked_by=d.get("locked_by"),
            locked_at=datetime.fromisoformat(d["locked_at"]) if d.get("locked_at") else None,
            metadata=d.get("metadata", {}),
        )
        self.sessions[session_id] = session
        return session
    
    def lock_session(self, session_id: str, owner: str, timeout: int = 300) -> bool:
        """
        鎖定 Session
        
        Args:
            session_id: Session ID
            owner: 鎖持有者
            timeout: 鎖過期時間（秒）
        
        Returns:
            bool: 是否成功鎖定
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 如果已經被其他人鎖定
        if session.locked_by and session.locked_by != owner:
            # 檢查是否過期
            if session.locked_at:
                elapsed = (datetime.now() - session.locked_at).total_seconds()
                if elapsed < timeout:
                    return False  # 還沒過期，不能搶
        
        session.locked_by = owner
        session.locked_at = datetime.now()
        session.status = "locked"
        
        # 持久化
        if self.backend == StorageBackend.SQLITE:
            self._save_to_sqlite(session)
        elif self.backend == StorageBackend.REDIS:
            self._save_to_redis(session)
        elif self.backend == StorageBackend.FILE:
            self._save_to_file(session)
        
        return True
    
    def unlock_session(self, session_id: str, owner: str) -> bool:
        """
        解鎖 Session
        
        Args:
            session_id: Session ID
            owner: 鎖持有者
        
        Returns:
            bool: 是否成功解鎖
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        # 只能由鎖持有者解鎖
        if session.locked_by != owner:
            return False
        
        session.locked_by = None
        session.locked_at = None
        session.status = "active"
        
        # 持久化
        if self.backend == StorageBackend.SQLITE:
            self._save_to_sqlite(session)
        elif self.backend == StorageBackend.REDIS:
            self._save_to_redis(session)
        elif self.backend == StorageBackend.FILE:
            self._save_to_file(session)
        
        return True
    
    def list_sessions(self, agent_id: str = None, status: str = None) -> List[Session]:
        """列出 Sessions"""
        sessions = list(self.sessions.values())
        
        if agent_id:
            sessions = [s for s in sessions if s.agent_id == agent_id]
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """刪除 Session"""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        
        # 從後端刪除
        if self.backend == StorageBackend.SQLITE:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
        elif self.backend == StorageBackend.REDIS:
            self.redis_client.delete(f"session:{session_id}")
        elif self.backend == StorageBackend.FILE:
            path = os.path.join(self.storage_path, f"{session_id}.json")
            if os.path.exists(path):
                os.remove(path)
        
        return True
    
    def get_status(self) -> dict:
        """取得狀態"""
        return {
            "backend": self.backend.value,
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s.status == "active"]),
            "locked_sessions": len([s for s in self.sessions.values() if s.status == "locked"]),
        }
