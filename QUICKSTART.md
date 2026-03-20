# 🚀 Methodology-v2 快速上手指南

> 5 分鐘入門，成為 AI Agent 開發專家

---

## 📖 這份指南是什麼？

**Methodology-v2** 是一套讓團隊用 AI Agent 開發軟體的完整方法論。

---

## 🎯 你會學到

| 時間 | 內容 |
|------|------|
| 5 分鐘 | 安裝 + 第一個範例 |
| 15 分鐘 | 核心功能實作 |
| 30 分鐘 | Extensions 企業整合 |
| 60 分鐘 | 完整專案開發 |

---

## 1️⃣ 安裝 (2 分鐘)

```bash
pip install methodology-v2
```

或從 GitHub：

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2
cd methodology-v2
pip install -e .
```

---

## 2️⃣ 統一入口 (3 分鐘)

**最簡單的開始方式：**

```python
from methodology import MethodologyCore

# 建立核心
core = MethodologyCore()

# 任務管理
core.tasks.split_from_goal("開發 AI 客服系統")

# Agent 注册
core.agents.register("dev-1", "Developer", AgentType.DEVELOPER)

# 發布事件
core.publish_event("task:created", {"task": "新任務"})

# 審計日誌
core.log_action("create", "task")
```

---

## 3️⃣ 核心功能

### 3.1 任務分解

```python
from methodology import TaskSplitterV2

splitter = TaskSplitterV2()
tasks = splitter.split_from_goal("開發 AI 客服系統")

for task in splitter.get_execution_order():
    print(f"📌 {task.name} ({task.priority.name})")
```

### 3.2 工作流程

```python
from methodology import WorkflowTemplates, WorkflowType

templates = WorkflowTemplates()
project = templates.create_project("scrum", "我的第一個專案")

print(f"Sprints: {[s['name'] for s in project['sprints']]}")
```

### 3.3 進度追蹤

```python
from methodology import ProgressDashboard

dashboard = ProgressDashboard()
sprint_id = dashboard.create_sprint("Sprint 1", "MVP 完成", capacity=50)
dashboard.start_sprint(sprint_id)

print(dashboard.generate_report())
```

---

## 4️⃣ Extensions 企業整合

### 4.1 MCP 企業服務整合

```python
from methodology import MCPAdapter

adapter = MCPAdapter()
adapter.connect("slack", token="xoxb-xxx")
result = adapter.execute("發送訊息到 #general")
```

### 4.2 成本優化

```python
from methodology import CostOptimizer

optimizer = CostOptimizer(monthly_budget=100)
optimizer.track(model="gpt-4o", prompt_tokens=1000, completion_tokens=500)

# 自動選擇最便宜模型
model = optimizer.select_model("simple_summary", required_quality="medium")
print(f"使用模型: {model}")  # 省 70-93%
```

### 4.3 垂直領域模板

```python
from methodology import CustomerServiceAgent, LegalAgent

# 客服機器人
cs = CustomerServiceAgent(knowledge_base="docs/")
result = cs.handle("我要退貨")

# 法律 Agent
legal = LegalAgent(jurisdiction="TW")
analysis = legal.analyze_contract("合約.txt")
```

### 4.4 安全審計

```python
from methodology import SecurityAuditor

auditor = SecurityAuditor()
report = auditor.scan("code.py")
print(f"嚴重問題: {len(report.critical_issues)}")
```

### 4.5 工作流視覺化

```python
from methodology import WorkflowVisualizer

viz = WorkflowVisualizer()
mermaid = viz.generate_diagram(
    agents=["researcher", "coder", "reviewer"],
    process="sequential"
)
print(mermaid)
```

---

## 5️⃣ 完整範例

```python
from methodology import MethodologyCore

# 初始化
core = MethodologyCore()

# 1. 建立專案
core.config.project_name = "AI 客服系統"

# 2. 注册團隊
from methodology import AgentType
core.agents.register("architect", "架構師", AgentType.ARCHITECT)
core.agents.register("dev-1", "開發者", AgentType.DEVELOPER)
core.agents.register("tester", "測試員", AgentType.TESTER)

# 3. 分解任務
tasks = core.tasks.split_from_goal("開發 AI 客服系統")

# 4. 建立工作流
workflow = core.workflow
workflow.add_node("design", "系統設計")
workflow.add_node("backend", "後端開發", depends_on=["design"])
workflow.add_edge("design", "backend")

# 5. 追蹤成本
core.track_cost(0.05, user_id="dev-1", model="gpt-4o")

# 6. 發布事件
core.publish_event("project:started", {"name": "AI 客服系統"})

# 7. 保存
core.save()

print("✅ 專案建立完成！")
```

---

## 6️⃣ 常見問題

### Q: 需要多少 Python 經驗？
A: 基礎即可。我們有完整的 API 文件。

### Q: 可以只用一部分功能嗎？
A: 可以！每個模組都是獨立的。

### Q: 資料存在哪裡？
A: SQLite (本地)，可設定 PostgreSQL。

### Q: 支援哪些模型？
A: GPT-4、Claude、Gemini、MiniMax 等 20+ 模型。

---

## 📚 學習路徑

```
Day 1: 基礎
├── 安裝完成
├── 跑第一個範例
└── 使用核心模組

Day 2-3: 企業整合
├── MCP 適配器
├── 成本優化
└── 安全審計

Day 4-5: 進階
├── Multi-Agent 協調
├── 工作流自動化
└── 部署上線
```

---

## 🔗 相關連結

- [完整文檔](./README.md)
- [PM 手冊](./PM_HANDBOOK.md)
- [GitHub](https://github.com/johnnylugm-tech/methodology-v2)

---

**記住：從一小步開始！** 🚀
