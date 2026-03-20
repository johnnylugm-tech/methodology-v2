# Methodology v2 使用手冊

> AI Agent 開發框架 - 從 PoC 到 Production-Ready

---

## 目錄

1. [快速開始](#快速開始)
2. [核心模組](#核心模組)
3. [CLI 命令](#cli-命令)
4. [範例](#範例)
5. [模組 API](#模組-api)
6. [測試](#測試)

---

## 快速開始

### 安裝

```bash
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2
```

### 基本使用

```python
from progress_dashboard import ProgressDashboard
from message_bus import MessageBus
from gantt_chart import GanttChart

# 初始化
dashboard = ProgressDashboard()

# 建立 Sprint
sprint_id = dashboard.create_sprint(
    name="Sprint 1",
    goal="完成核心功能",
    capacity=50
)

# 加入任務
item_id = dashboard.add_to_backlog(
    title="用戶登入功能",
    story_points=5,
    priority=1
)

# 標記完成
dashboard.mark_item_completed(item_id)

# 查詢
print(dashboard.get_sprint_completed_points(sprint_id))
```

---

## 核心模組

### 1. Progress Dashboard - 進度追蹤

追蹤 Sprint、Backlog、Burndown。

```python
from progress_dashboard import ProgressDashboard, BacklogItem, Sprint

dashboard = ProgressDashboard()

# Sprint 管理
sprint_id = dashboard.create_sprint(
    name="Sprint 5",
    goal="發布支付功能",
    capacity=40
)
dashboard.start_sprint(sprint_id)

# Backlog 管理
item_id = dashboard.add_to_backlog(
    title="開發 REST API",
    description="實作 CRUD 操作",
    story_points=8,
    priority=2
)

# 加入 Sprint
dashboard.add_item_to_sprint(item_id, sprint_id)

# 標記完成
dashboard.mark_item_completed(item_id)

# 取得 Sprint 進度
total = dashboard.get_sprint_total_points(sprint_id)
completed = dashboard.get_sprint_completed_points(sprint_id)
velocity = dashboard.get_sprint_velocity(sprint_id)

print(f"Sprint 進度: {completed}/{total} ({velocity:.1f} 點)")
```

### 2. Cost Allocator - 成本管控

追蹤 API 使用成本、計算資源。

```python
from cost_allocator import CostAllocator, CostType, Budget

allocator = CostAllocator()

# 建立預算
allocator.create_budget(
    name="AI Project",
    total_amount=1000.0,
    period="monthly"
)

# 記錄成本
allocator.add_entry(
    project_id="AI Project",
    user_id="user-1",
    cost_type=CostType.API_CALL,
    amount=50.0,
    model="gpt-4"
)

# 查詢成本
costs = allocator.get_project_costs("AI Project")
print(f"總成本: ${costs['total']:.2f}")
print(f"按模型: {costs['by_model']}")

# 預算狀態
status = allocator.get_budget_status()
for b in status:
    print(f"{b['name']}: ${b['spent']:.2f} / ${b['total']:.2f}")
```

### 3. Message Bus - 訊息系統

Pub/Sub 訊息系統。

```python
from message_bus import MessageBus, MessagePriority

bus = MessageBus()

# 發布訊息
bus.publish("tasks/completed", {
    "task_id": "task-1",
    "user": "alice"
}, MessagePriority.HIGH)

# 訂閱主題
def handle_completed(message):
    print(f"任務完成: {message['task_id']}")

bus.subscribe("tasks/completed", handle_completed)

# 查詢狀態
status = bus.get_queue_status()
print(f"佇列大小: {status['queue_size']}")
print(f"已發送: {status['stats']['messages_sent']}")

# CLI 輸出
print(bus.to_cli())
```

### 4. Gantt Chart - 甘特圖

視覺化專案時程。

```python
from gantt_chart import GanttChart, TaskStatus

gantt = GanttChart()

# 加入任務
gantt.add_task(
    task_id="task-1",
    name="需求分析",
    start_date="2026-03-20",
    duration=5,
    status=TaskStatus.COMPLETED,
    assignee="Alice"
)

gantt.add_task(
    task_id="task-2",
    name="系統設計",
    start_date="2026-03-25",
    duration=3,
    depends_on=["task-1"]
)

# 輸出
print(gantt.to_rich_ascii())

# CSV 匯出
print(gantt.to_csv())

# HTML 匯出
gantt.export_interactive_html("/tmp/gantt.html")
```

### 5. PM Mode - PM 日常

晨間報告、成本預測、健康狀況。

```python
from pm_mode import PMMode

pm = PMMode()

# 生成晨間報告
report = pm.generate_morning_report(
    sprint_name="Sprint 5",
    sprint_progress=65.0,
    completed_yesterday=["完成登入", "修復 Bug #123"],
    planned_today=["開發儀表板", "撰寫文件"],
    blockers=["等不及第三方 API 文件"],
    velocity=42.0
)
print(report.to_markdown())

# 成本預測
forecast = pm.predict_cost(
    project_name="AI Assistant",
    current_cost=500.0,
    budget=2000.0,
    daily_burn_rate=85.0,
    days_remaining=18
)
print(forecast.to_markdown())

# Sprint 健康狀況
health = pm.get_sprint_health(
    velocity=35,
    planned=50,
    completed=30
)
print(f"狀態: {health['health']}")
print(f"分數: {health['health_score']}/10")
```

### 6. PM Terminology - 術語對照

統一 PM/開發/Scrum 術語。

```python
from pm_terminology import PMTerminologyMapper, Role

mapper = PMTerminologyMapper()

# 搜尋術語
results = mapper.search("sprint")
for r in results:
    print(f"## {r.pm_term}")
    print(f"- Developer: {r.dev_term}")
    print(f"- Scrum: {r.scrum_term}")
    print(f"- 定義: {r.definition}")

# 翻譯術語
pm_term = mapper.translate("velocity", Role.DEV, Role.PM)
print(f"Dev → PM: {pm_term}")

# 產生報告
print(mapper.to_markdown_table())
```

### 7. Resource Dashboard - 資源管理

管理工具、API、團隊成員。

```python
from resource_dashboard import ResourceDashboard, ResourceType, SkillLevel

dashboard = ResourceDashboard()

# 新增資源
dashboard.add_resource(
    id="openai-api",
    name="OpenAI API",
    type=ResourceType.API,
    description="GPT 模型 API",
    cost=100.0,
    tags=["ai", "llm"]
)

# 加入團隊成員
dashboard.add_team_member(
    resource_id="member-alice",
    name="Alice",
    role="Senior Developer",
    skills={"python": SkillLevel.EXPERT, "ai": SkillLevel.ADVANCED}
)

# 輸出
print(dashboard.to_table())

# 摘要
summary = dashboard.get_resource_summary()
print(f"總資源: {summary['total']}")
print(f"月成本: ${summary['total_monthly_cost']:.2f}")

# 團隊技能矩陣
matrix = dashboard.get_team_skills_matrix()
for skill, members in matrix.items():
    print(f"{skill}: {', '.join(members)}")
```

---

## CLI 命令

使用 `cli.py` 統一介面：

```bash
# 初始化專案
python cli.py init "my-project"

# 任務管理
python cli.py task add "新功能" --points 5 --priority 2
python cli.py task list
python cli.py task complete task-1

# Sprint 管理
python cli.py sprint create "Sprint 1" --start 2026-03-20 --end 2026-04-02 --capacity 40
python cli.py sprint list

# 視覺化看板
python cli.py board

# 報告
python cli.py report --type weekly

# 狀態
python cli.py status

# Message Bus
python cli.py bus status
python cli.py bus tree

# 術語查詢
python cli.py term velocity

# 資源儀表板
python cli.py resources list
python cli.py resources stats
python cli.py resources skills

# PM Mode
python cli.py pm report      # 晨間報告
python cli.py pm forecast    # 成本預測
python cli.py pm health      # Sprint 健康

# 版本
python cli.py version
```

---

## 範例

### 完整工作流

```python
from progress_dashboard import ProgressDashboard
from message_bus import MessageBus
from gantt_chart import GanttChart, TaskStatus
from cost_allocator import CostAllocator, CostType
from pm_mode import PMMode

# 初始化所有模組
dashboard = ProgressDashboard()
bus = MessageBus()
gantt = GanttChart()
allocator = CostAllocator()
pm = PMMode()

# 1. 建立 Sprint
sprint_id = dashboard.create_sprint(
    name="Sprint 5",
    goal="發布 AI Assistant v1.0",
    capacity=50
)
dashboard.start_sprint(sprint_id)

# 2. 加入任務到 Backlog 和 Gantt
tasks = [
    ("需求分析", 3, "2026-03-20"),
    ("系統設計", 5, "2026-03-23"),
    ("開發登入", 8, "2026-03-26"),
    ("開發儀表板", 13, "2026-04-02"),
    ("測試部署", 5, "2026-04-09"),
]

for i, (name, points, start) in enumerate(tasks):
    task_id = f"task-{i+1}"
    dashboard.add_to_backlog(title=name, story_points=points)
    gantt.add_task(
        task_id=task_id,
        name=name,
        start_date=start,
        duration=points,
        status=TaskStatus.PLANNED
    )
    bus.publish("tasks/created", {"task_id": task_id, "name": name})

# 3. 模擬開發過程
for i in range(3):
    item_id = f"item-{i+1}"
    dashboard.mark_item_completed(item_id)
    bus.publish("tasks/completed", {"task_id": item_id})

# 4. 記錄成本
allocator.create_budget("AI Assistant", 2000.0, "project")
allocator.add_entry("AI Assistant", "user-1", CostType.API_CALL, 150.0)

# 5. 生成報告
report = pm.generate_morning_report(
    sprint_name="Sprint 5",
    sprint_progress=60.0,
    completed_yesterday=["需求分析", "系統設計"],
    planned_today=["開發登入功能"],
    blockers=[],
    velocity=45.0
)

print(report.to_markdown())
print(gantt.to_rich_ascii())
print(allocator.generate_report())
```

### 多人協作

```python
from message_bus import MessageBus, MessagePriority
from resource_dashboard import ResourceDashboard, SkillLevel

# 初始化
bus = MessageBus()
resources = ResourceDashboard()

# 團隊成員
resources.add_team_member(
    resource_id="alice",
    name="Alice",
    role="Tech Lead",
    skills={"python": SkillLevel.EXPERT, "architecture": SkillLevel.ADVANCED}
)
resources.add_team_member(
    resource_id="bob",
    name="Bob",
    role="Developer",
    skills={"python": SkillLevel.ADVANCED, "testing": SkillLevel.INTERMEDIATE}
)

# 事件訂閱
def on_task_assigned(message):
    print(f"任務分配: {message['task_id']} → {message['assignee']}")

bus.subscribe("tasks/assigned", on_task_assigned)

# 分發任務
bus.publish("tasks/assigned", {
    "task_id": "task-1",
    "assignee": "alice",
    "story_points": 5
}, MessagePriority.HIGH)

bus.publish("tasks/assigned", {
    "task_id": "task-2",
    "assignee": "bob",
    "story_points": 3
}, MessagePriority.NORMAL)

# 技能矩陣
print(resources.to_table())
```

---

## 模組 API

### ProgressDashboard

| 方法 | 說明 |
|------|------|
| `create_sprint(name, goal, capacity)` | 建立 Sprint |
| `start_sprint(sprint_id)` | 開始 Sprint |
| `add_to_backlog(title, story_points, priority)` | 加入 Backlog |
| `add_item_to_sprint(item_id, sprint_id)` | 指派到 Sprint |
| `mark_item_completed(item_id)` | 標記完成 |
| `get_sprint_total_points(sprint_id)` | 取得總點數 |
| `get_sprint_completed_points(sprint_id)` | 取得完成點數 |
| `get_sprint_velocity(sprint_id)` | 取得速度 |
| `save(path)` / `load(path)` | 持久化 |

### CostAllocator

| 方法 | 說明 |
|------|------|
| `create_budget(name, total_amount, period)` | 建立預算 |
| `add_entry(project_id, user_id, cost_type, amount)` | 新增成本 |
| `get_project_costs(project_id)` | 專案成本 |
| `get_user_costs(user_id)` | 用戶成本 |
| `get_budget_status()` | 預算狀態 |
| `generate_report()` | 生成報告 |

### MessageBus

| 方法 | 說明 |
|------|------|
| `publish(topic, payload, priority)` | 發布訊息 |
| `subscribe(topic, callback)` | 訂閱主題 |
| `get_queue_status()` | 佇列狀態 |
| `to_cli()` / `to_tree()` | CLI 輸出 |

### GanttChart

| 方法 | 說明 |
|------|------|
| `add_task(task_id, name, start_date, duration)` | 加入任務 |
| `to_rich_ascii()` | ASCII 輸出 |
| `to_csv()` | CSV 輸出 |
| `to_interactive_html(filename)` | HTML 輸出 |
| `get_summary()` | 摘要統計 |

### PMMode

| 方法 | 說明 |
|------|------|
| `generate_morning_report(...)` | 生成晨間報告 |
| `predict_cost(...)` | 成本預測 |
| `get_sprint_health(...)` | 健康狀況 |

### PMTerminologyMapper

| 方法 | 說明 |
|------|------|
| `search(query)` | 搜尋術語 |
| `get(term_id)` | 依 ID 取得 |
| `translate(term, from_role, to_role)` | 翻譯 |
| `to_markdown_table()` | Markdown 表格 |

### ResourceDashboard

| 方法 | 說明 |
|------|------|
| `add_resource(...)` | 新增資源 |
| `get_resources_by_type(type)` | 依類型取得 |
| `add_team_member(...)` | 加入團隊成員 |
| `get_resource_summary()` | 資源摘要 |
| `to_table()` | 表格輸出 |

---

## 測試

### 執行測試

```bash
# 所有測試
python -m unittest tests.test_modules -v

# 個別模組測試
python -m unittest tests.test_modules.TestProgressDashboard -v
python -m unittest tests.test_modules.TestCostAllocator -v
python -m unittest tests.test_modules.TestMessageBus -v
python -m unittest tests.test_modules.TestGanttChart -v
python -m unittest tests.test_modules.TestPMMode -v
python -m unittest tests.test_modules.TestPMTerminology -v
python -m unittest tests.test_modules.TestResourceDashboard -v
```

### 測試覆蓋

| 模組 | 測試數 |
|------|--------|
| ProgressDashboard | 5 |
| CostAllocator | 4 |
| MessageBus | 5 |
| GanttChart | 4 |
| PMMode | 4 |
| PMTerminology | 4 |
| ResourceDashboard | 5 |
| **總計** | **32** |

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.0.0 | 2026-03-20 | PM Mode + Real Data Connectors |
| v4.9.0 | 2026-03-20 | PM Terminology + Resource Dashboard |
| v4.8.0 | 2026-03-20 | CLI Interface |
| v4.7.0 | 2026-03-20 | P1 Visualizations |
| v4.6.2 | 2026-03-20 | P0 Bug Fixes |

---

## 許可

MIT License
