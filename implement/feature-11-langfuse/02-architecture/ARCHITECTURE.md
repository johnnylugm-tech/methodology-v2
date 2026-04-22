# Feature #11: Langfuse Observability — Architecture

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 02-architecture  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Draft  

---

## 1. Architecture Overview

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **OTel Native** | Use OpenTelemetry SDK as the primary tracing API; Langfuse acts as an OTel-compatible backend |
| **Zero-Drift Instrumentation** | Decorator-based auto-instrumentation requires minimal code changes to existing pipeline nodes |
| **Graceful Degradation** | Langfuse unavailability must never block the main pipeline |
| **Audit-First** | Human decision audit entries are append-only and indexed for compliance queries |

### 1.2 Component Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                     methodology-v2 Pipeline                       │
│  Phase 6: Risk Management  │  Phase 7: Decision Gate           │
│  ┌────────────────────────┐  │  ┌──────────────────────────┐   │
│  │ risk_evaluation()      │  │  │ uaf_check()              │   │
│  │ @observe_decision_pt  │  │  │ @observe_decision_pt     │   │
│  └──────────┬────────────┘  │  └──────────┬───────────────┘   │
│             │                │             │                    │
│  ┌──────────┴────────────┐  │  ┌──────────┴───────────────┐  │
│  │ clap_evaluation()     │  │  │ hitl_gate()               │  │
│  │ @observe_decision_pt  │  │  │ @observe_decision_pt       │  │
│  └──────────┬────────────┘  │  └──────────┬───────────────┘   │
│             │                │             │                    │
│  ┌──────────┴────────────┐  │  ┌──────────┴───────────────┐  │
│  │ @observe_llm_call     │  │  │ @observe_llm_call        │  │
│  │ (LLM call wrappers)   │  │  │ (LLM call wrappers)      │  │
│  └───────────────────────┘  │  └──────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ml_langfuse Layer                             │
│  ┌──────────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐ │
│  │ client.py    │  │ config.py│  │ trace.py│  │ span.py      │ │
│  │ Singleton   │  │ Pydantic │  │ Context │  │ create_span()│ │
│  │ Langfuse+OTel│  │ Config   │  │ Propag. │  │ 7 req. attrs │ │
│  └──────┬───────┘  └──────────┘  └─────────┘  └──────────────┘ │
│         │                      ┌────────────┐                    │
│         │                      │decorators.py│                   │
│         │                      │@observe_*   │                   │
│         │                      └────────────┘                    │
└─────────┼────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│                   OpenTelemetry SDK                              │
│  TracerProvider → SpanProcessor → SimpleSpanProcessor / BatchSpan│
│  OTLP Exporter ──────────────────────────────────────────────────►│
└──────────────────────────────────────────────────────────────────┘
          │
          ▼ (OTLP Protocol over HTTP/gRPC)
┌──────────────────────────────────────────────────────────────────┐
│               Langfuse (Cloud or Self-Hosted)                    │
│  Trace Storage → Query API → Dashboards / Audit Log              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Design

### 2.1 `ml_langfuse/__init__.py`

**Purpose:** Package entry point; re-exports public API.

```python
"""ml_langfuse — OTel-native Langfuse integration for methodology-v2."""

from ml_langfuse.client import get_langfuse_client, LangfuseClient, ConfigurationError
from ml_langfuse.config import LangfuseConfig, get_config
from ml_langfuse.trace import (
    get_current_trace_context,
    inject_trace_context,
    extract_trace_context,
    run_with_trace_context,
)
from ml_langfuse.span import (
    create_decision_span,
    end_span_with_status,
)
from ml_langfuse.decorators import (
    observe_llm_call,
    observe_decision_point,
    observe_decision_point_async,
    observe_tool_call,
    observe_span,
)

__all__ = [
    "get_langfuse_client",
    "LangfuseClient",
    "ConfigurationError",
    "LangfuseConfig",
    "get_config",
    "get_current_trace_context",
    "inject_trace_context",
    "extract_trace_context",
    "run_with_trace_context",
    "create_decision_span",
    "end_span_with_status",
    "observe_llm_call",
    "observe_decision_point",
    "observe_decision_point_async",
    "observe_tool_call",
    "observe_span",
]
```

