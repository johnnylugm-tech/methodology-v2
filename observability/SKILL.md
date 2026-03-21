---
name: observability
description: Enhanced Observability Module for methodology-v2. Provides structured logging, tracing, metrics, and visualization dashboard for debugging and monitoring agent execution.
---

# Observability Module

Enhanced debugging and monitoring for methodology-v2.

## Quick Start

```python
from observability import Observer, Tracer, MetricsCollector, DistributedTracer, UnifiedLogger

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

## Features

### 1. Distributed Tracing

跨 Agent 請求追蹤，支援完整呼叫鏈重建。

```python
from observability import DistributedTracer

dt = DistributedTracer()
span_id = dt.trace_request("req_001", "coder", metadata={"task": "debug"})
# ... agent work ...
dt.end_span("req_001", span_id)
tree = dt.get_trace_tree("req_001")  # 取得完整呼叫樹
```

### 2. Unified Logging

統一日誌格式，输出到 `/tmp/unified_logs.jsonl`。

```python
from observability import UnifiedLogger

ul = UnifiedLogger()
ul.info("coder", "agent_start", {"task": "fix bug"}, request_id="req_001")
ul.error("researcher", "tool_error", {"error": "timeout"})
logs = ul.get_logs(request_id="req_001")  # 查詢某請求的所有日誌
```

### 3. Tracing

```python
with Tracer("workflow") as span:
    # Agent execution
    span.set_tag("agent", "coder")
    span.set_tag("task", "debug_code")
```

### 4. Metrics

```python
# Counters
MetricsCollector.increment("requests_total")
MetricsCollector.increment("errors_total")

# Gauges
MetricsCollector.gauge("active_agents", count)
MetricsCollector.gauge("queue_size", size)

# Histograms
MetricsCollector.histogram("latency_ms", duration)
MetricsCollector.histogram("tokens_used", tokens)
```

### 5. Structured Logging

```python
Observer.log("agent_start", {"agent": "coder", "task": "fix bug"})
Observer.log("agent_end", {"agent": "coder", "status": "success"})
Observer.log("error", {"error": "timeout", "agent": "researcher"})
```

### 6. Dashboard

```bash
python observability/dashboard.py
```

Opens web dashboard with:
- Execution traces
- Performance metrics
- Error rates
- Agent activity

## CLI Usage

```bash
# Start dashboard
python -m observability.dashboard

# Export traces
python -m observability export --format json --output traces.json
```

## Architecture

```
┌─────────────────────────────────────┐
│         Observability               │
├─────────────────────────────────────┤
│  Tracer    → Span generation       │
│  Metrics   → Prometheus-style       │
│  Logger    → Structured JSON       │
│  Dashboard → Web UI                 │
└─────────────────────────────────────┘
```

## Integration

Integrates with existing methodology-v2 modules:
- Agent tracing
- Workflow monitoring
- Error tracking
- Performance profiling
