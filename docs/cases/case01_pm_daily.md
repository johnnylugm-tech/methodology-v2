# 案例一：PM 日常專案管理

## 情境描述

身為 AI 專案的專案經理，需要管理開會報告、追蹤進度、控制成本、分配任務。

---

## 案例 1.1：晨間進度報告

### 背景
每早需要向主管匯報昨日進度、今天的規劃、以及任何阻塞點。

### 使用方式

```python
from methodology import MethodologyCore, MethodologyConfig

# 建立 PM 環境
config = MethodologyConfig(
    project_name="AI 客服系統 v2",
    monthly_budget=5000
)
core = MethodologyCore(config=config)

# 1. 檢查昨日任務完成率
yesterday_tasks = [
    {"id": "task-1", "name": "登入功能開發", "status": "completed"},
    {"id": "task-2", "name": "用戶驗證模組", "status": "in_progress"},
    {"id": "task-3", "name": "API 文件", "status": "blocked"},
]

completed = sum(1 for t in yesterday_tasks if t["status"] == "completed")
total = len(yesterday_tasks)
completion_rate = (completed / total) * 100

print(f"昨日完成率: {completion_rate:.0f}%")

# 2. 查看健康狀態
from methodology import Dashboard
dashboard = Dashboard(mode="full")
health = dashboard.get_health_summary()

# 3. 生成晨間報告
report = f"""
# 🌅 晨間報告 - {datetime.now().strftime('%Y-%m-%d')}

## 昨日進度
- 完成: {completed}/{total} ({completion_rate:.0f}%)
- 進行中: 1
- 阻塞: 1

## 健康狀態
- 系統: {health.get('system_status', 'N/A')}
- 警報: {health.get('alert_count', 0)} 個

## 今日規劃
- [ ] 完成用戶驗證模組
- [ ] 解決 API 文件阻塞問題
- [ ] 召開 blocking issue 會議

## 風險事項
⚠️ API 文件依賴外部團隊回應
"""
print(report)
```

### 輸出範例
```
昨日完成率: 33%

# 🌅 晨間報告 - 2026-03-20

## 昨日進度
- 完成: 1/3 (33%)
- 進行中: 1
- 阻塞: 1

## 健康狀態
- 系統: healthy
- 警報: 0 個
```

---

## 案例 1.2：成本追蹤與預算控制

### 背景
每月 API 費用飆升，需要了解各任務的成本分佈。

### 使用方式

```python
from methodology import MethodologyCore, SmartRouter

core = MethodologyCore()

# 設定預算
core.config.monthly_budget = 5000

# 追蹤成本
core.track_cost_usage("gpt-4o", input_tokens=5000, output_tokens=2000)
core.track_cost_usage("claude-3-opus", input_tokens=3000, output_tokens=1500)

# 查詢成本摘要
summary = core.router.get_cost_summary()
print(f"本月支出: ${summary['total_spent']:.2f}")
print(f"剩餘預算: ${summary['remaining']:.2f}")
print(f"使用率: {summary['utilization']:.1f}%")

# 檢查是否超支
if core.router.is_over_budget():
    alert = core.router.get_cost_alert()
    print(f"🚨 {alert['message']}")
```

### 輸出範例
```
本月支出: $1.25
剩餘預算: $4998.75
使用率: 0.025%
```

---

## 案例 1.3：Sprint 規劃與任務分配

### 背景
新 Sprint 開始，需要拆分任務並分配給團隊成員。

### 使用方式

```python
from methodology import TaskSplitterV2, TaskPriority, AgentType

splitter = TaskSplitterV2()

# 定義 Sprint 目標
goal = "在兩週內完成 AI 客服系統的訂單查詢功能"

# 拆分任務
tasks = splitter.split_from_goal(goal)

print(f"拆分為 {len(tasks)} 個子任務:\n")
for i, task in enumerate(tasks, 1):
    print(f"{i}. [{task.priority.name}] {task.name}")
    if task.dependencies:
        print(f"   依賴: {', '.join(task.dependencies)}")

# 分配 Agent
core = MethodologyCore()
for task in tasks:
    # 根據任務類型分配
    if "api" in task.name.lower():
        agent_type = AgentType.DEVELOPER
    elif "test" in task.name.lower():
        agent_type = AgentType.TESTER
    else:
        agent_type = AgentType.DEVELOPER
    
    # 註冊任務
    core.tasks.add_task(
        name=task.name,
        priority=task.priority.value,
        agent_type=agent_type.value
    )
```

### 輸出範例
```
拆分為 6 個子任務:

1. [HIGH] 設計訂單 API 規格
   依賴: -
2. [HIGH] 實作訂單查詢端點
   依賴: 設計訂單 API 規格
3. [MEDIUM] 訂單資料模型
   依賴: 設計訂單 API 規格
4. [MEDIUM] 單元測試
   依賴: 實作訂單查詢端點
5. [LOW] API 文件
   依賴: 實作訂單查詢端點
6. [MEDIUM] 整合測試
   依賴: 單元測試, API 文件
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| 任務拆分 | `TaskSplitterV2` |
| 進度儀表板 | `Dashboard`, `ProgressDashboard` |
| 成本追蹤 | `SmartRouter`, `CostAllocator` |
| 健康監控 | `PredictiveMonitor` |