---

### 2.2 `ml_langfuse/config.py`

**Purpose:** Centralized configuration management with Pydantic validation.

**Class: `LangfuseConfig`**

Inherits from `pydantic.BaseModel`. Fields:

| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `mode` | `Literal["cloud", "self_hosted"]` | `"cloud"` | Required |
| `public_key` | `str` | `""` | Required if `mode=="cloud"` |
| `secret_key` | `str` | `""` | Required if `mode=="cloud"` |
| `host` | `str` | `""` | Required if `mode=="self_hosted"` |
| `otel_exporter_endpoint` | `str` | `""` | Valid URL format |
| `otel_service_name` | `str` | `"methodology-v2"` | Non-empty |
| `trace_sampling_rate` | `float` | `1.0` | `0.0 <= x <= 1.0` |
| `dashboard_poll_interval_seconds` | `int` | `5` | `> 0` |
| `audit_retention_days` | `int` | `90` | `> 0` |

**Config Resolution Order (priority high → low):**

1. Environment variables (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, etc.)
2. `config.yaml` file in project root (key: `ml_langfuse`)
3. Hardcoded defaults

**Validation Method:**

```python
def validate_config(self) -> None:
    """Raise ConfigurationError if config is invalid."""
    if self.mode == "cloud":
        if not self.public_key or not self.secret_key:
            raise ConfigurationError("Cloud mode requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
    elif self.mode == "self_hosted":
        if not self.host:
            raise ConfigurationError("Self-hosted mode requires LANGFUSE_HOST")
    if not 0.0 <= self.trace_sampling_rate <= 1.0:
        raise ConfigurationError("trace_sampling_rate must be in [0.0, 1.0]")
```

---

### 2.3 `ml_langfuse/client.py`

**Purpose:** Langfuse client singleton with OTel registration.

**Singleton Pattern:**

```python
_client: Optional[LangfuseClient] = None
_initialized: bool = False

def get_langfuse_client() -> LangfuseClient:
    global _client, _initialized
    if _initialized:
        return _client
    config = get_config()
    config.validate_config()
    _client = LangfuseClient(config)
    _client._setup_otel()
    _initialized = True
    return _client
```

**Class: `LangfuseClient`**

```python
class LangfuseClient:
    def __init__(self, config: LangfuseConfig): ...
    def _setup_otel(self) -> None:
        # 1. Create TracerProvider
        # 2. Set global default TracerProvider
        # 3. Configure OTLP exporter (cloud or self-hosted)
        # 4. Register BatchSpanProcessor with max 100 spans / 5s flush
        # 5. Register atexit handler for graceful flush
    def get_tracer(self, name: str) -> "Tracer":
        """Return an OTel Tracer for the given name."""
    def create_span(self, name: str, **kwargs) -> Span:
        """Convenience method wrapping span.py:create_decision_span()"""
    def flush(self) -> None:
        """Force-flush all pending spans."""
```

**OTel Setup Flow:**

```
1. Read config → get Langfuse SDK config
2. langfuse = LangfuseSDK(config)        # Standard Langfuse init
3. tracer_provider = TracerProvider(
       resource=Resource.create({"service.name": config.otel_service_name}),
       span_processor=BatchSpanProcessor(
           OTLPExporter(
               endpoint=config.otel_exporter_endpoint or DEFAULT_LANGFUSE_OTLP_ENDPOINT
           )
       )
   )
4. set_tracer_provider(tracer_provider)   # OTel global registry
5. tracer = tracer_provider.get_tracer(config.otel_service_name)
```

---

### 2.4 `ml_langfuse/trace.py`

