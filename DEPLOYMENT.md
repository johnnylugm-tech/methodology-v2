# DEPLOYMENT.md — Feature #5: LLM Cascade

> **Version:** 1.0
> **Feature:** #5 — LLM Cascade (Multi-Model Routing)
> **Branch:** `v3/llm-cascade`
> **Framework:** methodology-v3

---

## 1. Feature Overview

| Property | Value |
|----------|-------|
| **Feature Name** | LLM Cascade (Multi-Model Routing) |
| **Version** | 1.0 |
| **Deployment Type** | Framework library module |
| **Deployment Scope** | All methodology-v3 projects using LLM routing |
| **Deprecates** | N/A (new feature) |
| **Replaces** | N/A (new feature) |

### What It Does

LLM Cascade routes LLM requests across a configurable chain of model providers (Claude, GPT, Gemini), automatically escalating to the next model when confidence, latency, or cost thresholds are breached. It follows a **IDLE → ROUTING → MODEL_CALL → CASCADE_CHECK → EXHAUSTED** state machine.

**Core responsibilities:**
- Route requests through a priority-ordered model chain
- Score output confidence using entropy, repetition, length, and parse validity
- Track per-provider health (rolling success rate, median latency)
- Enforce latency budgets and cost caps
- Emit metrics and integrate with other safety features

---

## 2. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Uses `enum.StrEnum`, `typing.Self` |
| pytest | Latest | For running test suite |
| Feature #1 (MCP/SAIF) | — | For identity propagation (stubbed) |
| Feature #2 (Prompt Shields) | — | For input/output validation (stubbed) |
| Feature #3 (Tiered Governance) | — | For governance triggers (stubbed) |

### API Credentials Required

| Provider | Env Variable | Notes |
|----------|-------------|-------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | For Claude Opus, Sonnet |
| OpenAI (GPT) | `OPENAI_API_KEY` | For GPT-4o, GPT-4o-mini |
| Google (Gemini) | `GOOGLE_API_KEY` | For Gemini-Pro |

---

## 3. Installation Steps

### Step 1 — Verify Module Structure

```
implement/llm_cascade/
├── __init__.py
├── enums.py
├── models.py
├── exceptions.py
├── confidence_scorer.py
├── health_tracker.py
├── cost_tracker.py
├── cascade_engine.py
├── cascade_router.py
├── api.py
├── integration.py
└── api_clients/
    ├── __init__.py
    ├── base.py
    ├── anthropic.py
    ├── openai.py
    └── google.py
```

### Step 2 — Install API Keys

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."
```

Or via `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

### Step 3 — Import the Module

```python
from implement.llm_cascade import LLMCascade, CascadeConfig
from implement.llm_cascade.enums import ModelProvider, CascadeStateEnum, TriggerReason
```

### Step 4 — Configure and Initialize

```python
config = CascadeConfig(
    model_chain=[
        ModelProvider.ANTHROPIC_OPUS,
        ModelProvider.ANTHROPIC_SONNET,
        ModelProvider.OPENAI_GPT4O,
        ModelProvider.OPENAI_GPT4O_MINI,
        ModelProvider.GOOGLE_GEMINI_PRO,
    ],
    latency_budget=10.0,      # seconds
    cost_cap=0.50,            # dollars per request
    confidence_threshold=0.7,
    confidence_weights={
        "entropy": 0.30,
        "repetition": 0.25,
        "length": 0.20,
        "parse_validity": 0.25,
    },
)

cascade = LLMCascade(config=config)
```

### Step 5 — Run a Request

```python
result = cascade.route(
    prompt="What is the capital of France?",
    system_prompt="You are a helpful assistant.",
)
print(result.final_output)
print(f"Cascade stopped at: {result.provider_used}")
print(f"Confidence: {result.confidence}")
print(f"Cost: ${result.cost_usd}")
```

---

## 4. Configuration Parameters

### CascadeConfig

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `model_chain` | Claude Opus → Sonnet → GPT-4o → GPT-4o-mini → Gemini-Pro | `list[ModelProvider]` | Priority-ordered provider chain |
| `latency_budget` | `10.0` | `float` | Max seconds before cascade stops |
| `cost_cap` | `0.50` | `float` | Max USD per request |
| `confidence_threshold` | `0.7` | `float` | Score below this triggers escalation |
| `confidence_weights` | entropy 0.30, repetition 0.25, length 0.20, parse_validity 0.25 | `dict` | Per-signal weights summing to 1.0 |
| `max_attempts_per_request` | `5` | `int` | Hard cap on escalation steps |
| `excluded_providers` | `[]` | `list[ModelProvider]` | Providers to skip |
| `enable_health_tracking` | `True` | `bool` | Enable rolling health stats |
| `enable_cost_tracking` | `True` | `bool` | Enable cost tracking |

