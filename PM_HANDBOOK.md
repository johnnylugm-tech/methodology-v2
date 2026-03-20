# 📊 PM 工作手冊

> 專案經理使用 Methodology-v2 的完整指南

---

## 1️⃣ 每日工作流

### 晨間 30 分鐘

```python
from methodology import MethodologyCore, SprintPlanner, ResourceDashboard

core = MethodologyCore()

# 1. 檢查團隊狀態 (5 min)
from methodology import AgentLifecycleViewer
viewer = AgentLifecycleViewer()

print("=== Agent 狀態 ===")
status = viewer.get_all_status()
print(f"總數: {status['total']}")
for state, agents in status['agents'].items():
    if agents:
        print(f"  {state}: {len(agents)}")

# 2. 檢查資源 (5 min)
from methodology import ResourceDashboard
dashboard = ResourceDashboard()
print("\n=== 資源狀態 ===")
print(dashboard.generate_report())

# 3. Sprint 進度 (10 min)
planner = SprintPlanner()
active_sprints = [s for s in planner.sprints.values() if s.is_active]
for sprint in active_sprints:
    summary = planner.get_sprint_summary(sprint.id)
    print(f"\n{sprint.name}:")
    print(f"  完成率: {summary['completion_rate']:.0f}%")
    print(f"  剩餘天數: {sprint.remaining_days}")

# 4. 生成晨間報告 (10 min)
print("\n=== 晨間報告 ===")
from datetime import datetime
print(f"日期: {datetime.now().strftime('%Y-%m-%d')}")
print(f"重點: 請根據上述數據填寫")
```

### 日間工作

| 時間 | 任務 | 工具 |
|------|------|------|
| 09:00 | 晨間站會 | Dashboard |
| 10:00 | 任務分配 | AgentTeam |
| 12:00 | 品質審視 | AutoQualityGate |
| 15:00 | 成本檢視 | SmartRouter |
| 17:00 | 進度更新 | SprintPlanner |

---

## 2️⃣ Sprint 規劃

### 建立 Sprint

```python
from methodology import SprintPlanner, StoryStatus

planner = SprintPlanner()

# 1. 建立 Sprint
sprint = planner.create_sprint(
    name="Sprint 23",
    start="2026-03-20",
    end="2026-04-02",
    goal="完成用戶模組 v2",
    capacity=40  # 40 story points
)

# 2. 加入 Stories
stories = [
    ("用戶登入", "M", "Alice"),
    ("用戶註冊", "L", "Bob"),
    ("密碼重置", "M", "Alice"),
    ("個人資料", "S", "Charlie"),
    ("頭像上傳", "M", "Bob"),
]

for title, size, assignee in stories:
    story = planner.add_story(title, size=size, assignee=assignee)
    planner.assign_to_sprint(story.id, sprint.id)

# 3. 開始 Sprint
planner.start_sprint(sprint.id)

print(f"Sprint '{sprint.name}' 已建立")
print(f"容量: {sprint.capacity_points} points")
print(f"Stories: {len(stories)}")
```

### Sprint 報告

```python
# 生成每日報告
report = planner.generate_sprint_report(sprint.id)
print(report)

# Burndown Chart
burndown = planner.generate_burndown_chart(sprint.id)
print(f"\n燃盡圖:")
print(f"總點數: {burndown['total_points']}")
print(f"標籤: {burndown['labels']}")
```

---

## 3️⃣ 成本管理

### 設定預算

```python
from methodology import SmartRouter

router = SmartRouter()

# 設定月度預算
router.DEFAULT_CONFIG["monthly_budget"] = 5000  # $5000

# 追蹤使用
router.track_usage("gpt-4o", input_tokens=50000, output_tokens=25000)

# 查看摘要
summary = router.get_cost_summary()
print(f"本月支出: ${summary['total_spent']:.2f}")
print(f"剩餘預算: ${summary['remaining']:.2f}")
print(f"使用率: {summary['utilization']:.1f}%")

# 檢查超支
if router.is_over_budget():
    alert = router.get_cost_alert()
    print(f"⚠️ {alert['message']}")
```

### 省錢策略

```python
# 查看節省了多少
savings = router.calculate_savings()
print("=== 節省成本計算 ===")
for s in savings['scenarios']:
    print(f"{s['scenario']}:")
    print(f"  直接 GPT-4: ${s['direct_cost']}")
    print(f"  優化後: ${s['final_cost']}")
    print(f"  節省: {s['savings_rate']}%")
```

---

## 4️⃣ 品質把關

### 自動掃描

```python
from methodology import AutoQualityGate

gate = AutoQualityGate()

# 掃描程式碼
report = gate.scan("src/auth/login.py")

print(f"品質分數: {report.score}/100")
print(f"發現 {len(report.issues)} 個問題")

# 顯示高風險問題
high_risk = [i for i in report.issues if i.severity == "HIGH"]
if high_risk:
    print(f"\n⚠️ 高風險問題 ({len(high_risk)}):")
    for issue in high_risk:
        print(f"  - {issue.message}")

# 自動修復
if report.score < 80:
    result = gate.auto_fix_with_security("src/auth/login.py")
    print(f"\n修復結果: {result['fixed']}/{result['total']}")
```

---

## 5️⃣ 資源監控

### 全域資源視圖

