# 🎯 PM 手把手手冊：Methodology-v2 完整指南

> 讓傳統 PM 也能用 AI Agent 開發團隊

---

## 📖 目錄

1. [這份手冊是什麼？](#1-這份手冊是什麼)
2. [第一天：基本設定](#2-第一天基本設定)
3. [第二天：專案啟動](#3-第二天專案啟動)
4. [第三天：日常開發](#4-第三天日常開發)
5. [第四天：監控與彙報](#5-第四天監控與彙報)
6. [第五天：風險管理](#6-第五天風險管理)
7. [附錄：快速參考](#7-附錄快速參考)

---

## 1. 這份手冊是什麼？

### 這套系統能做什麼？

```
┌─────────────────────────────────────────┐
│  你 (PM)                                 │
│    ↓ 指揮                               │
│  AI Agent 團隊                          │
│    ↓ 執行                               │
│  自動任務分解 → 執行 → 品質把關 → 監控  │
└─────────────────────────────────────────┘
```

### 你的工作變成：

| 傳統方式 | 用這套系統 |
|----------|-----------|
| 手動拆任務 | AI 自動拆解 |
| 口頭分配 | 系統指派 |
| 看 Log 追進度 | 儀表板監控 |
| Excel 管預算 | 系統自動計算 |

---

## 2. 第一天：基本設定

### 2.1 安裝

```bash
pip install methodology-v2
```

### 2.2 第一次設定

```python
from methodology import (
    RBAC,              # 權限管理
    WorkflowTemplates,  # 工作流程
)

# 建立你的團隊
rbac = RBAC()

# 建立團隊成員
pm = rbac.create_user("小美", "pm@company.com", Role.PROJECT_MANAGER)
dev1 = rbac.create_user("大明", "dev1@company.com", Role.DEVELOPER)
dev2 = rbac.create_user("小明", "dev2@company.com", Role.DEVELOPER)

print("✅ 團隊建立完成！")
```

### 2.3 選擇工作流程

```python
# 建立 Scrum 流程
templates = WorkflowTemplates()
project = templates.create_project("scrum", "我的第一個專案")

print(f"📋 專案：{project['name']}")
print(f"📅 Sprint：{len(project['sprints'])} 個")
```

---

## 3. 第二天：專案啟動

### 3.1 自動拆解任務

```python
from methodology import TaskSplitterV2

# 描述你的目標
splitter = TaskSplitterV2()
splitter.set_project("AI 客服系統")

# AI 自動拆解任務
tasks = splitter.split_from_goal("開發一個 AI 客服系統，需要登入、知識庫、回應功能")

# 看結果
for task in tasks:
    print(f"📌 {task.name} ({task.priority.name})")
```

**輸出範例：**
```
📌 需求分析 (HIGH)
📌 系統設計 (HIGH)
📌 登入功能 (MEDIUM)
📌 知識庫開發 (MEDIUM)
📌 AI 回應邏輯 (MEDIUM)
📌 測試 (MEDIUM)
📌 部署 (LOW)
```

### 3.2 設定里程碑

```python
from datetime import datetime, timedelta

# 加入里程碑
mvp = splitter.add_milestone(
    "MVP 完成",
    datetime.now() + timedelta(days=7)
)

# 把任務 assign 到里程碑
for i, task in enumerate(tasks[:3]):
    task.milestone = mvp

print(f"🎯 里程碑已設定")
```

### 3.3 選擇 AI 模型

```python
from methodology import SmartRouter

# 選擇適合的模型
router = SmartRouter(budget="medium")  # low/medium/high

# 任務會自動選擇適合的模型
result = router.route("幫我寫登入功能")
print(f"🤖 使用模型：{result.model}")
print(f"💰 預估成本：${result.estimated_cost:.4f}")
```

---

## 4. 第三天：日常開發

### 4.1 早上：檢查任務

```python
from methodology import ProgressDashboard

dashboard = ProgressDashboard()

# 建立 Sprint
sprint_id = dashboard.create_sprint(
    "Sprint 1",
    "完成登入功能",
    capacity=30  # 總點數
)
dashboard.start_sprint(sprint_id)

# 加入任務
for task in tasks[:4]:
    item_id = dashboard.add_to_backlog(
        task.name,
        story_points=task.estimated_hours
    )
    dashboard.add_item_to_sprint(item_id, sprint_id)

# 看 Board
board = dashboard.get_sprint_board()
print(f"📊 Sprint: {board['sprint']['name']}")
print(f"   To Do: {board['summary']['todo']} 項")
print(f"   In Progress: {board['summary']['in_progress']} 項")
print(f"   Done: {board['summary']['completed']}項")
```

### 4.2 AI 程式碼品質把關

```python
from methodology import AutoQualityGate

gate = AutoQualityGate(auto_fix=True)  # 自動修復

# 掃描你的程式碼
report = gate.scan("src/login.py")

print(f"📝 檔案：{report.file}")
print(f"問題數：{report.total_issues}")
print(f"嚴重：{report.critical}")
print(f"警告：{report.warning}")

# 如果有問題，自動修復
if report.total_issues > 0:
    gate.auto_fix("src/login.py")
    print("✅ 已自動修復")
```

### 4.3 成本控制

```python
from methodology import CostTrendAnalyzer

analyzer = CostTrendAnalyzer()

# 記錄 API 成本
analyzer.record_api_call(
    model="gpt-4o",
    input_tokens=1000,
    output_tokens=500,
    user_id="大明"
)

# 看趨勢
trends = analyzer.get_trend(7)
summary = analyzer.get_summary(7)

print(f"💰 本週總成本：${summary['total_cost']:.4f}")
print(f"📊 日均：${summary['avg_daily']:.4f}")
print(f"📈 趨勢：{summary['trend_direction']}")
```

---

## 5. 第四天：監控與彙報

### 5.1 即時進度監控

```python
# 產生進度報告
report = dashboard.generate_report()
print(report)
```

**輸出範例：**
```
# 📊 Sprint 進度報告

## Sprint 1

**狀態**: active
**目標**: 完成登入功能
**剩餘**: 3 天

---

## 📈 統計

| 指標 | 數值 |
|------|------|
| 總點數 | 12 |
| 已完成 | 8 |
| 剩餘 | 4 |
| 速度 | 66.7% |
```

### 5.2 成本趨勢報告

```python
# 產生成本報告
report = analyzer.generate_report()
print(report)
```

### 5.3 團隊產能報告

```python
from methodology import PredictiveMonitor

monitor = PredictiveMonitor()

# 記錄團隊產出
monitor.record("tasks_completed", 5)
monitor.record("bugs_fixed", 3)
monitor.record("code_review_time", 2.5)

# 預測
pred = monitor.predict("tasks_completed")
print(f"📈 明天預測完成：{pred.predicted_value:.0f} 個任務")
print(f"💡 {pred.recommendation}")
```

---

## 6. 第五天：風險管理

### 6.1 預測風險

```python
from methodology import RiskDashboard

dashboard = RiskDashboard()

# 更新專案指標
dashboard.update_metrics(
    "ai-project",
    name="AI 客服系統",
    planned_progress=50.0,
    actual_progress=40.0,
    planned_velocity=10.0,
    actual_velocity=8.0,
    planned_budget=50000,
    actual_spend=22000,
)

# 看風險
health = dashboard.get_project_health("ai-project")
print(f"🏥 專案健康：{health['status']}")
print(f"⏰ 進度風險：{health['schedule_risk']}")
print(f"💰 預算風險：{health['budget_risk']}")

# 風險報告
report = dashboard.generate_report()
print(report)
```

### 6.2 故障轉移（系統保護）

```python
from methodology import FailoverManager

manager = FailoverManager()

# 設定模型
manager.register_model("gpt-4o", "GPT-4o", "OpenAI", is_primary=True)
manager.register_model("claude-4", "Claude 4", "Anthropic", is_primary=False)
manager.set_fallback("gpt-4o", "claude-4")

# 執行任務（自動備援）
result = manager.execute_with_failover(
    task_func=your_ai_task,
    primary_model="gpt-4o"
)
```

### 6.3 交付管理

```python
from methodology import DeliveryManager

manager = DeliveryManager()

# 建立交付項目
doc = manager.create_item(
    "登入模組文檔",
    "使用者認證 API 文檔",
    DeliveryType.DOCUMENT,
    author="大明"
)

# 版本管理
manager.bump_version(doc, "minor")

# 提交審核
manager.submit_for_review(doc, reviewers=["小美"])

# 核准
manager.approve(doc, "小美")

# 發布
manager.release(doc)

print("✅ 交付完成！")
```

---

## 7. 附錄：快速參考

### 7.1 PM 一天工作流

```python
# ========== 早上 9:00 - 健康檢查 ==========
from methodology import Dashboard, RiskDashboard

dashboard = Dashboard(mode="light")
risk = RiskDashboard()
health = risk.get_project_health("ai-project")

if health['status'] == 'critical':
    print("🚨 需要緊急處理！")
elif health['status'] == 'warning':
    print("⚠️ 有些問題需要關注")

# ========== 早上 10:00 - 任務分配 ==========
from methodology import TaskSplitterV2, ParallelExecutor

splitter = TaskSplitterV2()
tasks = splitter.split_from_goal("新功能開發")

executor = ParallelExecutor(max_workers=3)
for task in tasks:
    executor.add_task(task.name, task.execute)

executor.execute_all()

# ========== 中午 12:00 - 品質審視 ==========
from methodology import AutoQualityGate

gate = AutoQualityGate(auto_fix=True)
report = gate.scan("src/")
print(f"📊 品質報告：{report.total_issues} 個問題")

# ========== 下午 3:00 - 成本檢視 ==========
from methodology import CostTrendAnalyzer

analyzer = CostTrendAnalyzer()
summary = analyzer.get_summary(7)

if summary['trend_direction'] == 'up':
    print("📈 成本上升中，建議優化")

# ========== 下午 5:00 - 進度彙報 ==========
from methodology import ProgressDashboard

dashboard = ProgressDashboard()
report = dashboard.generate_report()
print(report)
```

### 7.2 常用功能速查表

| 情境 | 功能 | 程式碼 |
|------|------|--------|
| 拆任務 | TaskSplitterV2 | `split_from_goal()` |
| 看進度 | ProgressDashboard | `get_sprint_board()` |
| 檢查品質 | AutoQualityGate | `scan()` |
| 控制成本 | CostTrendAnalyzer | `get_summary()` |
| 預測風險 | RiskDashboard | `get_project_health()` |
| 排程任務 | ParallelExecutor | `execute_all()` |
| 故障轉移 | FailoverManager | `execute_with_failover()` |
| 交付管理 | DeliveryManager | `release()` |

### 7.3 角色權限

```python
from methodology import RBAC, Role

# Admin - 全部權限
admin = rbac.create_user("老闆", Role.ADMIN)

# PM - 任務、Sprint、預算管理
pm = rbac.create_user("小美", Role.PROJECT_MANAGER)

# Developer - 任務執行
dev = rbac.create_user("大明", Role.DEVELOPER)

# Viewer - 僅檢視
viewer = rbac.create_user("訪客", Role.VIEWER)
```

### 7.4 工作流程範本

```python
from methodology import WorkflowTemplates

templates = WorkflowTemplates()

# Scrum (2 週衝刺)
scrumb = templates.get_template("scrum")

# Kanban (持續流動)
kanban = templates.get_template("kanban")

# Spike (研究任務)
spike = templates.get_template("spike")
```

### 7.5 常見問題

**Q: 需要寫很多程式碼嗎？**
A: 只要會 Python 基礎就可以。我們有完整的 API 文件。

**Q: 適合多大的團隊？**
A: 1 人到 100 人都可以。

**Q: 資料存在哪裡？**
A: 預設 SQLite本地資料庫，可設定 PostgreSQL。

**Q: 可以不用 Docker 嗎？**
A: 可以，直接 pip install 就能用。

---

## 📚 更多資源

- [QUICKSTART.md](./QUICKSTART.md) - 5 分鐘快速開始
- [README.md](./README.md) - 完整功能列表
- [GitHub](https://github.com/johnnylugm-tech/methodology-v2) - 原始碼

---

**記住：不用一次學會全部，從一小步開始！** 🚀
