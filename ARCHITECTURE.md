# ARCHITECTURE.md — Feature #5: LLM Cascade (Multi-Model Routing)

**Document Version:** 1.0
**Feature:** LLM Cascade — Automatic Fallback Routing Across LLM Models
**Status:** Phase 2 — Architecture Design
**Last Updated:** 2026-04-17

---

## 1. Architecture Overview

### 1.1 System Purpose

LLM Cascade is a multi-model routing layer that automatically routes LLM requests through a priority-ordered chain of models. When the primary model fails, times out, or returns low-confidence output, the system transparently escalates to backup models until a successful response is obtained or the cascade is exhausted.

**Cost Philosophy:** "Use expensive models only when necessary" — route to cheaper models for simple tasks, escalate to premium models only when required. Same task, better margin.

**Performance Target:** < 3 seconds for cascade decision (routing logic, excluding model inference time).

### 1.2 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LLM CASCADE ARCHITECTURE                              │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         Cascade Router (Facade)                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │  │
│  │  │  Router      │  │ Health Track │  │  Cost Tracker                │  │  │
│  │  │  (orchestrate│  │ (per provider)│  │  (per request + cumulative)  │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └─────────────┬────────────────┘  │  │
│  └─────────┼─────────────────┼────────────────────────┼────────────────────┘  │
│            │                 │                        │                       │
│            ▼                 ▼                        ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────┐     │
│  │                      Cascade Engine                                  │     │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │     │
│  │  │ Model #1 │──▶│ Model #2 │──▶│ Model #3 │──▶│ Model #N │        │     │
│  │  │(primary) │   │(fallback)│   │(fallback)│   │ (last)   │        │     │
│  │  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘        │     │
│  │       │              │              │              │               │     │
│  │       ▼              ▼              ▼              ▼               │     │
│  │  [Confidence Scorer] ── Budget Enforcer ── Error Classifier         │     │
│  └──────────────────────────────────────────────────────────────────────┘     │
│                                  │                                             │
│                                  ▼                                             │
│                        ┌──────────────────┐                                   │
│                        │  Result Assembler│                                   │
│                        └──────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │ Claude   │    │ OpenAI   │    │  Gemini  │
   │ (Anthropic)│   │  (GPT)   │    │ (Google) │
   └──────────┘    └──────────┘    └──────────┘
```

### 1.3 Data Flow

```
Request (prompt, task_type, CascadeConfig)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ ROUTING: Router.select_model(chain, health, cost_budget)       │
│   - Read ProviderHealth for each provider                       │
│   - Skip providers with success_rate < 0.8 or active cooldown  │
│   - Select highest-priority healthy provider                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ MODEL_CALL: Cascade Engine.call_model(model, prompt)            │
│   - Execute HTTP/JSON request to model provider API            │
│   - Track latency per attempt                                   │
│   - Handle timeout, errors, rate limits                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ CASCADE_CHECK: Evaluate response                                │
│   ┌─────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│   │ Error?      │  │ Latency OK?   │  │ Confidence >=       │   │
│   │ (5xx/429/   │  │ < budget_left │  │ threshold?          │   │
│   │  timeout)   │  │               │  │                     │   │
│   └──────┬──────┘  └───────┬───────┘  └──────────┬──────────┘   │
│          │ yes              │ yes                  │ yes          │ no
│          ▼                  ▼                      ▼              ▼
│    [Next Model]      [Return Response]     [Return Response]  [Next Model]
│    in chain          (CascadeResult)         (CascadeResult)   in chain
└─────────────────────────────────────────────────────────────────┘
                          │
            All models exhausted?
                          │yes
                          ▼
              [Return CascadeResult with cascade_failure]
```

### 1.4 Key Components

| Component | Responsibility | Key Methods |
|-----------|---------------|-------------|
| **Cascade Router** | Facade; orchestrates entire cascade flow | `route(prompt, config)`, `select_model()` |
| **Health Tracker** | Track per-provider reliability (success rate, latency, errors) | `get_health(provider)`, `record_result()`, `is_healthy()` |
| **Cost Tracker** | Track per-request and cumulative cost | `add_cost()`, `get_total()`, `is_within_budget()` |
| **Cascade Engine** | Execute model calls in chain, handle retries | `execute_chain()`, `call_model()` |
| **Confidence Scorer** | Compute confidence 0-1 on model output | `score(output) → float` |

---

## 2. Component Specifications

### 2.1 Cascade Router

**Responsibility:** Facade class that orchestrates the entire cascade flow. Selects the first model based on health/cost/priority, then delegates to Cascade Engine for execution.

**Public API:**
```python
class CascadeRouter:
    def __init__(
        self,
        health_tracker: Optional[HealthTracker] = None,
        cost_tracker: Optional[CostTracker] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None
    ):
        """Initialize with optional injected dependencies."""

    async def route(
        self,
        prompt: str,
        config: CascadeConfig
    ) -> CascadeResult:
        """
        Main entry point. Executes full cascade chain.
        Returns CascadeResult on success or cascade exhaustion.
        """

    def select_model(
        self,
        chain: List[ModelConfig],
        health_map: Dict[str, ProviderHealth],
        remaining_budget_ms: int,
        remaining_budget_usd: float
    ) -> Optional[ModelConfig]:
        """
        Select highest-priority healthy provider from chain.
        Returns None if no healthy providers remain.
        """
```

**State:**
- `health_tracker: HealthTracker`
- `cost_tracker: CostTracker`
- `confidence_scorer: ConfidenceScorer`
- `cascade_engine: CascadeEngine`

**Interactions:**
- Calls HealthTracker to get per-provider health
- Calls CostTracker to enforce cost cap
- Delegates to CascadeEngine for actual model calls
- Calls ConfidenceScorer on each response

---

### 2.2 Health Tracker

**Responsibility:** Track rolling reliability metrics per model provider — success rate, median latency, error type distribution, and rate-limit count. Used by Router to skip unhealthy providers.

**Public API:**
```python
class HealthTracker:
    def record_result(
        self,
        provider: str,
        latency_ms: int,
        success: bool,
        error_type: Optional[str] = None,
        is_rate_limit: bool = False
    ) -> None:
        """Record outcome of a model call for health tracking."""

    def get_health(self, provider: str) -> ProviderHealth:
        """Get current health metrics for provider."""

    def is_healthy(self, provider: str, min_success_rate: float = 0.8) -> bool:
        """Check if provider is healthy enough for routing."""

    def get_cooldown_remaining(self, provider: str) -> float:
        """Get remaining cooldown seconds for rate-limited provider."""

    def get_all_health(self) -> Dict[str, ProviderHealth]:
        """Get health for all tracked providers."""
```

**State:**
- `health_data: Dict[str, ProviderHealth]` — rolling window per provider
- `window_seconds: int = 86400` — 24-hour rolling window (configurable)
- `rate_limit_cooldown_seconds: float = 60.0` — cooldown after 429 (configurable)
- `success_buffer: Dict[str, List[Tuple[bool, datetime]]]` — raw results for rolling rate
- `latency_buffer: Dict[str, List[int]]` — raw latencies for median calculation
- `error_buffer: Dict[str, Dict[str, int]]` — error type counts
- `rate_limit_timestamps: Dict[str, List[datetime]]` — 429 occurrence times

**Rolling Window Calculation:**
```python
def _compute_success_rate(self, provider: str) -> float:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=self.window_seconds)
    recent = [(s, t) for (s, t) in self.success_buffer[provider] if t >= window_start]
    if not recent:
        return 1.0  # No data → assume healthy
    return sum(1 for s, _ in recent if s) / len(recent)

