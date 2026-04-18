# ARCHITECTURE.md — Feature #7: UQLM + Activation Probes

**版本**: v1.0  
**日期**: 2026-04-19  
**Phase**: 2/8 — Architecture Specification  
**負責人**: System Architect (Sub-agent)  
**審查人**: Agent A (Main Agent)

---

## Chapter 1: Architecture Overview

### 1.1 System Purpose and Scope

The UQLM + Activation Probes module provides multi-dimensional hallucination detection capability for Layer 3 of the methodology-v2 framework. Its purpose is to quantify uncertainty in LLM outputs by integrating:

- **UQLM Ensemble**: Combines semantic entropy, semantic density, self-consistency, and token-level NLL
- **CLAP Activation Probes**: Contrastive learning-based probes for open-weight models
- **TinyLoRA**: Lightweight LoRA-based probes for edge deployment
- **MetaQA Drift Detection**: Monitors model output distribution shifts
- **Implementation Gap Detection**: AST-based code quality analysis
- **Unified Uncertainty Score**: Weighted combination of all components
- **Confidence Calibration**: Platt scaling for planner confidence alignment

This module sits between Layer 2 (LLM Cascade) and Layer 4 (Output Verifier), acting as the decision gate that determines whether outputs proceed automatically or require human review.

### 1.2 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LAYER 3: UQLM + Activation Probes                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  UQLM Ensemble   │    │   CLAP Probe     │    │  MetaQA Drift    │      │
│  │  (FR-U-1)        │    │   (FR-U-2)       │    │  (FR-U-4)        │      │
│  │                  │    │                  │    │                  │      │
│  │  - Semantic Ent  │    │  - Logistic Reg  │    │  - KL Divergence │      │
│  │  - Semantic Dens │    │  - Layer Select  │    │  - Token Drift   │      │
│  │  - Self-Consist  │    │  - TinyLoRA Opt  │    │  - Baseline Mgmt │      │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘      │
│           │                      │                      │                 │
│           └──────────────────────┼──────────────────────┘                 │
│                                  │                                        │
│                    ┌─────────────▼─────────────┐                          │
│                    │  Unified Score Calculator │                          │
│                    │       (FR-U-6)            │                          │
│                    │                           │                          │
│                    │  score = α·UQLM           │                          │
│                    │         + β·CLAP          │                          │
│                    │         + γ·MetaQA        │                          │
│                    └─────────────┬─────────────┘                          │
│                                  │                                        │
│           ┌──────────────────────┼──────────────────────┐                 │
│           │                      │                      │                 │
│  ┌────────▼─────────┐    ┌───────▼───────┐    ┌────────▼────────┐         │
│  │ Gap Detector     │    │  Confidence   │    │   Decision      │         │
│  │ (FR-U-5)         │    │  Calibrator   │    │   Gate          │         │
│  │                  │    │  (FR-U-7)     │    │                 │         │
│  │  - AST Analysis  │    │               │    │  PASS / ROUND_2 │         │
│  │  - Secret Scan   │    │  - Platt Scal │    │     / HITL      │         │
│  └──────────────────┘    └───────────────┘    └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Layer 4        │
                    │  Output         │
                    │  Verifier       │
                    └─────────────────┘
```

### 1.3 Data Flow: Input to Uncertainty Score

```
Input (prompt, response, hidden_states, model_name)
    │
    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 1: UQLM Ensemble Scoring (FR-U-1)                                 │
│   ├─ Generate n_samples responses (temperature sampling)               │
│   ├─ Compute semantic_entropy, semantic_density, self_consistency      │
│   └─ Return: uqlm_score ∈ [0.0, 1.0]                                   │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
    ┌────────────────────────────┴────────────────────────────┐
    │ (Only if open-weight model + hidden_states available)   │
    ▼                                                        ▼
┌────────────────────────────┐                ┌────────────────────────────┐
│ STEP 2a: CLAP Probe        │                │ STEP 2b: TinyLoRA (edge)  │
│ (FR-U-2)                   │                │ (FR-U-3)                   │
│   ├─ Extract hidden_states │                │   ├─ LoRA A,B matrices    │
│   ├─ L2 normalize          │                │   ├─ apply: W + BA        │
│   └─ probe.predict_proba() │                │   └─ return p_hallucinate │
└────────────────────────────┘                └────────────────────────────┘
    │                                                        │
    └────────────────────────────┬───────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 3: MetaQA Drift Detection (FR-U-4)                               │
│   ├─ Compute current token distribution (window_size=100)              │
│   ├─ Calculate KL(baseline || current)                                │
│   └─ Return: drift_score ∈ [0.0, 1.0], drifted_tokens                 │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Unified Score Combination (FR-U-6)                             │
│                                                                        │
│   uncertainty_score = α × UQLM + β × CLAP + γ × MetaQA                │
│                                                                        │
│   Default weights: α=0.5, β=0.3, γ=0.2                                 │
│   Weight redistribution when components missing:                      │
│     - No CLAP → α=0.6, β=0.0, γ=0.4                                    │
│     - No MetaQA → α=0.65, β=0.35, γ=0.0                               │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Decision Gate                                                  │
│                                                                        │
│   if score < 0.2  → PASS (proceed automatically)                      │
│   if score < 0.5  → ROUND_2 (additional verification)                 │
│   if score >= 0.5 → HITL (human-in-the-loop)                         │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │ UncertaintyScore     │
                    │ {score, decision,    │
                    │  components, meta}    │
                    └───────────────────────┘
