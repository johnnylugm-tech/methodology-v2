# Case 59: Memory Governance Framework

## Problem Statement

Vector DB 檢索時常出現大量雜訊，導致 Agent 取得過期或不一致的記憶。狀態漂移（state drift）讓多個 Agent 對同一事實產生衝突的理解。

## Solution

Memory Governance Framework 提供四層防護：

1. **Memory Validator** - 驗證記憶狀態，過濾過期/損壞的記憶
2. **State Coordinator** - 協調多 Agent 的記憶狀態，檢測衝突
3. **Conflict Resolver** - 根據策略解決記憶衝突
4. **Memory Audit** - 不可偽造的記憶審計日誌

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory Governance                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Memory    │───▶│     State       │───▶│   Conflict   │ │
│  │  Validator  │    │   Coordinator   │    │   Resolver   │ │
│  └─────────────┘    └─────────────────┘    └──────────────┘ │
│         │                   │                       │        │
│         ▼                   ▼                       ▼        │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Memory    │    │  Global State   │    │   Resolution │ │
│  │   Audit     │    │    Summary      │    │   Strategy   │ │
│  └─────────────┘    └─────────────────┘    └──────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Usage Examples

### 1. 驗證記憶狀態

```python
from memory_governance import MemoryValidator, MemoryState

validator = MemoryValidator(max_age_hours=24)

# 驗證單一記憶
result = validator.validate({
    "content": "user prefers dark mode",
    "timestamp": "2026-03-23T10:00:00",
    "version": 1
})

if result.is_trustworthy:
    print(f"✅ Memory is valid, age: {result.age_seconds/3600:.1f}h")
else:
    print(f"❌ Issues: {result.issues}")

# 批量驗證
memories = [...]
trustworthy = validator.get_trustworthy_memories(memories)
```

### 2. 協調多 Agent 狀態

```python
from memory_governance import StateCoordinator

coordinator = StateCoordinator()

# 註冊 Agent 狀態
coordinator.register("agent-1", {"theme": "dark", "language": "en"})
coordinator.register("agent-2", {"theme": "light", "language": "en"})

# 檢測衝突
conflicts = coordinator.detect_conflicts()
print(f"Found {len(conflicts)} conflicts")

# 解決衝突
for conflict in conflicts:
    coordinator.resolve(conflict.conflict_id, winner_agent_id="agent-1")

# 取得狀態摘要
summary = coordinator.get_global_state_summary()
print(f"Agents: {summary['total_agents']}, Keys: {summary['total_keys']}")
```

### 3. 解決衝突

```python
from memory_governance import ConflictResolver, ResolutionStrategy
from datetime import datetime

resolver = ConflictResolver(agent_priorities={"agent-1": 10, "agent-2": 5})

values = [
    {"agent_id": "agent-1", "value": "dark", "timestamp": datetime.now()},
    {"agent_id": "agent-2", "value": "light", "timestamp": datetime.now()},
]

# 使用最新時間戳策略
resolved = resolver.resolve(values, strategy=ResolutionStrategy.LATEST)
print(f"Winner: {resolved.winning_agent_id}, Value: {resolved.value}")

# 使用優先級策略
resolved = resolver.resolve(values, strategy=ResolutionStrategy.PRIORITY)
print(f"Winner (priority): {resolved.winning_agent_id}")
```

### 4. 審計日誌

```python
from memory_governance import MemoryAudit

audit = MemoryAudit(db_path=".methodology/memory_audit.db")

# 記錄操作
record_id = audit.record("agent-1", "write", "preference", {"value": "dark"})

# 驗證完整性
if audit.verify(record_id):
    print("✅ Record is authentic")

# 查詢記錄
records = audit.get_records(agent_id="agent-1", limit=50)
for r in records:
    print(f"{r.timestamp}: {r.action} on {r.memory_key}")
```

## CLI Usage

```bash
# 顯示記憶治理狀態
python cli.py memory status

# 驗證記憶
python cli.py memory validate

# 查看審計日誌
python cli.py memory audit

# 解決衝突（需要程式碼）
# Use StateCoordinator.resolve() in code
```

## Integration with Vector DB

在 Vector DB 檢索後加入驗證層：

```python
def retrieve_with_validation(vector_db, query, agent_id):
    """檢索並驗證記憶"""
    results = vector_db.search(query)
    
    validator = MemoryValidator(max_age_hours=24)
    audit = MemoryAudit()
    
    trustworthy = []
    for result in results:
        memory = result.payload
        validation = validator.validate(memory)
        
        if validation.is_trustworthy:
            trustworthy.append(result)
            audit.record(agent_id, "read", memory.get("key"))
        else:
            audit.record(agent_id, "read_rejected", memory.get("key"), 
                        {"issues": validation.issues})
    
    return trustworthy
```

## Key Benefits

| 問題 | 解決方案 | 效果 |
|------|----------|------|
| 過期記憶被使用 | 時間戳驗證 | 自動過濾 >24h 的記憶 |
| 狀態漂移 | 全局狀態協調 | 檢測並標記衝突 |
| 衝突無法解決 | 多策略解決器 | LATEST/MAJORITY/PRIORITY |
| 無法追溯 | SHA-256 審計日誌 | 不可偽造的完整日誌 |

## Version

- v5.32: Initial implementation