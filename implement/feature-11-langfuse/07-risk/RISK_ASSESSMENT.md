# Feature #11: Langfuse Observability — Risk Assessment

**Version:** 1.0.0  
**Feature ID:** FR-11  
**Phase:** 07-risk  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-22  
**Status:** Phase 1  

---

## 1. Risk Register

### Risk 1: Langfuse Cloud Unavailability Blocks Pipeline

| Field | Value |
|-------|-------|
| **Risk ID** | R-11-01 |
| **Description** | If Langfuse cloud is unreachable (network partition, outage), pending spans queue up and could eventually block the pipeline if OTLP exporter blocks. |
| **Probability** | Low (cloud SLAs are high; self-hosted mode available) |
| **Impact** | High (pipeline stalls) |
| **Score** | 0.15 (Low-Medium) |
| **Mitigation** | `BatchSpanProcessor` with 10,000-span buffer; overflow drops oldest spans. No blocking call in span creation path. |
| **Residual** | Low — spans dropped, pipeline continues |

### Risk 2: Missing Required Span Attributes

| Field | Value |
|-------|-------|
| **Risk ID** | R-11-02 |
| **Description** | Developers forget to include all 7 required attributes when calling `create_decision_span()` directly (without decorators). This would result in incomplete traces. |
| **Probability** | Medium (developer error) |
| **Impact** | Medium (incomplete audit trail) |
| **Score** | 0.25 (Medium) |
| **Mitigation** | Decorators (`@observe_decision_point`) provide safe API that auto-extracts all 7 fields from return dict. Direct `create_decision_span()` call requires all 7 fields as positional args — missing fields raise `TypeError`. |
| **Residual** | Low — direct calls are explicit and fail loudly if incomplete |

### Risk 3: PII Leakage in Span Attributes

| Field | Value |
|-------|-------|
| **Risk ID** | R-11-03 |
| **Description** | Developer accidentally stores PII (user content, prompts, personal data) in custom span attributes, violating compliance requirements. |
| **Probability** | Low (only scores/flags/tags stored by design) |
| **Impact** | Critical (GDPR/HIPAA violation) |
| **Score** | 0.10 (Low) |
| **Mitigation** | `create_decision_span()` only accepts the 7 defined fields; custom `attributes` dict is optional and should only be used for non-PII metadata. Docs explicitly warn against PII. |
| **Residual** | Very Low |

### Risk 4: Config Validation Bypass

| Field | Value |
|-------|-------|
| **Risk ID** | R-11-04 |
| **Description** | Env vars are set after `get_config()` is first called, bypassing validation. |
| **Probability** | Very Low (only happens in very unusual startup sequences) |
| **Impact** | Medium |
| **Score** | 0.05 (Very Low) |
| **Mitigation** | Config singleton is resolved on first call. Standard startup pattern (env vars set before any code runs) is unaffected. |
| **Residual** | Very Low |

### Risk 5: Test Environment vs Production Parity

| Field | Value |
|-------|-------|
| **Risk ID** | R-11-05 |
| **Description** | Tests use mock env vars (`pk_test`, `sk_test`) which don't connect to a real Langfuse instance. Integration gaps (network timeout, auth rejection) only discovered in production. |
| **Probability** | Medium |
| **Impact** | Medium |
| **Score** | 0.30 (Medium) |
| **Mitigation** | Phase 2 integration tests with real Langfuse credentials (staging environment). |
| **Residual** | Low |

---

## 2. Risk Score Matrix

| Risk ID | Probability | Impact | Score | Status |
|---------|------------|--------|-------|--------|
| R-11-01 | Low (0.2) | High (0.8) | 0.16 | Mitigated |
| R-11-02 | Medium (0.4) | Medium (0.5) | 0.20 | Mitigated |
| R-11-03 | Low (0.1) | Critical (1.0) | 0.10 | Mitigated |
| R-11-04 | Very Low (0.1) | Medium (0.5) | 0.05 | Accepted |
| R-11-05 | Medium (0.5) | Medium (0.5) | 0.25 | Open (Phase 2) |

---

## 3. Open Risks for Phase 2

| Risk | Action |
|------|--------|
| R-11-05 | Add integration tests with real staging Langfuse account in Phase 2 |

---

## 4. Compliance Assessment

| Requirement | Status | Notes |
|------------|--------|-------|
| SOX audit trail | ✅ Designed | Append-only audit entries for `decided_by=="human"` |
| GDPR Art.22 | ✅ Designed | No automated profiling; human decisions required for flagged items |
| HIPAA (if applicable) | ⚠️ Partial | No PHI in spans; `compliance_tags` field allows tagging |
| Data retention | ✅ Configurable | `audit_retention_days` (default 90 days) |
| TLS for Langfuse cloud | ✅ Enforced | `langfuse` SDK enforces TLS by default |
