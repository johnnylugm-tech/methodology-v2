# SPEC.md — Feature #7: UQLM + Activation Probes

**版本**: v1.0  
**日期**: 2026-04-19  
**Phase**: 1/8 — Requirements Specification  
**負責人**: Requirements Engineer (Sub-agent)  
**審查人**: Agent A (Main Agent)

---

## 1. Overview

### 1.1 Feature Name
**Layer 3: UQLM + Activation Probes** — Hallucination Detection Core Components

### 1.2 Purpose
提供多維度的 hallucination 偵測能力，整合 uncertainty quantification (UQLM)、activation probes (CLAP)、MetaQA drift detection 為統一的 uncertainty_score，作為 Planner 的 decision gate 輸入。

### 1.3 Scope

| Component | Description |
|-----------|-------------|
| **UQLM Ensemble** | 整合 semantic entropy, semantic density, self-consistency, token-level NLL |
| **CLAP Probe** | Contrastive Learning with Activation Probes，適用於 open-weight models |
| **TinyLoRA** | 輕量化 probe 实作，可在边缘设备运行 |
| **MetaQA Drift** | 偵測 model output distribution drift |
| **Gap Detection** | AST 分析偵測 implementation 問題（Base64/AES, test灌水, empty catch, secrets） |
| **Unified Score** | 合併 UQLM + CLAP + MetaQA 為 α·UQLM + β·CLAP + γ·MetaQA |
| **Confidence Calibration** | 校準 planner confidence 與實際結果 |

### 1.4 Position in v3.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      LAYER 0: Foundation                    │
├─────────────────────────────────────────────────────────────┤
│                      LAYER 1: Planner                        │
│              (generates tasks, routes to Layer 2)            │
├─────────────────────────────────────────────────────────────┤
│                  LAYER 2: LLM Cascade                       │
│         (GPT-4 / Claude / Gemini routing)                  │
├─────────────────────────────────────────────────────────────┤
│              LAYER 2.5: Hunter Agent                         │
│          (anomaly detection, self-correction)              │
├─────────────────────────────────────────────────────────────┤
│              LAYER 3: UQLM + Activation Probes  ← THIS      │
│   ┌──────────────────────────────────────────────────┐     │
│   │  UQLM Ensemble  │  CLAP Probe  │  MetaQA Drift   │     │
│   │  Gap Detection  │  Unified Score  │ Calibration │     │
│   └──────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│               LAYER 4: Output Verifier                       │
│              (quality gate, citation check)                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.5 Dependencies

| Dependency | Module | Purpose |
|------------|--------|---------|
| **Transformer Models** | `transformers` | Hidden states extraction, model loading |
| **scikit-learn** | `sklearn` | LogisticRegression probe |
| **AST Analysis** | `ast` (stdlib) | Gap detection |
| **NumPy** | `numpy` | Numerical operations |
| **PyTorch** | `torch` | TinyLoRA training |

---

## 2. Functional Requirements

### FR-U-1: UQLM Ensemble Scoring

#### Purpose
整合多個 uncertainty scorers 為單一 UAF (Uncertainty-Aware Framework) score。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | `str` | Yes | Input prompt to the model |
| `response` | `str` | Yes | Model response to evaluate |
| `n_samples` | `int` | No (default=5) | Number of samples for self-consistency |
| `model_name` | `str` | No | Model identifier (default=`gpt-3.5-turbo`) |
| `temperature` | `float` | No (default=0.7) | Sampling temperature |

#### Outputs
| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `uaf_score` | `float` | [0.0, 1.0] | Weighted ensemble score |
| `scorer_results` | `List[ScorerResult]` | — | Individual scorer outputs |
| `metadata` | `dict` | — | Computation metadata (latency, model_used) |

#### Scorers Configuration
| Scorer | Weight | Description |
|--------|--------|-------------|
| `semantic_entropy` | 0.4 | Semantic variation across samples |
| `semantic_density` | 0.3 | Concept density in response |
| `self_consistency` | 0.3 | Consistency of answers across samples |
| `token_nll` | — | Token-level negative log-likelihood (auxiliary) |