```python
from methodology import ResourceDashboard, ResourceType

dashboard = ResourceDashboard()

# 新增資源
dashboard.add_resource("gpu-1", "NVIDIA A100", ResourceType.GPU, 
                      capacity=100, cost_per_hour=2.50)
dashboard.add_resource("agent-pool", "Developer Pool", ResourceType.AGENT,
                      capacity=20, max_concurrent_tasks=20)
dashboard.add_resource("memory-1", "128GB RAM", ResourceType.MEMORY,
                      capacity=128, cost_per_hour=0.30)

# 更新使用量
dashboard.update_usage("gpu-1", percentage=65)
dashboard.update_usage("agent-pool", tasks=12)

# 生成報告
print(dashboard.generate_report())
```

### Agent 生命週期

```python
from methodology import AgentLifecycleViewer, AgentLifecycleState

viewer = AgentLifecycleViewer()

# 註冊並管理 Agent
viewer.register("pm-agent", "PM Assistant", "pm")
viewer.register("dev-agent-1", "Developer 1", "developer")
viewer.register("dev-agent-2", "Developer 2", "developer")
viewer.register("qa-agent", "QA Engineer", "tester")

# 模擬工作
viewer.task_started("dev-agent-1", "task-1", "實作用戶模組")
viewer.task_started("dev-agent-2", "task-2", "實作用戶介面")

# 查看狀態
print(viewer.to_ascii_diagram())
```

---

## 6️⃣ 版本與交付

### DeliveryTracker

```python
from methodology import DeliveryTracker

tracker = DeliveryTracker()

# 註冊交付物
tracker.register_artifact("auth-module", "認證模組", "code")

# 提交版本
v1 = tracker.commit("auth-module", "def login(): pass", 
                   author="dev@company.com", message="init")
v2 = tracker.commit("auth-module", "def login(mfa=True): pass",
                   author="dev@company.com", message="add MFA")
v3 = tracker.commit("auth-module", "def login(mfa=True, remember=False): pass",
                   author="dev@company.com", message="add remember")

# 標記版本
tracker.tag_version("auth-module", "v1.0.0", "stable")
tracker.tag_version("auth-module", "v1.0.0", "release")

# 版本比較
comp = tracker.compare_versions("auth-module")
print(f"總版本數: {comp['total_versions']}")

# 回滾
rollback = tracker.rollback("auth-module", "v1.0.0", reason="Security issue")
print(f"已回滾到: {rollback}")
```

---

## 7️⃣ 緊急應變

### 問題發生時

```python
from methodology_base import ErrorClassifier, ErrorHandler

classifier = ErrorClassifier()
handler = ErrorHandler()

# 分類錯誤
error = Exception("API timeout after 30s")
level = classifier.classify(error)

print(f"錯誤等級: {level.value}")

# 取得處理建議
action = handler.get_action(level)
print(f"建議動作: {action}")

# 根據等級處理
if level == ErrorLevel.L4:
    # 觸發熔斷
    from methodology import FailoverManager
    failover = FailoverManager()
    failover.trigger_circuitbreaker("api-service")
    print("⚠️ 熔斷器已觸發")
```

### 監控警報

```python
from methodology import PredictiveMonitor

monitor = PredictiveMonitor()

# 記錄指標
for i in range(20):
    monitor.record("error_rate", 0.5 + i * 0.1)

# 預測
pred = monitor.predict("error_rate", horizon=5)
if pred:
    print(f"預測錯誤率: {pred.predicted_value:.2f}%")
    print(f"置信度: {pred.confidence:.0%}")
    print(f"趨勢: {pred.trend}")
    
    if pred.confidence > 0.8 and pred.predicted_value > 2.0:
        print("⚠️ 警告: 錯誤率將顯著上升!")
```

---

## 8️⃣ PM 速查清單

### 每日檢查清單

- [ ] 晨間站會 (Agent 狀態)
- [ ] Sprint 進度 (Burndown)
- [ ] 資源使用 (Dashboard)
- [ ] 成本追蹤 (Router)
- [ ] 品質報告 (QualityGate)

### 每週檢查清單

- [ ] Sprint 回顧
- [ ] Velocity 分析
- [ ] 成本檢視
- [ ] 風險評估
- [ ] 下 Sprint 規劃

### 每月檢查清單

- [ ] 月度報告
- [ ] 趨勢分析
- [ ] 預算規劃
- [ ] 團隊效能
- [ ] 工具優化

---

## 9️⃣ 快速範例集合

### 範例 1：建立專案環境

```python
from methodology import MethodologyCore, SprintPlanner, ResourceDashboard

core = MethodologyCore()
planner = SprintPlanner()
dashboard = ResourceDashboard()

print("✅ 環境已準備好")
```

### 範例 2：追蹤成本

```python
from methodology import SmartRouter

router = SmartRouter()
router.track_usage("gpt-4o", 1000, 500)
print(f"本月支出: ${router.get_cost_summary()['total_spent']:.2f}")
```

### 範例 3：建立 Sprint

```python
from methodology import SprintPlanner

planner = SprintPlanner()
sprint = planner.create_sprint("Sprint 1", "2026-03-20", "2026-04-02", capacity=30)
print(f"✅ Sprint '{sprint.name}' 已建立")
```

---

## 📚 相關資源

| 資源 | 連結 |
|------|------|
| 快速開始 | [QUICKSTART.md](QUICKSTART.md) |
| 完整文檔 | [NEW_TEAM_GUIDE.md](docs/NEW_TEAM_GUIDE.md) |
| 案例集合 | [docs/cases/README.md](docs/cases/README.md) |
| GitHub | [methodology-v2](https://github.com/johnnylugm-tech/methodology-v2) |

---

**有任何問題？查看案例文檔或提交 Issue！**