**Purpose:** W3C TraceContext propagation utilities.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `get_current_trace_context` | `() -> dict` | Extract `{trace_id, span_id, trace_flags}` from current active span |
| `inject_trace_context` | `(carrier: dict) -> dict` | Inject context into `carrier` (HTTP headers, dict) |
| `extract_trace_context` | `(carrier: dict) -> Context` | Extract from `carrier`, return OTel `Context` |
| `run_with_trace_context` | `(ctx: Context, coro: Coroutine) -> Any` | Run coroutine within given context |

**Implementation Notes:**

- Uses `opentelemetry.trace.get_current_span()` to get active span
- Uses `opentelemetry.propagate.inject()` / `extract()` for carrier operations
- `run_with_trace_context` uses `contextmanager` + `asyncio.create_task()` with `set_up_context()`

---

### 2.5 `ml_langfuse/span.py`

**Purpose:** Span creation utilities with all 7 required attributes.

**Core Function:**

```python
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
    tracer: Optional["Tracer"] = None,
) -> Span:
    """
    Create and start an OTel span with all 7 required attributes.
    
    Args:
        name: Span name (e.g. "phase7.hitl_gate")
        uaf_score: User Authorization Factor score [0.0, 1.0]
        clap_flag: Content Legitimacy Assessment Protocol result
        risk_score: Aggregated risk score [0.0, 1.0]
        hitl_gate: "pass" | "review" | "block"
        human_decision: Human decision string or None
        decided_by: "agent" | "human" | "system"
        compliance_tags: List of compliance tag strings
        parent_span: Optional parent span for hierarchical tracing
        tracer: Optional OTel Tracer; defaults to ml_langfuse's global tracer
    
    Returns:
        The started Span object.
    
    Raises:
        ValueError: If hitl_gate not in ["pass", "review", "block"]
        ValueError: If decided_by not in ["agent", "human", "system"]
        ValueError: If uaf_score or risk_score outside [0.0, 1.0]
    """
```

**Attribute Validation:**

All 7 required attributes are validated before being set on the span:

```python
# Validation before span creation
assert 0.0 <= uaf_score <= 1.0, "uaf_score must be in [0.0, 1.0]"
assert 0.0 <= risk_score <= 1.0, "risk_score must be in [0.0, 1.0]"
assert hitl_gate in ("pass", "review", "block"), f"Invalid hitl_gate: {hitl_gate}"
assert decided_by in ("agent", "human", "system"), f"Invalid decided_by: {decided_by}"
```

**Span Lifecycle:**

```
create_decision_span()
    → start_span() [context manager or explicit]
    → set_attribute() for each of 7 required fields
    → set_attribute() for optional standard fields
    → return span
    → (caller later calls span.end())
```

---

### 2.6 `ml_langfuse/decorators.py`

**Purpose:** Zero-boilerplate auto-instrumentation decorators.

**Decorator: `@observe_llm_call`**

```python
def observe_llm_call(
    model_name: str,
    model_version: Optional[str] = None,
):
    """Decorator that wraps an LLM call and auto-captures tracing attributes."""
```

**Decorator: `@observe_decision_point` (sync) and `@observe_decision_point_async` (async)**

```python
def observe_decision_point(point: str, phase: str = "phase6"):
    """Decorator that marks a decision node and emits all 7 required fields."""
```

**Decorator: `@observe_tool_call`**

```python
def observe_tool_call(tool_name: str):
    """Decorator that wraps tool invocations with latency and I/O tracking."""
```

**Decorator: `@observe_span`**

```python
def observe_span(name: str, attributes: Optional[dict] = None):
    """Generic span wrapper for arbitrary operations."""
```

**Decorator Chaining Logic:**

Each decorator follows this pattern:

```python
def decorator_factory(**decorator_kwargs):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_langfuse_client().get_tracer(__name__)
            with tracer.start_as_current_span(func.__name__) as span:
                # Set decorator-specific attributes
                span.set_attribute(...)
                # Call original function
                result = await func(*args, **kwargs)
                # Record result attributes
                return result
        return wrapper
    return decorator
```

