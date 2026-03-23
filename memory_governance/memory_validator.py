#!/usr/bin/env python3
"""
Memory Validator
================
驗證記憶狀態，檢測狀態漂移

功能：
- 驗證記憶時間戳
- 檢測過期記憶
- 評估記憶一致性
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import json


class MemoryState(Enum):
    """記憶狀態"""
    VALID = "valid"
    STALE = "stale"          # 過期
    CORRUPTED = "corrupted"  # 損壞
    INCONSISTENT = "inconsistent"  # 不一致
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """驗證結果"""
    state: MemoryState
    timestamp: datetime
    age_seconds: float
    is_trustworthy: bool
    issues: List[str]


class MemoryValidator:
    """
    記憶驗證器
    
    使用方式：
    
    ```python
    validator = MemoryValidator()
    
    # 驗證記憶狀態
    result = validator.validate({
        "content": "user prefers dark mode",
        "timestamp": "2026-03-23T10:00:00",
        "version": 1
    })
    
    print(f"State: {result.state}")
    print(f"Trustworthy: {result.is_trustworthy}")
    ```
    """
    
    def __init__(self, max_age_hours: int = 24):
        self.max_age = timedelta(hours=max_age_hours)
        self.known_hashes: Dict[str, str] = {}
    
    def validate(self, memory: Dict[str, Any]) -> ValidationResult:
        """
        驗證記憶狀態
        
        Args:
            memory: 記憶內容，應包含 timestamp, content, version
        
        Returns:
            ValidationResult: 驗證結果
        """
        issues = []
        
        # 檢查必要欄位
        if "content" not in memory:
            issues.append("Missing 'content' field")
        
        if "timestamp" not in memory:
            issues.append("Missing 'timestamp' field")
        
        if issues:
            return ValidationResult(
                state=MemoryState.UNKNOWN,
                timestamp=datetime.now(),
                age_seconds=0,
                is_trustworthy=False,
                issues=issues
            )
        
        # 解析時間戳
        try:
            ts_str = memory["timestamp"]
            if isinstance(ts_str, str):
                timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                timestamp = ts_str
        except:
            issues.append("Invalid timestamp format")
            return ValidationResult(
                state=MemoryState.CORRUPTED,
                timestamp=datetime.now(),
                age_seconds=0,
                is_trustworthy=False,
                issues=issues
            )
        
        # 計算年齡
        age = datetime.now() - timestamp
        age_seconds = age.total_seconds()
        
        # 檢查是否過期
        if age > self.max_age:
            issues.append(f"Memory is stale (age: {age_seconds/3600:.1f}h)")
            return ValidationResult(
                state=MemoryState.STALE,
                timestamp=timestamp,
                age_seconds=age_seconds,
                is_trustworthy=False,
                issues=issues
            )
        
        # 檢查內容一致性
        content_hash = self._compute_hash(memory.get("content", ""))
        
        if "version" in memory:
            known_key = f"{memory.get('type', 'default')}"
            if known_key in self.known_hashes:
                if self.known_hashes[known_key] != content_hash:
                    issues.append("Content hash mismatch - possible drift detected")
                    return ValidationResult(
                        state=MemoryState.INCONSISTENT,
                        timestamp=timestamp,
                        age_seconds=age_seconds,
                        is_trustworthy=False,
                        issues=issues
                    )
            else:
                self.known_hashes[known_key] = content_hash
        
        return ValidationResult(
            state=MemoryState.VALID,
            timestamp=timestamp,
            age_seconds=age_seconds,
            is_trustworthy=True,
            issues=[]
        )
    
    def _compute_hash(self, content: str) -> str:
        """計算內容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def validate_batch(self, memories: List[Dict[str, Any]]) -> List[ValidationResult]:
        """批量驗證記憶"""
        return [self.validate(m) for m in memories]
    
    def get_trustworthy_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """過濾出可信賴的記憶"""
        trustworthy = []
        
        for memory in memories:
            result = self.validate(memory)
            if result.is_trustworthy:
                trustworthy.append(memory)
        
        return trustworthy