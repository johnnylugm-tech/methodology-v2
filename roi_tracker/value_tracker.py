#!/usr/bin/env python3
"""
Value Tracker
============
追蹤 Agent 開發的價值產出

價值類型：
- 任務完成數
- 效率提升
- 錯誤減少
- 品質改善
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import sqlite3

class ValueType(Enum):
    """價值類型"""
    TASK_COMPLETED = "task_completed"
    EFFICIENCY_GAIN = "efficiency_gain"
    BUGS_PREVENTED = "bugs_prevented"
    QUALITY_IMPROVEMENT = "quality_improvement"
    TIME_SAVED = "time_saved"

@dataclass
class ValueRecord:
    """價值記錄"""
    value_id: str
    value_type: ValueType
    amount: float  # 數值（如任務數、節省時間等）
    unit: str  # 單位（如 "tasks", "hours"）
    timestamp: datetime
    agent_id: str
    task_id: str
    description: str

class ValueTracker:
    """
    價值追蹤器
    
    使用方式：
    
    ```python
    tracker = ValueTracker()
    
    # 記錄任務完成
    tracker.record(
        value_type=ValueType.TASK_COMPLETED,
        amount=1,
        unit="tasks",
        agent_id="agent-1",
        task_id="TASK-123",
        description="Completed login feature"
    )
    
    # 記錄效率提升
    tracker.record(
        value_type=ValueType.EFFICIENCY_GAIN,
        amount=2.5,
        unit="hours",
        agent_id="agent-1",
        description="Saved 2.5 hours of manual work"
    )
    ```
    """
    
    def __init__(self, db_path: str = ".methodology/roi_values.db"):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """確保資料庫存在"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS value_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value_id TEXT UNIQUE,
                value_type TEXT,
                amount REAL,
                unit TEXT,
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
        value_type: ValueType,
        amount: float,
        unit: str,
        agent_id: str,
        task_id: str = "",
        description: str = ""
    ) -> str:
        """記錄價值"""
        import uuid
        
        value_id = f"value-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO value_records
            (value_id, value_type, amount, unit, timestamp, agent_id, task_id, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (value_id, value_type.value, amount, unit, timestamp, agent_id, task_id, description))
        conn.commit()
        conn.close()
        
        return value_id
    
    def get_summary(self, period: str = "month") -> Dict:
        """取得價值摘要"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if period == "day":
            where = "WHERE timestamp >= date('now')"
        elif period == "week":
            where = "WHERE timestamp >= date('now', '-7 days')"
        elif period == "month":
            where = "WHERE timestamp >= date('now', '-30 days')"
        else:
            where = ""
        
        cursor.execute(f"""
            SELECT value_type, SUM(amount) as total, COUNT(*) as count
            FROM value_records
            {where}
            GROUP BY value_type
        """)
        
        rows = cursor.fetchall()
        
        total_units = 0
        by_type = {}
        for row in rows:
            value_type = row[0]
            amount = row[1] or 0
            count = row[2]
            total_units += amount
            by_type[value_type] = {"amount": amount, "count": count, "unit": self._get_unit_for_type(value_type)}
        
        conn.close()
        
        return {
            "total_units": total_units,
            "by_type": by_type,
            "period": period
        }
    
    def _get_unit_for_type(self, value_type: str) -> str:
        units = {
            ValueType.TASK_COMPLETED.value: "tasks",
            ValueType.EFFICIENCY_GAIN.value: "hours",
            ValueType.BUGS_PREVENTED.value: "bugs",
            ValueType.QUALITY_IMPROVEMENT.value: "points",
            ValueType.TIME_SAVED.value: "hours"
        }
        return units.get(value_type, "units")
