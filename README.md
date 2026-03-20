# 🎯 Methodology-v2

> Multi-Agent Collaboration Development Framework
> 企業級 AI Agent 開發框架

---

[![Version](https://img.shields.io/badge/version-v4.1.0-blue.svg)](https://github.com/johnnylugm-tech/methodology-v2)
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
core.tasks.split_from_goal("開發 AI 客服系統")
core.agents.register("dev-1", "Developer", AgentType.DEVELOPER)
core.publish_event("project:started", {})
```

---

## 📚 功能概覽

### 核心模組 (37+)

| 類別 | 模組 | 功能 |
|------|------|------|
| **Agent 協調** | AgentTeam, AgentRegistry, MessageBus | 定義、注册、通訊 |
| **執行** | WorkflowGraph, Scheduler, ParallelExecutor | DAG 工作流、排程 |
| **品質** | AutoQualityGate, SmartRouter, TaskSplitterV2 | 把關、路由、分解 |
| **監控** | Dashboard, PredictiveMonitor, ProgressDashboard | 進度、成本、風險 |
| **交付** | DeliveryManager, DocGenerator, TestGenerator | 版本、文檔、測試 |
| **安全** | SecurityAuditor, RBAC, AuditLogger | 審計、權限、軌跡 |

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
    ├── AgentTeam       → Agent 定義
    ├── AgentRegistry   → Agent 注册
    ├── MessageBus      → Agent 通訊
    ├── WorkflowGraph   → 工作流引擎
    ├── Scheduler      → 任務排程
    ├── AutoQualityGate → 品質把關
    ├── SmartRouter    → 模型路由
    ├── Dashboard      → 監控儀表板
    └── Extensions     → 企業整合
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

## 💡 使用範例

### 任務管理

```python
from methodology import TaskSplitterV2

splitter = TaskSplitterV2()
tasks = splitter.split_from_goal("開發 AI 系統")

for task in splitter.get_execution_order():
    print(f"{task.id}: {task.name}")
```

### 工作流

```python
from methodology import WorkflowGraph

wf = WorkflowGraph(name="AI 開發")
wf.add_node("design", "系統設計")
wf.add_node("backend", "後端", depends_on=["design"])
execution = wf.execute()
```

### 成本追蹤

```python
from methodology import CostOptimizer

optimizer = CostOptimizer(monthly_budget=100)
optimizer.track(model="gpt-4o", prompt_tokens=1000, completion_tokens=500)
```

### MCP 整合

```python
from methodology import MCPAdapter

adapter = MCPAdapter()
adapter.connect("slack", token="xoxb-xxx")
result = adapter.execute("發送訊息")
```

---

## 🔧 配置

```python
from methodology import MethodologyCore, MethodologyConfig

config = MethodologyConfig(
    project_name="My Project",
    monthly_budget=500,
    enable_audit=True,
    enable_monitoring=True,
)

core = MethodologyCore(config=config)
```

---

## 📊 版本歷程

| 版本 | 日期 | 功能 |
|------|------|------|
| v4.1.0 | 2026-03-20 | Extensions 整合、統一入口 |
| v4.0.0 | 2026-03-20 | 企業 Extensions |
| v3.3.0 | 2026-03-20 | AgentCoordination 四核心 |
| v3.0.0 | 2026-03-20 | Phase 1-3 完整實作 |

---

## 🤝 貢獻

歡迎提交 Issue 和 PR！

---

## 📄 License

MIT

---

## 🔗 連結

- [GitHub](https://github.com/johnnylugm-tech/methodology-v2)
- [PyPI](https://pypi.org/project/methodology-v2)
- [文件](https://github.com/johnnylugm-tech/methodology-v2#readme)
