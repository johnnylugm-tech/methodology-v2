# Anti-Shortcut Framework 完整手冊

> 防止 AI Agent 走捷徑、確保工作流程嚴謹性

---

## 1️⃣ 概述

### 為什麼需要 Anti-Shortcut Framework？

```
傳統工作流程：
     ↓
人類有判斷力，會質疑「這樣做對嗎？」
     ↓
AI Agent 會為了速度而走捷徑
     ↓
品質下降、風險增加
```

**Anti-Shortcut Framework 的目標**：
- 讓正確的做法變得簡單
- 讓走捷徑變得困難或不可能

---

## 2️⃣ 六大模組

### 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                    Anti-Shortcut Framework                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Blacklist │    │ Gatekeeper │    │Enforcer    │    │
│  │  (B)       │    │  (A)       │    │  (F)       │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │Audit Logger│    │Double Conf │    │Phase Hooks │    │
│  │  (C)       │    │  (D)       │    │  (E)       │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 模組職責

| 模組 | 縮寫 | 職責 |
|------|------|------|
| **Blacklist** | B | 阻止危險操作 |
| **Gatekeeper** | A | 確保流程完整 |
| **Enforcer** | F | 防範捷徑 |
| **Audit Logger** | C | 記錄和審計 |
| **Double Confirmation** | D | 減少失誤 |
| **Phase Hooks** | E | 自動化驗證 |

---

## 3️⃣ 快速開始

### 第一步：啟用 Anti-Shortcut Framework

```bash
# 查看當前狀態
python3 cli.py gatekeeper status

# 檢查是否有危險命令
python3 cli.py audit status
```

### 第二步：理解風險操作

```bash
# 查看被阻止的命令
python3 cli.py blacklist --list
```

### 第三步：執行工作流程

```bash
# 1. 確保 Constitution 被執行
python3 cli.py constitution check

# 2. 開始任務（必須有 task_id）
git commit -m "[TASK-123] Add new feature"

# 3. 通過 Quality Gate
python3 cli.py quality gate

# 4. 請求審批
python3 cli.py approval create --type release
```

---

## 4️⃣ 詳細模組

### 4.1 Blacklist (B)

**職責**：阻止危險操作

| 被阻止的命令 | 嚴重性 |
|------------|--------|
| `guardrails --bypass` | 🔴 直接阻止 |
| `quality --skip` | 🔴 直接阻止 |
| `eval --modify` | 🔴 直接阻止 |
| `approval --self-approve` | 🔴 直接阻止 |
| `merge --no-review` | 🔴 直接阻止 |
| `git push --force` | 🟡 需要審批 |
| `constitution --bypass` | 🔴 直接阻止 |

**使用方式**：

```python
from anti_shortcut.blacklist import CommandBlacklist

blacklist = CommandBlacklist()
result = blacklist.check("guardrails --bypass")

if result:
    print("⚠️ 此命令被阻止")
    print(blacklist.explain(result))
```

### 4.2 Gatekeeper (A)

**職責**：確保每個階段都有强制檢查點

```
階段流程：
Constitution → Specify → Plan → Tasks → Verification → Release
    ↓           ↓        ↓      ↓         ↓          ↓
   Gate 1      Gate 2   Gate 3  Gate 4    Gate 5     Gate 6
```

**使用方式**：

```python
from anti_shortcut.gatekeeper import Gatekeeper, Phase

keeper = Gatekeeper()

# 開始 Constitution 階段
keeper.start_phase(Phase.CONSTITUTION)

# 檢查 Gate
keeper.check_gate("con-1")

# 查看狀態
status = keeper.get_status_report()
print(status)
```

### 4.3 Enforcer (F)

**職責**：防止走捷徑

| 捷徑 | 防範機制 |
|------|----------|
| Commit 沒有 task_id | ❌ 被阻止 |
| Task 沒有測試 | ⚠️ 警告 |
| 自己批准自己 | ❌ 被阻止 |
| 跳過 Quality Gate | ❌ 被阻止 |

**使用方式**：

```python
from anti_shortcut.enforcer import AntiShortcutEnforcer

enforcer = AntiShortcutEnforcer()

# 檢查 commit message
violations = enforcer.check_commit_message("[TASK-123] Add feature", "abc123")

# 檢查是否自己批准自己
if enforcer.check_self_approval(approver="agent-1", operator="agent-1"):
    print("⚠️ 自己批准自己被阻止")
```

### 4.4 Audit Logger (C)

**職責**：記錄所有 AI 操作

**使用方式**：

