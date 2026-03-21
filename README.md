# 🎯 Methodology-v2

> Multi-Agent Collaboration Development Framework
> 企業級 AI Agent 開發框架

---

[![Version](https://img.shields.io/badge/version-v5.6.0-blue.svg)](https://github.com/johnnylugm-tech/methodology-v2)
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

### 1️⃣ 專案初始化流程 (Setup Wizard)

```
┌─────────────────────────────────────────────────────────────────┐
│                   專案初始化 (Setup Wizard)                        │
└─────────────────────────────────────────────────────────────────┘

  1. 啟動 Wizard
     │   python cli.py wizard
     │
     ▼
  2. 選擇 Use Case
     │   ├── Customer Service (客服)
     │   ├── Coding (編程)
     │   ├── Research (研究)
     │   ├── Data Analysis (數據分析)
     │   └── Custom (自訂)
     │
     ▼
  3. 配置 Agent
     │   ├── 名稱
     │   ├── 模型
     │   └── 工具
     │
     ▼
  4. 選擇安全層級
     │   ├── Basic (基本)
     │   ├── Standard (標準)
     │   └── Enterprise (企業)
     │
     ▼
  5. 輸出設定檔
         └── project.yaml
```

### 2️⃣ 開發流程 (Development Flow)

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
     │   └── 訊息協調 (MAP Protocol)
     │
     ▼
  5. 安全把關 (Guardrails)
     │   ├── Prompt Injection 檢測
     │   ├── PII 過濾
     │   ├── SQL Injection 檢測
     │   └── Content Moderation
     │
     ▼
  6. 自動擴展 (AutoScaler)
     │   ├── 負載監控
     │   ├── 副本計算
     │   └── K8s HPA 支援
     │
     ▼
  7. 交付追蹤 (DeliveryTracker)
         ├── 版本記錄
         ├── Rollback
         └── Diff 比較
```

### 3️⃣ 評估流程 (Agent Evaluation)

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

### 4️⃣ 資料流程 (Data Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                    資料處理流程 (Data Flow)                       │
└─────────────────────────────────────────────────────────────────┘

  1. 資料輸入
     │
     ▼
  2. 安全檢查 (Guardrails)
     │   ├── PII 過濾
     │   └── 威脅檢測
     │
     ▼
  3. 結構化解析 (StructuredOutputEngine)
     │   ├── JSON Schema 驗證
     │   ├── 自動重試
     │   └── Fallback 機制
     │
     ▼
  4. 品質檢查 (DataQualityChecker)
     │   ├── Missing Value 偵測
     │   ├── Outlier 偵測
     │   ├── Duplicate 偵測
     │   └── Format 驗證
     │
     ▼
  5. 清理處理
     │   ├── Remove (移除)
     │   ├── Fill Null (填補)
     │   └── Default (預設值)
     │
     ▼
  6. 品質報告
         └── Markdown 報告
```

### 5️⃣ 企業整合流程 (Enterprise Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                 企業整合流程 (Enterprise Flow)                    │
└─────────────────────────────────────────────────────────────────┘

  1. 認證 (SSO Integration)
     │   ├── Okta (OIDC/SAML)
     │   ├── Azure AD (OAuth2)
     │   ├── LDAP
     │   ├── API Key
     │   └── Basic Auth
     │
     ▼
  2. 授權 (RBAC)
     │   ├── 角色定義
     │   ├── 權限分配
     │   └── 資源訪問控制
     │
     ▼
  3. 審計日誌 (AuditLogger)
     │   ├── 存取記錄
     │   ├── 操作軌跡
     │   └── 異常警報
     │
     ▼
  4. 通知 (EnterpriseHub)
     │   ├── Slack
     │   ├── Teams
     │   └── Syslog
     │
     ▼
  5. 監控 (Cloud Dashboard)
         ├── 即時監控
         ├── 團隊協作
         └── 警報系統
```

### 6️⃣ 遷移流程 (Migration Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                   遷移流程 (Migration Flow)                       │
└─────────────────────────────────────────────────────────────────┘

  1. 分析現有程式碼
     │
     ▼
  2. AST 解析 (LangGraphMigrationTool)
     │   ├── 節點識別
     │   ├── 依賴分析
     │   └── 風險評估
     │
     ▼
  3. 模式對應
     │   ├── State 轉換
     │   ├── Agent 轉換
     │   └── Tool 轉換
     │
     ▼
  4. 程式碼生成
     │
     ▼
  5. 驗證與部署
         ├── 語法驗證
         └── 測試
```

---

## 📦 功能清單

### 核心模組 (71+)

| 類別 | 模組 | 功能 |
|------|------|------|
| **任務管理** | task_splitter.py | 目標拆分、依賴分析 |
| | task_splitter_v2.py | 增強拆分演算法 |
| **Sprint** | sprint_planner.py | Sprint 建立、規劃、追蹤 |
| | progress_dashboard.py | Burndown、速度、產出追蹤 |
| **成本** | cost_allocator.py | API/Compute 成本追蹤 |
| | cost_optimizer.py | 自動成本優化 |
| **訊息** | message_bus.py | Pub/Sub 協調 |
| | map_protocol.py | 標準化 Agent 溝通 |
| **工作流** | workflow_graph.py | DAG 工作流 |
| | workflow_templates.py | 範本庫 |
| | parallel_executor.py | 並行執行 |
| **Agent** | agent_team.py | 團隊協調 |
| | agent_registry.py | 註冊管理 |
| | agent_spawner.py | 動態 Spawn |
| | agent_lifecycle.py | 生命週期 |
| | agent_state.py | 狀態追蹤 |
| **品質** | auto_quality_gate.py | 自動化把關 |
| | smart_router.py | 智慧路由 |
| **安全** | guardrails.py | Prompt Injection、PII、SQL Injection |
| **監控** | dashboard.py | 統一儀表板 |
| | predictive_monitor.py | 預測監控 |
| | resource_dashboard.py | 資源視圖 |
| | risk_dashboard.py | 風險儀表板 |
| | risk_registry.py | 風險登記表 |
| | cloud_dashboard.py | 雲端監控 |
| **交付** | delivery_manager.py | 交付管理 |
| | delivery_tracker.py | 版本追蹤 |
| | doc_generator.py | 文件生成 |
| **擴展** | wizard.py | 互動式設定精靈 |
| | autoscaler.py | 自動擴展管理 |
| | llm_providers.py | 多供應商支援 |
| | sso_integration.py | SSO 單一登入 |
| | marketplace.py | 模板市場 |
| | test_framework.py | 測試框架 |

### Solutions A-R

| 方案 | 模組 | 功能 |
|------|------|------|
| **A: Agent Evaluation** | agent_evaluator.py | A/B 測試、效能指標、HITL |
| **B: Structured Output** | structured_output.py | JSON Schema、重試機制、穩定性追蹤 |
| **C: Data Quality** | data_quality.py | 驗證、異常偵測、品質評分 |
| **D: Enterprise Hub** | enterprise_hub.py | SSO、審計日誌、Slack/Teams |
| **E: LangGraph Migrator** | langgraph_migrator.py | AST 分析、風險評估、程式碼生成 |
| **F: Output Validator** | agent_output_validator.py | Schema 驗證 + 自動修復 |
| **G: Agent Debugger** | agent_debugger.py | Trace/觀測性系統 |
| **H: Framework Bridge** | framework_bridge.py | CrewAI ↔ LangGraph 雙向遷移 |
| **I: Agent Memory** | agent_memory/ | 長期記憶、上下文管理 |
| **J: Observability** | observability/ | 可觀測性、日誌、追蹤 |
| **K: Auto Debugger** | auto_debugger/ | 自動調試、錯誤分類 |
| **L: API Gateway** | api_gateway/ | API 閘道、限流 |
| **M: Governance** | governance/ | 治理合規、政策執行 |
| **N: Advanced Security** | advanced-security/ | 安全掃描、滲透測試 |
| **O: Performance** | performance_optimizer/ | 效能優化、緩存 |
| **P: Three-Phase Executor** | three_phase_executor/ | 三階段並行執行 (串→並→串) |
| **Q: Fault Tolerant** | fault_tolerant/ | 容錯系統、熔斷器、Output Validator |
| **R: Smart Orchestrator** | smart_orchestrator/ | 智能任務協調、負載均衡 |

---

## ⭐ 關鍵亮點
### 🆕 強化 LLM Providers 模組 (2026-03-21)
- 新增 Provider 支援
- 來源: 輪換

### 🆕 強化 Guardrails 安全模組 (2026-03-21)
- 新增更多安全檢測規則
- 來源: 預設

### 🆕 Agent Output Validator (2026-03-21)
- 新增 `agent_output_validator.py`：JSON Schema / Pydantic / 自訂規則驗證 + 自動修復
- `StructuredOutputEngine.validate_output()` 整合驗證器
- `validate_and_fix_with_quality_gate()` 完整流程（Validator + QualityGate 整合）
- 來源: 任務 F

### 🆕 強化 Guardrails 安全模組 (2026-03-21)
- 新增更多安全檢測規則

### 🆕 強化 Guardrails 安全模組 (2026-03-20)
- 新增更多安全檢測規則

### 🆕 強化 Guardrails 安全模組 (2026-03-20)
- 新增更多安全檢測規則


### 1. 統一入口 (MethodologyCore)

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 所有功能統一存取
core.tasks.split_from_goal("開發登入")
core.sprints.create_sprint(...)
core.evaluator.run_suite(...)
core.guardrails.check(...)
core.autoscaler.scale_to(...)
core.enterprise.notify(...)
```

### 2. 互動式設定 (Wizard)

```bash
python cli.py wizard
# 引導式建立專案
```

### 3. 安全防護 (Guardrails)

```python
# Prompt Injection 檢測
result = guardrails.check(user_input)

# PII 過濾
result = guardrails.mask_pii(user_input)
```

### 4. 自動擴展 (AutoScaler)

```python
# 根據負載自動調整
scaler.update_metrics(cpu=85, queue=100)
action = scaler.check_and_scale()
```

### 5. 多 Agent 協調 (MAP Protocol)

```python
# 標準化 Agent 溝通
message = MAPProtocol.encode(sender="agent-1", action="request", data={})
```

---

## 🔗 工具相依 Skill

### 核心說明

> 📦 **重要提醒**：methodology-v2 已經**內建所有核心功能**，安裝後即可使用。
> 
> 下列技能/工具為 **Johnny's AI Agent 生態系** 的一部分，可按需安裝。

### Johnny's AI Agent 生態系

| 專案 | 版本 | 關係 | 說明 |
|------|------|------|------|
| **methodology-v2** | v5.6.0 | 主框架 | ✅ 內建，無需額外安裝 |
| Agent Quality Guard | v1.0.3 | 生態系 | 品質把關，可選 |
| Model Router | v2.3.0 | 生態系 | 模型路由，可選 |
| Agent Monitor | v3.2.0 | 生態系 | 監控警報，可選 |
| ai-agent-toolkit | v2.1.0 | 生態系 | 工具集，引用 |

### Python 依賴 (自動安裝)

```bash
# 安裝 methodology-v2 時會自動安裝
pip install -r requirements.txt
```

```txt
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
# 方法一：Clone 並安裝
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2
pip install -r requirements.txt

# 方法二：直接使用 (已包含所有依賴)
# 無需額外安裝任何 Skill 或工具
```

### 基本使用

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 1. 專案設定
core.wizard.create_project("my-project", "customer_service")

# 2. 任務分解
tasks = core.tasks.split_from_goal("開發 AI 客服系統")

# 3. 安全檢查
result = core.guardrails.check(user_input)

# 4. Agent 評估
suite = core.evaluator.create_suite("Test Suite")
core.evaluator.run_suite(suite.id, my_agent)

# 5. 自動擴展
core.autoscaler.scale_to(replicas=5)

# 6. 部署通知
core.enterprise.alert("Deployment Complete", "Sprint 1 done")
```

### CLI 使用

```bash
# 初始化
python cli.py wizard

# 任務管理
python cli.py task add "新功能" --points 5
python cli.py task list

# Sprint
python cli.py sprint create "Sprint 1"
python cli.py sprint list

# 視覺化
python cli.py board

# 安全
python cli.py guardrails check --text "..."

# 擴展
python cli.py scale status

# Solutions
python cli.py eval create "Tests"
python cli.py quality check
python cli.py enterprise status
python cli.py migrate my_agent.py
```

---

## 🖥️ CLI 參考

| 命令 | 說明 |
|------|------|
| `wizard` | 互動式專案設定 |
| `init` | 初始化專案 |
| `task` | 任務管理 (add/list/complete) |
| `sprint` | Sprint 管理 (create/list/start) |
| `board` | 視覺化看板 |
| `eval` | Agent 評估 (create/run/hitl/report/list) |
| `quality` | 資料品質檢查 (check/report) |
| `guardrails` | 安全檢查 (check) |
| `scale` | 自動擴展 (status) |
| `enterprise` | 企業整合 (status/audit) |
| `migrate` | 遷移到 LangGraph |
| `parse` | 結構化輸出解析 |
| `term` | PM 術語查詢 |
| `resources` | 資源清單 |
| `pm` | PM Mode (report/forecast/health) |
| `bus` | Message Bus 狀態 |
| `report` | 產生報告 |
| `status` | 顯示狀態 |
| `version` | 顯示版本 |
| `approval` | 人類審批管理 (list/create/approve/reject/show/report/stats) |
| `risk` | 風險登記表 (add/list/show/close/mitigate/report/stats/delete) |

**共 21 個 CLI 命令**

### 🔧 Risk CLI 範例

```bash
# 新增風險
python cli.py risk add --title "API 超時" --desc "第三方 API 回應時間超過 5 秒" --level high --owner alice --impact "用戶體驗下降" --probability 0.6 --mitigation "添加重試機制和備用供應商"

# 列出所有風險
python cli.py risk list

# 按等級篩選
python cli.py risk list --level high

# 查看風險詳情
python cli.py risk show --risk-id <id>

# 緩解風險
python cli.py risk mitigate --risk-id <id>

# 關閉風險
python cli.py risk close --risk-id <id>

# 產生風險報告
python cli.py risk report

# 查看統計
python cli.py risk stats
```

### 🔧 Approval CLI 範例

```bash
# 查看待審批任務
python cli.py approval list

# 創建審批請求
python cli.py approval create --name "代碼審查" --approval-type code_review --requester dev-1 --requester-name "大明"

# 批准任務
python cli.py approval approve --request-id <id> --approver lead --comment "LGTM"

# 駁回任務
python cli.py approval reject --request-id <id> --approver lead --comment "需要修改"

# 查看任務詳情
python cli.py approval show --request-id <id>

# 查看統計
python cli.py approval stats
```

### 🌐 Approval Web UI

啟動 Streamlit 審批界面：

```bash
streamlit run approval_ui.py
```

功能：
- 📋 查看待審批任務
- ✅/❌ Approve/Reject 按鈕
- 📊 統計儀表板
- ➕ 創建新審批請求

---

## 🔗 OmO + Methodology-v2 整合

### 整合方案

Methodology-v2 支援與 [Oh My OpenCode (OmO)](https://github.com/code-yeongyu/oh-my-openagent) 整合：

- **Mode A**: OmO → v2 品質把關
- **Mode B**: v2 → OmO 多模型執行
- **Mode C**: 兩者同時 (完整整合)

### 安裝

```bash
npm install -g oh-my-opencode
oh-my-opencode --version
```

### 使用方式

```python
from om_bridge import EventBridge

bridge = EventBridge()  # Mode C 完整整合
await bridge.start()
```

詳見：[案例 8：OmO + v2 整合實戰](docs/cases/case08_omo_integration.md)

---

## 🆕 Extensions (v5.6.0 新增)

| 模組 | 功能 |
|------|------|
| **advanced-security** | 高級安全檢查、滲透測試 |
| **agent_memory** | 長期記憶、上下文管理 |
| **api_gateway** | API 閘道、限流、監控 |
| **auto_debugger** | 自動調試、錯誤分類、根因分析 |
| **governance** | 治理合規、政策執行 |
| **observability** | 可觀測性、日誌、追蹤、儀表板 |
| **performance_optimizer** | 效能優化、延遲優化、緩存 |

---

## 📚 案例文檔

完整範例請參考：[docs/cases/README.md](docs/cases/README.md)

| # | 情境 | 檔案 |
|---|------|------|
| 1 | PM 日常管理 | docs/cases/case01_pm_daily.md |
| 2 | 軟體開發團隊 | docs/cases/case02_development.md |
| 3 | Multi-Agent 協作 | docs/cases/case03_multi_agent.md |
| 4 | 企業整合 | docs/cases/case04_enterprise.md |
| 5 | 錯誤處理與監控 | docs/cases/case05_monitoring.md |
| 6 | 知識管理 | docs/cases/case06_knowledge.md |
| 7 | 錯誤處理與例外情境 | docs/cases/case07_error_handling.md |
| 8 | OmO + v2 整合實戰 | docs/cases/case08_omo_integration.md |

---

## 📚 API 參考

### MethodologyCore

```python
class MethodologyCore:
    # 專案
    @property
    def wizard(self) -> SetupWizard
    
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
    
    # 安全 (Guardrails)
    @property
    def guardrails(self) -> Guard
    
    # 自動擴展 (AutoScaler)
    @property
    def autoscaler(self) -> AutoScaler
    
    # 企業整合 (Solution D)
    @property
    def enterprise(self) -> EnterpriseHub
    
    # 遷移 (Solution E)
    @property
    def migrator(self) -> LangGraphMigrationTool
```

---

## 📊 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.6.0 | 2026-03-20 | Trend Optimization: 強化 Guardrails 安全模組 |
| v5.6.0 | 2026-03-20 | v4.5.0 Extensions 整合 |
| v5.3.1 | 2026-03-20 | 工作流程案例 |
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
**Release**: https://github.com/johnnylugm-tech/methodology-v2/releases/tag/v5.6.0
