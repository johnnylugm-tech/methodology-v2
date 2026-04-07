"""
Technical Debt Module
====================
技術債務追蹤系統

使用方式：

    from technical_debt import DebtRegistry
    
    registry = DebtRegistry()
    registry.add("使用 eval()", severity="high", ticket="TASK-123")
    registry.list()
    registry.resolve("debt-xxx")
"""

from .registry import DebtRegistry, DebtRecord

__all__ = ['DebtRegistry', 'DebtRecord']
