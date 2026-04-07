#!/usr/bin/env python3
"""
Cost Tracker
===========
追蹤 Agent 開發的成本

成本類型：
- API 調用成本
- 計算資源成本
- 人力成本
- 維護成本
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import sqlite3
import json

class CostType(Enum):
    """成本類型"""
    API_CALL = "api_call"
    COMPUTE = "compute"
    HUMAN_HOURS = "human_hours"
    MAINTENANCE = "maintenance"
    INCIDENT = "incident"

@dataclass
class CostRecord:
    """成本記錄"""
    cost_id: str
    cost_type: CostType
    amount: float  # 金額
    currency: str  # 幣種
    timestamp: datetime
    agent_id: str
    task_id: str
    description: str

class CostTracker:
    """
    成本追蹤器
    
    使用方式：
    
    ```python
    tracker = CostTracker()
    
    # 記錄 API 調用成本
    tracker.record(
        cost_type=CostType.API_CALL,
        amount=0.15,
        agent_id="agent-1",
        task_id="TASK-123",
        description="Claude API call"
    )
    
    # 取得成本摘要
    summary = tracker.get_summary(period="month")
    print(f"Total: ${summary['total']}")
    ```
    """
    
    def __init__(self, db_path: str = ".methodology/roi_costs.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """確保資料庫存在"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cost_id TEXT UNIQUE,
                cost_type TEXT,
                amount REAL,
                currency TEXT,
                timestamp TEXT,
                agent_id TEXT,
                task_id TEXT,
                description TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def record(
        self,
        cost_type: CostType,
        amount: float,
        agent_id: str,
        task_id: str = "",
        description: str = "",
        currency: str = "USD"
    ) -> str:
        """記錄成本"""
        import uuid
        
        cost_id = f"cost-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO costs 
            (cost_id, cost_type, amount, currency, timestamp, agent_id, task_id, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (cost_id, cost_type.value, amount, currency, timestamp, agent_id, task_id, description))
        conn.commit()
        conn.close()
        
        return cost_id
    
    def get_summary(self, period: str = "month") -> Dict:
        """取得成本摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 根據 period 設定時間範圍
        if period == "day":
            where = "WHERE timestamp >= date('now')"
        elif period == "week":
            where = "WHERE timestamp >= date('now', '-7 days')"
        elif period == "month":
            where = "WHERE timestamp >= date('now', '-30 days')"
        else:
            where = ""
        
        cursor.execute(f"""
            SELECT cost_type, SUM(amount) as total, COUNT(*) as count
            FROM costs
            {where}
            GROUP BY cost_type
        """)
        
        rows = cursor.fetchall()
        
        total = 0
        by_type = {}
        for row in rows:
            cost_type = row[0]
            amount = row[1] or 0
            count = row[2]
            total += amount
            by_type[cost_type] = {"amount": amount, "count": count}
        
        conn.close()
        
        return {
            "total": total,
            "by_type": by_type,
            "period": period
        }
    
    def get_records(self, agent_id: str = None, limit: int = 100) -> List[CostRecord]:
        """取得成本記錄"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent_id:
            cursor.execute("""
                SELECT cost_id, cost_type, amount, currency, timestamp, agent_id, task_id, description
                FROM costs
                WHERE agent_id=?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (agent_id, limit))
        else:
            cursor.execute("""
                SELECT cost_id, cost_type, amount, currency, timestamp, agent_id, task_id, description
                FROM costs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            CostRecord(
                cost_id=row[0],
                cost_type=CostType(row[1]),
                amount=row[2],
                currency=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                agent_id=row[5],
                task_id=row[6],
                description=row[7]
            )
            for row in rows
        ]