```

---

## Chapter 2: Component Specifications

### 2.1 uqlm_ensemble.py — FR-U-1: UQLM Ensemble Scorer

#### 2.1.1 Responsibility

The UQLM Ensemble Scorer integrates multiple uncertainty quantification methods into a single weighted score (UAF - Uncertainty-Aware Framework score). It generates multiple samples from the target model and evaluates semantic variation, concept density, answer consistency, and token-level negative log-likelihood to produce a comprehensive uncertainty measure.

#### 2.1.2 Public API

```python
class EnsembleScorer:
    """UQLM Ensemble Scorer — Combines multiple uncertainty scorers."""

    def __init__(self, config: Optional[EnsembleConfig] = None) -> None:
        """Initialize with optional config.
        
        Args:
            config: Optional EnsembleConfig with weights, scorers, n_samples.
                   If None, uses default configuration.
        """
        
    def add_scorer(self, name: str, scorer: "BaseScorer") -> None:
        """Add a custom scorer to the ensemble.
        
        Args:
            name: Scorer identifier (e.g., "semantic_entropy").
            scorer: BaseScorer implementation instance.
            
        Raises:
            ValueError: If scorer with name already exists.
        """
        
    def remove_scorer(self, name: str) -> None:
        """Remove a scorer from the ensemble.
        
        Args:
            name: Scorer identifier to remove.
        """
        
    def score(
        self,
        prompt: str,
        response: str,
        n_samples: Optional[int] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> EnsembleResult:
        """Compute UQLM ensemble score for a prompt-response pair.
        
        Args:
            prompt: Input prompt to the model.
            response: Model response to evaluate.
            n_samples: Number of samples for self-consistency (default=5).
            model_name: Model identifier (default from config).
            temperature: Sampling temperature (default=0.7).
            
        Returns:
            EnsembleResult with uaf_score, scorer_results, metadata.
            
        Raises:
            UQLMError: If model API fails or network timeout.
        """
        
    async def async_score(
        self,
        prompt: str,
        response: str,
        n_samples: int = 5,
        model_name: Optional[str] = None,
    ) -> EnsembleResult:
        """Async version for batch processing.
        
        Args:
            prompt: Input prompt.
            response: Model response.
            n_samples: Number of samples (default=5).
            model_name: Model identifier.
            
        Returns:
            EnsembleResult with computed UAF score.
        """
        
    def get_scorers(self) -> List[str]:
        """Return list of active scorer names."""
        
    def set_weights(self, weights: Dict[str, float]) -> None:
        """Update scorer weights.
        
        Args:
            weights: Dict mapping scorer names to weights.
                   Weights are automatically normalized to sum to 1.0.
        """
```

#### 2.1.3 State

```python
class EnsembleScorer:
    _config: EnsembleConfig
    _scorers: Dict[str, "BaseScorer"]
    _weights: Dict[str, float]
    _model_client: Optional["ModelClient"]
    _cache: Dict[str, Any]
```

#### 2.1.4 Interactions

| Component | Interface | Purpose |
|-----------|-----------|---------|
| `BaseScorer` | Abstract interface | Pluggable scorer implementations |
| `ModelClient` | External dependency | API calls to LLM providers |
| `EnsembleResult` | Output dataclass | Unified output format |
| `Cache` | Internal | LRU cache for repeated prompts |

#### 2.1.5 Internal Architecture

```
BaseScorer (Abstract)
    ├── SemanticEntropyScorer
    │       └── Computes token distribution entropy
    ├── SemanticDensityScorer
    │       └── Measures concept density via embedding
    ├── SelfConsistencyScorer
    │       └── Measures answer consistency across samples
    └── TokenNLLScorer
            └── Computes token-level negative log-likelihood

EnsembleScorer
    ├── Orchestrates scorer execution
    ├── Normalizes scores to [0.0, 1.0]
    ├── Applies weighted combination
    └── Returns EnsembleResult
```

---

### 2.2 clap_probe.py — FR-U-2: CLAP Activation Probe

#### 2.2.1 Responsibility

The CLAP (Contrastive Learning with Activation Probes) module provides hallucination detection via trained classifiers on model hidden states. It is designed for open-weight models (Llama-3.3, Qwen-2.5) where internal representations can be directly accessed. For closed-source models, it falls back to logprobs-based estimation.

#### 2.2.2 Public API

```python
class ActivationProbe:
    """CLAP Activation Probe for hallucination detection."""

    def __init__(self, config: ProbeConfig) -> None:
        """Initialize with probe configuration.
        
        Args:
            config: ProbeConfig with model_type, layer_idx, probe_type, threshold.
            
        Raises:
            ProbeError: If model_type is not supported.
        """
        
    def fit(self, training_data: List[Tuple[np.ndarray, int]]) -> ProbeResult:
        """Train the probe on labeled hidden states.
        
        Args:
            training_data: List of (hidden_state, label) tuples.
                          label=1 indicates hallucination, 0 indicates factual.
                          
        Returns:
            ProbeResult with training metrics.
            
        Raises:
            DataInsufficientError: If training_data < 10 samples.
            ProbeError: If training fails.
        """
        
    def predict(self, hidden_states: np.ndarray) -> ProbeResult:
        """Predict hallucination probability from hidden states.
        
        Args:
            hidden_states: Numpy array of shape (sequence_len, hidden_dim)
                          or (hidden_dim,) for single state.
                          
        Returns:
            ProbeResult with p_hallucinate, confidence, layer_used.
        """
        
    def predict_proba(self, hidden_states: np.ndarray) -> np.ndarray:
        """Return probability estimates for both classes.
        
        Args:
            hidden_states: Hidden states array.
            
        Returns:
            Array of shape (n_samples, 2) with [P(non-halluc), P(halluc)].
        """
        
    def save(self, path: str) -> None:
        """Save trained probe to disk.
        
        Args:
            path: File path for serialized probe.
            
        Raises:
            IOError: If save fails.
        """
        
    @classmethod
    def load(cls, path: str) -> "ActivationProbe":
        """Load trained probe from disk.
        
        Args:
            path: File path to serialized probe.
            
        Returns:
            Loaded ActivationProbe instance.
            
        Raises:
            IOError: If file not found or corrupted.
        """
        
    def get_supported_models(self) -> List[str]:
        """Return list of supported model types."""
        
    def set_threshold(self, threshold: float) -> None:
        """Update classification threshold.
        
        Args:
            threshold: New threshold in [0.0, 1.0].
        """
```

#### 2.2.3 State

```python
class ActivationProbe:
    _config: ProbeConfig
    _probe_model: Optional[LogisticRegression]
    _layer_idx: int
    _is_fitted: bool
    _normalizer: Optional["L2Normalizer"]
```

#### 2.2.4 Interactions

| Component | Interface | Purpose |
|-----------|-----------|---------|
| `LogisticRegression` | sklearn | Binary classifier for hallucination |
| `L2Normalizer` | Internal | Hidden state normalization |
| `ProbeConfig` | Input dataclass | Probe configuration |
| `ProbeResult` | Output dataclass | Prediction results |

#### 2.2.5 Supported Models

| Model Type | Probe Strategy | Fallback |
|------------|---------------|----------|
| `llama-3.3` | Activation probe (LogisticRegression) | — |
| `qwen-2.5` | Activation probe (LogisticRegression) | — |
| `gpt-4` | logprobs + self-consistency | FR-U-1 scorer |
| `claude-3` | logprobs + self-consistency | FR-U-1 scorer |

---

### 2.3 tinylora.py — FR-U-3: TinyLoRA Lightweight Probes

#### 2.3.1 Responsibility

TinyLoRA provides a lightweight LoRA-based probe implementation for edge deployment. It trains low-rank adaptation matrices (A ∈ R^{d×r}, B ∈ R^{r×d}) that can be applied to frozen model weights with minimal parameter overhead. The resulting probe model can run on resource-constrained devices while maintaining accuracy comparable to full linear probes.

#### 2.3.2 Public API

```python
class TinyLoRA:
    """TinyLoRA Lightweight Probes for edge deployment."""

    def __init__(self, config: TinyLoRAConfig) -> None:
        """Initialize TinyLoRA with configuration.
        
        Args:
            config: TinyLoRAConfig with hidden_dim, rank, alpha, lr, dropout.
        """
        
    def train(
        self,
        training_data: List[Tuple[np.ndarray, int]],
        validation_data: Optional[List[Tuple[np.ndarray, int]]] = None,
    ) -> Tuple[TinyLoRAModel, float]:
        """Train LoRA adapters on labeled data.
        
        Args:
            training_data: List of (hidden_state, label) tuples for training.
            validation_data: Optional validation set for early stopping.
            
        Returns:
            Tuple of (TinyLoRAModel, final_training_loss).
            
        Raises:
            DataInsufficientError: If training_data < 10 samples.
            TrainingDivergenceError: If loss increases beyond tolerance.
        """
        
    def infer(
        self,
        model: TinyLoRAModel,
        hidden_states: np.ndarray,
    ) -> float:
        """Run inference with trained LoRA probe.
        
        Args:
            model: Trained TinyLoRAModel.
            hidden_states: Input hidden states (single or batch).
            
        Returns:
            Hallucination probability in [0.0, 1.0].
        """
        
    def apply_lora(
        self,
        original_weights: np.ndarray,
        lora_a: np.ndarray,
        lora_b: np.ndarray,
    ) -> np.ndarray:
        """Apply LoRA adaptation: W' = W + BA.
        
        Args:
            original_weights: Original frozen weight matrix W ∈ R^{d×d}.
            lora_a: LoRA matrix A ∈ R^{d×r}.
            lora_b: LoRA matrix B ∈ R^{r×d}.
            
        Returns:
            Adapted weight matrix W' ∈ R^{d×d}.
            
        Note:
            Application order: B @ A (A applied first to input)
        """
        
    def save_model(self, model: TinyLoRAModel, path: str) -> None:
        """Save trained model to disk.
        
        Args:
            model: Trained TinyLoRAModel.
            path: File path for serialization.
        """
        
    @classmethod
    def load_model(cls, path: str) -> TinyLoRAModel:
        """Load trained model from disk.
        
        Args:
            path: File path to serialized model.
            
        Returns:
            Loaded TinyLoRAModel instance.
        """
        
    def get_model_size(self, model: TinyLoRAModel) -> int:
        """Return model size in bytes.
        
        Args:
            model: TinyLoRAModel instance.
            
        Returns:
            Model size in bytes.
        """
```

#### 2.3.3 State

```python
class TinyLoRA:
    _config: TinyLoRAConfig
    _device: str  # "cpu" or "cuda"
    _lora_a: Optional[np.ndarray]  # Trainable
    _lora_b: Optional[np.ndarray]  # Trainable
    _optimizer: Optional["Adam"]  # From numpy-compatible optimizer
```

#### 2.3.4 LoRA Architecture

```
Original Weight: W ∈ R^{d×d} (frozen)

LoRA Adaptation:
    A ∈ R^{d×r} (trainable, initialized with random Gaussian)
    B ∈ R^{r×d} (trainable, initialized with zeros)
    
Adapted Output: W' = W + B @ A

Memory footprint: 2 × d × r parameters (vs d² for full weight)
    - d = hidden_dim (e.g., 4096)
    - r = rank (e.g., 4)
    - For d=4096, r=4: ~64KB vs 64MB for full matrix
```

#### 2.3.5 Interactions

| Component | Interface | Purpose |
|-----------|-----------|---------|
| `TinyLoRAConfig` | Input dataclass | Configuration parameters |
| `TinyLoRAModel` | Output dataclass | Trained model container |
| `AdamOptimizer` | Internal | Parameter optimization |
| `MSE-loss` | Training objective | Binary classification |

---

**[END OF PART 1 — 412 lines]**---

## Chapter 3: Data Models

### 3.1 EnsembleConfig

```python
@dataclass
class EnsembleConfig:
    """Configuration for UQLM Ensemble Scorer."""

    model_name: str = "gpt-4"
    n_samples: int = 5
    temperature: float = 0.7
    weights: Optional[Dict[str, float]] = None  # Auto-normalized if provided
    scorer_types: List[str] = field(
        default_factory=lambda: [
            "semantic_entropy",
            "semantic_density",
            "self_consistency",
            "token_nll"
        ]
    )
    cache_enabled: bool = True
    cache_size: int = 1000
    timeout_seconds: float = 30.0
    api_base: Optional[str] = None  # For custom API endpoints
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.n_samples < 1:
            raise ValueError(f"n_samples must be >= 1, got {self.n_samples}")
        if not 0.0 < self.temperature <= 2.0:
            raise ValueError(f"temperature must be in (0, 2], got {self.temperature}")
        if self.weights is not None:
            total = sum(self.weights.values())
            if abs(total - 1.0) > 1e-6:
                # Auto-normalize weights
                self.weights = {k: v/total for k, v in self.weights.items()}
```

### 3.2 ScorerResult

```python
@dataclass
class ScorerResult:
    """Result from a single scorer in the UQLM ensemble."""

    scorer_name: str
    score: float  # Normalized to [0.0, 1.0]
    raw_value: float  # Original scorer output (unnormalized)
    confidence: float = 1.0  # Confidence in the score [0.0, 1.0]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate scorer result."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass
class EnsembleResult:
    """Aggregated result from UQLM Ensemble Scorer."""

    uaf_score: float  # Weighted combination of scorer results
    scorer_results: List[ScorerResult]
    n_samples: int  # Number of samples used
    model_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def uncertainty_level(self) -> str:
        """Categorize uncertainty level."""
        if self.uaf_score < 0.2:
            return "LOW"
        elif self.uaf_score < 0.5:
            return "MEDIUM"
        else:
            return "HIGH"

    @property
    def dominant_factor(self) -> Optional[str]:
        """Identify the scorer's contributing most to high uncertainty."""
        if not self.scorer_results:
            return None
        return max(
            self.scorer_results,
            key=lambda r: r.score * r.confidence
        ).scorer_name
```

### 3.3 ProbeConfig

```python
@dataclass
class ProbeConfig:
    """Configuration for CLAP Activation Probe."""

    model_type: str  # e.g., "llama-3.3", "qwen-2.5", "gpt-4"
    layer_idx: int = -1  # -1 = last layer
    probe_type: str = "logistic_regression"  # or "linear_probe"
    threshold: float = 0.5  # Classification threshold
    hidden_dim: Optional[int] = None  # Auto-detected if None
    use_normalization: bool = True
    calibration_enabled: bool = True
    training_config: Optional[TrainingConfig] = None

    # For TinyLoRA compatibility
    use_tinylora: bool = False
    lora_rank: int = 4
    lora_alpha: float = 1.0

    def __post_init__(self) -> None:
        """Validate probe configuration."""
        supported_types = ["llama-3.3", "qwen-2.5", "gpt-4", "claude-3", "gpt-3.5-turbo"]
        if self.model_type not in supported_types:
            raise ProbeError(
                f"Unsupported model_type: {self.model_type}. "
                f"Supported: {supported_types}"
            )
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"threshold must be in [0.0, 1.0], got {self.threshold}")


