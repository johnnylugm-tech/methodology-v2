# Traceability Matrix - 追溯性矩陣

> AI-native ASPICE 合規追溯系統

## 概述

Traceability Matrix 為 Multi-Agent 系統提供自動化的執行鏈追溯能力，支援 ASPICE SWE.3 / SYS.4 等流程的追溯性要求。

**核心價值：**
- 🏗️ 零負擔集成：自動記錄，無需手動干預
- ✅ 客觀證據：每次操作都有可追溯的鏈接
- 📊 ASPICE 合規：符合汽車行業軟體流程標準
- 🔍 完整性驗證：自動檢測追溯缺口

## 核心概念

### 追溯鏈接 (TraceLink)

```
task → agent → output → verification → signed
  │       │        │          │          │
  └───────┴────────┴──────────┴──────────┘
           追溯鏈
```

| 類型 | 說明 |
|------|------|
| `task→agent` | 任務分配給 Agent |
| `agent→output` | Agent 產生輸出 |
| `output→verification` | 輸出進入驗證 |
| `verification→signed` | 驗證通過並簽署 |

### 狀態流

```
PENDING → IN_PROGRESS → VERIFIED
    │                    │
    └──────→ FAILED ←────┘
```

## 使用方式

### 基本用法

```python
from traceability_matrix import (
    TraceabilityMatrix,
    TraceStatus,
    get_traceability_matrix
)

# 初始化
trace = TraceabilityMatrix(project_id="my-project")

# 或使用全局實例
trace = get_traceability_matrix()
```

### 添加追溯鏈接

```python
# 任務建立時：建立 task → agent 鏈接
link_id = trace.add_link(
    source_type="task",
    source_id="task-001",
    target_type="agent",
    target_id="architect-001"
)

# Agent 執行時：建立 agent → output 鏈接
output_link_id = trace.add_link(
    source_type="agent",
    source_id="architect-001",
    target_type="output",
    target_id="output-001"
)
```

### 標記驗證狀態

```python
# 驗證完成
trace.mark_verified(link_id, verifier="human-reviewer")

# 驗證失敗
trace.mark_failed(link_id, reason="不符合規格")
```

### 查詢追溯鏈

```python
# 查詢某任務的完整追溯鏈
chain = trace.get_trace("task-001")

# 查詢下游鏈接（從某節點出發的所有鏈接）
downstream = trace.get_downstream_links("task-001")

# 查詢上游鏈接（指向某節點的所有鏈接）
upstream = trace.get_upstream_links("output-001")
```

### 驗證完整性

```python
# 驗證追溯完整性
completeness = trace.verify_completeness()
# {
#     "total_links": 10,
#     "verified": 8,
#     "pending": 1,
#     "in_progress": 1,
#     "failed": 0,
#     "complete_rate": "80.0%",
#     "verification_rate": "80.0%",
#     "tasks_with_agents": 5,
#     "tasks_with_outputs": 5
# }
```

### 匯出報告

```python
# 標準報告
report = trace.export_report()

# ASPICE 合規報告
aspice_report = trace.export_report(format="aspice")
# {
#     "project_id": "my-project",
#     "aspice_compliance": {
#         "traceability_complete": True,
#         "verification_complete": False,
#         "coverage": {
#             "tasks_with_agent_assignment": 5,
#             "tasks_with_outputs": 5
#         }
#     },
#     "summary": {...},
#     "all_links": [...]
# }
```

### 保存/加載

```python
# 保存到文件
trace.save("trace_report.json")

# 從文件加載
trace = TraceabilityMatrix.load("trace_report.json")
```

## 與現有模組整合

### 與 TaskSplitter 整合

```python
from task_splitter import TaskSplitter
from traceability_matrix import get_traceability_matrix

# 初始化
splitter = TaskSplitter()
trace = get_traceability_matrix()

# 創建任務並自動建立追溯
task = splitter.create_task("設計架構", "設計系統架構")
trace.add_link("task", task.id, "agent", "architect")

# Agent 執行並產生輸出
output = agent.execute(task)
trace.add_link("agent", "architect", "output", output.id)
```

### 與 AgentTeam 整合

```python
from agent_team import AgentTeam
from traceability_matrix import get_traceability_matrix

# 初始化
team = AgentTeam(...)
trace = get_traceability_matrix()

# 任務分配時
for task in tasks:
    agent = team.assign(task)
    trace.add_link("task", task.id, "agent", agent.id)

# 產出產生時
for output in agent.outputs:
    trace.add_link("agent", agent.id, "output", output.id)
```

### 混入類方式

```python
from traceability_matrix import TraceabilityMixin

class MyAgent(TraceabilityMixin):
    def __init__(self):
        self.trace = self.get_traceability_matrix()
    
    def execute(self, task):
        link_id = self.trace.add_link("agent", self.id, "output", output_id)
        # ... execute
        self.trace.mark_verified(link_id)
```

## ASPICE 合規矩陣

| ASPICE 能力 | 支持 |
|-------------|------|
| SWE.3.B.SP1 任務到工作產品追溯 | ✅ |
| SWE.3.B.SP2 工作產品之間的雙向追溯 | ✅ |
| SWE.3.B.SP3 追溯一致性 | ✅ |
| SYS.4.B.SP1 需求到設計追溯 | ✅ |

## 最佳實踐

1. **盡早建立鏈接**：在任務創建時就建立 task→agent 鏈接
2. **自動驗證**：在 quality gate 通過時自動調用 `mark_verified()`
3. **定期檢查**：使用 `verify_completeness()` 發現缺口
4. **保存證據**：在關鍵節點保存追溯報告作為客觀證據

## API 速查

| 方法 | 說明 |
|------|------|
| `add_link()` | 添加追溯鏈接 |
| `mark_verified()` | 標記為已驗證 |
| `mark_failed()` | 標記為失敗 |
| `get_trace()` | 查詢完整追溯鏈 |
| `get_downstream_links()` | 獲取下游鏈接 |
| `get_upstream_links()` | 獲取上游鏈接 |
| `verify_completeness()` | 驗證完整性 |
| `export_report()` | 匯出報告 |
| `get_aspice_report()` | 生成 ASPICE 報告 |
| `save()` / `load()` | 保存/加載 |
