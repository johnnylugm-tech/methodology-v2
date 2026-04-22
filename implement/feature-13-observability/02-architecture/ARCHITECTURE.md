# Feature #13 — Architecture Document

**Version:** 1.0.0
**Feature:** FR-13 Observability Enhancement
**Date:** 2026-04-22
**Phase:** 02-architecture

---

## 1. System Overview

### 1.1 Three Modules and Their Responsibilities

| Module | File | FR-ID | Core Responsibility |
|--------|------|-------|---------------------|
| `UqlmMetricsSpan` | `uqlm_metrics_span.py` | FR-13-01 | Write UQLM uncertainty score into active OTel spans |
| `DecisionLogWriter` | `decision_log.py` | FR-13-02 | Persist Planner decision rationale as YAML files |
| `EffortTracker` | `effort_metrics.py` | FR-13-03 | Track compute/time/token cost per agent run in SQLite |

### 1.2 Boundaries

- **UqlmMetricsSpan**: Span-level only; does not own storage or persistence.
- **DecisionLogWriter**: YAML-file-only; does not touch the Langfuse API.
- **EffortTracker**: SQLite-only; single-process, no cross-process sharing.

### 1.3 Integration with Existing Features

```
Feature #07 (UQLM)                      Feature #11 (Langfuse)
┌─────────────────────────┐             ┌──────────────────────────┐
│ detection.uncertainty_   │             │ ml_langfuse.span         │
│ score.UncertaintyScore  │────────────► │ ml_langfuse.trace         │
└─────────────────────────┘  inject     └──────────────────────────┘
                               attrs              ▲
                                                    │
                              ┌────────────────────┤
                              ▼                    │
                    ┌──────────────────┐          │
                    │  UqlmMetricsSpan  │──────────┘
                    └──────────────────┘
```

- **Feature #07** (`detection.uncertainty_score`): `UqlmMetricsSpan` receives `UncertaintyScore` objects and maps fields → OTel span attributes.
- **Feature #11** (`ml_langfuse`): All three modules write into spans managed by the OTel `Tracer` provided by Feature #11.

---

## 2. Architecture Diagram

```
[Planner Agent]
    │
    ├──► [UqlmMetricsSpan]
    │         │
    │         ├── attach_to_span(span, uqlm_result)
    │         │         │
    │         │         ▼ set_attribute("uqlm.uaf_score", ...)
    │         │         ▼ set_attribute("uqlm.decision", ...)
    │         │         ▼ set_attribute("uqlm.components", ...)
    │         │         ▼ set_attribute("uqlm.computation_time_ms", ...)
    │         │
    │         ▼
    │    [ml_langfuse Span] ──► [OTel TracerProvider] ──► [Langfuse Cloud]
    │
    ├──► [DecisionLogWriter]
    │         │
    │         ▼ write(entry) / write_async(entry)
    │    [data/decision_logs/YYYY-MM-DD/{agent}_{seq:04d}.yaml]
    │
    └──► [EffortTracker]
              │
              ▼ start() → effort_id
              ▼ increment_*(effort_id)
              ▼ stop() → EffortRecord
         [data/effort_metrics.db]  (auto-flush: 30s or ≥100 records)
```

---

## 3. Module Detailed Design

### 3.1 uqlm_metrics_span.py

**File:** `observability/uqlm_metrics_span.py`

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
        """
        Write UQLM attributes to an already-existing span.
        Raises: none (graceful no-op if span is None).
        """

    @staticmethod
    def create_span_with_uqlm(
        tracer: "Tracer",
        name: str,
        uqlm_result: "UqlmResult",   # from detection.uncertainty_score
        parent_span: Optional[Span] = None,
    ) -> Span:
        """
        Create a child span with UQLM attributes pre-populated.
        Calls tracer.start_span() then attach_to_span().
        """
