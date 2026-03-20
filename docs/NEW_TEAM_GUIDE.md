# 🎯 Methodology-v2 完整介紹

> 給新團隊的入門指南

---

## 1️⃣ 什麼是 Methodology-v2？

**Methodology-v2** 是一個 **企業級 AI Agent 開發框架**，幫助團隊：

- 🤖 協調多個 AI Agent 完成複雜任務
- 📊 管理專案進度、成本、品質
- 🔒 確保程式碼安全與合規
- 🚀 自動化 CI/CD 部署

---

## 2️⃣ 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    MethodologyCore (統一入口)                  │
└─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    ▼                         ▼                         ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Planning   │       │  Execution   │       │   Delivery  │
│              │       │              │       │             │
│ • 任務拆分   │       │ • 工作流引擎 │       │ • 版本管理   │
│ • Agent 定義 │       │ • 排程執行   │       │ • 文檔生成   │
│ • 審批流程   │       │ • 品質把關   │       │ • 測試生成   │
│ • 依賴管理   │       │ • 錯誤處理   │       │ • 交付追蹤   │
└─────────────┘       └─────────────┘       └─────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring (監控層)                         │
│                                                             │
│ • 健康狀態   • 成本追蹤   • 風險儀表板   • 預測監控          │
└─────────────────────────────────────────────────────────────┘
```

### 詳細流程

```
Step 1: 需求輸入
        │
        ▼
Step 2: 任務拆分 (TaskSplitter)
        │ • 拆解成子任務
        │ • 建立依賴關係 (DAG)
        │ • 設定優先級
        ▼
Step 3: Agent 分配 (AgentTeam)
        │ • 定義角色 (Developer/Reviewer/Tester)
        │ • 設定能力
        │ • 權限管理 (RBAC)
        ▼
Step 4: 模型路由 (SmartRouter)
        │ • 根據任務選擇合適模型
        │ • 成本優化 (省 70-93%)
        ▼
Step 5: 執行與協調 (WorkflowGraph)
        │ • 順序/並行/階層執行
        │ • 訊息傳遞 (MessageBus)
        │ • 狀態共享 (AgentState)
        ▼
Step 6: 品質把關 (AutoQualityGate)
        │ • 安全掃描
        │ • 程式碼品質檢查
        │ • 自動修復
        ▼
Step 7: 監控與警報 (Dashboard)
        │ • 即時健康狀態
        │ • 成本追蹤
        │ • 異常預測
        ▼
Step 8: 交付與版本 (DeliveryManager)
        • 版本控制
        • Rollback
        • 交付追蹤
