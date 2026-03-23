# Case 47: Double Confirmation - 雙重確認機制

## 問題背景

在關鍵操作上，單次確認往往不足以防止失誤：

- **發布到 GitHub**：版本號填錯可能導致相依套件冲突
- **修改 Constitution**：影響全局規則，需要多方確認
- **刪除檔案**：誤刪代價高昂
- **繞過 Quality Gate**：繞過辛苦建立的品質防線

這些操作一旦執行就很難逆轉，需要更嚴格的確認機制。

---

## 解決方案：Double Confirmation

### 核心設計

```
確認等級：
┌─────────────────────────────────────────────┐
│  NONE      → 不需要確認                      │
│  SINGLE    → 單次確認                         │
│  DOUBLE    → 雙重確認（2人）                   │
│  APPROVAL  → 需要人類審批                      │
│  BLOCKED   → 直接阻止                         │
└─────────────────────────────────────────────┘
```

### 確認矩陣

| 操作 | 確認等級 | 說明 |
|------|---------|------|
| `release` | DOUBLE | 需要2人確認版本號 |
| `constitution_edit` | APPROVAL | 需要人類審批 |
| `delete_file` | DOUBLE | 需要2人確認 |
| `bypass_quality_gate` | APPROVAL | 需要人類審批 |
| `force_push` | APPROVAL | 需要人類審批 |
| `merge_no_review` | BLOCKED | 直接阻止 |
| `schema_change` | APPROVAL | 需要人類審批 |
| `env_modification` | DOUBLE | 需要2人確認 |

---

## 使用範例

### 1. 基本使用

```python
from anti_shortcut import (
    DoubleConfirmation,
    ConfirmationLevel,
    create_pending,
    confirm,
    is_approved,
)

# 初始化
dc = DoubleConfirmation(timeout_minutes=30)

# 檢查操作是否需要確認
level = dc.requires_confirmation("release")
print(f"Level: {level.value}")  # "double"

# 創建待確認
conf_id = dc.create_pending(
    operation="release",
    description="發布 v2.1.0 到 GitHub",
    metadata={"version": "2.1.0", "repo": "my-project"}
)

if conf_id == "__BLOCKED__":
    print("操作被阻止，無法執行")
elif conf_id is None:
    print("不需要確認，直接執行")
else:
    print(f"等待確認，ID: {conf_id}")
```

### 2. 雙重確認流程

```python
# Agent 確認（第一次確認）
dc.confirm(conf_id, confirmed_by="agent-001")

# 檢查狀態
status = dc.get_status(conf_id)
print(f"""
操作: {status['operation']}
狀態: {status['status']}
已確認: {status['confirmations']}
需要: {status['required']} 人
""")

# 人類確認（第二次確認）
if len(status['confirmations']) < status['required']:
    print("等待第二人確認...")

dc.confirm(conf_id, confirmed_by="human-supervisor")

# 最終檢查
if dc.is_approved(conf_id):
    print("✓ 確認完成，可以執行操作")
else:
    print("✗ 確認未完成")
```

### 3. 拒絕操作

```python
# 人類拒絕
dc.reject(
    confirmation_id=conf_id,
    rejected_by="human-supervisor",
    reason="版本號不正確，應該是 2.1.1"
)

status = dc.get_status(conf_id)
print(f"狀態: {status['status']}")  # "rejected"
```

### 4. 快速函數

```python
from anti_shortcut import requires_confirmation, create_pending, confirm, is_approved

# 快速檢查
if requires_confirmation("release") != ConfirmationLevel.NONE:
    conf_id = create_pending("release", "發布 v2.0.0")
    # ... 等待確認

# 確認
if confirm(conf_id, "agent-001"):
    if is_approved(conf_id):
        print("可以執行")
```

### 5. 取得待確認列表

```python
# 所有待確認
pending = dc.get_pending()
for p in pending:
    print(f"[{p.confirmation_id}] {p.operation}: {p.description}")

# 特定操作的待確認
release_pending = dc.get_pending(operation="release")
```

### 6. 清理過期確認

```python
dc.cleanup_expired()
print(f"已清理過期確認")
```

---

## CLI 整合

### 發布前雙重確認

```bash
# 發布前需要雙重確認
$ python3 cli.py release --version 2.1.0 --confirm

Waiting for confirmation...
[1/2] Agent confirmed
[2/2] Waiting for human confirmation...

# 人類在另一個 terminal 或 UI 確認
$ python3 cli.py confirm --id abc12345 --by human-admin

✓ Release approved
```

### 確認命令

```bash
# 查看待確認列表
$ python3 cli.py confirmations list

# 確認操作
$ python3 cli.py confirmations confirm --id abc12345 --by human-admin

# 拒絕操作
$ python3 cli.py confirmations reject --id abc12345 --by human-admin --reason "版本號錯誤"
```

---

## 與 Anti-Shortcut Enforcer 整合

```python
from anti_shortcut import AntiShortcutEnforcer, DoubleConfirmation

enforcer = AntiShortcutEnforcer()
dc = DoubleConfirmation()

# 檢查是否需要確認
level = dc.requires_confirmation("release")

if level == ConfirmationLevel.BLOCKED:
    print("操作被阻止")
    enforcer.log_violation("BLOCKED_OPERATION", operation="merge_no_review")
    
elif level != ConfirmationLevel.NONE:
    conf_id = dc.create_pending("release", "發布新版本")
    # 等待確認流程
```

---

## 設計理念

### 為什麼需要雙重確認？

1. **防止單點失誤**：一個人可能看錯，兩個人同時看錯的概率極低
2. **強制審查**：確認過程本身就是審查
3. **責任分散**：多人確認 = 多人負責
4. **心理門檻**：需要叫第二人看，會讓人更謹慎

### 確認 vs 審批

```
確認 (Confirmation)：
- 快速，雙方都在場
- 適用於標準操作
- 如：「你確認要刪除這個檔案？」

審批 (Approval)：
- 正式，需要記錄
- 適用於重大變更
- 如：「申請繞過 quality gate，理由是...」
```

---

## 總結

Double Confirmation 為關鍵操作提供了一層保護：

```
┌──────────────────────────────────────────┐
│          Double Confirmation             │
├──────────────────────────────────────────┤
│  操作級別     確認要求      適用場景      │
├──────────────────────────────────────────┤
│  NONE       無           一般操作        │
│  SINGLE     1人          低風險變更       │
│  DOUBLE     2人          重要操作         │
│  APPROVAL   人類審批     高風險變更       │
│  BLOCKED    直接拒絕     禁止操作        │
└──────────────────────────────────────────┘
```

**目標：讓失誤變得困難，讓確認變得簡單。**