```

**OTel span attributes written:**

| Attribute Key | Type | Value Source |
|---|---|---|
| `uqlm.uaf_score` | `float` | `uqlm_result.score` |
| `uqlm.decision` | `str` | `uqlm_result.decision` |
| `uqlm.components` | `dict` | `uqlm_result.components` |
| `uqlm.computation_time_ms` | `float` | `uqlm_result.computation_time_ms` |

**Integration with `ml_langfuse.span`:**

`create_span_with_uqlm` calls `tracer.start_span(name, parent=parent_span)` — the returned `Span` object is the same type used by `ml_langfuse.span`. After attributes are set, the span is returned to the caller who is responsible for calling `span.end()` or `span.flush()`.

**Integration with `detection.uncertainty_score`:**

The `uqlm_result` parameter is typed as `UqlmResult` (from Feature #07). The staticmethod unpacks `score`, `decision`, `components`, and `computation_time_ms` fields from that object and writes them as OTel attributes.

**Error handling:** If any field is `None` or missing, the attribute is skipped (not written). No exception propagates.

---

### 3.2 decision_log.py

**File:** `observability/decision_log.py`

```python
@dataclass
class DecisionLogEntry:
    trace_id: str
    span_id: str
    agent_id: str
    timestamp: str          # ISO 8601
    decision: str           # "proceed" | "escalate" | "block"
    reasoning: str
    options_considered: list[str]
    chosen_action: str
    uaf_score: float
    risk_score: float
    hitl_gate: str
    metadata: dict

class DecisionLogWriter:
    def __init__(self, data_dir: Optional[str] = None) -> None: ...
    def write(self, entry: DecisionLogEntry) -> Path: ...
    def write_async(self, entry: DecisionLogEntry) -> asyncio.Task: ...
    def flush(self) -> None: ...

class DecisionLogReader:
    def read(self, path: Path) -> DecisionLogEntry: ...
    def query_by_date(self, date: str) -> list[DecisionLogEntry]: ...  # YYYY-MM-DD
    def query_by_agent(self, agent_id: str) -> list[DecisionLogEntry]: ...
```

**File naming pattern:**

```
data/decision_logs/{date}/{agent_id}_{seq:04d}.yaml
```

- `date`: `YYYY-MM-DD` of the decision (from entry timestamp)
- `agent_id`: from `entry.agent_id`
- `seq`: zero-padded 4-digit sequential counter, **unique per agent per day**

**Sequence counter implementation:**

The writer maintains an in-memory `dict[tuple[str, str], int]` (`_seq_cache: dict[(agent_id, date), int]`) keyed by `(agent_id, date_string)`. On every `write()`:

1. Increment the cached counter for that key.
2. If no counter exists for the key, read the last-written sequence from the directory (scan existing files matching `{agent_id}_*.yaml`) to find the current max, then increment from there.
3. Format as `f"{counter:04d}"`.

This means the same agent writing decisions throughout the day always gets an incrementing sequence number.

**Async write implementation:**

```python
def write_async(self, entry: DecisionLogEntry) -> asyncio.Task:
    return asyncio.create_task(self._async_write(entry))

async def _async_write(self, entry: DecisionLogEntry) -> None:
    path = self._resolve_path(entry)
    yaml_str = self._serialize(entry)
    await asyncio.to_thread(self._write_file, path, yaml_str)
```

`asyncio.create_task` is used so the caller can fire-and-forget. The actual I/O is moved to a thread pool via `asyncio.to_thread` to avoid blocking the event loop. This satisfies "async write" as non-blocking, not as async I/O.

**YAML serialization:** Uses `PyYAML`. On serialization failure, falls back to writing the same data as JSON in the same directory.

**Fallback on YAML write failure:** Writes `{agent}_{seq:04d}.json` alongside the YAML attempt.

**DATA_DIR resolution:**

```python
# Priority: env var > default relative path
_data_dir = os.environ.get("DECISION_LOG_DIR") or str(
    Path(__file__).resolve().parents[2] / "data"
)
```

`parents[2]` from `observability/decision_log.py` → `03-implement/` → `feature-13-observability/` → workspace root.

---

### 3.3 effort_metrics.py

**File:** `observability/effort_metrics.py`

```python
@dataclass
class EffortRecord:
    trace_id: str
    span_id: str
    agent_id: str
    timestamp: str          # ISO 8601
    time_spent_ms: int = 0
    tokens_consumed: int = 0
    iteration_count: int = 0
    calls_count: int = 0
    metadata: dict = field(default_factory=dict)

class EffortTracker:
    def __init__(self, db_path: Optional[str] = None) -> None: ...
    def start(self, agent_id: str) -> str: ...   # returns effort_id (UUID)
    def stop(self, effort_id: str) -> EffortRecord: ...
    def increment_iteration(self, effort_id: str) -> None: ...
    def increment_calls(self, effort_id: str) -> None: ...
    def add_tokens(self, effort_id: str, count: int) -> None: ...
    def record(self, record: EffortRecord) -> None: ...  # direct insert
    def query(self, trace_id: str) -> list[EffortRecord]: ...
    def flush(self) -> None: ...  # force flush buffered records
