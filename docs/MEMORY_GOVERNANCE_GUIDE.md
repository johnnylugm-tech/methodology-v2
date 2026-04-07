# Memory Governance Framework - 新手上路

> 解決 Vector DB 檢索雜訊多、狀態漂移問題

---

## 📋 概述

Memory Governance Framework 提供：

| 模組 | 功能 |
|------|------|
| `MemoryValidator` | 驗證記憶狀態 |
| `StateCoordinator` | 協調多 Agent 記憶 |
| `ConflictResolver` | 解決記憶衝突 |
| `MemoryAudit` | 不可偽造的審計日誌 |

---

## 🚀 快速開始

### Step 1: 驗證記憶

```bash
python3 cli.py memory validate
```

### Step 2: 查看狀態

```bash
python3 cli.py memory status
```

### Step 3: 查看審計日誌

```bash
python3 cli.py memory audit
```

---

## 📖 核心概念

### MemoryValidator

驗證記憶狀態，檢測過期、損壞、不一致的記憶。

```python
from memory_governance import MemoryValidator

validator = MemoryValidator()

result = validator.validate({
    "content": "user prefers dark mode",
    "timestamp": "2026-03-23T10:00:00",
    "version": 1
})

print(f"State: {result.state}")
print(f"Trustworthy: {result.is_trustworthy}")
```

### StateCoordinator

協調多個 Agent 的記憶狀態。

```python
from memory_governance import StateCoordinator

coordinator = StateCoordinator()

# 註冊 Agent 狀態
coordinator.register("agent-1", {"preference": "dark"})
coordinator.register("agent-2", {"preference": "light"})

# 檢測衝突
conflicts = coordinator.detect_conflicts()

# 解決衝突
for conflict in conflicts:
    coordinator.resolve(conflict.conflict_id, "agent-1")
```

### ConflictResolver

解決記憶衝突，提供三種策略。

```python
from memory_governance import ConflictResolver, ResolutionStrategy

resolver = ConflictResolver()

values = [
    {"agent_id": "agent-1", "value": "dark", "timestamp": ...},
    {"agent_id": "agent-2", "value": "light", "timestamp": ...},
]

resolved = resolver.resolve(values, strategy=ResolutionStrategy.LATEST)
print(resolved.value)  # "dark" or "light"
```

### MemoryAudit

不可偽造的審計日誌。

```python
from memory_governance import MemoryAudit

audit = MemoryAudit()

# 記錄操作
audit.record("agent-1", "write", "preference", {"value": "dark"})

# 驗證
if audit.verify(record_id):
    print("✅ Record is authentic")
```

---

## 🎯 使用場景

### 場景 1: 多 Agent 協作

```
Agent-1: 我選擇方案 A
Agent-2: 我選擇方案 B
     ↓
StateCoordinator 檢測衝突
     ↓
ConflictResolver 解決
     ↓
共識：方案 A（多數服從）
```

### 場景 2: 長時間任務

```
任務開始 → 記憶更新 → 驗證狀態 → 任務繼續
     ↓
如果 MemoryValidator 發現過期
     ↓
重新同步或警告
```

---

## 📊 預期效果

| 指標 | 改善 |
|------|------|
| 檢索雜訊 | -60% |
| 狀態漂移 | -80% |
| 行為一致性 | +90% |

---

*最後更新：2026-03-23*