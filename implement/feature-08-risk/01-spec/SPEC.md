# Feature #8: 8-Dimensional Risk Assessment Engine

## Specification Document

**Version:** 1.0  
**Created:** 2026-04-19  
**Feature ID:** FR-R (Risk Assessment)  
**Implementation:** `risk_assessment_engine.py`  
**Location:** `implement/feature-08-risk/03-implement/`

---

## 1. Overview

### 1.1 Purpose

The Risk Assessment Engine provides comprehensive, multi-dimensional risk evaluation for agent-based system decisions. It integrates with the existing methodology-v2 framework to provide real-time risk scoring, decision logging, confidence calibration, and effort tracking.

### 1.2 Scope

This specification covers:
- 8-dimensional risk assessment model
- Decision Log system (YAML-based)
- Confidence Calibration with UQLM integration
- Effort Metrics tracking
- Alerting and monitoring infrastructure

### 1.3 Dependencies

- `uncertainty_quantification.py` (UQLM) — provides uncertainty quantification
- `devil_advocate.py` — provides adversarial review integration
- `config.py` — provides threshold and configuration management

---

## 2. Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Risk Assessment Engine                       │
├──────────────┬──────────────┬───────────────┬────────────────┤
│   Decision  │  Confidence  │    Effort     │      8D        │
│     Log     │  Calibration  │   Metrics     │     Risk       │
│   (YAML)    │   (UQLM)     │   (Agent)     │   Engine       │
└──────────────┴──────────────┴───────────────┴────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   Alert Manager   │
                    └───────────────────┘
```

### 2.2 Data Flow

```
Agent Decision → Decision Log → Risk Engine → 8D Assessment
                    │                            │
                    ▼                            ▼
              Confidence                  Risk Scores
              Calibration                  + Alerts
                    │
                    ▼
              UQLM Integration
```

---

## 3. 8-Dimensional Risk Model

### 3.1 Dimension Definitions

| Dimension | ID | Description | Weight Range |
|-----------|-----|-------------|--------------|
| Data Privacy Risk | D1 | Risk of unauthorized data exposure or PII leakage | 0.0–1.0 |
| Injection Risk | D2 | Risk of prompt injection, code injection, or malicious input | 0.0–1.0 |
| Cost/Token Risk | D3 | Risk of excessive token consumption or cost overrun | 0.0–1.0 |
| UAF/CLAP Risk | D4 | Risk of Unbounded Agent Frameworks or Cumulative LLM Agentic Processing | 0.0–1.0 |
| Memory Poisoning Risk | D5 | Risk of corrupted or manipulated agent memory/context | 0.0–1.0 |
| Cross-Agent Leak Risk | D6 | Risk of information leakage between agents | 0.0–1.0 |
| Latency/SLO Risk | D7 | Risk of exceeding response time targets or SLO breaches | 0.0–1.0 |
| Compliance Risk | D8 | Risk of regulatory or policy violations | 0.0–1.0 |

### 3.2 Risk Score Calculation

**Composite Risk Score (CRS):**

```
CRS = Σ(w_i × r_i) / Σ(w_i)
```

Where:
- `w_i` = weight for dimension `i` (configurable per context)
- `r_i` = raw risk score for dimension `i`

**Risk Level Thresholds:**

| Level | Score Range | Action |
|-------|-------------|--------|
| CRITICAL | 0.8 – 1.0 | Immediate halt + alert |
| HIGH | 0.6 – 0.8 | Block execution + alert |
| MEDIUM | 0.4 – 0.6 | Warning + logging |
| LOW | 0.0 – 0.4 | Acceptable, monitor |

### 3.3 Dimension-Specific Assessment

#### D1: Data Privacy Risk [FR-R-1]

**Assessment Factors:**
- Presence of PII (Personally Identifiable Information)
- Data classification level
- Encryption status
- Access control maturity

**Scoring Formula:**
```python
def assess_privacy_risk(data_context: dict) -> float:
    pii_score = detect_pii(data_context) * 0.4
    classification_score = get_classification_score(data_context) * 0.3
    encryption_score = (1 - is_encrypted(data_context)) * 0.2
    access_score = evaluate_access_controls(data_context) * 0.1
    return pii_score + classification_score + encryption_score + access_score
