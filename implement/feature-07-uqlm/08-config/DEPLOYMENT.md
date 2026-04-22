# Deployment Guide — Feature #7: UQLM + Activation Probes

**Version:** 1.0  
**Date:** 2026-04-19  
**Feature:** Layer 3: UQLM + Activation Probes (Hallucination Detection)

---

## 1. System Requirements

### Runtime Environment

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11 |
| RAM | 4GB | 8GB |
| Storage | 100MB | 500MB |
| GPU | Optional | CUDA 11.8+ (for TinyLoRA training) |

### Dependencies

| Package | Version | Required | Purpose |
|---------|---------|----------|---------|
| numpy | >= 1.24 | Yes | Numerical operations |
| scikit-learn | >= 1.3 | Yes | CLAP probe (LogisticRegression) |
| torch | >= 2.0 | Optional | TinyLoRA training |
| transformers | >= 4.30 | Optional | Hidden states extraction |
| scipy | >= 1.11 | Optional | KL divergence in MetaQA |
| pandas | - | Optional | Data analysis |

---

## 2. Installation

### Option A: pip install

```bash
pip install methodology-v2[detection]
```

### Option B: From source

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2
pip install -e .
```

### Option C: Install detection extras only

```bash
pip install numpy scikit-learn scipy
pip install torch transformers  # optional
```

---

## 3. Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UQLM_WEIGHT_ALPHA` | 0.5 | UQLM ensemble weight |
| `UQLM_WEIGHT_BETA` | 0.3 | CLAP probe weight |
| `UQLM_WEIGHT_GAMMA` | 0.2 | MetaQA drift weight |
| `CLAP_THRESHOLD` | 0.5 | Probe classification threshold |
| `METAQA_WINDOW` | 100 | Drift detection window size |
| `UQLM_N_SAMPLES` | 5 | Number of samples for self-consistency |
| `UQLM_TEMPERATURE` | 0.7 | Sampling temperature |
| `UQLM_MODEL` | gpt-3.5-turbo | Default model for scoring |

### Python Configuration

```python
from detection import EnsembleScorer, UncertaintyScoreCalculator

# Initialize ensemble scorer
ensemble = EnsembleScorer()

# Initialize unified score calculator
calc = UncertaintyScoreCalculator(
    ensemble_scorer=ensemble,
    alpha=0.5,   # UQLM weight
    beta=0.3,    # CLAP weight
    gamma=0.2,   # MetaQA weight
)
```

---

## 4. Usage Examples

### 4.1 Basic Uncertainty Scoring

```python
from detection import UncertaintyScoreCalculator, EnsembleScorer

# Initialize
ensemble = EnsembleScorer()
calc = UncertaintyScoreCalculator(
    ensemble_scorer=ensemble,
    alpha=0.5, beta=0.3, gamma=0.2
)

# Score a response
result = calc.compute(
    prompt="What is the capital of France?",
    response="The capital of France is Paris."
)
print(f"Decision: {result.decision}")
print(f"UAF Score: {result.score}")
print(f"Components: {result.components}")
```

### 4.2 CLAP Activation Probe

```python
from detection import ActivationProbe, ProbeConfig
import numpy as np

# Initialize probe
config = ProbeConfig(
    model_type="llama-3.3",
    layer_idx=-1,
    threshold=0.5
)
probe = ActivationProbe(config)

# Train on labeled data (hidden_states, label)
training_data = [
    (np.random.randn(4096), 0),  # non-hallucination
    (np.random.randn(4096), 1),  # hallucination
]
probe.fit(training_data)

# Predict
hidden_states = np.random.randn(4096)
result = probe.predict(hidden_states)
print(f"p(hallucinate): {result.p_hallucinate}")
```

### 4.3 TinyLoRA Training

