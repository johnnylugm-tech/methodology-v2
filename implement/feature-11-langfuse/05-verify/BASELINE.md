# Feature #11: Langfuse Observability — Baseline Measurement

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 05-verify / BASELINE  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Phase 5 — Implemented  

---

## 1. Baseline Context

This document records the pre-implementation state of the methodology-v2 observability layer. Feature #11 introduces a new `ml_langfuse` package; there is no prior implementation to compare against.

**Baseline = "greenfield"**: no Langfuse integration existed before this feature.

---

## 2. Current State (Pre-Feature #11)

### 2.1 Existing Observability

| Component | State Before |
|-----------|-------------|
| AI decision spans | No instrumentation |
| Risk score logging | Print-based / ad-hoc logging only |
| UAF/CLAP fields | Stored in pipeline state dict, not queryable externally |
| HITL audit trail | No centralized audit log |
| Trace propagation | None (no W3C TraceContext) |
| Langfuse | Not integrated |

---

## 3. Target Post-Implementation State

After Phase 1, the following will be measurable:

| Metric | Target |
|--------|--------|
| Span creation overhead | < 1ms per span |
| Required fields coverage | 7/7 fields present on every AI decision span |
| Config validation coverage | All 8 env vars validated at startup |
| Decorator coverage | 5 decorators implemented |
| Test coverage | > 80% line coverage |
| Test pass rate | 100% (all 50 tests) |

---

## 4. Verification Plan

| Check | Method | Expected |
|-------|--------|----------|
| Client init in cloud mode | Run `get_langfuse_client()` with env vars | Returns client without exception |
| Client init in self-hosted mode | Run with `LANGFUSE_HOST` set | Returns client without exception |
| Client init missing vars | Run without any credentials | `ConfigurationError` raised |
| All 7 required fields on span | Unit test inspects span attributes | 7 attributes present |
| Trace context propagation | Inject → extract roundtrip | Same trace_id recovered |
| Decorator creates span | Unit test with mock tracer | Span created with correct name |
| Exception re-raised from decorator | Unit test with failing function | Exception propagates |
| Config singleton | Two calls to `get_config()` | Same object returned |