```

#### D2: Injection Risk [FR-R-2]

**Assessment Factors:**
- User input sanitization
- Code execution scope
- External content rendering
- Dynamic prompt construction

**Scoring Formula:**
```python
def assess_injection_risk(input_context: dict) -> float:
    sanitization_score = (1 - sanitize_inputs(input_context)) * 0.35
    execution_scope_score = evaluate_execution_scope(input_context) * 0.25
    external_content_score = detect_external_content(input_context) * 0.25
    dynamic_prompt_score = measure_dynamic_prompt_complexity(input_context) * 0.15
    return sanitization_score + execution_scope_score + external_content_score + dynamic_prompt_score
```

#### D3: Cost/Token Risk [FR-R-3]

**Assessment Factors:**
- Estimated token budget vs. actual usage
- Context window utilization
- Batch vs. streaming cost comparison
- Retry/redundancy overhead

**Scoring Formula:**
```python
def assess_cost_risk(usage_context: dict) -> float:
    budget_ratio = actual_tokens / budget_tokens
    window_utilization = context_used / context_limit
    redundancy_overhead = retry_cost / total_cost
    batch_efficiency = (1 - batch_waste / total_tokens) * 0.2
    
    if budget_ratio > 1.0:
        return 1.0
    return min(1.0, budget_ratio * 0.4 + window_utilization * 0.3 + 
               redundancy_overhead * 0.1 + batch_efficiency)
```

#### D4: UAF/CLAP Risk [FR-R-4]

**Assessment Factors:**
- Recursive agent depth
- Cumulative context window growth
- Loop detection (same agent called >N times)
- Frame boundary enforcement

**Scoring Formula:**
```python
def assess_uaf_risk(agent_context: dict) -> float:
    depth_score = min(1.0, agent_depth / MAX_AGENT_DEPTH) * 0.3
    context_growth_score = measure_context_growth_rate(agent_context) * 0.3
    loop_score = detect_loop(agent_context) * 0.25
    boundary_score = evaluate_frame_boundaries(agent_context) * 0.15
    return depth_score + context_growth_score + loop_score + boundary_score
```

#### D5: Memory Poisoning Risk [FR-R-5]

**Assessment Factors:**
- Memory source verification
- Content authenticity checks
- Tampering detection
- Historical consistency validation

**Scoring Formula:**
```python
def assess_poisoning_risk(memory_context: dict) -> float:
    source_verification = verify_memory_sources(memory_context) * 0.3
    authenticity_score = check_content_authenticity(memory_context) * 0.3
    tampering_score = detect_tampering(memory_context) * 0.25
    consistency_score = validate_historical_consistency(memory_context) * 0.15
    return source_verification + authenticity_score + tampering_score + consistency_score
```

#### D6: Cross-Agent Leak Risk [FR-R-6]

**Assessment Factors:**
- Agent isolation level
- Shared state exposure
- Message sanitization between agents
- Authorization checks on inter-agent calls

**Scoring Formula:**
```python
def assess_leak_risk(agent_interaction: dict) -> float:
    isolation_score = (1 - agent_isolation_level) * 0.3
    shared_state_score = measure_shared_state_exposure(agent_interaction) * 0.3
    message_sanitization_score = (1 - sanitize_inter_agent_messages()) * 0.25
    auth_check_score = (1 - has_authorization_checks()) * 0.15
    return isolation_score + shared_state_score + message_sanitization_score + auth_check_score
