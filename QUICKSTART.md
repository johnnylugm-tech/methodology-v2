# 🚀 Methodology-v2 快速上手

> 5 分鐘學會企業級 AI Agent 開發框架

---

## 1️⃣ 安裝 (30秒)

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

## 2️⃣ 第一個範例 (1分鐘)

### 最簡單的使用

```python
from methodology import MethodologyCore

# 1行代碼啟動
core = MethodologyCore()

# 拆分任務
tasks = core.tasks.split_from_goal("開發 AI 客服系統")
print(f"建立了 {len(tasks)} 個子任務")
```

### 完整工作流

```python
from methodology import MethodologyCore

core = MethodologyCore()

# 1. 拆分任務
tasks = core.tasks.split_from_goal("開發 AI 客服系統")

# 2. 註冊 Agent
core.agents.register("dev-1", "Developer", AgentType.DEVELOPER)

# 3. 發布事件
core.publish_event("project:started", {"tasks": len(tasks)})

# 4. 追蹤成本
core.track_cost_usage("gpt-4o", 1000, 500)

# 5. 保存狀態
core.save()
```

---

## 3️⃣ 十大常見情境

### 情境 A：PM 日常管理

```python
from methodology import SprintPlanner, StoryStatus

# 建立 Sprint Planner
planner = SprintPlanner()

# 建立 Sprint
sprint = planner.create_sprint(
    name="Sprint 1",
    start="2026-03-20",
    end="2026-04-02",
    goal="完成用戶登入功能",
    capacity=30  # 30 story points
)

# 加入 Stories
planner.add_story("用戶登入", size="M", assignee="Alice")
planner.add_story("用戶註冊", size="L", assignee="Bob")

# 開始 Sprint
planner.start_sprint("sprint-1")

# 更新狀態
planner.update_story_status("story-1", StoryStatus.DONE)

# 生成報告
print(planner.generate_sprint_report("sprint-1"))
```

---

### 情境 B：智慧模型選擇

```python
from methodology import SmartRouter

router = SmartRouter()

# 任務自動路由
result = router.route("幫我寫一個 Python 函數")
print(f"選擇模型: {result.model}")
print(f"預估成本: ${result.estimated_cost:.4f}")

# 手動選擇最便宜的
model = router.select_cost_efficient_model("翻譯任務", required_quality="low")
print(f"選擇: {model}")

# 查看節省了多少
savings = router.calculate_savings()
for s in savings['scenarios']:
    print(f"{s['scenario']}: 節省 {s['savings_rate']}%")
```

---

### 情境 C：Agent 團隊建立

```python
from methodology import AgentTeam, AgentRole, AgentCapability

team = AgentTeam(name="開發團隊")

# 定義 Developer
dev = AgentDefinition(
    name="Backend Developer",
    role=AgentRole.DEVELOPER,
    capabilities=[AgentCapability.CODING, AgentCapability.API_DESIGN]
)

# 定義 Reviewer
reviewer = AgentDefinition(
    name="Code Reviewer",
    role=AgentRole.REVIEWER,
    capabilities=[AgentCapability.CODE_REVIEW, AgentCapability.SECURITY]
)

team.register(dev)
team.register(reviewer)

# 查詢可用 Agent
available = team.get_available_agents(role=AgentRole.DEVELOPER)
print(f"可用 Developer: {len(available)}")
```

---

### 情境 D：品質把關

```python
from methodology import AutoQualityGate

gate = AutoQualityGate()

# 掃描程式碼
report = gate.scan("src/login.py")

print(f"品質分數: {report.score}/100")
print(f"問題數量: {len(report.issues)}")

# 顯示問題
for issue in report.issues:
    print(f"[{issue.severity}] {issue.message}")

# 自動修復
if report.score < 80:
    fixed = gate.fix(report)
    print(f"已修復: {fixed['success']}/{fixed['total']}")
```

---

### 情境 E：甘特圖規劃

```python
from methodology import GanttChart

gantt = GanttChart()

# 加入任務
gantt.add_task("設計", start="2026-03-20", duration=2, assignee="Alice")
gantt.add_task("開發", start="2026-03-22", duration=3, depends_on=["設計"], assignee="Bob")
gantt.add_task("測試", start="2026-03-25", duration=2, depends_on=["開發"], assignee="Charlie")

# 加入里程碑
gantt.add_milestone("Beta", "2026-03-27", depends_on=["測試"])

# 產生圖表
print(gantt.to_ascii())
```

