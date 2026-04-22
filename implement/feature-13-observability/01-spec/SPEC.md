# Feature #13: Observability Enhancement — Specification

**Version:** 1.0.0
**Feature ID:** FR-13
**Phase:** 01-spec
**Author:** methodology-v2 Agent
**Date:** 2026-04-22
**Status:** Phase 1 — Awaiting Architecture

---

## 1. Feature Overview

### 1.1 Purpose

Feature #13 extends the Langfuse observability layer (Feature #11) with three specialized components that enrich the trace data produced by the methodology-v2 pipeline.

### 1.2 Motivation

The existing Langfuse integration captures span-level timing and the 7 required decision attributes. However, it lacks:

- **UQLM uncertainty awareness in traces** — the UQLM module (Feature #07) computes an uncertainty score, but it never appears in Langfuse traces
- **Decision rationale logging** — when the Planner makes a decision, there is no persistent record of *why* a particular action was chosen
- **Agent effort tracking** — there is no metric for how much compute/time/tokens a given agent run consumes

### 1.3 Components

| # | Component | File | Description |
|---|-----------|------|-------------|
| 1 | UQLM Metrics Span | `uqlm_metrics_span.py` | Writes UQLM uncertainty score into OTel span attributes |
| 2 | Decision Log | `decision_log.py` | YAML-encoded decision rationale per agent run |
| 3 | Effort Metrics | `effort_metrics.py` | SQLite-based tracker for work-unit consumption |

---

## 2. Functional Requirements

### [FR-13-01] UQLM Metrics Span

**Module:** `observability/uqlm_metrics_span.py`

Injects UQLM uncertainty scores into active OTel spans. Integrates with:
- `ml_langfuse.span` (Feature #11) — uses the existing `Span` API
- `detection.uncertainty_score` (Feature #07) — accepts its output schema

**OTel Span Attributes:**

| Attribute Key | Type | Description |
|---------------|------|-------------|
| `uqlm.uaf_score` | `float` | Uncertainty-aware forecast score, range `[0.0, 1.0]` |
| `uqlm.decision` | `str` | Decision label: `proceed`, `review`, `block` |
| `uqlm.components` | `dict` | Per-component uncertainty breakdown |
| `uqlm.computation_time_ms` | `float` | UQLM computation elapsed time in ms |

**API:**

```python
class UqlmMetricsSpan:
    @staticmethod
    def attach_to_span(
        span: Span,
        uaf_score: float,
        decision: str,
        components: dict,
        computation_time_ms: float,
    ) -> None:
        """Write UQLM attributes to an existing span."""

    @staticmethod
    def create_span_with_uqlm(
        tracer: "Tracer",
        name: str,
        uqlm_result: "UqlmResult",   # from detection.uncertainty_score
        parent_span: Optional[Span] = None,
    ) -> Span:
        """Create a new child span with UQLM attributes pre-populated."""
```

### [FR-13-02] Decision Log

**Module:** `observability/decision_log.py`

Records every Planner decision as a YAML file on disk. Each log entry captures the full decision context for post-hoc audit and replay.

**Classes:**

```python
@dataclass
class DecisionLogEntry:
    trace_id: str
    span_id: str
    agent_id: str
    timestamp: str          # ISO 8601
    decision: str           # e.g. "proceed", "escalate", "block"
    reasoning: str          # free-text rationale
    options_considered: list[str]
    chosen_action: str
    uaf_score: float
    risk_score: float
    hitl_gate: str
    metadata: dict          # arbitrary extra context

class DecisionLogWriter:
    def write(entry: DecisionLogEntry) -> Path: ...
    def write_async(entry: DecisionLogEntry) -> asyncio.Task: ...

class DecisionLogReader:
    def read(path: Path) -> DecisionLogEntry: ...
    def query_by_date(date: str) -> list[DecisionLogEntry]: ...
    def query_by_agent(agent_id: str) -> list[DecisionLogEntry]: ...
```

**YAML Schema:**

```yaml
trace_id: "abc123"
span_id: "def456"
agent_id: "planner-alpha"
timestamp: "2026-04-22T14:30:00+08:00"
decision: "proceed"
reasoning: "Risk score below threshold; UAF favorable."
options_considered:
  - "proceed"
  - "escalate"
  - "block"
chosen_action: "proceed"
uaf_score: 0.82
risk_score: 0.15
hitl_gate: "pass"
metadata:
  session_id: "sess-789"
  user_id: "u001"
```

**Storage Path Pattern:** `data/decision_logs/{date}/{agent_id}_{seq:04d}.yaml`

- `data/` is relative to the project root (resolved via `Path(__file__).resolve().parents[2] / "data"` or `DATA_DIR` env var)
- `date` format: `YYYY-MM-DD`
- `seq` is a zero-padded 4-digit sequential counter, unique per agent per day

### [FR-13-03] Effort Metrics

**Module:** `observability/effort_metrics.py`

Tracks compute cost per agent run in a local SQLite database.

**Metrics Captured:**

| Metric | Type | Description |
|--------|------|-------------|
| `time_spent_ms` | `int` | Wall-clock elapsed time in ms |
| `tokens_consumed` | `int` | Total LLM tokens consumed |
| `iteration_count` | `int` | Number of agent loops |
| `calls_count` | `int` | Number of external tool/LLM calls |

**SQLite Schema:**

```sql
CREATE TABLE IF NOT EXISTS effort_metrics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id    TEXT NOT NULL,
    span_id     TEXT NOT NULL,
    agent_id    TEXT NOT NULL,
    timestamp   TEXT NOT NULL,        -- ISO 8601
    time_spent_ms    INTEGER NOT NULL,
    tokens_consumed  INTEGER NOT NULL DEFAULT 0,
    iteration_count  INTEGER NOT NULL DEFAULT 0,
    calls_count      INTEGER NOT NULL DEFAULT 0,
    metadata   TEXT                  -- JSON blob
);
CREATE INDEX IF NOT EXISTS idx_trace_id ON effort_metrics(trace_id);
CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON effort_metrics(agent_id, timestamp);
```

**Storage Path:** `data/effort_metrics.db` (resolved same as Decision Log)

**Class API:**

```python
@dataclass
class EffortRecord:
    trace_id: str
    span_id: str
    agent_id: str
    time_spent_ms: int = 0
    tokens_consumed: int = 0
    iteration_count: int = 0
    calls_count: int = 0
    metadata: dict = field(default_factory=dict)

class EffortTracker:
    def __init__(self, db_path: str = "data/effort_metrics.db"): ...
    def record(self, record: EffortRecord) -> None: ...
    def query(trace_id: str) -> list[EffortRecord]: ...
    def flush() -> None:  # force-write pending records
```

**Flush Policy:** Background flush every **30 seconds** OR when **≥ 100** records are buffered, whichever comes first.

### [FR-13-04] Langfuse Dashboard Integration

Explains how to query UQLM-enriched traces via the Langfuse SDK.

**Query Example — Get traces by decision:**

```python
from langfuse import Langfuse

client = Langfuse()

def get_traces_by_decision(decision: str, limit: int = 50):
    """
    Retrieve traces where uqlm.decision == decision.
    Useful for auditing all "block" decisions, for example.
    """
    return client.trace.list(
        tags=["methodology-v2"],
        metadata={"uqlm.decision": decision},
        limit=limit,
    )

# Usage
blocked_traces = get_traces_by_decision("block")
for trace in blocked_traces:
    print(trace.id, trace.metadata)
```

**Attributes Available in Langfuse Dashboard:**

All 4 UQLM span attributes (`uqlm.uaf_score`, `uqlm.decision`, `uqlm.components`, `uqlm.computation_time_ms`) appear as filterable/tr的可視化欄位 in the Langfuse UI under the trace's span detail panel.

---

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-13-01 | Latency — span attribute write | < 10ms |
| NFR-13-02 | Latency — decision log write | < 50ms |
| NFR-13-03 | Latency — effort record write | < 5ms |
| NFR-13-04 | Async Flush — decision log | Background `asyncio.create_task`, non-blocking |
| NFR-13-05 | Async Flush — effort | Flush every 30s or 100 records; uses `threading.Timer` |
| NFR-13-06 | Thread Safety | All shared state (buffers, file handles) protected by `threading.Lock` |
| NFR-13-07 | Graceful Degradation | If Langfuse unreachable, write UQLM attrs to fallback log; no crash |

---

## 4. Module Structure

```
implement/feature-13-observability/03-implement/observability/
├── __init__.py
├── uqlm_metrics_span.py   # FR-13-01
├── decision_log.py        # FR-13-02
├── effort_metrics.py      # FR-13-03
└── integration.py         # FR-13-04 helpers + combined setup
```

---

## 5. Dependencies

| Dependency | Source | Used By |
|------------|--------|---------|
| `ml_langfuse.span` | Feature #11 | All 3 components |
| `detection.uncertainty_score` | Feature #07 | FR-13-01 |
| `PyYAML` | PyPI | FR-13-02 |
| `sqlite3` | Python stdlib | FR-13-03 |
| `opentelemetry.trace` | OTel SDK | FR-13-01 |

---

## 6. Acceptance Criteria

| ID | Criterion | Testable By |
|----|-----------|-------------|
| AC-13-01 | `UqlmMetricsSpan.attach_to_span()` writes `uqlm.uaf_score` into the span's attributes and it is queryable | Unit test: create span → attach → verify attribute |
| AC-13-02 | `DecisionLogWriter.write()` produces a YAML file containing all schema fields; `DecisionLogReader.read()` reconstructs the entry losslessly | Unit test: round-trip |
| AC-13-03 | `EffortTracker.record()` stores `time_spent_ms` and `tokens_consumed`; `query()` retrieves them | Unit test: insert → select |
| AC-13-04 | When Langfuse is unreachable, no exception propagates; UQLM attrs fall back to local log | Integration test: mock unavailable endpoint |
| AC-13-05 | All pytest tests under `04-tests/` pass | `pytest 04-tests/` |
| AC-13-06 | `git diff --name-only` shows no modified files under `feature-0{6,7,8,9,10,11,12}/` | `git diff` |

---

## 7. Out of Scope

- Langfuse server installation or configuration (Feature #11 owns that)
- Dashboard UI customization beyond existing Langfuse capabilities
- Cross-process effort aggregation (single-process SQLite only)
- Real-time streaming of decision logs to external systems