```

---

## 3️⃣ 功能清單 (49+ 模組)

### 3.1 核心協調 (Core Coordination)

| 模組 | 功能 | 範例 |
|------|------|------|
| `MethodologyCore` | 統一入口 | `core = MethodologyCore()` |
| `AgentTeam` | Agent 團隊定義 | 定義 Developer/Reviewer/Tester |
| `AgentRegistry` | Agent 注册 | 追蹤所有 Agent 狀態 |
| `AgentSpawner` | 標準化 Spawn | 數量限制、優先級佇列 |
| `MessageBus` | Agent 間通訊 | 發布/訂閱模式 |
| `AgentCommunication` | 訊息協議 | REQUEST/RESPONSE/HANDOFF |
| `AgentState` | 共享狀態 | 跨 Agent 狀態同步 |
| `WorkflowGraph` | 工作流引擎 | DAG 執行順序 |
| `ApprovalFlow` | 審批流程 | Human-in-the-Loop |

### 3.2 執行引擎 (Execution)

| 模組 | 功能 | 範例 |
|------|------|------|
| `TaskSplitter` | 任務拆分 | 拆解複雜任務 |
| `TaskSplitterV2` | 進階拆分 | DAG + 里程碑 |
| `Scheduler` | 排程執行 | 優先級 + 截止時間 |
| `ParallelExecutor` | 並行執行 | 多任務同時處理 |
| `FailoverManager` | 故障轉移 | 自動切換備用方案 |

### 3.3 品質保證 (Quality)

| 模組 | 功能 | 範例 |
|------|------|------|
| `AutoQualityGate` | 自動品質把關 | 掃描 + 自動修復 |
| `SmartRouter` | 智慧模型路由 | 根據任務選模型 |
| `SecurityAuditor` | 安全審計 | API Key/Injection 檢測 |
| `RBAC` | 權限管理 | 角色 + 權限控制 |

### 3.4 監控儀表板 (Monitoring)

| 模組 | 功能 | 範例 |
|------|------|------|
| `Dashboard` | 統一儀表板 | Web UI (Port 8080) |
| `ProgressDashboard` | 進度追蹤 | Sprint/Backlog/Burndown |
| `PredictiveMonitor` | 預測監控 | 異常預測 |
| `RiskDashboard` | 風險儀表板 | 風險辨識 + 評分 |
| `CostTrendAnalyzer` | 成本趨勢 | 月度成本分析 |

### 3.5 交付管理 (Delivery)

| 模組 | 功能 | 範例 |
|------|------|------|
| `DeliveryManager` | 交付追蹤 | 版本 + 狀態管理 |
| `DocGenerator` | 文檔生成 | 自動產生 API 文檔 |
| `TestGenerator` | 測試生成 | pytest/unittest |
| `CostAllocator` | 成本分攤 | 按人/按專案分攤 |
| `VersionControl` | 版本控制 | Rollback + Diff |

### 3.6 企業整合 (Enterprise)

| 模組 | 功能 | 範例 |
|------|------|------|
| `CICDIntegration` | CI/CD 建立 | GitHub Actions/Jenkins |
| `MultiLanguageSupport` | 多語言支援 | Python/JS/Go/Rust |
| `KnowledgeBase` | 知識庫 | Pattern + Best Practice |
| `Storage` | 持久化 | SQLite + PostgreSQL |

### 3.7 Extensions (7 個)

| Extension | 功能 |
|-----------|------|
| `mcp_adapter` | Slack/GitHub/Notion 整合 |
| `cost_optimizer` | 成本控制 (省 70-93%) |
| `vertical_templates` | 客服/法律 Agent 模板 |
| `security_audit` | OWASP Top 10 檢測 |
| `langchain_adapter` | LangChain 遷移工具 |
| `local_deployment` | 本地 Docker 部署 |
| `workflow_visualizer` | Mermaid 圖表生成 |

---

## 4️⃣ 關鍵亮點 (10 大特色)

### 🌟 為什麼選 Methodology-v2？

| # | 亮點 | 說明 |
|---|------|------|
| 1 | **統一入口** | 一行程式碼啟動完整框架 |
| 2 | **Agent 協調** | 完整的角色、通訊、狀態管理 |
| 3 | **三大核心工具** | Model Router + Agent Monitor + Quality Guard |
| 4 | **成本優化** | 省 70-93% API 成本 |
| 5 | **企業整合** | MCP + CI/CD + 多語言 |
| 6 | **預測監控** | 趨勢預測 + 異常檢測 |
| 7 | **版本控制** | Rollback + Diff + Tag |
| 8 | **CI/CD** | GitHub Actions / Jenkins / GitLab CI |
| 9 | **多語言支援** | Python / JS / Go / Rust |
| 10 | **知識庫** | 15+ Pattern + Best Practice |

### 💰 成本對比

| 方案 | 月成本 | 效率 |
|------|--------|------|
| 直接用 GPT-4 | $500 | 100% |
| **Methodology-v2** | **$35-150** | **省 70-93%** |

### 📊 功能覆蓋

| 需求 | 支援 |
|------|------|
| Multi-Agent 協作 | ✅ |
| 任務拆分 + DAG | ✅ |
| 品質把關 | ✅ |
| 成本優化 | ✅ |
| CI/CD 整合 | ✅ |
| 版本控制 | ✅ |
| 預測監控 | ✅ |
| 知識庫 | ✅ |
| Human-in-the-Loop | ✅ |
| 多語言支援 | ✅ |

---

## 5️⃣ 三大核心工具 (單獨維護)

| 工具 | GitHub | 功能 |
|------|--------|------|
| **Model Router** | [model-router-v2](https://github.com/johnnylugm-tech/model-router-v2) | 智慧路由 + 快取 + Failover |
| **Agent Monitor** | [agent-dashboard-v3](https://github.com/johnnylugm-tech/agent-dashboard-v3) | 即時監控 + 警報 |
| **Agent Quality Guard** | [Agent-Quality-Guard](https://github.com/johnnylugm-tech/Agent-Quality-Guard) | 程式碼品質 + 安全掃描 |

---

## 6️⃣ 使用的 Skills 清單

### 6.1 核心工具 (Tool Skills)

| Skill | GitHub | 用途 | 整合方式 |
|-------|--------|------|----------|
| **Model Router** | model-router-v2 | 智慧路由 | 整合到 SmartRouter |
| **Agent Monitor** | agent-dashboard-v3 | 監控儀表板 | 整合到 Dashboard |
| **Agent Quality Guard** | Agent-Quality-Guard | 程式碼品質 | 整合到 AutoQualityGate |

### 6.2 框架 Skills

| Skill | 用途 | 整合方式 |
|-------|------|----------|
| `dispatching-parallel-agents` | 任務分配 | AgentTeam 引用 |
| `sessions_spawn` | 建立子 Agent | AgentSpawner 使用 |
| `sessions_send` | 跨 Agent 溝通 | MessageBus 使用 |
| `verification-before-completion` | 交付前驗證 | AutoQualityGate 使用 |
| `requesting-code-review` | 程式碼審查 | 品質把關流程 |
| `agent-task-manager` | 任務管理 | TaskSplitter 整合 |
| `long-term-memory` | 長期記憶 | Storage 搭配 |
| `executing-plans` | 執行計劃 | WorkflowGraph 引用 |
| `planning-with-files` | 規劃管理 | 任務規劃參考 |

### 6.3 企業 Skills

| Skill | 用途 | 整合方式 |
|-------|------|----------|
| MCP Adapter | 企業服務整合 | Extensions 層 |
| LangChain Adapter | 遷移工具 | Extensions 層 |
| Local Deployment | 本地部署 | Extensions 層 |
| Workflow Visualizer | 圖表生成 | Extensions 層 |

---

## 7️⃣ 快速開始

### 安裝

```bash
pip install methodology-v2
```

### 第一個範例

```python
from methodology import MethodologyCore

