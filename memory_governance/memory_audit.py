#!/usr/bin/env python3
"""
Memory Audit
============
不可偽造的記憶審計日誌

功能：
- 記錄所有記憶操作
- 生成 SHA-256 簽名
- 驗證記憶完整性
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import hashlib
import json
import sqlite3


@dataclass
class MemoryRecord:
    """記憶記錄"""
    record_id: str
    agent_id: str
    action: str  # read, write, delete
    memory_key: str
    timestamp: datetime
    signature: str  # SHA-256
    verified: bool = True


class MemoryAudit:
    """
    記憶審計
    
    使用方式：
    
    ```python
    audit = MemoryAudit()
    
    # 記錄操作
    audit.record("agent-1", "write", "preference", {"value": "dark"})
    
    # 驗證
    if audit.verify(record_id):
        print("Record is authentic")
    ```
    """
    
    def __init__(self, db_path: str = ".methodology/memory_audit.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """確保資料庫存在"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT UNIQUE,
                agent_id TEXT,
                action TEXT,
                memory_key TEXT,
                timestamp TEXT,
                signature TEXT UNIQUE,
                verified INTEGER DEFAULT 1,
                extra TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _generate_signature(self, data: Dict) -> str:
        """生成簽名"""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def record(
        self,
        agent_id: str,
        action: str,
        memory_key: str,
        extra: Dict = None
    ) -> str:
        """
        記錄記憶操作
        
        Returns:
            str: record_id
        """
        timestamp = datetime.now()
        record_id = f"mem-{timestamp.strftime('%Y%m%d%H%M%S%f')}"
        
        data = {
            "record_id": record_id,
            "agent_id": agent_id,
            "action": action,
            "memory_key": memory_key,
            "timestamp": timestamp.isoformat(),
            "extra": extra or {}
        }
        
        signature = self._generate_signature(data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory_audit 
            (record_id, agent_id, action, memory_key, timestamp, signature, extra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            agent_id,
            action,
            memory_key,
            timestamp.isoformat(),
            signature,
            json.dumps(extra or {})
        ))
        conn.commit()
        conn.close()
        
        return record_id
    
    def verify(self, record_id: str) -> bool:
        """驗證記錄是否被篡改"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT agent_id, action, memory_key, timestamp, extra FROM memory_audit WHERE record_id=?",
            (record_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False
        
        # 重新計算簽名
        data = {
            "record_id": record_id,
            "agent_id": row[0],
            "action": row[1],
            "memory_key": row[2],
            "timestamp": row[3],
            "extra": json.loads(row[4])
        }
        
        expected_signature = self._generate_signature(data)
        
        # 比對
        cursor = conn.cursor()
        cursor.execute(
            "SELECT signature FROM memory_audit WHERE record_id=?",
            (record_id,)
        )
        actual_signature = cursor.fetchone()[0]
        conn.close()
        
        return expected_signature == actual_signature
    
    def get_records(
        self,
        agent_id: str = None,
        limit: int = 100
    ) -> List[MemoryRecord]:
        """取得記錄"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent_id:
            cursor.execute("""
                SELECT record_id, agent_id, action, memory_key, timestamp, signature, verified
                FROM memory_audit
                WHERE agent_id=?
                ORDER BY id DESC
                LIMIT ?
            """, (agent_id, limit))
        else:
            cursor.execute("""
                SELECT record_id, agent_id, action, memory_key, timestamp, signature, verified
                FROM memory_audit
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            MemoryRecord(
                record_id=row[0],
                agent_id=row[1],
                action=row[2],
                memory_key=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                signature=row[5],
                verified=bool(row[6])
            )
            for row in rows
        ]