#### Behavior
1. Generate `n_samples` responses using sampling
2. Compute each scorer independently
3. Apply weights: `uaf_score = Σ(weight_i × score_i)`
4. Return normalized score [0.0, 1.0]

#### Edge Cases
- Empty response → return `1.0` (maximum uncertainty)
- Model API failure → raise `UQLMError`, log error, return `None`
- Network timeout → retry 2 times, then raise `UQLMError`

---

### FR-U-2: CLAP Activation Probe

#### Purpose
使用 activation probe 偵測 hallucination，適用於 open-weight models (Llama-3.3, Qwen-2.5)。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `hidden_states` | `np.ndarray` | Yes | Hidden states from target layer |
| `model_type` | `str` | Yes | Model identifier (`llama-3.3`, `qwen-2.5`, `gpt-4`) |
| `layer_idx` | `int` | No | Target attention layer (default=last) |

#### Outputs
| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `p_hallucinate` | `float` | [0.0, 1.0] | Probability of hallucination |
| `confidence` | `float` | [0.0, 1.0] | Prediction confidence |
| `layer_used` | `int` | — | Which layer was used for prediction |

#### Supported Models
| Model Type | Probe Type | Fallback |
|------------|------------|----------|
| `llama-3.3`, `qwen-2.5` | Activation Probe (LogisticRegression) | — |
| `gpt-4`, `claude-3` | logprobs + self-consistency | `FR-U-1` scorer |

#### Behavior
1. Extract hidden states from specified attention layer
2. Normalize states (L2 norm)
3. Apply trained probe: `p_hallucinate = probe.predict_proba(states)[:, 1]`
4. Return probability and confidence

#### Edge Cases
- Closed-source model → use fallback to logprobs
- Invalid `layer_idx` → use last layer
- Model not supported → raise `ProbeError`

---

### FR-U-3: TinyLoRA Lightweight Probes

#### Purpose
輕量化 LoRA-based probe 實作，可在邊緣設備運行。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `training_data` | `List[Tuple[np.ndarray, int]]` | Yes | (hidden_state, label) pairs |
| `hidden_dim` | `int` | Yes | Hidden state dimension |
| `rank` | `int` | No (default=4) | LoRA rank |
| `alpha` | `float` | No (default=8.0) | LoRA alpha scaling |
| `lr` | `float` | No (default=0.001) | Learning rate |

#### Outputs
| Output | Type | Description |
|--------|------|-------------|
| `probe_model` | `TinyLoRAModel` | Trained probe model |
| `training_loss` | `float` | Final training loss |
| `metrics` | `dict` | Accuracy, F1, AUC on training set |

#### Behavior
1. Initialize LoRA adapters (A ∈ R^{d×r}, B ∈ R^{r×d})
2. Train with MSE loss on binary labels
3. Return trained probe for inference

#### Edge Cases
- Insufficient training data (< 10 samples) → raise `DataInsufficientError`
- Training divergence → reduce lr, retry, raise if still fails

---

### FR-U-4: MetaQA Drift Detection

#### Purpose
偵測 model output distribution drift，識別 distribution shift。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_outputs` | `List[str]` | Yes | Current model outputs |
| `baseline_distribution` | `Dict[str, float]` | Yes | Baseline token distribution |
| `window_size` | `int` | No (default=100) | Sliding window for drift calc |

#### Outputs
| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `drift_score` | `float` | [0.0, 1.0] | Distribution drift magnitude |
| `drifted_tokens` | `List[str]` | — | Tokens with significant drift |
| `kl_divergence` | `float` | [0.0, ∞) | KL divergence from baseline |

#### Behavior
1. Compute current token distribution over `window_size` outputs
2. Calculate KL divergence: `KL(baseline || current)`
3. Normalize to [0.0, 1.0] using sigmoid scaling
4. Identify tokens with drift > 2σ from baseline

#### Edge Cases
- Empty `model_outputs` → return `0.0` drift
- Baseline not initialized → raise `BaselineNotFoundError`
- First run (no baseline) → initialize baseline, return `0.0`

---

### FR-U-5: Implementation Gap Detection

#### Purpose
偵測程式碼中的 implementation 問題，防止假性通過。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_code` | `str` | Yes | Source code to analyze |
| `file_path` | `str` | Yes | Path for error reporting |
| `gap_types` | `List[GapType]` | No (default=all) | Which gaps to detect |

