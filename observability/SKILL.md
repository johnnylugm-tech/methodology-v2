---
name: observability
description: Enhanced Observability Module for methodology-v2. Provides structured logging, tracing, metrics, and visualization dashboard for debugging and monitoring agent execution.
---

# Observability Module

Enhanced debugging and monitoring for methodology-v2.

## Quick Start

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

## Features

### 1. Tracing

```python
with Tracer("workflow") as span:
    # Agent execution
    span.set_tag("agent", "coder")
    span.set_tag("task", "debug_code")
```

### 2. Metrics

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

### 3. Structured Logging

```python
Observer.log("agent_start", {"agent": "coder", "task": "fix bug"})
Observer.log("agent_end", {"agent": "coder", "status": "success"})
Observer.log("error", {"error": "timeout", "agent": "researcher"})
```

### 4. Dashboard

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
