# 案例十一：Framework Bridge (方案 H)

## 概述

Framework Bridge 支援 CrewAI ↔ LangGraph 雙向遷移，讓開發者能夠在不同 Agent 框架間自由遷移。

---

## 問題背景

```
Framework migration is painful
選擇 LangGraph 做原型，然後想遷移到 CrewAI 生產，意味著要重寫大部分邏輯
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| CrewAI → LangGraph | 將 CrewAI 工作流轉換為 LangGraph 圖 |
| LangGraph → CrewAI | 將 LangGraph 圖轉換為 CrewAI 工作流 |
| 遷移驗證 | 確保轉換前後行為一致 |

---

## 快速開始

### CrewAI → LangGraph

```python
from framework_bridge import FrameworkBridge

bridge = FrameworkBridge()

# 假設有一個 CrewAI flow
crewai_flow = {
    "agents": [
        {"role": "researcher", "goal": "Research topic"},
        {"role": "writer", "goal": "Write content"}
    ],
    "tasks": [...]
}

# 轉換為 LangGraph
langgraph_graph = bridge.crewai_to_langgraph(crewai_flow)
print(langgraph_graph)
```

### LangGraph → CrewAI

```python
# 假設有一個 LangGraph
langgraph_spec = {
    "nodes": ["researcher", "writer"],
    "edges": [("researcher", "writer")]
}

# 轉換為 CrewAI
crewai_flow = bridge.langgraph_to_crewai(langgraph_spec)
print(crewai_flow)
```

---

## 遷移驗證

```python
# 驗證遷移正確性
validation = bridge.validate_migration(
    original=crewai_flow,
    converted=langgraph_graph
)

if validation.is_valid:
    print("✅ 遷移成功，行為一致")
else:
    print(f"⚠️ 警告: {validation.differences}")
```

---

## CLI 命令

```bash
# CrewAI → LangGraph
python cli.py migrate \
    --from crewai \
    --to langgraph \
    --input crewai_flow.py \
    --output langgraph_graph.py

# LangGraph → CrewAI
python cli.py migrate \
    --from langgraph \
    --to crewai \
    --input langgraph_graph.py \
    --output crewai_flow.py

# 驗證遷移
python cli.py migrate \
    --validate \
    --original crewai_flow.py \
    --converted langgraph_graph.py
```

---

## 支援的轉換

### CrewAI → LangGraph

| CrewAI 概念 | LangGraph 概念 |
|-------------|---------------|
| Agent | Node (節點) |
| Task | Edge (邊) |
| Crew | Graph (圖) |
| Sequential | Sequential Edges |
| Hierarchical | Subgraphs |

### LangGraph → CrewAI

| LangGraph 概念 | CrewAI 概念 |
|---------------|-------------|
| Node | Agent |
| Edge | Task Dependency |
| Graph | Crew |
| Conditional Edge | Custom Task Routing |

---

## 限制與警告

| 限制 | 說明 |
|------|------|
| 自訂 Tool | 需手動遷移 |
| 複雜條件邏輯 | 可能需要簡化 |
| 第三方整合 | 需重新配置 |

---

## 與 LangGraphMigrator 整合

```python
from langgraph_migrator import LangGraphMigrator

migrator = LangGraphMigrator()
bridge = FrameworkBridge()

# 先用 LangGraphMigrator 分析
analysis = migrator.analyze(code)

# 再用 FrameworkBridge 轉換
converted = bridge.convert(analysis)
```

---

## 最佳實踐

1. **遷移前先完整備份**
2. **分階段遷移，不要一次全轉**
3. **使用遷移驗證確保行為一致**
4. **測試環境先驗證再上生產**

---

## 相關模組

| 模組 | 說明 |
|------|------|
| LangGraphMigrator | LangGraph 遷移工具 |
| TaskSplitter | 任務分解 |
| WorkflowGraph | 工作流圖 |