#### Outputs
| Output | Type | Description |
|--------|------|-------------|
| `findings` | `List[GapFinding]` | List of detected gaps |
| `summary` | `dict` | Counts by gap type |

#### Gap Types

| GapType | Detection Method | Severity |
|---------|------------------|----------|
| `BASE64_VS_AES` | AST analysis: look for mixed crypto usage | HIGH |
| `TEST_TODO_FLOOD` | Assertion count: detect test.todo() spam | MEDIUM |
| `EMPTY_CATCH` | AST analysis: empty except blocks | HIGH |
| `HARDCODED_SECRETS` | Rule scan: api_key, password, token patterns | CRITICAL |

#### Behavior
1. Parse source code with `ast`
2. For each gap type, run specialized detector
3. Return list of `GapFinding` with location, severity, description

#### Edge Cases
- Syntax errors in source → raise `SyntaxError`, skip file
- Empty source → return empty findings
- Binary file → skip with warning

---

### FR-U-6: Unified Uncertainty Score

#### Purpose
合併 UQLM + CLAP + MetaQA 為統一分數，作為 decision gate 輸入。

#### Inputs
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | `str` | Yes | — | Input prompt |
| `response` | `str` | Yes | — | Model response |
| `hidden_states` | `np.ndarray` | No | — | For CLAP probe |
| `model_name` | `str` | No | — | Model identifier |
| `α` | `float` | No | 0.5 | UQLM weight |
| `β` | `float` | No | 0.3 | CLAP weight |
| `γ` | `float` | No | 0.2 | MetaQA weight |

#### Outputs
| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `uncertainty_score` | `float` | [0.0, 1.0] | Combined uncertainty |
| `components` | `dict` | — | Individual scores |
| `decision` | `str` | — | `PASS`, `ROUND_2`, `HITL` |

#### Decision Thresholds
| Score Range | Decision | Action |
|-------------|----------|--------|
| < 0.2 | `PASS` | Proceed to next step |
| 0.2 – 0.5 | `ROUND_2` | Additional verification |
| > 0.5 | `HITL` | Human-in-the-loop review |

#### Formula
```
uncertainty_score = α × UQLM_ensemble + β × CLAP_probe + γ × MetaQA_drift

where:
  UQLM_ensemble = weighted sum of scorers (FR-U-1)
  CLAP_probe = p_hallucinate (FR-U-2, or fallback)
  MetaQA_drift = drift_score (FR-U-4)
```

#### Edge Cases
- Missing CLAP input → weight redistributes: α=0.6, β=0, γ=0.4
- Missing MetaQA → weight redistributes: α=0.65, β=0.35, γ=0
- All missing → raise `InsufficientDataError`

---

### FR-U-7: Confidence Calibration

#### Purpose
校準 planner confidence 與實際結果，確保 planner 的信心指數與實際準確率對齊。

#### Inputs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `initial_confidence` | `float` | Yes | Planner's stated confidence [0.0, 1.0] |
| `actual_outcome` | `bool` | Yes | True outcome (True=success, False=failure) |
| `uqlm_uncertainty` | `float` | Yes | UQLM uncertainty score [0.0, 1.0] |