```

#### D7: Latency/SLO Risk [FR-R-7]

**Assessment Factors:**
- Historical latency vs. SLO target
- Current queue depth
- Timeout configuration
- Degradation detection

**Scoring Formula:**
```python
def assess_latency_risk(latency_context: dict) -> float:
    slo_violation_score = latency / SLO_target if latency > SLO_target else 0
    queue_score = min(1.0, queue_depth / MAX_QUEUE) * 0.25
    timeout_score = (1 - configure_timeouts()) * 0.2
    degradation_score = detect_performance_degradation(latency_context) * 0.15
    return min(1.0, slo_violation_score * 0.4 + queue_score + timeout_score + degradation_score)
```

#### D8: Compliance Risk [FR-R-8]

**Assessment Factors:**
- Regulatory framework alignment (GDPR, CCPA, SOC2, etc.)
- Policy violation detection
- Audit trail completeness
- Data residency requirements

**Scoring Formula:**
```python
def assess_compliance_risk(compliance_context: dict) -> float:
    regulatory_score = (1 - check_regulatory_alignment()) * 0.35
    policy_violation_score = detect_policy_violations(compliance_context) * 0.30
    audit_trail_score = (1 - audit_trail_completeness()) * 0.20
    residency_score = check_data_residency_requirements(compliance_context) * 0.15
    return regulatory_score + policy_violation_score + audit_trail_score + residency_score
```

---

## 4. Decision Log System

### 4.1 Purpose

The Decision Log records all significant Planner decisions in a structured YAML format for auditability, review, and improvement.

### 4.2 Schema [FR-R-9]

```yaml
planner_decision_trace:
  decision_id: string          # Unique identifier (e.g., "arch-001", "api-20260419-003")
  timestamp: ISO8601           # When decision was made
  agent_id: string             # Which agent made the decision
  task_id: string              # Associated task
  
  choice: string               # The chosen option
  alternatives_considered:
    - option: string           # Alternative option
      rejection_reason: string # Why it was rejected (if applicable)
  
  confidence_score: float       # Initial confidence (0.0–10.0)
  actual_outcome: float        # Post-hoc outcome score (0.0–10.0), filled later
  confidence_calibrated: bool   # Whether calibration was performed
  
  effort_minutes: int          # Time spent on this decision
  tool_calls: int             # Number of tool calls made
  tokens_consumed: int        # Token count for this decision
  
  key_assumptions:
    - assumption: string
      verified: bool
      verification_method: string
  
  uncertainties:
    - uncertainty: string
      impact: low|medium|high
      mitigation: string
  
  evidence_hash: string        # SHA-256 of decision context
  evidence_payload: object    # Full context for reproducibility
  
  reviewed_by: string          # "devil_advocate" or agent_id
  review_round: int           # Which review round this is
  review_notes: string        # Notes from reviewer
  
  metadata:
    model_version: string
    session_id: string
    parent_decision_id: string # Link to parent decision if sub-decision
```

### 4.3 Decision ID Generation

Format: `{category}-{YYYYMMDD}-{sequence}`

Examples:
- `arch-20260419-001`
- `api-20260419-002`
- `test-20260419-003`

### 4.4 Evidence Hash Calculation

```python
def calculate_evidence_hash(decision_payload: dict) -> str:
    canonical_payload = json.dumps(decision_payload, sort_keys=True)
    return sha256(canonical_payload.encode()).hexdigest()
```

### 4.5 Storage

- **Primary:** `{workspace}/memory/decisions/{YYYY}/{MM}/{decision_id}.yaml`
- **Index:** `{workspace}/memory/decisions/index.yaml` (append-only log)

---

## 5. Confidence Calibration

### 5.1 Purpose

Confidence Calibration ensures that the system's confidence scores match actual outcomes, enabling better decision-making and calibration error detection.

### 5.2 Integration with UQLM [FR-R-10]

The Confidence Calibration module integrates with the Uncertainty Quantification Layer (UQLM) to:

1. **Uncertainty Propagation:** Map UQLM uncertainty metrics to confidence adjustments
2. **Calibration Error Detection:** Compare predicted confidence against actual outcomes
3. **Adaptive Threshold Adjustment:** Update risk thresholds based on calibration history

### 5.3 Calibration Formula

**Calibration Error:**
```python
calibration_error = abs(initial_confidence - actual_outcome)
```

**Calibration Status:**
- **Well-Calibrated:** `calibration_error ≤ 0.2`
- **Moderately Miscalibrated:** `0.2 < calibration_error ≤ 0.3`
- **Miscalibrated:** `calibration_error > 0.3`

**Alert Trigger:**
```python
if calibration_error > 0.3:
    alert("confidence_mismatch", decision_id=decision_id, 
          initial=initial_confidence, actual=actual_outcome)
