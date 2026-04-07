# 案例十：Agent Debugger (方案 G)

## 概述

Agent Debugger 提供 Agent 系統的可觀測性增強，讓開發者能夠追蹤、診斷和視覺化 Agent 的行為。

---

## 問題背景

```
Black-box agent systems are hard to debug
當 Agent 生產失敗，很難確定哪個環節出了問題
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| Trace 追蹤 | 記錄每次 LLM 呼叫的輸入/輸出 |
| 狀態變化追蹤 | 追蹤 Agent 狀態的每一次變化 |
| 時間軸視覺化 | 顯示事件發生的時間順序 |
| 狀態快照 | 保存關鍵時刻的完整狀態 |

---

## 快速開始

### 基本追蹤

```python
from agent_debugger import AgentDebugger

debugger = AgentDebugger()

# 追蹤 Agent 事件
debugger.trace(
    agent_id="agent-001",
    event_type="llm_call",
    data={
        "input": "用戶查詢",
        "output": "系統回應",
        "model": "claude-3-opus",
        "latency_ms": 1500
    }
)
```

### 獲取 Trace 歷史

```python
# 獲取特定 Agent 的 Trace
traces = debugger.get_trace(
    agent_id="agent-001",
    time_range={"start": "2026-03-21", "end": "2026-03-22"}
)

for trace in traces:
    print(f"{trace.timestamp}: {trace.event_type}")
    print(f"  Input: {trace.data.get('input')}")
    print(f"  Output: {trace.data.get('output')}")
```

### 視覺化 Trace

```python
# 生成視覺化報告
report = debugger.visualize(agent_id="agent-001")
print(report)
```

---

## 與 MessageBus 整合

```python
from message_bus import MessageBus

bus = MessageBus()

# 啟用 Debug 模式
bus.enable_debug(debugger)

# 之後所有 publish/subscribe 都會自動追蹤
bus.publish("task.completed", {"task_id": "123", "result": "success"})
```

---

## CLI 命令

```bash
# 查看 Agent Trace
python cli.py debug agent-001

# 即時監控 Agent
python cli.py trace agent-001 --follow

# 生成 Trace 報告
python cli.py trace agent-001 --report

# 顯示狀態變化
python cli.py debug agent-001 --state-changes
```

---

## Trace 事件類型

| 事件類型 | 說明 |
|----------|------|
| `llm_call` | LLM API 呼叫 |
| `tool_execution` | 工具執行 |
| `state_change` | 狀態變化 |
| `error` | 錯誤發生 |
| `message_sent` | 訊息發送 |
| `message_received` | 訊息接收 |

---

## 輸出格式

```python
@dataclass
class TraceEvent:
    event_id: str
    agent_id: str
    event_type: str
    timestamp: datetime
    data: dict
    metadata: dict
```

---

## 與 Agent Evaluator 整合

```python
from agent_evaluator import AgentEvaluator

evaluator = AgentEvaluator()

# 啟用 Debugger
evaluator.enable_debugger(debugger)

# 評估時自動追蹤
result = evaluator.run_evaluation(agent)

# 查看評估過程的 Trace
traces = debugger.get_trace(agent_id=result.agent_id)
```

---

## 最佳實踐

1. **在開發環境啟用完整 Trace**
2. **生產環境只追蹤關鍵事件**
3. **定期分析 Trace 找出效能瓶頸**
4. **結合 Agent Evaluator 使用**

---

## 相關模組

| 模組 | 說明 |
|------|------|
| MessageBus | 訊息協調（整合 Debugger） |
| AgentEvaluator | Agent 評估 |
| PredictiveMonitor | 預測監控 |
