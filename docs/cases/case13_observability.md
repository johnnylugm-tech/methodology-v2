# 案例 13：Observability Module (observability)

## 概述

Enhanced Observability Module 提供結構化日誌、追蹤、指標和視覺化儀表板。

---

## 快速開始

```python
from observability import Observer, Tracer, MetricsCollector

# Trace execution
with Tracer("agent_task") as span:
    result = agent.run(task)
    span.set_tag("status", "success")

# Record metrics
MetricsCollector.record("tokens", token_count)
MetricsCollector.record("latency_ms", duration)

# Log state
Observer.log("agent_state", {"step": 1, "agent": "coder"})
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| Tracing | 執行追蹤 |
| Metrics | 指標收集 |
| Logging | 結構化日誌 |
| Dashboard | 視覺化儀表板 |

---

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| agent_debugger | 共享追蹤系統 |
| message_bus | 事件日誌 |
| dashboard | 統一儀表板 |

---

## Dashboard 使用

```python
from observability.dashboard import ObservabilityDashboard

dashboard = ObservabilityDashboard()
dashboard.show_metrics(agent_id="coder")
dashboard.show_traces(time_range="1h")
```

---

## 相關模組

- agent_debugger.py
- message_bus.py
- cloud_dashboard.py
