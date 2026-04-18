# SPEC.md — Feature #5: LLM Cascade

## 1. Feature Overview

### Feature Name
LLM Cascade (Multi-Model Routing)

### Core Functionality
Automatic fallback routing across LLM models — when primary model fails, times out, or returns low confidence, system transparently escalates to backup models in priority order until successful response or cascade exhausted.

### Target Response Time
< 3 seconds for cascade decision (excluding model inference time)

### Cost Philosophy
**"Use expensive models only when necessary"** — route to cheaper models for simple tasks, escalate to premium models only when required. Same task, better margin.

---

## 2. Problem Statement

### Why Static Model Selection Fails
- **Single point of failure**: If one model API goes down, entire system fails
- **No latency optimization**: Expensive premium model used even for simple tasks
- **Cost inefficiency**: GPT-4 class models billed for tasks BERT-class models could handle
- **Provider rate limits**: High-volume usage hits rate limits with no fallback
- **Silent failures**: Model returns error or malformed output with no recovery
- **No confidence awareness**: System treats model outputs as equally trustworthy regardless of actual quality

### Why Existing Routing Is Insufficient
- **Round-robin is not intelligent**: Doesn't consider task complexity or model capability match
- **Hardcoded fallbacks are fragile**: Static retry with same model = same failure
- **No cost-aware routing**: No concept of cost-per-task optimization
- **No confidence scoring**: Doesn't use uncertainty quantification to trigger escalation

### Cost of Not Having Cascade
- **Downstream failures**: Primary model failure cascades to dependent workflows
- **Budget overruns**: Expensive models used unnecessarily, margin erosion
- **User experience degradation**: Slow responses or failures on complex tasks
- **Operational blindness**: No visibility into model-level reliability metrics

---

## 3. User Stories

### Operator Stories

**US-LC-1: Transparent Fallback**
> As an **operator**, I want **automatic model fallback when primary fails** so that **end users experience seamless continuity even when a model provider has issues**.

**US-LC-2: Cost-Optimized Routing**
> As an **operator**, I want **system to route easy tasks to cheaper models** so that **my LLM bill is optimized without manual task classification**.

**US-LC-3: Cascade Visibility**
> As an **operator**, I want **dashboard showing which models were used per request** so that **I can audit cost attribution and diagnose routing issues**.

### Developer Stories

**US-LC-4: Configurable Cascade Chains**
> As a **developer**, I want to **define custom cascade chains per task type** so that **different workflows can have different model priority orders**.

**US-LC-5: Confidence Threshold Triggers**
> As a **developer**, I want **system to escalate to next model when confidence falls below threshold** so that **low-quality outputs are caught and improved automatically**.

**US-LC-6: Timeout-Aware Routing**
> As a **developer**, I want **system to timeout primary and fallback within configurable window** so that **users don't wait forever for a hanging model**.

### System Stories

**US-LC-7: Latency Budget Management**
> As the **system**, I want to **enforce total latency budget across cascade** so that **slow models are skipped if they would exceed overall SLA**.

**US-LC-8: Rate Limit Handling**
> As the **system**, I want to **detect provider rate limits and skip to next model in chain** so that **system remains available even when usage spikes**.

**US-LC-9: Provider Health Tracking**
> As the **system**, I want to **track per-provider reliability metrics (success rate, latency, errors)** so that **routing decisions are data-driven, not static**.

**US-LC-10: Cost Cap Enforcement**
> As the **system**, I want to **stop cascade if cost累积 exceeds budget** so that ** runaway cascades don't multiply costs unexpectedly**.

---

## 4. Functional Requirements

| FR-ID | Description | Acceptance Criteria |
|-------|-------------|---------------------|
| **FR-LC-1** | Cascade Router | System shall route requests through configured model chain in priority order until success or chain exhausted |
| **FR-LC-2** | Failure Mode Handling | System shall treat the following as cascade triggers: API errors, timeout, malformed response, rate limit (429), server error (500-599) |
| **FR-LC-3** | Confidence-Based Escalation | System shall compute confidence score on model output; if score < configured threshold, escalate to next model |
| **FR-LC-4** | Configurable Cascade Chains | Operator shall be able to define cascade chains as ordered lists: `[primary, fallback1, fallback2, ...]` per task type |
| **FR-LC-5** | Latency Budget | Total time from request to final response shall not exceed configured `latency_budget_ms`; if exceeded, return last available response or error |
| **FR-LC-6** | Cost Tracking | System shall record per-request cost (sum of token costs across all cascade attempts) and expose via metrics API |
| **FR-LC-7** | Provider Health Metrics | System shall track rolling success rate, median latency, error types per provider; expose as `ProviderHealth` struct |
| **FR-LC-8** | Rate Limit Detection | Upon HTTP 429 from provider, immediately skip to next model; do not retry same provider within `cooldown_seconds` |
| **FR-LC-9** | Confidence Scoring | System shall compute output confidence as normalized score 0-1 based on: token entropy, repetition patterns, length sanity, parse validity |
| **FR-LC-10** | Cascade Exhausted Handling | When all models in chain fail/return low confidence/exceed latency budget, return error with `cascade_failure` reason and attempted models list |
| **FR-LC-11** | Request-Level Isolation | Each cascade request shall be independent; failures in one request shall not affect concurrent requests |

---

## 5. Cascade Strategy Table

| Strategy Name | Trigger Condition | Fallback Model | Degraded Behavior |
|---------------|-------------------|----------------|-------------------|
| **Fast-Fail** | Primary returns error immediately | Next in chain | Return last valid response or error |
| **Confidence-Gated** | Output confidence < threshold | Next in chain | Return lowest-confidence valid response |
| **Latency-Budgeted** | Cumulative latency > budget | Stop cascade | Return best response so far or timeout error |
| **Cost-Capped** | Cumulative cost > cap | Stop cascade | Return cheapest valid response or error |
| **Rate-Limit-Aware** | HTTP 429 received | Skip provider, try next | Skip provider for `cooldown_seconds` |
| **Health-Based** | Provider success rate < 80% | Next healthy provider | Route away from unhealthy providers |