@dataclass
class TrainingConfig:
    """Configuration for probe training."""

    n_epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 0.001
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    l2_reg: float = 0.01


@dataclass
class ProbeResult:
    """Result from activation probe prediction."""

    p_hallucinate: float  # Probability of hallucination [0.0, 1.0]
    p_factual: float  # Probability of being factual
    confidence: float  # Confidence in prediction [0.0, 1.0]
    layer_used: int  # Which layer was used for prediction
    model_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def prediction(self) -> str:
        """Return 'hallucination' or 'factual' based on threshold."""
        return "hallucination" if self.p_hallucinate >= 0.5 else "factual"

    @property
    def is_high_confidence(self) -> bool:
        """Check if prediction confidence is high."""
        return self.confidence >= 0.8
```

### 3.4 TinyLoRAConfig and TinyLoRAModel

```python
@dataclass
class TinyLoRAConfig:
    """Configuration for TinyLoRA lightweight probes."""

    hidden_dim: int = 4096
    rank: int = 4
    alpha: float = 1.0  # Scaling factor
    learning_rate: float = 0.001
    dropout: float = 0.1
    batch_size: int = 32
    n_epochs: int = 100
    patience: int = 10  # Early stopping patience
    device: str = "cpu"  # "cpu" or "cuda"
    lora_init_method: str = "gaussian"  # "gaussian" or "normal"

    # Scaling: output = W + (alpha/rank) * B @ A
    scaling: float = field(init=False)

    def __post_init__(self) -> None:
        self.scaling = self.alpha / self.rank
        if self.hidden_dim <= 0:
            raise ValueError(f"hidden_dim must be > 0, got {self.hidden_dim}")
        if self.rank <= 0:
            raise ValueError(f"rank must be > 0, got {self.rank}")


@dataclass
class TinyLoRAModel:
    """Container for trained TinyLoRA parameters."""

    lora_a: np.ndarray  # Shape: (hidden_dim, rank)
    lora_b: np.ndarray  # Shape: (rank, hidden_dim)
    config: TinyLoRAConfig
    training_history: Dict[str, List[float]] = field(default_factory=dict)
    final_loss: Optional[float] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_parameter_count(self) -> int:
        """Return total number of trainable parameters."""
        return self.lora_a.size + self.lora_b.size

    def get_memory_bytes(self) -> int:
        """Estimate memory footprint in bytes."""
        return self.lora_a.nbytes + self.lora_b.nbytes
