#!/usr/bin/env python3
"""
AI Audit Logger - AI Agent 操作審計日誌

目標：所有 AI 操作都被記錄和審計

記錄內容：
- 所有 CLI 命令執行
- 所有檔案修改
- 所有 API 調用
- 所有異常行為
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

class ActionType(Enum):
    """操作類型"""
    CLI_COMMAND = "cli_command"
    FILE_CREATE = "file_create"
    FILE_MODIFY = "file_modify"
    FILE_DELETE = "file_delete"
    API_CALL = "api_call"
    ERROR = "error"
    APPROVAL = "approval"
    GATE_CHECK = "gate_check"

@dataclass
class AuditEntry:
    """審計條目"""
    entry_id: str
    agent_id: str
    action_type: ActionType
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: str = "success"  # success, failure, blocked
    
    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type.value,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "result": self.result,
        }

class AnomalyType(Enum):
    """異常類型"""
    RAPID_SEQUENCE = "rapid_sequence"        # 快速連續操作
    LARGE_DELETE = "large_delete"            # 大量刪除
    UNAUTHORIZED_ACCESS = "unauthorized_access"  # 未授權訪問
    BYPASS_ATTEMPT = "bypass_attempt"      # 嘗試繞過
    SELF_APPROVAL = "self_approval"          # 自己批准

@dataclass
class Anomaly:
    """異常行為"""
    anomaly_id: str
    agent_id: str
    anomaly_type: AnomalyType
    description: str
    timestamp: datetime
    entries: List[AuditEntry] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high, critical

class AIAuditLogger:
    """
    AI Agent 操作審計日誌
    
    功能：
    - 記錄所有 AI 操作
    - 偵測異常行為
    - 生成審計報告
    """
    
    def __init__(self, storage_path: str = "./data/audit"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        self.entries: List[AuditEntry] = []
        self.anomalies: List[Anomaly] = []
        self._load_existing()
    
    def _load_existing(self):
        """載入現有日誌"""
        log_file = Path(self.storage_path) / "audit.jsonl"
        if log_file.exists():
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.entries.append(AuditEntry(
                            entry_id=data["entry_id"],
                            agent_id=data["agent_id"],
                            action_type=ActionType(data["action_type"]),
                            description=data["description"],
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            metadata=data.get("metadata", {}),
                            result=data.get("result", "success"),
                        ))
    
    def _save_entry(self, entry: AuditEntry):
        """保存條目"""
        log_file = Path(self.storage_path) / "audit.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
    
    def log(self, agent_id: str, action_type: ActionType, description: str,
            metadata: Dict = None, result: str = "success") -> str:
        """
        記錄操作
        
        Args:
            agent_id: Agent ID
            action_type: 操作類型
            description: 描述
            metadata: 額外元數據
            result: 結果
        
        Returns:
            entry_id: 條目 ID
        """
        entry = AuditEntry(
            entry_id=f"audit-{len(self.entries)}",
            agent_id=agent_id,
            action_type=action_type,
            description=description,
            timestamp=datetime.now(),
            metadata=metadata or {},
            result=result,
        )
        
        self.entries.append(entry)
        self._save_entry(entry)
        
        # 檢查異常
        self._check_anomaly(entry)
        
        return entry.entry_id
    
    def log_cli(self, agent_id: str, command: str, result: str = "success"):
        """記錄 CLI 命令"""
        self.log(agent_id, ActionType.CLI_COMMAND, f"CLI: {command}", 
                {"command": command}, result)
    
    def log_file_change(self, agent_id: str, action: ActionType, file_path: str):
        """記錄檔案變更"""
        self.log(agent_id, action, f"File {action.value}: {file_path}",
                {"file_path": file_path})
    
    def log_approval(self, agent_id: str, approver: str, target: str, status: str):
        """記錄審批"""
        self.log(agent_id, ActionType.APPROVAL, 
                f"Approval: {approver} -> {target} ({status})",
                {"approver": approver, "target": target, "status": status})
    
    def _check_anomaly(self, entry: AuditEntry):
        """檢查異常"""
        # 快速連續操作
        recent = [e for e in self.entries[-10:] 
                 if e.agent_id == entry.agent_id 
                 and e.timestamp.timestamp() > entry.timestamp.timestamp() - 60]
        if len(recent) >= 10:
            anomaly = Anomaly(
                anomaly_id=f"anomaly-{len(self.anomalies)}",
                agent_id=entry.agent_id,
                anomaly_type=AnomalyType.RAPID_SEQUENCE,
                description=f"Rapid sequence: {len(recent)} operations in 60s",
                timestamp=datetime.now(),
                entries=recent,
                severity="high"
            )
            self.anomalies.append(anomaly)
        
        # 嘗試繞過
        if "bypass" in entry.description.lower() or "skip" in entry.description.lower():
            anomaly = Anomaly(
                anomaly_id=f"anomaly-{len(self.anomalies)}",
                agent_id=entry.agent_id,
                anomaly_type=AnomalyType.BYPASS_ATTEMPT,
                description=f"Bypass attempt detected: {entry.description}",
                timestamp=datetime.now(),
                entries=[entry],
                severity="critical"
            )
            self.anomalies.append(anomaly)
    
    def get_recent_entries(self, agent_id: str = None, limit: int = 100) -> List[AuditEntry]:
        """取得最近的條目"""
        entries = self.entries[-limit:]
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        return entries
    
    def get_anomalies(self, agent_id: str = None, severity: str = None) -> List[Anomaly]:
        """取得異常"""
        anomalies = self.anomalies
        if agent_id:
            anomalies = [a for a in anomalies if a.agent_id == agent_id]
        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]
        return anomalies
    
    def get_audit_report(self, agent_id: str = None) -> dict:
        """取得審計報告"""
        entries = self.get_recent_entries(agent_id, 1000)
        
        by_type = {}
        for e in entries:
            by_type.setdefault(e.action_type.value, 0)
            by_type[e.action_type.value] += 1
        
        anomalies = self.get_anomalies(agent_id)
        
        return {
            "agent_id": agent_id or "all",
            "period": {
                "start": entries[0].timestamp.isoformat() if entries else None,
                "end": entries[-1].timestamp.isoformat() if entries else None,
            },
            "total_operations": len(entries),
            "by_type": by_type,
            "anomalies": {
                "total": len(anomalies),
                "critical": sum(1 for a in anomalies if a.severity == "critical"),
                "high": sum(1 for a in anomalies if a.severity == "high"),
            },
        }
    
    def export_report(self, format: str = "json") -> str:
        """導出報告"""
        if format == "json":
            return json.dumps(self.get_audit_report(), indent=2)
        else:
            return str(self.get_audit_report())