```

**SQLite schema:**

```sql
CREATE TABLE IF NOT EXISTS effort_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id        TEXT NOT NULL,
    span_id         TEXT NOT NULL,
    agent_id        TEXT NOT NULL,
    timestamp       TEXT NOT NULL,
    time_spent_ms   INTEGER NOT NULL,
    tokens_consumed INTEGER NOT NULL DEFAULT 0,
    iteration_count INTEGER NOT NULL DEFAULT 0,
    calls_count     INTEGER NOT NULL DEFAULT 0,
    metadata        TEXT
);
CREATE INDEX IF NOT EXISTS idx_trace_id ON effort_metrics(trace_id);
CREATE INDEX IF NOT EXISTS idx_agent_timestamp ON effort_metrics(agent_id, timestamp);
```

**DATA_DIR resolution (same pattern as decision_log):**

```python
_data_dir = os.environ.get("EFFORT_METRICS_DIR") or str(
    Path(__file__).resolve().parents[2] / "data"
)
db_path = db_path or os.path.join(_data_dir, "effort_metrics.db")
```

**Flush policy:**

The tracker maintains an in-memory buffer of up to 100 `EffortRecord` objects. Two conditions trigger a flush:

1. **Time-based:** A `threading.Timer` fires every **30 seconds**, calling `flush()`.
2. **Count-based:** When `len(self._buffer) >= 100`, flush immediately.

```python
class EffortTracker:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._lock = threading.RLock()
        self._buffer: list[EffortRecord] = []
        self._setup_flush_timer(interval=30.0)

    def _setup_flush_timer(self, interval: float) -> None:
        def _tick() -> None:
            self.flush()
            self._flush_timer = threading.Timer(interval, _tick)
            self._flush_timer.start()
        self._flush_timer = threading.Timer(interval, _tick)
        self._flush_timer.start()
```

`flush()` acquires the lock, bulk-inserts all buffered records into SQLite, then clears the buffer. If SQLite write fails, the error is logged to stderr and the buffer is preserved so records are not lost.

**Thread safety:**

All public methods (`start`, `stop`, `increment_*`, `add_tokens`, `record`, `query`, `flush`) acquire `self._lock` (a `threading.RLock`). The flush timer callback also acquires the lock. No operations hold the lock across I/O boundaries.

---

### 3.4 integration.py

**File:** `observability/integration.py`

```python
def setup_observability(
    tracer: "Tracer",
) -> tuple[UqlmMetricsSpan, DecisionLogWriter, EffortTracker]:
    """
    Initialize all three observability components.

    Returns (uqlm_span, decision_writer, effort_tracker) in order.
    DATA_DIR resolved automatically from environment or workspace root.
    """
```

**Behavior:**

1. Creates `UqlmMetricsSpan(tracer=tracer)`.
2. Creates `DecisionLogWriter()` with default `data_dir=None` (auto-resolved).
3. Creates `EffortTracker()` with default `db_path=None` (auto-resolved).
4. Starts the EffortTracker flush timer.
5. Returns the 3-tuple.

Callers receive the three ready-to-use components and are responsible for calling `effort_tracker.flush()` on shutdown if graceful teardown is desired.

---

## 4. Data Flow

### Path A: UQLM Score → Langfuse Trace

```
detection.uncertainty_score.UncertaintyScoreCalculator.compute()
    │
    ▼  UncertaintyScore(score=0.35, decision="proceed",
         components={"total": 0.35, ...}, computation_time_ms=12.4)
UqlmMetricsSpan.create_span_with_uqlm(tracer, "planner-decision", uqlm_result)
    │
    ├── tracer.start_span("planner-decision", parent=parent_span)
    │
    ├── span.set_attribute("uqlm.uaf_score", 0.35)
    ├── span.set_attribute("uqlm.decision", "proceed")
    ├── span.set_attribute("uqlm.components", {"total": 0.35, ...})
    ├── span.set_attribute("uqlm.computation_time_ms", 12.4)
    │
    ▼
span.end() / span.flush()
    │
    ▼
OTel BatchSpanProcessor → Langfuse Cloud
    │
    ▼
Langfuse Dashboard — filterable by uqlm.uaf_score, uqlm.decision
```

### Path B: Planner Decision → Decision Log

```
Planner makes decision
    │
    ▼ DecisionLogEntry(agent_id="planner", decision="proceed", ...)
