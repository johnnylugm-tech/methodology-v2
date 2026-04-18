# ARCHITECTURE.md — methodology-v2 v3.0 System Architecture

**Document Version:** 3.0
**Date:** 2026-04-19
**Status:** System Architecture

---

## 1. System Architecture Overview

### Design Philosophy

methodology-v2 v3.0 is a **layered security-first framework** for multi-agent orchestration:

- **Layer 1 (Foundation):** Core agent infrastructure
- **Layer 1.5 (Identity):** Agent identity propagation
- **Layer 1.7 (Security):** Input sanitization
- **Layer 2 (Governance):** Tiered oversight and circuit breaking
- **Layer 3 (Intelligence):** Intelligent routing and fallback

Each layer can operate independently or in concert.

---

## 2. Layer Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Intelligence                                       │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  LLM Cascade     │  │  Future: Hunter   │                │
│  │  (Multi-provider │  │  Agent           │                │
│  │   routing)       │  │                  │                │
│  └──────────────────┘  └──────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Governance & Reliability                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Tiered Govern.  │  │  Kill-Switch     │                │
│  │  (HOTL/HITL/    │  │  (Circuit        │                │
│  │   HOOTL)        │  │   Breaker)       │                │
│  └──────────────────┘  └──────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│  Layer 1.7: Security                                        │
│  ┌──────────────────┐                                       │
│  │  Prompt Shields  │                                       │
│  │  (Injection/PII  │                                       │
│  │   detection)     │                                       │
│  └──────────────────┘                                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1.5: Identity                                        │
│  ┌──────────────────┐                                       │
│  │  MCP + SAIF 2.0  │                                       │
│  │  (Identity       │                                       │
│  │   Propagation)    │                                       │
│  └──────────────────┘                                       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Core                                               │
│  ┌──────────────────┐                                       │
│  │  Agent Registry   │                                       │
│  │  Tool Registry    │                                       │
│  │  Session Manager  │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Module Map

```
implement/
├── mcp/                          # Feature #1 — Layer 1.5
│   ├── saif_identity_middleware.py    # Identity injection middleware
│   └── data_perimeter.py              # PII detection and deidentification
│
├── security/                      # Feature #2 — Layer 1.7
│   ├── prompt_shield.py               # Main shield logic
│   ├── detection_modes.py             # Detection configurations
│   └── shield_enums.py                # Verdict/PatternMatch enums
│
├── governance/                    # Feature #3 — Layer 2
│   ├── tier_classifier.py             # Core classification engine
│   ├── governance_trigger.py           # Workflow trigger evaluation
│   ├── override_manager.py             # Human override authority
│   ├── escalation_engine.py           # Tier escalation/de-escalation
│   ├── audit_logger.py               # Immutable hash-chain audit log
│   ├── enums.py                      # GovernanceDecision, Tier, RiskLevel
│   ├── models.py                      # AuditEntry, GovernanceContext, TierDecision
│   └── exceptions.py                  # GovernanceError, TierEscalationError
│
├── kill_switch/                   # Feature #4 — Layer 2
│   ├── kill_switch.py                # Main facade
│   ├── circuit_breaker.py            # Circuit state machine
│   ├── interrupt_engine.py            # OS-level interrupt (SIGTERM/SIGKILL)
│   ├── health_monitor.py              # Resource health monitoring
│   ├── state_manager.py              # Persistent circuit state (JSON)
│   ├── audit_logger.py               # Kill-switch audit log
│   ├── enums.py                      # CircuitState, KillReason
│   ├── models.py                      # InterruptEvent, KillReason
│   └── exceptions.py                 # AgentNotFoundError, InterruptInProgressError
│
└── llm_cascade/                   # Feature #5 — Layer 3
    ├── api.py                         # Main API facade
    ├── cascade_engine.py              # Core execution engine
    ├── cascade_router.py              # Provider selection
    ├── confidence_scorer.py            # Response quality scoring
    ├── health_tracker.py              # Provider health tracking
    ├── cost_tracker.py                # Cost budget management
    ├── integration.py                  # Integration with governance
    ├── models.py                      # CascadeConfig, CascadeResult, ModelConfig
    ├── enums.py                       # CascadeStateEnum, ModelProvider
    ├── exceptions.py                   # CascadeError, CostBudgetExceededError
    └── api_clients/
        ├── base.py                    # Abstract APIResponse
        ├── anthropic.py               # Anthropic API client
        ├── google.py                  # Google Gemini API client
        └── openai.py                  # OpenAI API client
```

---

## 4. Cross-Feature Integration

### Identity → Governance

```
Agent registers identity:
    middleware.create(agent_id, scopes)

Governance receives identity context:
    context = GovernanceContext(
        agent_id="agent-1",
        authorized_scopes=["read", "write"],
        identity_propagated=True
    )
    decision = classifier.classify_operation(context, operation)
```

### Governance → LLM Cascade

```
Governance decision affects routing:
    decision = classifier.classify(op)
    if decision.tier == Tier.HITL:
        await wait_for_human_approval()
    elif decision.tier == Tier.BLOCK:
        raise GovernanceBlockedError()
    else:
        result = await cascade.execute_chain(messages)
```

### LLM Cascade → Kill-Switch

