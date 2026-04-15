"""
Ralph Mode - SessionsSpawnLog Schema Validator

確保 sessions_spawn.log 的 schema 穩定，支持：
- 舊格式：JSONL（每行一個 JSON，可能沒有 status）
- 新格式：Schema v1.0+（帶 schema_version 和 entries 陣列）

Author: methodology-v2
Version: 1.1.1
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class ValidationResult:
    """驗證結果"""
    ok: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    supported_schemas: List[str] = None
    is_legacy_format: bool = False  # True if JSONL format detected


@dataclass
class ParsedEntry:
    """解析後的 log entry"""
    timestamp: str
    session_id: str
    fr: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED


class RalphSchemaError(Exception):
    """Ralph Schema 錯誤"""
    pass


class SessionsSpawnLogValidator:
    """
    sessions_spawn.log Schema 驗證器
    
    支持兩種格式：
    1. 舊格式（JSONL）：每行一個 JSON object
    2. 新格式（v1.0+）：帶 schema_version 和 entries 陣列
    """
    
    CURRENT_SCHEMA = "1.0"
    SUPPORTED_SCHEMAS = ["1.0", "0.9"]
    
    REQUIRED_FIELDS = ["timestamp", "session_id", "fr", "status"]
    STATUS_VALUES = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    
    # 舊格式的狀態值（從 verdict 推斷）
    LEGACY_STATUS_MAP = {
        "APPROVED": "COMPLETED",
        "REJECT": "FAILED",
        "PENDING": "PENDING",
        "RUNNING": "RUNNING"
    }
    
    def validate_path(self, log_path: Path) -> ValidationResult:
        """驗證 log 檔案路徑"""
        if not log_path.exists():
            return ValidationResult(ok=False, error=f"Log file not found: {log_path}")
        
        try:
            content = log_path.read_text()
            return self.validate_content(content)
        except Exception as e:
            return ValidationResult(ok=False, error=f"Cannot read log file: {e}")
    
    def validate_content(self, content: str) -> ValidationResult:
        """驗證 log 內容（自動檢測格式）"""
        if not content.strip():
            return ValidationResult(ok=True, warning="Empty log file")
        
        stripped = content.strip()
        
        # 檢測是否是新格式（單一 JSON 且有 schema_version）
        if stripped.startswith('{'):
            try:
                data = json.loads(stripped)
                if "schema_version" in data:
                    return self._validate_new_format(content)
            except json.JSONDecodeError:
                pass
        
        # 默認為 JSONL 格式（舊格式）
        return self._validate_legacy_format(content)
    
    def _validate_new_format(self, content: str) -> ValidationResult:
        """驗證新格式（Schema v1.0+）"""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return ValidationResult(ok=False, error=f"Invalid JSON: {e}")
        
        schema = data.get("schema_version", None)
        if schema is None:
            return ValidationResult(ok=False, error=f"No schema_version found")
        
        if schema not in self.SUPPORTED_SCHEMAS:
            return ValidationResult(
                ok=False,
                error=f"Unsupported schema: {schema}",
                supported_schemas=self.SUPPORTED_SCHEMAS
            )
        
        entries = data.get("entries", [])
        for i, entry in enumerate(entries):
            for field in self.REQUIRED_FIELDS:
                if field not in entry:
                    return ValidationResult(
                        ok=False,
                        error=f"Entry {i} missing required field: {field}"
                    )
        
        if schema != self.CURRENT_SCHEMA:
            return ValidationResult(
                ok=True,
                warning=f"Schema version {schema} is not latest ({self.CURRENT_SCHEMA})"
            )
        
        return ValidationResult(ok=True)
    
    def _validate_legacy_format(self, content: str) -> ValidationResult:
        """驗證舊格式（JSONL）"""
        lines = content.strip().split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    ok=False,
                    error=f"Line {i+1}: Invalid JSON: {e}"
                )
            
            # 檢查關鍵欄位（timestamp, session_id, fr）- status 可能沒有
            for field in ["timestamp", "session_id", "fr"]:
                if field not in entry:
                    return ValidationResult(
                        ok=False,
                        error=f"Line {i+1}: Missing required field: {field}"
                    )
        
        return ValidationResult(
            ok=True,
            is_legacy_format=True,
            warning="Legacy JSONL format detected"
        )
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """
        解析 log 內容為統一的 entries 格式
        """
        if not content.strip():
            return self.create_empty_log()
        
        stripped = content.strip()
        
        # 檢測是否是新格式（單一 JSON 且有 schema_version）
        if stripped.startswith('{'):
            try:
                data = json.loads(stripped)
                if "schema_version" in data:
                    return data
            except json.JSONDecodeError:
                pass
        
        # 舊格式（JSONL）→ 轉換為新格式
        lines = stripped.split('\n')
        entries = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            entry = json.loads(line)
            
            # 如果沒有 status 欄位，根據其他資訊推斷
            if "status" not in entry:
                if "verdict" in entry:
                    entry["status"] = self.LEGACY_STATUS_MAP.get(entry["verdict"], "PENDING")
                else:
                    # 預設為 COMPLETED（因為在 log 中就表示已執行）
                    entry["status"] = "COMPLETED"
            
            entries.append(entry)
        
        return {
            "schema_version": "legacy",
            "entries": entries
        }
    
    def parse_entry(self, entry: Dict[str, Any]) -> ParsedEntry:
        """解析單個 entry"""
        return ParsedEntry(
            timestamp=entry.get("timestamp", ""),
            session_id=entry.get("session_id", ""),
            fr=entry.get("fr", "UNKNOWN"),
            status=entry.get("status", "UNKNOWN")
        )
    
    def parse_entries(self, content: str) -> List[ParsedEntry]:
        """解析所有 entries"""
        data = self.parse_content(content)
        entries = data.get("entries", [])
        return [self.parse_entry(e) for e in entries]
    
    def create_empty_log(self) -> Dict[str, Any]:
        """建立空白 log 結構（新格式 v1.0）"""
        return {
            "schema_version": self.CURRENT_SCHEMA,
            "schema_definition": {
                "required": self.REQUIRED_FIELDS,
                "status_values": self.STATUS_VALUES
            },
            "entries": []
        }
    
    def init_log_file(self, log_path: Path) -> bool:
        """初始化 log 檔案（如果不存在）"""
        if log_path.exists():
            return False
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(self.create_empty_log(), indent=2))
        return True
