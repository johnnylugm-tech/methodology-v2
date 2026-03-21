# Case 27: Resource Gantt + Conflict Detection - 資源視圖與衝突檢測

## 情境

需要一眼看出任務衝突，特別是多個 Agent 被派相同任務時。

## 解決方案

### Resource Gantt Chart

```python
from gantt_chart import ResourceGanttChart

chart = ResourceGanttChart()
chart.generate_resource_view(tasks, agents)
chart.detect_conflicts()
```

### 任務衝突檢測

```python
from smart_orchestrator import SmartOrchestrator, ConflictError

orchestrator = SmartOrchestrator(conflict_detection=True)

# 自動衝突檢測
try:
    orchestrator.assign_task("task-123", "agent-1")
except ConflictError as e:
    print(f"衝突: Agent 已被派任務")
```

## 功能

| 功能 | 說明 |
|------|------|
| 資源 Gantt | X=時間, Y=資源, 顯示任務分配 |
| 衝突檢測 | 同一 Agent 不能同時被派兩任務 |
| 負載追蹤 | 實時監控 Agent 負載 |

## Gantt 輸出格式

```
        | 9AM | 10AM | 11AM | 12PM |
Agent-1 | ████████████ |       |      |
Agent-2 |       | ████████████████ |  |
Agent-3 |       |       | ████ |      |
```

## Related

- gantt_chart.py
- smart_orchestrator.py
- ConflictError
