# Methodology v2 - 完整使用手冊

> 從 PoC 到 Production-Ready 的 AI Agent 開發框架

---

## 目錄

1. [快速開始](#快速開始)
2. [核心架構](#核心架構)
3. [Solutions A-E 完整指南](#solutions-a-e-完整指南)
4. [統一 CLI](#統一-cli)
5. [完整工作流程](#完整工作流程)
6. [範例](#範例)
7. [API 參考](#api-參考)

---

## 快速開始

### 安裝

```bash
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2
```

### 基本使用

```python
from methodology import MethodologyCore

# 初始化
core = MethodologyCore()

# 使用各模組
core.tasks.split_from_goal("新任務")
core.costs.track(...)
```

---

## 核心架構

```
methodology-v2/
├── core.py                 # 統一入口
├── progress_dashboard.py   # Sprint/Backlog 追蹤
├── cost_allocator.py      # 成本管控
├── message_bus.py         # 訊息系統
├── gantt_chart.py         # 甘特圖
├── pm_mode.py             # PM Mode
├── pm_terminology.py       # 術語對照
├── resource_dashboard.py   # 資源儀表板
│
├── # Solutions A-E
├── agent_evaluator.py     # Solution A: Agent 評估
├── structured_output.py   # Solution B: 結構化輸出
├── data_quality.py        # Solution C: 資料品質
├── enterprise_hub.py       # Solution D: 企業整合
└── langgraph_migrator.py  # Solution E: LangGraph 遷移
```

---

## Solutions A-E 完整指南

### Solution A: Agent Evaluation Framework

**用途**：自動化 Agent 行為評估、A/B 測試

```python
from methodology import AgentEvaluator, TestCase

evaluator = AgentEvaluator()

# 建立測試套件
suite = evaluator.create_suite(
    name="Login Flow",
    iterations=3,
    version_a_name="GPT-4",
    version_b_name="Claude-3"
)

# 加入測試用例
evaluator.add_test_case(
    suite.id,
    name="Valid Login",
    input_prompt="User logs in with correct credentials",
    expected_output="Login successful"
)

# 定義 Agent
def agent_v1(prompt, context=None, timeout=30):
    # 呼叫你的 Agent
    return f"[Agent] Response to: {prompt}"

# 執行評估
evaluator.run_suite(suite.id, agent_v1)

# 產生報告
print(evaluator.generate_report(suite.id))
```

**CLI**：
```bash
python cli.py eval create "Login Tests"
python cli.py eval add <suite_id> "Valid Login" --prompt "User login"
python cli.py eval run <suite_id>
python cli.py eval report <suite_id>
```

---

### Solution B: Structured Output Engine

**用途**：確保 LLM 輸出穩定性、JSON 解析

```python
from methodology import StructuredOutputEngine

engine = StructuredOutputEngine()

# 定義 Schema
from methodology import OutputSchema, FieldDefinition

user_schema = OutputSchema(
    name="user",
    fields={
        "id": FieldDefinition("id", int),
        "name": FieldDefinition("name", str),
        "email": FieldDefinition("email", str),
    },
    required_fields=["id", "email"]
)
engine.register_schema(user_schema)

# 解析 LLM 輸出
def mock_llm(prompt):
    return '{"id": 123, "name": "John", "email": "john@test.com"}'

result = engine.parse(
    prompt="Extract user info",
    llm_call=mock_llm,
    schema_name="user",
    max_retries=3
)

print(f"Success: {result.success}")
print(f"Data: {result.data}")
print(f"Validation: {result.validation.valid if result.validation else None}")
```

**解析策略**：
1. **Direct** - 直接 JSON parse
2. **Regex** - 從 Markdown/code block 提取
3. **Repair** - Key-value 提取
4. **Retry** - 重試 LLM

**CLI**：
```bash
python cli.py parse
```

---

### Solution C: Data Quality Connector

**用途**：資料驗證、異常偵測、品質評分

```python
from methodology import DataQualityChecker

checker = DataQualityChecker()

# 測試資料
data = [
    {"id": 1, "name": "Alice", "email": "alice@test.com", "age": 30},
    {"id": 2, "name": "Bob", "email": "bob@test.com", "age": 25},
    {"id": 3, "name": "", "email": "invalid-email", "age": None},
    {"id": 4, "name": "Diana", "email": "diana@test.com", "age": 150},  # Outlier
]

field_types = {"id": int, "name": str, "email": str, "age": int}

# 分析
report = checker.analyze(data, field_types)

# 產生報告
print(checker.generate_report_markdown(report))

# 清理
cleaned, _ = checker.clean_data(data, strategy="remove")
```

**問題偵測**：
- Missing Value - 缺失值
- Outlier - 異常值 (3σ 外)
- Duplicate - 重複資料
- Invalid Format - 格式錯誤

**CLI**：
```bash
python cli.py quality check
python cli.py quality report
```

---

### Solution D: Enterprise Integration Hub

**用途**：企業單一登入、審計日誌、Slack/Teams 通知

```python
from methodology import EnterpriseHub, SlackMessenger, AuditLevel

hub = EnterpriseHub()

# 設定 Slack
hub.add_slack("alerts", webhook_url="https://hooks.slack.com/...")

# 審計日誌
hub.audit.log_access(
    user_id="user-123",
    username="john.doe",
    resource="/api/tasks",
    method="GET"
)

# 發送警報
hub.alert(
    title="High CPU Usage",
    message="Server CPU at 95%",
    severity="warning"
)

# 認證
user = hub.auth.create_user(
    username="john.doe",
    email="john@company.com",
    role="developer",
    permissions=["read", "write"]
)
api_key = hub.auth.create_api_key(user.id)
```

**支援的認證**：
- Okta (OIDC/SAML)
- Azure AD (OAuth2)
- LDAP
- API Key
- Basic Auth

**CLI**：
```bash
python cli.py enterprise status
python cli.py enterprise audit
```

---

### Solution E: LangGraph Migration Tool

**用途**：將現有 Agent 遷移到 LangGraph

```python
from methodology import LangGraphMigrationTool

tool = LangGraphMigrationTool()

# 分析檔案
result = tool.analyze_file("my_agent.py")

# 產生報告
print(tool.generate_report(result))

# 遷移
result = tool.migrate_file("my_agent.py", "my_agent_langgraph.py")

print(f"Output: {result.output_file}")
print(f"Risk: {result.overall_risk}")
```

**風險評估**：
- 🟢 Low - 可自動遷移
- 🟡 Medium - 需要部分手動調整
- 🔴 High - 需要完整重構

**CLI**：
```bash
python cli.py migrate my_agent.py
```

---

## 統一 CLI

```bash
# 專案管理
python cli.py init "my-project"
python cli.py task add "新功能" --points 5
python cli.py task list
python cli.py sprint create "Sprint 1"

# 視覺化
python cli.py board
python cli.py report --type weekly

# PM Mode
python cli.py pm report
python cli.py pm forecast
python cli.py pm health

# Solutions A-E
python cli.py eval create "Tests"
python cli.py quality check
python cli.py enterprise status
python cli.py migrate my_agent.py
python cli.py parse
python cli.py term velocity
python cli.py resources list
```

---

## 完整工作流程

### 開發流程

```
1. 需求 → Task拆分
   core.tasks.split_from_goal("開發登入功能")
       ↓
2. 規劃 → Sprint排程
   core.sprints.create_sprint(...)
       ↓
3. 執行 → Agent開發
   core.evaluator.run_suite(...)
       ↓
4. 評估 → 品質把關
   core.structured.parse(...)
       ↓
5. 部署 → 企業整合
   core.enterprise.notify(...)
```

### 評估流程

```
1. 定義測試用例
   evaluator.add_test_case(suite.id, "Valid Login", ...)
       ↓
2. 執行評估
   evaluator.run_suite(suite.id, agent_fn)
       ↓
3. 人類審查 (可選)
   hitl.submit_for_review(result)
       ↓
4. 產生報告
   evaluator.generate_report(suite.id)
```

### 資料品質流程

```
1. 收集資料
   data = [...]
       ↓
2. 分析品質
   report = checker.analyze(data)
       ↓
3. 檢視問題
   checker.generate_report_markdown(report)
       ↓
4. 清理資料
   cleaned, _ = checker.clean_data(data)
```

---

## 範例

### 完整專案開發

```python
from methodology import MethodologyCore

core = MethodologyCore(config={
    "project_name": "AI Assistant",
    "monthly_budget": 1000
})

# 1. 規劃
core.tasks.split_from_goal("開發 AI 助手")

# 2. 建立 Sprint
core.sprints.create_sprint(
    name="Sprint 1",
    capacity=40
)

# 3. Agent 評估
def my_agent(prompt, context=None, timeout=30):
    # Agent 實作
    return "Agent response"

test_cases = [
    {"name": "問答", "prompt": "什麼是 AI?", "expected": "AI 是..."},
    {"name": "翻譯", "prompt": "翻譯 hello 為中文", "expected": "你好"},
]

report = core.run_full_evaluation(my_agent, test_cases)

# 4. 資料驗證
data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": ""}]
quality_report = core.check_data_quality(data)

# 5. 部署通知
core.enterprise.alert("Deployment Complete", "Sprint 1 done", "info")
```

### 企業級整合

```python
from methodology import EnterpriseHub

hub = EnterpriseHub()

# 設定認證
hub.auth.configure_okta(
    domain="company.okta.com",
    client_id="xxx",
    client_secret="yyy"
)

# 設定 Slack
hub.add_slack("deployments", webhook_url="https://hooks.slack.com/...")

# 設定 Teams
hub.add_teams("alerts", webhook_url="https://company.webhook.teams...")

# 審計
hub.audit.log_access(user_id, username, "/api/deploy", "POST")
hub.audit.log_auth(user_id, username, "success")

# 部署時通知
hub.alert("Deployment", "v1.2.0 deployed to production", "info")
```

---

## API 參考

### MethodologyCore

| 屬性 | 模組 | 用途 |
|------|------|------|
| `core.tasks` | TaskSplitter | 任務拆分 |
| `core.sprints` | SprintPlanner | Sprint 管理 |
| `core.costs` | CostAllocator | 成本追蹤 |
| `core.bus` | MessageBus | 訊息系統 |
| `core.evaluator` | AgentEvaluator | Agent 評估 |
| `core.structured_output` | StructuredOutputEngine | 輸出解析 |
| `core.data_quality` | DataQualityChecker | 資料品質 |
| `core.enterprise` | EnterpriseHub | 企業整合 |
| `core.migrator` | LangGraphMigrationTool | 框架遷移 |

### AgentEvaluator

| 方法 | 說明 |
|------|------|
| `create_suite(name)` | 建立測試套件 |
| `add_test_case(suite_id, name, input_prompt, expected)` | 加入測試 |
| `run_suite(suite_id, agent_fn)` | 執行評估 |
| `generate_report(suite_id)` | 產生報告 |
| `compare_versions(suite_id)` | 比較 A/B |

### StructuredOutputEngine

| 方法 | 說明 |
|------|------|
| `parse(prompt, llm_call, schema_name)` | 解析輸出 |
| `register_schema(schema)` | 註冊 Schema |
| `generate_report()` | 穩定性報告 |

### DataQualityChecker

| 方法 | 說明 |
|------|------|
| `analyze(data, field_types)` | 分析品質 |
| `clean_data(data, strategy)` | 清理資料 |
| `generate_report_markdown(report)` | 產生報告 |

### EnterpriseHub

| 屬性 | 說明 |
|------|------|
| `auth` | 認證管理器 |
| `audit` | 審計日誌 |
| `messengers` | 訊息系統 |

### LangGraphMigrationTool

| 方法 | 說明 |
|------|------|
| `analyze_file(path)` | 分析檔案 |
| `migrate_file(path, output)` | 遷移檔案 |
| `generate_report(result)` | 產生報告 |

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.3.0 | 2026-03-20 | Solutions A-E 發布 |
| v5.2.0 | 2026-03-20 | Agent Evaluation |
| v5.1.0 | 2026-03-20 | 單元測試 + 文件 |
| v5.0.0 | 2026-03-20 | PM Mode + Real Data |
| v4.9.0 | 2026-03-20 | PM Terminology + Resources |
| v4.7.0 | 2026-03-20 | P1 Visualizations |

---

## 許可

MIT License