#### Outputs
| Output | Type | Range | Description |
|--------|------|-------|-------------|
| `calibrated_confidence` | `float` | [0.0, 1.0] | Adjusted confidence |
| `calibration_error` | `float` | [0.0, 1.0] | |initial - actual| deviation |
| `alert` | `bool` | — | True if calibration_error > 0.3 |

#### Behavior
1. Compute expected accuracy from UQLM: `expected_acc = 1 - uqlm_uncertainty`
2. Apply Platt scaling: `calibrated = sigmoid(logit(initial) - logit(expected_acc))`
3. Compute error: `calibration_error = |calibrated - actual_outcome|`
4. Alert if `calibration_error > 0.3`

#### Edge Cases
- First calibration (no history) → return initial as calibrated
- Divergent history (> 100 samples) → slide window, forget old
- Invalid outcome → raise `ValueError`

---

## 3. Data Models

### 3.1 UQLM Ensemble Models

```python
@dataclass
class EnsembleConfig:
    """UQLM Ensemble configuration"""
    weights: List[float] = field(default_factory=lambda: [0.4, 0.3, 0.3])
    scorers: List[str] = field(default_factory=lambda: [
        "semantic_entropy", "semantic_density", "self_consistency"
    ])
    n_samples: int = 5
    temperature: float = 0.7
    model_name: str = "gpt-3.5-turbo"


@dataclass
class ScorerResult:
    """Individual scorer output"""
    scorer_name: str
    raw_score: float
    normalized_score: float  # [0.0, 1.0]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnsembleResult:
    """UQLM Ensemble result"""
    uaf_score: float  # [0.0, 1.0]
    scorer_results: List[ScorerResult]
    computation_time_ms: float
    model_used: str
    n_samples: int
```

### 3.2 CLAP Probe Models

```python
@dataclass
class ProbeConfig:
    """Activation probe configuration"""
    model_type: str  # "llama-3.3", "qwen-2.5", "gpt-4"
    layer_idx: int = -1  # -1 means last layer
    probe_type: str = "logistic_regression"  # or "linear", "mlp"
    threshold: float = 0.5


@dataclass
class ProbeResult:
    """Activation probe output"""
    p_hallucinate: float  # [0.0, 1.0]
    confidence: float  # [0.0, 1.0]
    layer_used: int
    model_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 3.3 TinyLoRA Models

```python
@dataclass
class TinyLoRAConfig:
    """TinyLoRA configuration"""
    hidden_dim: int
    rank: int = 4
    alpha: float = 8.0
    lr: float = 0.001
    dropout: float = 0.1
    max_iter: int = 1000


@dataclass
class TinyLoRAModel:
    """Trained TinyLoRA probe model"""
    config: TinyLoRAConfig
    state_dict: Dict[str, np.ndarray]
    training_loss: float
    metrics: Dict[str, float]  # accuracy, f1, auc
```

### 3.4 MetaQA Models

```python
@dataclass
class MetaQAResult:
    """MetaQA drift detection result"""
    drift_score: float  # [0.0, 1.0]
    drifted_tokens: List[str]
    kl_divergence: float
    window_size: int
    baseline_version: str


@dataclass
class DriftScore:
    """Drift score with timestamp"""
    score: float
    timestamp: datetime
    tokens: List[str]
    kl_div: float
```

### 3.5 Gap Detection Models

```python
class GapType(Enum):
    """Types of implementation gaps"""
    BASE64_VS_AES = "base64_vs_aes"
    TEST_TODO_FLOOD = "test_todo_flood"
    EMPTY_CATCH = "empty_catch"
    HARDCODED_SECRETS = "hardcoded_secrets"


@dataclass
class GapFinding:
    """Detected implementation gap"""
    gap_type: GapType
    file_path: str
    line_number: int
    severity: str  # "HIGH", "MEDIUM", "CRITICAL"
    description: str
    code_snippet: str = ""
    suggestion: str = ""


@dataclass
class GapSummary:
    """Summary of gap detection scan"""
    total_files: int
    total_findings: int
    by_type: Dict[GapType, int]
    by_severity: Dict[str, int]
    findings: List[GapFinding]
