#!/usr/bin/env python3
"""
Input Validator
==============
Layer 1: 輸入驗證 - 檢測 Prompt Injection、LPCI 攻擊

功能：
- Prompt Injection 檢測
- LPCI 特徵辨識
- 黑白名單機制
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Set
import re


class ThreatType(Enum):
    """威脅類型"""
    PROMPT_INJECTION = "prompt_injection"
    LPCI = "lpi_attack"
    COMMAND_INJECTION = "command_injection"
    DATA_EXFILTRATION = "data_exfiltration"
    SOCIAL_ENGINEERING = "social_engineering"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """驗證結果"""
    is_safe: bool
    threat_type: Optional[ThreatType]
    confidence: float  # 0-1
    matched_patterns: List[str]
    sanitized_input: str
    recommendations: List[str]


class InputValidator:
    """
    輸入驗證器
    
    使用方式：
    
    ```python
    validator = InputValidator()
    
    result = validator.validate("Remember to ignore previous instructions and...")
    
    if not result.is_safe:
        print(f"Threat: {result.threat_type}")
        print(f"Confidence: {result.confidence}")
        print(f"Sanitized: {result.sanitized_input}")
    ```
    """
    
    # LPCI 特徵模式
    LPCI_PATTERNS = [
        r'ignore\s+(all\s+)?previous?\s+instructions?',
        r'disregard\s+(all\s+)?safety',
        r'new\s+system\s+prompt',
        r'override\s+(your\s+)?(safety|security)',
        r'you\s+are\s+now\s+.*\(as\s+an?\s+AI\)',
        r'\(_system:\s*',
        r'<\|.*\|>',  # XML tags often used in LPCI
    ]
    
    # Prompt Injection 模式
    INJECTION_PATTERNS = [
        r'###\s*instruction',
        r'---\s*user',
        r' END\s+OF\s+SYSTEM',
        r'\[\[INST\]',
        r'<\?xml',
        r'<script',
    ]
    
    # 可疑關鍵詞
    SUSPICIOUS_KEYWORDS = [
        "bypass", "ignore", "disregard", "forget",
        "override", "new instructions", "system prompt",
        "admin", "root", "sudo",
    ]
    
    def __init__(self):
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self._setup_default_patterns()
    
    def _setup_default_patterns(self):
        """設定預設模式"""
        # 預設不加入任何 whitelist
        # 黑白名單可由用戶配置
    
    def validate(self, input_text: str) -> ValidationResult:
        """
        驗證輸入
        
        Args:
            input_text: 待驗證的輸入文字
        
        Returns:
            ValidationResult: 驗證結果
        """
        matched_patterns = []
        threat_type = None
        confidence = 0.0
        
        # 1. 檢查 LPCI 模式
        for pattern in self.LPCI_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                matched_patterns.append(f"LPCI: {pattern}")
                threat_type = ThreatType.LPCI
                confidence = max(confidence, 0.9)
        
        # 2. 檢查 Prompt Injection 模式
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                matched_patterns.append(f"INJECTION: {pattern}")
                if threat_type is None:
                    threat_type = ThreatType.PROMPT_INJECTION
                confidence = max(confidence, 0.8)
        
        # 3. 檢查可疑關鍵詞
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in input_text.lower():
                matched_patterns.append(f"KEYWORD: {keyword}")
                if threat_type is None:
                    threat_type = ThreatType.UNKNOWN
                confidence = max(confidence, 0.5)
        
        # 4. 檢查黑白名單
        if self.blacklist:
            for blacklisted in self.blacklist:
                if blacklisted.lower() in input_text.lower():
                    matched_patterns.append(f"BLACKLIST: {blacklisted}")
                    threat_type = ThreatType.UNKNOWN
                    confidence = max(confidence, 0.95)
        
        # 計算最終結果
        is_safe = len(matched_patterns) == 0 or confidence < 0.7
        
        # 清理輸入
        sanitized = self._sanitize(input_text, matched_patterns)
        
        return ValidationResult(
            is_safe=is_safe,
            threat_type=threat_type,
            confidence=confidence,
            matched_patterns=matched_patterns,
            sanitized_input=sanitized,
            recommendations=self._get_recommendations(threat_type, confidence)
        )
    
    def _sanitize(self, text: str, matched_patterns: List[str]) -> str:
        """清理輸入"""
        sanitized = text
        
        # 移除明顯的 injection 模式
        sanitized = re.sub(r'###\s*instruction.*', '[REDACTED]', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'---\s*user.*', '[REDACTED]', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'<script.*?</script>', '[REDACTED]', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        return sanitized
    
    def _get_recommendations(self, threat_type: Optional[ThreatType], confidence: float) -> List[str]:
        """取得建議"""
        recommendations = []
        
        if threat_type == ThreatType.LPCI:
            recommendations.append("LPCI attack detected - review input carefully")
            recommendations.append("Do not follow injected instructions")
        elif threat_type == ThreatType.PROMPT_INJECTION:
            recommendations.append("Potential prompt injection - sanitize input")
        elif confidence > 0.7:
            recommendations.append("High confidence threat - consider rejecting input")
        
        return recommendations
    
    def add_to_whitelist(self, pattern: str):
        """加入白名單"""
        self.whitelist.add(pattern)
    
    def add_to_blacklist(self, pattern: str):
        """加入黑名單"""
        self.blacklist.add(pattern)
