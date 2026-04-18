# SPEC.md — methodology-v2 v3.0 System Overview

**Document Version:** 3.0
**Date:** 2026-04-19
**Status:** System Specification

---

## 1. System Overview

### System Name
methodology-v2 v3.0 — AI Agent Collaboration Framework

### Core Purpose
A framework for orchestrating multi-agent AI systems with governance, security, reliability, and intelligent routing.

### Version Summary

| Feature | Name | Layer | Purpose |
|---------|------|-------|---------|
| #1 | MCP + SAIF 2.0 | 1.5 | Identity propagation across agent calls |
| #2 | Prompt Shields | 1.7 | Input security: injection, PII, jailbreak detection |
| #3 | Tiered Governance | 2.0 | Tiered oversight: HOTL / HITL / HOOTL |
| #4 | Kill-Switch | 2.0 | Circuit breaker for runaway agents |
| #5 | LLM Cascade | 3.0 | Multi-model routing with fallback and cost control |

---

## 2. Feature Specifications

### Feature #1: MCP + SAIF 2.0 Identity Propagation

**Module:** `implement/mcp/`

**Purpose:** Propagate agent identity and authorization context across all tool calls and agent invocations.

**Key Components:**
- `saif_identity_middleware.py` — SAIF 2.0 middleware for identity injection
- `data_perimeter.py` — PII detection and deidentification

**Responsibilities:**
- Inject identity headers into all MCP tool calls
- Track agent lineage through call chain
- Enforce data perimeter boundaries
- Auto-detect and deidentify PII fields

**Interface:**
```python
# Agent registers identity context
middleware = SAIFIdentityMiddleware(agents_config)
middleware.create(agent_id="agent-1", scopes=["read", "write"])

# All subsequent calls auto-propagate identity
middleware.check(operation="tool.use", scopes_needed=["write"])
```

---

### Feature #2: Prompt Shields (Input Security)

**Module:** `implement/security/`

**Purpose:** Security layer for all agent inputs — detect injection attacks, PII leakage, jailbreak attempts.

**Key Components:**
- `prompt_shield.py` — Main shield with verdict logic
- `detection_modes.py` — Detection mode configurations
- `shield_enums.py` — Verdict, ScanResult, PatternMatch

**Responsibilities:**
- Scan all prompts for injection patterns (SQL, XSS, command)
- Detect jailbreak attempts and prompt leakage
- Apply PII redaction before forwarding
- Return structured verdict: ALLOW / DENY / ESCALATE

**Interface:**
```python
shield = PromptShield()
verdict = shield.check(prompt=raw_input)
# verdict.action in [Verdict.ALLOW, Verdict.DENY, Verdict.ESCALATE]
```

---

### Feature #3: Tiered Governance (HOTL / HITL / HOOTL)

**Module:** `implement/governance/`

**Purpose:** Classify every agent operation into exactly one governance tier and enforce the appropriate oversight level.

**Key Components:**
- `tier_classifier.py` — Core classification engine
- `governance_trigger.py` — Trigger evaluation for workflows
- `override_manager.py` — Human override authority
- `escalation_engine.py` — Tier escalation/de-escalation logic
- `audit_logger.py` — Immutable audit trail

**Responsibilities:**
- Classify operation into: HOTL (Human On The Loop), HITL (Human In The Loop), HOOTL (Human Out Of The Loop)
- Trigger governance workflows based on data classification and risk level
- Support human escalation and override
- Maintain immutable audit log with hash chain verification

**Interface:**
```python
classifier = TierClassifier(rules=classification_rules)
decision = classifier.classify_operation(
    operation=op,
    risk_level=RiskLevel.HIGH,
    data_classification=DataClassification.RESTRICTED
)
# decision.tier in [Tier.HOTL, Tier.HITL, Tier.HOOTL, Tier.BLOCK]
```

---

### Feature #4: Kill-Switch Circuit Breaker

**Module:** `implement/kill_switch/`

**Purpose:** Detect runaway agents and forcibly interrupt them before resource exhaustion.

**Key Components:**
- `kill_switch.py` — Main facade
- `circuit_breaker.py` — Circuit state machine
- `interrupt_engine.py` — OS-level interrupt execution
- `health_monitor.py` — Resource health monitoring
- `state_manager.py` — Persistent circuit state

**Responsibilities:**
- Monitor agent health (CPU, memory, latency, error rate)
- Open circuit when thresholds exceeded
- Execute OS-level interrupt (SIGTERM → SIGKILL → process termination)
- Maintain circuit state across restarts

**Interface:**
```python
ks = KillSwitch(config=kill_switch_config)
ks.start_monitoring(agent_id="agent-1")
health = ks.get_agent_health(agent_id="agent-1")
ks.manual_trigger(agent_id="agent-1", reason="user_requested")
```