# 1. 建立核心
core = MethodologyCore()

# 2. 拆分任務
tasks = core.tasks.split_from_goal("開發 AI 客服系統")
print(f"建立 {len(tasks)} 個子任務")

# 3. Spawn Agent
agent_id = core.spawn_agent("developer", "task-1", "實作登入功能")

# 4. 版本控制
v1 = core.commit_version("login-module", "def login(): pass", message="init")

# 5. 安全掃描
report = core.scan_security("src/login.py")

# 6. 成本追蹤
core.track_cost_usage("gpt-4o", 1000, 500)

print("✅ 完成！")
```

---

## 8️⃣ 案例索引 (18 個實作案例)

| 情境 | 案例 |
|------|------|
| PM 日常 | [晨間報告](docs/cases/case01_pm_daily.md)、[成本追蹤](docs/cases/case01_pm_daily.md)、[Sprint 規劃](docs/cases/case01_pm_daily.md) |
| 軟體開發 | [團隊建立](docs/cases/case02_development.md)、[智慧路由](docs/cases/case02_development.md)、[品質把關](docs/cases/case02_development.md) |
| Multi-Agent | [階層協作](docs/cases/case03_multi_agent.md)、[通訊](docs/cases/case03_multi_agent.md)、[狀態共享](docs/cases/case03_multi_agent.md) |
| 企業整合 | [CI/CD](docs/cases/case04_enterprise.md)、[多語言](docs/cases/case04_enterprise.md)、[MCP](docs/cases/case04_enterprise.md) |
| 監控 | [錯誤分類](docs/cases/case05_monitoring.md)、[預測](docs/cases/case05_monitoring.md)、[熔斷](docs/cases/case05_monitoring.md) |
| 知識管理 | [Pattern](docs/cases/case06_knowledge.md)、[版本控制](docs/cases/case06_knowledge.md)、[Rollback](docs/cases/case06_knowledge.md) |

---

## 9️⃣ 版本歷程

| 版本 | 日期 | 功能 |
|------|------|------|
| v4.4.0 | 2026-03-20 | 18 個案例文檔 |
| v4.3.3 | 2026-03-20 | 修復命名衝突 |
| v4.3.0 | 2026-03-20 | PM 缺口 15/15 全部解決 |
| v4.2.0 | 2026-03-20 | Extensions 整合 |
| v4.1.0 | 2026-03-20 | 架構優化 + 統一入口 |

---

## 🔗 資源連結

| 資源 | 連結 |
|------|------|
| GitHub | https://github.com/johnnylugm-tech/methodology-v2 |
| Releases | https://github.com/johnnylugm-tech/methodology-v2/releases |
| 文檔 | [QUICKSTART.md](QUICKSTART.md)、[PM_HANDBOOK.md](PM_HANDBOOK.md) |
| 案例 | [docs/cases/README.md](docs/cases/README.md) |

---

**準備好使用了嗎？從 [QUICKSTART.md](QUICKSTART.md) 開始！**