---

### 情境 F：Agent 生命週期

```python
from methodology import AgentLifecycleViewer, AgentLifecycleState

viewer = AgentLifecycleViewer()

# 註冊 Agent
viewer.register("dev-1", "Developer", "developer")

# 模擬工作
viewer.task_started("dev-1", "task-1", "實作登入")
viewer.task_completed("dev-1", success=True)

# 查看狀態
view = viewer.get_lifecycle_view("dev-1")
print(f"狀態: {view['current_state']}")
print(f"完成任務: {view['tasks_completed']}")

# 產生狀態圖
print(viewer.to_mermaid())
```

---

### 情境 G：資源監控

```python
from methodology import ResourceDashboard, ResourceType

dashboard = ResourceDashboard()

# 新增資源
dashboard.add_resource("gpu-1", "NVIDIA A100", ResourceType.GPU, capacity=100)
dashboard.add_resource("agent-pool", "Developer Pool", ResourceType.AGENT, capacity=20)

# 更新使用量
dashboard.update_usage("gpu-1", percentage=75)
dashboard.update_usage("agent-pool", tasks=15)

# 生成報告
print(dashboard.generate_report())
```

---

### 情境 H：錯誤分類處理

```python
from methodology_base import ErrorClassifier, ErrorLevel

classifier = ErrorClassifier()

# 分類錯誤
errors = [
    Exception("Invalid input: email format"),
    Exception("Connection timeout"),
    Exception("Database unavailable"),
]

for error in errors:
    level = classifier.classify(error)
    print(f"{error}: {level.value}")
```

---

### 情境 I：CI/CD 建立

```python
from methodology import CICDIntegration

cicd = CICDIntegration(project_path="/path/to/project")

# 一鍵建立 GitHub Actions
cicd.setup_all("github")

# 或手動
cicd.create_github_actions_workflow(
    workflow_name="CI/CD",
    python_version="3.11"
)

# 建立 docker-compose
with open("docker-compose.yml", 'w') as f:
    f.write(cicd.generate_docker_compose())
```

---

### 情境 J：版本控制與回滾

```python
from methodology import DeliveryTracker

tracker = DeliveryTracker()

# 提交版本
v1 = tracker.commit("login-module", "def login(): return True", message="init")
v2 = tracker.commit("login-module", "def login(mfa=False): return True", message="add MFA")

print(f"目前版本: {tracker.get_version('login-module')}")

# 標記穩定版本
tracker.tag_version("login-module", "v1.0.0", "stable")

# 回滾
rollback = tracker.rollback("login-module", "v1.0.0", reason="Found bug")
print(f"回滾到: {rollback}")
```

---

## 4️⃣ 速查表

### 常用類別

| 類別 | 用途 |
|------|------|
| `MethodologyCore` | 統一入口 |
| `SmartRouter` | 模型路由 |
| `AutoQualityGate` | 品質把關 |
| `SprintPlanner` | Sprint 管理 |
| `GanttChart` | 甘特圖 |
| `AgentLifecycleViewer` | Agent 生命週期 |
| `ResourceDashboard` | 資源監控 |
| `DeliveryTracker` | 版本控制 |
| `CICDIntegration` | CI/CD |
| `KnowledgeBase` | 知識庫 |

### 常見任務

| 任務 | 一行代碼 |
|------|----------|
| 拆分任務 | `core.tasks.split_from_goal("...")` |
| 註冊 Agent | `core.agents.register("id", "name", type)` |
| 追蹤成本 | `core.track_cost_usage(model, in, out)` |
| 安全掃描 | `core.scan_security("path")` |
| 生成圖表 | `gantt.to_mermaid()` |
| 查看狀態 | `viewer.get_all_status()` |

---

## 5️⃣ 下一步

- 📖 [完整文檔](docs/NEW_TEAM_GUIDE.md) - 新團隊入門指南
- 📚 [案例文檔](docs/cases/README.md) - 18 個實作案例
- 📘 [PM 手冊](PM_HANDBOOK.md) - 專案管理手冊
- 🔧 [技術規格](SKILL.md) - API 詳細說明

---

**準備好了嗎？從選擇你的情境開始！**