```python
from detection import TinyLoRA, TinyLoRAConfig
import numpy as np

# Initialize
config = TinyLoRAConfig(hidden_dim=4096, rank=4, alpha=8.0)
lora = TinyLoRA(config)

# Training data: (hidden_state, label)
training_data = [
    (np.random.randn(4096), 0) for _ in range(100)
] + [
    (np.random.randn(4096), 1) for _ in range(100)
]

# Train
model, loss = lora.train(training_data)
print(f"Training loss: {loss}")
print(f"Metrics: {model.metrics}")
```

### 4.4 MetaQA Drift Detection

```python
from detection import MetaQADetector

# Initialize with baseline
detector = MetaQADetector(baseline={"the": 0.05, "is": 0.03})

# Update baseline
detector.update_baseline(["The quick brown fox", "Hello world"])

# Detect drift
result = detector.detect_drift(
    model_outputs=["Completely different text"],
    window_size=100
)
print(f"Drift score: {result.drift_score}")
print(f"Drifted tokens: {result.drifted_tokens}")
```

### 4.5 Gap Detection

```python
from detection import GapDetector, GapType

detector = GapDetector()

# Scan source code
findings = detector.scan(
    source_code=open("example.py").read(),
    file_path="example.py",
    gap_types=[GapType.HARDCODED_SECRETS, GapType.EMPTY_CATCH]
)

for finding in findings:
    print(f"[{finding.severity}] {finding.file_path}:{finding.line_number}")
    print(f"  {finding.description}")
```

### 4.6 Confidence Calibration

```python
from detection import ConfidenceCalibrator

calibrator = ConfidenceCalibrator(history_size=100)

# Calibrate
result = calibrator.calibrate(
    initial_confidence=0.9,
    actual_outcome=True,
    uqlm_uncertainty=0.2
)
print(f"Calibrated confidence: {result.calibrated_confidence}")
print(f"Calibration error: {result.calibration_error}")
print(f"Alert: {result.alert}")
```

---

## 5. Integration Points

### Layer 3 Integration

| Direction | Interface |
|-----------|-----------|
| **Input** | Layer 2 LLM responses (prompt, response, model_name, hidden_states) |
| **Output** | Uncertainty score + decision (PASS/ROUND_2/HITL) |
| **Feeds** | Layer 4 Output Verifier |

### Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                      LAYER 2: LLM Cascade                   │
│         (GPT-4 / Claude / Gemini routing)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              LAYER 3: UQLM + Activation Probes  ← HERE     │
│  ┌─────────────┬─────────────┬─────────────┬────────────┐ │
│  │ UQLM Ensemble│ CLAP Probe  │ MetaQA Drift│ Gap Detect│ │
│  └─────────────┴─────────────┴─────────────┴────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               LAYER 4: Output Verifier                       │
│              (quality gate, citation check)                 │
└─────────────────────────────────────────────────────────────┘
```

### Decision Thresholds

| Score Range | Decision | Action |
|-------------|----------|--------|
| < 0.2 | `PASS` | Proceed to next step |
| 0.2 – 0.5 | `ROUND_2` | Additional verification |
| > 0.5 | `HITL` | Human-in-the-loop review |

---

## 6. Monitoring

### Metrics to Track

| Metric | Target | Description |
|--------|--------|-------------|
| `calibration_error` | < 0.1 | Planner confidence alignment |
| `uaf_score_distribution` | — | Monitor for distribution drift |
| `hitl_rate` | < 10% | Human-in-the-loop trigger rate |
| `drift_score` | < 0.3 | Model output distribution drift |

### Health Checks

```bash
# Run detection module health check
python -c "from detection import EnsembleScorer, ActivationProbe, MetaQADetector; print('Detection module OK')"

# Verify all imports
python -c "from detection import UncertaintyScoreCalculator, ConfidenceCalibrator, GapDetector; print('All imports OK')"
```

### Prometheus Metrics (if integrated)

```
# HELP uqlm_uncertainty_score Current uncertainty score
# TYPE uqlm_uncertainty_score gauge
uqlm_uncertainty_score{source="uqlm"} 0.23

