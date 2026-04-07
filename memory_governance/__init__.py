"""
Memory Governance Framework
===========================
解決 Vector DB 檢索雜訊、狀態漂移問題

核心概念：
- Memory Validator：驗證記憶狀態
- State Coordinator：協調多 Agent 記憶
- Conflict Resolver：解決記憶衝突
- Audit Trail：不可偽造的記憶日誌
"""

from .memory_validator import MemoryValidator, MemoryState
from .state_coordinator import StateCoordinator, MemoryConflict
from .conflict_resolver import ConflictResolver, ResolutionStrategy
from .memory_audit import MemoryAudit, MemoryRecord

__all__ = [
    'MemoryValidator',
    'MemoryState',
    'StateCoordinator',
    'MemoryConflict',
    'ConflictResolver',
    'ResolutionStrategy',
    'MemoryAudit',
    'MemoryRecord',
]