```

### 5.4 Confidence Adjustment

```python
def calibrate_confidence(
    initial_confidence: float,
    uqlm_uncertainty: float,
    historical_calibration_error: float
) -> float:
    """
    Adjust initial confidence based on UQLM uncertainty and historical calibration.
    
    Args:
        initial_confidence: Original confidence score (0.0–10.0)
        uqlm_uncertainty: Uncertainty score from UQLM (0.0–1.0)
        historical_calibration_error: Average calibration error from past decisions
    
    Returns:
        Adjusted confidence score
    """
    uncertainty_penalty = uqlm_uncertainty * 0.5
    calibration_penalty = historical_calibration_error * 0.3
    
    adjusted = initial_confidence - (uncertainty_penalty + calibration_penalty) * 10
    return max(0.0, min(10.0, adjusted))
```

### 5.5 UQLM Integration Interface

```python
class UQLMIntegration:
    """Interface for UQLM uncertainty integration."""
    
    def get_uncertainty_score(self, context: dict) -> float:
        """
        Get uncertainty score from UQLM.
        Returns value in range [0.0, 1.0] where 0 = certain, 1 = highly uncertain.
        """
        pass
    
    def get_uncertainty_breakdown(self, context: dict) -> dict:
        """
        Get detailed uncertainty breakdown by category.
        """
        pass
    
    def get_calibration_data(self, decision_id: str) -> dict:
        """
        Retrieve historical calibration data for a specific decision.
        """
        pass
```

---

## 6. Effort Metrics

### 6.1 Purpose

Effort Metrics track the actual resources consumed by each agent during task execution, enabling cost analysis, performance optimization, and output quality assessment.

### 6.2 Metrics Schema [FR-R-11]

```python
effort_metrics = {
    "agent_id": str,              # Agent identifier (e.g., "planner", "coder")
    "task_id": str,               # Associated task ID
    "session_id": str,            # Session for correlation
    
    # Time Metrics
    "time_spent_minutes": float,  # Wall-clock time spent
    
    # Resource Metrics
    "tool_calls": int,            # Total tool invocations
    "tokens_consumed": int,      # Input + output tokens
    
    # Iteration Metrics
    "iteration_count": int,       # Number of feedback loops
    "ab_round_triggered": bool,  # Whether AB test was needed
    
    # Quality Metrics
    "output_quality_score": float, # Post-hoc quality assessment (0.0–1.0)
    
    # Error Metrics
    "error_count": int,           # Errors encountered
    "retry_count": int,           # Retries performed
    
    # Context Metrics
    "context_window_usage": float, # Percentage of context used
    "memory_references": int,     # Memory read/write operations
    
    # Timestamps
    "started_at": ISO8601,
    "completed_at": ISO8601,
}
```

### 6.3 Collection Interface

```python
class EffortTracker:
    """Tracks and records agent effort metrics."""
    
    def start_tracking(self, agent_id: str, task_id: str) -> str:
        """
        Start tracking for an agent/task.
        Returns tracking_id for later reference.
        """
        pass
    
    def record_tool_call(self, tracking_id: str, tool_name: str, duration_ms: float):
        """Record individual tool call."""
        pass
    
    def record_token_usage(self, tracking_id: str, input_tokens: int, output_tokens: int):
        """Record token consumption."""
        pass
    
    def finish_tracking(self, tracking_id: str, quality_score: float = None):
        """Finalize tracking and compute metrics."""
        pass
    
    def get_metrics(self, tracking_id: str) -> dict:
        """Retrieve collected metrics."""
        pass