```

### 3.5 MetaQAResult

```python
@dataclass
class MetaQAResult:
    """Result from MetaQA drift detection."""

    drift_score: float  # KL divergence or distribution shift measure [0.0, 1.0]
    drifted_tokens: List[int]  # Indices of tokens with significant drift
    baseline_distribution: Dict[str, float]  # Reference distribution
    current_distribution: Dict[str, float]  # Current token distribution
    window_size: int  # Analysis window
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_significant_drift(self) -> bool:
        """Check if drift exceeds threshold."""
        return self.drift_score > 0.3

    @property
    def drift_severity(self) -> str:
        """Categorize drift severity."""
        if self.drift_score < 0.1:
            return "NEGLIGIBLE"
        elif self.drift_score < 0.3:
            return "MINOR"
        elif self.drift_score < 0.5:
            return "MODERATE"
        else:
            return "SEVERE"


@dataclass
class DriftScore:
    """Detailed drift score with per-token breakdown."""

    overall_drift: float
    per_token_drift: Dict[int, float]  # token_idx -> drift amount
    concept_drift: Dict[str, float]  # concept -> drift amount
    temporal_drift: Optional[float] = None  # Drift over time
    baseline_version: Optional[str] = None
    current_version: Optional[str] = None


@dataclass
class GapFinding
    """Represents a detected implementation gap."""

    gap_type: GapType
    severity: GapSeverity
    location: str  # File path or function name
    description: str
    expected: str  # What should be present
    actual: str  # What is actually present
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


enum GapType(Enum):
    """Types of implementation gaps."""

    MISSING_ERROR_HANDLING = "missing_error_handling"
    MISSING_VALIDATION = "missing_validation"
    MISSING_LOGGING = "missing_logging"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    SECRET_EXPOSURE = "secret_exposure"
    UNHANDLED_EDGE_CASE = "unhandled_edge_case"
    INCONSISTENT_API = "inconsistent_api"
    DEPRECATED_USAGE = "deprecated_usage"


enum GapSeverity(Enum):
    """Severity levels for implementation gaps."""

    CRITICAL = 1  # Must fix before deployment
    HIGH = 2  # Should fix soon
    MEDIUM = 3  # Fix when convenient
    LOW = 4  # Nice to fix
    INFO = 5  # Informational only
```

### 3.6 UncertaintyScore

```python
@dataclass
class UncertaintyScore:
    """Unified uncertainty score combining all components."""

    score: float  # Final combined score [0.0, 1.0]
    decision: str  # "PASS" | "ROUND_2" | "HITL"
    components: Dict[str, float]  # Component contributions
    weights: Dict[str, float]  # Weights used for combination
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Detailed component scores
    uqlm_score: Optional[float] = None
    clap_score: Optional[float] = None
    metaqa_score: Optional[float] = None
    gap_score: Optional[float] = None

    # Additional context
    model_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self) -> None:
        """Validate and set decision based on score."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score}")

        # Auto-set decision if not provided
        if self.decision == "AUTO":
            if self.score < 0.2:
                self.decision = "PASS"
            elif self.score < 0.5:
                self.decision = "ROUND_2"
            else:
                self.decision = "HITL"

    @property
    def is_safe(self) -> bool:
        """Check if output can proceed automatically."""
        return self.decision == "PASS"

    @property
    def needs_review(self) -> bool:
        """Check if output needs human review."""
        return self.decision == "HITL"


@dataclass
class CalibrationResult:
    """Result from confidence calibration."""

    calibrated_score: float
    original_score: float
    calibration_method: str  # "platt" | "isotonic" | "temperature"
    reliability_diagram: Optional[List[Tuple[float, float]]] = None  # (avg_pred, avg_true)
    ece: Optional[float] = None  # Expected Calibration Error
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def improvement(self) -> float:
        """Return improvement from calibration."""
        return abs(self.calibrated_score - self.original_score)

    @property
    def is_calibrated(self) -> bool:
        """Check if ECE is below threshold."""
        return self.ece is not None and self.ece < 0.05
```

---

## Chapter 4: Component Specifications (Continued)

### 2.4 metaqa.py — FR-U-4: MetaQA Drift Detection

#### 2.4.1 Responsibility

The MetaQA module monitors model output distribution for shifts that indicate potential hallucinations. It computes KL divergence between baseline and current token distributions, tracks drifted tokens, and maintains rolling baselines for continuous monitoring. The module is designed to work with any token-generating model by analyzing the output distribution at inference time.

#### 2.4.2 Public API

```python
class MetaQADetector:
    """MetaQA Drift Detection for output distribution monitoring."""

    def __init__(
        self,
        baseline_distribution: Optional[Dict[str, float]] = None,
        window_size: int = 100,
        drift_threshold: float = 0.3,
        min_samples: int = 50,
    ) -> None:
        """Initialize MetaQA detector.

        Args:
            baseline_distribution: Reference distribution for KL comparison.
            window_size: Number of recent tokens to analyze.
            drift_threshold: Threshold for triggering drift alert.
            min_samples: Minimum samples needed for reliable estimation.
        """

    def update_baseline(
        self,
        token_distribution: Dict[str, float],
        version: Optional[str] = None,
    ) -> None:
        """Update the baseline distribution.

        Args:
            token_distribution: New baseline distribution.
            version: Optional version identifier for tracking.
        """

    def compute_drift(
        self,
        current_tokens: List[str],
        current_distribution: Optional[Dict[str, float]] = None,
    ) -> MetaQAResult:
        """Compute drift between baseline and current distribution.

        Args:
            current_tokens: List of tokens from current response.
            current_distribution: Optional pre-computed distribution.

        Returns:
            MetaQAResult with drift_score, drifted_tokens, and metadata.
        """

    def compute_kl_divergence(
        self,
        p: Dict[str, float],
        q: Dict[str, float],
        smoothing: float = 1e-9,
    ) -> float:
        """Compute KL(p || q) divergence.

        Args:
            p: Target distribution.
            q: Reference distribution.
            smoothing: Laplace smoothing constant.

        Returns:
            KL divergence value (bounded to [0.0, 1.0]).
        """

    def rolling_baseline_update(
        self,
        token: str,
        reward_signal: float,
    ) -> None:
        """Update rolling baseline with new token and reward.

        Args:
            token: Token string.
            reward_signal: Quality signal (-1 to 1).
        """

    def get_baseline(self) -> Dict[str, float]:
        """Return current baseline distribution."""

    def reset_baseline(self) -> None:
        """Reset baseline to uniform distribution."""
```

#### 2.4.3 State

```python
class MetaQADetector:
    _baseline: Dict[str, float]
    _baseline_version: Optional[str]
    _window_size: int
    _drift_threshold: float
    _min_samples: int
    _token_history: List[str]
    _drift_history: List[float]
    _rolling_baseline: Optional[Dict[str, float]]
```

#### 2.4.4 Interactions

| Component | Interface | Purpose |
|-----------|-----------|---------|
| `MetaQAResult` | Output dataclass | Drift detection results |
| `BaselineManager` | Internal | Baseline version management |
| `TokenBuffer` | Internal | Rolling window of tokens |

---

### 2.5 gap_detector.py — FR-U-5: Implementation Gap Detection

#### 2.5.1 Responsibility

The Gap Detector performs AST-based code quality analysis to identify implementation gaps that could lead to hallucinations in generated code. It scans for missing error handling, security vulnerabilities, secret exposures, deprecated API usage, and other quality issues. The detector integrates with the unified scoring system by providing a gap_score that correlates with hallucination risk.

#### 2.5.2 Public API

```python
class GapDetector:
    """Implementation Gap Detector for code quality analysis."""

    def __init__(
        self,
        rules: Optional[List[GapRule]] = None,
        severity_threshold: GapSeverity = GapSeverity.MEDIUM,
        languages: Optional[List[str]] = None,
    ) -> None:
        """Initialize Gap Detector.

        Args:
            rules: Custom gap detection rules. Uses defaults if None.
            severity_threshold: Minimum severity to report.
            languages: Languages to scan (e.g., ["python", "javascript"]).
        """

    def detect(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GapFinding]:
        """Detect implementation gaps in code.

        Args:
            code: Source code to analyze.
            language: Programming language (e.g., "python").
            context: Optional context (file_path, function_name, etc.).

        Returns:
            List of GapFinding sorted by severity (most severe first).
        """

    def detect_secrets(self, code: str) -> List[GapFinding]:
        """Scan for hardcoded secrets and credentials.

        Args:
            code: Source code to scan.

        Returns:
            List of GapFinding with SECRET_EXPOSURE type.
        """

    def detect_error_handling(self, code: str, language: str) -> List[GapFinding]:
        """Detect missing or inadequate error handling.

        Args:
            code: Source code to analyze.
            language: Programming language.

        Returns:
            List of GapFinding with MISSING_ERROR_HANDLING type.
        """

    def detect_security(self, code: str, language: str) -> List[GapFinding]:
        """Detect potential security vulnerabilities.

        Args:
            code: Source code to analyze.
            language: Programming language.

        Returns:
            List of GapFinding with SECURITY_VULNERABILITY type.
        """

    def compute_gap_score(
        self,
        findings: List[GapFinding],
    ) -> float:
        """Compute normalized gap score from findings.

        Args:
            findings: List of detected gaps.

        Returns:
            Gap score in [0.0, 1.0] where 1.0 = maximum risk.
        """

    def add_rule(self, rule: GapRule) -> None:
        """Add a custom gap detection rule.

        Args:
            rule: GapRule to add to detection pipeline.
        """
```

#### 2.5.3 State

```python
class GapDetector:
    _rules: List[GapRule]
    _severity_threshold: GapSeverity
    _languages: Set[str]
    _ast_parser: Dict[str, "ASTParser"]
    _secret_patterns: List[Pattern]
    _findings_cache: LRUCache
```

#### 2.5.4 Gap Detection Rules

| Rule | Severity | Description |
|------|----------|-------------|
| `bare_except` | HIGH | Bare `except:` clause that catches all exceptions |
| `hardcoded_secret` | CRITICAL | Hardcoded API keys, passwords, tokens |
| `sql_injection` | CRITICAL | Unescaped SQL string concatenation |
| `no_validation` | MEDIUM | Missing input validation |
| `deprecated_api` | LOW | Usage of deprecated API |
| `resource_leak` | HIGH | Unclosed resources (files, connections) |
| `log_injection` | MEDIUM | Unsanitized log input |
| `weak_crypto` | HIGH | Weak cryptographic usage |

---

### 2.6 uncertainty_score.py — FR-U-6: Unified Score Calculator

#### 2.6.1 Responsibility

The Unified Score Calculator combines uncertainty signals from all components (UQLM, CLAP, MetaQA, Gap) into a single normalized score using weighted combination. It handles missing components gracefully, redistributes weights accordingly, and produces a final decision (PASS/ROUND_2/HITL) based on configurable thresholds.

#### 2.6.2 Public API

```python
class UnifiedScoreCalculator:
    """Unified uncertainty score calculator."""

    DEFAULT_WEIGHTS = {
        "uqlm": 0.5,
        "clap": 0.3,
        "metaqa": 0.2,
        "gap": 0.0,  # Optional, not included by default
    }

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize calculator.

        Args:
            weights: Component weights. Defaults to DEFAULT_WEIGHTS.
            thresholds: Decision thresholds. Defaults to standard thresholds.
        """

    def compute(
        self,
        uqlm_score: Optional[float] = None,
        clap_score: Optional[float] = None,
        metaqa_score: Optional[float] = None,
        gap_score: Optional[float] = None,
    ) -> UncertaintyScore:
        """Compute unified uncertainty score.

        Args:
            uqlm_score: UQLM ensemble score.
            clap_score: CLAP activation probe score.
            metaqa_score: MetaQA drift detection score.
            gap_score: Implementation gap score.

        Returns:
            UncertaintyScore with combined score and decision.
        """

    def compute_weighted_sum(
        self,
        scores: Dict[str, float],
        weights: Dict[str, float],
    ) -> float:
        """Compute weighted sum of scores.

        Args:
            scores: Component scores dict.
            weights: Component weights dict.

        Returns:
            Weighted sum normalized to [0.0, 1.0].
        """

    def redistribute_weights(
        self,
        available_components: List[str],
    ) -> Dict[str, float]:
        """Redistribute weights when components are missing.

        Args:
            available_components: List of available component names.

        Returns:
            Redistributed weights dict.
        """

    def decide(self, score: float) -> str:
        """Make routing decision based on score.

        Args:
            score: Combined uncertainty score.

        Returns:
            Decision: "PASS" | "ROUND_2" | "HITL".
        """

    def set_thresholds(
        self,
        pass_threshold: float,
        round2_threshold: float,
    ) -> None:
        """Update decision thresholds.

        Args:
            pass_threshold: Max score for PASS decision.
            round2_threshold: Max score for ROUND_2 decision.
        """
