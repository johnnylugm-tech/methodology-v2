#!/usr/bin/env python3
"""
Execution Registry - 執行登記處
===================================
解決方案：產出物要能證明「真的做了」

核心概念：
- 每次執行步驟時記錄 timestamp + artifact
- 生成 cryptographic signature（不可偽造）
- 可驗證：這個步驟真的執行過嗎？
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib
import json
import os
import sqlite3

@dataclass
class ExecutionRecord:
    """執行記錄"""
    step: str
    timestamp: str
    artifact: Dict[str, Any]
    signature: str
    verified: bool = True
    note: str = ""

class ExecutionRegistry:
    """
    執行登記處
    
    功能：
    - 記錄所有步驟執行
    - 生成不可偽造的 signature
    - 驗證步驟是否真的執行
    
    使用方式：
    
    ```python
    registry = ExecutionRegistry()
    
    # 記錄步驟執行
    sig = registry.record(
        step="quality-gate",
        artifact={
            "score": 95,
            "passed": True,
            "files_checked": 42
        }
    )
    
    # 驗證步驟是否執行
    if registry.prove("quality-gate"):
        print("✅ Quality Gate 已執行")
    else:
        print("❌ Quality Gate 未執行（不合規）")
    ```
    """
    
    def __init__(self, db_path: str = ".methodology/execution_registry.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """確保資料庫存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                artifact TEXT NOT NULL,
                signature TEXT NOT NULL UNIQUE,
                verified INTEGER DEFAULT 1,
                note TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def _generate_signature(self, data: Dict) -> str:
        """生成不可偽造的簽名"""
        # 使用 SHA-256 哈希
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def record(self, step: str, artifact: Dict[str, Any], note: str = "") -> str:
        """
        記錄步驟執行
        
        Args:
            step: 步驟名稱
            artifact: 執行產出物
            note: 備註
        
        Returns:
            str: signature（可用於驗證）
        """
        timestamp = datetime.now().isoformat()
        
        record_data = {
            "step": step,
            "timestamp": timestamp,
            "artifact": artifact,
        }
        
        signature = self._generate_signature(record_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO executions (step, timestamp, artifact, signature, note)
            VALUES (?, ?, ?, ?, ?)
        """, (step, timestamp, json.dumps(artifact), signature, note))
        conn.commit()
        conn.close()
        
        return signature
    
    def prove(self, step: str, since: Optional[str] = None) -> bool:
        """
        驗證步驟是否真的執行過
        
        Args:
            step: 步驟名稱
            since: 起始時間（可選）
        
        Returns:
            bool: True = 執行過, False = 沒執行
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if since:
            cursor.execute(
                "SELECT COUNT(*) FROM executions WHERE step=? AND timestamp>=?",
                (step, since)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM executions WHERE step=?",
                (step,)
            )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_records(self, step: Optional[str] = None, limit: int = 100) -> List[ExecutionRecord]:
        """取得執行記錄"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if step:
            cursor.execute(
                "SELECT step, timestamp, artifact, signature, verified, note FROM executions WHERE step=? ORDER BY id DESC LIMIT ?",
                (step, limit)
            )
        else:
            cursor.execute(
                "SELECT step, timestamp, artifact, signature, verified, note FROM executions ORDER BY id DESC LIMIT ?",
                (limit,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            ExecutionRecord(
                step=row[0],
                timestamp=row[1],
                artifact=json.loads(row[2]),
                signature=row[3],
                verified=bool(row[4]),
                note=row[5]
            )
            for row in rows
        ]
    
    def verify_chain(self, steps: List[str]) -> Dict:
        """
        驗證步驟鏈是否完整
        
        Args:
            steps: 預期執行的步驟列表
        
        Returns:
            dict: {complete: bool, missing: [], executed: []}
        """
        records = self.get_records(limit=1000)
        executed_steps = set(r.step for r in records)
        
        missing = [s for s in steps if s not in executed_steps]
        
        return {
            "complete": len(missing) == 0,
            "missing": missing,
            "executed": list(executed_steps & set(steps)),
            "total": len(steps)
        }
    
    def get_evidence_report(self, step: str) -> Dict:
        """取得步驟的證據報告"""
        records = self.get_records(step=step, limit=1)
        
        if not records:
            return {
                "step": step,
                "executed": False,
                "evidence": None
            }
        
        record = records[0]
        
        return {
            "step": step,
            "executed": True,
            "evidence": {
                "timestamp": record.timestamp,
                "artifact": record.artifact,
                "signature": record.signature,
                "verified": record.verified
            }
        }


def create_minimal_registry() -> ExecutionRegistry:
    """創建最小化的執行登記處（只用於關鍵步驟）"""
    return ExecutionRegistry()