# HELP detection_hitl_total Human-in-the-loop triggers
# TYPE detection_hitl_total counter
detection_hitl_total 42

# HELP calibration_error Current calibration error
# TYPE calibration_error gauge
calibration_error 0.08
```

---

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| `ImportError: sklearn` | `pip install scikit-learn` |
| `ImportError: torch` | `pip install torch` (optional) |
| `ImportError: transformers` | `pip install transformers` (optional) |
| `MemoryError` | Reduce batch size or n_samples |
| `Timeout` | Increase `UQLM_TIMEOUT` env var |
| `BaselineNotFoundError` | Initialize MetaQADetector with baseline |
| `DataInsufficientError` | TinyLoRA requires >= 10 training samples |
| `ProbeError` | Check model_type is supported (llama-3.3, qwen-2.5) |

### Common Issues

**Q: CLAP probe returns same score for all inputs**  
A: Probe may not be trained. Ensure `fit()` was called with sufficient labeled data (>= 100 samples).

**Q: MetaQA drift score is always 0**  
A: Baseline not initialized. Call `update_baseline()` with representative outputs first.

**Q: TinyLoRA training diverges**  
A: Reduce learning rate (lr=0.0001) or increase alpha scaling.

**Q: Gap detection misses findings**  
A: Ensure source code is valid Python. Binary files are skipped automatically.

---

## 8. Rollback

### Rollback to previous version

```bash
# List available versions
pip index versions methodology-v2

# Install specific version
pip install methodology-v2==1.0.0

# Or from source
git checkout <previous-tag>
pip install -e .
```

### Disable detection module

If detection causes issues, disable by setting weights to zero:

```python
calc = UncertaintyScoreCalculator(alpha=0.0, beta=0.0, gamma=0.0)
```

---

## 9. File Structure

```
methodology-v2/
├── detection/
│   ├── __init__.py                 # Module exports
│   ├── uqlm_ensemble.py           # FR-U-1: UQLM Ensemble Scorer
│   ├── clap_probe.py               # FR-U-2: Activation Probe
│   ├── tinylora.py                 # FR-U-3: TinyLoRA Lightweight
│   ├── metaqa.py                   # FR-U-4: MetaQA Drift Detection
│   ├── gap_detector.py             # FR-U-5: Implementation Gap Detection
│   ├── uncertainty_score.py        # FR-U-6: Unified Uncertainty Score
│   ├── confidence_calibrator.py    # FR-U-7: Confidence Calibration
│   ├── data_models.py              # Shared dataclasses
│   ├── enums.py                    # Type definitions
│   └── exceptions.py               # Custom exceptions
└── implement/
    └── feature-07-uqlm/
        ├── 01-spec/SPEC.md
        ├── 02-architecture/ARCHITECTURE.md
        ├── 03-implement/detection/  # Source
        ├── 04-tests/                 # Test suite
        └── 08-deploy/DEPLOYMENT.md   # This file
```

---

## 10. API Reference

### Core Classes

| Class | File | Purpose |
|-------|------|---------|
| `EnsembleScorer` | uqlm_ensemble.py | UQLM ensemble scoring |
| `ActivationProbe` | clap_probe.py | CLAP activation probes |
| `TinyLoRA` | tinylora.py | Lightweight LoRA probes |
| `MetaQADetector` | metaqa.py | Drift detection |
| `GapDetector` | gap_detector.py | Implementation gap scanning |
| `UncertaintyScoreCalculator` | uncertainty_score.py | Unified scoring |
| `ConfidenceCalibrator` | confidence_calibrator.py | Planner calibration |

### Exceptions

| Exception | Purpose |
|-----------|---------|
| `UQLMError` | UQLM ensemble failures |
| `ProbeError` | CLAP probe failures |
| `DataInsufficientError` | Insufficient training data |
| `BaselineNotFoundError` | MetaQA baseline not initialized |
| `CalibrationError` | Calibration failures |
| `GapDetectionError` | Gap detection failures |

---

**END OF DEPLOYMENT.md**