DecisionLogWriter.write(entry)
    │
    ├── _resolve_path(entry)
    │      agent_id="planner", date="2026-04-22", seq=0012
    │      → data/decision_logs/2026-04-22/planner_0012.yaml
    │
    ▼
YAML dump → file write (sync)
    │
    ▼ (on failure)
fallback JSON in same directory
    │
    ▼ (if write_async)
asyncio.create_task(_async_write(entry))
    │      asyncio.to_thread(self._write_file, path, yaml_str)
    ▼ (fire-and-forget)
```

### Path C: Agent Run → Effort Metrics

```
Agent run starts
    │
    ▼ EffortTracker.start(agent_id="planner") → effort_id="uuid-abc"
in-memory map: effort_id → {start_time, iteration_count=0, calls_count=0, tokens=0}
    │
    ▼ (per operation)
EffortTracker.increment_iteration(effort_id)
    │   OR
EffortTracker.increment_calls(effort_id)
    │   OR
EffortTracker.add_tokens(effort_id, count=150)
    │
    ▼ (run ends)
EffortTracker.stop(effort_id) → EffortRecord(time_spent_ms=2341, ...)
    │
    ▼ (auto-flush trigger: 30s timer OR buffer ≥ 100)
EffortTracker.flush() — acquires lock, bulk INSERT to SQLite, clear buffer
    │
    ▼ (SQLite write failure)
log to stderr, keep buffer, retry on next flush
```

---

## 5. Error Handling

| Failure | Handling |
|---------|----------|
| Langfuse unreachable | OTel SDK's `BatchSpanProcessor` buffers spans; no exception propagates to application code |
| `uqlm_metrics_span.py` field missing | Skip that attribute; log at debug level |
| YAML write fails | Fallback: write same entry as JSON to same directory |
| SQLite write fails | Log `stderr.write(f"[EffortTracker] flush error: {e}")`; keep buffer; continue operation |
| `data/` directory missing | Create it automatically on first write |

---

## 6. Test Strategy

All tests live under `04-tests/test_obs/`.

**test_uqlm_metrics_span.py**

- Mock `trace.Span` using a simple dict-based fake that records `set_attribute` calls
- Verify: after `attach_to_span`, fake span contains `uqlm.uaf_score`, `uqlm.decision`, `uqlm.components`, `uqlm.computation_time_ms`
- Verify: `create_span_with_uqlm` calls `tracer.start_span` once with correct name and parent

**test_decision_log.py**

- Create `DecisionLogWriter` pointing at a temp dir
- Write 5 entries for same agent+date → verify sequence numbers are 0001–0005
- Round-trip: `write()` → `read()` → assert all fields match exactly
- `write_async()` returns an `asyncio.Task`; await it and verify file exists

**test_effort_metrics.py**

- Create `EffortTracker` against a temp SQLite file
- `start()` → `increment_iteration()` × 3 → `stop()` → `query()` by trace_id → assert counts
- Flush policy: populate buffer to 100 records, verify one `executemany` call
- Thread safety: spawn 10 threads calling `record()` concurrently; verify no exceptions and count is correct

**Important:** Tests must not modify any code under `implement/feature-0{6,7,8,9,10,11,12}/`.

---

## 7. Constraints and Limits

| Constraint | Value |
|------------|-------|
| SQLite scope | Single-process only; no cross-process sharing |
| Decision log write mode | Synchronous file I/O; async write is non-blocking fire-and-forget via `asyncio.create_task` |
| Langfuse fallback | `data/fallback_logs/uqlm_{timestamp}.jsonl` when OTel export fails |
| File path encoding | UTF-8 |
| Max effort buffer | 100 records before forced flush |
| Flush timer | 30 seconds, using `threading.Timer` |
| Python version | 3.10+ (for `asyncio.to_thread`) |

---

## 8. File Structure

```
implement/feature-13-observability/
├── 01-spec/SPEC.md
├── 02-architecture/ARCHITECTURE.md          ← this file
├── 03-implement/observability/
│   ├── __init__.py
│   ├── uqlm_metrics_span.py                # FR-13-01 (~130 lines)
│   ├── decision_log.py                     # FR-13-02 (~220 lines)
│   ├── effort_metrics.py                  # FR-13-03 (~180 lines)
│   └── integration.py                     # FR-13-04 (~40 lines)
└── 04-tests/test_obs/
    ├── __init__.py
    ├── test_uqlm_metrics_span.py           # (~90 lines)
    ├── test_decision_log.py                # (~160 lines)
    └── test_effort_metrics.py               # (~130 lines)
```