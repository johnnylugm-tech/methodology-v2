# 案例 54：Git Pre-Commit Hook - 自動化強制執行

## 情境描述

**問題：** Policy Engine 存在，但開發者可能不會自願執行。

**解決方案：** Git Pre-Commit Hook - 每次 `git commit` 都會自動觸發，無法繞過。

---

## 案例 54.1：安裝 Pre-Commit Hook

### 背景
需要將 pre-commit hook 安裝到專案中，自動化執行所有政策檢查。

### 安裝方式

```bash
# 方法一：使用 CLI 安裝
python cli.py install-hook

# 方法二：手動安裝
cd /path/to/methodology-v2
cp pre-commit.template ../.git/hooks/pre-commit
chmod +x ../.git/hooks/pre-commit
```

### 輸出範例

```
✅ Pre-commit hook installed at /path/to/.git/hooks/pre-commit
```

---

## 案例 54.2：使用 CLI 命令

### 背景
使用 CLI 來管理 policy 和 hook。

### 安裝 Hook

```bash
python cli.py install-hook
```

### 執行 Policy Check

```bash
python cli.py policy
```

### 輸出範例

```
🔍 methodology-v2 Pre-Commit Hook
==================================

📝 Checking commit message format...
✅ Commit message has task ID

⚙️ Running Policy Engine...
✅ commit-has-task-id: 所有 commit 必須有 task_id
✅ quality-gate-90: Quality Gate 分數必須 >= 90
✅ no-bypass-commands: 不允許使用 bypass/skip/--no-verify
✅ test-coverage-80: 測試覆蓋率必須 >= 80%
✅ security-score-95: 安全分數必須 >= 95
Passed: 5/5

✅ All pre-commit checks passed

Proceeding with commit...
```

---

## 案例 54.3：Hook 攔截場景

### 場景 1：沒有 Task ID 的 Commit

```bash
$ git commit -m "fix bug"
```

### 輸出

```
🔍 methodology-v2 Pre-Commit Hook
==================================

📝 Checking commit message format...
❌ Commit message MUST contain task ID (e.g., [TASK-123])
   Your commit message: fix bug
exit 1
```

### 正確格式

```bash
$ git commit -m "[TASK-123] fix user authentication bug"
```

---

### 場景 2：嘗試使用 --no-verify

```bash
$ git commit --no-verify -m "[TASK-124] bypass checks"
```

### 輸出

```
⚙️ Running Policy Engine...
❌ Policy Engine check failed
   Some required policies did not pass
exit 1
```

---

## 案例 54.4：手動執行 Policy Check

### 背景
在 commit 之前，手動檢查所有政策是否通過。

### 使用方式

```bash
python cli.py policy
```

### 輸出範例

```
📊 Policy Summary:
   Passed: 5/5
   Pass Rate: 100.0%

✅ All policies passed
```

---

## Hook 流程圖

```
git commit
    │
    ▼
┌─────────────────┐
│  Read commit msg│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Check task ID   │──── No ────▶ Exit 1 (Blocked)
│ [TASK-XXX]      │
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│ Run Policy      │
│ Engine          │
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ All    │──── No ────▶ Exit 1 (Blocked)
    │ Passed?│
    └────────┘
         │ Yes
         ▼
┌─────────────────┐
│ Proceed with   │
│ commit         │
└─────────────────┘
```

---

## 相關功能

- [案例 53：Policy Engine](./case53_policy_engine.md) - 政策引擎
- [案例 45：Anti-Shortcut](./case45_anti_shortcut.md) - 防範捷徑系統
- [案例 47：Double Confirm](./case47_double_confirm.md) - 雙重確認機制