### Default Cascade Chain
```
Claude Opus → Claude Sonnet → GPT-4o → GPT-4o-mini → Gemini-Pro
```
(Most capable → Most cost-effective, left-to-right priority)

---

## 6. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-End Success Rate | > 99.5% | (Successful responses / Total requests), counting cascade as success if any model succeeds |
| Cost Reduction | > 30% vs single premium model | (Baseline single-model cost - Actual cascade cost) / Baseline |
| Cascade Hit Rate | 15-40% | Percentage of requests that used at least one fallback |
| Average Cascade Depth | 1.2-1.8 models | Mean number of models attempted per request |
| P99 Latency | < 10 seconds | Time from request start to final response including all retries |
| Confidence Accuracy | > 85% | Correlation between low-confidence flag and actual output quality issues |
| Cost Attribution Error | < 1% | Variance between logged cost and provider billing |

---

## 7. Out of Scope

- **Model fine-tuning**: Cascade selects from pre-trained models, does not train or fine-tune
- **Multi-modal routing**: This spec covers text-only models; images/audio handled by separate system
- **Batch request optimization**: Cascade is per-request; batch scheduling is separate
- **Model-specific prompt engineering**: Prompt templates are external; cascade just routes to models

---

## 8. Dependencies

| Dependency | Source | Purpose |
|------------|--------|---------|
| **Model Provider APIs** | External | Claude, OpenAI, Google Gemini — abstraction via standard HTTP+JSON interface |
| **Feature #1: MCP/SAIF** | v3/mcp-saif | Identity propagation ensures model calls carry correct attribution |
| **Feature #2: Prompt Shields** | v3/prompt-shields | Input validation before cascade; output validation after cascade |
| **Feature #3: Tiered Governance** | v3/tiered-governance | Governance triggers when cascade behavior suggests policy concern |
| **Configuration Store** | Core | Stores cascade chains, thresholds, latency budgets per task type |
| **Metrics Infrastructure** | Core | Exposes provider health, cascade stats to observability layer |

---

## 9. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Cascade Router                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ Router      │  │ Health Track │  │ Cost Tracker           │  │
│  │ (orchestrate)│ │ (per provider)│  │ (per request + cumul.) │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────┬────────────┘  │
│         │                │                      │               │
│         ▼                ▼                      ▼               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Cascade Engine                         │    │
│  │  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐  │    │
│  │  │ Model 1 │──▶│ Model 2 │──▶│ Model 3 │──▶│ Model N │  │    │
│  │  │(primary)│   │(fallback)│   │(fallback)│   │(last)   │  │    │
│  │  └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘  │    │
│  │       │             │             │             │        │    │
│  │       ▼             ▼             ▼             ▼        │    │
│  │  [Confidence Check] [Latency Budget] [Cost Cap]  [Error]   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Claude   │    │ OpenAI   │    │ Gemini   │
   └──────────┘    └──────────┘    └──────────┘
```

### Cascade Flow

```
Request → Router.select_model()
         │
         ▼
    Model #1 (primary)
         │
    ┌────┼────┐
    │    │    │
 success failure timeout
    │    │    │
    │    ▼    ▼
    │  Retry / Timeout → Model #2
    │    │
    │    ▼
    │  [Confidence Check]
    │    │
    │  confidence < threshold?
    │    │yes         │no
    │    ▼            ▼
    │  Model #2   [Return Response]
    │    │
    └────┘
         │
    All models exhausted?
         │yes              │no
         ▼                  ▼
   [Return Error]     [Return Response]
```

---

## 10. State Definitions

| State | Description |
|-------|-------------|
| **IDLE** | No active request; system monitoring provider health |
| **ROUTING** | Selecting model based on health/cost/priority |
| **MODEL_CALL** | Active call to selected model |
| **CASCADE_CHECK** | Evaluating success/failure/confidence/latency/cost |
| **EXHAUSTED** | All models tried; preparing error response |

---

## 11. Key Interfaces

```python
@dataclass
class CascadeConfig:
    chain: List[ModelConfig]           # Ordered model list
    latency_budget_ms: int = 10000     # Max total time
    cost_cap_usd: float = 0.50         # Max cost per request
    confidence_threshold: float = 0.7  # Min acceptable confidence

@dataclass
class CascadeResult:
    response: str
    model_used: str
    cascade_depth: int                  # Which model in chain succeeded
    total_cost_usd: float
    latency_ms: int
    confidence: float
    attempt_history: List[AttemptRecord]

@dataclass
class ProviderHealth:
    provider: str
    success_rate: float                # Rolling 24h
    median_latency_ms: int
    error_types: Dict[str, int]
    rate_limit_count: int              # 429s in rolling window
```

---

## 12. Acceptance Test Scenarios

| Scenario | Expected Result |
|----------|-----------------|
| Primary model returns 200 with high confidence | Return immediately, no fallback |
| Primary model returns 500 error | Cascade to fallback, record error |
| Primary model times out | Cascade to fallback, record timeout |
| Output confidence = 0.5 (< threshold) | Cascade to next model |
| All models in chain fail | Return error with `cascade_failure` and attempt list |
| Latency budget exceeded mid-cascade | Return best response so far or timeout error |
| Total cost exceeds cap | Stop cascade, return cheapest valid response |
| Provider has 5 consecutive 429s | Skip provider, route to next healthy model |
| Concurrent requests to same provider | Independent cascades, no shared state mutation |