```

### 3.6 Unified Score Models

```python
@dataclass
class UncertaintyScore:
    """Unified uncertainty score"""
    score: float  # [0.0, 1.0]
    decision: str  # "PASS", "ROUND_2", "HITL"
    components: Dict[str, float]  # uqlm, clap, metaqa
    alpha: float
    beta: float
    gamma: float
    computation_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CalibrationResult:
    """Confidence calibration result"""
    initial_confidence: float
    calibrated_confidence: float
    actual_outcome: bool
    calibration_error: float
    alert: bool
    timestamp: datetime
```

---

## 4. API Design

### 4.1 uqlm_ensemble.py

```python
class EnsembleScorer:
    """UQLM Ensemble Scorer"""

    def __init__(self, config: Optional[EnsembleConfig] = None) -> None:
        """Initialize with optional config."""

    def add_scorer(self, name: str, scorer: BaseScorer) -> None:
        """Add a custom scorer to the ensemble."""

    def score(
        self,
        prompt: str,
        response: str,
        n_samples: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> EnsembleResult:
        """Compute UQLM ensemble score."""

    async def async_score(
        self,
        prompt: str,
        response: str,
        n_samples: int = 5,
    ) -> EnsembleResult:
        """Async version for batch processing."""
```

### 4.2 clap_probe.py

```python
class ActivationProbe:
    """CLAP Activation Probe"""

    def __init__(self, config: ProbeConfig) -> None:
        """Initialize with probe configuration."""

    def fit(self, training_data: List[Tuple[np.ndarray, int]]) -> ProbeResult:
        """Train the probe on labeled hidden states."""

    def predict(self, hidden_states: np.ndarray) -> ProbeResult:
        """Predict hallucination probability."""

    def save(self, path: str) -> None:
        """Save trained probe to disk."""

    @classmethod
    def load(cls, path: str) -> "ActivationProbe":
        """Load trained probe from disk."""
```

### 4.3 tinylora.py

```python
class TinyLoRA:
    """TinyLoRA Lightweight Probes"""

    def __init__(self, config: TinyLoRAConfig) -> None:
        """Initialize TinyLoRA with configuration."""

    def train(
        self,
        training_data: List[Tuple[np.ndarray, int]],
    ) -> Tuple[TinyLoRAModel, float]:
        """Train LoRA adapters on labeled data."""

    def infer(
        self,
        model: TinyLoRAModel,
        hidden_states: np.ndarray,
    ) -> float:
        """Run inference with trained LoRA probe."""

    def apply_lora(self, original_weights: np.ndarray, lora_a: np.ndarray, lora_b: np.ndarray) -> np.ndarray:
        """Apply LoRA adaptation: W + BA."""
```

### 4.4 metaqa.py (update existing)

```python
class MetaQADetector:
    """MetaQA Drift Detection"""

    def __init__(self, baseline: Optional[Dict[str, float]] = None) -> None:
        """Initialize with optional baseline distribution."""

    def update_baseline(self, model_outputs: List[str]) -> None:
        """Update baseline distribution from outputs."""

    def detect_drift(
        self,
        model_outputs: List[str],
        window_size: int = 100,
    ) -> MetaQAResult:
        """Detect drift from baseline distribution."""

    def get_drift_history(self) -> List[DriftScore]:
        """Return historical drift scores."""
```

### 4.5 gap_detector.py (update existing)

```python
class GapDetector:
    """Implementation Gap Detector"""

    def __init__(self, rules: Optional[List[GapRule]] = None) -> None:
        """Initialize with optional custom rules."""

    def scan(
        self,
        source_code: str,
        file_path: str,
        gap_types: Optional[List[GapType]] = None,
    ) -> List[GapFinding]:
        """Scan source code for implementation gaps."""

    def scan_directory(
        self,
        directory: str,
        patterns: List[str] = ["*.py"],
    ) -> GapSummary:
        """Scan entire directory recursively."""

    def get_findings(
        self,
        filter_severity: Optional[str] = None,
    ) -> List[GapFinding]:
        """Get findings with optional severity filter."""
```

### 4.6 uncertainty_score.py

```python
class UncertaintyScoreCalculator:
    """Unified Uncertainty Score Calculator"""

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2,
        ensemble_scorer: Optional[EnsembleScorer] = None,
        clap_probe: Optional[ActivationProbe] = None,
        metaqa_detector: Optional[MetaQADetector] = None,
    ) -> None:
        """Initialize with weights and component modules."""

    def compute(
        self,
        prompt: str,
        response: str,
        hidden_states: Optional[np.ndarray] = None,
        model_name: Optional[str] = None,
    ) -> UncertaintyScore:
        """Compute unified uncertainty score."""

    def set_weights(
        self,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
    ) -> None:
        """Update component weights."""