### ProviderHealthConfig (per-provider override)

| Parameter | Default | Type | Description |
|-----------|---------|------|-------------|
| `rolling_window_size` | `100` | `int` | Number of requests for rolling stats |
| `success_rate_threshold` | `0.8` | `float` | Below this → provider deprioritized |
| `latency_p99_threshold_ms` | `5000` | `float` | Above this → provider deprioritized |
| `rate_limit_cooldown_seconds` | `60` | `float` | Cooldown after 429 |

---

## 5. Usage Examples

### Example 1 — Basic Routing

```python
from implement.llm_cascade import LLMCascade, CascadeConfig
from implement.llm_cascade.enums import ModelProvider

config = CascadeConfig(
    model_chain=[
        ModelProvider.ANTHROPIC_OPUS,
        ModelProvider.OPENAI_GPT4O,
    ],
    latency_budget=10.0,
    cost_cap=0.50,
)
cascade = LLMCascade(config=config)

result = cascade.route(
    prompt="Explain quantum entanglement in one paragraph.",
)
print(f"Output: {result.final_output}")
print(f"Provider: {result.provider_used}")
print(f"Attempts: {result.attempt_count}")
```

### Example 2 — Route with Fallback

```python
result = cascade.route_with_fallback(
    prompt="Write a haiku about moonlight.",
    fallback_output="A gentle default haiku response.",
)
print(f"Output: {result.final_output}")
print(f"State: {result.state}")
```

### Example 3 — Check Provider Health

```python
from implement.llm_cascade import LLMCascade

cascade = LLMCascade()

health = cascade.get_provider_health(ModelProvider.ANTHROPIC_OPUS)
print(f"Success rate: {health.success_rate:.2%}")
print(f"Median latency: {health.median_latency_ms:.1f}ms")
print(f"In cooldown: {health.in_cooldown}")
```

### Example 4 — Check Cumulative Cost

```python
cost = cascade.get_cumulative_cost()
print(f"Total cost (session): ${cost.total_usd:.4f}")
print(f"Request count: {cost.request_count}")
print(f"Avg cost per request: ${cost.avg_cost_per_request:.4f}")
```

### Example 5 — Custom Confidence Weights

```python
from implement.llm_cascade import CascadeConfig

config = CascadeConfig(
    confidence_weights={
        "entropy": 0.40,      # weight more on randomness
        "repetition": 0.20,
        "length": 0.20,
        "parse_validity": 0.20,
    },
    confidence_threshold=0.6,  # lower threshold = less escalation
)
```

### Example 6 — Exclude a Provider

```python
config = CascadeConfig(
    excluded_providers=[ModelProvider.GOOGLE_GEMINI_PRO],
    # Requests will skip Gemini even if prior models fail
)
```

---

## 6. State Machine

```
    ┌─────────┐
    │  IDLE   │ ◄──────────────────────────┐
    └────┬────┘                            │
         │ route() called                  │
         ▼                                 │
   ┌───────────┐                          │
   │ ROUTING   │                          │
   └─────┬─────┘                          │
         │ model selected                  │
         ▼                                 │
  ┌──────────────┐    response received    │
  │ MODEL_CALL   │────────────────────────┤
  └──────┬───────┘                        │
         │                                 │
         ▼                                 │
  ┌────────────────┐  confidence >= thresh │
  │CASCADE_CHECK   │─────────────────────►│ return result
  └───────┬────────┘                      │
          │ confidence < thresh            │
          │ latency not exceeded           │
          │ cost not exceeded              │
          │ providers remain               │
          ▼                                │
     (next provider)                        │
     ─────────────────────────────────────
         │
         │ no providers remain OR
         │ latency budget exceeded OR
         │ cost cap exceeded
         ▼
  ┌─────────────┐
  │  EXHAUSTED  │ ───────────────────────►│ return best effort
  └─────────────┘
```

### State Definitions

| State | Description |
|-------|-------------|
| **IDLE** | No active request; ready to route |
| **ROUTING** | Selecting next provider in chain |
| **MODEL_CALL** | Waiting for model response |
| **CASCADE_CHECK** | Evaluating confidence, latency, cost |
| **EXHAUSTED** | All providers exhausted; returning best effort |

