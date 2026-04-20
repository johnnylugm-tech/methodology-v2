#!/usr/bin/env python3
"""
enums.py - Risk Assessment Enumerations
[FR-04] State tracking enums
"""

from enum import Enum


class RiskDimension(Enum):
    """風險維度分類"""
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    EXTERNAL = "external"


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """根據分數推斷風險等級"""
        if score >= 0.7:
            return cls.CRITICAL
        elif score >= 0.5:
            return cls.HIGH
        elif score >= 0.3:
            return cls.MEDIUM
        else:
            return cls.LOW

    @property
    def priority(self) -> int:
        """優先級數值（越高越嚴重）"""
        return {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }[self]


class RiskStatus(Enum):
    """風險狀態"""
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    ESCALATED = "escalated"
    CLOSED = "closed"

    def can_transition_to(self, target: "RiskStatus") -> bool:
        """檢查狀態轉換是否合法"""
        valid_transitions = {
            RiskStatus.OPEN: [RiskStatus.MITIGATED, RiskStatus.ACCEPTED, RiskStatus.ESCALATED],
            RiskStatus.MITIGATED: [RiskStatus.CLOSED, RiskStatus.ESCALATED, RiskStatus.OPEN],
            RiskStatus.ACCEPTED: [RiskStatus.CLOSED, RiskStatus.ESCALATED],
            RiskStatus.ESCALATED: [RiskStatus.CLOSED, RiskStatus.OPEN],
            RiskStatus.CLOSED: [],  # 終態
        }
        return target in valid_transitions.get(self, [])


class StrategyType(Enum):
    """風險應對策略類型"""
    AVOID = "avoid"       # 消除風險源
    MITIGATE = "mitigate"  # 降低概率或影響
    TRANSFER = "transfer"  # 保險、外包
    ACCEPT = "accept"     # 列入監控清單

    @classmethod
    def from_score(cls, score: float) -> "StrategyType":
        """根據分數選擇策略"""
        if score > 0.6:
            return cls.AVOID
        elif score >= 0.3:
            return cls.MITIGATE
        else:
            return cls.ACCEPT