# Feature #11: Langfuse Observability — Test Plan

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 04-testing  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Draft  

---

## 1. Test Strategy

### 1.1 Test Pyramid

| Layer | Scope | Tools | Coverage Target |
|-------|-------|-------|----------------|
| Unit | `ml_langfuse` module internals (config, span validation, decorators) | `pytest`, `pytest-mock` | 100% |
| Integration | Langfuse client init, trace context propagation across async boundaries | `pytest-asyncio`, real env var injection | 100% |
| E2E | Full pipeline span emission → Langfuse UI query | Manual + API tests | > 90% |

### 1.2 Test Configuration

**Environment:**

```bash
# Unit/Integration tests (CI)
LANGFUSE_PUBLIC_KEY=test_pk
LANGFUSE_SECRET_KEY=test_sk
LANGFUSE_HOST=https://cloud.langfuse.com
OTEL_SERVICE_NAME=methodology-v2-test
```

**Isolation:** Each test class has its own isolated `client.py` singleton reset via `pytest.fixture(autouse=True)` with `client._initialized = False`.

---

## 2. Test Cases

### 2.1 `ml_langfuse/test_client.py` — Client Tests

#### TC-01: `test_client_init_success_cloud_mode`

**Setup:** Env vars `LANGFUSE_PUBLIC_KEY=pk_test`, `LANGFUSE_SECRET_KEY=sk_test` set.

**Steps:**
1. Call `get_langfuse_client()`
2. Assert client is not `None`
3. Assert client has `get_tracer()` method

**Expected:** Client initializes without exception.

---

#### TC-02: `test_client_init_success_self_hosted_mode`

**Setup:** Env var `LANGFUSE_HOST=https://lf.example.com` set; `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` unset.

**Steps:**
1. Call `get_langfuse_client()`
2. Assert client is not `None`

**Expected:** Client initializes in self-hosted mode.

---

#### TC-03: `test_client_init_missing_required_vars`

**Setup:** All Langfuse-related env vars unset.

**Steps:**
1. Call `get_langfuse_client()`

**Expected:** `ConfigurationError` raised with message mentioning missing keys.

---

#### TC-04: `test_client_init_invalid_sampling_rate`

**Setup:** Env vars valid, but `LANGFUSE_TRACE_SAMPLING_RATE=1.5` set.

**Steps:**
1. Call `get_langfuse_client()`

**Expected:** `ConfigurationError` raised with message about sampling rate range.

---

#### TC-05: `test_client_singleton`

**Steps:**
1. Call `get_langfuse_client()` twice
2. Assert both calls return the **same object** (identity check via `is`)

**Expected:** Singleton behavior; only one client instance per process.

---

#### TC-06: `test_client_flush`

**Setup:** Valid client initialized.

**Steps:**
1. Call `client.flush()`
2. Assert no exception

**Expected:** Flush completes without error.

---

### 2.2 `ml_langfuse/test_trace.py` — Trace Context Tests

#### TC-07: `test_get_current_trace_context_no_active_span`

**Setup:** No active span.

**Steps:**
1. Call `get_current_trace_context()`

**Expected:** Returns dict with `trace_id=None, span_id=None, trace_flags=0`.

---

#### TC-08: `test_get_current_trace_context_with_active_span`

**Setup:** Active span created via `tracer.start_as_current_span()`.

**Steps:**
1. Call `get_current_trace_context()` inside the span context
2. Assert `trace_id` is a valid 32-char hex string
3. Assert `span_id` is a valid 16-char hex string

**Expected:** Returns valid context from active span.

---

#### TC-09: `test_inject_and_extract_trace_context`

**Setup:** Active span context available.

**Steps:**
1. `carrier = {}`
2. `inject_trace_context(carrier)`
3. Assert `carrier["traceparent"]` matches W3C format `00-{32hex}-{16hex}-0{2hex}`
4. `extracted = extract_trace_context(carrier)`
5. Assert `extracted` is a valid OTel `Context`

**Expected:** Context round-trips correctly through carrier.

---

#### TC-10: `test_run_with_trace_context`

**Setup:** Valid trace context dict.

**Steps:**
1. `ctx = extract_trace_context({"traceparent": "00-0af765e2cd75ef2d70dc673f96d12085-a21d4b1edb19f7a0-01"})`
2. Result = `run_with_trace_context(ctx, some_async_coro())`
3. Assert result equals `await some_async_coro()` (function executes normally)

**Expected:** Coroutine runs within the injected trace context.

---

### 2.3 `ml_langfuse/test_span.py` — Span Tests

#### TC-11: `test_create_decision_span_all_required_fields`

**Steps:**
1. Call `create_decision_span(name="phase7.test", uaf_score=0.75, clap_flag=True, risk_score=0.45, hitl_gate="review", human_decision="approved", decided_by="human", compliance_tags=["GDPR Art.22"])`
2. Assert returned span is not `None`
3. Assert span is in recording state (not ended)

**Expected:** Span created with all 7 attributes set.

---

