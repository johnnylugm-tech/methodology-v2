# Risk Register — Feature #7: UQLM + Activation Probes

## 1. Risk Assessment Summary

| Category | High | Medium | Low |
|----------|------|--------|-----|
| Technical | 2 | 5 | 3 |
| Operational | 1 | 2 | 1 |
| External | 1 | 2 | 0 |

**Total Risks:** 12 (High: 4, Medium: 9, Low: 3 — overlaps counted once per category)

---

## 2. Technical Risks

### R-01: External API Failures
- **Severity**: High
- **Likelihood**: High
- **Impact**: UQLM ensemble cannot score responses
- **Mitigation**: Fallback to local scorers (semantic_entropy, semantic_density)
- **Owner**: Layer 2 LLM Cascade

### R-02: Rate Limiting
- **Severity**: Medium
- **Likelihood**: Medium
- **Impact**: Scoring requests throttled, delayed responses
- **Mitigation**: Exponential backoff with jitter
- **Owner**: Layer 2 LLM Cascade

### R-03: Model Response Format Changes
- **Severity**: Medium
- **Likelihood**: Low
- **Impact**: Parsing failures in ensemble scorer
- **Mitigation**: Schema validation on all model outputs
- **Owner**: Layer 2 LLM Cascade

### R-04: sklearn Unavailable
- **Severity**: High
- **Likelihood**: Low
- **Impact**: CLAP probe cannot train
- **Mitigation**: Graceful degradation with warning
- **Owner**: Feature #7 (CLAP Probe)

### R-05: Model Hidden States Extraction Failure
- **Severity**: High
- **Likelihood**: Medium
- **Impact**: CLAP probe training pipeline breaks
- **Mitigation**: Clear error messages with diagnostic hints
- **Owner**: Feature #7 (CLAP Probe)

### R-06: torch Not Available
- **Severity**: High
- **Likelihood**: Low
- **Impact**: TinyLoRA training disabled
- **Mitigation**: Optional dependency declaration; feature-flagged import
- **Owner**: Feature #7 (TinyLoRA)

### R-07: Training Instability
- **Severity**: Medium
- **Likelihood**: Medium
- **Impact**: Degraded fine-tuning quality or divergence
- **Mitigation**: Early stopping, gradient clipping, loss monitoring
- **Owner**: Feature #7 (TinyLoRA)

### R-08: Empty Baseline in Drift Detection
- **Severity**: Medium
- **Likelihood**: Medium
- **Impact**: MetaQA drift detection cannot compute delta
- **Mitigation**: Auto-initialize baseline on first N outputs
- **Owner**: Feature #7 (MetaQA Drift)

### R-09: Distribution Shift False Positives
- **Severity**: Low
- **Likelihood**: Medium
- **Impact**: Spurious drift alerts, noise in monitoring
- **Mitigation**: Adaptive thresholds with cooldown windows
- **Owner**: Feature #7 (MetaQA Drift)

### R-10: Large Codebase Scanning Slow
- **Severity**: Low
- **Likelihood**: Medium
- **Impact**: Gap detection takes excessive time on large repos
- **Mitigation**: Parallel processing with worker pool
- **Owner**: Feature #7 (Gap Detection)

### R-11: AST Parsing Errors
- **Severity**: Low
- **Likelihood**: Low
- **Impact**: Certain files skipped, partial coverage
- **Mitigation**: Skip problematic files with logged warning
- **Owner**: Feature #7 (Gap Detection)

### R-12: Weight Normalization Issues
- **Severity**: High
- **Likelihood**: Low
- **Impact**: Uncertainty scores out of range, bad gating decisions
- **Mitigation**: Validation pass + clamping post-compute
- **Owner**: Feature #7 (Uncertainty Score)

### R-13: Threshold Miscalibration
- **Severity**: Medium
- **Likelihood**: Medium
- **Impact**: False accept or reject rates deviate from target
- **Mitigation**: User-configurable thresholds with live preview
- **Owner**: Feature #7 (Uncertainty Score)

### R-14: Insufficient Calibration Data
- **Severity**: Medium
- **Likelihood**: High
- **Impact**: Confidence calibration curve poorly fitted
- **Mitigation**: Platt scaling with fallback to temperature scaling
- **Owner**: Feature #7 (Confidence Calibration)

### R-15: Calibration Drift Over Time
- **Severity**: Medium
- **Likelihood**: Medium
- **Impact**: Calibration accuracy degrades as model behavior shifts
- **Mitigation**: Periodic recalibration on recent production samples
- **Owner**: Feature #7 (Confidence Calibration)

---

## 3. Risk Response Strategies

| Strategy | Count |
|----------|-------|
| Avoid | 2 |
| Mitigate | 8 |
| Transfer | 0 |
| Accept | 4 |

### Avoid
- R-10: Parallel processing eliminates sequential bottleneck
- R-12: Validation + clamping prevents out-of-range scores

### Mitigate
- R-01: Fallback scorers maintain partial functionality
- R-02: Exponential backoff reduces throttling impact
- R-03: Schema validation catches format changes early
- R-04: Graceful degradation keeps system alive
- R-05: Clear error messages accelerate debugging
- R-06: Optional dependency prevents hard install failure
- R-07: Training safeguards prevent divergence
- R-08: Auto-initialization resolves empty baseline issue

### Transfer
- (None currently identified)

### Accept
- R-09: False positive cost is low; monitoring overhead acceptable
- R-11: AST parsing errors are rare; file-level skip is sufficient
- R-13: User-configurable thresholds shift responsibility to operator
- R-15: Periodic recalibration is standard practice; drift cost accepted

---

## 4. Monitoring & Review

- **Weekly**: Review calibration metrics (ECE, NLL) for drift
- **Monthly**: Adjust uncertainty thresholds based on production false accept/reject rates
- **Quarterly**: Architecture review — assess whether UQLM ensemble composition remains optimal
- **Ongoing**: Log all fallback activations (API failures, sklearn/torch unavailability) to detect patterns

---

## 5. Risk Matrix (Heat Map)

| Likelihood → | Low | Medium | High |
|-------------|-----|--------|------|
| **Impact Low** | R-09, R-10, R-11 | R-02, R-07, R-09, R-10, R-13, R-15 | — |
| **Impact Medium** | R-03, R-11 | R-02, R-07, R-08, R-13, R-14, R-15 | R-01, R-05 |
| **Impact High** | R-04, R-06, R-12 | R-05 | R-01, R-04, R-06, R-12 |

---

## 6. Key Watch Items

1. **API failure cascade** — If OpenAI AND Anthropic both fail, ensemble is down to 2 local scorers. Monitor fallback activation rate.
2. **Calibration data sufficiency** — CLAP probe needs ≥500 samples for reliable Platt scaling. Track sample count per model.
3. **Training divergence** — TinyLoRA loss should converge within 10 epochs. Alert if loss increases for 3 consecutive steps.
