#!/usr/bin/env python3
"""
Decision Recorder
================
決策紀錄器，持久化所有技術決策
"""

import json
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from .classifier import DecisionClassifier, RiskLevel, DecisionType, ClassifiedDecision

class DecisionRecord:
    """決策紀錄"""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.decisions_dir = self.project_path / ".methodology" / "decisions"
        self.log_file = self.decisions_dir / "decision_log.json"
        self.classifier = DecisionClassifier()
        self._ensure_dir()
    
    def _ensure_dir(self):
        """確保目錄存在"""
        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self._write_log([])
    
    def _read_log(self) -> List[Dict]:
        """讀取日誌"""
        return json.loads(self.log_file.read_text())
    
    def _write_log(self, decisions: List[Dict]):
        """寫入日誌"""
        self.log_file.write_text(json.dumps(decisions, indent=2, ensure_ascii=False))
    
    def record(
        self,
        item: str,
        description: str,
        decision_type: str,
        risk_level: str,
        decision: str,
        依据: str = "",
        status: str = "pending"
    ) -> str:
        """記錄一個決策"""
        decision_id = f"D-{uuid.uuid4().hex[:6].upper()}"
        
        record = {
            "id": decision_id,
            "item": item,
            "description": description,
            "type": decision_type,
            "risk": risk_level,
            "decision": decision,
            "依据": 依据,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        decisions = self._read_log()
        decisions.append(record)
        self._write_log(decisions)
        
        return decision_id
    
    def classify_and_record(
        self,
        item: str,
        description: str,
        spec_reference: Optional[str] = None
    ) -> ClassifiedDecision:
        """分類並記錄"""
        # 分類
        classified = self.classifier.classify(item, description, spec_reference)
        
        # 記錄
        self.record(
            item=item,
            description=description,
            decision_type=classified.decision_type.value,
            risk_level=classified.risk_level.value,
            decision=classified.recommendation or "TBD",
            依据=spec_reference or "",
            status="pending" if classified.requires_confirmation else "auto"
        )
        
        return classified
    
    def get_all(self) -> List[Dict]:
        """取得所有決策"""
        return self._read_log()
    
    def get_by_risk(self, risk_level: str) -> List[Dict]:
        """按風險等級篩選"""
        return [d for d in self._read_log() if d["risk"] == risk_level]
    
    def get_pending(self) -> List[Dict]:
        """取得所有待確認的決策"""
        return [d for d in self._read_log() if d["status"] == "pending"]
    
    def confirm(self, decision_id: str, confirmed_value: str):
        """確認決策"""
        decisions = self._read_log()
        for d in decisions:
            if d["id"] == decision_id:
                d["decision"] = confirmed_value
                d["status"] = "confirmed"
                d["confirmed_at"] = datetime.now().isoformat()
                break
        self._write_log(decisions)
    
    def generate_report(self) -> str:
        """生成決策報告"""
        decisions = self._read_log()
        
        report = ["# 決策紀錄報告\n"]
        report.append(f"生成時間: {datetime.now().isoformat()}\n")
        report.append(f"總決策數: {len(decisions)}\n")
        
        # 按風險分組
        high = self.get_by_risk("🔴 HIGH")
        medium = self.get_by_risk("🟡 MEDIUM")
        low = self.get_by_risk("🔵 LOW")
        
        report.append(f"\n## 🔴 HIGH 風險: {len(high)}")
        for d in high:
            report.append(f"  - {d['item']}: {d['decision']} ({d['status']})")
        
        report.append(f"\n## 🟡 MEDIUM 風險: {len(medium)}")
        for d in medium:
            report.append(f"  - {d['item']}: {d['decision']} ({d['status']})")
        
        report.append(f"\n## 🔵 LOW 風險: {len(low)}")
        for d in low:
            report.append(f"  - {d['item']}: {d['decision']} ({d['status']})")
        
        return "\n".join(report)

# Alias for backwards compatibility
DecisionRecorder = DecisionRecord