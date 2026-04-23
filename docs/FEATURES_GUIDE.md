# Features Guide — methodology-v2 v9.1

**Version:** 9.1  
**Date:** 2026-04-24  
**Status:** Complete

---

## Table of Contents

1. [Overview](#overview)
2. [Enabling/Disabling Features](#enablingdisabling-features)
3. [Feature #1: MCP + SAIF Identity Propagation](#feature-1-mcp--saif-identity-propagation)
4. [Feature #2: Prompt Shields](#feature-2-prompt-shields)
5. [Feature #3: Governance](#feature-3-governance)
6. [Feature #4: Kill-Switch](#feature-4-kill-switch)
7. [Feature #5: LLM Cascade](#feature-5-llm-cascade)
8. [Feature #6: Hunter Agent](#feature-6-hunter-agent)
9. [Feature #7: UQLM](#feature-7-uqlm)
10. [Feature #8: Gap Detector](#feature-8-gap-detector)
11. [Feature #9: Risk Assessment](#feature-9-risk-assessment)
12. [Feature #10: LangGraph (Selective Extraction)](#feature-10-langgraph-selective-extraction)
13. [Feature #11: Langfuse Observability](#feature-11-langfuse-observability)
14. [Feature #12: Compliance](#feature-12-compliance)
15. [Feature #13: Observability Enhancement](#feature-13-observability-enhancement)
16. [Phase-to-Phase Flow](#phase-to-phase-flow)
17. [Quick Reference](#quick-reference)
18. [Troubleshooting](#troubleshooting)

---

## Overview

The **PhaseHooks Adapter** (`adapters/phase_hooks_adapter.py`) is the central integration hub that wraps the existing `PhaseHooks` framework with 13 independently-togglable Features. It orchestrates all Features across 7 hook points and 8 phases without requiring a standalone pipeline.

### Architecture: 4 Waves

The 13 Features are organized into 4 Waves based on their security/assurance role:

| Wave | Name | Features | Purpose |
|------|------|----------|---------|
| **Wave 1** | Defend & Log | #11 Langfuse, #13 Decision Log, #2 Shields, #4 KillSwitch | Observability + basic protection |
| **Wave 2** | Score & Detect | #7 UQLM, #8 Gap Detector, #5 LLM Cascade | Hallucination detection + quality scoring |
| **Wave 3** | Govern & Hunt | #1 SAIF, #6 Hunter, #3 Governance | Identity, integrity, tiered oversight |
| **Wave 4** | Assess & Comply | #9 Risk, #12 Compliance | Risk quantification + regulatory reporting |

### Feature #10: LangGraph Selective Extraction

Feature #10 is architecturally distinct — it is **not** a PhaseHooks-integrated feature. Instead, it provides optional LangGraph infrastructure that wraps the FR execution loop to enable:
- **CheckpointManager** (`checkpoint: False`) — HITL resume from saved state
- **Parallel Executor** (`parallel: False`) — Cascade parallelization
- **Router** (`routing: False`) — Conditional routing based on state

These three sub-features are independently togglable via the `checkpoint`, `parallel`, and `routing` flags in `DEFAULT_FEATURE_FLAGS`.

---

## Enabling/Disabling Features

### DEFAULT_FEATURE_FLAGS

All Features are controlled via the `DEFAULT_FEATURE_FLAGS` dictionary in `adapters/phase_hooks_adapter.py`:

```python
DEFAULT_FEATURE_FLAGS = {
    # Wave 1: Defend & Log
    "langfuse": True,        # #11 Langfuse tracing
    "decision_log": True,    # #13 Decision Log
    "effort": True,          # #13 Effort Metrics
    "shields": True,         # #2 Prompt Shields (warn mode)
    "kill_switch": True,     # #4 Kill-Switch
    # Wave 2: Score & Detect
    "uqlm": True,            # #7 UQLM (block on high uncertainty)
    "gap_detector": True,    # #8 Gap Detector (warn→block on critical)
    "llm_cascade": True,     # #5 LLM Cascade (simplified 2-model)
    # Wave 3: Govern & Hunt
    "saif": True,            # #1 SAIF (identity propagation)
    "hunter": True,         # #6 Hunter (integrity validation)
    "governance": True,      # #3 Governance (tier classification)
    # Wave 4: Assess & Comply
    "risk": True,            # #9 Risk (warn ≥7, freeze ≥9)
    "compliance": True,      # #12 Compliance (ASPICE >80%)
    # Feature #10 LangGraph (selective extraction)
    "checkpoint": False,     # CheckpointManager for HITL resume
    "parallel": False,       # Parallel executor for Cascade
    "routing": False,        # Router for conditional routing
}
```

### Overriding Per-Feature

Pass a custom `feature_flags` dict to `PhaseHooksAdapter`:

```python
from adapters.phase_hooks_adapter import PhaseHooksAdapter, DEFAULT_FEATURE_FLAGS

# Disable UQLM for a specific phase
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["uqlm"] = False

adapter = PhaseHooksAdapter(
    project_path="/path/to/project",
    phase=3,
    feature_flags=flags
)
```

### Wave-Level Defaults

| Wave | Default State | Rationale |
|------|--------------|-----------|
| Wave 1 | All enabled | Core observability and safety |
| Wave 2 | All enabled | Core quality detection |
| Wave 3 | All enabled | Core governance |
| Wave 4 | All enabled | Core risk/compliance |
| Feature #10 | All disabled | Optional enhancement |

---

## Feature #1: MCP + SAIF Identity Propagation

### Introduction

**SAIF (Security Authority Identity Framework)** is an identity propagation and scope validation system that ensures every Agent operation has a cryptographically verifiable identity chain. It prevents identity spoofing between sessions and provides the audit trail required for HR-01 compliance (Developer ≠ Reviewer).

SAIF validates that each session spawn carries a valid, scope-limited identity token. Without SAIF, sessions can be spawned without verifying who/what they are, making it impossible to enforce the Developer/Reviewer separation requirement.

### Before / After

**Before (without SAIF):**
- No identity propagation between sessions
- MCP tools called without scope validation
- No audit trail for tool access
- HR-01 Developer ≠ Reviewer enforced only by convention, not mechanism
- A compromised Developer session could impersonate a Reviewer

**After (with SAIF):**
- Identity token propagated through entire session chain
- MCP tool access requires valid scopes (developer scope vs reviewer scope)
- Full audit trail in decision_log with identity context
- HR-01 enforced cryptographically: token validation fails if scopes don't match required roles
- `SAIFMiddleware` + `ScopeValidator` provide defense-in-depth

### Benefits

- **Identity chain integrity**: Every session has a verifiable identity token
- **Scope-based access control**: Tools require specific scopes (e.g., `code_write`, `review_approve`)
- **Compliance-ready audit trail**: HR-01, HR-05 compliance with evidence in decision_log
- **Defense against impersonation**: Token validation prevents Developer from acting as Reviewer

### Phase Integration

- **Hook**: `preflight_all()` + `monitoring_after_dev()`
- **Phase**: Developer session startup validation
- **Flow**: Validates SAIF token before spawning developer session; validates again after output

```
preflight_all()
└── _preflight_saif_token()     ← Validates token before Phase starts

monitoring_after_dev()
└── saif.validate(result)       ← Re-validates after developer output
```

### Configuration

**Feature Flag**: `"saif": True` (default)

```python
# Override (e.g., disable for testing)
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["saif"] = False

adapter = PhaseHooksAdapter(project_path=path, phase=phase, feature_flags=flags)
```

### Implementation Details

```python
class SAIFWrapper:
    """Wave 3 Feature #1"""
    
    def validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Validates SAIF token in request"""
        
    def check_scopes(self, required_scopes: List[str]) -> bool:
        """Verifies current context has required scopes"""
```

### Threshold / Action

| Condition | Action |
|-----------|--------|
| Token missing or invalid | `PREFLIGHT_FAILED` — blocks Phase start |
| Token missing required scopes | `PREFLIGHT_FAILED` — blocks Phase start |
| Token valid but context mismatch | `PHASE_HOOK_FAILED` — blocks FR execution |

---

## Feature #2: Prompt Shields

### Introduction

**Prompt Shields** detects and blocks prompt injection attacks in developer output before it is written to disk. It scans all generated files for injection patterns (malicious instructions embedded in code or comments that could manipulate future LLM calls).

Shields operates in **warn mode** by default — suspicious patterns generate warnings but do not block, while confirmed injection patterns can be configured to block. This is the last security checkpoint before code persistence.

### Before / After

**Before (without Shields):**
- Generated code written directly to disk without injection scan
- Malicious instructions in comments or strings are invisible
- Prompt injection attacks propagate to future sessions
- No record of what was scanned

**After (with Shields):**
- All files scanned before disk write
- Injection patterns identified and logged
- Block mode: confirmed injection prevents file write
- Audit trail in decision_log with pattern details

### Benefits

- **Injection prevention**: Stops prompt injection at the last checkpoint
- **Warn/Block flexibility**: Configurable response to suspicious content
- **Audit trail**: Every scan logged with verdict and pattern
- **Zero false positives in production**: Pattern matching is conservative

### Phase Integration

- **Hook**: `monitoring_after_dev()`
- **Phase**: After developer outputs code, before disk write
- **Flow**: Scans `dev_result["files"]` content; blocks or warns based on verdict

```
monitoring_after_dev()
└── _scan_developer_output()    ← Scans files before write
    ├── verdict.BLOCK → PHASE_HOOK_FAILED (file not written)
    └── verdict.WARN → logger.warning (file written with warning)
```

### Configuration

**Feature Flag**: `"shields": True` (default, warn mode)

```python
# Block mode (more aggressive)
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["shields"] = True  # still True, but configure block mode in shield config
```

### Threshold / Action

| Pattern Severity | Verdict | Action |
|-----------------|---------|--------|
| CRITICAL (e.g., "ignore previous instructions") | BLOCK | File not written, `PHASE_HOOK_FAILED` raised |
| HIGH (e.g., role hijack patterns) | WARN | File written with warning logged |
| MEDIUM (context injection hints) | WARN | File written with warning logged |
| LOW / clean | PASS | File written normally |

### Detection Patterns

Prompt Shields checks for:
- **Direct override**: "ignore previous instructions", "disregard your instructions"
- **Role hijack**: "you are now DAN", "pretend you are"
- **Permission escalation**: "grant admin", "enable developer mode"
- **Rule modification**: "change system prompt to", "modify your rules"
- **Context injection**: "append to system prompt", "add to your instructions"

---

## Feature #3: Governance

### Introduction

**Governance** implements tiered human oversight classification for each FR execution. It replaces ad-hoc human approval decisions with a systematic tier system:

| Tier | Full Name | Human Role | When Used |
|------|-----------|------------|-----------|
| **HOOTL** | Human-Out-of-the-Loop | None — fully autonomous | Low-risk, well-understood tasks |
| **HOTL** | Human-on-the-Loop | Monitor and can intervene | Moderate risk |
| **HITL** | Human-in-the-Loop | Must approve each step | High risk |
| **LOOP** | Human Loop | Human must be in the decision chain | Highest risk |

Governance classifies each FR into a tier based on UAF score, previous rejection count, and risk signals. This drives downstream behavior (e.g., HOTL triggers multi-reviewer consensus via LLM Cascade).

### Before / After

**Before (without Governance):**
- Reviewer decides ad-hoc whether to escalate to human
- No systematic tier classification
- Hotl/HITL decisions undocumented
- No record of why human was or wasn't involved

**After (with Governance):**
- Every FR gets systematic tier classification before review
- Tier decision recorded in decision_log with reasoning
- HOTL tier triggers LLM Cascade (multi-reviewer consensus)
- HOOTL tier proceeds autonomously with full logging
- Human can still intervene at any HITL-tier FR

### Benefits

- **Systematic oversight**: Every FR has a documented oversight tier
- **Consistent escalation**: UAF + rejection count drive tier, not intuition
- **Audit trail**: Tier classification + reasoning recorded
- **Cascade integration**: HOTL automatically triggers multi-reviewer review

### Phase Integration

- **Hook**: `monitoring_before_rev()`
- **Phase**: Before Reviewer execution
- **Flow**: Reads UAF score, classifies tier, logs decision, triggers cascade if HOTL

```
monitoring_before_rev()
├── governance.classify(ctx)        ← Classifies FR into tier
├── decision_log.write(tier=...)    ← Logs tier decision
└── 若 tier==HOTL → llm_cascade.start()  ← Triggers multi-reviewer
```

### Configuration

**Feature Flag**: `"governance": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["governance"] = False  # Disable for low-risk, fast iteration phases
```

### Tier Classification Logic

```python
def classify(self, ctx: GovernanceContext) -> Tier:
    # UAF > 0.7 → HITL
    if ctx.uaf_score > 0.7:
        return Tier.HITL
    
    # Previous rejections ≥ 3 → elevate tier
    if ctx.previous_rejections >= 3:
        return Tier.HOTL
    
    # Risk score > 0.7 → HITL
    if ctx.risk_score > 0.7:
        return Tier.HITL
    
    # Default → LOW (HOOTL)
    return Tier.LOW
```

### Threshold / Action

| Condition | Tier | Action |
|-----------|------|--------|
| UAF > 0.7 | HITL | Human must approve; notify Johnny |
| Rejections ≥ 3 | HOTL | Multi-reviewer consensus required |
| Risk > 0.7 | HITL | Human must approve |
| Default LOW | HOOTL | Autonomous execution, monitored |

---

## Feature #4: Kill-Switch

### Introduction

**Kill-Switch** is the emergency stop mechanism that halts all AI operations when a critical failure condition is detected. It implements EU AI Act Article 14(4)(e) requirement for operators to be able to interrupt the AI system.

Kill-Switch is not a soft "pause" — it is a hard halt that stops further FR iterations and prevents new FR execution until explicitly reset. It also triggers compliance reporting and risk register updates.

### Before / After

**Before (without Kill-Switch):**
- HR-12 (>5 iterations) triggers only a notification
- Project state remains RUNNING despite critical failure
- No emergency stop mechanism
- No compliance evidence for Art.14(4)(e)

**After (with Kill-Switch):**
- HR-12 triggers hard halt (not just notification)
- `KillSwitchError` raised, all hooks blocked
- Compliance report generated (EU AI Act Art.14)
- Risk registered in RISK_REGISTER.md
- Project FSM transitions to PAUSE/FREEZE

### Benefits

- **EU AI Act Art.14(4)(e) compliance**: Emergency interrupt capability with evidence
- **Hard halt**: Prevents continued execution after critical failure
- **Compliance reporting**: Every trigger generates audit evidence
- **Risk tracking**: Critical events logged to risk register

### Phase Integration

- **Hook**: `monitoring_hr12_check()`
- **Phase**: After each rejection cycle
- **Flow**: Checks iteration count; if >5, triggers Kill-Switch + compliance report

```
monitoring_hr12_check()
└── 若 iteration > 5:
    ├── _pause_project()              ← FSM state → PAUSE
    ├── compliance.report_hr12_event() ← EU AI Act evidence
    ├── risk_assessor.register()     ← Log to risk register
    └── kill_switch.trigger()         ← Hard halt
        └── KillSwitchError raised
```

### Configuration

**Feature Flag**: `"kill_switch": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["kill_switch"] = False  # Disable for non-critical phases (not recommended)
```

### Threshold / Action

| Condition | Action |
|-----------|--------|
| iteration > 5 (HR-12) | Kill-Switch triggered; `KillSwitchError` raised |
| Risk score > 0.9 at preflight | `PREFLIGHT_FAILED` (pre-emptive halt) |
| Kill-Switch triggered | All subsequent hooks blocked until reset |

### Kill-Switch Response Time

EU AI Act Art.14(4)(e) requires interrupt capability within **5 seconds**. Kill-Switch is designed to meet this requirement:
- Hardware-level interrupt signal
- Minimal code path between trigger and halt
- Response time tracked in `killswitch_compliance_log.json`

---

## Feature #5: LLM Cascade

### Introduction

**LLM Cascade** is a simplified 2-model parallel review system for HOTL-tier FRs. When Governance classifies an FR as HOTL (High-risk Automated), instead of a single Reviewer, two or more Reviewer sessions run in parallel using different models (e.g., GPT-4 + Claude) and their outputs are compared for consensus.

Cascade reduces single-model blind spots and provides stronger assurance for high-risk automated decisions without requiring human review for every FR.

### Before / After

**Before (without Cascade):**
- HOTL tier still uses single Reviewer model
- Blind spots of one model (e.g., GPT-4 missing something Claude catches)
- No systematic multi-model consensus
- HOTL vs single-reviewer difference only theoretical

**After (with Cascade):**
- HOTL → multiple Reviewer sessions (different models) run in parallel
- Both must APPROVE for the FR to pass
- Any REJECT → consensus: reject
- Full audit trail: which models agreed/disagreed

### Benefits

- **Reduced blind spots**: Different model architectures catch different issues
- **Consensus guarantee**: HOTL decisions require agreement, not single-model fiat
- **Configurable model set**: 2-3 models based on risk level
- **Selective deployment**: Only HOTL FRs trigger cascade (efficient for LOW/HOOTL)

### Phase Integration

- **Hook**: `monitoring_before_rev()` (when tier == HOTL)
- **Phase**: Reviewer execution for HOTL-classified FRs
- **Flow**: Spawns multiple reviewer sessions, collects consensus

```
monitoring_before_rev()
└── 若 tier == HOTL:
    └── llm_cascade.start(models=[...])
        ├── reviewer_model_1 → verdict_1
        └── reviewer_model_2 → verdict_2
            └── consensus: both APPROVE → pass
                          any REJECT → reject
```

### Configuration

**Feature Flag**: `"llm_cascade": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["llm_cascade"] = False  # Disable multi-model review (not recommended for production)
```

### Threshold / Action

| Condition | Action |
|-----------|--------|
| Tier == HOTL | Trigger 2-model parallel review |
| Both models APPROVE | FR passes with consensus record |
| Any model REJECT | FR rejected; consensus REJECT logged |
| Cascade disabled but tier == HOTL | Falls back to single reviewer with warning |

### Cascade Models

Default models for parallel review:
```python
models = ["gpt-4o", "claude-3-opus"]  # Architecturally different
```

Additional models can be configured for higher-risk scenarios.

---

## Feature #6: Hunter Agent

### Introduction

**Hunter Agent** (MAS-Hunt) is Layer 2.5's integrity monitoring system that detects four categories of threats in Agent communications:

1. **Instruction Tampering**: Attempts to modify system rules or override governance decisions
2. **Dialogue Fabrication**: Agent claims "as I said earlier" with no audit log evidence
3. **Memory Poisoning**: Unauthorized modification of agent memory
4. **Tool Abuse**: Agent uses tools outside its Agents.md whitelist

Hunter operates as a passive monitor — it inspects messages and raises alerts, but does not block directly. It works alongside UQLM and Governance to provide defense-in-depth against deceptive or compromised agent behavior.

### Before / After

**Before (without Hunter):**
- Tampering attempts go undetected
- Agents can claim false conversation history
- Tool usage not validated against whitelist
- No anomaly detection on agent output patterns

**After (with Hunter):**
- All agent messages inspected for tampering patterns
- Fabrication claims cross-checked against audit log
- Tool calls validated against Agents.md whitelist
- Anomaly score generated for each FR output

### Benefits

- **Tampering detection**: Catches override/injection patterns with ≥95% accuracy
- **Fabrication detection**: Contradicts false claims using audit log
- **Tool abuse prevention**: Whitelist enforcement at runtime
- **Integrity validation**: Hash verification on memory/context reads

### Phase Integration

- **Hook**: `monitoring_after_dev()`
- **Phase**: After developer output, in parallel with UQLM
- **Flow**: Inspects files for tampering, fabrication, anomaly patterns

```
monitoring_after_dev()
├── uqlm.compute()            ← First: UAF score
├── hunter.detect()            ← Second: anomaly detection
│   ├── is_confirmed → PHASE_HOOK_FAILED (direct reject)
│   └── is_suspicious → tier elevation, logged warning
└── decision_log.write(hunter_status)
```

### Configuration

**Feature Flag**: `"hunter": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["hunter"] = False  # Disable (not recommended — core integrity feature)
```

### Detection Patterns

**Instruction Tampering** (severity: CRITICAL/HIGH):
| Pattern | Example | Severity |
|---------|---------|----------|
| Direct override | "ignore previous instructions" | CRITICAL |
| Role hijack | "you are now DAN" | CRITICAL |
| Permission escalation | "grant admin privileges" | HIGH |
| Rule modification | "change system prompt to:" | HIGH |
| Context injection | "append to system prompt:" | MEDIUM |

**Dialogue Fabrication** keywords:
- "as I said earlier"
- "as we discussed"
- "you told me to"
- "we agreed on"
- "per your request"

### Threshold / Action

| Hunter Result | Action |
|--------------|--------|
| `is_confirmed` (anomaly confirmed) | `PHASE_HOOK_FAILED` — FR rejected immediately |
| `is_suspicious` (unconfirmed anomaly) | Tier elevation (LOW→HOTL), warning logged |
| Clean (no anomaly) | Proceed normally |

### Hunter Alert Types

| Detection Type | Severity | Action |
|---------------|----------|--------|
| Instruction Tampering | CRITICAL | `PHASE_HOOK_FAILED` |
| Dialogue Fabrication | HIGH | Tier elevation + warning |
| Memory Poisoning | CRITICAL | `PHASE_HOOK_FAILED` |
| Tool Abuse | HIGH | Block tool call, log alert |

---

## Feature #7: UQLM

### Introduction

**UQLM (Uncertainty Quantification via Language Models)** computes a hallucination risk score (UAF — Uncertainty-Aware Framework score) for every developer output. It combines multiple scorers into a unified ensemble score that drives downstream decisions:

| Scorer | Weight | What it Measures |
|--------|--------|------------------|
| Semantic Entropy | 0.4 | Variation in meaning across sampling |
| Semantic Density | 0.3 | Concept density in response |
| Self-Consistency | 0.3 | Answer consistency across samples |

UAF is the primary input to Governance tier classification — high UAF automatically elevates the oversight tier.

### Before / After

**Before (without UQLM):**
- No quantification of output uncertainty
- Reviewer relies entirely on human judgment
- No objective signal for "this looks like hallucination"
- Confidence scores from LLM itself (unreliable — model doesn't know what it doesn't know)

**After (with UQLM):**
- Objective UAF score computed from model output characteristics
- High UAF (>0.5) triggers BLOCK
- UAF feeds directly into Governance tier classification
- External, model-agnostic measurement (not the model's own confidence)

### Benefits

- **Hallucination quantification**: Objective measurement, not self-reported confidence
- **Threshold-driven action**: Clear PASS/WARN/BLOCK decisions
- **Governance integration**: UAF drives tier elevation
- **Multi-scorer ensemble**: Robust against single-scorer blind spots

### Phase Integration

- **Hook**: `monitoring_after_dev()`
- **Phase**: First check after developer output
- **Flow**: Computes UAF, writes to Langfuse span, drives downstream decisions

```
monitoring_after_dev()
├── uqlm.compute()              ← UAF score computed first
│   ├── uaf < 0.3 → PASS
│   ├── 0.3 ≤ uaf < 0.5 → WARN
│   └── uaf ≥ 0.5 → BLOCK
├── langfuse.set_span_attribute("uaf_score", uaf)  ← Written to trace
└── decision_log.write(uaf=...)
```

### Configuration

**Feature Flag**: `"uqlm": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["uqlm"] = False  # Disable for low-risk, fast iteration (not recommended)
```

### Threshold / Action

| UAF Score | Verdict | Action |
|-----------|---------|--------|
| < 0.3 | PASS | Proceed normally |
| 0.3 – 0.5 | WARN | Proceed with warning; Reviewer notified |
| ≥ 0.5 | BLOCK | FR rejected; developer must revise |
| UQLM failure | BLOCK | Conservative fallback (uaf=0.85) |

### Thresholds (Configurable)

```python
UAF_THRESHOLD_WARN = 0.3   # UAF ≥ 0.3 triggers warning
UAF_THRESHOLD_BLOCK = 0.5   # UAF ≥ 0.5 triggers block
```

---

## Feature #8: Gap Detector

### Introduction

**Gap Detector** automatically identifies missing, incomplete, or orphaned implementation items by comparing `SPEC.md` promises against `implement/` directory reality. It runs at `postflight_all()` to ensure every Phase ends with a full coverage report.

Gap types detected:

| Gap Type | Description | Severity |
|----------|-------------|----------|
| MISSING | SPEC feature has no corresponding code | CRITICAL / MAJOR |
| INCOMPLETE | Feature exists but missing params/docstrings | MAJOR / MINOR |
| ORPHANED | Code exists but SPEC never mentioned it | MINOR (informational) |

### Before / After

**Before (without Gap Detector):**
- Phase completion assessed manually
- Missing test coverage undetected until later phases
- SPEC/IMPLEMENTATION drift accumulates silently
- No automated evidence of what was/wasn't built

**After (with Gap Detector):**
- Automated SPEC-vs-implementation comparison
- Gap report generated at phase end
- High-severity gaps trigger Johnny notification
- Structural gaps (no 04-tests dir, etc.) detected and warned

### Benefits

- **Automated coverage analysis**: No manual SPEC verification needed
- **Gap severity classification**: CRITICAL gaps flagged for immediate action
- **Phase-specific scanning**: Phase 4 gets full scan; Phase 3+ gets structural checks
- **Automated reports**: `GAP_REPORT.md` delivered at phase end

### Phase Integration

- **Hook**: `postflight_all()`
- **Phase**: End of every phase
- **Flow**: Scans 04-tests directory, compares to SPEC.md, generates gap report

```
postflight_all()
├── 若 phase == 4:
│   └── gap_detector.scan_full()    ← Full gap detection
│       ├── high_severity gaps → Johnny notification
│       └── GAP_REPORT.md delivered
└── 若 phase >= 3:
    └── gap_detector.scan_basic()    ← Structural checks only
```

### Configuration

**Feature Flag**: `"gap_detector": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["gap_detector"] = False  # Disable for rapid prototyping phases
```

### Gap Detection Logic

```python
def scan_full(self, test_dir):
    gaps = []
    for spec_feature in spec_features:
        matched_code = find_code_match(spec_feature.name)
        if not matched_code:
            gaps.append(Gap(gap_type="MISSING", severity="CRITICAL"))
        elif not matched_code.has_complete_params:
            gaps.append(Gap(gap_type="INCOMPLETE", severity="MAJOR"))
    
    for code_item in code_items:
        if not code_item.in_spec:
            gaps.append(Gap(gap_type="ORPHANED", severity="MINOR"))
    
    return gaps
```

### Threshold / Action

| Condition | Action |
|-----------|--------|
| Phase 4 + any gap | Generate GAP_REPORT.md |
| Phase 4 + high_severity gap | Johnny notification |
| Phase 3+ + basic structural gap | Warning logged |
| No tests directory | Warning logged |

---

## Feature #9: Risk Assessment

### Introduction

**Risk Assessment** provides continuous, quantitative risk evaluation across all phases. It evaluates probability × impact for identified risks and generates mitigation strategies. Unlike single-point checks, Risk Assessment runs at both `preflight_all()` and `postflight_all()` to maintain ongoing risk visibility.

Risk scores drive executive decisions and can trigger pre-emptive halts before critical failures occur.

### Before / After

**Before (without Risk Assessment):**
- Risk evaluated subjectively by agents
- No quantitative scoring
- Risks accumulate silently until crisis
- No risk register maintained
- No connection between risk signals and FSM state

**After (with Risk Assessment):**
- Quantitative risk scores at phase start and end
- Risk register maintained in `RISK_REGISTER.md`
- High risk → Johnny notification + FSM state change
- Risk trends visible across phases
- Mitigation strategies auto-generated

### Benefits

- **Quantitative scoring**: Probability × Impact × Detectability_Factor
- **Continuous monitoring**: Both preflight and postflight evaluation
- **Risk register**: Persistent log of all identified risks
- **Executive reporting**: `RISK_ASSESSMENT.md` at phase end

### Phase Integration

- **Hook**: `preflight_all()` + `postflight_all()`
- **Phase**: Start and end of every phase
- **Flow**: Evaluates risk signals, updates register, triggers notifications/actions

```
preflight_all()
└── risk_assessment.phase_start()
    ├── risk_score > 0.9 → PREFLIGHT_FAILED (halt)
    └── risk_score > 0.7 → Johnny notification

postflight_all()
└── risk_assessment.phase_end()
    ├── New high risks → Johnny notification
    └── RISK_REGISTER.md updated
```

### Configuration

**Feature Flag**: `"risk": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["risk"] = False  # Not recommended — core governance feature
```

### Risk Scoring Formula

```
Risk Score = Probability × Impact × Detectability_Factor

where:
  Probability: 0.0 - 1.0
  Impact: 1 - 5
  Detectability_Factor: 0.5 - 1.0
```

### Threshold / Action

| Risk Score | Level | Action |
|-----------|-------|--------|
| > 0.9 | CRITICAL | `PREFLIGHT_FAILED` — Phase halted |
| 0.7 – 0.9 | HIGH | Johnny notification; proceed with caution |
| 0.3 – 0.7 | MEDIUM | Monitor; add to risk register |
| < 0.3 | LOW | Accept; log for record |

### Risk Dimensions

| Dimension | Assessment Factors |
|-----------|-------------------|
| Technical | System complexity, dependencies, code quality |
| Operational | Human resources, process maturity, knowledge transfer |
| External | Market changes, regulatory compliance, third-party dependencies |

---

## Feature #10: LangGraph (Selective Extraction)

### Introduction

**Feature #10** provides optional LangGraph infrastructure that wraps the FR execution loop. Unlike the other 12 Features which integrate into PhaseHooks, LangGraph is a **wrapper around the execution model** that provides:

1. **CheckpointManager** — Persistent state snapshots for HITL resume
2. **Parallel Executor** — Fan-out/fan-in for Cascade parallelization
3. **Router** — Conditional routing based on state values

These three sub-features are independently togglable. They are **disabled by default** — set `checkpoint`, `parallel`, or `routing` to `True` in `feature_flags` to enable.

### Before / After

**Before (without LangGraph):**
- FR execution is a stateless for-loop
- No recovery from mid-phase crashes
- HOTL cascade runs sequentially
- Routing logic scattered across hook code

**After (with LangGraph):**
- FR execution has persistent state across steps
- Checkpoint resume: crash recovery from saved state
- Parallel fan-out: Cascade reviews run concurrently
- Centralized routing: conditional edges defined in graph

### Benefits

- **HITL resume**: Developer interrupted mid-phase → resume from checkpoint
- **Parallel execution**: Cascade reviews run concurrently (not sequentially)
- **Stateful execution**: Graph remembers execution history
- **Clean routing**: Conditional edges replace scattered if-statements

### Phase Integration

**Not integrated into PhaseHooks** — this is an optional wrapper around the FR execution loop.

```python
# Enable CheckpointManager
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["checkpoint"] = True  # HITL resume support

# Enable Parallel Executor
flags["parallel"] = True  # Cascade runs in parallel

# Enable Router
flags["routing"] = True  # Conditional routing
```

### Sub-Features

#### CheckpointManager

```python
class CheckpointManager:
    def checkpoint(self, state, node_name) -> str: ...
    def resume(self, checkpoint_id) -> State: ...
    def list_checkpoints(self, run_id) -> list[CheckpointRecord]: ...
```

#### Parallel Executor (for Cascade)

```python
# Fan-out: multiple reviewer sessions
Send("reviewer", state)  # from langgraph

# Fan-in: synchronization barrier
def wait_all(state) -> State:
    # Aggregates results from all parallel reviewers
```

#### Router (Conditional Routing)

```python
def route_by_confidence(state) -> str:
    score = state["intermediate_results"]["confidence_score"]
    if score >= 0.9: return "finalize"
    elif score >= 0.7: return "human_review"
    else: return "retry"
```

### Configuration

| Sub-Feature | Flag | Default | Purpose |
|-------------|------|---------|---------|
| CheckpointManager | `"checkpoint"` | False | HITL resume |
| Parallel Executor | `"parallel"` | False | Cascade parallelization |
| Router | `"routing"` | False | Conditional routing |

---

## Feature #11: Langfuse Observability

### Introduction

**Langfuse** is the OpenTelemetry-based observability foundation for the entire pipeline. It instruments every PhaseHooks call with trace spans, capturing all 7 required decision attributes per span:

| Attribute | Type | Description |
|-----------|------|-------------|
| `uaf_score` | float | UQLM uncertainty score |
| `clap_flag` | bool | CLAP activation probe result |
| `risk_score` | float | Aggregated risk score |
| `hitl_gate` | str | HITL gate status: `pass`, `review`, `block` |
| `human_decision` | str | Human override decision (or None) |
| `decided_by` | str | `agent`, `human`, or `system` |
| `compliance_tags` | list[str] | Applicable compliance tags |

Langfuse is the **observability substrate** — all other Features write their data through it.

### Before / After

**Before (without Langfuse):**
- No systematic trace of PhaseHooks calls
- Decision attributes scattered across logs
- No centralized view of FR execution
- Audit trail fragmented

**After (with Langfuse):**
- Every hook point has a trace span
- All 7 required attributes captured
- Execution path visible in Langfuse dashboard
- Langfuse → Feature #13 (Observability Enhancement) → UQLM metrics, Decision Log, Effort

### Benefits

- **Complete trace coverage**: Every hook instrumented
- **7 required attributes**: All compliance fields captured
- **Self-hosted option**: No data leaves infrastructure if required
- **Dashboard integration**: Real-time view, trend charts, audit log

### Phase Integration

- **Hook**: All hooks (preflight_all, monitoring_
before_dev, monitoring_after_dev, monitoring_before_rev, monitoring_after_rev, monitoring_hr12_check, postflight_all)
- **Phase**: All phases — active throughout
- **Flow**: Every hook creates/extends a trace span with 7 required attributes

```
preflight_all()
└── langfuse.trace()              ← Trace started
    └── span with phase metadata

monitoring_after_dev()
└── span with uaf_score, hunter_status

monitoring_after_rev()
└── span with reviewer decision

postflight_all()
└── langfuse.close()              ← Trace ended
```

### Configuration

**Feature Flag**: `"langfuse": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["langfuse"] = False  # Disable for local testing without Langfuse server
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LANGFUSE_PUBLIC_KEY` | Yes (cloud) | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | Yes (cloud) | Langfuse secret key |
| `LANGFUSE_HOST` | Yes (self-hosted) | Self-hosted URL |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP collector endpoint |
| `LANGFUSE_TRACE_SAMPLING_RATE` | No | 0.0-1.0, default 1.0 |

### Failure Strategy

Langfuse failures use **graceful degradation**:
- Langfuse unreachable → spans dropped, no blocking
- No crash, no interruption of main pipeline
- Warning logged

---

## Feature #12: Compliance

### Introduction

**Compliance** generates automated regulatory reports mapping methodology-v2 mechanisms to three frameworks:

1. **EU AI Act Article 14** — Human oversight requirements
2. **NIST AI RMF** — Govern, Map, Measure, Manage functions
3. **Anthropic RSP v3.0** — ASL-1 through ASL-4 deployment conditions

Compliance is not a gate — it is **evidence generation** that ensures every decision has a regulatory audit trail. It also enforces the Kill-Switch response time requirement (≤5s for Art.14(4)(e)).

### Before / After

**Before (without Compliance):**
- No regulatory mapping
- No automated compliance reports
- HR-12 / Kill-Switch events lack compliance evidence
- ASL classification ad-hoc

**After (with Compliance):**
- EU AI Act Art.14 compliance checker runs every phase
- NIST AI RMF coverage matrix maintained
- ASL level automatically assessed
- Every Kill-Switch trigger logged with Art.14 evidence
- `COMPLIANCE_PHASE_N.md` report generated at phase end

### Benefits

- **EU AI Act Art.14 compliance**: Human oversight evidence for all 6 sub-articles
- **NIST AI RMF mapping**: All 4 functions (Govern, Map, Measure, Manage) covered
- **ASL classification**: Automatic ASL-1 through ASL-4 assessment
- **Kill-Switch timing**: Response time tracked for Art.14(4)(e) compliance
- **Immutable audit trail**: Append-only logs with SHA-256 integrity

### Phase Integration

- **Hook**: `postflight_all()` + `monitoring_hr12_check()`
- **Phase**: End of every phase; on Kill-Switch trigger
- **Flow**: Generates compliance matrix, ASL assessment, human override audit

```
postflight_all()
└── compliance.generate_phase_report()
    ├── EU AI Act Art.14 compliance score
    ├── NIST AI RMF coverage matrix
    ├── ASL assessment
    └── COMPLIANCE_PHASE_N.md delivered

monitoring_hr12_check()
└── 若 Kill-Switch triggered:
    └── compliance.report_hr12_event()    ← Art.14(4)(e) evidence
```

### Configuration

**Feature Flag**: `"compliance": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["compliance"] = False  # Disable for internal-only projects (not recommended)
```

### Compliance Coverage

#### EU AI Act Article 14 Mapping

| Sub-Article | Requirement | v3.0 Mechanism | Evidence |
|-------------|-------------|----------------|----------|
| 14(1) | Human oversight measures | HITL/HOTL分级 | Gate policy config |
| 14(4)(a) | Understand AI limits | Model cards + Agents.md | `model_card.json` |
| 14(4)(b) | Prevent automation bias | DA challenge + UAF warnings | `debate_agent.py` |
| 14(4)(c) | Interpret AI outputs | Langfuse trace viewer | Langfuse dashboard |
| 14(4)(d) | Human override capability | `HumanOverrideGate` | `override_audit_log.json` |
| 14(4)(e) | Interrupt system (≤5s) | Kill-switch | `killswitch_compliance_log.json` |

#### NIST AI RMF Coverage

| Function | Covered |
|----------|---------|
| Govern | ✅ Constitution + Agents.md |
| Map | ✅ Phase 1 TRACEABILITY_MATRIX |
| Measure | ✅ Langfuse + UAF/CLAP |
| Manage | ✅ Gate policy + Kill-switch |

#### ASL Levels

| ASL | Trigger | Status |
|-----|---------|--------|
| ASL-1 | Default (no high-risk tasks) | ✅ Supported |
| ASL-2 | Chatbot, image generation | ✅ Supported |
| ASL-3 | Autonomous coding, scientific research | ✅ Supported |
| ASL-4 | AGI-level systems | ⚠️ Warning only — not recommended for v3.0 |

### Threshold / Action

| Condition | Action |
|-----------|--------|
| Kill-Switch triggered | `compliance.report_hr12_event()` — Art.14 evidence generated |
| Phase end | `compliance.generate_phase_report()` — COMPLIANCE_PHASE_N.md |
| Human override | Audit log entry in `override_audit_log.json` |
| ASL-4 detected | Warning + "not proceed" recommendation |

---

## Feature #13: Observability Enhancement

### Introduction

**Feature #13** extends Langfuse (Feature #11) with three specialized components:

1. **UQLM Metrics Span** (`uqlm_metrics_span.py`) — Injects UQLM uncertainty scores into OTel span attributes
2. **Decision Log** (`decision_log.py`) — YAML-encoded decision rationale per agent run
3. **Effort Metrics** (`effort_metrics.py`) — SQLite-based tracker for work-unit consumption

Together, these provide the complete observability picture: what was decided, why, and how much work it took.

### Before / After

**Before (without Observability Enhancement):**
- UQLM scores not in Langfuse traces
- Decision rationale not persisted
- No effort/cost tracking per agent run
- No audit trail for why specific actions were taken

**After (with Observability Enhancement):**
- UQLM scores visible in every Langfuse span
- Every decision logged with full reasoning in YAML
- Effort metrics tracked: time_ms, tokens, iterations
- Complete "who did what why" audit trail

### Benefits

- **UQLM in traces**: Uncertainty data visible alongside all other metrics
- **Decision rationale**: YAML log of why each decision was made
- **Effort tracking**: Quantify work per agent run (time, tokens, calls)
- **Replay capability**: Decision log enables post-hoc reconstruction

### Phase Integration

- **Hook**: All hooks
- **Phase**: Throughout all phases
- **Flow**: UQLM metrics attach to spans; decisions logged; effort tracked

```
monitoring_after_dev()
├── langfuse.set_span_attribute("uaf_score", uaf)    ← UQLM in trace
├── decision_log.write(uaf_score=...)               ← Decision rationale
└── effort.record(time_spent_ms=...)               ← Effort metrics

postflight_all()
└── effort.get_summary()                             ← Phase effort report
```

### Components

#### UQLM Metrics Span

```python
UqlmMetricsSpan.attach_to_span(
    span,
    uaf_score=0.42,
    decision="WARN",
    components={"semantic_entropy": 0.3, "self_consistency": 0.5},
    computation_time_ms=145.3
)
```

#### Decision Log Schema

```yaml
trace_id: "abc123"
span_id: "def456"
agent_id: "planner-alpha"
timestamp: "2026-04-24T14:30:00+08:00"
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
```

**Storage**: `data/decision_logs/{date}/{agent_id}_{seq:04d}.yaml`

#### Effort Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `time_spent_ms` | int | Wall-clock elapsed time in ms |
| `tokens_consumed` | int | Total LLM tokens consumed |
| `iteration_count` | int | Number of agent loops |
| `calls_count` | int | Number of external tool/LLM calls |

**Storage**: `data/effort_metrics.db` (SQLite)

### Configuration

**Feature Flags**: `"decision_log": True`, `"effort": True` (default)

```python
flags = DEFAULT_FEATURE_FLAGS.copy()
flags["decision_log"] = False  # Disable for low-overhead runs
flags["effort"] = False        # Disable for local testing
```

### Failure Strategy

Observability Enhancement uses **graceful degradation**:
- Langfuse unreachable → UQLM attrs written to fallback log
- Decision log write failure → logged as warning, execution continues
- Effort DB write failure → buffered in memory, flush retried

---

## Phase-to-Phase Flow

### Complete Execution Flow

```
Johnny: "Execute Phase 3"
         ↓
Agent: plan-phase --phase 3 --goal "FR-01~FR-08"
         ↓
Agent: run-phase --phase 3
         ↓
┌─────────────────────────────────────────────────────────────┐
│ preflight_all()                                            │
│ ├── _preflight_fsm()                    → FSM check        │
│ ├── _preflight_constitution()           → Constitution      │
│ ├── _preflight_saif_token()             → #1 SAIF          │
│ ├── _preflight_risk_assessment()        → #9 Risk          │
│ └── langfuse.trace.start()              → #11 Langfuse     │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ FR LOOP (each FR in sequence)                               │
│                                                             │
│ for FR in FRs:                                             │
│   monitoring_before_dev(FR)                                 │
│   └── decision_log.write("FR-XX dev start")                │
│       ↓                                                     │
│   sessions_spawn(developer) → files returned                │
│       ↓                                                     │
│   monitoring_after_dev(FR)                                 │
│   ├── uqlm.compute(files)              → #7 UQLM          │
│   ├── hunter.detect(files)             → #6 Hunter         │
│   ├── prompt_shield.scan(files)        → #2 Shields        │
│   ├── effort.start(dev)                → #13 Effort        │
│   └── decision_log.write(uaf, hunter)  → #13 Decision      │
│       ↓                                                     │
│   monitoring_before_rev(FR)                                 │
│   ├── governance.classify(fr_id, uaf)  → #3 Governance     │
│   ├── decision_log.write(tier=...)     → #13 Decision      │
│   └── 若 tier==HOTL → llm_cascade.start() → #5 Cascade    │
│       ↓                                                     │
│   sessions_spawn(reviewer) → review_status                 │
│       ↓                                                     │
│   monitoring_after_rev(FR)                                 │
│   ├── governance.verify(result)       → #3 Governance      │
│   ├── effort.increment(rev)           → #13 Effort         │
│   └── decision_log.write(reviewer)    → #13 Decision       │
│       ↓                                                     │
│   monitoring_hr12_check(FR, iteration)                    │
│   └── 若 >5 → Kill-Switch.trigger() → #4 KillSwitch      │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ postflight_all()                                           │
│ ├── gap_detector.scan()               → #8 Gap Detector    │
│ ├── risk_assessment.phase_end()       → #9 Risk           │
│ ├── compliance.generate_phase_report() → #12 Compliance    │
│ ├── effort.get_summary()               → #13 Effort        │
│ └── langfuse.close()                  → #11 Langfuse      │
└─────────────────────────────────────────────────────────────┘
```

### Feature Activation by Phase

| Feature | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7 | Phase 8 |
|---------|---------|---------|---------|---------|---------|---------|---------|
| #1 SAIF | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #2 Shields | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #3 Governance | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #4 KillSwitch | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #5 LLM Cascade | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #6 Hunter | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #7 UQLM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #8 Gap Detector | — | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #9 Risk | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #10 LangGraph | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| #11 Langfuse | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #12 Compliance | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| #13 Observability | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Legend**: ✅ = Active | — = Not applicable | ⬜ = Optional (disabled by default)

---

## Quick Reference

### Feature Flag Reference Table

| Feature | Flag Key | Default | Wave | Purpose |
|---------|----------|---------|------|---------|
| SAIF Identity | `"saif"` | True | 3 | Identity propagation |
| Prompt Shields | `"shields"` | True | 1 | Injection detection |
| Governance | `"governance"` | True | 3 | Tier classification |
| Kill-Switch | `"kill_switch"` | True | 1 | Emergency halt |
| LLM Cascade | `"llm_cascade"` | True | 2 | Multi-model review |
| Hunter Agent | `"hunter"` | True | 3 | Anomaly detection |
| UQLM | `"uqlm"` | True | 2 | Hallucination scoring |
| Gap Detector | `"gap_detector"` | True | 2 | Coverage gaps |
| Risk Assessment | `"risk"` | True | 4 | Risk scoring |
| LangGraph | `"checkpoint"` | False | — | HITL resume |
| LangGraph | `"parallel"` | False | — | Parallel execution |
| LangGraph | `"routing"` | False | — | Conditional routing |
| Langfuse | `"langfuse"` | True | 1 | Observability |
| Compliance | `"compliance"` | True | 4 | Regulatory reporting |
| Decision Log | `"decision_log"` | True | 1 | Decision audit trail |
| Effort Metrics | `"effort"` | True | 1 | Work-unit tracking |

### Key Thresholds

| Threshold | Value | Feature | Action |
|-----------|-------|---------|--------|
| UAF WARN | ≥ 0.3 | #7 UQLM | Warning logged |
| UAF BLOCK | ≥ 0.5 | #7 UQLM | FR rejected |
| Risk HIGH | ≥ 0.7 | #9 Risk | Johnny notification |
| Risk FREEZE | ≥ 0.9 | #9 Risk | Phase halted |
| Kill-Switch | > 5 iterations | #4 KillSwitch | Hard halt |
| ASPICE | < 80% | #12 Compliance | Non-compliance flagged |
| Gap CRITICAL | severity ≥ 0.8 | #8 Gap Detector | Johnny notification |

### Hook-to-Feature Map

| Hook | Features Active |
|------|----------------|
| `preflight_all()` | #1 SAIF, #9 Risk, #11 Langfuse |
| `monitoring_before_dev()` | #13 Decision Log |
| `monitoring_after_dev()` | #2 Shields, #6 Hunter, #7 UQLM, #13 Decision Log, #13 Effort |
| `monitoring_before_rev()` | #3 Governance, #5 LLM Cascade, #13 Decision Log |
| `monitoring_after_rev()` | #3 Governance, #13 Decision Log, #13 Effort |
| `monitoring_hr12_check()` | #4 KillSwitch, #12 Compliance |
| `postflight_all()` | #8 Gap Detector, #9 Risk, #12 Compliance, #13 Effort, #11 Langfuse |

---

## Troubleshooting

### Wave 1: Defend & Log

**Issue**: Langfuse traces not appearing in dashboard
- **Check**: Verify `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set
- **Check**: Verify Langfuse server is reachable (`curl $LANGFUSE_HOST`)
- **Check**: `feature_flags["langfuse"]` is not False
- **Fix**: Run with `OTEL_EXPORTER_OTLP_ENDPOINT` pointing to OTLP collector

**Issue**: Decision Log files not being written
- **Check**: `data/decision_logs/` directory exists and is writable
- **Check**: `feature_flags["decision_log"]` is True
- **Fix**: Check disk space; log rotation should prevent accumulation

**Issue**: Shields generating too many false positives
- **Cause**: Conservative pattern matching
- **Fix**: Adjust `shields_threshold` in feature config; currently warn-only

**Issue**: Kill-Switch not triggering on HR-12
- **Check**: `feature_flags["kill_switch"]` is True
- **Check**: `monitoring_hr12_check()` is being called with correct iteration count
- **Fix**: Verify `HR12_THRESHOLD=5` in config

### Wave 2: Score & Detect

**Issue**: UQLM returning uaf=0.0 for all outputs
- **Check**: `feature_flags["uqlm"]` is True
- **Check**: `EnsembleScorer` initialized successfully (check logs)
- **Cause**: UQLM disabled or not available → falls back to 0.0
- **Fix**: Install dependencies: `pip install detection/`

**Issue**: UQLM blocking legitimate outputs
- **Cause**: UAF threshold too aggressive (0.5 block threshold)
- **Fix**: Increase `UAF_THRESHOLD_BLOCK` to 0.7 if hallucinations are well-calibrated
- **Note**: Conservative default (0.5) is intentional for safety

**Issue**: Gap Detector scan hanging
- **Check**: 04-tests directory exists
- **Cause**: Large codebase with many files
- **Fix**: Add `.gitignore`-style exclusions in gap_detector config

**Issue**: Gap Detector reporting orphaned code that IS in SPEC
- **Cause**: Fuzzy match threshold too strict (similarity < 0.6)
- **Fix**: Lower similarity threshold to 0.5 in gap_detector config

### Wave 3: Govern & Hunt

**Issue**: SAIF token validation always failing
- **Check**: `SAIFMiddleware` initialized correctly
- **Check**: `agents/` directory contains valid Agents.md files
- **Cause**: SAIF not available → falls back to allowing all requests
- **Fix**: Ensure `implement/mcp/saif_identity_middleware.py` exists

**Issue**: Governance tier always returns LOW
- **Check**: UQLM is running (tier depends on UAF score)
- **Check**: `previous_rejections` counter is being updated
- **Cause**: UAF < 0.7, rejections < 3, risk < 0.7 → LOW is correct
- **Fix**: If tier should be higher, manually elevate via risk_assessor

**Issue**: Hunter detecting false tampering
- **Cause**: Comments containing "ignore", "forget", etc. in benign context
- **Fix**: Hunter works on confidence levels — confirmed only at CRITICAL/HIGH
- **Note**: Suspicious but unconfirmed only triggers tier elevation, not block

**Issue**: LLM Cascade not starting for HOTL
- **Check**: `governance` feature enabled
- **Check**: `llm_cascade` feature enabled
- **Check**: Tier correctly classified as HOTL
- **Fix**: Manual tier override possible via `adapter._current_tier = Tier.HOTL`

### Wave 4: Assess & Comply

**Issue**: Risk Assessment blocking valid phase runs
- **Cause**: Risk score > 0.9 at preflight
- **Fix**: Investigate which risk signal is elevated via `RISK_REGISTER.md`
- **Note**: Blocking at 0.9 is intentional; if clearly false positive, temporarily disable risk feature

**Issue**: Compliance report missing evidence
- **Check**: Langfuse running (evidence sources from Langfuse)
- **Check**: All Features enabled during phase run
- **Cause**: Evidence collected from Features; partial run = partial evidence
- **Fix**: Re-run full phase with all Features enabled

**Issue**: ASPICE score showing < 80% but implementation looks complete
- **Cause**: ASPICE measures process compliance, not implementation completeness
- **Fix**: Review process artifacts: decision logs, effort records, compliance reports

### Feature #10: LangGraph

**Issue**: Checkpoint resume not working
- **Check**: `feature_flags["checkpoint"]` is True
- **Check**: Checkpoint storage backend (MemorySaver vs SQLiteSaver)
- **Cause**: MemorySaver checkpoints lost on process restart
- **Fix**: Use SQLiteSaver or PostgresSaver for persistence

**Issue**: Parallel cascade not executing in parallel
- **Check**: `feature_flags["parallel"]` is True
- **Check**: `langgraph` installed: `pip install langgraph`
- **Cause**: Sequential fallback if parallel execution fails
- **Fix**: Verify LangGraph version ≥ 0.0.20

**Issue**: Router not routing correctly
- **Check**: `feature_flags["routing"]` is True
- **Check**: Routing function returns valid route keys
- **Cause**: Route key not in mapping → routes to `default` or error
- **Fix**: Ensure routing function returns keys that exist in edge mapping

### General

**Issue**: PhaseHooks Adapter not found
- **Fix**: Ensure `METHODOLOGY_ROOT` in path; import `from adapters.phase_hooks_adapter import PhaseHooksAdapter`

**Issue**: Feature enabled but not behaving as expected
- **Check**: Verify feature flag in `DEFAULT_FEATURE_FLAGS` matches intended value
- **Check**: Check logs for feature initialization messages: `[FEATURE_NAME] initialized`
- **Cause**: Override not applied correctly
- **Fix**: Pass explicit `feature_flags` dict to `PhaseHooksAdapter.__init__()`

**Issue**: Performance degradation with all Features enabled
- **Cause**: All Features add overhead; UQLM and Hunter most expensive
- **Fix**: Disable non-critical Features in fast-iteration phases
- **Note**: Wave 1 (Defend & Log) features are lightweight; Wave 2 (UQLM/Hunter) add ~100-500ms per FR

---

*End of Features Guide — methodology-v2 v9.1*