```

### 4.7 confidence_calibrator.py

```python
class ConfidenceCalibrator:
    """Confidence Calibration for Planner"""

    def __init__(self, history_size: int = 100) -> None:
        """Initialize with optional history size limit."""

    def calibrate(
        self,
        initial_confidence: float,
        actual_outcome: bool,
        uqlm_uncertainty: float,
    ) -> CalibrationResult:
        """Calibrate confidence based on actual outcome."""

    def get_calibration_error(self) -> float:
        """Get historical calibration error."""

    def reset_history(self) -> None:
        """Reset calibration history."""
```

---

## 5. Integration Points

### 5.1 Layer 2 (LLM Cascade) Interface

```
Input from Layer 2:
  - prompt: str
  - response: str
  - model_name: str
  - hidden_states: Optional[np.ndarray] (if open-weight model)

Output to Layer 2:
  - decision: "PASS" | "ROUND_2" | "HITL"
  - uncertainty_score: float
  - metadata: dict (computation details)
```

### 5.2 Layer 2.5 (Hunter Agent) Interface

```
Input from Hunter Agent:
  - model_outputs: List[str] (for MetaQA baseline update)
  - anomaly_detected: bool

Output to Hunter Agent:
  - uncertainty_context: Dict[str, float] (for anomaly interpretation)
  - gap_findings: List[GapFinding] (if code-related anomaly)
```

### 5.3 Layer 4 (Output Verifier) Interface

```
Input from Layer 4:
  - verification_result: bool

Output to Layer 4:
  - calibration_data: Tuple[float, bool, float] 
    (confidence, actual_outcome, uqlm_uncertainty)