```
LLM health events feed kill-switch:
    health_tracker.on_result(cascade_result)
    if health_tracker.is_healthy(provider) == False:
        health_monitor.record_failure(provider)
    if circuit_breaker.should_trigger():
        kill_switch.manual_trigger(agent_id)
```

---

## 5. Key Design Decisions

### AD-001: Layered Security Over Single Gateway
**Decision:** Security layers are composable, not monolithic.
**Rationale:** Prompt Shields operates at Layer 1.7. Kill-Switch at Layer 2. Governance at Layer 2. Each can be independently enabled/disabled.
**Trade-off:** Slight overhead per request (~60ms total). Acceptable for production.

### AD-002: Governance Tier is Contractual
**Decision:** Tier classification output is a binding contract, not a suggestion.
**Rationale:** Downstream components (LLM Cascade, Kill-Switch) rely on governance decision to proceed.
**Consequence:** Governance must be fast and deterministic. No probabilistic classification.

### AD-003: Kill-Switch is Final Authority
**Decision:** Kill-Switch overrides all other layers, including governance.
**Rationale:** If an agent is consuming 100% CPU, governance latency is irrelevant.
**Implementation:** Kill-Switch has its own health monitor, not dependent on governance.

### AD-004: LLM Cascade Provider Clients are Stubs
**Decision:** API clients (OpenAI, Anthropic, Google) are synchronous stubs.
**Rationale:** Actual HTTP calls are made by the agent runtime, not by this library.
**Consequence:** Cost tracking and health scoring are based on wrapper metadata, not real network metrics. Future: integrate with actual provider SDKs.

### AD-005: No Cross-Layer Dependencies
**Decision:** No module in a higher layer depends on a lower layer's internals.
**Rationale:** Each layer can be tested and deployed independently.
**Verification:** detect-secrets baseline confirms zero cross-layer imports in implement/.

---

## 6. State Management

### Persistent State (Disk)

| Component | State File | Format |
|-----------|-----------|--------|
| Circuit Breaker | `~/.kill_switch/circuits.json` | JSON |
| Kill-Switch Audit | `~/.kill_switch/audit.log` | JSONL |
| Governance Audit | In-memory + pluggable backend | — |

### Transient State (Memory)

| Component | State | Lifetime |
|-----------|-------|----------|
| Circuit Breaker | `CircuitBreakerState` | Process restart |
| Health Monitor | Sliding window metrics | Sliding window |
| LLM Cascade | Per-request context | Request lifetime |
| Governance Classifier | Rule cache | Process restart |

---

## 7. Test Architecture

```
test/
├── governance/      # Feature #3: 84 tests, 92% coverage
├── kill_switch/     # Feature #4: 71 tests, 82% coverage
├── llm_cascade/     # Feature #5: 455 tests, 95% coverage
├── mcp/             # Feature #1: 66 tests, 93% coverage
└── security/        # Feature #2: 59 tests, 97% coverage

Total: 735 tests across 5 Features
```

**Coverage by Layer:**
| Layer | Coverage | Notes |
|-------|----------|-------|
| Layer 1.5 (Identity) | 93% | mcp/saif_identity_middleware.py: 88% |
| Layer 1.7 (Security) | 97% | prompt_shield.py: 95% |
| Layer 2 (Governance) | 92% | audit_logger.py: 96% |
| Layer 2 (KillSwitch) | 82% | interrupt_engine.py: 70% ← lowest |
| Layer 3 (LLM Cascade) | 95% | api_clients: 0% ← stubs, intentionally untested |

---

## 8. Dependency Graph

```
governance/
  ├── enums.py
  ├── models.py
  ├── exceptions.py
  ├── tier_classifier.py
  ├── governance_trigger.py
  ├── override_manager.py
  ├── escalation_engine.py
  └── audit_logger.py

kill_switch/
  ├── enums.py
  ├── models.py
  ├── exceptions.py
  ├── audit_logger.py          ← local, no cross-dependency
  ├── circuit_breaker.py
  ├── health_monitor.py
  ├── interrupt_engine.py      ← local, no cross-dependency
  ├── state_manager.py
  └── kill_switch.py

llm_cascade/
  ├── enums.py
  ├── models.py
  ├── exceptions.py
  ├── api.py
  ├── cascade_engine.py
  ├── cascade_router.py
  ├── confidence_scorer.py
  ├── health_tracker.py
  ├── cost_tracker.py
  ├── integration.py           ← local, no cross-dependency
  └── api_clients/             ← stubs, no external deps
      ├── base.py
      ├── anthropic.py
      ├── google.py
      └── openai.py

mcp/
  ├── saif_identity_middleware.py
  └── data_perimeter.py

security/
  ├── shield_enums.py
  ├── detection_modes.py
  └── prompt_shield.py

No circular dependencies.
No cross-layer imports (verified by detect-secrets baseline).
```

---

## 9. Deployment Model

Each layer is a **plugin** to the OpenClaw Gateway:

```python
# Gateway plugin registration
gateway.register_plugin("prompt_shields", PromptShield())
gateway.register_plugin("governance", TieredGovernance())
gateway.register_plugin("kill_switch", KillSwitch())
gateway.register_plugin("llm_cascade", LLMCascade())
gateway.register_plugin("saif_identity", SAIFIdentityMiddleware())
```

Each plugin exposes:
- `health()` — Returns health status
- `configure(config)` — Receives runtime configuration
- `metrics()` — Returns metrics for observability
