# Case 56: Constitution as Code - 規範即代碼

## 問題

**「框架是文件，違反了也沒人管」**

現有 Constitution 的問題：
- 寫在文件裡：「建議 commit message 包含 task_id」
- 但沒有強制力，開發者可以忽略
- 違反了也不會阻擋，只會「建議改進」

## 解決方案：Constitution as Code

核心概念：
- **不是建議，是規則**
- **違反就阻擋，不是警告**
- **規則是代碼，可以執行和測試**

### 對比

```
❌ 傳統方式（Document）：
   "建議 commit message 包含 task_id，格式：[TASK-123]"
   
✅ Constitution as Code：
   commit message 沒有 task_id → 直接阻擋
```

### 預設規則

| 規則 ID | 描述 | 嚴重性 |
|---------|------|--------|
| R001 | Commit 必須有 task_id | CRITICAL |
| R002 | 不允許 bypass/skip/--no-verify | CRITICAL |
| R003 | Quality Gate 分數 >= 90 | CRITICAL |
| R004 | 測試覆蓋率 >= 80% | HIGH |
| R005 | 安全分數 >= 95 | HIGH |
| R006 | 不允許自己批准自己 | CRITICAL |
| R007 | 新功能必須有測試 | HIGH |

### 使用範例

```python
from enforcement import ConstitutionAsCode, ConstitutionViolation

constitution = ConstitutionAsCode()

# 檢查 commit message
violations = constitution.check_commit_message("[DEV-456] Add feature")

if violations:
    for v in violations:
        print(f"❌ {v.error_message}")
    raise ConstitutionViolation("Commit message 不符合規範")

# 通用檢查
try:
    constitution.enforce({
        "commit_message": "[DEV-456] Add feature",
        "quality_score": 95,
        "coverage": 85,
        "security_score": 98,
    })
    print("✅ 所有檢查通過")
except ConstitutionViolation as e:
    print(f"❌ Critical 違規: {e}")
    sys.exit(1)
except ConstitutionWarning as e:
    print(f"⚠️ High 警告: {e}")
```

### 自定義規則

```python
from enforcement import ConstitutionAsCode, Rule, RuleSeverity
import re

constitution = ConstitutionAsCode()

# 添加自定義規則
constitution.add_rule(Rule(
    id="R101",
    description="PR 描述必須 >= 20 字",
    check_fn=lambda desc: len(desc or "") >= 20,
    severity=RuleSeverity.MEDIUM,
    error_message="PR 描述太短，必須 >= 20 字"
))

# 添加特定業務規則
constitution.add_rule(Rule(
    id="R102", 
    description="資料庫 Migration 必須有 rollback plan",
    check_fn=lambda ctx: ctx.get("has_rollback", False),
    severity=RuleSeverity.HIGH,
    error_message="資料庫變更沒有 rollback plan"
))
```

### 與 Execution Registry 整合

```python
from enforcement import (
    ExecutionRegistry,
    ConstitutionAsCode,
    ConstitutionViolation
)

registry = ExecutionRegistry()
constitution = ConstitutionAsCode()

def deploy_with_compliance(version: str):
    """帶合規檢查的部署流程"""
    
    # 1. 執行 Security Scan
    scan_result = run_security_scan()
    
    # 2. 記錄到 Registry
    registry.record(
        step="security-scan",
        artifact=scan_result
    )
    
    # 3. Constitution 檢查
    try:
        constitution.enforce({
            "security_score": scan_result["score"],
            "command": "deploy"  # 檢查是否有 bypass
        })
    except ConstitutionViolation:
        print("🚫 部署被阻擋：安全分數不合規")
        raise
    
    # 4. 執行部署
    execute_deploy(version)
    
    # 5. 記錄部署
    registry.record(
        step="deployment",
        artifact={"version": version, "status": "success"}
    )
```

### 規則嚴重性

| 等級 | 行為 | 異常類型 |
|------|------|----------|
| CRITICAL | 立即阻擋 | ConstitutionViolation |
| HIGH | 警告並阻擋 | ConstitutionWarning |
| MEDIUM | 警告 | (無異常，僅警告) |
| LOW | 僅記錄 | (無異常，僅記錄) |

### 規則摘要

```python
summary = constitution.get_rules_summary()
# {
#     "total": 7,
#     "enabled": 7,
#     "by_severity": {
#         "critical": 4,
#         "high": 3,
#         "medium": 0,
#         "low": 0
#     }
# }
```

## 與 Policy Engine 的區別

| 特性 | Policy Engine | Constitution as Code |
|------|---------------|---------------------|
| 焦點 | 流程/資源政策 | 業務規則/合規 |
| 觸發時機 | 操作時 | 操作後/提交時 |
| 檢查方式 | 結構化評估 | 簡單條件判斷 |
| 典型用途 | 配額、權限審批 | Commit 規範、質量門檻 |

## 何時使用

**Constitution as Code 適用場景：**
- ✅ Commit message 規範
- ✅ Code review 審批鏈
- ✅ Quality Gate 門檻
- ✅ Security 最低分數
- ✅ TDD 測試要求

**Policy Engine 適用場景：**
- ✅ Rate limiting
- ✅ 資源配額
- ✅ 多步驟審批流程
- ✅ 條件化權限

---

**核心原則**：把「應該做的事」變成「不做就會失敗的事」。
