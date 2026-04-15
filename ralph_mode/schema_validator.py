"""
Ralph Mode - SessionsSpawnLog Schema Validator

確保 sessions_spawn.log 的 schema 穩定，避免因格式變化導致 Ralph 誤判。

Author: methodology-v2
Version: 1.0.0
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
    
    確保 log 格式穩定，Ralph 啟動前必須通過驗證。
    
    Example:
        >>> validator = SessionsSpawnLogValidator()
        >>> result = validator.validate_path(Path("/repo/.methodology/sessions_spawn.log"))
        >>> if not result.ok:
        ...     raise RalphSchemaError(result.error)
    """
    
    CURRENT_SCHEMA = "1.0"
    SUPPORTED_SCHEMAS = ["1.0", "0.9"]  # 向後相容
    
    REQUIRED_FIELDS = ["timestamp", "session_id", "fr", "status"]
    STATUS_VALUES = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    
    def validate_path(self, log_path: Path) -> ValidationResult:
        """
        驗證 log 檔案路徑
        
        Args:
            log_path: sessions_spawn.log 檔案路徑
            
        Returns:
            ValidationResult
        """
        if not log_path.exists():
            return ValidationResult(
                ok=False,
                error=f"Log file not found: {log_path}"
            )
        
        try:
            content = json.loads(log_path.read_text())
            return self.validate_content(content)
        except json.JSONDecodeError as e:
            return ValidationResult(
                ok=False,
                error=f"Invalid JSON: {e}"
            )
    
    def validate_content(self, content: Dict[str, Any]) -> ValidationResult:
        """
        驗證 log 內容
        
        Args:
            content: 已解析的 log JSON 內容
            
        Returns:
            ValidationResult
        """
        # 檢查 schema_version
        schema = content.get("schema_version", None)
        
        if schema is None:
            return ValidationResult(
                ok=False,
                error=f"No schema_version found. Expected {self.CURRENT_SCHEMA}"
            )
        
        if schema not in self.SUPPORTED_SCHEMAS:
            return ValidationResult(
                ok=False,
                error=f"Unsupported schema: {schema}. Supported: {self.SUPPORTED_SCHEMAS}",
                supported_schemas=self.SUPPORTED_SCHEMAS
            )
        
        # 檢查 entries 結構
        entries = content.get("entries", [])
        if not isinstance(entries, list):
            return ValidationResult(
                ok=False,
                error=f"entries must be a list, got {type(entries)}"
            )
        
        # 檢查每個 entry 的 required fields
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                return ValidationResult(
                    ok=False,
                    error=f"Entry {i} must be a dict, got {type(entry)}"
                )
            
            for field in self.REQUIRED_FIELDS:
                if field not in entry:
                    return ValidationResult(
                        ok=False,
                        error=f"Entry {i} missing required field: {field}"
                    )
            
            # 檢查 status 值是否合法
            status = entry.get("status", "")
            if status not in self.STATUS_VALUES:
                return ValidationResult(
                    ok=False,
                    error=f"Entry {i} invalid status: {status}. Expected one of {self.STATUS_VALUES}"
                )
        
        # 警告：如果 schema 不是最新版本
        if schema != self.CURRENT_SCHEMA:
            return ValidationResult(
                ok=True,
                warning=f"Schema version {schema} is not latest ({self.CURRENT_SCHEMA}). Consider upgrading."
            )
        
        return ValidationResult(ok=True)
    
    def parse_entry(self, entry: Dict[str, Any]) -> ParsedEntry:
        """
        解析單個 entry
        
        Args:
            entry: log entry dict
            
        Returns:
            ParsedEntry
        """
        return ParsedEntry(
            timestamp=entry["timestamp"],
            session_id=entry["session_id"],
            fr=entry["fr"],
            status=entry["status"]
        )
    
    def parse_entries(self, content: Dict[str, Any]) -> List[ParsedEntry]:
        """
        解析所有 entries
        
        Args:
            content: log 內容
            
        Returns:
            List[ParsedEntry]
        """
        entries = content.get("entries", [])
        return [self.parse_entry(e) for e in entries]
    
    def create_empty_log(self) -> Dict[str, Any]:
        """
        建立空白 log 結構（用於初始化）
        
        Returns:
            空白 log 結構
        """
        return {
            "schema_version": self.CURRENT_SCHEMA,
            "schema_definition": {
                "required": self.REQUIRED_FIELDS,
                "status_values": self.STATUS_VALUES
            },
            "entries": []
        }
    
    def init_log_file(self, log_path: Path) -> bool:
        """
        初始化 log 檔案（如果不存在）
        
        Args:
            log_path: log 檔案路徑
            
        Returns:
            True if created, False if already existed
        """
        if log_path.exists():
            return False
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(self.create_empty_log(), indent=2))
        return True