```

#### 2.6.3 State

```python
class UnifiedScoreCalculator:
    _weights: Dict[str, float]
    _thresholds: Dict[str, float]
    _component_stats: Dict[str, Dict[str, float]]  # Running statistics
```

#### 2.6.4 Weight Redistribution Rules

| Missing Components | Redistributed Weights |
|-------------------|----------------------|
| None | uqlm=0.5, clap=0.3, metaqa=0.2 |
| CLAP only | uqlm=0.65, metaqa=0.35 |
| MetaQA only | uqlm=0.65, clap=0.35 |
| CLAP + MetaQA | uqlm=1.0 |
| Gap (optional) | Weights unchanged, gap_score ignored |

---

### 2.7 confidence_calibrator.py — FR-U-7: Confidence Calibration

#### 2.7.1 Responsibility

The Confidence Calibrator aligns model confidence with actual accuracy using Platt scaling and temperature scaling. It learns calibration parameters from historical prediction data, computes Expected Calibration Error (ECE), and generates reliability diagrams. This ensures that when the system says "80% confident," it is actually correct 80% of the time.

#### 2.7.2 Public API

```python
class ConfidenceCalibrator:
    """Confidence calibration using Platt and temperature scaling."""

    def __init__(
        self,
        method: str = "platt",
        n_bins: int = 10,
    ) -> None:
        """Initialize calibrator.

        Args:
            method: Calibration method ("platt" | "isotonic" | "temperature").
            n_bins: Number of bins for ECE calculation.
        """

    def fit(
        self,
        predictions: List[float],  # Predicted probabilities
        labels: List[int],  # Ground truth (0 or 1)
    ) -> CalibrationResult:
        """Fit calibration parameters on prediction data.

        Args:
            predictions: List of predicted probabilities.
            labels: List of ground truth labels.

        Returns:
            CalibrationResult with trained parameters and ECE.

        Raises:
            DataInsufficientError: If len(predictions) < 100.
        """

    def calibrate(
        self,
        score: float,
    ) -> float:
        """Apply calibration to a single score.

        Args:
            score: Uncalibrated score.

        Returns:
            Calibrated probability in [0.0, 1.0].
        """

    def calibrate_batch(
        self,
        scores: List[float],
    ) -> List[float]:
        """Apply calibration to a batch of scores.

        Args:
            scores: List of uncalibrated scores.

        Returns:
            List of calibrated probabilities.
        """

    def compute_ece(
        self,
        predictions: List[float],
        labels: List[int],
        n_bins: Optional[int] = None,
    ) -> float:
        """Compute Expected Calibration Error.

        Args:
            predictions: Predicted probabilities.
            labels: Ground truth labels.
            n_bins: Number of bins (overrides default).

        Returns:
            ECE value (0.0 = perfectly calibrated).
        """

    def platt_transform(
        self,
        score: float,
        a: float,
        b: float,
    ) -> float:
        """Apply Platt scaling: p_calibrated = 1 / (1 + exp(a * score + b)).

        Args:
            score: Uncalibrated score.
            a: Scale parameter.
            b: Bias parameter.

        Returns:
            Platt-calibrated probability.
        """

    def temperature_scale(
        self,
        score: float,
        temperature: float,
    ) -> float:
        """Apply temperature scaling: p_calibrated = score^(1/T).

        Args:
            score: Uncalibrated logit or probability.
            temperature: Temperature parameter (T > 0).

        Returns:
            Temperature-scaled probability.
        """

    def get_reliability_diagram(
        self,
        predictions: List[float],
        labels: List[int],
    ) -> List[Tuple[float, float]]:
        """Generate reliability diagram data.

        Args:
            predictions: Predicted probabilities.
            labels: Ground truth labels.

        Returns:
            List of (avg_predicted, avg_accuracy) per bin.
        """

    def save(self, path: str) -> None:
        """Save calibration parameters to disk."""

    @classmethod
    def load(cls, path: str) -> "ConfidenceCalibrator":
        """Load calibration parameters from disk."""