```

---

## 6. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| UQLM ensemble AUC | ≥ 0.85 | ROC-AUC on hallucination benchmark |
| CLAP probe accuracy | ≥ 80% | 5-fold CV accuracy |
| Gap detection rate | ≥ 90% | Synthetic gap test suite |
| Latency per score | < 100ms | P50 latency on A100 |
| Coverage | 100% | All FRs have passing tests |

### 6.1 Test Coverage Requirements

| FR | Minimum Coverage |
|----|-----------------|
| FR-U-1 | 100% (UQLM ensemble) |
| FR-U-2 | 100% (CLAP probe) |
| FR-U-3 | 100% (TinyLoRA) |
| FR-U-4 | 100% (MetaQA drift) |
| FR-U-5 | 100% (Gap detection) |
| FR-U-6 | 100% (Unified score) |
| FR-U-7 | 100% (Calibration) |

---

## 7. File Structure

```
detection/
├── __init__.py                 # Module exports
├── uqlm_ensemble.py            # FR-U-1: UQLM Ensemble Scorer
├── clap_probe.py               # FR-U-2: Activation Probe
├── tinylora.py                 # FR-U-3: TinyLoRA Lightweight
├── metaqa.py                   # FR-U-4: MetaQA Drift Detection (update)
├── gap_detector.py             # FR-U-5: Implementation Gap Detection (update)
├── uncertainty_score.py        # FR-U-6: Unified Uncertainty Score
├── confidence_calibrator.py     # FR-U-7: Confidence Calibration
└── data_models.py              # Shared dataclasses
```

### 7.1 New Files to Create

| File | FR | Lines (est.) |
|------|----|--------------|
| `detection/__init__.py` | — | 50 |
| `detection/uqlm_ensemble.py` | FR-U-1 | 250 |
| `detection/clap_probe.py` | FR-U-2 | 200 |
| `detection/tinylora.py` | FR-U-3 | 150 |
| `detection/uncertainty_score.py` | FR-U-6 | 120 |
| `detection/confidence_calibrator.py` | FR-U-7 | 100 |
| `detection/data_models.py` | — | 200 |

### 7.2 Files to Update

| File | Changes |
|------|---------|
| `detection/metaqa.py` | Add `detect_drift()` method |
| `detection/gap_detector.py` | Add `scan_directory()` method |

---

## 8. Error Handling

### 8.1 Exception Hierarchy

```python
class UQLMError(Exception): pass
class ProbeError(Exception): pass
class DataInsufficientError(Exception): pass
class BaselineNotFoundError(Exception): pass
class CalibrationError(Exception): pass
class GapDetectionError(Exception): pass
```

### 8.2 Retry Policy

| Operation | Retry | Backoff |
|-----------|-------|---------|
| Model API call | 2 | 1.0s, 2.0s |
| File I/O | 3 | 0.1s |
| Network request | 2 | exponential |

---

## 9. Dependencies

```python
# requirements.txt
transformers>=4.36.0
torch>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
scipy>=1.11.0
```

---

## 10. Acceptance Criteria

### AC-U-1: UQLM Ensemble
- [ ] `EnsembleScorer.score()` returns `uaf_score` in [0.0, 1.0]
- [ ] Weights sum to 1.0
- [ ] Each scorer contributes independently

### AC-U-2: CLAP Probe
- [ ] Probe trained on 100+ samples achieves ≥80% accuracy
- [ ] `predict()` returns result in < 10ms
- [ ] Fallback to logprobs for closed-source models

### AC-U-3: TinyLoRA
- [ ] Model fits in < 1MB
- [ ] Training converges in < 100 iterations
- [ ] Accuracy on par with full Linear probe

### AC-U-4: MetaQA Drift
- [ ] `drift_score` increases when distribution shifts
- [ ] `drifted_tokens` identifies specific drifted tokens
- [ ] Baseline auto-initializes on first run

### AC-U-5: Gap Detection
- [ ] Detects all 4 gap types with ≥90% accuracy
- [ ] Returns file path and line number for each finding
- [ ] Handles syntax errors gracefully

### AC-U-6: Unified Score
- [ ] `uncertainty_score` correctly combines all 3 components
- [ ] Decision thresholds match spec
- [ ] Missing components trigger weight redistribution

### AC-U-7: Confidence Calibration
- [ ] Calibration error tracked over time
- [ ] Alert fires when error > 0.3
- [ ] Historical data slide window = 100

---

## 11. Appendix: Reference Implementations

### A. Semantic Entropy Calculation
```python
def semantic_entropy(logits: np.ndarray) -> float:
    """Compute semantic entropy from token logits."""
    probs = softmax(logits, axis=-1)
    entropy = -np.sum(probs * np.log(probs + 1e-10), axis=-1)
    return np.mean(entropy)
```

### B. LoRA Application
```python
def apply_lora(original: np.ndarray, lora_a: np.ndarray, lora_b: np.ndarray) -> np.ndarray:
    """Apply LoRA: W + BA where B is applied first."""
    return original + lora_b @ lora_a
```

### C. Platt Scaling
```python
def platt_scale(initial: float, expected: float) -> float:
    """Apply Platt scaling for calibration."""
    from scipy.special import expit, logit
    return expit(logit(initial) - logit(expected))
```

---

**END OF SPEC.md**
