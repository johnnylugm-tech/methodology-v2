# Feature #11: Langfuse Observability — Specification

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 01-spec  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Draft  

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [Data Field Definitions](#4-data-field-definitions)
5. [User Scenarios](#5-user-scenarios)
6. [Acceptance Criteria](#6-acceptance-criteria)
7. [Dependencies](#7-dependencies)
8. [Out of Scope](#8-out-of-scope)
9. [Glossary](#9-glossary)

---

## 1. Feature Overview

### 1.1 What is Langfuse Observability?

Langfuse is an open-source observability platform for LLM applications. It provides:

- **Distributed tracing**: trace requests across multiple services and AI models
- **Span-level granularity**: capture input/output, latency, token counts, and custom attributes
- **Prompt engineering tooling**: manage, version, and compare prompts
- **Analytics dashboards**: real-time metrics, trends, and audit logs

Feature #11 integrates Langfuse into methodology-v2 using the OpenTelemetry (OTel) SDK as the tracing backend. Every AI decision point in Phase 6/7 is instrumented with 7 required OTel span attributes: `uaf_score`, `clap_flag`, `risk_score`, `hitl_gate`, `human_decision`, `decided_by`, `compliance_tags`.

### 1.2 Why Langfuse?

| Consideration | Decision |
|---------------|----------|
| Vendor lock-in | OTel SDK is vendor-neutral; trace data can be exported to any OTel-compatible backend |
| LangChain compatibility | `opentelemetry-instrumentation-langchain` provides automatic span creation for LCEL chains |
| Self-hosted option | Langfuse supports self-hosting; no data leaves the infrastructure if required |
| Audit compliance | Append-only trace storage satisfies SOX/GDPR audit requirements |

### 1.3 Architecture

```
methodology-v2 Pipeline
│
├── Phase 6: Risk Management
│   └── risk_evaluation() → emits [FR-11-02] span
│
├── Phase 7: Decision Gate
│   ├── uaf_check() → emits [FR-11-02] span
│   ├── clap_evaluation() → emits [FR-11-02] span
│   └── hitl_gate() → emits [FR-11-02] span
│
└── ml_langfuse/
    ├── client.py        → Langfuse client singleton [FR-11-01]
    ├── config.py       → Environment/config validation [FR-11-08]
    ├── trace.py        → Trace context helpers [FR-11-03]
    ├── span.py        → Span creation utilities [FR-11-02]
    └── decorators.py  → Auto-instrumentation decorators [FR-11-04]
```

---

## 2. Functional Requirements

### [FR-11-01] Langfuse Client Initialization

**Description:**

Initialize a Langfuse client singleton with OTel SDK integration. The client must:

- Be instantiated once per process lifecycle (singleton pattern)
- Register an OTel `TracerProvider` with the global OTel registry
- Support both **cloud mode** (Langfuse hosted) and **self-hosted mode**
- Register an `atexit` handler to flush pending spans on process exit
- Raise `ConfigurationError` with a clear message if required env vars are missing

**Environment Variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Yes (cloud) | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Yes (cloud) | Langfuse secret key |
| `LANGFUSE_HOST` | Yes (self-hosted) | Self-hosted URL, e.g. `https://langfuse.example.com` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP collector endpoint; defaults to Langfuse cloud OTLP endpoint |
| `OTEL_SERVICE_NAME` | No | Service name for traces; defaults to `methodology-v2` |
| `LANGFUSE_TRACE_SAMPLING_RATE` | No | Sample rate 0.0–1.0; defaults to `1.0` (all traces) |

**API Surface:**

```python
# ml_langfuse/client.py
from ml_langfuse import LangfuseClient, get_client

def get_langfuse_client() -> LangfuseClient:
    """Returns the singleton Langfuse client instance."""
    ...

class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    ...
```

**Validation Rules:**

1. Cloud mode: `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` must both be set or both absent (treat as cloud mode)
2. Self-hosted mode: if `LANGFUSE_HOST` is set, use it as the base URL and skip public/secret key check
3. At least one mode must be configuratively active; raise `ConfigurationError` if neither is set
4. `LANGFUSE_TRACE_SAMPLING_RATE` must be in range `[0.0, 1.0]`; raise `ConfigurationError` if out of range

---

### [FR-11-02] OTel Span with Required Fields

**Description:**

Every AI decision point in the methodology-v2 pipeline must emit an OTel span containing exactly these **7 required attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `uaf_score` | `float` | Yes | User Authorization Factor score, range `[0.0, 1.0]` |
| `clap_flag` | `bool` | Yes | Content Legitimacy Assessment Protocol result |
| `risk_score` | `float` | Yes | Aggregated risk score, range `[0.0, 1.0]` |
| `hitl_gate` | `str` | Yes | HITL gate status: one of `pass`, `review`, `block` |
| `human_decision` | `str` or `None` | Yes | Human override decision; `None` if no human involved |
| `decided_by` | `str` | Yes | Decision authority: one of `agent`, `human`, `system` |
| `compliance_tags` | `list[str]` | Yes | List of applicable compliance tags |

**Optional standard OTel attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `llm.model` | `str` | LLM model name (e.g. `claude-3-opus`) |
| `llm.token_count` | `int` | Total tokens consumed |
| `llm.latency_ms` | `float` | LLM call latency in milliseconds |
| `session.id` | `str` | Session identifier |
| `user.id` | `str` | User identifier |

**Span Naming Convention:**

```
{phase}.{node_name}
Examples:
  "phase6.risk_evaluation"
  "phase7.uaf_check"
  "phase7.hitl_gate"
  "phase7.clap_evaluation"
```

**Span Status:**

- `StatusCode.OK` — span completed normally
- `StatusCode.ERROR` — span encountered an error; set `span.set_status(StatusCode.ERROR)` and record exception

**API Surface:**

```python
# ml_langfuse/span.py
from opentelemetry.trace import Span
from opentelemetry.sdk.trace import Span as SDKSpan

def create_decision_span(
    name: str,
    uaf_score: float,
    clap_flag: bool,
    risk_score: float,
    hitl_gate: str,
    human_decision: Optional[str],
    decided_by: str,
    compliance_tags: list[str],
    parent_span: Optional[Span] = None,
) -> Span:
    """Create and start an OTel span with all 7 required attributes."""
    ...

def end_span_with_status(span: Span, status: StatusCode, exception: Optional[Exception] = None) -> None:
    """End a span with appropriate status and exception recording."""
    ...
```

---

### [FR-11-03] Trace Context Propagation

**Description:**

The trace context (W3C `traceparent` header) must propagate correctly across all async boundaries:

- Across `async`/`await` boundaries within the same process
- Across LangChain/LangGraph node boundaries (state flows between nodes)
- Across HTTP requests to downstream microservices
- Across multi-agent sessions (session stitching)

**W3C TraceContext Format:**

```
traceparent: 00-{trace_id}-{span_id}-{trace_flags}
```

**Propagation APIs:**

```python
# ml_langfuse/trace.py

def get_current_trace_context() -> dict:
    """Extract current trace context (trace_id, span_id, trace_flags)."""
    ...

def inject_trace_context(carrier: dict) -> dict:
    """Inject trace context into a carrier dict (e.g. HTTP headers)."""
    ...

def extract_trace_context(carrier: dict) -> Context:
    """Extract trace context from a carrier dict."""
    ...

async def run_with_trace_context(ctx: Context, coro: Coroutine) -> Any:
    """Run a coroutine within a given trace context."""
    ...
```

**LangChain/LangGraph Integration:**

The `observe_llm_call` decorator (see [FR-11-04]) must propagate the current trace context into LangChain tool call headers automatically.

---

### [FR-11-04] Decorator-Based Auto-Instrumentation

**Description:**

Provide four decorators that enable zero-boilerplate instrumentation. Each decorator wraps the target function/class method, creates an appropriate span, and ensures all 7 required attributes are set.

**Decorator 1: `@observe_llm_call`**

```python
@observe_llm_call(model_name: str, model_version: Optional[str] = None)
async def some_llm_invocation(prompt: str, **kwargs) -> str:
    """Wraps LLM invocations; auto-captures model, tokens, latency."""
```

- Creates span named `llm.{model_name}`
- Sets `llm.model`, `llm.token_count` (estimated), `llm.latency_ms`
- Injects trace context into LangChain run (if applicable)
- Propagates the span as the parent for downstream tool calls

**Decorator 2: `@observe_decision_point`**

```python
@observe_decision_point(point: str, phase: str = "phase6")
def sync_risk_evaluation(state: dict) -> dict:
    """Wraps synchronous decision nodes; emits all 7 required fields."""
```

- Creates span named `{phase}.{point}`
- **Requires the decorated function to return a dict** that includes the 7 required fields (or they are passed via kwargs)
- Sets all 7 required attributes from function return value or explicit kwargs
- For `async` functions: use `@observe_decision_point_async`

**Decorator 3: `@observe_tool_call`**

```python
@observe_tool_call(tool_name: str)
def some_tool_invocation(input_data: dict) -> dict:
    """Wraps tool/function calls; captures tool name, input, output, latency."""
```

- Creates span named `tool.{tool_name}`
- Sets `tool.name`, `tool.input_size`, `tool.output_size`, `tool.latency_ms`

**Decorator 4: `@observe_span`**

```python
@observe_span(name: str, attributes: Optional[dict] = None)
async def generic_operation(arg1, arg2):
    """Generic span wrapper for arbitrary operations."""
```

- Creates span named `{name}`
- Sets any additional attributes passed via `attributes` dict

**Decorator Chaining:**

Multiple decorators can be stacked. The inner decorator creates the span; outer decorators add their own attributes:

```python
@observe_decision_point(point="clap_evaluation", phase="phase7")
@observe_llm_call(model_name="claude-3-opus")
async def clap_evaluation_with_llm(state: dict) -> dict:
    ...
```

---

### [FR-11-05] Langfuse Dashboard — Real-Time View

**Description:**

The Langfuse hosted UI (or self-hosted) provides a real-time trace view accessible at `/ traces`. For methodology-v2, the following filters and columns are required:

**Required Filters:**

| Filter | Type | Description |
|--------|------|-------------|
| `hitl_gate` | Multi-select | `pass`, `review`, `block` |
| `decided_by` | Multi-select | `agent`, `human`, `system` |
| `compliance_tags` | Multi-select | e.g. `GDPR Art.22`, `SOX` |
| `risk_score` | Range slider | Min/Max range `[0.0, 1.0]` |
| `uaf_score` | Range slider | Min/Max range `[0.0, 1.0]` |
| `time_range` | Select | Last 1h, 6h, 24h, 7d, 30d |

**Required Columns:**

- Trace ID, Span ID
- Span Name (phase + node)
- `hitl_gate`, `decided_by`, `risk_score`, `uaf_score`
- Timestamp
- Duration (ms)
- `compliance_tags`

**Real-Time Updates:**

- Polling interval: 5 seconds (configurable)
- Maximum displayed traces: 100 (paginated)

---

### [FR-11-06] Langfuse Dashboard — Trend Charts

**Description:**

The Langfuse analytics module provides trend visualizations for decision quality monitoring:

**Chart 1: Risk Score Time-Series**

- Type: Line chart
- X-axis: Time (rolling 7-day window)
- Y-axis: Average `risk_score` per hour
- Segmentation: by `compliance_tags`

**Chart 2: HITL Gate Status Distribution**

- Type: Stacked bar chart
- X-axis: Time (daily buckets)
- Y-axis: Count of spans with each `hitl_gate` value (`pass`/`review`/`block`)
- Colors: Green=`pass`, Yellow=`review`, Red=`block`

**Chart 3: Decision Authority Breakdown**

- Type: Pie chart or stacked bar
- Segments: `agent`, `human`, `system`
- Shows proportion of decisions by authority type

**Chart 4: Escalation Rate Trend**

- Type: Line chart
- Metric: `(count of hitl_gate="review" + "block") / total_spans` per day
- Y-axis: Percentage (0–100%)

**Chart 5: Risk Score × Compliance Tag Heatmap**

- Type: Heatmap
- X-axis: `compliance_tags`
- Y-axis: `risk_score` buckets (`[0-0.2]`, `[0.2-0.4]`, etc.)
- Color intensity: Count of spans

---

### [FR-11-07] Langfuse Dashboard — Audit Log

**Description:**

An immutable audit log entry is created for every span where `decided_by == "human"`. Each entry records the full decision context for compliance review.

**Audit Entry Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique audit entry ID (UUID) |
| `timestamp` | `datetime` | ISO 8601 timestamp of human decision |
| `trace_id` | `str` | Parent trace ID |
| `span_id` | `str` | Span ID of the HITL gate span |
| `session_id` | `str` | Session in which decision was made |
| `user_id` | `str` | Human user who made the decision |
| `input_snapshot` | `str` | Truncated input state (max 2000 chars) |
| `human_decision` | `str` | The human's decision (`approved`/`rejected`/`escalate`) |
| `decided_by` | `str` | Always `human` |
| `compliance_tags` | `list[str]` | Tags applicable to this span |
| `risk_score` | `float` | Risk score at time of decision |
| `uaf_score` | `float` | UAF score at time of decision |

**Retention Policy:**

- Default retention: 90 days
- Configurable per `compliance_tags` category (e.g. SOX: 7 years)
- No update or delete API for audit entries (append-only)

**Export:**

- CSV export via Langfuse UI (admin only)
- JSON export via Langfuse REST API
- Scheduled export to S3/GCS blob storage (infra concern, documented here)

---

### [FR-11-08] Configuration Management

**Description:**

All Langfuse and OTel configuration is centralized in `ml_langfuse/config.py`. Configuration sources (in priority order):

1. Environment variables (highest priority)
2. `config.yaml` file (if present)
3. Hardcoded defaults (lowest priority)

**Config Schema:**

```python
# ml_langfuse/config.py
from pydantic import BaseModel, Field
from typing import Literal

class LangfuseConfig(BaseModel):
    # Mode
    mode: Literal["cloud", "self_hosted"] = "cloud"
    
    # Cloud mode
    public_key: str = Field(default="", description="LANGFUSE_PUBLIC_KEY")
    secret_key: str = Field(default="", description="LANGFUSE_SECRET_KEY")
    
    # Self-hosted mode
    host: str = Field(default="", description="LANGFUSE_HOST URL")
    
    # OTel
    otel_exporter_endpoint: str = ""
    otel_service_name: str = "methodology-v2"
    
    # Sampling
    trace_sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Dashboard
    dashboard_poll_interval_seconds: int = 5
    audit_retention_days: int = 90
    
    def validate_config(self) -> None:
        """Validate configuration; raise ConfigurationError if invalid."""
        ...
```

**Startup Validation:**

On first call to `get_langfuse_client()`, the config must be validated. If invalid:

1. Raise `ConfigurationError` with message describing the issue
2. Do NOT attempt to connect or create any spans
3. Log validation failure to `ml_langfuse.config` logger

---

## 3. Non-Functional Requirements

### NFR-11-01: Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Span creation overhead | < 1ms per span | Local benchmark with `time.perf_counter()` |
| Async tracer safety | 0 blocking calls in async context | Code review + async stress test |
| Batch export interval | Every 5 seconds or 100 spans | OTel SDK configuration |
| Memory bound | Max 10,000 pending spans in buffer | Overflow protection via SDK config |

### NFR-11-02: Security

| Requirement | Implementation |
|-------------|----------------|
| No PII in spans | Only scores/flags/tags; no user content |
| API keys not logged | Keys stored in env vars only, never in span attributes |
| TLS for all Langfuse cloud traffic | Enforced by `langfuse` SDK default |
| Self-hosted network isolation | Documented requirement for infra team |

### NFR-11-03: Compliance

| Requirement | Implementation |
|-------------|----------------|
| SOX audit trail | Append-only audit entries for human decisions |
| GDPR Art.22 | `human_decision` and `decided_by` fields; no automated profiling |
| HIPAA (if applicable) | `compliance_tags` field; no PHI in span attributes |
| Data retention | Configurable `audit_retention_days` per tag category |

### NFR-11-04: Reliability

| Scenario | Behavior |
|----------|----------|
| Langfuse unreachable | Graceful degradation; spans dropped, no blocking |
| OTLP exporter retry | Exponential backoff via OTel SDK |
| Buffer overflow | Oldest spans dropped (ring buffer behavior) |
| Process crash | `atexit` handler flushes pending spans |
