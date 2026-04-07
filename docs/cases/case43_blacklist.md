# 案例 43：危險操作黑名單 (Blacklisted Commands)

## 情境描述

當 AI Agent 執行操作時，可能會嘗試執行危險操作，例如停用安全檢查、跳過品質審核、自己批准自己的操作等。黑名單機制用於阻止這些危險操作。

---

## 案例 43.1：基本黑名單檢查

### 背景
在執行任何命令前，先檢查是否在黑名單中。

### 使用方式

```python
from anti_shortcut.blacklist import CommandBlacklist, ViolationSeverity

# 初始化黑名單檢查器
blacklist = CommandBlacklist()

# 檢查命令
dangerous_cmd = "guardrails --bypass"
result = blacklist.check(dangerous_cmd)

if result:
    print(f"⚠️ 危險命令被阻止: {result.description}")
    print(f"替代方案: {result.alternative}")
else:
    print("✅ 命令安全")
```

### 輸出
```
⚠️ 危險命令被阻止: 停用安全檢查是非常危險的
替代方案: 使用 'guardrails --audit' 查看問題
```

---

## 案例 43.2：強制推送需要審批

### 背景
`git push --force` 是危險操作，但有時需要。此時標記為需要審批。

### 使用方式

```python
from anti_shortcut.blacklist import CommandBlacklist

blacklist = CommandBlacklist()

# 檢查 git force push
result = blacklist.check("git push --force origin main")

if result:
    print(f"嚴重程度: {result.severity.value}")
    if result.requires_approver:
        print("🚨 此操作需要額外審批!")
        print(f"替代方案: {result.alternative}")
```

### 輸出
```
嚴重程度: approval_required
🚨 此操作需要額外審批!
替代方案: 使用 'git push --force-with-lease'
```

---

## 案例 43.3：違規報告

### 背景
追蹤一段時間內的所有違規操作。

### 使用方式

```python
from anti_shortcut.blacklist import CommandBlacklist

blacklist = CommandBlacklist()

# 模擬多次檢查
commands = [
    "guardrails --bypass",
    "quality --skip",
    "eval --modify",
    "git push --force",
    "rm -rf /tmp/*",
]

for cmd in commands:
    result = blacklist.check(cmd)
    if result:
        print(f"阻止: {cmd}")

# 取得報告
report = blacklist.get_violation_report()
print(f"\n報告:")
print(f"- 總違規: {report['total']}")
print(f"- 直接阻止: {report['blocked']}")
print(f"- 需要審批: {report['approval_required']}")
```

### 輸出
```
阻止: guardrails --bypass
阻止: quality --skip
阻止: eval --modify
阻止: git push --force
阻止: rm -rf /tmp/*

報告:
- 總違規: 5
- 直接阻止: 4
- 需要審批: 1
```

---

## 案例 43.4：整合進 CLI

### 背景
將黑名單檢查整合進命令列介面，在執行前先檢查。

### 使用方式

```python
from anti_shortcut.blacklist import CommandBlacklist

_blacklist = CommandBlacklist()

def execute_command(command: str) -> bool:
    """檢查並執行命令"""
    blocked = _blacklist.check(command)
    if blocked:
        print(_blacklist.explain(blocked))
        return False
    # 執行命令...
    return True

# 使用
success = execute_command("guardrails --bypass")
print(f"執行結果: {success}")
```

---

## 黑名單項目說明

| 命令模式 | 嚴重程度 | 說明 | 替代方案 |
|---------|---------|------|---------|
| `guardrails --bypass` | 🚫 直接阻止 | 停用安全檢查 | `guardrails --audit` |
| `quality --skip` | 🚫 直接阻止 | 跳過品質檢查 | `quality --fix` |
| `eval --modify` | 🚫 直接阻止 | 測試後修改測試 | 先修復問題再測試 |
| `approval --self-approve` | 🚫 直接阻止 | 自己批准自己 | 請求他人批准 |
| `merge --no-review` | 🚫 直接阻止 | 不經審查合併 | 標準合併流程 |
| `git push --force` | ⚠️ 需要審批 | 強制推送覆寫歷史 | `git push --force-with-lease` |
| `rm -rf /*` | 🚫 直接阻止 | 危險刪除 | 使用 `trash` |
| `constitution --bypass` | 🚫 直接阻止 | 繞過 Constitution | `constitution edit` |

---

## 最佳實踐

1. **在執行前檢查**：所有命令執行前都應該通過黑名單檢查
2. **記錄違規**：追蹤所有違規操作，便於審計
3. **提供替代方案**：阻止危險操作的同時，提供安全的替代方案
4. **分級處理**：
   - `BLOCKED`：直接阻止
   - `WARN`：警告後允許
   - `APPROVAL_REQUIRED`：需要額外審批

---

## 整合架構

```
┌─────────────┐
│  Command    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Blacklist   │ ◄───── Pattern Match
│ Checker     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Severity   │
│  Decision   │
└──────┬──────┘
       │
       ├──────► BLOCKED ──────► 阻止執行
       │
       ├──────► WARN ─────────► 顯示警告後執行
       │
       └──────► APPROVAL ─────► 請求審批後執行
```
