#!/usr/bin/env python3
"""
Technical Debt Registry
======================
技術債務登記與追蹤
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from enum import Enum

class Severity(Enum):
    CRITICAL = "🔴 CRITICAL"
    HIGH = "🟠 HIGH"
    MEDIUM = "🟡 MEDIUM"
    LOW = "🔵 LOW"

@dataclass
class DebtRecord:
    """債務記錄"""
    id: str
    description: str
    severity: str
    ticket: Optional[str]
    created_at: str
    resolved_at: Optional[str]
    status: str  # "open", "resolved", "accepted"
    reason: Optional[str]  # 為什麼接受這個債務

class DebtRegistry:
    """
    技術債務登記處
    
    使用方式：
    
    ```python
    registry = DebtRegistry()
    
    # 添加債務
    debt_id = registry.add(
        description="使用 eval() 而非 ast.literal_eval",
        severity="high",
        ticket="TASK-123"
    )
    
    # 列出所有債務
    for debt in registry.list_open():
        print(f"{debt.severity}: {debt.description}")
    
    # 解決債務
    registry.resolve(debt_id)
    
    # 接受債務（決定不修復）
    registry.accept(debt_id, reason="短期內沒有安全風險")
    ```
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.debt_dir = self.project_path / ".methodology" / "debts"
        self.debt_file = self.debt_dir / "debt_registry.json"
        self.debt_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.debt_file.exists():
            self._write([])
    
    def _read(self) -> List[dict]:
        return json.loads(self.debt_file.read_text())
    
    def _write(self, debts: List[dict]):
        self.debt_file.write_text(json.dumps(debts, indent=2, ensure_ascii=False))
    
    def add(
        self,
        description: str,
        severity: str = "medium",
        ticket: Optional[str] = None
    ) -> str:
        """添加技術債務"""
        debt_id = f"debt-{uuid.uuid4().hex[:8]}"
        
        debt = {
            "id": debt_id,
            "description": description,
            "severity": severity,
            "ticket": ticket,
            "created_at": datetime.now().isoformat(),
            "resolved_at": None,
            "status": "open",
            "reason": None
        }
        
        debts = self._read()
        debts.append(debt)
        self._write(debts)
        
        return debt_id
    
    def list_all(self) -> List[DebtRecord]:
        """列出所有債務"""
        return [DebtRecord(**d) for d in self._read()]
    
    def list_open(self) -> List[DebtRecord]:
        """列出未解決的債務"""
        return [DebtRecord(**d) for d in self._read() if d["status"] == "open"]
    
    def list_by_severity(self, severity: str) -> List[DebtRecord]:
        """按嚴重性篩選"""
        return [DebtRecord(**d) for d in self._read() if d["severity"] == severity]
    
    def resolve(self, debt_id: str) -> bool:
        """標記為已解決"""
        debts = self._read()
        for debt in debts:
            if debt["id"] == debt_id:
                debt["status"] = "resolved"
                debt["resolved_at"] = datetime.now().isoformat()
                self._write(debts)
                return True
        return False
    
    def accept(self, debt_id: str, reason: str) -> bool:
        """接受債務（決定不修復）"""
        debts = self._read()
        for debt in debts:
            if debt["id"] == debt_id:
                debt["status"] = "accepted"
                debt["reason"] = reason
                self._write(debts)
                return True
        return False
    
    def delete(self, debt_id: str) -> bool:
        """刪除債務"""
        debts = self._read()
        original_len = len(debts)
        debts = [d for d in debts if d["id"] != debt_id]
        
        if len(debts) < original_len:
            self._write(debts)
            return True
        return False
    
    def generate_report(self) -> str:
        """生成債務報告"""
        debts = self._read()
        
        open_debts = [d for d in debts if d["status"] == "open"]
        accepted = [d for d in debts if d["status"] == "accepted"]
        resolved = [d for d in debts if d["status"] == "resolved"]
        
        report = ["# Technical Debt Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        
        report.append(f"\n## Summary")
        report.append(f"- Total: {len(debts)}")
        report.append(f"- Open: {len(open_debts)}")
        report.append(f"- Accepted: {len(accepted)}")
        report.append(f"- Resolved: {len(resolved)}")
        
        if open_debts:
            report.append(f"\n## 🔴 Open Debts ({len(open_debts)})")
            for d in open_debts:
                report.append(f"- [{d['severity']}] {d['description']} ({d['id']})")
        
        return "\n".join(report)