```

### 6.4 Aggregation Functions

```python
def aggregate_effort_metrics(task_id: str) -> dict:
    """
    Aggregate effort metrics across all agents for a task.
    """
    metrics = load_metrics_for_task(task_id)
    
    return {
        "total_time_minutes": sum(m.time_spent_minutes for m in metrics),
        "total_tool_calls": sum(m.tool_calls for m in metrics),
        "total_tokens": sum(m.tokens_consumed for m in metrics),
        "total_iterations": sum(m.iteration_count for m in metrics),
        "avg_quality_score": mean(m.output_quality_score for m in metrics),
        "agents_involved": [m.agent_id for m in metrics],
        "ab_rounds_triggered": sum(1 for m in metrics if m.ab_round_triggered),
    }
```

---

## 7. Risk Assessment Engine API

### 7.1 Core Interface [FR-R-12]

```python
class RiskAssessmentEngine:
    """
    Main risk assessment engine providing 8-dimensional risk evaluation.
    """
    
    def __init__(self, config: RiskConfig):
        """
        Initialize with configuration.
        
        Args:
            config: RiskConfig object with thresholds, weights, and settings
        """
        self.config = config
        self.decision_log = DecisionLog()
        self.confidence_calibrator = ConfidenceCalibrator()
        self.effort_tracker = EffortTracker()
        self.uqlm_integration = UQLMIntegration()
    
    def assess_risk(
        self,
        context: dict,
        dimensions: List[str] = None
    ) -> RiskAssessmentResult:
        """
        Perform risk assessment on the given context.
        
        Args:
            context: Assessment context with relevant data
            dimensions: Optional list of specific dimensions to assess.
                       If None, all 8 dimensions are assessed.
        
        Returns:
            RiskAssessmentResult with scores, alerts, and recommendations
        """
        pass
    
    def log_decision(
        self,
        decision: DecisionInput
    ) -> str:
        """
        Log a planner decision to the decision log.
        
        Returns:
            decision_id: Unique identifier for the logged decision
        """
        pass
    
    def calibrate_confidence(
        self,
        decision_id: str,
        actual_outcome: float
    ) -> CalibrationResult:
        """
        Perform post-hoc confidence calibration.
        
        Args:
            decision_id: The decision to calibrate
            actual_outcome: The actual outcome score (0.0–10.0)
        
        Returns:
            CalibrationResult with adjusted scores and alerts
        """
        pass
    
    def track_effort(
        self,
        agent_id: str,
        task_id: str
    ) -> str:
        """
        Start effort tracking for an agent/task.
        
        Returns:
            tracking_id for later reference
        """
        pass
    
    def get_composite_risk_score(
        self,
        assessment: RiskAssessmentResult
    ) -> float:
        """
        Calculate composite risk score from dimension scores.
        
        Args:
            assessment: Completed risk assessment
        
        Returns:
            Composite risk score (0.0–1.0)
        """
        pass
```

### 7.2 RiskAssessmentResult

```python
@dataclass
class RiskAssessmentResult:
    assessment_id: str
    timestamp: datetime
    
    # Individual dimension scores
    dimension_scores: Dict[str, float]  # { "D1": 0.3, "D2": 0.7, ... }
    
    # Composite score
    composite_score: float
    
    # Risk level
    risk_level: RiskLevel  # CRITICAL, HIGH, MEDIUM, LOW
    
    # Alerts triggered
    alerts: List[Alert]
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    dimensions_assessed: List[str]
    assessment_duration_ms: float