def _compute_median_latency(self, provider: str) -> int:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=self.window_seconds)
    recent = [l for l, t in self.latency_buffer[provider] if t >= window_start]
    if not recent:
        return 0
    return int(sorted(recent)[len(recent) // 2])
```

**Interactions:**
- Called by CascadeEngine after each model call
- Called by Router before selecting a model

---

### 2.3 Cost Tracker

**Responsibility:** Track token usage and compute cost per model call and per cascade request. Enforce cost caps per request and cumulative budgets.

**Public API:**
```python
class CostTracker:
    def add_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_input: float,
        cost_per_1k_output: float
    ) -> float:
        """
        Record a model call's cost.
        Returns cost in USD for this call.
        """

    def get_total_cost(self) -> float:
        """Get cumulative cost for current cascade request."""

    def is_within_budget(self, config: CascadeConfig) -> bool:
        """Check if remaining budget allows another attempt."""

    def get_cost_breakdown(self) -> List[AttemptCost]:
        """Get per-attempt cost breakdown."""

    def reset(self) -> None:
        """Reset cost tracking for new cascade request."""
```

**State:**
- `attempt_costs: List[AttemptCost]` — cost per model attempt
- `total_cost_usd: float` — running total for current request
- `token_pricing: Dict[str, ModelPricing]` — per-model token pricing

**Cost Calculation:**
```python
def add_cost(...) -> float:
    input_cost = (input_tokens / 1000) * cost_per_1k_input
    output_cost = (output_tokens / 1000) * cost_per_1k_output
    call_cost = input_cost + output_cost
    self.total_cost_usd += call_cost
    self.attempt_costs.append(AttemptCost(...))
    return call_cost
```

**Model Pricing (default, overridable):**
| Model | Input $/1K tokens | Output $/1K tokens |
|-------|------------------|-------------------|
| Claude Opus | $0.015 | $0.075 |
| Claude Sonnet | $0.003 | $0.015 |
| GPT-4o | $0.005 | $0.015 |
| GPT-4o-mini | $0.00015 | $0.0006 |
| Gemini-Pro | $0.00125 | $0.005 |

---

### 2.4 Cascade Engine

**Responsibility:** Execute model calls in chain order. Handle API errors, timeouts, and rate limits. Coordinate with ConfidenceScorer and CostTracker. Enforce latency budget.

**Public API:**
```python
class CascadeEngine:
    def __init__(
        self,
        health_tracker: HealthTracker,
        cost_tracker: CostTracker,
        confidence_scorer: ConfidenceScorer
    ):
        ...

    async def execute_chain(
        self,
        prompt: str,
        config: CascadeConfig
    ) -> CascadeResult:
        """
        Execute cascade chain: try models in order until success.
        Returns CascadeResult on success or cascade exhaustion.
        """

    async def call_model(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_ms: int
    ) -> ModelCallResult:
        """
        Make a single model API call.
        Handles HTTP errors, timeouts, rate limits.
        """
```

**ModelCallResult:**
```python
@dataclass
class ModelCallResult:
    success: bool
    response: Optional[str] = None
    error_type: Optional[str] = None       # "api_error", "timeout", "rate_limit", "server_error"
    http_status: Optional[int] = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    raw_error: Optional[str] = None
```

**Cascade Trigger Evaluation:**
```python
def _should_escalate(
    self,
    result: ModelCallResult,
    confidence: float,
    config: CascadeConfig,
    remaining_budget_ms: int,
    remaining_budget_usd: float
) -> Tuple[bool, str]:
    """
    Returns (should_escalate, reason).
    Escalate if: error occurred OR confidence < threshold
                 OR remaining budget insufficient.
    """
    # Error triggers
    if not result.success:
        if result.error_type == "rate_limit":
            return True, "rate_limit"
        elif result.error_type == "timeout":
            return True, "timeout"
        elif result.http_status is not None:
            if 500 <= result.http_status < 600:
                return True, "server_error"
            elif result.http_status == 429:
                return True, "rate_limit"
            else:
                return True, f"api_error_{result.http_status}"
        else:
            return True, "unknown_error"

    # Confidence trigger
    if confidence < config.confidence_threshold:
        return True, f"low_confidence_{confidence:.2f}"

    # Latency budget trigger
    if result.latency_ms > remaining_budget_ms:
        return True, "latency_budget_exceeded"

    # Cost budget trigger
    estimated_cost = self._estimate_call_cost(result)
    if estimated_cost > remaining_budget_usd:
        return True, "cost_budget_exceeded"

    return False, ""
```

**Interactions:**
- Calls model provider APIs (Claude, OpenAI, Gemini)
- Records results to HealthTracker
- Records costs to CostTracker
- Scores response with ConfidenceScorer

---

### 2.5 Confidence Scorer

**Responsibility:** Compute a normalized confidence score (0.0–1.0) on model output. Used to detect low-quality or malformed responses and trigger escalation.

**Scoring Dimensions:**
| Dimension | Signal | Weight |
|-----------|--------|--------|
| **Token Entropy** | High entropy (random-looking text) → low confidence | 0.30 |
| **Repetition Ratio** | High repetition (stuck in loop) → low confidence | 0.25 |
| **Length Sanity** | Output too short/long for task type → low confidence | 0.20 |
| **Parse Validity** | JSON/markdown/code malformed → low confidence | 0.25 |

**Public API:**
```python
class ConfidenceScorer:
    def score(self, output: str, task_type: str = "general") -> float:
        """
        Compute confidence score 0.0–1.0.
        Higher = more confident the output is high quality.
        """
```

**Scoring Algorithm:**
```python
def score(self, output: str, task_type: str = "general") -> float:
    entropy_score = self._entropy_score(output)      # 0–1
    repetition_score = self._repetition_score(output)  # 0–1
    length_score = self._length_score(output, task_type)  # 0–1
    parse_score = self._parse_validity_score(output)  # 0–1

    weighted = (
        entropy_score * 0.30 +
        repetition_score * 0.25 +
        length_score * 0.20 +
        parse_score * 0.25
    )
    return round(weighted, 3)
```

**Scoring Detail:**

```python
def _entropy_score(self, output: str) -> float:
    """Token-level entropy. High entropy = more uncertain."""
    if not output.strip():
        return 0.0
    tokens = output.split()
    if len(tokens) < 2:
        return 0.5
    freq = Counter(tokens)
    probs = [count / len(tokens) for count in freq.values()]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    # Normalize: max entropy for vocab size V is log2(V)
    max_entropy = math.log2(len(freq) + 1)
    normalized = min(entropy / max_entropy, 1.0) if max_entropy > 0 else 0.0
    # Invert: high entropy → low confidence
    return 1.0 - normalized

def _repetition_score(self, output: str) -> float:
    """
    Detect repetition loops.
    Find longest substring repeated >= 3 times.
    """
    if len(output) < 50:
        return 1.0
    # Sliding window: count repeated n-grams
    for n in range(3, min(10, len(output) // 5)):
        ngrams = [output[i:i+n] for i in range(len(output) - n + 1)]
        ngram_counts = Counter(ngrams)
        repeated = sum(1 for c in ngram_counts.values() if c >= 3)
        repetition_ratio = repeated / len(ngram_counts) if ngram_counts else 0
        if repetition_ratio > 0.3:
            return max(0.0, 1.0 - repetition_ratio * 2)
    return 1.0

def _length_score(self, output: str, task_type: str) -> float:
    """Length sanity check based on task type."""
    length = len(output)
    if task_type == "general":
        # Very short responses may be truncated or refused
        if length < 20:
            return 0.2
        if length < 100:
            return 0.6
        if length > 50000:
            return 0.5  # suspiciously long
        return 1.0
    elif task_type == "code":
        if length < 10:
            return 0.1
        if "```" in output and output.count("```") < 2:
            return 0.5  # unclosed code block
        return 1.0
    elif task_type == "json":
        try:
            json.loads(output)
            return 1.0
        except Exception:
            return 0.1
    return 1.0

def _parse_validity_score(self, output: str) -> float:
    """Check structural validity of structured outputs."""
    # JSON validity
    if output.strip().startswith("{"):
        try:
            json.loads(output)
            return 1.0
        except Exception:
            return 0.0
    # Markdown code blocks
    if "```" in output:
        if output.count("```") % 2 != 0:
            return 0.3  # unclosed code block
        if output.count("```") >= 2:
            return 0.9  # well-formed code block(s)
    # XML-like structures
    if output.strip().startswith("<"):
        if "</" not in output and "/>" not in output:
            return 0.2
    return 0.8  # default moderate confidence for unstructured text
```

---

## 3. State Machine

### 3.1 Cascade States

```
  ┌───────┐
  │ IDLE  │◀─────────────────────────────────────────┐
  └───────┘                                          │
      │ start_request()                              │
      ▼                                              │
  ┌───────────┐     ┌─────────────┐   success       │
  │ ROUTING   │────▶│ MODEL_CALL  │──────────────┐  │
  └───────────┘     └──────┬──────┘              │  │
                           │                     │  │
      ┌─────────────────────┼─────────────────────┼──┘
      │                     │                     │
      ▼                     ▼                     ▼
  ┌──────────────────┐  ┌────────────────┐  ┌──────────────┐
  │  CASCADE_CHECK   │  │  CASCADE_CHECK │  │CASCADE_CHECK  │
  │  (escalate)      │  │  (return OK)   │  │(return error)│
  └────────┬─────────┘  └────────────────┘  └──────┬──────┘
           │                                       │
           │ next model in chain                   │
           │ available?                            │
           ├──── yes ───────┐                       │
           │                │ no                    │
           ▼                ▼                       ▼
      [ROUTING]         ┌───────────┐          ┌───────────┐
      (next model)      │ EXHAUSTED │          │ EXHAUSTED │
                       └───────────┘          └───────────┘
```

### 3.2 State Definitions

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| **IDLE** | No active request; monitoring provider health, idle cost tracking | → ROUTING (on new request) |
| **ROUTING** | Selecting next model from chain based on health/cost/priority | → MODEL_CALL (model selected), → EXHAUSTED (no models left) |
| **MODEL_CALL** | Active HTTP call to selected model provider | → CASCADE_CHECK (call returns) |
| **CASCADE_CHECK** | Evaluating success/failure/confidence/latency/cost | → MODEL_CALL (escalate), → IDLE/EXHAUSTED (finalize) |
| **EXHAUSTED** | All models tried; preparing error response | → IDLE (after response returned) |

### 3.3 State Variables

```python
class CascadeState:
    state: CascadeStateEnum  # IDLE, ROUTING, MODEL_CALL, CASCADE_CHECK, EXHAUSTED
    current_depth: int = 0       # Index in chain (0 = primary)
    attempt_history: List[AttemptRecord] = []
    total_latency_ms: int = 0
    total_cost_usd: float = 0.0
    best_response: Optional[str] = None
    best_confidence: float = 0.0
    error: Optional[str] = None
```

---

## 4. Data Models

### 4.1 Enums

```python
class CascadeStateEnum(Enum):
    IDLE = auto()
    ROUTING = auto()
    MODEL_CALL = auto()
    CASCADE_CHECK = auto()
    EXHAUSTED = auto()

class CascadeErrorType(Enum):
    ALL_MODELS_FAILED = auto()
    ALL_MODELS_LOW_CONFIDENCE = auto()
    LATENCY_BUDGET_EXCEEDED = auto()
    COST_BUDGET_EXCEEDED = auto()
    NO_MODELS_AVAILABLE = auto()

class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    CUSTOM = "custom"
```

### 4.2 CascadeConfig

```python
@dataclass
class CascadeConfig:
    chain: List[ModelConfig]           # Ordered model list
    latency_budget_ms: int = 10000     # Max total cascade time
    cost_cap_usd: float = 0.50         # Max cost per request
    confidence_threshold: float = 0.7  # Min acceptable confidence
    timeout_per_call_ms: int = 5000    # Max wait per model call
    rate_limit_cooldown_seconds: float = 60.0

    def validate(self) -> None:
        """Validate configuration."""
        if not self.chain:
            raise ValueError("cascade chain cannot be empty")
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            raise ValueError("confidence_threshold must be 0-1")
        if self.cost_cap_usd <= 0:
            raise ValueError("cost_cap_usd must be positive")
```

### 4.3 ModelConfig

```python
@dataclass
class ModelConfig:
    provider: ModelProvider
    model_name: str                    # e.g., "claude-opus-4", "gpt-4o"
    api_key_ref: str = "env"           # Reference to key storage (env var name or vault path)
    endpoint: Optional[str] = None      # Override endpoint URL
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_input: float = 0.0     # Override default pricing
    cost_per_1k_output: float = 0.0
    priority: int = 1                  # 1 = highest (primary), 2 = secondary, etc.
```

**Default Cascade Chain:**
```
Claude Opus (priority=1) → Claude Sonnet (priority=2) → GPT-4o (priority=3) → GPT-4o-mini (priority=4) → Gemini-Pro (priority=5)
```

### 4.4 CascadeResult

```python
@dataclass
class CascadeResult:
    response: Optional[str]            # Final response text (None if exhausted)
    model_used: Optional[str]           # Model name that produced response
    cascade_depth: int                  # Index in chain that succeeded (0 = primary)
    total_cost_usd: float
    latency_ms: int
    confidence: float                   # Confidence of returned response
    attempt_history: List[AttemptRecord]
    error: Optional[str] = None         # Error message if cascade exhausted
    cascade_failure: bool = False       # True if all models failed
    cascade_exhausted: bool = False     # True if chain fully attempted

    @property
    def success(self) -> bool:
        return not self.cascade_failure and self.response is not None
```

### 4.5 AttemptRecord

```python
@dataclass
class AttemptRecord:
    model_name: str
    provider: str
    latency_ms: int
    success: bool
    error_type: Optional[str] = None
    http_status: Optional[int] = None
    confidence: Optional[float] = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    escalated_reason: Optional[str] = None  # Why escalated to next model
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

### 4.6 ProviderHealth

```python
@dataclass
class ProviderHealth:
    provider: str
    success_rate: float                # Rolling 24h success rate (0.0-1.0)
    median_latency_ms: int             # Rolling median latency
    error_types: Dict[str, int]        # Count by error type
    rate_limit_count: int              # 429s in rolling window
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_in_cooldown: bool = False        # Currently in rate-limit cooldown
    cooldown_ends_at: Optional[datetime] = None
```

### 4.7 AttemptCost

```python
@dataclass
class AttemptCost:
    model_name: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

### 4.8 ModelPricing

```python
@dataclass
class ModelPricing:
    provider: str
    model_name: str
    cost_per_1k_input: float
    cost_per_1k_output: float
```

---

## 5. Cascade Flow (Step-by-Step)

### 5.1 Main Cascade Algorithm

```python
async def route(self, prompt: str, config: CascadeConfig) -> CascadeResult:
    """
    Main cascade routing algorithm.
    """
    self.cost_tracker.reset()
    state = CascadeState(state=CascadeStateEnum.ROUTING)
    start_time = datetime.now(timezone.utc)
    attempt_history: List[AttemptRecord] = []

    for depth, model in enumerate(config.chain):
        # ── Step 1: ROUTING ─────────────────────────────────────────
        state.state = CascadeStateEnum.ROUTING
        state.current_depth = depth

        # Check health
        health = self.health_tracker.get_health(model.provider.value)
        if not self.health_tracker.is_healthy(model.provider.value):
            record = AttemptRecord(
                model_name=model.model_name,
                provider=model.provider.value,
                latency_ms=0,
                success=False,
                error_type="provider_unhealthy",
                escalated_reason=f"provider health={health.success_rate:.2f}"
            )
            attempt_history.append(record)
            continue  # skip to next model

        # Check cost budget
        remaining_cost = config.cost_cap_usd - self.cost_tracker.get_total_cost()
        if remaining_cost <= 0:
            state.state = CascadeStateEnum.EXHAUSTED
            return self._build_exhausted_result(
                attempt_history, start_time, config,
                error=f"cost_cap_exceeded: {config.cost_cap_usd} USD"
            )

        # ── Step 2: MODEL_CALL ──────────────────────────────────────
        state.state = CascadeStateEnum.MODEL_CALL
        remaining_budget_ms = config.latency_budget_ms - state.total_latency_ms
        timeout = min(config.timeout_per_call_ms, remaining_budget_ms)

        call_result = await self.cascade_engine.call_model(
            model, prompt, timeout_ms=timeout
        )

        # Record cost
        call_cost = self.cost_tracker.add_cost(
            provider=model.provider.value,
            model=model.model_name,
            input_tokens=call_result.input_tokens,
            output_tokens=call_result.output_tokens,
            cost_per_1k_input=model.cost_per_1k_input,
            cost_per_1k_output=model.cost_per_1k_output
        )

        # Record health
        self.health_tracker.record_result(
            provider=model.provider.value,
            latency_ms=call_result.latency_ms,
            success=call_result.success,
            error_type=call_result.error_type,
            is_rate_limit=(call_result.error_type == "rate_limit")
        )

        elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

        # ── Step 3: CASCADE_CHECK ───────────────────────────────────
        state.state = CascadeStateEnum.CASCADE_CHECK
        state.total_latency_ms = elapsed_ms
        state.total_cost_usd = self.cost_tracker.get_total_cost()

        if call_result.success and call_result.response:
            confidence = self.confidence_scorer.score(call_result.response)
        else:
            confidence = 0.0

        should_escalate, escalate_reason = self.cascade_engine._should_escalate(
            call_result, confidence, config,
            remaining_budget_ms=remaining_budget_ms,
            remaining_budget_usd=remaining_cost
        )

        record = AttemptRecord(
            model_name=model.model_name,
            provider=model.provider.value,
            latency_ms=call_result.latency_ms,
            success=call_result.success,
            error_type=call_result.error_type,
            http_status=call_result.http_status,
            confidence=confidence,
            cost_usd=call_cost,
            escalated_reason=escalate_reason if should_escalate else None
        )
        attempt_history.append(record)

        # ── Decision: escalate or return ───────────────────────────
        if not should_escalate:
            # Success with acceptable confidence
            return CascadeResult(
                response=call_result.response,
                model_used=model.model_name,
                cascade_depth=depth,
                total_cost_usd=state.total_cost_usd,
                latency_ms=elapsed_ms,
                confidence=confidence,
                attempt_history=attempt_history,
                cascade_failure=False,
                cascade_exhausted=False
            )

        # Track best response so far (in case all fail)
        if call_result.success and call_result.response:
            if confidence > state.best_confidence:
                state.best_response = call_result.response
                state.best_confidence = confidence

        # Check if latency budget already exceeded
        if elapsed_ms >= config.latency_budget_ms:
            if state.best_response:
                return CascadeResult(
                    response=state.best_response,
                    model_used=attempt_history[0].model_name,  # first successful
                    cascade_depth=depth,
                    total_cost_usd=state.total_cost_usd,
                    latency_ms=elapsed_ms,
                    confidence=state.best_confidence,
                    attempt_history=attempt_history,
                    cascade_failure=False,
                    cascade_exhausted=True
                )
            else:
                return self._build_exhausted_result(
                    attempt_history, start_time, config,
                    error="latency_budget_exceeded"
                )

    # ── All models exhausted ────────────────────────────────────────
    state.state = CascadeStateEnum.EXHAUSTED
    return self._build_exhausted_result(
        attempt_history, start_time, config,
        error="all_models_exhausted"
    )
```

### 5.2 Rate Limit Handling

```python
async def call_model(self, model: ModelConfig, prompt: str, timeout_ms: int) -> ModelCallResult:
    try:
        response = await self._http_call(
            model=model,
            prompt=prompt,
            timeout=timeout_ms / 1000
        )
        return response
    except RateLimitError as e:
        # Immediately mark provider for cooldown
        self.health_tracker.record_result(
            provider=model.provider.value,
            latency_ms=e.latency_ms,
            success=False,
            error_type="rate_limit",
            is_rate_limit=True
        )
        return ModelCallResult(
            success=False,
            error_type="rate_limit",
            http_status=429,
            latency_ms=e.latency_ms
        )
```

### 5.3 Latency Budget Enforcement

```python
def _check_latency_budget(self, config: CascadeConfig, state: CascadeState) -> bool:
    """
    Returns True if within budget and more calls are allowed.
    """
    if state.total_latency_ms >= config.latency_budget_ms:
        return False
    return True
```

---

## 6. API Design

### 6.1 LLM Cascade Facade (Main Class)

```python
class LLMCascade:
    """
    Main LLM Cascade facade.
    Provides unified interface for multi-model routing with fallback.
    """

    def __init__(
        self,
        config: Optional[CascadeConfig] = None,
        health_tracker: Optional[HealthTracker] = None,
        cost_tracker: Optional[CostTracker] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
        api_clients: Optional[Dict[ModelProvider, APIClient]] = None
    ):
        self.config = config or self._default_config()
        self.health_tracker = health_tracker or HealthTracker()
        self.cost_tracker = cost_tracker or CostTracker()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.cascade_engine = CascadeEngine(
            self.health_tracker,
            self.cost_tracker,
            self.confidence_scorer
        )
        self.router = CascadeRouter    # ─────────────────────────────────────────────────────────────────
    # Core Routing
    # ─────────────────────────────────────────────────────────────────

    async def route(
        self,
        prompt: str,
        config: Optional[CascadeConfig] = None
    ) -> CascadeResult:
        """
        Route a prompt through the cascade chain.
        Returns CascadeResult on success or cascade exhaustion.
        """

    async def route_with_fallback(
        self,
        prompt: str,
        task_type: str,
        fallback_chain: Optional[List[ModelConfig]] = None
    ) -> CascadeResult:
        """
        Convenience method: route with a task-type-specific chain override.
        """

    # ─────────────────────────────────────────────────────────────────
    # Health & Metrics
    # ─────────────────────────────────────────────────────────────────

    def get_provider_health(self, provider: str) -> ProviderHealth:
        """Get health metrics for a provider."""

    def get_all_provider_health(self) -> Dict[str, ProviderHealth]:
        """Get health metrics for all providers."""

    def get_cascade_stats(self) -> CascadeStats:
        """Get aggregate cascade statistics."""

    # ─────────────────────────────────────────────────────────────────
    # Configuration
    # ─────────────────────────────────────────────────────────────────

    def update_config(self, config: CascadeConfig) -> None:
        """Update active cascade configuration."""

    def get_config(self) -> CascadeConfig:
        """Get current cascade configuration."""

    def add_model_to_chain(
        self,
        model: ModelConfig,
        position: Optional[int] = None
    ) -> None:
        """Add a model to the cascade chain (default: append at end)."""

    def remove_model_from_chain(self, model_name: str) -> None:
        """Remove a model from the cascade chain."""

    # ─────────────────────────────────────────────────────────────────
    # Cost Management
    # ─────────────────────────────────────────────────────────────────

    def get_request_cost(self) -> float:
        """Get total cost for the last cascade request."""

    def get_cost_breakdown(self) -> List[AttemptCost]:
        """Get per-attempt cost breakdown for last request."""

    def reset_cost_tracking(self) -> None:
        """Reset cost tracking counters."""
```

### 6.2 CascadeStats

```python
@dataclass
class CascadeStats:
    total_requests: int
    successful_requests: int
    cascade_hit_count: int            # Requests that used fallback
    cascade_hit_rate: float            # cascade_hit_count / total_requests
    average_cascade_depth: float       # Mean models tried per request
    average_latency_ms: int
    average_cost_usd: float
    total_cost_usd: float
    provider_usage: Dict[str, int]    # Model → request count
    provider_success_rate: Dict[str, float]
    cost_reduction_vs_baseline_pct: float
```

### 6.3 Configuration API

```python
@dataclass
class LLMCascadeConfig:
    """Global LLM Cascade configuration."""

    default_chain: List[ModelConfig]
    default_latency_budget_ms: int = 10000
    default_cost_cap_usd: float = 0.50
    default_confidence_threshold: float = 0.7
    default_timeout_per_call_ms: int = 5000
    health_window_seconds: int = 86400     # 24h rolling
    rate_limit_cooldown_seconds: float = 60.0
    min_provider_success_rate: float = 0.8  # Skip providers below this
    enable_request_isolation: bool = True  # Per-request state isolation
```

---

## 7. Cascade State Definitions

### 7.1 State Summary

| State | Description | Entry Condition | Exit Condition |
|-------|-------------|------------------|----------------|
| **IDLE** | No active request; monitoring provider health | After `route()` completes or before any request | `route()` called |
| **ROUTING** | Selecting next model from chain | Model needed | Model selected or no models left |
| **MODEL_CALL** | Active HTTP call to selected model | Model selected | Response received or timeout/error |
| **CASCADE_CHECK** | Evaluating response quality and budget | Model call returns | Escalate, return, or exhaust |
| **EXHAUSTED** | All models tried; preparing error response | Chain fully traversed | Result returned to caller |

### 7.2 State Transition Table

| Current State | Trigger | Next State | Action |
|--------------|---------|-----------|--------|
| IDLE | `route()` called | ROUTING | Initialize state |
| ROUTING | Model selected, healthy | MODEL_CALL | Execute API call |
| ROUTING | No healthy models | EXHAUSTED | Build error result |
| MODEL_CALL | Call returns success | CASCADE_CHECK | Score confidence |
| MODEL_CALL | Call returns error | CASCADE_CHECK | Record error |
| CASCADE_CHECK | Confidence >= threshold | IDLE | Return success result |
| CASCADE_CHECK | Confidence < threshold | ROUTING | Record, try next model |
| CASCADE_CHECK | Error detected | ROUTING | Record, try next model |
| CASCADE_CHECK | Latency budget exceeded | IDLE or EXHAUSTED | Return best or error |
| CASCADE_CHECK | Cost budget exceeded | EXHAUSTED | Return cheapest valid or error |
| CASCADE_CHECK | No more models | EXHAUSTED | Build error result |

---

## 8. File Structure

### 8.1 Directory Layout

```
implement/llm_cascade/
├── __init__.py
├── enums.py                  # CascadeStateEnum, CascadeErrorType, ModelProvider
├── models.py                 # All dataclass models
├── exceptions.py             # Custom exceptions
├── health_tracker.py         # HealthTracker component
├── cost_tracker.py           # CostTracker component
├── cascade_engine.py         # CascadeEngine component
├── confidence_scorer.py      # ConfidenceScorer component
├── cascade_router.py         # CascadeRouter facade
├── api_clients/
│   ├── __init__.py
│   ├── base.py               # Abstract APIClient
│   ├── anthropic.py          # Claude API client
│   ├── openai.py             # OpenAI API client
│   └── google.py             # Gemini API client
└── llm_cascade.py            # Main LLMCascade facade

test/llm_cascade/
├── __init__.py
├── test_health_tracker.py
├── test_cost_tracker.py
├── test_confidence_scorer.py
├── test_cascade_engine.py
├── test_cascade_router.py
├── test_llm_cascade.py
└── test_integration.py

config/
└── llm_cascade_config.yaml   # Default chain, thresholds, pricing
```

### 8.2 Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `enums.py` | Type definitions | `CascadeStateEnum`, `CascadeErrorType`, `ModelProvider` |
| `models.py` | Data structures | `CascadeConfig`, `CascadeResult`, `ProviderHealth`, `ModelConfig`, `AttemptRecord` |
| `exceptions.py` | Error types | `CascadeError`, `AllModelsExhaustedError`, `CostBudgetExceededError` |
| `health_tracker.py` | Provider health tracking | `HealthTracker` |
| `cost_tracker.py` | Cost accounting | `CostTracker` |
| `cascade_engine.py` | Model call execution | `CascadeEngine`, `ModelCallResult` |
| `confidence_scorer.py` | Output quality scoring | `ConfidenceScorer` |
| `cascade_router.py` | Routing orchestration | `CascadeRouter` |
| `llm_cascade.py` | Facade | `LLMCascade` |
| `api_clients/base.py` | Provider API abstraction | `APIClient` |
| `api_clients/anthropic.py` | Claude API | `AnthropicAPIClient` |
| `api_clients/openai.py` | OpenAI API | `OpenAIAPIClient` |
| `api_clients/google.py` | Gemini API | `GoogleAPIClient` |

### 8.3 Test Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| HealthTracker | ≥ 85% |
| CostTracker | ≥ 90% |
| ConfidenceScorer | ≥ 85% |
| CascadeEngine | ≥ 85% |
| CascadeRouter | ≥ 80% |
| LLMCascade (facade) | ≥ 85% |
| **Overall** | **≥ 85%** |

---

## 9. Dependencies & Interfaces

### 9.1 External Dependencies

| Layer | Component | Interface | Purpose |
|-------|-----------|-----------|---------|
| Feature #1 | MCP/SAIF | v3/mcp-saif | Identity propagation for model call attribution |
| Feature #2 | Prompt Shields | v3/prompt-shields | Input validation before cascade; output validation after |
| Feature #3 | Tiered Governance | v3/tiered-governance | Governance triggers on cascade policy concerns |
| Core | Configuration Store | `config/llm_cascade_config.yaml` | Cascade chains, thresholds, pricing per task type |
| Core | Metrics Infrastructure | Observability layer | Expose provider health, cascade stats |
| External | Anthropic API | `https://api.anthropic.com` | Claude model calls |
| External | OpenAI API | `https://api.openai.com` | GPT model calls |
| External | Google AI API | `https://generativelanguage.googleapis.com` | Gemini model calls |

### 9.2 Interfaces Provided to Other Components

| Interface | Methods | Consumers |
|-----------|---------|-----------|
| LLMCascade | `route()` | All layers |
| LLMCascade | `get_provider_health()`, `get_cascade_stats()` | Dashboard, observability |
| HealthTracker | `is_healthy()`, `record_result()` | CascadeRouter, external monitoring |
| CostTracker | `add_cost()`, `is_within_budget()` | CascadeRouter, billing |
| ConfidenceScorer | `score()` | CascadeEngine |

---

## 10. Edge Cases & Error Handling

### 10.1 All Models Fail Simultaneously

**Scenario:** All providers return errors (e.g., internet outage, all APIs down).

**Handling:**
```python
# Cascade exhausts all models → EXHAUSTED state
return CascadeResult(
    response=None,
    model_used=None,
    cascade_depth=-1,
    total_cost_usd=total_cost,
    latency_ms=elapsed_ms,
    confidence=0.0,
    attempt_history=attempt_history,
    error="all_models_failed",
    cascade_failure=True,
    cascade_exhausted=True
)
```

### 10.2 Confidence Threshold Impossible to Meet

**Scenario:** All models return low confidence (< threshold), but no explicit errors.

**Handling:** Treat as cascade exhaustion with `low_confidence_all_models` error. Return best response with warning flag.

### 10.3 Rate Limit Mid-Cascade

**Scenario:** Model #2 returns 429, cooldown = 60s.

**Handling:**
```python
# HealthTracker records rate_limit and starts cooldown
self.health_tracker.record_result(
    provider=model.provider.value,
    latency_ms=call_result.latency_ms,
    success=False,
    error_type="rate_limit",
    is_rate_limit=True
)
# Router skips this provider for next attempts within cooldown window
# Escalate to Model #3 immediately
```

### 10.4 Concurrent Requests Competing for Same Provider

**Scenario:** Request A and Request B both route to same provider simultaneously.

**Handling:** Request-level isolation ensures no shared state mutation per cascade. HealthTracker uses thread-safe data structures (locks per provider). Concurrent requests see consistent provider health snapshots.

### 10.5 Token Counting Disagreement

**Scenario:** Our token count differs from provider's billing.

**Handling:** Use provider-reported `usage` field from API response for cost calculation. If provider doesn't report usage, estimate using `len(prompt) // 4` for input and `len(response) // 4` for output. Flag discrepancy in logs.

### 10.6 Malformed JSON from Model

**Scenario:** Model returns invalid JSON when task_type = "json".

**Handling:**
```python
if task_type == "json":
    try:
        parsed = json.loads(output)
        parse_score = 1.0
    except json.JSONDecodeError:
        parse_score = 0.0
        confidence = 0.0  # triggers escalation
```

### 10.7 Latency Budget Exactly Exceeded

**Scenario:** Latency budget = 10000ms, current elapsed = 10001ms after a successful call.

**Handling:** Return the successful response obtained (don't discard). The latency budget is a soft limit — we return the best available response rather than erroring unnecessarily.

### 10.8 Empty Response from Model

**Scenario:** Model returns empty string or whitespace-only response.

**Handling:**
```python
if not output.strip():
    confidence = 0.0  # triggers escalation
    score("")  # entropy=0, repetition=0, length=0 → very low confidence
```

### 10.9 Cascade Chain Empty (Misconfiguration)

**Scenario:** `CascadeConfig.chain` is empty list.

**Handling:**
```python
def validate(self) -> None:
    if not self.chain:
        raise CascadeConfigurationError("cascade chain cannot be empty")
```

### 10.10 Partial Success (Some Models Fail, One Succeeds)

**Scenario:** Model #1 and #2 fail, Model #3 succeeds.

**Handling:** Return Model #3's response. `cascade_depth = 2` (0-indexed), `cascade_hit = True`, `attempt_history` records all 3 attempts. This is considered a **successful** cascade (not a failure).

---

## 11. Success Metrics & Validation

### 11.1 Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-End Success Rate | > 99.5% | (Successful responses / Total requests) |
| Cost Reduction | > 30% vs single premium | (Baseline - Actual) / Baseline |
| Cascade Hit Rate | 15-40% | Fallback usage ratio |
| Average Cascade Depth | 1.2-1.8 | Mean models tried per request |
| P99 Latency | < 10 seconds | 99th percentile total time |
| Confidence Accuracy | > 85% | Low confidence → actual quality issue correlation |
| Cost Attribution Error | < 1% | Logged cost vs provider billing variance |

### 11.2 Observability Signals

Each `CascadeResult` emitted as an event with:
- `cascade_depth` — which model succeeded
- `total_cost_usd` — per-request cost
- `confidence` — quality signal
- `attempt_history` — full per-model breakdown
- `cascade_hit` — whether fallback was used

---

## Appendix: FR Mapping

| FR-ID | Component | Implementation |
|-------|-----------|----------------|
| FR-LC-1: Cascade Router | CascadeRouter | `route()`, `select_model()` |
| FR-LC-2: Failure Mode Handling | CascadeEngine | `_should_escalate()` — API errors, timeout, 429, 5xx |
| FR-LC-3: Confidence-Based Escalation | ConfidenceScorer + CascadeEngine | `score()`, confidence threshold check |
| FR-LC-4: Configurable Cascade Chains | LLMCascade | `add_model_to_chain()`, `CascadeConfig.chain` |
| FR-LC-5: Latency Budget | CascadeEngine | `_check_latency_budget()`, remaining budget tracking |
| FR-LC-6: Cost Tracking | CostTracker | `add_cost()`, `get_total_cost()` |
| FR-LC-7: Provider Health Metrics | HealthTracker | `get_health()`, rolling success/latency windows |
| FR-LC-8: Rate Limit Detection | CascadeEngine + HealthTracker | 429 detection, cooldown enforcement |
| FR-LC-9: Confidence Scoring | ConfidenceScorer | `_entropy_score()`, `_repetition_score()`, `_length_score()`, `_parse_validity_score()` |
| FR-LC-10: Cascade Exhausted Handling | CascadeRouter | `_build_exhausted_result()`, all-models-failed error |
| FR-LC-11: Request-Level Isolation | LLMCascade | Per-request `cost_tracker.reset()`, isolated state |

---

*End of ARCHITECTURE.md — Feature #5: LLM Cascade (Multi-Model Routing)*