```

#### 2.7.3 State

```python
class ConfidenceCalibrator:
    _method: str
    _n_bins: int
    _platt_a: Optional[float] = None
    _platt_b: Optional[float] = None
    _temperature: Optional[float] = None
    _is_fitted: bool = False
    _calibration_curve: List[Tuple[float, float]]
```

#### 2.7.4 Calibration Methods

| Method | Formula | Use Case |
|--------|---------|----------|
| Platt Scaling | p = 1/(1+exp(a·s+b)) | Binary classification |
| Temperature Scaling | p = s^(1/T) | Multi-class, model-level |
| Isotonic Regression | p = monotone interpolation | Non-parametric |

---

**[END OF PART 2 — 412 lines]**
---

## Chapter 5: Algorithm Details

### 5.1 UQLM Ensemble Algorithm

#### 5.1.1 Semantic Entropy

```
Algorithm: SemanticEntropy(prompt, response, n_samples)
    tokens ← tokenize(response)
    samples ← []
    
    for i in 1 to n_samples:
        s ← generate(prompt, temperature=0.7)
        emb ← embed(s)  # Sentence-level embedding
        samples.append(emb)
    
    # Compute embedding distribution entropy
    distances ← pairwise_distances(samples, metric='cosine')
    probs ← softmax(-distances)  # Convert to probability distribution
    
    entropy ← -sum(p * log(p + ε) for p in probs)
    normalized_entropy ← entropy / log(n_samples)  # Bound to [0, 1]
    
    return normalized_entropy
```

**Interpretation**: High semantic entropy means the model generates semantically diverse responses to the same prompt, indicating uncertainty.

#### 5.1.2 Semantic Density

```
Algorithm: SemanticDensity(response)
    tokens ← tokenize(response)
    embeddings ← [embed(t) for t in tokens]
    
    # Measure concept concentration
    concept_scores ← []
    for i, emb in enumerate(embeddings):
        # Cosine similarity to concept vocabulary
        similarity ← max(cos_sim(emb, concept) for concept in concept_vocab)
        concept_scores.append(similarity)
    
    density ← mean(concept_scores)
    coverage ← fraction(tokens_above_threshold(concept_scores))
    
    # Penalize both sparse and overly dense responses
    score ← 0.5 * density + 0.5 * min(coverage, 1.0)
    
    return score
```

**Interpretation**: Low semantic density may indicate hallucinated content that lacks grounding in known concepts.

#### 5.1.3 Self-Consistency

```
Algorithm: SelfConsistency(prompt, response, n_samples=5)
    samples ← [generate(prompt, temperature=0.7) for _ in range(n_samples)]
    
    # Extract answer entities/values
    answers ← [extract_key_answer(s) for s in samples]
    
    # Compute agreement rate
    consensus ← mode(answers)
    agreement ← count(answers == consensus) / n_samples
    
    # Penalize if response differs from consensus
    response_answer ← extract_key_answer(response)
    consistency ← 1.0 if response_answer == consensus else 0.0
    
    return 1.0 - agreement  # High agreement = low uncertainty
```

#### 5.1.4 Token-Level NLL

```
Algorithm: TokenNLL(response, model)
    tokens ← tokenize(response)
    nlls ← []
    
    for i, token in enumerate(tokens):
        # Compute log probability of token given previous
        logits ← model.predict_logits(tokens[:i])
        log_probs ← softmax(logits)
        token_idx ← vocabulary[token]
        nll ← -log_probs[token_idx]
        nlls.append(nll)
    
    # Aggregate: mean with outlier clipping
    nlls_filtered ← clip(nlls, lower=0, upper=percentile(nlls, 95))
    mean_nll ← mean(nlls_filtered)
    
    # Normalize to [0, 1]
    normalized ← sigmoid((mean_nLL - 2.0) / 1.0)  # 2.0 = typical threshold
    
    return normalized
```

#### 5.1.5 UQLM Ensemble Combination

```
Algorithm: UQLMEnsemble(prompt, response)
    scores ← {}
    
    scores['semantic_entropy'] ← SemanticEntropy(prompt, response, n=5)
    scores['semantic_density'] ← SemanticDensity(response)
    scores['self_consistency'] ← SelfConsistency(prompt, response, n=5)
    scores['token_nll'] ← TokenNLL(response, model)
    
    # Weighted combination
    weights ← {'semantic_entropy': 0.3, 'semantic_density': 0.2,
               'self_consistency': 0.3, 'token_nll': 0.2}
    
    uaf_score ← sum(scores[k] * weights[k] for k in scores)
    
    return uaf_score, scores
```

---

### 5.2 CLAP Probe Algorithm

#### 5.2.1 Layer Selection

```
Algorithm: SelectOptimalLayer(hidden_states, labels, n_layers_to_try=5)
    best_layer ← -1
    best_score ← 0.0
    
    candidate_layers ← evenly_spaced(0, n_layers, n_layers_to_try)
    
    for layer_idx in candidate_layers:
        states ← hidden_states[:, layer_idx, :]  # Extract layer
        states ← L2_normalize(states)
        
        # Quick training with logistic regression
        clf ← LogisticRegression(C=1.0, max_iter=100)
        clf.fit(states, labels)
        
        score ← cross_val_score(clf, states, labels, cv=3)
        
        if score > best_score:
            best_score ← score
            best_layer ← layer_idx
    
    return best_layer
```

#### 5.2.2 Contrastive Training

```
Algorithm: CLAPContrastiveTrain(states, margin=0.5)
    # Positive pairs: same label states
    # Negative pairs: different label states
    
    for epoch in range(n_epochs):
        total_loss ← 0.0
        
        for (anchor, positive, negative) in batches:
            # Compute distances
            d_pos ← ||anchor - positive||²
            d_neg ← ||anchor - negative||²
            
            # Contrastive loss
            loss ← max(0, d_pos - d_neg + margin)
            
            # Backpropagate
            update(anchor, positive, negative, loss)
            total_loss += loss
        
        if total_loss < convergence_threshold:
            break
    
    return trained_probes
```

---

### 5.3 Unified Score Combination

#### 5.3.1 Weight Redistribution

```
Algorithm: RedistributeWeights(available_components)
    base_weights ← {
        'uqlm': 0.5,
        'clap': 0.3,
        'metaqa': 0.2,
        'gap': 0.0
    }
    
    if 'gap' not in available_components:
        # Gap is optional, redistribute to others
        factor ← 1.0 / (1.0 - base_weights['gap'])
        for k in available_components:
            base_weights[k] *= factor
    
    total ← sum(base_weights[k] for k in available_components)
    
    # Normalize
    for k in base_weights:
        base_weights[k] /= total
    
    return {k: base_weights[k] for k in available_components}
