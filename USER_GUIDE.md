# Methodology v2 - 完整使用手冊

> 企業級 AI Agent 開發框架 - 從 PoC 到 Production-Ready

---

## 目錄

1. [完整工作流程](#完整工作流程)
2. [快速開始](#快速開始)
3. [模組使用指南](#模組使用指南)
4. [Solutions A-E](#solutions-a-e)
5. [CLI 參考](#cli-參考)
6. [範例](#範例)

---

## 完整工作流程

### 6 大核心流程

```
1️⃣  專案初始化 → Setup Wizard
         │
2️⃣  開發執行 → Task → Sprint → Agent → Guardrails → AutoScaler
         │
3️⃣  評估測試 → AgentEvaluator → HITL
         │
4️⃣  資料處理 → Guardrails → StructuredOutput → DataQuality
         │
5️⃣  企業整合 → SSO → RBAC → Audit → Notification
         │
6️⃣  框架遷移 → LangGraph Migration
```

---

## 快速開始

### 方式一：互動式 Wizard

```bash
python cli.py wizard
```

引導步驟：
1. 輸入專案名稱
2. 選擇 Use Case
3. 配置 Agent 數量
4. 選擇安全層級
5. 自動生成專案結構

### 方式二：程式碼

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 1. 專案設定
core.wizard.create_project("ai-assistant", "customer_service")

# 2. 任務規劃
tasks = core.tasks.split_from_goal("開發 AI 客服")
sprint = core.sprints.create_sprint("Sprint 1", capacity=40)

# 3. 安全把關
result = core.guardrails.check(user_input)
if not result.safe:
    print("Blocked by Guardrails")
    return

# 4. Agent 執行
def my_agent(prompt, context=None):
    return call_llm(prompt)

# 5. 評估
suite = core.evaluator.create_suite("Evaluation")
core.evaluator.run_suite(suite.id, my_agent)

# 6. 自動擴展
core.autoscaler.scale_to(replicas=5)

# 7. 通知
core.enterprise.alert("Deployment", "Sprint 1 complete", "info")
```

---

## 模組使用指南

### 1. Setup Wizard

```python
from wizard import SetupWizard, TEMPLATES

wizard = SetupWizard()

# 使用範本
config = wizard.create_project(
    name="my-agent",
    use_case="customer_service"
)

# 自訂配置
config = wizard.create_custom_project(
    name="my-agent",
    agents=[
        {"name": "support", "model": "gpt-4"},
        {"name": "coder", "model": "claude-3"}
    ],
    workflow="parallel"
)
```

### 2. Guardrails (安全)

```python
from guardrails import Guard

guard = Guard()

# 檢查威脅
result = guard.check(user_input)
print(f"Safe: {result.safe}")
print(f"Action: {result.action}")
if result.threats:
    for threat in result.threats:
        print(f"  - {threat['type']}: {threat['message']}")

# 掃描代碼
scan_result = guard.scan_code(code_snippet)
```

### 3. AutoScaler (自動擴展)

```python
from autoscaler import AutoScaler

scaler = AutoScaler()

# 更新指標
scaler.update_metrics(
    cpu_usage=85,
    memory_usage=70,
    queue_length=100,
    response_time=250,
    error_rate=0.02
)

# 檢查並擴展
action = scaler.check_and_scale()
print(f"Action: {action.value}")

# 獲取狀態
status = scaler.get_status()
print(f"Current replicas: {status['current_agents']}")
```

### 4. MAP Protocol (Agent 協調)

```python
from map_protocol import MAPProtocol

protocol = MAPProtocol()

# 編碼訊息
msg = protocol.encode(
    sender="agent-1",
    action="request",
    data={"task": "analyze"}
)

# 解碼訊息
decoded = protocol.decode(msg)
```

### 5. Agent Evaluator (評估)

```python
from agent_evaluator import AgentEvaluator, TestCase

evaluator = AgentEvaluator()

# 建立套件
suite = evaluator.create_suite(
    name="Login Tests",
    version_a_name="GPT-4",
    version_b_name="Claude-3",
    iterations=3
)

# 加入測試
evaluator.add_test_case(
    suite.id,
    name="Valid Login",
    input_prompt="User login with correct credentials",
    expected_output="Login successful"
)

# 執行
evaluator.run_suite(suite.id, agent_a_fn, agent_b_fn)

# 報告
print(evaluator.generate_report(suite.id))
```

### 6. Structured Output (輸出解析)

```python
from structured_output import StructuredOutputEngine, OutputSchema, FieldDefinition

engine = StructuredOutputEngine()

# 定義 Schema
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

# 解析
result = engine.parse(
    prompt="Extract user info",
    llm_call=llm_fn,
    schema_name="user"
)
print(f"Success: {result.success}")
print(f"Data: {result.data}")
```

### 7. Data Quality (資料品質)

```python
from data_quality import DataQualityChecker

checker = DataQualityChecker()

# 分析
report = checker.analyze(data, field_types)

# 報告
print(checker.generate_report_markdown(report))

# 清理
cleaned, _ = checker.clean_data(data, strategy="remove")
```

### 8. Enterprise Hub (企業整合)

```python
from enterprise_hub import EnterpriseHub

hub = EnterpriseHub()

# SSO
hub.auth.configure_okta(domain="company.okta.com", client_id="xxx")

# Slack
hub.add_slack("alerts", webhook_url="https://hooks.slack.com/...")

# 審計
hub.audit.log_access(user_id, username, "/api/tasks")

# 警報
hub.alert("High CPU", "Server at 95%", "warning")
```

### 9. LangGraph Migration (遷移)

```python
from langgraph_migrator import LangGraphMigrationTool

tool = LangGraphMigrationTool()

# 分析
result = tool.analyze_file("my_agent.py")
print(tool.generate_report(result))

# 遷移
result = tool.migrate_file("my_agent.py", "migrated.py")
print(f"Risk: {result.overall_risk}")
```

---

## Solutions A-E

| 方案 | 模組 | CLI | 功能 |
|------|------|-----|------|
| **A** | agent_evaluator.py | eval | A/B 測試、HITL |
| **B** | structured_output.py | parse | JSON Schema、重試 |
| **C** | data_quality.py | quality | 品質檢查、清理 |
| **D** | enterprise_hub.py | enterprise | SSO、審計、通知 |
| **E** | langgraph_migrator.py | migrate | 框架遷移 |

---

## CLI 參考

### 初始化

```bash
# 互動式設定
python cli.py wizard

# 專案初始化
python cli.py init my-project
```

### 任務管理

```bash
python cli.py task add "新功能" --points 5 --priority 2
python cli.py task list
python cli.py task complete task-1
```

### Sprint

```bash
python cli.py sprint create "Sprint 1" --capacity 40
python cli.py sprint list
python cli.py sprint start sprint-1
```

### 視覺化

```bash
python cli.py board
python cli.py report --type weekly
```

### 安全

```bash
python cli.py guardrails check --text "user input"
```

### 擴展

```bash
python cli.py scale status
python cli.py scale scale --current 3
```

### Solutions

```bash
# Agent 評估
python cli.py eval create "Tests"
python cli.py eval add suite-1 "Test 1" --prompt "..." --expected "..."
python cli.py eval run suite-1
python cli.py eval report suite-1

# 資料品質
python cli.py quality check
python cli.py quality report

# 企業整合
python cli.py enterprise status
python cli.py enterprise audit

# 遷移
python cli.py migrate my_agent.py

# 輸出解析
python cli.py parse --schema user
```

### 其他

```bash
python cli.py term velocity
python cli.py resources list
python cli.py pm report
python cli.py version
```

---

## 範例

### 案例：完整 AI 客服系統開發

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 1. 專案設定
print("1. 初始化專案...")
core.wizard.create_project("ai-customer-service", "customer_service")

# 2. 任務規劃
print("2. 規劃任務...")
tasks = core.tasks.split_from_goal("""
開發 AI 客服系統：
1. 自然語言理解
2. 知識庫檢索
3. 多輪對話
4. 轉人工機制
""")

# 3. Sprint 設定
sprint = core.sprints.create_sprint("Sprint 1 - MVP", capacity=40)

# 4. Agent 定義
def客服_agent(prompt, context=None):
    # 安全的輸入
    safe_input = core.guardrails.check(prompt)
    if not safe_input.safe:
        return "對不起，我無法處理這個請求"
    
    # Agent 邏輯
    return call_llm(prompt)

# 5. 測試定義
test_cases = [
    {"name": "問答", "prompt": "如何重置密碼?", "expected": "重置步驟"},
    {"name": "投訴", "prompt": "我很不滿意", "expected": "道歉"},
]

# 6. 執行評估
suite = core.evaluator.create_suite("客服評估")
for tc in test_cases:
    core.evaluator.add_test_case(suite.id, tc["name"], tc["prompt"], tc["expected"])

core.evaluator.run_suite(suite.id, 客服_agent)
print(core.evaluator.generate_report(suite.id))

# 7. 部署
core.autoscaler.scale_to(replicas=5)
core.enterprise.alert("Deployment", "Sprint 1 MVP deployed", "info")
```

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.4.0 | 2026-03-20 | v4.5.0 Extensions 整合 |
| v5.3.1 | 2026-03-20 | 工作流程案例 |
| v5.3.0 | 2026-03-20 | Solutions A-E 完整整合 |
| v5.2.0 | 2026-03-20 | Agent Evaluation |
| v5.1.0 | 2026-03-20 | 單元測試 + 手冊 |
| v5.0.0 | 2026-03-20 | PM Mode |
| v4.9.0 | 2026-03-20 | Terminology + Resources |
| v4.8.0 | 2026-03-20 | CLI Interface |
| v4.7.0 | 2026-03-20 | Visualizations |
| v4.6.2 | 2026-03-20 | Bug Fixes |
| v4.3.0 | 2026-03-20 | 15 缺口解決 |

---

## 許可

MIT License

---

## 🔗 OmO + Methodology-v2 整合

### 整合模式

| 模式 | 說明 | 適用場景 |
|------|------|---------|
| Mode A | OmO → v2 品質把關 | 用 OmO 執行，用 v2 把關 |
| Mode B | v2 → OmO 多模型執行 | 用 v2 規劃，用 OmO 執行 |
| **Mode C** | **兩者同時** | **需要完整協作** |

### 安裝 OmO

```bash
npm install -g oh-my-opencode
oh-my-opencode --version
```

### 快速開始

```python
from om_bridge import EventBridge

# Mode C：完整整合
bridge = EventBridge()
await bridge.start()
```

### 案例

詳細範例請參考：[docs/cases/case08_omo_integration.md](docs/cases/case08_omo_integration.md)
