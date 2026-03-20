# 🎯 Methodology-v2

> Multi-Agent Collaboration Development Framework
> 企業級 AI Agent 開發框架

---

[![Version](https://img.shields.io/badge/version-v5.3.0-blue.svg)](https://github.com/johnnylugm-tech/methodology-v2)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-32%20passed-green.svg)]()

---

## 📋 目錄

1. [完整工作流程](#完整工作流程)
2. [功能清單](#功能清單)
3. [關鍵亮點](#關鍵亮點)
4. [工具相依 Skill](#工具相依-skill)
5. [快速開始](#快速開始)
6. [CLI 參考](#cli-參考)
7. [API 參考](#api-參考)

---

## 🔄 完整工作流程

### 開發流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    開發流程 (Development Flow)                    │
└─────────────────────────────────────────────────────────────────┘

  1. 需求輸入
     │
     ▼
  2. 任務分解 (TaskSplitter)
     │   ├── 目標拆分
     │   ├── 依賴分析
     │   └── 優先級排序
     │
     ▼
  3. Sprint 規劃 (SprintPlanner)
     │   ├── 容量計算
     │   ├── 點數估算
     │   └── 時間規劃
     │
     ▼
  4. Agent 執行 (AgentTeam)
     │   ├── 角色分配
     │   ├── 並行執行
     │   └── 訊息協調
     │
     ▼
  5. 品質把關 (AutoQualityGate)
     │   ├── 程式碼審查
     │   ├── 安全掃描
     │   └── 測試覆蓋
     │
     ▼
  6. 交付追蹤 (DeliveryTracker)
         ├── 版本記錄
         ├── Rollback
         └── Diff 比較
```

### 評估流程 (Solution A)

```
┌─────────────────────────────────────────────────────────────────┐
│                   Agent 評估流程 (Evaluation Flow)                │
└─────────────────────────────────────────────────────────────────┘

  1. 定義測試用例 (TestCase)
     │
     ▼
  2. 執行評估 (AgentEvaluator)
     │   ├── Version A 測試
     │   └── Version B 測試
     │
     ▼
  3. 指標收集
     │   ├── Latency (延遲)
     │   ├── Accuracy (準確率)
     │   ├── Cost (成本)
     │   └── Success Rate (成功率)
     │
     ▼
  4. 人類審查 (HITL) - 可選
     │
     ▼
  5. 產生報告
         ├── A/B 比較
         ├── 風險評估
         └── 建議
```

### 資料流程 (Solutions B + C)

```
┌─────────────────────────────────────────────────────────────────┐
│                    資料處理流程 (Data Flow)                       │
└─────────────────────────────────────────────────────────────────┘

  1. 資料輸入
     │
     ▼
  2. 結構化解析 (StructuredOutputEngine)
     │   ├── JSON Schema 驗證
     │   ├── 自動重試
     │   └── Fallback 機制
     │
     ▼
  3. 品質檢查 (DataQualityChecker)
     │   ├── Missing Value 偵測
     │   ├── Outlier 偵測
     │   ├── Duplicate 偵測
     │   └── Format 驗證
     │
     ▼
  4. 清理處理
     │   ├── Remove (移除)
     │   ├── Fill Null (填補)
     │   └── Default (預設值)
     │
     ▼
  5. 品質報告
         └── Markdown 報告
```

### 企業整合流程 (Solution D)

```
┌─────────────────────────────────────────────────────────────────┐
│                 企業整合流程 (Enterprise Flow)                    │
└─────────────────────────────────────────────────────────────────┘

  1. 認證 (Authenticator)
     │   ├── SSO (Okta/Azure AD/LDAP)
     │   ├── API Key
     │   └── Basic Auth
     │
     ▼
  2. 審計日誌 (AuditLogger)
     │   ├── 存取記錄
     │   ├── 操作軌跡
     │   └── 異常警報
     │
     ▼
  3. 通知 (EnterpriseHub)
     │   ├── Slack
     │   ├── Teams
     │   └── Syslog
     │
     ▼
  4. 監控整合
         └── Prometheus/Grafana
```

---

## 📦 功能清單

### 核心模組 (49+)

| 類別 | 模組 | 功能 |
|------|------|------|
| **任務管理** | task_splitter.py | 目標拆分、依賴分析 |
| | task_splitter_v2.py | 增強拆分演算法 |
| **Sprint** | sprint_planner.py | Sprint 建立、規劃、追蹤 |
| | progress_dashboard.py | Burndown、速度、產出追蹤 |
| **成本** | cost_allocator.py | API/Compute 成本追蹤 |
| | cost_optimizer.py | 自動成本優化 |
| **訊息** | message_bus.py | Pub/Sub 協調 |
| **工作流** | workflow_graph.py | DAG 工作流 |
| | workflow_templates.py | 範本庫 |
| | parallel_executor.py | 並行執行 |
| **Agent** | agent_team.py | 團隊協調 |
| | agent_registry.py | 註冊管理 |
| | agent_spawner.py | 動態 Spawn |
| | agent_lifecycle.py | 生命週期 |
| | agent_state.py | 狀態追蹤 |
| | agent_communication.py | 通訊協議 |
| **品質** | auto_quality_gate.py | 自動化把關 |
| | smart_router.py | 智慧路由 |
| | task_splitter_v2.py | 任務拆分 |
| **監控** | dashboard.py | 統一儀表板 |
| | predictive_monitor.py | 預測監控 |
| | resource_dashboard.py | 資源視圖 |
| | risk_dashboard.py | 風險儀表板 |
| | dashboard_cost_trend.py | 成本趨勢 |
| **交付** | delivery_manager.py | 交付管理 |
| | delivery_tracker.py | 版本追蹤 |
| | doc_generator.py | 文件生成 |
| **安全** | rbac.py | 權限管理 |
| | audit_logger.py | 審計日誌 |
| | approval_flow.py | 審批流程 |
| **整合** | cicd_integration.py | CI/CD 整合 |
| | storage.py | 持久化 |
| | multi_language.py | 多語言支援 |
| | openclaw_adapter.py | OpenClaw 適配 |
| | extension_configurator.py | 擴展配置 |
| | extensions.py | 擴展管理 |
| **知識** | knowledge_base.py | 模式庫 |
| | doc_generator.py | 文件生成 |
| **工具** | scheduler.py | 優先級排程 |
| | failover_manager.py | 故障轉移 |
| **專案** | project.py | 專案管理 |
| | agent_lifecycle.py | Agent 生命週期 |

### Solutions A-E

| 方案 | 模組 | 功能 |
|------|------|------|
| **A: Agent Evaluation** | agent_evaluator.py | A/B 測試、效能指標、HITL |
| **B: Structured Output** | structured_output.py | JSON Schema、重試機制、穩定性追蹤 |
| **C: Data Quality** | data_quality.py | 驗證、異常偵測、品質評分 |
| **D: Enterprise Hub** | enterprise_hub.py | SSO、審計日誌、Slack/Teams |
| **E: LangGraph Migrator** | langgraph_migrator.py | AST 分析、風險評估、程式碼生成 |

### Extensions

| 模組 | 功能 |
|------|------|
| mcp_adapter | 企業服務整合 |
| cost_optimizer | 成本控制 |
| vertical_templates | 垂直範本 |
| security_audit | 安全審計 |
| langchain_adapter | LangChain 遷移 |
| local_deployment | 本地部署 |
| workflow_visualizer | 流程視覺化 |

---

## ⭐ 關鍵亮點

### 1. 統一入口 (MethodologyCore)

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 所有功能統一存取
core.tasks.split_from_goal("開發登入")
core.sprints.create_sprint(...)
core.evaluator.run_suite(...)
core.enterprise.notify(...)
```

### 2. 多 Agent 協調

- **Sequential**: 順序執行，依賴鏈
- **Parallel**: 並行執行，產出合併
- **Hierarchical**: 層級結構，父子協調

```python
# 並行執行
core.workflow.execute_parallel([
    ("task-1", agent_1),
    ("task-2", agent_2),
    ("task-3", agent_3),
])
```

### 3. 智慧路由 (SmartRouter)

```python
router = SmartRouter()

# 根據任務類型自動選擇最佳模型
result = router.route(task_type="code_review", prompt="...")
# 自動選擇性價比最高的模型
```

### 4. 成本控制

```python
# 設定預算
core.costs.set_budget(monthly=1000)

# 追蹤花費
core.costs.track("api_call", model="gpt-4", tokens=1000)

# 超出警報
core.costs.set_alert(threshold=0.8, callback=notify)
```

### 5. 品質把關

```python
gate = AutoQualityGate()

# 自動化審查
result = gate.check(code_snippet, context={
    "language": "python",
    "security_level": "high"
})

print(f"Passed: {result.passed}")
print(f"Score: {result.score}/100")
```

### 6. 可視化

```python
# 甘特圖
gantt.to_rich_ascii()

# Burndown
dashboard.show_burndown(sprint_id)

# 資源視圖
resource_dashboard.to_table()
```

---

## 🔗 工具相依 Skill

### 核心依賴

| Skill | 版本 | 用途 |
|-------|------|------|
| ai-agent-toolkit | v2.1.0 | Agent 工具集 |
| multi-agent-toolkit | - | 協作框架 |
| model-router | v1.0.1 | 模型路由 |

### 整合 Skills

| Skill | 版本 | 整合方式 |
|-------|------|----------|
| Agent Quality Guard | v1.0.3 | 品質把關 |
| Agent Monitor | v3.2.0 | 監控警報 |
| OpenClaw | - | Agent 執行環境 |

### 擴展 Skills

| Skill | 版本 | 功能 |
|-------|------|------|
| mcp_adapter | - | MCP 協定適配 |
| langchain_adapter | - | LangChain 整合 |
| local_deployment | - | 本地部署 |

### Python 依賴

```
# requirements.txt
pydantic>=2.0
dataclasses-json>=0.6
rich>=13.0
pyyaml>=6.0
urllib3>=1.26
```

---

## 🚀 快速開始

### 安裝

```bash
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2
```

### 基本使用

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 1. 任務分解
tasks = core.tasks.split_from_goal("開發 AI 客服系統")

# 2. 建立 Sprint
core.sprints.create_sprint(
    name="Sprint 1",
    capacity=40
)

# 3. 執行 Agent
def my_agent(prompt, context=None):
    return f"Response to: {prompt}"

# 4. 評估
suite = core.evaluator.create_suite("Test Suite")
core.evaluator.run_suite(suite.id, my_agent)

# 5. 檢視報告
print(core.evaluator.generate_report(suite.id))
```

### CLI 使用

```bash
# 初始化
python cli.py init "my-project"

# 任務管理
python cli.py task add "新功能" --points 5
python cli.py task list

# Sprint
python cli.py sprint create "Sprint 1"
python cli.py sprint list

# 視覺化
python cli.py board

# Solutions
python cli.py eval create "Tests"
python cli.py quality check
python cli.py enterprise status
python cli.py migrate my_agent.py
```

---

## 🖥️ CLI 參考

### 專案管理

| 命令 | 說明 |
|------|------|
| `init <name>` | 初始化專案 |
| `status` | 顯示狀態 |
| `version` | 版本資訊 |

### 任務管理

| 命令 | 說明 |
|------|------|
| `task add <name> [--points] [--priority]` | 新增任務 |
| `task list` | 列出任務 |
| `task complete <id>` | 標記完成 |

### Sprint

| 命令 | 說明 |
|------|------|
| `sprint create <name> [--start] [--end] [--capacity]` | 建立 Sprint |
| `sprint list` | 列出 Sprint |
| `sprint start <id>` | 開始 Sprint |

### Solutions

| 命令 | 說明 |
|------|------|
| `eval create <name>` | 建立評估套件 |
| `eval run <suite_id>` | 執行評估 |
| `eval report <suite_id>` | 評估報告 |
| `quality check` | 資料品質檢查 |
| `enterprise status` | 企業整合狀態 |
| `migrate <file>` | 遷移到 LangGraph |
| `parse [--schema]` | 結構化輸出解析 |

### 其他

| 命令 | 說明 |
|------|------|
| `board` | 視覺化看板 |
| `report [--type]` | 產生報告 |
| `term <query>` | PM 術語查詢 |
| `resources list` | 資源清單 |
| `pm report` | 晨間報告 |
| `pm forecast` | 成本預測 |
| `pm health` | Sprint 健康 |

---

## 📚 API 參考

### MethodologyCore

```python
class MethodologyCore:
    # 任務
    @property
    def tasks(self) -> TaskSplitter
    
    # Sprint
    @property
    def sprints(self) -> SprintPlanner
    
    # 成本
    @property
    def costs(self) -> CostAllocator
    
    # 訊息
    @property
    def bus(self) -> MessageBus
    
    # 工作流
    @property
    def workflow(self) -> WorkflowGraph
    
    # 評估 (Solution A)
    @property
    def evaluator(self) -> AgentEvaluator
    
    # 輸出解析 (Solution B)
    @property
    def structured_output(self) -> StructuredOutputEngine
    
    # 資料品質 (Solution C)
    @property
    def data_quality(self) -> DataQualityChecker
    
    # 企業整合 (Solution D)
    @property
    def enterprise(self) -> EnterpriseHub
    
    # 遷移 (Solution E)
    @property
    def migrator(self) -> LangGraphMigrationTool
```

### AgentEvaluator

```python
class AgentEvaluator:
    def create_suite(name, iterations=1) -> EvaluationSuite
    def add_test_case(suite_id, name, input_prompt, expected_output) -> TestCase
    def run_suite(suite_id, agent_a_fn, agent_b_fn=None) -> EvaluationSuite
    def generate_report(suite_id) -> str
    def compare_versions(suite_id) -> Dict
```

### StructuredOutputEngine

```python
class StructuredOutputEngine:
    def parse(prompt, llm_call, schema_name, max_retries=3) -> ParseResult
    def register_schema(schema: OutputSchema)
    def generate_report() -> str
```

### DataQualityChecker

```python
class DataQualityChecker:
    def analyze(data, field_types=None) -> QualityReport
    def clean_data(data, strategy="remove") -> Tuple[List, QualityReport]
    def generate_report_markdown(report) -> str
```

### EnterpriseHub

```python
class EnterpriseHub:
    @property
    def auth(self) -> Authenticator
    @property
    def audit(self) -> AuditLogger
    
    def add_slack(name, webhook_url) -> SlackMessenger
    def add_teams(name, webhook_url) -> TeamsMessenger
    def notify(messenger_name, message) -> bool
    def alert(title, message, severity) -> None
```

### LangGraphMigrationTool

```python
class LangGraphMigrationTool:
    def analyze_file(file_path) -> MigrationResult
    def migrate_file(file_path, output_path) -> MigrationResult
    def generate_report(result) -> str
    def validate_langgraph_syntax(code) -> Tuple[bool, str]
```

---

## 📊 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.3.0 | 2026-03-20 | Solutions A-E 完整整合 |
| v5.2.0 | 2026-03-20 | Agent Evaluation Framework |
| v5.1.0 | 2026-03-20 | 單元測試 + 使用手冊 |
| v5.0.0 | 2026-03-20 | PM Mode + Real Data Connectors |
| v4.9.0 | 2026-03-20 | PM Terminology + Resource Dashboard |
| v4.8.0 | 2026-03-20 | CLI Interface |
| v4.7.0 | 2026-03-20 | P1 Visualizations |
| v4.6.2 | 2026-03-20 | P0 Bug Fixes |
| v4.3.0 | 2026-03-20 | 15 缺口全部解決 |

---

## 📄 許可

MIT License

---

**GitHub**: https://github.com/johnnylugm-tech/methodology-v2
**Release**: https://github.com/johnnylugm-tech/methodology-v2/releases/tag/v5.3.0