---

### Feature #5: LLM Cascade (Multi-Model Routing)

**Module:** `implement/llm_cascade/`

**Purpose:** Route LLM requests across multiple providers with fallback, cost optimization, and health-aware selection.

**Key Components:**
- `cascade_engine.py` — Main execution engine
- `cascade_router.py` — Provider selection logic
- `api_clients/` — Provider-specific API clients (OpenAI, Anthropic, Google)
- `confidence_scorer.py` — Response quality scoring
- `health_tracker.py` — Provider health tracking
- `cost_tracker.py` — Cost budget management

**Responsibilities:**
- Route requests to primary provider based on config
- Fallback to secondary/tertiary on failure or health degradation
- Score response confidence; escalate if below threshold
- Track cost per provider; enforce budget limits
- Emit provider health events for governance integration

**Interface:**
```python
cascade = CascadeEngine(config=llm_cascade_config)
result = await cascade.execute_chain(messages=[...])
# result.state in [CascadeState.PRIMARY_SUCCESS, CascadeState.FALLBACK, CascadeState.EXHAUSTED]
```

---

## 3. Feature Integration

### Data Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────────┐
│ Feature #2: Prompt Shields              │
│ (Security scan before processing)        │
└─────────────────────────────────────────┘
    │ ALLOW
    ▼
┌─────────────────────────────────────────┐
│ Feature #1: MCP + SAIF Identity         │
│ (Inject identity context)               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ Feature #3: Tiered Governance          │
│ (Classify operation tier)               │
│ HOTL → auto-proceed                     │
│ HITL → wait for human approval          │
│ HOOTL → enhanced monitoring             │
│ BLOCK → reject                          │
└─────────────────────────────────────────┘
    │ APPROVED
    ▼
┌─────────────────────────────────────────┐
│ Feature #5: LLM Cascade                │
│ (Route to provider, track cost/health) │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ Feature #4: Kill-Switch               │
│ (Monitor health, interrupt if needed)   │
└─────────────────────────────────────────┘
    │
    ▼
Response
```

### Cross-Feature Dependencies

| From | To | Dependency Type |
|------|-----|----------------|
| Feature #2 (Prompt Shields) | Feature #1 (Identity) | Pre-condition: input must be clean |
| Feature #1 (Identity) | Feature #3 (Governance) | Governance needs identity to classify |
| Feature #3 (Governance) | Feature #5 (LLM Cascade) | Governance result affects routing decision |
| Feature #5 (LLM Cascade) | Feature #4 (Kill-Switch) | Kill-switch monitors LLM health metrics |
| Feature #5 (LLM Cascade) | Feature #3 (Governance) | LLM health events trigger governance |

---

## 4. Non-Functional Requirements

### Performance
- LLM Cascade latency overhead: <50ms per request (excluding model latency)
- Kill-Switch interrupt latency: <100ms from threshold breach to signal
- Prompt Shield scan: <10ms per prompt

### Reliability
- Kill-Switch circuit must survive agent crash (state persisted)
- Governance audit log must be immutable (hash chain verification)
- LLM Cascade must guarantee at-least-once delivery with fallback

### Security
- All agent identities cryptographically verifiable
- Prompt injection zero-day coverage via pattern learning
- No PII in logs (auto-redaction enabled)
- Zero hardcoded credentials (detect-secrets baseline maintained)

### Compatibility
- OpenClaw Gateway plugin interface compatible
- MCP protocol support for SAIF 2.0 identity propagation
- REST API for health and governance queries

---

## 5. Quality Gates (v3.0)

| Gate | Threshold | Status |
|------|-----------|--------|
| D1 Linting | 100% | ✅ Pass |
| D2 Type Safety | 100% | ✅ Pass |
| D3 Test Coverage | ≥85% | ✅ Pass (88%) |
| D4 Secrets | 100% | ✅ Pass |
| D5 Complexity | ≤85% | ✅ Pass |
| D6 Architecture | Clean deps | ✅ Pass |
| D7 Readability | 100% | ✅ Pass |
| D8 Error Handling | 100% | ✅ Pass |
| D9 Documentation | 100% | ✅ Pass |

---

## 6. Future Features (Roadmap)

| # | Feature | Branch | Status |
|---|---------|--------|--------|
| #6 | Hunter Agent | v3/hunter-agent | Planned |
| #7 | UQLM + Probes | v3/uqlm-probes | Planned |
| #8 | Gap Detection | v3/gap-detector | Planned |
| #9 | Risk Assessment | v3/risk-engine | Planned |
| #10 | LangGraph Integration | v3/langgraph | Planned |
