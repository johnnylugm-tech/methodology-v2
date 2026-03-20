# 🎯 Methodology-v2

> Multi-Agent Collaboration Development Framework
> 企業級 AI Agent 開發框架

---

[![Version](https://img.shields.io/badge/version-v4.3.0-blue.svg)](https://github.com/johnnylugm-tech/methodology-v2)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)

---

## 📦 安裝

```bash
pip install methodology-v2
```

或：

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2
cd methodology-v2
pip install -e .
```

---

## 🚀 快速開始

### 統一入口

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 任務分解
core.tasks.split_from_goal("開發 AI 客服系統")

# Agent 注册
core.agents.register("dev-1", "Developer", AgentType.DEVELOPER)

# 發布事件
core.publish_event("project:started", {})

# 安全掃描
core.scan_security("src/code.py")

# 版本控制
core.commit_version("login-module", "def login(): pass", message="init")
```

---

## 📚 功能概覽

### 核心模組 (44+)

| 類別 | 模組 | 功能 |
|------|------|------|
| **Agent 協調** | AgentTeam, AgentRegistry, AgentSpawner, MessageBus | 定義、注册、Spawn、通訊 |
| **執行** | WorkflowGraph, Scheduler, ParallelExecutor | DAG 工作流、排程 |
| **品質** | AutoQualityGate, SmartRouter, TaskSplitterV2 | 把關、路由、分解 |
| **監控** | Dashboard, PredictiveMonitor, ProgressDashboard | 進度、成本、風險 |
| **交付** | DeliveryManager, DocGenerator, TestGenerator | 版本、文檔、測試 |
| **安全** | SecurityAuditor, RBAC, AuditLogger | 審計、權限、軌跡 |
| **企業整合** | CICDIntegration, MultiLanguage, KnowledgeBase | CI/CD、多語言、知識庫 |
| **版本控制** | VersionControl | 版本、Rollback、Diff |

### Extensions (7)

| 模組 | 功能 |
|------|------|
| **mcp_adapter** | 企業服務整合 (Slack, Notion, GitHub) |
| **cost_optimizer** | 成本控制 (省 70-93%) |
| **vertical_templates** | 客服、法律 Agent 模板 |
| **security_audit** | API Key、SQL 注入檢測 |
| **langchain_adapter** | LangChain 遷移工具 |
| **local_deployment** | 本地部署 (隱私合規) |
| **workflow_visualizer** | Mermaid 圖表生成 |

---

## 🏗️ 架構

```
MethodologyCore (統一入口)
    │
    ├── tasks              → 任務分解
    ├── costs              → 成本追蹤
    ├── project            → 專案管理
    ├── workflow           → 工作流引擎
    ├── agents             → Agent Registry
    ├── bus                → Message Bus
    ├── audit              → 審計日誌
    ├── router             → Smart Router + Cost Optimizer
    ├── spawner            → Agent Spawner
    ├── version_control    → 版本控制
    ├── knowledge_base     → 知識庫
    └── extensions         → 企業整合
```

---

## 💡 使用範例

### 完整工作流

```python
from methodology import MethodologyCore, MethodologyConfig

# 初始化
config = MethodologyConfig(
    project_name="AI 客服系統",
    monthly_budget=500
)
core = MethodologyCore(config=config)

# 1. 任務規劃
tasks = core.tasks.split_from_goal("開發 AI 客服系統")
print(f"建立 {len(tasks)} 個子任務")

# 2. Spawn Agents
agent_id = core.spawn_agent("developer", "task-1", "實作登入功能")
print(f"Spawned: {agent_id}")

# 3. 版本控制
v1 = core.commit_version("login-module", "def login(): pass", message="init")
print(f"Version: {v1}")

# 4. 安全掃描
report = core.scan_security("src/login.py")
print(f"Security: {report}")

# 5. 成本追蹤
core.track_cost_usage("gpt-4o", 1000, 500)

# 6. 生成工作流圖表
diagram = core.generate_workflow_diagram()

# 7. 保存
core.save()
```

### CI/CD 整合

```python
from methodology import CICDIntegration

cicd = CICDIntegration()
cicd.setup_all("github")  # GitHub Actions + Docker Compose
```

### 多語言支援

```python
from methodology import MultiLanguageSupport

ml = MultiLanguageSupport()
lang = ml.detect_language("app.py")  # python
route = ml.route_to_agent("build a Go microservice")
```

### 知識庫

```python
from methodology import KnowledgeBase

kb = KnowledgeBase()
pattern = kb.find_similar_scenario("multi-agent coordination")
recs = kb.get_recommendations("debugging")
```

---

## 📖 文件

| 文件 | 說明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 5 分鐘快速上手 |
| [PM_HANDBOOK.md](PM_HANDBOOK.md) | PM 手把手教學 |
| [SKILL.md](SKILL.md) | 技術規格 |
| Extensions/*/SKILL.md | 各 Extension 文檔 |

---

## 🎯 關鍵亮點

| # | 亮點 | 說明 |
|---|------|------|
| 1 | **統一入口** | `MethodologyCore()` 一行初始化 |
| 2 | **AgentCoordination** | 四大核心 (Team/Registry/Communication/State) |
| 3 | **三大核心工具** | Model Router · Agent Monitor · Agent Quality Guard |
| 4 | **成本優化** | 省 70-93% |
| 5 | **企業整合** | MCP + Extensions |
| 6 | **預測監控** | 趨勢預測 + 異常檢測 |
| 7 | **版本控制** | Rollback + Diff |
| 8 | **CI/CD** | GitHub Actions / Jenkins / GitLab CI |
| 9 | **多語言** | Python / JS / Go / Rust |
| 10 | **知識庫** | Pattern + Best Practice |

### 三大核心工具

| 工具 | GitHub |
|------|--------|
| **Model Router** | [model-router-v2](https://github.com/johnnylugm-tech/model-router-v2) |
| **Agent Monitor** | [agent-dashboard-v3](https://github.com/johnnylugm-tech/agent-dashboard-v3) |
| **Agent Quality Guard** | [Agent-Quality-Guard](https://github.com/johnnylugm-tech/Agent-Quality-Guard) |

---

## 📊 版本歷程

| 版本 | 日期 | 功能 |
|------|------|------|
| v4.3.0 | 2026-03-20 | PM 缺口改善 (15/15) |
| v4.2.0 | 2026-03-20 | Extensions 整合 |
| v4.1.0 | 2026-03-20 | 架構優化 + 統一入口 |
| v4.0.0 | 2026-03-20 | AgentCoordination 核心 |
| v3.3.0 | 2026-03-20 | 風險儀表板 |
| v3.2.0 | 2026-03-20 | 交付管理 |

---

## 🤝 貢獻

歡迎提交 Issue 和 PR！

---

## 📄 License

MIT

---

## 🔗 連結

- [GitHub](https://github.com/johnnylugm-tech/methodology-v2)
- [Releases](https://github.com/johnnylugm-tech/methodology-v2/releases)
