# Case 45: Anti-Shortcut Enforcer

## 問題背景

在多人協作的 Agent 系統中，走捷徑是一個常見的效率誘惑：

- 工程師直接 commit 不附 task_id
- 沒有對應 test 就標示完成
- 自己批准自己的變更
- 跳過 quality gate 直接上線

這些捷徑在短期內節省時間，但長期累積技術債，導致系統可靠性下降。

---

## 解決方案：Anti-Shortcut Enforcer

### 核心設計原則

```
捷徑防範規則：
1. 每個 commit 必須有 task_id
2. 每個 task 必須有對應的 test
3. 錯誤必須被分類和確認
4. 批准者 != 操作者
```

### 模組架構

```
anti_shortcut/
├── __init__.py
├── enforcer.py          # 核心 enforcer
├── blacklist.py         # 危險命令黑名單
└── git-hooks/
    └── commit-msg       # Git hook for task_id validation
```

### 違規類型定義

| 類型 | 說明 | 嚴重性 |
|------|------|--------|
| `COMMIT_WITHOUT_TASK` | Commit 沒有附 task_id | critical |
| `TASK_WITHOUT_TEST` | Task 沒有對應測試 | critical |
| `ERROR_NOT_ACKNOWLEDGED` | 錯誤未被確認 | warning |
| `SELF_APPROVAL` | 自己批准自己 | critical |
| `SKIP_GATE` | 跳過 quality gate | critical |
| `BYPASS_SECURITY` | 繞過安全檢查 | critical |

---

## 使用範例

### 1. Commit 驗證

```python
from anti_shortcut import AntiShortcutEnforcer

enforcer = AntiShortcutEnforcer()

# 檢查 commit message
violations = enforcer.check_commit_message(
    commit_message="[TASK-123] Add user authentication",
    commit_id="abc123"
)

if violations:
    for v in violations:
        print(f"Violation: {v.type.value} - {v.description}")
else:
    print("Commit validated successfully")
```

**輸出：**
```
Commit validated successfully
```

### 2. Task 測試覆蓋率追蹤

```python
# 註冊 task
enforcer.register_task("TASK-123", task_type="development")

# 註冊對應測試
enforcer.register_test("TASK-123", "test_auth_flow")

# 檢查是否有測試
if enforcer.check_task_has_test("TASK-123"):
    print("Task has test coverage")
else:
    print("WARNING: Task lacks test coverage!")
```

### 3. 防止自己批准自己

```python
# 嘗試自己批准自己的變更
is_self_approval = enforcer.check_self_approval(
    approver_id="agent-001",
    operator_id="agent-001"
)

if is_self_approval:
    print("SELF-APPROVAL BLOCKED!")
    # 必須由另一個 agent 批准
```

### 4. 違規確認（需要人工）

```python
# 取得未確認的違規
unack = enforcer.get_unacknowledged_violations()

for v in unack:
    print(f"[{v.violation_id}] {v.type.value}: {v.description}")

# 人工確認違規
enforcer.acknowledge_violation(
    violation_id="vio-0",
    acknowledged_by="human-supervisor"
)
```

### 5. 違規摘要報告

```python
summary = enforcer.get_violation_summary()
print(f"""
=== Violation Summary ===
Total: {summary['total']}
Unacknowledged: {summary['unacknowledged']}
Critical (unacked): {summary['critical_unacknowledged']}
By type: {summary['by_type']}
""")

coverage = enforcer.get_task_coverage()
print(f"""
=== Task Coverage ===
Total tasks: {coverage['total_tasks']}
With tests: {coverage['tasks_with_tests']}
Coverage: {coverage['coverage']}
""")
```

---

## Git Hook 整合

### 安裝

```bash
cd /path/to/repo
ln -s /path/to/methodology-v2/anti_shortcut/git-hooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

### 驗證行為

**有效 commit：**
```bash
$ git commit -m "[TASK-123] Add user authentication"
# ✓ 通过
```

**無效 commit：**
```bash
$ git commit -m "Add user authentication"
# ✗ ANTI-SHORTCUT VIOLATION DETECTED
#   Commit message MUST contain a task_id
```

---

## 設計理念

### 為什麼要防止捷徑？

1. **可追溯性**：沒有 task_id 的 commit 無法追溯其目的
2. **品質保證**：沒有測試的 task 無法保證功能正確性
3. **責任分離**：自己批准自己違反基本的内部控制原則
4. **累積技術債**：每個捷徑都是未來的坑

### 為什麼不是完全阻擋？

系統設計允許「有管理的繞過」：

- 可以用 `git commit --no-verify` 繞過（需要紀錄）
- 違規可以被確認（acknowledged）而非消除
- 區分 critical 和 warning 等級

關鍵是：**捷徑必須是可見的、有記錄的，而不是默默發生的。**

---

## 與現有系統的整合

### 與 Approval Flow 整合

```python
# 在審批前檢查
approval = enforcer.check_self_approval(
    approver_id=approval_request.approver_id,
    operator_id=approval_request.operator_id
)

if approval:
    # 自動拒絕或標記為需要額外確認
    raise ApprovalError("Self-approval not allowed")
```

### 與 Quality Gate 整合

```python
# 在 quality gate 中檢查 task coverage
coverage = enforcer.get_task_coverage()

if coverage['coverage'] < TARGET_COVERAGE:
    quality_gate.fail(
        reason=f"Task coverage {coverage['coverage']} below target"
    )
```

---

## 總結

Anti-Shortcut Enforcer 不是要讓工作變慢，而是要讓捷徑**可見**。

```
沒有追蹤的捷徑 = 累積的技術債
有追蹤的捷徑 = 有意識的風險承擔
```

系統會記住每一次繞過，幫助團隊在事後檢討是否有更好的做法。