```

#### 5.3.2 Decision Thresholds

| Score Range | Decision | Action |
|-------------|----------|--------|
| [0.0, 0.2) | PASS | Proceed automatically |
| [0.2, 0.5) | ROUND_2 | Additional verification |
| [0.5, 1.0] | HITL | Human-in-the-loop review |

**Adaptive Thresholds** (optional):
- Domain-specific thresholds can be set per use case
- High-stakes domains (medical, legal) use lower HITL threshold (0.3)

---

### 5.4 MetaQA Drift Detection

```
Algorithm: ComputeDrift(current_tokens, baseline)
    current_dist ← compute_distribution(current_tokens)
    
    # KL divergence: D_KL(baseline || current)
    kl ← 0.0
    for token in union(baseline.keys(), current_dist.keys()):
        p ← baseline.get(token, ε)
        q ← current_dist.get(token, ε)
        kl += p * log(p / q)
    
    # Bound to [0, 1]
    bounded_kl ← min(kl / log(2), 1.0)  # log(2) ≈ 0.693
    
    # Identify drifted tokens
    drifted ← []
    for token, prob in current_dist.items():
        baseline_prob ← baseline.get(token, ε)
        if |prob - baseline_prob| > drift_tolerance:
            drifted.append(token)
    
    return MetaQAResult(
        drift_score=bounded_kl,
        drifted_tokens=drifted,
        baseline_distribution=baseline,
        current_distribution=current_dist
    )
```

---

## Chapter 6: API Design

### 6.1 Module Export Summary

#### ensemble.py (FR-U-1)
```python
from ensemble import EnsembleScorer, EnsembleConfig, EnsembleResult, ScorerResult

__all__ = [
    'EnsembleScorer',
    'EnsembleConfig',
    'EnsembleResult',
    'ScorerResult',
]
```

#### clap_probe.py (FR-U-2)
```python
from clap_probe import (
    ActivationProbe,
    ProbeConfig,
    ProbeResult,
    TrainingConfig,
)

__all__ = [
    'ActivationProbe',
    'ProbeConfig',
    'ProbeResult',
    'TrainingConfig',
]
```

#### tinylora.py (FR-U-3)
```python
from tinylora import (
    TinyLoRA,
    TinyLoRAConfig,
    TinyLoRAModel,
)

__all__ = [
    'TinyLoRA',
    'TinyLoRAConfig',
    'TinyLoRAModel',
]
```

#### metaqa.py (FR-U-4)
```python
from metaqa import (
    MetaQADetector,
    MetaQAResult,
    DriftScore,
)

__all__ = [
    'MetaQADetector',
    'MetaQAResult',
    'DriftScore',
]
```

#### gap_detector.py (FR-U-5)
```python
from gap_detector import (
    GapDetector,
    GapFinding,
    GapType,
    GapSeverity,
)

__all__ = [
    'GapDetector',
    'GapFinding',
    'GapType',
    'GapSeverity',
]
```

#### uncertainty_score.py (FR-U-6)
```python
from uncertainty_score import (
    UnifiedScoreCalculator,
    UncertaintyScore,
    CalibrationResult,
)

__all__ = [
    'UnifiedScoreCalculator',
    'UncertaintyScore',
    'CalibrationResult',
]
```

#### confidence_calibrator.py (FR-U-7)
```python
from confidence_calibrator import (
    ConfidenceCalibrator,
    CalibrationResult,
)

__all__ = [
    'ConfidenceCalibrator',
    'CalibrationResult',
]
```

### 6.2 High-Level Entry Point

```python
# uncertainty_gateway.py — Single entry point for Layer 3

from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class UncertaintyInput:
    prompt: str
    response: str
    model_name: str
    hidden_states: Optional[np.ndarray] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class UncertaintyOutput:
    score: UncertaintyScore
    metadata: Dict[str, Any]

class UncertaintyGateway:
    """Unified entry point for uncertainty quantification."""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.ensemble = EnsembleScorer(config.get('ensemble'))
        self.probe = ActivationProbe(config.get('probe'))
        self.metaqa = MetaQADetector(config.get('metaqa'))
        self.gap_detector = GapDetector(config.get('gap'))
        self.calculator = UnifiedScoreCalculator(config.get('weights'))
        self.calibrator = ConfidenceCalibrator()

    def quantify(
        self,
        input: UncertaintyInput,
    ) -> UncertaintyOutput:
        """Quantify uncertainty for a prompt-response pair."""
        # Collect all scores
        scores = {}

        # UQLM (always available)
        ensemble_result = self.ensemble.score(
            input.prompt, input.response, model_name=input.model_name
        )
        scores['uqlm'] = ensemble_result.uaf_score

        # CLAP (if hidden states available)
        if input.hidden_states is not None:
            probe_result = self.probe.predict(input.hidden_states)
            scores['clap'] = probe_result.p_hallucinate

        # MetaQA (if baseline available)
        metaqa_result = self.metaqa.compute_drift(input.response)
        scores['metaqa'] = metaqa_result.drift_score

        # Gap (if code)
        if input.context.get('is_code', False):
            gaps = self.gap_detector.detect(
                input.response,
                input.context.get('language', 'python')
            )
            scores['gap'] = self.gap_detector.compute_gap_score(gaps)

        # Combine
        final_score = self.calculator.compute(**scores)

        return UncertaintyOutput(
            score=final_score,
            metadata={
                'ensemble_details': ensemble_result.scorer_results,
                'metaqa_details': metaqa_result,
            }
        )
```

---

## Chapter 7: File Structure

```
skills/methodology-v2/
├── uncertainty/
│   ├── __init__.py
│   ├── ensemble.py              # FR-U-1: UQLM Ensemble
│   ├── clap_probe.py            # FR-U-2: CLAP Activation Probe
│   ├── tinylora.py              # FR-U-3: TinyLoRA Lightweight
│   ├── metaqa.py                # FR-U-4: MetaQA Drift Detection
│   ├── gap_detector.py          # FR-U-5: Implementation Gap Detection
│   ├── uncertainty_score.py     # FR-U-6: Unified Score Calculator
│   ├── confidence_calibrator.py # FR-U-7: Confidence Calibration
│   ├── uncertainty_gateway.py   # High-level entry point
│   ├── data_models.py           # Shared dataclasses
│   └── utils.py                 # Shared utilities
├── tests/
│   ├── test_ensemble.py
│   ├── test_clap_probe.py
│   ├── test_tinylora.py
│   ├── test_metaqa.py
│   ├── test_gap_detector.py
│   ├── test_uncertainty_score.py
│   └── test_integration.py
├── configs/
│   ├── default_config.yaml
│   ├── probe_training.yaml
│   └── calibration.yaml
├── data/
│   ├── baselines/               # MetaQA baselines
│   ├── probes/                  # Trained CLAP probes
│   └── training_data/          # Probe training datasets
├── ARCHITECTURE.md              # This document
└── README.md
```

---

## Chapter 8: Dependencies & Interfaces

### 8.1 External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | ≥1.24 | Array operations |
| `scikit-learn` | ≥1.3 | Logistic regression, calibration |
| `torch` | ≥2.0 | TinyLoRA training (optional) |
| `transformers` | ≥4.35 | Hidden state extraction |
| `sentence-transformers` | ≥2.2 | Semantic embeddings |
| `ast` | (stdlib) | Python code parsing |
| `re` | (stdlib) | Pattern matching for secrets |
| `json` | (stdlib) | Configuration files |

### 8.2 Layer Interfaces

#### Layer 2 → Layer 3 Interface
```python
@dataclass
class LLMOutput:
    text: str
    model_name: str
    hidden_states: Optional[np.ndarray] = None
    logprobs: Optional[List[float]] = None
    finish_reason: str = "stop"
```

#### Layer 3 → Layer 4 Interface
```python
@dataclass
class Layer3Output:
    decision: str  # "PASS" | "ROUND_2" | "HITL"
    uncertainty_score: float
    component_scores: Dict[str, float]
    requires_verification: bool
    metadata: Dict[str, Any]
