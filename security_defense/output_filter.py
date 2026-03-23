#!/usr/bin/env python3
"""
Output Filter
============
Layer 3: 輸出過濾 - 敏感資訊檢測與脫敏

功能：
- 敏感資訊檢測（密碼、API Key、信用卡等）
- 脫敏處理
- 審計日誌
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import re


class SensitivePattern(Enum):
    """敏感模式"""
    PASSWORD = "password"
    API_KEY = "api_key"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    EMAIL = "email"
    PHONE = "phone"
    IP_ADDRESS = "ip_address"
    PRIVATE_KEY = "private_key"
    SECRET = "secret"


class OutputFilter:
    """
    輸出過濾器
    
    使用方式：
    
    ```python
    filter = OutputFilter()
    
    result = filter.filter("Your API key is: sk-1234567890abcdef")
    
    if result.has_sensitive:
        print(f"Found: {result.found_types}")
        print(f"Sanitized: {result.sanitized_output}")
    ```
    """
    
    # 敏感模式正則表達式
    PATTERNS = {
        SensitivePattern.PASSWORD: [
            r'password[:\s=]+\S+',
            r'passwd[:\s=]+\S+',
            r'pwd[:\s=]+\S+',
        ],
        SensitivePattern.API_KEY: [
            r'sk-[a-zA-Z0-9]{32,}',
            r'api[_-]?key[:\s=]+[a-zA-Z0-9]{20,}',
            r'ghp_[a-zA-Z0-9]{36,}',
            r'gho_[a-zA-Z0-9]{36,}',
        ],
        SensitivePattern.CREDIT_CARD: [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        ],
        SensitivePattern.SSN: [
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        ],
        SensitivePattern.EMAIL: [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        ],
        SensitivePattern.PHONE: [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        ],
        SensitivePattern.IP_ADDRESS: [
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        ],
        SensitivePattern.PRIVATE_KEY: [
            r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----',
        ],
        SensitivePattern.SECRET: [
            r'secret[:\s=]+\S+',
            r'token[:\s=]+[a-zA-Z0-9]{20,}',
        ],
    }
    
    def __init__(self):
        self.audit_log: List[dict] = []
        self.redaction_marker = "[REDACTED]"
    
    def filter(self, output: str) -> Dict:
        """
        過濾輸出
        
        Returns:
            dict: {
                has_sensitive: bool,
                found_types: List[SensitivePattern],
                sanitized_output: str,
                audit_log: dict
            }
        """
        found_types = []
        sanitized = output
        
        for pattern_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    found_types.append(pattern_type)
                    # 脫敏
                    sanitized = re.sub(pattern, self.redaction_marker, sanitized, flags=re.IGNORECASE)
        
        # 記錄審計
        audit_entry = {
            "timestamp": self._get_timestamp(),
            "found_count": len(found_types),
            "types": [t.value for t in found_types]
        }
        self.audit_log.append(audit_entry)
        
        return {
            "has_sensitive": len(found_types) > 0,
            "found_types": found_types,
            "sanitized_output": sanitized,
            "audit_log": audit_entry
        }
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_audit_log(self) -> List[dict]:
        """取得審計日誌"""
        return self.audit_log