#### TC-12: `test_create_decision_span_invalid_hitl_gate`

**Steps:**
1. Call `create_decision_span()` with `hitl_gate="invalid_gate"`

**Expected:** `ValueError` raised.

---

#### TC-13: `test_create_decision_span_invalid_decided_by`

**Steps:**
1. Call `create_decision_span()` with `decided_by="robot"`

**Expected:** `ValueError` raised.

---

#### TC-14: `test_create_decision_span_uaf_score_out_of_range`

**Steps:**
1. Call `create_decision_span()` with `uaf_score=1.5`

**Expected:** `ValueError` raised.

---

#### TC-15: `test_create_decision_span_risk_score_out_of_range`

**Steps:**
1. Call `create_decision_span()` with `risk_score=-0.1`

**Expected:** `ValueError` raised.

---

#### TC-16: `test_create_decision_span_with_parent`

**Setup:** Parent span created first.

**Steps:**
1. Parent span = `tracer.start_span("parent")`
2. Child span = `create_decision_span(..., parent_span=parent_span)`
3. Assert child span's `parent_span_id` matches parent span's `span_id`

**Expected:** Child span correctly linked to parent.

---

#### TC-17: `test_end_span_with_status_ok`

**Setup:** Span created via `create_decision_span()`.

**Steps:**
1. `end_span_with_status(span, StatusCode.OK)`
2. Assert span is ended

**Expected:** Span ends with `OK` status.

---

#### TC-18: `test_end_span_with_status_error`

**Setup:** Span created via `create_decision_span()`.

**Steps:**
1. `end_span_with_status(span, StatusCode.ERROR, exception=ValueError("test"))`
2. Assert span status is `ERROR`
3. Assert exception recorded in span events

**Expected:** Span ends with `ERROR` status and exception recorded.

---

### 2.4 `ml_langfuse/test_decorators.py` — Decorator Tests

#### TC-19: `test_observe_llm_call_decorator`

**Setup:** Valid client initialized with mock tracer.

**Steps:**
1. Define: `@observe_llm_call(model_name="claude-3-opus") async def my_llm(prompt): return "response"`
2. Call `await my_llm("hello")`
3. Assert span was created with name starting with `llm.`

**Expected:** Decorator creates span; model name attribute set.

---

#### TC-20: `test_observe_decision_point_sync`

**Setup:** Valid client initialized.

**Steps:**
1. Define: `@observe_decision_point(point="risk_eval", phase="phase6") def sync_fn(state): return {"uaf_score": 0.8, "clap_flag": True, "risk_score": 0.3, "hitl_gate": "pass", "human_decision": None, "decided_by": "agent", "compliance_tags": []}`
2. Call `sync_fn({})`
3. Assert span was created with name `phase6.risk_eval`

**Expected:** Decorator creates span with correct name.

---

#### TC-21: `test_observe_decision_point_async`

**Setup:** Valid client initialized.

**Steps:**
1. Define: `@observe_decision_point_async(point="uaf_check", phase="phase7") async def async_fn(state): return {"uaf_score": 0.8, ...}`
2. Call `await async_fn({})`
3. Assert span was created

**Expected:** Async decorator creates span correctly.

---

#### TC-22: `test_observe_tool_call`

**Setup:** Valid client initialized.

**Steps:**
1. Define: `@observe_tool_call(tool_name="search") def tool_fn(q): return {"result": "found"}`
2. Call `tool_fn("query")`
3. Assert span was created with name starting with `tool.`

**Expected:** Tool spans created with correct name and I/O attributes.

---

#### TC-23: `test_observe_span_generic`

**Setup:** Valid client initialized.

**Steps:**
1. Define: `@observe_span(name="custom_op", attributes={"custom.attr": "val"}) async def op(): return 42`
2. Call `await op()`
3. Assert span created with custom attribute

**Expected:** Generic span with custom attributes created.

---

#### TC-24: `test_decorator_chaining`

**Setup:** Valid client initialized.

**Steps:**
1. Define a function with both `@observe_llm_call` and `@observe_decision_point` stacked
2. Call the function
3. Assert multiple spans created (one per decorator in chain)

**Expected:** Multiple spans created in chain.

---

## 3. Acceptance Test Criteria

| Criterion | Threshold |
|-----------|-----------|
| Unit test pass rate | 100% |
| Integration test pass rate | 100% |
| Code coverage | > 80% line coverage |
| Async test stability | 0 flaky tests across 3 CI runs |

---

## 4. Manual Test Scenarios

### MT-01: Langfuse UI — Real-Time View

**Steps:**
1. Run the pipeline with Langfuse enabled
2. Open Langfuse UI → Traces
3. Apply filters: `hitl_gate=review`
4. Verify correct spans appear within 5s

**Expected:** Real-time trace view loads and filters correctly.

---

### MT-02: Audit Log Export

**Steps:**
1. Trigger a human decision in the pipeline
2. Open Langfuse Admin → Audit Log
3. Export to CSV

**Expected:** CSV contains all audit fields for the human decision span.
