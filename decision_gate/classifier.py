#!/usr/bin/env python3
"""
Decision Classifier
==================
自動分類技術決策的風險等級
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class RiskLevel(Enum):
    """風險等級"""
    HIGH = "🔴 HIGH"      # 必須照 spec
    MEDIUM = "🟡 MEDIUM"  # 列出選項建議
    LOW = "🔵 LOW"        # 可自主決定

class DecisionType(Enum):
    """決策類型"""
    ARCHITECTURE = "architecture"      # 架構決策
    API_CHOICE = "api_choice"          # API 選擇
    ALGORITHM = "algorithm"            # 演算法
    CONFIG_DEFAULT = "config_default"  # 預設值
    TOOL_SELECTION = "tool_selection"  # 工具選型
    FILE_STRUCTURE = "file_structure"  # 目錄結構
    NAMING = "naming"                  # 命名

@dataclass
class ClassifiedDecision:
    """已分類的決策"""
    decision_id: str
    item: str  # 決策項目（如 "chunk_size"）
    decision_type: DecisionType
    risk_level: RiskLevel
    description: str
    spec_reference: Optional[str] = None  # spec 中的依據
    options: Optional[List[str]] = None  # 選項列表（MEDIUM 用）
    recommendation: Optional[str] = None  # 建議（MEDIUM 用）
    requires_confirmation: bool = False  # 是否需要 user 確認

class DecisionClassifier:
    """
    決策分類器
    
    使用方式：
    
    ```python
    classifier = DecisionClassifier()
    
    # 分類一個決策
    decision = classifier.classify(
        item="chunk_size",
        description="Embedding chunk size"
    )
    
    print(f"Risk: {decision.risk_level.value}")
    print(f"Needs confirmation: {decision.requires_confirmation}")
    ```
    """
    
    # HIGH 風險關鍵字
    HIGH_RISK_KEYWORDS = [
        "architecture", "api", "database", "auth", "security",
        "algorithm", "model", "framework", "protocol", "gateway"
    ]
    
    # MEDIUM 風險關鍵字
    MEDIUM_RISK_KEYWORDS = [
        "timeout", "retry", "cache", "pool", "batch",
        "default", "threshold", "limit", "size", "count"
    ]
    
    def __init__(self):
        self.decisions: List[ClassifiedDecision] = []
    
    def classify(
        self,
        item: str,
        description: str,
        spec_reference: Optional[str] = None
    ) -> ClassifiedDecision:
        """分類一個決策"""
        import uuid
        
        item_lower = item.lower()
        desc_lower = description.lower()
        combined = item_lower + " " + desc_lower
        
        # 判斷決策類型和風險
        decision_type, risk_level = self._determine_type_and_risk(combined)
        
        # HIGH 風險決策需要確認
        requires_confirmation = risk_level == RiskLevel.HIGH
        
        # MEDIUM 風險決策需要列出選項
        options = None
        recommendation = None
        if risk_level == RiskLevel.MEDIUM:
            options = self._generate_options(item, description)
            recommendation = options[0] if options else None
        
        decision = ClassifiedDecision(
            decision_id=f"D-{uuid.uuid4().hex[:6].upper()}",
            item=item,
            decision_type=decision_type,
            risk_level=risk_level,
            description=description,
            spec_reference=spec_reference,
            options=options,
            recommendation=recommendation,
            requires_confirmation=requires_confirmation
        )
        
        self.decisions.append(decision)
        return decision
    
    def _determine_type_and_risk(self, text: str) -> tuple:
        """判斷決策類型和風險"""
        # HIGH 風險檢測
        for keyword in self.HIGH_RISK_KEYWORDS:
            if keyword in text:
                return self._get_decision_type(keyword), RiskLevel.HIGH
        
        # MEDIUM 風險檢測
        for keyword in self.MEDIUM_RISK_KEYWORDS:
            if keyword in text:
                return DecisionType.CONFIG_DEFAULT, RiskLevel.MEDIUM
        
        # 預設為 LOW
        return DecisionType.FILE_STRUCTURE, RiskLevel.LOW
    
    def _get_decision_type(self, keyword: str) -> DecisionType:
        """根據關鍵字取得決策類型"""
        mapping = {
            "architecture": DecisionType.ARCHITECTURE,
            "api": DecisionType.API_CHOICE,
            "algorithm": DecisionType.ALGORITHM,
            "model": DecisionType.ALGORITHM,
            "framework": DecisionType.ARCHITECTURE,
            "protocol": DecisionType.ARCHITECTURE,
            "gateway": DecisionType.ARCHITECTURE,
            "database": DecisionType.ARCHITECTURE,
            "auth": DecisionType.API_CHOICE,
            "security": DecisionType.API_CHOICE,
        }
        return mapping.get(keyword, DecisionType.TOOL_SELECTION)
    
    def _generate_options(self, item: str, description: str) -> List[str]:
        """為 MEDIUM 風險決策生成選項"""
        # 根據項目類型生成合理選項
        options_map = {
            "timeout": ["30", "60", "120"],
            "retry": ["3", "5", "10"],
            "chunk_size": ["512", "800", "1024"],
            "batch_size": ["32", "64", "128"],
            "pool_size": ["10", "20", "50"],
        }
        
        item_lower = item.lower().replace("-", "_").replace(" ", "_")
        return options_map.get(item_lower, ["option_a", "option_b", "option_c"])
    
    def get_unconfirmed_high_risk(self) -> List[ClassifiedDecision]:
        """取得所有未確認的 HIGH 風險決策"""
        return [
            d for d in self.decisions
            if d.risk_level == RiskLevel.HIGH and d.requires_confirmation
        ]
    
    def confirm_decision(self, decision_id: str, confirmed_value: str) -> bool:
        """確認一個決策"""
        for decision in self.decisions:
            if decision.decision_id == decision_id:
                decision.requires_confirmation = False
                return True
        return False