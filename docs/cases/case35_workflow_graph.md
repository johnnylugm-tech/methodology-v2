# Case 35: Workflow Graph - 工作流圖結構視覺化

## 概述

對標 LangGraph 的圖結構概念，實現工作流可視化系統。

## 核心概念

### 節點類型 (NodeType)

| 類型 | 說明 | 圖形表示 |
|------|------|----------|
| `START` | 起始節點 | 圓形 |
| `END` | 結束節點 | 圓形 |
| `TASK` | 任務節點 | 方形 |
| `AGENT` | Agent 節點 | 方形 |
| `CONDITION` | 條件節點 | 菱形 |
| `MERGE` | 合併節點 | 菱形 |
| `OUTPUT` | 輸出節點 | 方形 |

### 邊類型 (EdgeType)

| 類型 | 說明 |
|------|------|
| `SEQUENCE` | 順序執行 |
| `BRANCH` | 條件分支 |
| `MERGE` | 分支合併 |
| `FEEDBACK` | 回饋循環 |

## 快速開始

```python
from workflow_graph import WorkflowGraph, NodeType, EdgeType

# 創建工作流
wf = WorkflowGraph("My Workflow")

# 添加節點
start = wf.add_node("Start", NodeType.START)
task1 = wf.add_node("Process Data", NodeType.TASK)
cond = wf.add_node("Check Result", NodeType.CONDITION)
task2a = wf.add_node("Handle Success", NodeType.TASK)
task2b = wf.add_node("Handle Error", NodeType.TASK)
end = wf.add_node("End", NodeType.END)

# 設置起始和結束
wf.set_start(start)
wf.set_end(end)

# 添加邊
wf.add_edge(start, task1)
wf.add_edge(task1, cond)
wf.add_edge(cond, task2a, EdgeType.BRANCH)
wf.add_edge(cond, task2b, EdgeType.BRANCH)
wf.add_edge(task2a, end)
wf.add_edge(task2b, end)

# 可視化輸出
print(wf.visualize())
```

## 輸出格式

### ASCII 輸出

```
Workflow: My Workflow
==================================================
→ Start (start)
   └─[sequence]→ Process Data
   └─[sequence]→ Check Result
      └─[branch]→ Handle Success
      └─[branch]→ Handle Error
   └─[sequence]→ End [END]
```

### DOT 輸出 (Graphviz)

```dot
digraph "My Workflow" {
  rankdir=LR;
  node-abc123 [label="Start", shape=oval];
  node-def456 [label="Process Data", shape=box];
  ...
}
```

### JSON 導出

```json
{
  "graph_id": "graph-abc123",
  "name": "My Workflow",
  "nodes": [...],
  "edges": [...],
  "start": "node-abc123",
  "ends": ["node-xyz789"]
}
```

## 工廠函數

### 線性工作流

```python
from workflow_graph import create_linear_flow

wf = create_linear_flow("Pipeline", ["Step 1", "Step 2", "Step 3"])
```

### 分支工作流

```python
from workflow_graph import create_branch_flow

wf = create_branch_flow(
    "Decision Flow",
    condition_node="Check Status",
    branches={
        "success": "Handle Success",
        "error": "Handle Error"
    },
    merge_node="Merge Results"
)
```

## 條件分支

```python
wf = WorkflowGraph("Conditional Flow")
start = wf.add_node("Start", NodeType.START)
check = wf.add_node("Check", NodeType.CONDITION)
process = wf.add_node("Process", NodeType.TASK)
end = wf.add_node("End", NodeType.END)

wf.set_start(start)
wf.add_edge(start, check)
wf.add_edge(check, process, EdgeType.BRANCH, condition=lambda ctx: ctx.get("approved"))
wf.add_edge(process, end)

# 遍歷時傳入上下文
next_nodes = wf.get_next_nodes(check, context={"approved": True})
```

## 與 LangGraph 對比

| LangGraph | WorkflowGraph | 說明 |
|-----------|---------------|------|
| `StateGraph` | `WorkflowGraph` | 主圖結構 |
| `@entrypoint` | `set_start()` | 入口點 |
| `@entrypoint` | `set_end()` | 結束點 |
| `.add_node()` | `.add_node()` | 添加節點 |
| `.add_edge()` | `.add_edge()` | 添加邊 |
| `.add_conditional_edges()` | `.add_edge(..., condition=)` | 條件邊 |
| `get_graph()` | `to_ascii()` / `to_dot()` / `to_json()` | 導出圖 |

## 最佳實踐

1. **清晰命名**：節點名稱應該描述其職責
2. **單一職責**：每個節點只做一件事
3. **條件明確**：分支條件應該易於理解和測試
4. **可視化優先**：先用 ASCII 視覺化確認結構

## 整合使用

```python
# 與 agent_team.py 整合
from workflow_graph import WorkflowGraph, NodeType, EdgeType

wf = WorkflowGraph("Agent Team Workflow")
researcher = wf.add_node("Researcher Agent", NodeType.AGENT)
analyzer = wf.add_node("Analyzer Agent", NodeType.AGENT)
reporter = wf.add_node("Reporter Agent", NodeType.TASK)

wf.set_start(researcher)
wf.add_edge(researcher, analyzer)
wf.add_edge(analyzer, reporter)
wf.set_end(reporter)

# 導出給團隊調度器
graph_def = wf.to_json()
```
