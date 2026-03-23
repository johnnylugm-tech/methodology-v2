# Case 61: ROI 追蹤儀表板 (ROI Tracking Dashboard)

## 概述

ROI 追蹤儀表板用於量化 Agent 開發的投資回報率，幫助團隊了解：
- 開發成本（API 調用、計算資源）
- 維護成本（錯誤修復、安全更新）
- 產出價值（任務完成數、效率提升）
- 失敗成本（錯誤導致的損失）

## 快速開始

### 記錄成本

```python
from roi_tracker import CostTracker, CostType

tracker = CostTracker()

# 記錄 API 調用成本
tracker.record(
    cost_type=CostType.API_CALL,
    amount=0.15,
    agent_id="agent-1",
    task_id="TASK-123",
    description="Claude API call"
)

# 記錄維護成本
tracker.record(
    cost_type=CostType.MAINTENANCE,
    amount=2.0,
    agent_id="agent-1",
    task_id="TASK-456",
    description="Bug fix: memory leak"
)
```

### 記錄價值

```python
from roi_tracker import ValueTracker, ValueType

tracker = ValueTracker()

# 記錄任務完成
tracker.record(
    value_type=ValueType.TASK_COMPLETED,
    amount=1,
    unit="tasks",
    agent_id="agent-1",
    task_id="TASK-123",
    description="Completed login feature"
)

# 記錄效率提升
tracker.record(
    value_type=ValueType.EFFICIENCY_GAIN,
    amount=2.5,
    unit="hours",
    agent_id="agent-1",
    description="Automated testing saved 2.5 hours"
)
```

### 計算 ROI

```python
from roi_tracker import ROICalculator

calculator = ROICalculator()

# 取得儀表板資料
data = calculator.get_dashboard_data()

for period, report in data.items():
    print(f"\n{period.upper()}:")
    print(f"  Cost: ${report.total_cost:.2f}")
    print(f"  Value: ${report.total_value:.2f}")
    print(f"  ROI: {report.roi_percentage}%")
    print(f"  Net: ${report.net_value:.2f}")
    print(f"  Recommendation: {report.recommendation}")
```

## ROI 計算公式

```
ROI = (Value - Cost) / Cost × 100%
```

## 價值轉換率

| 價值類型 | 轉換率 |
|---------|-------|
| task_completed | $100/task |
| efficiency_gain | $50/hour |
| bugs_prevented | $200/bug |
| quality_improvement | $25/point |
| time_saved | $50/hour |

## CLI 使用

```bash
# 查看儀表板
methodology roi dashboard

# 查看特定期間報告
methodology roi report month
methodology roi report week
methodology roi report day
```

## 建議解讀

| ROI 範圍 | 建議 |
|---------|-----|
| > 200% | Excellent ROI! Consider scaling up investment. |
| 100-200% | Good ROI. Current investment is paying off. |
| 0-100% | Positive but marginal ROI. Look for optimization opportunities. |
| -50-0% | Negative ROI. Investigate cost drivers and value delivery. |
| < -50% | Critical: ROI is significantly negative. Major changes needed. |

## 資料存放

- 成本資料：`.methodology/roi_costs.db` (SQLite)
- 價值資料：`.methodology/roi_values.db` (SQLite)