```

### 7.3 Usage Example

```python
# Initialize engine
config = RiskConfig(
    thresholds={
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
    },
    dimension_weights={
        "D1": 1.0,  # Data Privacy
        "D2": 1.2,  # Injection (higher weight)
        "D3": 0.8,  # Cost
        "D4": 1.0,  # UAF/CLAP
        "D5": 1.1,  # Memory Poisoning (higher)
        "D6": 1.0,  # Cross-Agent Leak
        "D7": 0.9,  # Latency
        "D8": 1.0,  # Compliance
    }
)
engine = RiskAssessmentEngine(config)

# Assess risk
context = {
    "data": user_provided_data,
    "agent_interactions": current_agents,
    "memory_state": current_memory,
    "compliance_context": regulatory_requirements,
}
result = engine.assess_risk(context)

# Log decision
decision = DecisionInput(
    choice="Use cached memory for context",
    alternatives=["Fresh fetch from API"],
    confidence_score=7.5,
    effort_minutes=15,
    context=context
)
decision_id = engine.log_decision(decision)

# Track effort
tracking_id = engine.track_effort("planner", "task-123")
# ... agent does work ...
engine.effort_tracker.finish_tracking(tracking_id, quality_score=0.85)
```

---

## 8. Alert System

### 8.1 Alert Types [FR-R-13]

| Alert Type | Trigger Condition | Severity |
|------------|-------------------|----------|
| `confidence_mismatch` | Calibration error > 0.3 | HIGH |
| `risk_threshold_exceeded` | Any dimension score > threshold | Per dimension |
| `composite_risk_high` | Composite score > 0.6 | HIGH |
| `cost_overrun` | Actual cost > 1.1 × budget | MEDIUM |
| `uaf_depth_exceeded` | Agent depth > MAX_DEPTH | CRITICAL |
| `memory_tampering_detected` | Poisoning score > 0.7 | CRITICAL |
| `compliance_violation` | Compliance score > 0.5 | HIGH |
| `latency_slo_breach` | Latency > SLO × 1.2 | MEDIUM |

### 8.2 Alert Payload

```python
@dataclass
class Alert:
    alert_id: str
    alert_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    timestamp: datetime
    
    # Alert source
    source_dimension: str  # e.g., "D4" for UAF/CLAP
    decision_id: str  # Associated decision if applicable
    
    # Alert details
    message: str
    details: dict
    
    # Recommended action
    recommended_action: str
    
    # Acknowledgment
    acknowledged: bool
    acknowledged_by: str
    acknowledged_at: datetime
```

---

## 9. Configuration Schema

### 9.1 RiskConfig

```python
@dataclass
class RiskConfig:
    # Thresholds
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "critical": 0.8,
        "high": 0.6,
        "medium": 0.4,
        "low": 0.0,
    })
    
    # Dimension weights (default all 1.0)
    dimension_weights: Dict[str, float] = field(default_factory=lambda: {
        f"D{i}": 1.0 for i in range(1, 9)
    })
    
    # UQLM integration settings
    uqlm_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "uncertainty_threshold": 0.3,
        "auto_calibrate": True,
    })
    
    # Effort tracking settings
    effort_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "track_detailed": True,
        "quality_threshold": 0.7,
    })
    
    # Alert settings
    alert_settings: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,
        "notify_on_critical": True,
        "notify_on_high": True,
    })
    
    # Limits
    limits: Dict[str, int] = field(default_factory=lambda: {
        "max_agent_depth": 5,
        "max_context_window": 200000,
        "max_tokens_per_task": 500000,
        "max_execution_time_minutes": 60,
    })