```python
from anti_shortcut.audit_logger import AIAuditLogger, ActionType

logger = AIAuditLogger()

# 記錄操作
logger.log_cli("agent-1", "git commit -m '...'")
logger.log_file_change("agent-1", "file_create", "src/main.py")

# 取得異常
anomalies = logger.get_anomalies(severity="critical")

# 生成報告
report = logger.get_audit_report("agent-1")
```

### 4.5 Double Confirmation (D)

**職責**：關鍵操作需要雙重確認

| 操作 | 確認等級 |
|------|----------|
| 發布 Release | DOUBLE (2人) |
| 修改 Constitution | APPROVAL |
| 刪除檔案 | DOUBLE |
| 繞過 Quality Gate | APPROVAL |

**使用方式**：

```python
from anti_shortcut.double_confirm import DoubleConfirmation

confirmer = DoubleConfirmation()

# 創建待確認
conf_id = confirmer.create_pending("release", "發布 v1.0.0")

if conf_id:
    print(f"等待確認: {conf_id}")
    # 等待人類確認...

# 確認
confirmer.confirm(conf_id, "human-reviewer")
```

### 4.6 Phase Hooks (E)

**職責**：每個階段結束自動觸發驗證

```
┌─────────────────────────────────────┐
│         Development Phase              │
│                                       │
│  lint → test → constitution_check    │
│    ↓      ↓            ↓            │
│   [    全部通過才能繼續    ]         │
└─────────────────────────────────────┘
```

**使用方式**：

```python
from anti_shortcut.phase_hooks import PhaseHooks, Phase

hooks = PhaseHooks()

# 執行 development 階段的鉤子
result = hooks.execute_phase(Phase.DEVELOPMENT)

# 檢查是否可以繼續
can_proceed, reason = hooks.can_proceed(
    Phase.DEVELOPMENT, 
    Phase.VERIFICATION
)

if not can_proceed:
    print(f"無法繼續: {reason}")
```

---

## 5️⃣ 整合使用

### 完整工作流程

```bash
#!/bin/bash

# 1. 開始任務前：檢查 Constitution
python3 cli.py constitution check || exit 1

# 2. 創建任務
python3 cli.py task create --id TASK-001 --name "新功能"

# 3. 開發（使用 enforcer）
git commit -m "[TASK-001] Add new feature" || {
    echo "❌ Commit message 必須包含 task_id"
    exit 1
}

# 4. 執行測試（使用 phase hooks）
python3 cli.py phase execute development || exit 1

# 5. Quality Gate（使用 blacklist + gatekeeper）
python3 cli.py quality gate || exit 1

# 6. 請求審批（使用 double confirmation）
python3 cli.py approval create --type release --confirm || exit 1

# 7. 發布
python3 cli.py release --execute
```

---

## 6️⃣ CLI 命令速查

| 模組 | 命令 | 說明 |
|------|------|------|
| **Blacklist** | `cli.py blacklist --check <cmd>` | 檢查命令 |
| **Gatekeeper** | `cli.py gatekeeper status` | 查看狀態 |
| **Gatekeeper** | `cli.py gatekeeper check` | 檢查 Gates |
| **Enforcer** | `cli.py enforcer commit-msg <msg>` | 檢查 Commit |
| **Audit** | `cli.py audit status` | 查看審計 |
| **Audit** | `cli.py audit anomalies` | 查看異常 |
| **Confirm** | `cli.py confirmations list` | 查看待確認 |
| **Confirm** | `cli.py confirmations confirm <id>` | 確認操作 |
| **Phase** | `cli.py phase execute <phase>` | 執行階段鉤子 |

---

## 7️⃣ 常見問題

**Q: 如何允許特殊情況下繞過限制？**

A: 所有繞過都需要明確的審批和理由：
```bash
# 需要人類審批才能繞過
python3 cli.py approval create --type bypass --reason "緊急修復"
```

**Q: 如果不小心阻擋了正常操作？**

A: 使用 `skip_hook` 並記錄理由：
```python
hooks.skip_hook("dev-lint", "第三方庫，無法修改")
```

**Q: 如何監控團隊的合規情況？**

A: 使用 Audit Logger：
```bash
python3 cli.py audit report --format markdown
```

---

## 8️⃣ 相關資源

- [案例 43: Blacklist](cases/case43_blacklist.md)
- [案例 44: Gatekeeper](cases/case44_gatekeeper.md)
- [案例 45: Anti-Shortcut](cases/case45_anti_shortcut.md)
- [案例 46: Audit Logger](cases/case46_audit_logger.md)
- [案例 47: Double Confirm](cases/case47_double_confirm.md)
- [案例 48: Phase Hooks](cases/case48_phase_hooks.md)

---

*最後更新：2026-03-23*