---

## 7. Cascade Result Object

```python
@dataclass
class CascadeResult:
    final_output: str                    # The response text
    provider_used: ModelProvider         # Which provider produced the output
    confidence: float                    # 0.0–1.0 confidence score
    trigger_reason: TriggerReason | None # Why cascade stopped/escalated
    state: CascadeStateEnum              # Final state
    attempt_count: int                   # Number of model calls made
    cost_usd: float                     # Cost of this request
    latency_seconds: float               # Total request latency
    error: str | None                   # Error message if failed
```

---

## 8. Metrics & Observability

### Per-Request Metrics

```python
result = cascade.route(prompt="...")
print(f"  Provider:    {result.provider_used}")
print(f"  Confidence:  {result.confidence:.3f}")
print(f"  Attempts:    {result.attempt_count}")
print(f"  Cost:        ${result.cost_usd:.4f}")
print(f"  Latency:     {result.latency_seconds:.2f}s")
print(f"  Trigger:     {result.trigger_reason}")
```

### Session-Level Metrics

```python
session = cascade.get_session_metrics()
print(f"  Total requests:  {session.total_requests}")
print(f"  Total cost:      ${session.total_cost_usd:.4f}")
print(f"  Avg confidence:  {session.avg_confidence:.3f}")
print(f"  Exhausted rate:  {session.exhausted_rate:.2%}")
```

### Provider Health

```python
for provider in ModelProvider:
    health = cascade.get_provider_health(provider)
    print(f"  {provider.name}: success={health.success_rate:.2%}, "
          f"latency={health.median_latency_ms:.1f}ms, "
          f"cooldown={health.in_cooldown}")
```

---

## 9. Rollback Procedures

### Disable Cascade Entirely

```python
# Use a single-model config to effectively disable cascade
from implement.llm_cascade import CascadeConfig
from implement.llm_cascade.enums import ModelProvider

config = CascadeConfig(
    model_chain=[ModelProvider.ANTHROPIC_OPUS],  # single provider
    max_attempts_per_request=1,
)
cascade = LLMCascade(config=config)
```

### Reset Provider Health

```python
from implement.llm_cascade import LLMCascade
from implement.llm_cascade.enums import ModelProvider

cascade = LLMCascade()
cascade.reset_provider_health(ModelProvider.ANTHROPIC_OPUS)
```

### Reset Cumulative Cost

```python
cascade.reset_cumulative_cost()
```

---

## 10. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `ImportError` on deploy | Module not in Python path | Ensure `implement/` is in `PYTHONPATH` or install via `pip install -e .` |
| All requests return EXHAUSTED | API keys not set or all providers failing | Check `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` env vars |
| Cost keeps escalating | `cost_cap` too high or `model_chain` too long | Lower `cost_cap`; reduce `model_chain` length |
| Latency always times out | Network latency to all providers | Increase `latency_budget`; check network/firewall |
| Confidence always low | Output genuinely low quality or scoring miscalibrated | Tune `confidence_weights`; lower `confidence_threshold` |
| 429 errors cascading | Multiple providers rate-limited | Enable `rate_limit_cooldown_seconds`; implement backoff |
| `cascade_engine.py` returns simulated response | `api_clients/` not wired to real APIs | Wire `api_clients/anthropic.py`, `openai.py`, `google.py` to real APIs |

### Debugging Commands

```bash
# Verify imports
python3 -c "from implement.llm_cascade import LLMCascade; print('OK')"

# Check API key presence
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
echo $GOOGLE_API_KEY

# Run tests
pytest test/llm_cascade/ -v --cov=implement.llm_cascade --cov-report=term-missing

# Check cascade state machine
python3 -c "
from implement.llm_cascade import CascadeConfig, LLMCascade
from implement.llm_cascade.enums import CascadeStateEnum
c = LLMCascade(config=CascadeConfig())
print('States:', [s.name for s in CascadeStateEnum])
"
```

---

## Quick Reference

```python
# Minimal setup
from implement.llm_cascade import LLMCascade, CascadeConfig

config = CascadeConfig()  # uses all defaults
cascade = LLMCascade(config=config)

# Route a request
result = cascade.route(prompt="What is 2+2?")

# Check results
print(result.final_output)
print(f"Provider: {result.provider_used}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Cost: ${result.cost_usd:.4f}")
print(f"State: {result.state.name}")
```
