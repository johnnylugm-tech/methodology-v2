# 案例 53：Policy Engine - 政策引擎（Hard Block 強制執行）

## 情境描述

**問題：** 框架只是建議，開發者可以繞過所有檢查，直接 commit。

**解決方案：** Policy Engine - 政策即代碼，沒有「可選」，只有「完成」或「失敗」。

核心概念：
- **Hard Block**：不符合政策就阻擋
- **No Opt-Out**：沒有繞過選項
- **Policy as Code**：政策是可執行的代碼

---

## 案例 53.1：基本使用

### 背景
需要一個可以定義、執行和強制執行政策的引擎，確保所有開發者都遵守相同的規則。

### 使用方式

```python
from enforcement.policy_engine import (
    PolicyEngine, 
    Policy, 
    EnforcementLevel,
    PolicyViolationException
)

# 創建政策引擎
engine = PolicyEngine()

# 定義政策（沒有可選）
engine.add_policy(Policy(
    id="quality-gate",
    description="Quality Gate 必須 >= 90",
    check_fn=lambda: get_quality_score() >= 90,
    enforcement=EnforcementLevel.BLOCK,
    severity="critical"
))

# 執行所有政策
results = engine.enforce_all()

# 如果有阻擋，拋出異常
engine.raise_on_block(results)
```

### 輸出範例

```
✅ commit-has-task-id: 所有 commit 必須有 task_id
✅ quality-gate-90: Quality Gate 分數必須 >= 90
✅ no-bypass-commands: 不允許使用 bypass/skip/--no-verify
```

---

## 案例 53.2：創建嚴格引擎

### 背景
有時需要確保所有政策都是 BLOCK 等級，沒有任何繞過空間。

### 使用方式

```python
from enforcement.policy_engine import create_hard_block_engine

# 工廠函數：創建嚴格的政策引擎
engine = create_hard_block_engine()
results = engine.enforce_all()

summary = engine.get_summary()
print(f"Passed: {summary['passed']}/{summary['total']}")
print(f"Pass Rate: {summary['pass_rate']}%")
print(f"All Passed: {summary['all_passed']}")
```

### 輸出範例

```
✅ commit-has-task-id: 所有 commit 必須有 task_id
✅ quality-gate-90: Quality Gate 分數必須 >= 90
✅ no-bypass-commands: 不允許使用 bypass/skip/--no-verify
✅ test-coverage-80: 測試覆蓋率必須 >= 80%
✅ security-score-95: 安全分數必須 >= 95

📊 Policy Summary:
   Passed: 5/5
   Pass Rate: 100.0%
   All Passed: True
```

---

## 案例 53.3：自定義政策

### 背景
需要添加自定義政策來滿足特定專案需求。

### 使用方式

```python
from enforcement.policy_engine import PolicyEngine, Policy, EnforcementLevel

engine = PolicyEngine()

# 添加自定義政策
engine.add_policy(Policy(
    id="max-file-size",
    description="代碼檔案不能超過 1000 行",
    check_fn=lambda: check_file_lines() <= 1000,
    enforcement=EnforcementLevel.BLOCK,
    severity="high"
))

engine.add_policy(Policy(
    id="no-secrets",
    description="不能包含明文密碼或 API Key",
    check_fn=lambda: not contains_secrets(),
    enforcement=EnforcementLevel.BLOCK,
    severity="critical"
))

# 執行
results = engine.enforce_all()
```

---

## 案例 53.4：政策違規處理

### 背景
當政策被違反時，需要捕獲異常並進行處理。

### 使用方式

```python
from enforcement.policy_engine import (
    PolicyEngine, 
    PolicyViolationException
)

engine = PolicyEngine()

try:
    results = engine.enforce_all()
except PolicyViolationException as e:
    print(f"❌ Policy Violation: {e}")
    # 進行相應處理
    # - 阻止 commit
    # - 發送通知
    # - 記錄審計日誌
```

### 輸出範例

```
❌ PolicyViolationException: Policy violation: 所有 commit 必須有 task_id
Policy ID: commit-has-task-id
Enforcement: block
This is a REQUIRED policy and cannot be bypassed.
```

---

## 預設政策列表

| Policy ID | 描述 | 等級 | 嚴重性 |
|-----------|------|------|--------|
| commit-has-task-id | 所有 commit 必須有 task_id | BLOCK | critical |
| quality-gate-90 | Quality Gate 分數必須 >= 90 | BLOCK | critical |
| no-bypass-commands | 不允許使用 bypass/skip/--no-verify | BLOCK | critical |
| test-coverage-80 | 測試覆蓋率必須 >= 80% | BLOCK | high |
| security-score-95 | 安全分數必須 >= 95 | BLOCK | high |

---

## 相關功能

- [案例 54：Pre-Commit Hook](./case54_pre_commit_hook.md) - Git Hook 自動執行
- [案例 45：Anti-Shortcut](./case45_anti_shortcut.md) - 防範捷徑系統