```

---

## 10. File Structure

```
implement/feature-08-risk/
├── 01-spec/
│   └── SPEC.md                      # This specification
├── 02-tests/
│   ├── test_risk_engine.py
│   ├── test_decision_log.py
│   ├── test_confidence_calibration.py
│   └── test_effort_metrics.py
└── 03-implement/
    ├── __init__.py
    ├── risk_assessment_engine.py   # Main engine
    ├── decision_log.py             # Decision logging
    ├── confidence_calibration.py   # Confidence calibration
    ├── effort_tracker.py           # Effort metrics
    ├── dimensions/                  # Dimension-specific assessors
    │   ├── __init__.py
    │   ├── privacy.py
    │   ├── injection.py
    │   ├── cost.py
    │   ├── uaf_clap.py
    │   ├── memory_poisoning.py
    │   ├── cross_agent_leak.py
    │   ├── latency.py
    │   └── compliance.py
    ├── alert_manager.py             # Alert handling
    ├── config.py                    # Configuration
    └── uqlm_integration.py          # UQLM interface
```

---

## 11. Acceptance Criteria

### 11.1 Functional Requirements

- [ ] [FR-R-1] D1 (Data Privacy) assessment returns score 0.0–1.0
- [ ] [FR-R-2] D2 (Injection) assessment returns score 0.0–1.0
- [ ] [FR-R-3] D3 (Cost/Token) assessment returns score 0.0–1.0
- [ ] [FR-R-4] D4 (UAF/CLAP) assessment returns score 0.0–1.0
- [ ] [FR-R-5] D5 (Memory Poisoning) assessment returns score 0.0–1.0
- [ ] [FR-R-6] D6 (Cross-Agent Leak) assessment returns score 0.0–1.0
- [ ] [FR-R-7] D7 (Latency/SLO) assessment returns score 0.0–1.0
- [ ] [FR-R-8] D8 (Compliance) assessment returns score 0.0–1.0
- [ ] [FR-R-9] Decision log creates valid YAML files per schema
- [ ] [FR-R-10] Confidence calibration integrates with UQLM uncertainty
- [ ] [FR-R-11] Effort metrics track all specified fields
- [ ] [FR-R-12] RiskAssessmentEngine.assess_risk() returns complete results
- [ ] [FR-R-13] Alert system triggers on threshold violations

### 11.2 Non-Functional Requirements

- [ ] Assessment latency < 100ms for typical context
- [ ] Decision log write < 50ms
- [ ] Support concurrent assessments (thread-safe)
- [ ] Graceful degradation when UQLM unavailable

### 11.3 Test Coverage Requirements

- All 8 dimensions: 100% coverage of scoring functions
- Decision log: CRUD operations
- Confidence calibration: error calculation and alerts
- Effort tracking: start/record/stop lifecycle
- Alert system: all alert types triggered correctly

---

## 12. Integration Points

### 12.1 With Devil's Advocate

The Devil's Advocate review process writes findings to the Decision Log:
```python
# Devil's Advocate calls:
decision_log.update_review(
    decision_id="arch-001",
    reviewed_by="devil_advocate",
    review_round=2,
    review_notes="Concerns about scaling...",
    confidence_adjustment=-0.5
)
```

### 12.2 With UQLM

```python
# Get uncertainty for confidence adjustment
uncertainty = uqlm.get_uncertainty_score(context)
adjusted_confidence = calibrator.calibrate(initial_confidence, uncertainty)
```

### 12.3 With Planner

```python
# Planner logs decision and tracks effort
tracking_id = engine.track_effort("planner", task_id)
# ... execute plan ...
engine.log_decision(plan_decision)
engine.effort_tracker.finish_tracking(tracking_id, quality_score=quality)
```

---

## 13. Error Handling

### 13.1 Error Types

| Error | Handling |
|-------|----------|
| UQLM unavailable | Log warning, use default uncertainty (0.5), continue |
| Decision log write fails | Queue for retry, do not block execution |
| Invalid context data | Return partial assessment with missing dimension flagged |
| Alert delivery fails | Log locally, retry with exponential backoff |

### 13.2 Fallback Values

```python
FALLBACK_UNCERTAINTY = 0.5
FALLBACK_QUALITY_SCORE = 0.5
FALLBACK_CONFIDENCE = 5.0
```

---

## 14. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-04-19 | System | Initial specification |

---

_End of Specification_