---

## 3. Data Flow

### 3.1 Pipeline Span Flow

```
Pipeline Execution
│
├─ Phase 6 Node: risk_evaluation()
│   └─ @observe_decision_point(point="risk_evaluation", phase="phase6")
│       └─ create_decision_span(
│             name="phase6.risk_evaluation",
│             uaf_score=0.85, clap_flag=True, risk_score=0.32,
│             hitl_gate="review", human_decision=None,
│             decided_by="agent", compliance_tags=["GDPR Art.22"]
│         )
│           └─ span.end()
│
├─ Phase 7 Node: uaf_check()
│   └─ @observe_decision_point(point="uaf_check", phase="phase7")
│       └─ create_decision_span(...)
│
└─ Phase 7 Node: hitl_gate()
    └─ @observe_decision_point(point="hitl_gate", phase="phase7")
        └─ create_decision_span(...)
            └─ if decided_by=="human": create_audit_entry()
```

### 3.2 Trace Context Flow

```
Request enters (HTTP)
    │
    ▼
extract_trace_context(headers)
    │
    ▼
run_with_trace_context(ctx, pipeline_coro)
    │
    ├── Phase 6: risk_evaluation()
    │   └── creates child span with parent=ctx
    │
    └── Phase 7: uaf_check()
        └── creates child span with parent=ctx
            │
            ▼
            HTTP call to downstream service
                │
                ▼
                inject_trace_context(headers)
                    │
                    ▼
                    Downstream receives ctx, creates child span
```

---

## 4. Error Handling

### 4.1 Error Strategy

| Error | Handling |
|-------|----------|
| Missing env var at startup | `ConfigurationError` → fail fast with clear message |
| Invalid env var value | `ConfigurationError` → fail fast |
| Langfuse/OTel unreachable | Span dropped (graceful degradation), pipeline continues |
| OTLP export failure | OTel SDK retry with exponential backoff; then drop span |
| Span attribute validation error | `ValueError` raised from `create_decision_span()` |
| Decorator on non-async function without expected return | Log warning, span created with empty attributes |

### 4.2 Logging

All errors are logged to `ml_langfuse` logger:

```python
import logging
logger = logging.getLogger("ml_langfuse")
```

| Event | Level | Message |
|-------|-------|---------|
| Config validation failure | ERROR | "ml_langfuse configuration invalid: {detail}" |
| Langfuse unreachable | WARNING | "Langfuse unreachable, traces will be dropped" |
| Span attribute validation error | ERROR | "Invalid attribute {name}={value}: {detail}" |
| Audit entry created | INFO | "Audit entry created for trace_id={trace_id}" |

---

## 5. Package Structure

```
ml_langfuse/
├── __init__.py          # Public API re-exports
├── client.py            # Langfuse client singleton + OTel setup
├── config.py            # Pydantic config model + validation
├── trace.py             # TraceContext propagation helpers
├── span.py              # Span creation with 7 required attributes
└── decorators.py        # @observe_* decorators
```

---

## 6. Dependencies

| Package | Version | Role |
|---------|---------|------|
| `langfuse` | >= 3.0 | Langfuse Python SDK |
| `opentelemetry-api` | >= 1.20 | OTel API |
| `opentelemetry-sdk` | >= 1.20 | OTel SDK |
| `opentelemetry-exporter-otlp` | >= 1.20 | OTLP HTTP exporter |
| `opentelemetry-instrumentation-langchain` | >= 0.30b | LangChain auto-instrumentation |
| `opentelemetry-propagate` | >= 1.20 | W3C TraceContext propagation |
| `opentelemetry-instrumentation-asyncio` | >= 0.40b | Async context propagation |
| `pydantic` | >= 2.0 | Config validation |
| `pytest` | >= 7.0 | Test framework |
| `pytest-asyncio` | >= 0.21 | Async test support |
| `pytest-mock` | >= 3.10 | Mocking utilities |