```

### 8.3 Internal Module Dependencies

```
uncertainty_gateway.py
├── EnsembleScorer (ensemble.py)
│   ├── BaseScorer (abstract)
│   ├── SemanticEntropyScorer
│   ├── SemanticDensityScorer
│   ├── SelfConsistencyScorer
│   └── TokenNLLScorer
├── ActivationProbe (clap_probe.py)
│   ├── LogisticRegression (sklearn)
│   └── L2Normalizer
├── TinyLoRA (tinylora.py)
├── MetaQADetector (metaqa.py)
├── GapDetector (gap_detector.py)
├── UnifiedScoreCalculator (uncertainty_score.py)
└── ConfidenceCalibrator (confidence_calibrator.py)
```

---

## Chapter 9: Edge Cases & Error Handling

### 9.1 UQLM Ensemble Edge Cases

| Edge Case | Handling |
|-----------|----------|
| API timeout | Return cached result or degrade gracefully |
| Empty response | Return score=0.0 (no uncertainty) |
| Single token response | Skip self-consistency, use token NLL only |
| Model not available | Raise `UQLMError` with clear message |
| n_samples=0 | Return default score with metadata |

### 9.2 CLAP Probe Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Hidden states shape mismatch | Reshape or raise `ProbeError` |
| Layer index out of range | Clamp to valid range |
| Model not supported | Fall back to logprobs-based estimation |
| Untrained probe | Raise `ProbeNotFittedError` |
| Very short sequences | Pad or skip probe |

### 9.3 MetaQA Edge Cases

| Edge Case | Handling |
|-----------|----------|
| No baseline set | Use uniform distribution as baseline |
| Unknown tokens in current | Apply smoothing, add to KL calculation |
| Empty token list | Return drift_score=0.0 |
| Single token | Return drift_score=0.0 (insufficient data) |
| Baseline distribution empty | Initialize with current distribution |

### 9.4 Gap Detector Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Unknown language | Skip AST analysis, use regex only |
| Malformed code | Report parse error as INFO finding |
| Very large file | Stream parse, limit findings |
| Binary file | Skip with warning |
| Empty code | Return empty findings |

### 9.5 Unified Score Edge Cases

| Edge Case | Handling |
|-----------|----------|
| All components missing | Raise `ScoreComputationError` |
| Score out of [0,1] range | Clamp to valid range |
| NaN score | Replace with 0.5 (maximum uncertainty) |
| Weight sum != 1.0 | Auto-normalize weights |
| Unknown component | Ignore with warning |

### 9.6 Calibration Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Insufficient data (<100) | Raise `DataInsufficientError` |
| All same label | Skip calibration, return original |
| Perfect predictions | Return score as-is |
| Extreme scores (0 or 1) | Apply epsilon smoothing |

---

## Chapter 10: Performance Considerations

### 10.1 Computational Complexity

| Component | Time Complexity | Space Complexity |
|-----------|----------------|-----------------|
| Semantic Entropy | O(n·m·l) | O(n·m) |
| Self-Consistency | O(n·k·l) | O(k) |
| Token NLL | O(l·V) | O(V) |
| CLAP Probe | O(l·d) | O(d) |
| MetaQA | O(l·logV) | O(V) |
| Gap Detector | O(l) | O(l) |
| Unified Score | O(1) | O(1) |

Where:
- n = number of samples
- m = embedding dimension
- l = sequence length
- k = number of self-consistency samples
- d = hidden dimension
- V = vocabulary size

### 10.2 Caching Strategy

```
┌─────────────────────────────────────────────────────┐
│ Cache Key Format                                     │
├─────────────────────────────────────────────────────┤
│ uqlm:{model_name}:{hash(prompt)}:{hash(response)}   │
│ probe:{probe_path}:{hash(hidden_states)}           │
│ metaqa:{baseline_version}:{hash(tokens)}            │
└─────────────────────────────────────────────────────┘

Cache TTL:
- UQLM scores: 1 hour
- Probe predictions: 24 hours
- MetaQA drift: 10 minutes
```

### 10.3 Batch Processing

```python
async def batch_quantify(
    inputs: List[UncertaintyInput],
    max_concurrent: int = 5,
) -> List[UncertaintyOutput]:
    """Process multiple inputs concurrently.

    Args:
        inputs: List of inputs to process.
        max_concurrent: Maximum concurrent API calls.

    Returns:
        List of uncertainty outputs in same order.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(input):
        async with semaphore:
            return await gateway.async_quantify(input)

    tasks = [process_one(inp) for inp in inputs]
    return await asyncio.gather(*tasks)
```

### 10.4 Memory Optimization

| Technique | Applicable Component | Savings |
|-----------|---------------------|---------|
| LRU Cache | All components | ~70% redundant computation |
| Streaming parse | Gap Detector | ~80% memory for large files |
| Pruned hidden states | CLAP Probe | ~50% memory |
| Quantized probes | TinyLoRA | ~75% model size |
| Lazy loading | All | Startup time |

---

## Chapter 11: Testing Strategy

### 11.1 Unit Tests

| Module | Test Cases |
|--------|------------|
| ensemble.py | Test each scorer independently, test weight normalization |
| clap_probe.py | Test fit/predict cycle, test unsupported model error |
| tinylora.py | Test LoRA application formula, test parameter count |
| metaqa.py | Test KL divergence calculation, test baseline update |
| gap_detector.py | Test each rule type, test severity ordering |
| uncertainty_score.py | Test weight redistribution, test threshold decisions |
| confidence_calibrator.py | Test Platt scaling formula, test ECE calculation |

### 11.2 Integration Tests

```
Test: Full pipeline with known hallucination
Steps:
  1. Generate response with known hallucination
  2. Run through UncertaintyGateway
  3. Verify decision == "HITL" or "ROUND_2"
  4. Verify component scores reflect hallucination

Test: Graceful degradation (no hidden states)
Steps:
  1. Provide input without hidden_states
  2. Run through UncertaintyGateway
  3. Verify CLAP score is None/missing
  4. Verify final decision still computed
  5. Verify weights redistributed correctly
```

### 11.3 Benchmark Tests

```python
@pytest.mark.benchmark
def test_latency_budget():
    """Test that pipeline completes within latency budget."""
    target_latency_ms = {
        'uqlm': 2000,
        'clap': 500,
        'metaqa': 100,
        'gap': 200,
        'unified': 10,
    }

    for component, budget in target_latency_ms.items():
        elapsed = measure_time(component_processing)
        assert elapsed < budget, f"{component} exceeded budget: {elapsed}ms"
```

---

## Appendix A: Error Codes

| Code | Name | Description |
|------|------|-------------|
| UQLM-001 | API_TIMEOUT | Model API call timed out |
| UQLM-002 | INVALID_RESPONSE | Model returned malformed response |
| UQLM-003 | SAMPLING_ERROR | Temperature sampling failed |
| PROBE-001 | MODEL_UNSUPPORTED | Model type not supported by probe |
| PROBE-002 | NOT_FITTED | Probe.predict() called before fit() |
| PROBE-003 | INVALID_HIDDEN_STATES | Hidden states shape/dtype invalid |
| LORA-001 | TRAINING_DIVERGENCE | Loss increased beyond tolerance |
| LORA-002 | INSUFFICIENT_DATA | Training data below minimum |
| METAQA-001 | NO_BASELINE | Baseline distribution not set |
| METAQA-002 | EMPTY_TOKENS | Token list is empty |
| GAP-001 | PARSE_ERROR | Failed to parse code |
| GAP-002 | LANGUAGE_UNSUPPORTED | Language not supported |
| SCORE-001 | ALL_COMPONENTS_MISSING | No scores available |
| SCORE-002 | INVALID_WEIGHTS | Weight dict invalid |
| CALIB-001 | INSUFFICIENT_CALIB_DATA | Calibration data below 100 samples |
| CALIB-002 | ALL_SAME_LABEL | Cannot calibrate with single class |

---

**[END OF ARCHITECTURE.md — 2192 lines]**
