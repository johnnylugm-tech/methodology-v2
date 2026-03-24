"""
Decision Gate Module
===================
決策分類閘道，確保所有技術決策都有明確的風險分類和確認

風險等級：
- 🔴 HIGH: 架構決策、API 選擇、核心演算法 → 必須照 spec
- 🟡 MEDIUM: 預設值、工具選型 → 列出選項建議
- 🔵 LOW: 目錄結構、檔案命名 → 可自主決定
"""

from .classifier import DecisionClassifier, RiskLevel, DecisionType
from .recorder import DecisionRecorder, DecisionRecord

__all__ = [
    'DecisionClassifier',
    'RiskLevel', 
    'DecisionType',
    'DecisionRecorder',
    'DecisionRecord',
]