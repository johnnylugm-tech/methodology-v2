# 案例二：軟體開發團隊

## 情境描述

開發團隊需要快速建立 Multi-Agent 開發環境，自動選擇合適模型、管理任務流程、確保程式碼品質。

---

## 案例 2.1：建立開發環境

### 背景
新專案啟動，需要快速建立包含 Developer、Reviewer、Tester 的開發團隊。

### 使用方式

```python
from methodology import MethodologyCore, AgentType, AgentTeam

core = MethodologyCore()

# 建立 Agent 團隊
team = AgentTeam(name="AI-客服開發團隊")

# 定義 Developer Agent
dev_def = AgentDefinition(
    name="Backend Developer",
    role=AgentRole.DEVELOPER,
    capabilities=[
        AgentCapability.CODING,
        AgentCapability.API_DESIGN,
        AgentCapability.DATABASE,
    ],
    permissions=[
        AgentPermission.READ_CODE,
        AgentPermission.WRITE_CODE,
        AgentPermission.EXECUTE_TESTS,
    ]
)

# 定義 Reviewer Agent
reviewer_def = AgentDefinition(
    name="Code Reviewer",
    role=AgentRole.REVIEWER,
    capabilities=[
        AgentCapability.CODE_REVIEW,
        AgentCapability.SECURITY,
        AgentCapability.PERFORMANCE,
    ],
    permissions=[
        AgentPermission.READ_CODE,
        AgentPermission.COMMENT,
    ]
)

# 註冊 Agents
team.register(dev_def)
team.register(reviewer_def)

# 查詢可用 Agent
available = team.get_available_agents(role=AgentRole.DEVELOPER)
print(f"可用 Developer: {len(available)}")
```

### 輸出範例
```
可用 Developer: 1
```

---

## 案例 2.2：智慧模型選擇

### 背景
不同任務需要不同能力的模型，需要自動選擇性價比最高的模型。

### 使用方式

```python
from methodology import SmartRouter, TaskType, BudgetLevel

router = SmartRouter()

# 任務 1：複雜的系統設計 → 需要高品質
result1 = router.route(
    "設計一個高並發的分散式系統架構",
    task_type=TaskType.CODING,
    budget=BudgetLevel.HIGH
)
print(f"系統設計 → {result1.model} (${result1.estimated_cost:.4f})")

# 任務 2：簡單的文案生成 → 低成本
result2 = router.route(
    "生成錯誤訊息文字",
    task_type=TaskType.WRITING,
    budget=BudgetLevel.LOW
)
print(f"文案生成 → {result2.model} (${result2.estimated_cost:.4f})")

# 任務 3：中難度的程式碼審查
result3 = router.route(
    "審查這段登入邏輯",
    task_type=TaskType.REVIEW,
    budget=BudgetLevel.MEDIUM
)
print(f"程式碼審查 → {result3.model} (${result3.estimated_cost:.4f})")

# 比較成本
print(f"\n成本節省: {(1 - result2.estimated_cost/result1.estimated_cost)*100:.0f}%")
```

### 輸出範例
```
系統設計 → gpt-4o ($0.0450)
文案生成 → gpt-3.5-turbo ($0.0010)
程式碼審查 → claude-3-sonnet ($0.0080)

成本節省: 98%
```

---

## 案例 2.3：自動品質把關

### 背景
程式碼提交前需要自動掃描問題並修復。

### 使用方式

```python
from methodology import AutoQualityGate

gate = AutoQualityGate()

# 掃描程式碼
code = """
import sqlite3

def get_user(uid):
    query = "SELECT * FROM users WHERE id=" + uid
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchone()
"""

report = gate.scan(code)

print(f"品質分數: {report.score}/100")
print(f"問題數量: {len(report.issues)}")

# 顯示問題
for issue in report.issues[:3]:
    print(f"\n[{issue.severity}] {issue.rule_id}")
    print(f"  {issue.message}")
    print(f"  Line {issue.line}: {issue.code}")

# 自動修復
if report.score < 80:
    fixed = gate.fix(report)
    print(f"\n修復結果: {fixed['success']}/{fixed['total']} 已修復")
```

### 輸出範例
```
品質分數: 45/100
問題數量: 4

[HIGH] SQL Injection
  發現 SQL 注入漏洞
  Line 4: query = "SELECT * FROM users WHERE id=" + uid

[HIGH] String Concatenation
  使用字串拼接構建 SQL

[MEDIUM] No Input Validation
  缺少輸入驗證

[LOW] Resource Leak
  資料庫連接未關閉

修復結果: 3/4 已修復
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| Agent 團隊 | `AgentTeam`, `AgentDefinition` |
| 智慧路由 | `SmartRouter` |
| 品質把關 | `AutoQualityGate` |
| 程式碼審查 | `SecurityAuditor` |
