# Release Notes - v5.32

## Date: 2026-03-23

## New Feature: Memory Governance Framework

### Overview

記憶治理框架 (Memory Governance Framework) 解決 Vector DB 檢索時的雜訊問題和狀態漂移問題。

### Components

#### 1. Memory Validator (`memory_governance/memory_validator.py`)
- 驗證記憶時間戳
- 檢測過期記憶（預設 24 小時）
- 評估記憶內容一致性（hash 追蹤）
- 批量驗證支援

**新增類別：**
- `MemoryState` (Enum): VALID, STALE, CORRUPTED, INCONSISTENT, UNKNOWN
- `ValidationResult` (Dataclass): 驗證結果含狀態、時間、年齡、可信度

#### 2. State Coordinator (`memory_governance/state_coordinator.py`)
- 維護全局記憶狀態
- 檢測多 Agent 間的記憶衝突
- 支援衝突解決追蹤

**新增類別：**
- `ConflictType` (Enum): CONTENT_MISMATCH, TIMESTAMP_CONFLICT, VERSION_CONFLICT, DELETED_CONFLICT
- `MemoryConflict` (Dataclass): 衝突資料結構
- `StateCoordinator` (Class): 狀態協調器

#### 3. Conflict Resolver (`memory_governance/conflict_resolver.py`)
- 四種解決策略：LATEST, MAJORITY, PRIORITY, MANUAL
- 優先級自訂支援
- 平手時使用時間戳打破

**新增類別：**
- `ResolutionStrategy` (Enum): LATEST, MAJORITY, PRIORITY, MANUAL
- `ResolvedValue` (Dataclass): 解決後的值
- `ConflictResolver` (Class): 衝突解決器

#### 4. Memory Audit (`memory_governance/memory_audit.py`)
- 記錄所有記憶操作（read/write/delete）
- SHA-256 簽名防止篡改
- SQLite 持久化存儲
- 完整性驗證

**新增類別：**
- `MemoryRecord` (Dataclass): 審計記錄
- `MemoryAudit` (Class): 審計系統

### CLI Integration

新增 `memory` 子命令：

```bash
# 顯示記憶治理狀態
python cli.py memory status

# 驗證記憶
python cli.py memory validate

# 查看審計日誌
python cli.py memory audit

# 解決衝突（需要程式碼）
```

### Files Added

```
memory_governance/
├── __init__.py
├── memory_validator.py
├── state_coordinator.py
├── conflict_resolver.py
└── memory_audit.py

docs/cases/case59_memory_governance.md
```

### Usage Example

```python
from memory_governance import (
    MemoryValidator,
    StateCoordinator,
    ConflictResolver,
    ResolutionStrategy,
    MemoryAudit
)

# 驗證記憶
validator = MemoryValidator()
result = validator.validate({
    "content": "user prefers dark mode",
    "timestamp": "2026-03-23T10:00:00",
    "version": 1
})

# 協調狀態
coordinator = StateCoordinator()
coordinator.register("agent-1", {"theme": "dark"})
coordinator.register("agent-2", {"theme": "light"})
conflicts = coordinator.detect_conflicts()

# 解決衝突
resolver = ConflictResolver()
resolved = resolver.resolve(values, strategy=ResolutionStrategy.LATEST)

# 審計
audit = MemoryAudit()
record_id = audit.record("agent-1", "write", "preference", {"value": "dark"})
audit.verify(record_id)
```

### Dependencies

- Python 3.8+
- sqlite3 (標準庫)

### Migration Notes

此功能完全向後相容，不影響現有功能。

---

**Full Changelog:** [CHANGELOG.md](CHANGELOG.md)