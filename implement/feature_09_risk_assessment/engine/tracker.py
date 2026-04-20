#!/usr/bin/env python3
"""
tracker.py - Risk Status Tracker
[FR-04] Track risk status changes and history
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from models.risk import Risk
from models.enums import RiskStatus, RiskLevel


@dataclass
class RiskHistoryEntry:
    """風險狀態變更歷史記錄"""
    risk_id: str
    changed_at: datetime
    old_status: RiskStatus
    new_status: RiskStatus
    changed_by: str
    note: str = ""


class RiskTracker:
    """
    [FR-04] Risk tracking with history persistence

    Manages risk lifecycle state transitions and maintains audit trail.
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.db_path = self.project_root / ".methodology" / "risk_assessment.db"
        self._init_database()

    def _init_database(self) -> None:
        """初始化 SQLite 資料庫"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Risks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                dimension TEXT,
                level TEXT,
                status TEXT DEFAULT 'OPEN',
                probability REAL DEFAULT 0.5,
                impact INTEGER DEFAULT 3,
                detectability_factor REAL DEFAULT 1.0,
                score REAL,
                owner TEXT,
                mitigation TEXT,
                mitigation_plan TEXT,
                created_at TEXT,
                updated_at TEXT,
                closed_at TEXT,
                evidence TEXT
            )
        """)

        # Risk history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id TEXT,
                changed_at TEXT,
                old_status TEXT,
                new_status TEXT,
                changed_by TEXT,
                note TEXT,
                FOREIGN KEY (risk_id) REFERENCES risks (id)
            )
        """)

        conn.commit()
        conn.close()

    def save_risk(self, risk: Risk) -> bool:
        """[FR-04] 保存風險到資料庫"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO risks
                (id, title, description, dimension, level, status, probability,
                 impact, detectability_factor, score, owner, mitigation,
                 mitigation_plan, created_at, updated_at, closed_at, evidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                risk.id,
                risk.title,
                risk.description,
                risk.dimension.value if hasattr(risk.dimension, 'value') else risk.dimension,
                risk.level.value if hasattr(risk.level, 'value') else risk.level,
                risk.status.value if hasattr(risk.status, 'value') else risk.status,
                risk.probability,
                risk.impact,
                risk.detectability_factor,
                risk.score,
                risk.owner,
                risk.mitigation,
                json.dumps(risk.mitigation_plan.to_dict() if hasattr(risk.mitigation_plan, 'to_dict') else risk.mitigation_plan),
                risk.created_at.isoformat() if isinstance(risk.created_at, datetime) else risk.created_at,
                risk.updated_at.isoformat() if isinstance(risk.updated_at, datetime) else risk.updated_at,
                risk.closed_at.isoformat() if isinstance(risk.closed_at, datetime) else risk.closed_at,
                json.dumps(risk.evidence),
            ))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Error saving risk: {e}")
            return False

    def load_risk(self, risk_id: str) -> Optional[Risk]:
        """[FR-04] 從資料庫載入風險"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM risks WHERE id = ?", (risk_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_risk(row)
            return None
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"Error loading risk: {e}")
            return None

    def load_all_risks(self) -> List[Risk]:
        """[FR-04] 載入所有風險"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM risks ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()

            return [self._row_to_risk(row) for row in rows]
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"Error loading risks: {e}")
            return []

    def update_status(
        self,
        risk_id: str,
        new_status: RiskStatus,
        changed_by: str = "System",
        note: str = ""
    ) -> Tuple[bool, str]:
        """
        [FR-04] 更新風險狀態

        Args:
            risk_id: 風險 ID
            new_status: 新狀態
            changed_by: 變更人
            note: 備註

        Returns:
            (success, message)
        """
        risk = self.load_risk(risk_id)
        if not risk:
            return False, f"Risk {risk_id} not found"

        old_status = risk.status

        # Validate transition
        if not old_status.can_transition_to(new_status):
            return False, f"Invalid transition: {old_status.value} -> {new_status.value}"

        # Update risk
        risk.status = new_status
        risk.updated_at = datetime.now()

        if new_status == RiskStatus.CLOSED:
            risk.closed_at = datetime.now()

        # Save
        self.save_risk(risk)

        # Record history
        self._record_history(risk_id, old_status, new_status, changed_by, note)

        return True, f"Status updated: {old_status.name} -> {new_status.name}"

    def get_history(self, risk_id: str) -> List[RiskHistoryEntry]:
        """[FR-04] 獲取風險歷史記錄"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT risk_id, changed_at, old_status, new_status, changed_by, note
                FROM risk_history
                WHERE risk_id = ?
                ORDER BY changed_at DESC
            """, (risk_id,))

            rows = cursor.fetchall()
            conn.close()

            return [
                RiskHistoryEntry(
                    risk_id=row[0],
                    changed_at=datetime.fromisoformat(row[1]),
                    old_status=RiskStatus(row[2]),
                    new_status=RiskStatus(row[3]),
                    changed_by=row[4],
                    note=row[5] or "",
                )
                for row in rows
            ]
        except (sqlite3.Error, ValueError) as e:
            print(f"Error loading history: {e}")
            return []

    def get_open_risks(self) -> List[Risk]:
        """[FR-04] 獲取所有 Open 狀態的風險"""
        all_risks = self.load_all_risks()
        return [r for r in all_risks if r.status == RiskStatus.OPEN]

    def get_closed_risks(self) -> List[Risk]:
        """[FR-04] 獲取所有 Closed 狀態的風險"""
        all_risks = self.load_all_risks()
        return [r for r in all_risks if r.status == RiskStatus.CLOSED]

    def get_by_level(self, level) -> List[Risk]:
        """[FR-04] 根據等級篩選風險"""
        all_risks = self.load_all_risks()
        return [r for r in all_risks if r.level == level]

    def _record_history(
        self,
        risk_id: str,
        old_status: RiskStatus,
        new_status: RiskStatus,
        changed_by: str,
        note: str
    ) -> None:
        """記錄狀態變更歷史"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO risk_history
                (risk_id, changed_at, old_status, new_status, changed_by, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                risk_id,
                datetime.now().isoformat(),
                old_status.value,
                new_status.value,
                changed_by,
                note,
            ))

            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error recording history: {e}")

    def _row_to_risk(self, row: tuple) -> Risk:
        """將資料庫 row 轉換為 Risk 物件"""
        from models.risk import MitigationPlan
        from models.enums import RiskDimension, RiskLevel, RiskStatus, StrategyType

        return Risk(
            id=row[0],
            title=row[1],
            description=row[2] or "",
            dimension=RiskDimension(row[3]),
            level=RiskLevel(row[4]),
            status=RiskStatus(row[5]),
            probability=row[6],
            impact=row[7],
            detectability_factor=row[8],
            owner=row[10] or "",
            mitigation=row[11] or "",
            mitigation_plan=MitigationPlan.from_dict(json.loads(row[12])) if row[12] else MitigationPlan(),
            created_at=datetime.fromisoformat(row[13]),
            updated_at=datetime.fromisoformat(row[14]),
            closed_at=datetime.fromisoformat(row[15]) if row[15] else None,
            evidence=json.loads(row[16]) if row[16] else [],
        )

    def export_to_register(self) -> Dict[str, Any]:
        """[FR-04] 導出風險登記表摘要"""
        risks = self.load_all_risks()

        return {
            "total": len(risks),
            "open": len([r for r in risks if r.status == RiskStatus.OPEN]),
            "closed": len([r for r in risks if r.status == RiskStatus.CLOSED]),
            "by_level": {
                "critical": len([r for r in risks if r.level == RiskLevel.CRITICAL]),
                "high": len([r for r in risks if r.level == RiskLevel.HIGH]),
                "medium": len([r for r in risks if r.level == RiskLevel.MEDIUM]),
                "low": len([r for r in risks if r.level == RiskLevel.LOW]),
            },
            "risks": [r.to_dict() for r in risks],
        }

    def validate_state_machine(self) -> Dict[str, Any]:
        """
        [FR-04] 驗證狀態機一致性

        檢查所有風險是否符合狀態機規則。
        """
        risks = self.load_all_risks()
        violations = []

        for risk in risks:
            # CLOSED should have closed_at
            if risk.status == RiskStatus.CLOSED and not risk.closed_at:
                violations.append(f"{risk.id}: CLOSED but no closed_at")

            # OPEN should not have closed_at
            if risk.status == RiskStatus.OPEN and risk.closed_at:
                violations.append(f"{risk.id}: OPEN but has closed_at")

            # Timestamps should be consistent
            if risk.created_at > risk.updated_at:
                violations.append(f"{risk.id}: created_at > updated_at")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "total_checked": len(risks),
        }