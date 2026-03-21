# Observability Module

Enhanced debugging and monitoring for methodology-v2.

## Quick Start

```python
from observability import Observer, Tracer, MetricsCollector, DistributedTracer, UnifiedLogger

# === Distributed Tracing ===
dt = DistributedTracer()
span_id = dt.trace_request("req_001", "coder", metadata={"task": "debug"})
# ... agent work ...
dt.end_span("req_001", span_id, metadata={"status": "success"})
tree = dt.get_trace_tree("req_001")  # Get complete call chain

# === Unified Logging ===
ul = UnifiedLogger()
ul.info("coder", "agent_start", {"task": "fix bug"}, request_id="req_001")
ul.error("researcher", "tool_error", {"tool": "browser", "error": "timeout"})
ul.set_min_level("DEBUG")  # Enable debug logs

# === Traditional Observability ===
with Tracer("agent_task") as span:
    result = agent.run(task)
    span.set_tag("status", "success")

MetricsCollector.record("tokens", token_count)
MetricsCollector.record("latency_ms", duration)
```

## Features

### 1. Distributed Tracing (DistributedTracer)

跨 Agent 追蹤，支援單一請求在多個 Agent 間的完整呼叫鏈。

```python
dt = DistributedTracer()

# 開始追蹤
span_id = dt.trace_request(
    request_id="req_123",
    agent_id="coder",
    parent_span_id=None,  # 可選，支援巢狀
    metadata={"task": "write_tests"}
)

# 結束 span
dt.end_span("req_123", span_id, metadata={"status": "completed"})

# 取得完整呼叫樹
tree = dt.get_trace_tree("req_123")
# tree = {
#   "request_id": "req_123",
#   "total_duration_ms": 1234.5,
#   "root_spans": [...],
#   "span_count": 5
# }

# 列出所有活躍追蹤
active = dt.list_active_traces()
```

追蹤資料寫入：`/tmp/distributed_traces.jsonl`

### 2. Unified Logging (UnifiedLogger)

統一日誌格式，所有 Agent 日誌輸出到同一位置。

```python
ul = UnifiedLogger()

# 四種等級
ul.debug("agent_name", "event_name", {"key": "value"})
ul.info("agent_name", "event_name", {"key": "value"})
ul.warn("agent_name", "event_name", {"key": "value"})
ul.error("agent_name", "event_name", {"key": "value"})

# 關聯 request_id（用於關聯分散式追蹤）
ul.info("coder", "agent_start", {"task": "debug"}, request_id="req_123")

# 查詢日誌
logs = ul.get_logs(agent_id="coder", level="ERROR", limit=50)
logs = ul.get_logs(request_id="req_123")  # 某請求的所有日誌

# 從檔案讀取（重啟後可用）
logs = ul.read_logs_from_file(since=datetime(2025, 1, 1), limit=1000)
```

日誌檔案：`/tmp/unified_logs.jsonl`

日誌格式：
```json
{
  "timestamp": "2025-01-01T12:00:00.000000",
  "level": "INFO",
  "agent_id": "coder",
  "event": "agent_start",
  "metadata": {"task": "fix bug"},
  "request_id": "req_123"
}
```

### 3. Tracing (Tracer)

傳統單一 Agent 追蹤。

```python
with Tracer("workflow") as span:
    # Agent execution
    span.set_tag("agent", "coder")
    span.set_tag("task", "debug_code")
```

追蹤資料寫入：`/tmp/traces/{trace_id}.jsonl`

### 4. Metrics (MetricsCollector)

Prometheus-style metrics。

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

# Get stats
stats = MetricsCollector.get_stats("latency_ms")
# {"count": 100, "min": 10, "max": 5000, "avg": 250}
```

### 5. Structured Logging (Observer)

```python
observer = Observer()
observer.log("agent_start", {"agent": "coder", "task": "fix bug"})
observer.log("agent_end", {"agent": "coder", "status": "success"})
observer.log("error", {"error": "timeout", "agent": "researcher"})
observer.handle_error(exception, {"task": "test"})
```

## Dashboard

```bash
python observability/dashboard.py
```

Opens web dashboard with:
- Execution traces
- Performance metrics
- Error rates
- Agent activity

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Observability                      │
├─────────────────────────────────────────────────────┤
│  DistributedTracer  → 跨 Agent 呼叫鏈追蹤           │
│  UnifiedLogger      → 統一 JSON 日誌格式            │
│  Tracer            → Span 生成（單一 Agent）         │
│  MetricsCollector  → Prometheus-style 指標          │
│  Observer          → 結構化日誌 + 錯誤處理           │
│  Dashboard         → Web UI 可視化                  │
└─────────────────────────────────────────────────────┘

輸出檔案：
  /tmp/distributed_traces.jsonl   ← 分散式追蹤
  /tmp/unified_logs.jsonl         ← 統一日誌
  /tmp/traces/{id}.jsonl          ← 單一追蹤
```

## Integration

Integrates with existing methodology-v2 modules:
- Agent tracing
- Workflow monitoring
- Error tracking
- Performance profiling
