# RISK_REGISTER.md — Feature #5: LLM Cascade

> Feature #5 of methodology-v3 upgrade
> Branch: `v3/llm-cascade`
> Last Updated: 2026-04-17

---

## Risk Register Table

| Risk ID | Category | Description | Likelihood | Impact | Risk Score | Mitigation | Owner |
|---------|----------|-------------|------------|--------|------------|------------|-------|
| LC-R01 | Integration | **API Client Stub Risk**: `api_clients/` modules are stubs not wired to real APIs. `call_model()` in `cascade_engine.py` returns simulated responses. Production use requires real API integration. | 5 | 4 | **20** | Complete api_clients wiring to real APIs (Anthropic, OpenAI, Google); add integration tests with live API keys; mock layer for test environments | @developer |
| LC-R02 | Technical | **Cascade Loop Risk**: Infinite escalation in edge cases where all models return low confidence — state machine could loop without termination guard | 2 | 4 | **8** | State machine has explicit EXHAUSTED terminal state; loop guard in `cascade_engine.py` tracks attempt count per request; hard cap configurable via `max_attempts_per_request` | @developer |
| LC-R03 | Financial | **Cost Overrun Risk**: Cascade exhausts all models sequentially; each model call incurs cost; worst case = cost of 5 API calls per request | 4 | 3 | **12** | Configurable `cost_cap` per request (default $0.50); cumulative cost budget tracked via `cost_tracker.py`; early termination when cost cap reached | @developer |
| LC-R04 | Performance | **Latency Budget Risk**: Cumulative latency across cascade chain exceeds SLA; each model adds latency; worst case = sum of all model latencies in chain | 4 | 3 | **12** | Configurable `latency_budget` (default 10s) enforced at cascade level; `health_tracker.py` tracks per-provider median latency; providers exceeding latency SLA are deprioritized | @developer |
| LC-R05 | Integration | **Provider Rate Limit Risk**: 429 from one provider triggers cascade to next; but next provider may also be rate-limited; cascading 429s could exhaust budget with zero output | 3 | 3 | **9** | `health_tracker.py` tracks rate-limit cooldowns per provider; providers in cooldown are skipped; exponential backoff not implemented (future enhancement) | @developer |
| LC-R06 | Technical | **Confidence Scoring Accuracy**: Low confidence flag may be wrong; scoring signals (entropy, repetition, length, parse_validity) are heuristics that can misjudge good outputs | 3 | 3 | **9** | Configurable confidence weights allow tuning per use case; threshold 0.7 is a starting point, not a guarantee; log all cascade decisions for offline analysis; fallback always available | @developer |
| LC-R07 | Technical | **State Machine Concurrent Access Risk**: Concurrent requests share `CascadeRouter` state; concurrent state transitions may corrupt shared state without locking | 2 | 4 | **8** | `CascadeRouter` uses threading lock (`threading.RLock`) for shared state; `cascade_engine.py` per-request state is isolated; concurrent unit tests cover basic race scenarios; full stress test deferred | @developer |
| LC-R08 | Integration | **Feature Interdependency Risk**: Features #1-3 (MCP/SAIF, Prompt Shields, Tiered Governance) integration hooks in `integration.py` are stubs; cascade may not respect governance policies in production | 3 | 4 | **12** | Complete integration with Features #1-3 before production; add integration tests verifying governance triggers; stub functions have clear TODO markers | @developer |
| LC-R09 | Financial | **Cost Tracking Lag**: `cost_tracker.py` tracks cost after response; if API provider bills after summary (e.g., tiered or overage), actual cost may exceed tracked estimate | 2 | 2 | **4** | Use provider-reported token counts (not estimates); compare tracked vs. actual monthly; add buffer margin to `cost_cap`; reconcile billing reports quarterly | @operator |
| LC-R10 | Operational | **Default Chain Not Optimal**: Default chain (Claude Opus → Sonnet → GPT-4o → GPT-4o-mini → Gemini-Pro) may not be optimal for all request types; routing is static priority, not adaptive | 3 | 2 | **6** | Default chain is configurable; `CascadeConfig.model_chain` accepts custom ordering; future: cost/latency/quality adaptive routing based on `ProviderHealth` rolling stats | @developer |
| LC-R11 | Technical | **Provider Health Stale Data**: `health_tracker.py` rolling stats may be stale if provider experiences prolonged outage; system continues routing to unhealthy provider until stats refresh | 2 | 3 | **6** | Rolling window has configurable `window_size`; providers with 0% success rate are flagged; manual health override available; heartbeat pings for liveness (future enhancement) | @developer |
| LC-R12 | Legal | **Multi-Provider Data Routing**: Routing requests across multiple LLM providers may have different data handling / GDPR implications per provider; user data may reach provider unexpectedly | 2 | 4 | **8** | Document which provider receives which request type; allow users to restrict providers via `excluded_providers`; governance policy per provider (Feature #3 integration); opt-in for cross-provider routing | @operator |

---

## Risk Score Summary

| Risk Score | Color | Count | Risks |
|------------|-------|-------|-------|
| 15–25 | 🔴 Critical | 2 | LC-R01, LC-R03 |
| 8–14 | 🟠 High | 6 | LC-R02, LC-R04, LC-R05, LC-R06, LC-R08, LC-R12 |
| 4–7 | 🟡 Medium | 3 | LC-R07, LC-R10, LC-R11 |
| 1–3 | 🟢 Low | 1 | LC-R09 |

---

## Risk Mitigation Summary

### Immediate Mitigations (Pre-Launch)

1. **LC-R01 API Client Stub Risk**: Wire `api_clients/` to real APIs before production; add mock layer for CI.
2. **LC-R03 Cost Overrun Risk**: Validate `cost_cap` enforcement end-to-end with test API keys; set conservative defaults.
3. **LC-R08 Feature Interdependency Risk**: Complete Features #1-3 integration; do not ship with stubbed governance hooks.

### Short-Term Mitigations (Post-Launch 30 days)

1. **LC-R04 Latency Budget Risk**: Profile realistic request workloads; calibrate `latency_budget` per SLA requirement.
2. **LC-R05 Provider Rate Limit Risk**: Add exponential backoff; implement circuit-breaking per provider.
3. **LC-R06 Confidence Scoring Accuracy**: Run offline analysis on cascade decisions; tune weights based on production false-positive/negative rates.
4. **LC-R12 Multi-Provider Data Routing**: Complete GDPR/data handling audit for each provider in the chain.

### Ongoing Mitigations (Operational)

1. **All risks**: Monthly risk register review; update scores based on operational data.
2. **LC-R03/LC-R04 Cost & Latency**: Weekly cost and latency reports; alert on budget burn rate.
3. **LC-R01 API Clients**: Quarterly review of provider API changes; update client implementations.
4. **LC-R07 State Machine Concurrency**: Periodic concurrent load tests; monitor for state corruption in logs.
5. **LC-R09 Cost Tracking Lag**: Monthly billing reconciliation vs. tracked costs.
