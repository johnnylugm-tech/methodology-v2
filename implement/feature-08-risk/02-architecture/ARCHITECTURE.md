# Feature #8: Risk Assessment — Architecture Document

**Version:** 1.0.0
**Date:** 2026-04-19
**Feature Tag:** FR-R-1 ~ FR-R-13
**Dimensions:** D1 ~ D8

---

## 1. Overview

### 1.1 Purpose

This document describes the architecture of the **Risk Assessment Subsystem** for the methodology-v2 agent system. The subsystem evaluates AI-generated outputs across 8 risk dimensions, calibrates confidence scores, tracks decision logs, and triggers alerts when risk thresholds are breached.

### 1.2 Scope

- **In-scope:** 8-dimension risk model, confidence calibration, decision logging, effort tracking, alert management, UQLM integration
- **Out-of-scope:** External API integrations beyond UQLM, persistence backends (delegated to infrastructure layer), UI/presentation layer

### 1.3 Risk Dimensions

| ID  | Dimension           | Description                                                           |
|-----|---------------------|-----------------------------------------------------------------------|
| D1  | Security            | Vulnerability to injection, leakage, unauthorized access             |
| D2  | Safety              | Potential for harmful, unethical, or dangerous outputs               |
| D3  | Accuracy            | Factual correctness and logical soundness                             |
| D4  | Robustness         | Stability under adversarial or out-of-distribution inputs             |
| D5  | Privacy            | Data exfiltration, PII exposure, compliance risks                     |
| D6  | Performance         | Latency, throughput, resource consumption                            |
| D7  | Maintainability    | Code quality, testability, technical debt                            |
| D8  | Compliance          | Regulatory alignment, licensing, policy adherence                    |

### 1.4 FR Tags Mapping

| Tag      | Requirement                                                      |
|----------|------------------------------------------------------------------|
| FR-R-1   | System shall evaluate all 8 risk dimensions on every assessment |
| FR-R-2   | System shall compute weighted composite risk score (0.0–1.0)    |
| FR-R-3   | System shall log all decisions with full audit trail            |
| FR-R-4   | System shall calibrate confidence scores against historical accuracy |
| FR-R-5   | System shall track effort (time, token count) per assessment    |
| FR-R-6   | System shall trigger alerts when any dimension score > threshold |
| FR-R-7   | System shall support custom weight profiles per use case        |
| FR-R-8   | System shall provide real-time risk dashboards                 |
| FR-R-9   | System shall quarantine high-risk outputs pending review        |
| FR-R-10  | System shall export audit logs in structured format            |
| FR-R-11  | System shall integrate with UQLM for uncertainty quantification  |
| FR-R-12  | System shall detect concept drift in risk patterns              |
| FR-R-13  | System shall provide remediation suggestions for high-risk dimensions |

---

## 2. Architecture Overview

### 2.1 High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           Risk Assessment System                              │
│                                                                              │
│  ┌──────────────┐    ┌──────────────────┐    ┌────────────────────────────┐  │
│  │   Input      │───▶│  RiskAssessment  │───▶│   Alert Manager           │  │
│  │   Validator  │    │  Engine          │    │   (thresholds, routing)  │  │
│  └──────────────┘    └──────────────────┘    └────────────────────────────┘  │
│                              │                          │                   │
│         ┌────────────────────┼──────────────────────────┘                   │
│         │                    │                                              │
│  ┌──────▼──────┐    ┌─────────▼──────────┐    ┌────────────────────────────┐ │
│  │  Decision   │    │  Dimension Assessors │    │  Confidence Calibration   │ │
│  │  Log        │    │  (D1─D8)            │    │  Engine                   │ │
│  └─────────────┘    └─────────────────────┘    └────────────────────────────┘ │
│                              │                          │                     │
│                    ┌─────────▼──────────────────────────┘                   │
│                    │           UQLM Integration                              │
│                    │  (uncertainty quantification, drift detection)          │
│                    └────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component              | Responsibility                                                      |
|------------------------|---------------------------------------------------------------------|
| `RiskAssessmentEngine` | Orchestrates the full assessment pipeline; computes composite scores |
| `DimensionAssessor`    | Evaluates a single risk dimension (D1–D8); returns `DimensionResult` |
| `DecisionLog`          | Append-only audit log; stores all decisions, inputs, outputs, scores |
| `ConfidenceCalibration`| Calibrates model confidence against observed accuracy (Platt scaling / isotonic regression) |
| `EffortTracker`        | Tracks time elapsed, token counts, API call counts per assessment  |
| `AlertManager`         | Evaluates threshold conditions; routes alerts to configured channels |
| `UQLMIntegration`      | Wraps UQLM client; provides uncertainty quantification signals       |
| `InputValidator`       | Sanitizes and validates inputs before assessment                   |
| `Config`               | Typed configuration object; manages profiles, thresholds, weights  |

### 2.3 Directory Structure

```
feature-08-risk/
├── SPEC.md
├── 01-spec/
├── 02-architecture/
│   └── ARCHITECTURE.md          ← this file
├── 03-implementation/
│   ├── risk_assessment_engine.py
│   ├── decision_log.py
│   ├── confidence_calibration.py
│   ├── effort_tracker.py
│   ├── alert_manager.py
│   ├── config.py
│   ├── uqlm_integration.py
│   └── dimensions/
│       ├── __init__.py
│       ├── base.py              # AbstractDimensionAssessor
│       ├── d1_security.py
│       ├── d2_safety.py
│       ├── d3_accuracy.py
│       ├── d4_robustness.py
│       ├── d5_privacy.py
│       ├── d6_performance.py
│       ├── d7_maintainability.py
│       └── d8_compliance.py
├── 04-tests/
│   ├── test_risk_assessment_engine.py
│   ├── test_decision_log.py
│   ├── test_confidence_calibration.py
│   ├── test_effort_tracker.py
│   ├── test_alert_manager.py
│   └── test_dimensions/
│       ├── test_d1_security.py
│       ├── test_d2_safety.py
│       ├── test_d3_accuracy.py
│       ├── test_d4_robustness.py
│       ├── test_d5_privacy.py
│       ├── test_d6_performance.py
│       ├── test_d7_maintainability.py
│       └── test_d8_compliance.py
└── 05-integration/
    └── test_uqlm_integration.py
```

---

## 3. Data Flow

### 3.1 Assessment Pipeline

```
1. [Input]
       │
       ▼
2. [InputValidator.sanitize(input)]
       │  ── validates structure, sanitizes strings, checks size limits
       ▼
3. [RiskAssessmentEngine.assess(input, profile='default')]
       │
       ├──────────────────────────────┐
       ▼                              ▼
4. [Parallel: DimensionAssessor.run(dimension) for D1..D8]
       │  ── each assessor returns DimensionResult(score, evidence, metadata)
       ▼
5. [RiskAssessmentEngine.compute_composite(dimension_results, profile.weights)]
       │  ── weighted sum → composite_risk_score
       ▼
6. [ConfidenceCalibration.calibrate(input, dimension_results, observed_outcome)]
       │  ── updates calibration state (optional, batch mode)
       ▼
7. [DecisionLog.append(record)]
       │  ── append-only write of AssessmentRecord
       ▼
8. [EffortTracker.finalize(assessment_id)]
       │  ── records elapsed_time_ms, tokens_used, api_calls
       ▼
9. [AlertManager.evaluate(assessment_record)]
       │  ── checks thresholds; fires alerts if any dimension > threshold
       ▼
10. [Return AssessmentResult to caller]
```

### 3.2 Text-Based Data Flow Diagram

```
Input
  │
  ▼
┌─────────────────────────────┐
│   InputValidator            │
│   .sanitize()               │
└─────────────────────────────┘
  │ raw_input: RawInput
  ▼ sanitized_input: SanitizedInput
┌─────────────────────────────┐
│   RiskAssessmentEngine      │
│   .assess()                 │
└─────────────────────────────┘
  │
  ├──────────────────────────────┐
  ▼                              ▼
┌────────┐  ┌────────┐  ┌────────┐
│  D1    │  │  D2    │  │  D3    │  ...  D8
│Security│  │Safety │  │Accuracy│
│ .run() │  │ .run() │  │ .run() │
└────────┘  └────────┘  └────────┘
  │          │          │
  ▼          ▼          ▼
DimensionResult(d1)  DimensionResult(d2)  DimensionResult(d3) ... DimensionResult(d8)
  │
  └──────────────────────────────┐
                                  ▼
                   ┌────────────────────────────┐
                   │  compute_composite()        │
                   │  weighted_sum(weights)      │
                   └────────────────────────────┘
                                  │
                                  ▼ composite_risk_score: float
                   ┌────────────────────────────┐
                   │  ConfidenceCalibration      │
                   │  .calibrate()              │
                   └────────────────────────────┘
                                  │
                                  ▼ calibrated_confidence: float
                   ┌────────────────────────────┐
                   │  DecisionLog.append()      │
                   │  (AssessmentRecord)        │
                   └────────────────────────────┘
                                  │
                                  ▼
                   ┌────────────────────────────┐
                   │  EffortTracker.finalize() │
                   └────────────────────────────┘
                                  │
                                  ▼ effort_summary: EffortSummary
                   ┌────────────────────────────┐
                   │  AlertManager.evaluate()   │
                   │  (check thresholds)         │
                   └────────────────────────────┘
                                  │
                                  ▼ alert_events: List[AlertEvent] (may be empty)
                                  │
                                  ▼
                          AssessmentResult
```

### 3.3 Data Structures

#### RawInput
```python
@dataclass
class RawInput:
    content: str                    # Raw text or code to assess
    context: Optional[dict]         # Additional context (e.g., prompt, model)
    metadata: Optional[dict]       # Caller-supplied metadata
```

#### SanitizedInput
```python
@dataclass
class SanitizedInput:
    content: str                    # Sanitized content
    context: dict                   # Validated context
    validation_warnings: List[str]  # Non-fatal warnings issued during sanitization
```

#### DimensionResult
```python
@dataclass
class DimensionResult:
    dimension_id: str               # e.g., "D1", "D2"
    score: float                    # 0.0 (safe) – 1.0 (critical)
    evidence: List[str]             # Human-readable evidence snippets
    metadata: dict                  # Dimension-specific metadata
    assessor_version: str           # Version of the assessor that produced this result
    timestamp: datetime
```

#### AssessmentRecord
```python
@dataclass
class AssessmentRecord:
    assessment_id: str              # UUID
    input_content_hash: str         # SHA-256 of input content
    sanitized_input: SanitizedInput
    dimension_results: Dict[str, DimensionResult]  # dimension_id → result
    composite_score: float
    calibrated_confidence: float
    effort_summary: 'EffortSummary'
    alert_events: List['AlertEvent']
    profile_name: str
    created_at: datetime
```

#### AssessmentResult
```python
@dataclass
class AssessmentResult:
    assessment_id: str
    status: AssessmentStatus        # COMPLETED, QUARANTINED, FAILED
    dimension_results: Dict[str, DimensionResult]
    composite_score: float
    calibrated_confidence: float
    effort_summary: 'EffortSummary'
    alert_events: List['AlertEvent']
    quarantine_reason: Optional[str]  # Set if status == QUARANTINED
```

#### EffortSummary
```python
@dataclass
class EffortSummary:
    assessment_id: str
    elapsed_time_ms: int
    tokens_used: int
    api_calls: int
    dimension_timings_ms: Dict[str, int]  # dimension_id → ms
```

#### AlertEvent
```python
@dataclass
class AlertEvent:
    alert_id: str                   # UUID
    assessment_id: str
    dimension_id: Optional[str]     # None for composite alerts
    threshold: float
    actual_score: float
    severity: AlertSeverity         # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    created_at: datetime
```

---

## 4. Design Decisions

### 4.1 Composite Score Formula

```
composite_score = Σ(w_i × s_i) / Σ(w_i)
```

Where `w_i` is the configured weight for dimension `i` and `s_i` is the score.
Default weights are uniform (1.0 for all 8 dimensions).
Custom profiles may adjust weights based on use case (e.g., security-critical vs. creative).

### 4.2 Calibration Strategy

Confidence calibration uses **Platt Scaling** (sigmoid) for binary outcomes
and **Isotonic Regression** for multi-class / continuous outcomes.
Calibration data is accumulated in `DecisionLog` and consumed by
`ConfidenceCalibration` in batch mode (not online).

### 4.3 Quarantine Logic

An output is **quarantined** when:
- Any single dimension score ≥ `quarantine_threshold` (default: 0.85), OR
- Composite score ≥ `quarantine_threshold` AND `quarantine_composite_enabled` (default: True)

Quarantined outputs are NOT blocked — they are returned with `status=QUARANTINED`
and `quarantine_reason`, allowing the caller to decide whether to proceed.

### 4.4 Alert Routing

Alerts are dispatched to one or more channels based on `AlertChannel` config:
- **Log** — written to the decision log (always)
- **Callback** — `alert_callback(url, alert_event)` HTTP POST
- **Queue** — published to an internal message queue (future integration)

---

## 5. Configuration Schema

```python
@dataclass
class RiskConfig:
    # Dimension weights (profile name → dimension_id → weight)
    profiles: Dict[str, Dict[str, float]]

    # Thresholds
    alert_threshold: float           # Score above which to fire an alert (default: 0.7)
    quarantine_threshold: float      # Score above which to quarantine (default: 0.85)

    # Feature flags
    quarantine_composite_enabled: bool = True
    calibration_enabled: bool = True
    drift_detection_enabled: bool = True

    # UQLM
    uqlm_endpoint: Optional[str] = None
    uqlm_timeout_seconds: float = 10.0

    # Effort tracking
    max_tokens_per_assessment: int = 100_000
    max_time_ms_per_assessment: int = 60_000

    # Alert channels
    alert_channels: List[AlertChannel] = field(default_factory=list)

    # Logging
    log_retention_days: int = 90
    log_format: str = "json"        # "json" or "text"
```

### 5.1 Default Profile

```python
DEFAULT_PROFILE: Dict[str, float] = {
    "D1": 1.0,   # Security
    "D2": 1.0,   # Safety
    "D3": 1.0,   # Accuracy
    "D4": 1.0,   # Robustness
    "D5": 1.0,   # Privacy
    "D6": 0.5,   # Performance (often less critical for safety-relevant apps)
    "D7": 0.5,   # Maintainability
    "D8": 1.0,   # Compliance
}
```

---

## 6. Text-Based System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Risk Assessment Subsystem                           │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Input Layer                                    │   │
│  │   RawInput ──▶ InputValidator.sanitize() ──▶ SanitizedInput        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Assessment Engine (Orchestrator)                  │   │
│  │                                                                       │   │
│  │   RiskAssessmentEngine.assess(sanitized_input, profile)              │   │
│  │       │                                                              │   │
│  │       ├──▶ Parallel Dimension Assessors (D1–D8)                     │   │
│  │       │       │                                                      │   │
│  │       │       ├── D1SecurityAssessor.run() ──▶ DimensionResult        │   │
│  │       │       ├── D2SafetyAssessor.run()   ──▶ DimensionResult        │   │
│  │       │       ├── D3AccuracyAssessor.run() ──▶ DimensionResult        │   │
│  │       │       ├── D4RobustnessAssessor.run() ──▶ DimensionResult      │   │
│  │       │       ├── D5PrivacyAssessor.run()  ──▶ DimensionResult        │   │
│  │       │       ├── D6PerformanceAssessor.run() ──▶ DimensionResult      │   │
│  │       │       ├── D7MaintainabilityAssessor.run() ──▶ DimensionResult │   │
│  │       │       └── D8ComplianceAssessor.run() ──▶ DimensionResult       │   │
│  │       │                                                              │   │
│  │       ├──▶ compute_composite(dimension_results, weights)             │   │
│  │       │                                                              │   │
│  │       └──▶ QuarantineDecision(composite_score, dimension_scores)     │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────────────┐     │
│         ▼                          ▼                                  ▼     │
│  ┌─────────────┐        ┌──────────────────┐       ┌──────────────┐        │
│  │ DecisionLog │        │ Confidence       │       │ EffortTracker│        │
│  │ (audit)     │        │ Calibration      │       │              │        │
│  └─────────────┘        └──────────────────┘       └──────────────┘        │
│         │                          │                        │                │
│         └──────────────────────────┼────────────────────────┘                │
│                                    ▼                                         │
│                           ┌──────────────────┐                               │
│                           │  AlertManager     │                               │
│                           │  (evaluate)       │                               │
│                           └──────────────────┘                               │
│                                    │                                         │
│                                    ▼                                         │
│                           ┌──────────────────┐                               │
│                           │  UQLMIntegration  │                               │
│                           │  (uncertainty)    │                               │
│                           └──────────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Class Signatures — Core Classes

### 7.1 `risk_assessment_engine.py`

#### RiskAssessmentEngine

```python
class RiskAssessmentEngine:
    """
    Orchestrates the full risk assessment pipeline.

    Responsibilites:
        1. Validates and sanitizes input
        2. Dispatches parallel dimension assessments
        3. Computes composite risk score
        4. Makes quarantine decisions
        5. Records decision log
        6. Triggers alert evaluation
        7. Tracks effort metrics
    """

    def __init__(
        self,
        config: RiskConfig,
        assessors: Dict[str, 'AbstractDimensionAssessor'],
        decision_log: 'DecisionLog',
        confidence_calibration: Optional['ConfidenceCalibration'] = None,
        effort_tracker: Optional['EffortTracker'] = None,
        alert_manager: Optional['AlertManager'] = None,
        uqlm_integration: Optional['UQLMIntegration'] = None,
    ) -> None:
        """
        Initialize the engine.

        Args:
            config: RiskConfig with weights, thresholds, profiles.
            assessors: Dict mapping dimension_id (e.g., "D1") to assessor instance.
            decision_log: DecisionLog instance for audit records.
            confidence_calibration: Optional ConfidenceCalibration instance.
            effort_tracker: Optional EffortTracker instance.
            alert_manager: Optional AlertManager instance.
            uqlm_integration: Optional UQLMIntegration instance.
        """
        ...

    def assess(
        self,
        raw_input: RawInput,
        profile_name: str = "default",
        assessment_id: Optional[str] = None,
    ) -> AssessmentResult:
        """
        Run the full risk assessment pipeline.

        Args:
            raw_input: RawInput to assess.
            profile_name: Name of the weight profile to use (default: "default").
            assessment_id: Optional UUID string; auto-generated if not provided.

        Returns:
            AssessmentResult with dimension scores, composite score, alerts, effort.

        Raises:
            InputValidationError: If raw_input fails validation.
            AssessmentPipelineError: If the pipeline fails unexpectedly.
        """
        ...

    def assess_dimension(
        self,
        dimension_id: str,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run a single dimension assessor (useful for partial evaluation).

        Args:
            dimension_id: e.g., "D1", "D2".
            sanitized_input: Pre-sanitized input.
            assessment_id: Assessment UUID.

        Returns:
            DimensionResult for the specified dimension.

        Raises:
            KeyError: If dimension_id is not registered.
            DimensionAssessmentError: If the assessor fails.
        """
        ...

    def compute_composite(
        self,
        dimension_results: Dict[str, DimensionResult],
        profile_name: str,
    ) -> float:
        """
        Compute the weighted composite risk score.

        Args:
            dimension_results: Dict of dimension_id → DimensionResult.
            profile_name: Name of the weight profile.

        Returns:
            Composite risk score in [0.0, 1.0].

        Raises:
            ValueError: If no dimension results are provided or profile not found.
        """
        ...

    def quarantine_decision(
        self,
        composite_score: float,
        dimension_results: Dict[str, DimensionResult],
    ) -> Tuple[AssessmentStatus, Optional[str]]:
        """
        Decide whether to quarantine the output.

        Args:
            composite_score: Weighted composite risk score.
            dimension_results: Per-dimension results.

        Returns:
            Tuple of (AssessmentStatus, quarantine_reason or None).
        """
        ...

    def get_config(self) -> RiskConfig:
        """Return the current RiskConfig."""
        ...

    def update_config(self, config: RiskConfig) -> None:
        """
        Update configuration at runtime.

        Args:
            config: New RiskConfig. Thread-safety is the caller's responsibility.
        """
        ...

    def get_registered_dimensions(self) -> List[str]:
        """Return list of registered dimension IDs."""
        ...
```

#### AssessmentStatus (Enum)

```python
class AssessmentStatus(Enum):
    """Possible states for an assessment result."""

    COMPLETED = "completed"       # Assessment finished normally
    QUARANTINED = "quarantined"   # High risk detected; output held for review
    FAILED = "failed"             # Pipeline error; assessment could not complete
```

### 7.2 `decision_log.py`

#### DecisionLog

```python
class DecisionLog:
    """
    Append-only audit log for all risk assessment decisions.

    Implements the requirements of FR-R-3 and FR-R-10.

    The log is append-only: records can never be modified or deleted
    (enforced by the append method rejecting mutation of stored records).

    Storage backend is delegated to an injected persistence adapter.
    """

    def __init__(
        self,
        persistence_adapter: 'LogPersistenceAdapter',
        retention_days: int = 90,
    ) -> None:
        """
        Initialize the decision log.

        Args:
            persistence_adapter: Backend adapter (see LogPersistenceAdapter).
            retention_days: Number of days to retain records before archival.
        """
        ...

    def append(self, record: AssessmentRecord) -> str:
        """
        Append a new assessment record to the log.

        Args:
            record: AssessmentRecord to persist.

        Returns:
            The assessment_id of the appended record.

        Raises:
            LogPersistenceError: If the underlying storage fails.
        """
        ...

    def get(
        self,
        assessment_id: str,
    ) -> AssessmentRecord:
        """
        Retrieve a single assessment record by ID.

        Args:
            assessment_id: UUID of the assessment.

        Returns:
            The corresponding AssessmentRecord.

        Raises:
            RecordNotFoundError: If assessment_id is not in the log.
        """
        ...

    def query(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        dimension_filter: Optional[List[str]] = None,
        min_composite_score: Optional[float] = None,
        status_filter: Optional[List[AssessmentStatus]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AssessmentRecord]:
        """
        Query the log with filters.

        Args:
            start_time: Filter records created on or after this time.
            end_time: Filter records created on or before this time.
            dimension_filter: Only return records where these dimensions were assessed.
            min_composite_score: Only return records with composite_score >= this.
            status_filter: Only return records with matching AssessmentStatus values.
            limit: Maximum number of records to return (default: 100, max: 1000).
            offset: Pagination offset.

        Returns:
            List of matching AssessmentRecord objects, newest first.
        """
        ...

    def export(
        self,
        format: ExportFormat,
        path: Path,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        Export audit log to a structured file format.

        Args:
            format: ExportFormat (JSON, CSV, Parquet).
            path: Destination file path.
            start_time: Optional start time filter.
            end_time: Optional end time filter.

        Returns:
            Number of records exported.

        Raises:
            ExportError: If export fails.
        """
        ...

    def count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        Return the total number of records matching the time filter.

        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.

        Returns:
            Total count of matching records.
        """
        ...

    def get_calibration_dataset(
        self,
        limit: Optional[int] = None,
    ) -> List[Tuple[float, bool]]:
        """
        Return (predicted_confidence, observed_outcome) pairs for calibration.

        Args:
            limit: Optional maximum number of records to return.

        Returns:
            List of (confidence_score, actual_correctness_bool) tuples.
        """
        ...

    def archive_old_records(self, before: datetime) -> int:
        """
        Archive records older than the retention period.

        Args:
            before: Archive records created before this timestamp.

        Returns:
            Number of records archived.
        """
        ...
```

#### LogPersistenceAdapter (Abstract)

```python
class LogPersistenceAdapter(ABC):
    """
    Abstract backend for DecisionLog persistence.

    Implement this to add custom storage (SQLite, PostgreSQL, S3, etc.).
    """

    @abstractmethod
    def append(self, record: AssessmentRecord) -> str:
        """Persist a single record. Returns the record's assessment_id."""
        ...

    @abstractmethod
    def get(self, assessment_id: str) -> AssessmentRecord:
        """Retrieve a record by assessment_id."""
        ...

    @abstractmethod
    def query(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        dimension_filter: Optional[List[str]],
        min_composite_score: Optional[float],
        status_filter: Optional[List[AssessmentStatus]],
        limit: int,
        offset: int,
    ) -> List[AssessmentRecord]:
        ...

    @abstractmethod
    def count(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> int:
        ...

    @abstractmethod
    def export(
        self,
        format: ExportFormat,
        path: Path,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
    ) -> int:
        ...

    @abstractmethod
    def close(self) -> None:
        """Release any held resources (connections, file handles, etc.)."""
        ...
```

#### ExportFormat (Enum)

```python
class ExportFormat(Enum):
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
```

### 7.3 `confidence_calibration.py`

#### ConfidenceCalibration

```python
class ConfidenceCalibration:
    """
    Calibrates model confidence scores against observed accuracy.

    Implements FR-R-4 using Platt Scaling (binary) or Isotonic Regression (multi-class).
    Calibration state is updated in batch mode using historical data from DecisionLog.
    """

    def __init__(
        self,
        method: CalibrationMethod = CalibrationMethod.PLATT_SCALING,
        min_samples: int = 100,
    ) -> None:
        """
        Initialize the calibrator.

        Args:
            method: CalibrationMethod.PLATT_SCALING or CalibrationMethod.ISOTONIC.
            min_samples: Minimum number of labeled samples before calibration is applied.
        """
        ...

    def calibrate(
        self,
        predicted_confidence: float,
        dimension_results: Dict[str, DimensionResult],
        observed_outcome: bool,
    ) -> float:
        """
        Apply calibration to a predicted confidence value.

        Args:
            predicted_confidence: Raw confidence score from the model [0.0, 1.0].
            dimension_results: Per-dimension results (used for per-dimension calibration).
            observed_outcome: Actual correctness of the output (True = correct).

        Returns:
            Calibrated confidence score in [0.0, 1.0].
        """
        ...

    def calibrate_batch(
        self,
        dataset: List[Tuple[float, bool]],
    ) -> None:
        """
        Update calibration parameters from a batch of (confidence, outcome) samples.

        Args:
            dataset: List of (predicted_confidence, observed_correctness_bool) tuples.
        """
        ...

    def get_calibration_curve(
        self,
        n_bins: int = 10,
    ) -> CalibrationCurve:
        """
        Compute calibration curve data for evaluation.

        Args:
            n_bins: Number of bins for the reliability diagram.

        Returns:
            CalibrationCurve with bin edges, bin accuracies, bin confidences.
        """
        ...

    def get_expected_calibration_error(self) -> float:
        """
        Compute the Expected Calibration Error (ECE) for the current model.

        Returns:
            ECE value (lower is better; 0.0 = perfectly calibrated).
        """
        ...

    def is_calibrated(self) -> bool:
        """
        Check whether enough samples have been collected for reliable calibration.

        Returns:
            True if min_samples threshold has been reached.
        """
        ...

    def reset(self) -> None:
        """Reset all calibration parameters and sample counts."""
        ...
```

#### CalibrationMethod (Enum)

```python
class CalibrationMethod(Enum):
    PLATT_SCALING = "platt_scaling"     # Sigmoid calibration (binary)
    ISOTONIC = "isotonic"               # Isotonic regression (multi-class / continuous)
```

#### CalibrationCurve

```python
@dataclass
class CalibrationCurve:
    bin_edges: List[float]        # n_bins + 1 bin edges in [0.0, 1.0]
    bin_confidences: List[float]  # Average predicted confidence per bin
    bin_accuracies: List[float]  # Average observed accuracy per bin
    bin_counts: List[int]         # Number of samples per bin
    ece: float                    # Expected Calibration Error
```

### 7.4 `effort_tracker.py`

#### EffortTracker

```python
class EffortTracker:
    """
    Tracks effort metrics for each assessment.

    Implements FR-R-5.
    Records wall-clock time, token consumption, API call counts,
    and per-dimension timing breakdowns.
    """

    def __init__(self, max_tokens_per_assessment: int = 100_000, max_time_ms: int = 60_000) -> None:
        """
        Initialize the effort tracker.

        Args:
            max_tokens_per_assessment: Upper bound for token count before flagging.
            max_time_ms: Upper bound for wall-clock time before flagging.
        """
        ...

    def start(self, assessment_id: str) -> None:
        """
        Begin tracking effort for an assessment.

        Args:
            assessment_id: UUID of the assessment being tracked.
        """
        ...

    def record_tokens(self, assessment_id: str, token_count: int) -> None:
        """
        Record token usage for the current assessment.

        Args:
            assessment_id: UUID of the assessment.
            token_count: Number of tokens consumed.
        """
        ...

    def record_api_call(self, assessment_id: str, endpoint: str) -> None:
        """
        Record an API call made during the assessment.

        Args:
            assessment_id: UUID of the assessment.
            endpoint: Identifier for the API endpoint called.
        """
        ...

    def record_dimension_time(
        self,
        assessment_id: str,
        dimension_id: str,
        elapsed_ms: int,
    ) -> None:
        """
        Record the time taken by a single dimension assessor.

        Args:
            assessment_id: UUID of the assessment.
            dimension_id: e.g., "D1".
            elapsed_ms: Wall-clock milliseconds for this dimension.
        """
        ...

    def finalize(self, assessment_id: str) -> EffortSummary:
        """
        Finalize tracking and produce an EffortSummary.

        Args:
            assessment_id: UUID of the assessment.

        Returns:
            EffortSummary with all tracked metrics.

        Raises:
            TrackingNotStartedError: If start() was not called for this assessment_id.
        """
        ...

    def get_in_progress(self, assessment_id: str) -> Optional[EffortSummary]:
        """
        Get an in-progress snapshot without finalizing.

        Args:
            assessment_id: UUID of the assessment.

        Returns:
            Partial EffortSummary, or None if assessment_id not found.
        """
        ...

    def is_over_limit(self, effort_summary: EffortSummary) -> Tuple[bool, List[str]]:
        """
        Check whether an effort summary exceeds configured limits.

        Args:
            effort_summary: EffortSummary to check.

        Returns:
            Tuple of (is_over_limit, list_of_violation_descriptions).
        """
        ...
```

### 7.5 `alert_manager.py`

#### AlertManager

```python
class AlertManager:
    """
    Evaluates risk thresholds and routes alert events.

    Implements FR-R-6 and FR-R-13 (remediation suggestions).
    """

    def __init__(
        self,
        channels: List[AlertChannel],
        dimension_thresholds: Dict[str, float],
        composite_threshold: float,
        remediation_provider: Optional['RemediationProvider'] = None,
    ) -> None:
        """
        Initialize the alert manager.

        Args:
            channels: List of AlertChannel configurations.
            dimension_thresholds: Per-dimension alert thresholds (dimension_id → score).
            composite_threshold: Composite score threshold for alerts.
            remediation_provider: Optional provider for remediation suggestions.
        """
        ...

    def evaluate(
        self,
        assessment_record: AssessmentRecord,
    ) -> List[AlertEvent]:
        """
        Evaluate an assessment record and generate any necessary alerts.

        Args:
            assessment_record: Completed AssessmentRecord.

        Returns:
            List of AlertEvent objects (may be empty).
        """
        ...

    def add_channel(self, channel: AlertChannel) -> None:
        """
        Register a new alert channel at runtime.

        Args:
            channel: AlertChannel configuration to add.
        """
        ...

    def remove_channel(self, channel_id: str) -> None:
        """
        Remove an alert channel by ID.

        Args:
            channel_id: UUID of the channel to remove.
        """
        ...

    def update_threshold(
        self,
        dimension_id: Optional[str],
        new_threshold: float,
    ) -> None:
        """
        Update an alert threshold at runtime.

        Args:
            dimension_id: If provided, update that dimension's threshold; else update composite.
            new_threshold: New threshold value in [0.0, 1.0].
        """
        ...

    def get_active_alerts(
        self,
        assessment_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[AlertEvent]:
        """
        Query currently active (unresolved) alerts.

        Args:
            assessment_id: Optional filter by specific assessment.
            since: Return alerts created on or after this timestamp.

        Returns:
            List of active AlertEvent objects.
        """
        ...

    def resolve_alert(self, alert_id: str, resolution_note: str) -> None:
        """
        Mark an alert as resolved.

        Args:
            alert_id: UUID of the alert to resolve.
            resolution_note: Human-readable note explaining the resolution.
        """
        ...
```

#### AlertChannel

```python
@dataclass
class AlertChannel:
    """Configuration for a single alert destination."""

    channel_id: str                      # UUID
    channel_type: AlertChannelType       # LOG, CALLBACK, QUEUE
    name: str                            # Human-readable name
    enabled: bool = True
    min_severity: AlertSeverity = AlertSeverity.LOW  # Minimum severity to dispatch

    # For CALLBACK type
    callback_url: Optional[str] = None
    callback_headers: Optional[Dict[str, str]] = None
    callback_timeout_seconds: float = 5.0

    # For QUEUE type
    queue_name: Optional[str] = None

    # Filters
    dimension_filter: Optional[List[str]] = None  # Only fire for these dimensions
    exclude_profile_names: Optional[List[str]] = None
```

#### AlertChannelType (Enum)

```python
class AlertChannelType(Enum):
    LOG = "log"
    CALLBACK = "callback"
    QUEUE = "queue"
```

#### AlertSeverity (Enum)

```python
class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @staticmethod
    def from_score(score: float) -> 'AlertSeverity':
        """Map a risk score to an AlertSeverity tier."""
        if score >= 0.9:
            return AlertSeverity.CRITICAL
        elif score >= 0.75:
            return AlertSeverity.HIGH
        elif score >= 0.5:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
```

### 7.6 `config.py`

#### RiskConfig

```python
@dataclass
class RiskConfig:
    """
    Top-level configuration object for the Risk Assessment System.

    This class is the single source of truth for all tunable parameters.
    It is designed to be serializable (to/from YAML or JSON) and immutable
    after construction (use with_update() to create modified copies).
    """

    # Profile definitions: profile_name → dimension_id → weight
    profiles: Dict[str, Dict[str, float]]

    # Default profile name
    default_profile: str = "default"

    # Thresholds
    alert_threshold: float = 0.7
    quarantine_threshold: float = 0.85

    # Feature flags
    quarantine_composite_enabled: bool = True
    calibration_enabled: bool = True
    drift_detection_enabled: bool = True

    # UQLM integration
    uqlm_endpoint: Optional[str] = None
    uqlm_timeout_seconds: float = 10.0
    uqlm_retry_count: int = 3

    # Effort limits
    max_tokens_per_assessment: int = 100_000
    max_time_ms_per_assessment: int = 60_000

    # Decision log
    log_retention_days: int = 90
    log_format: str = "json"  # "json" or "text"

    # Calibration
    calibration_method: CalibrationMethod = CalibrationMethod.PLATT_SCALING
    calibration_min_samples: int = 100

    # Alert channels (serialized as list; reconstructed at load time)
    alert_channels: List[AlertChannel] = field(default_factory=list)

    # Drift detection
    drift_detection_window: int = 500   # Number of records for drift window
    drift_z_score_threshold: float = 3.0

    @classmethod
    def from_dict(cls, data: dict) -> 'RiskConfig':
        """
        Reconstruct RiskConfig from a dictionary (e.g., from YAML/JSON).

        Args:
            data: Dictionary representation of RiskConfig.

        Returns:
            RiskConfig instance.
        """
        ...

    @classmethod
    def from_yaml(cls, path: Path) -> 'RiskConfig':
        """Load RiskConfig from a YAML file."""
        ...

    @classmethod
    def from_json(cls, path: Path) -> 'RiskConfig':
        """Load RiskConfig from a JSON file."""
        ...

    def to_dict(self) -> dict:
        """Serialize RiskConfig to a dictionary."""
        ...

    def to_yaml(self, path: Path) -> None:
        """Write RiskConfig to a YAML file."""
        ...

    def with_updates(self, **kwargs) -> 'RiskConfig':
        """
        Create a modified copy of this config with the given field updates.

        Args:
            **kwargs: Field names and new values to override.

        Returns:
            New RiskConfig instance (this instance is unchanged).
        """
        ...

    def get_weights(self, profile_name: str) -> Dict[str, float]:
        """
        Get the dimension weights for a named profile.

        Args:
            profile_name: Name of the profile.

        Returns:
            Dict of dimension_id → weight.

        Raises:
            KeyError: If profile_name is not defined.
        """
        ...

    def validate(self) -> List[str]:
        """
        Validate the configuration and return a list of warnings.

        Returns:
            List of validation warning strings (empty if all valid).
        """
        ...
```

### 7.7 `uqlm_integration.py`

#### UQLMIntegration

```python
class UQLMIntegration:
    """
    Wrapper around the UQLM (Uncertainty Quantification Language Model) client.

    Provides:
        - Uncertainty score per output
        - Confidence intervals for risk estimates
        - Concept drift detection via distribution shift monitoring
        - Per-dimension uncertainty breakdown

    Implements FR-R-11 and FR-R-12.
    """

    def __init__(
        self,
        endpoint: str,
        timeout_seconds: float = 10.0,
        retry_count: int = 3,
        cache_enabled: bool = True,
    ) -> None:
        """
        Initialize UQLM integration.

        Args:
            endpoint: Base URL of the UQLM API.
            timeout_seconds: Request timeout per call.
            retry_count: Number of retries on failure.
            cache_enabled: Whether to cache UQLM responses for identical inputs.
        """
        ...

    def quantify_uncertainty(
        self,
        input_content: str,
        output_content: str,
        context: Optional[dict] = None,
    ) -> UncertaintyResult:
        """
        Query UQLM for an uncertainty quantification of an input-output pair.

        Args:
            input_content: The original input prompt.
            output_content: The AI-generated output to evaluate.
            context: Optional additional context metadata.

        Returns:
            UncertaintyResult with overall uncertainty and per-dimension scores.

        Raises:
            UQLMConnectionError: If the UQLM endpoint cannot be reached.
            UQLMTimeoutError: If the request times out.
            UQLMResponseError: If the response is malformed or indicates an error.
        """
        ...

    def detect_drift(
        self,
        recent_window: List[UncertaintyResult],
        baseline_window: List[UncertaintyResult],
    ) -> DriftReport:
        """
        Detect concept drift by comparing recent uncertainty distributions to baseline.

        Args:
            recent_window: List of recent UncertaintyResult objects (size = drift_detection_window).
            baseline_window: Historical baseline UncertaintyResult objects.

        Returns:
            DriftReport with drift_detected flag, z-scores, and affected dimensions.

        Raises:
            InsufficientDataError: If windows are too small for statistical testing.
        """
        ...

    def get_uncertainty_history(
        self,
        dimension_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[UncertaintyResult]:
        """
        Retrieve historical uncertainty quantification results.

        Args:
            dimension_id: Optional filter to a specific dimension.
            limit: Maximum number of records to return.

        Returns:
            List of UncertaintyResult objects, most recent first.
        """
        ...

    def clear_cache(self) -> None:
        """Clear the UQLM response cache."""
        ...

    def health_check(self) -> bool:
        """
        Check if the UQLM endpoint is reachable and healthy.

        Returns:
            True if the endpoint responds with a 2xx status code.
        """
        ...
```

#### UncertaintyResult

```python
@dataclass
class UncertaintyResult:
    """Result of a UQLM uncertainty quantification query."""

    assessment_id: str
    overall_uncertainty: float          # 0.0 (certain) – 1.0 (highly uncertain)
    dimension_uncertainty: Dict[str, float]  # Per-dimension uncertainty scores
    confidence_interval_95: Tuple[float, float]  # (lower, upper) bounds
    entropy: float                      # Output entropy measure
    mutual_information: Optional[float]  # Mutual information I(input; output)
    model_version: str
    computed_at: datetime
    raw_response: Optional[dict]        # Raw UQLM API response (for debugging)
```

#### DriftReport

```python
@dataclass
class DriftReport:
    """Report on detected concept drift between two observation windows."""

    drift_detected: bool
    overall_z_score: float
    dimension_z_scores: Dict[str, float]  # Per-dimension z-scores
    affected_dimensions: List[str]         # Dimensions with |z_score| > threshold
    p_value: float
    confidence: float                      # Confidence in the drift detection
    recommendation: str                    # Human-readable recommendation
    created_at: datetime
```

---

## 8. Class Signatures — Dimension Assessors (D1–D8)

### 8.1 `dimensions/base.py`

#### AbstractDimensionAssessor (ABC)

```python
class AbstractDimensionAssessor(ABC):
    """
    Abstract base class for all dimension-specific risk assessors.

    All concrete assessors (D1–D8) must implement the `run` method.

    Attributes:
        dimension_id: Unique identifier (e.g., "D1").
        dimension_name: Human-readable name (e.g., "Security").
        version: Semantic version string of this assessor.
    """

    dimension_id: str = "UNKNOWN"
    dimension_name: str = "Unknown Dimension"
    version: str = "0.0.0"

    def __init__(self, config: Optional[RiskConfig] = None) -> None:
        """
        Initialize the assessor.

        Args:
            config: Optional RiskConfig for accessing shared settings.
        """
        ...

    @abstractmethod
    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Evaluate the risk for this dimension.

        Args:
            sanitized_input: Pre-sanitized input to assess.
            assessment_id: UUID of the current assessment.

        Returns:
            DimensionResult with score, evidence, and metadata.

        Raises:
            DimensionAssessmentError: If assessment fails.
        """
        ...

    def get_dimension_id(self) -> str:
        """Return the dimension ID."""
        ...

    def get_version(self) -> str:
        """Return the assessor version string."""
        ...

    def get_metadata(self) -> dict:
        """
        Return assessor metadata (can be overridden for richer metadata).

        Returns:
            Dict with keys: dimension_id, dimension_name, version.
        """
        ...
```

### 8.2 `dimensions/d1_security.py`

#### D1SecurityAssessor

```python
class D1SecurityAssessor(AbstractDimensionAssessor):
    """
    Assessor for Security risk (D1).

    Evaluates vulnerability to:
        - Prompt injection attacks
        - Code injection / shell command injection
        - SQL injection
        - Path traversal
        - Authentication/authorization bypass attempts
        - Sensitive data exfiltration via output

    Implements pattern-matching heuristics and, when UQLM is available,
    leverages its uncertainty signals for novel attack detection.
    """

    dimension_id: str = "D1"
    dimension_name: str = "Security"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        uqlm_integration: Optional[UQLMIntegration] = None,
        injection_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize D1 Security assessor.

        Args:
            config: Optional RiskConfig.
            uqlm_integration: Optional UQLMIntegration for advanced detection.
            injection_patterns: Dict of attack_type → list of regex patterns.
                               Defaults to built-in patterns if not provided.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the security risk assessment.

        Detection methods:
            1. Pattern matching against known injection signatures
            2. Structural analysis (suspicious escape sequences, nested contexts)
            3. UQLM uncertainty scoring (if available)
            4. Output content analysis for exfiltrated sensitive data

        Returns:
            DimensionResult with:
                - score: 0.0–1.0 (0 = safe, 1 = critical)
                - evidence: List of matched attack pattern descriptions
                - metadata: {
                    "matched_patterns": [...],
                    "attack_types": [...],
                    "uqlm_uncertainty": float or None,
                  }
        """
        ...

    def add_pattern(self, attack_type: str, pattern: str) -> None:
        """
        Register a new injection pattern at runtime.

        Args:
            attack_type: Category of attack (e.g., "prompt_injection").
            pattern: Regex pattern string.
        """
        ...

    def get_supported_attack_types(self) -> List[str]:
        """Return list of supported attack type categories."""
        ...
```

### 8.3 `dimensions/d2_safety.py`

#### D2SafetyAssessor

```python
class D2SafetyAssessor(AbstractDimensionAssessor):
    """
    Assessor for Safety risk (D2).

    Evaluates potential for:
        - Harmful advice (medical, legal, financial without disclaimers)
        - Hate speech, harassment, discrimination
        - Violent or graphic content generation
        - Self-harm inducing content
        - Misinformation with potential for real-world harm
        - Sexual content involving minors or non-consent

    Uses a combination of:
        - Keyword/phrase blocklists (configurable severity tiers)
        - Sentiment analysis signals
        - UQLM uncertainty for novel harmful content detection
    """

    dimension_id: str = "D2"
    dimension_name: str = "Safety"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        uqlm_integration: Optional[UQLMIntegration] = None,
        blocklist_path: Optional[Path] = None,
        severity_thresholds: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Initialize D2 Safety assessor.

        Args:
            config: Optional RiskConfig.
            uqlm_integration: Optional UQLMIntegration.
            blocklist_path: Optional path to custom blocklist YAML/JSON.
            severity_thresholds: Optional override of per-category severity thresholds.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the safety risk assessment.

        Returns:
            DimensionResult with:
                - score: 0.0–1.0
                - evidence: List of harmful content category matches
                - metadata: {
                    "matched_categories": [...],
                    "severity_tier": "low" | "medium" | "high" | "critical",
                    "uqlm_uncertainty": float or None,
                  }
        """
        ...

    def update_severity_threshold(self, category: str, threshold: float) -> None:
        """Update the alert threshold for a specific harm category."""
        ...
```

### 8.4 `dimensions/d3_accuracy.py`

#### D3AccuracyAssessor

```python
class D3AccuracyAssessor(AbstractDimensionAssessor):
    """
    Assessor for Accuracy risk (D3).

    Evaluates:
        - Factual correctness of claims (against known knowledge bases)
        - Mathematical and logical error detection
        - Consistency with provided context / retrieved documents
        - Hallucination signals (assertions not supported by input)
        - Citation accuracy (if citations are present)

    When UQLM is available, cross-references uncertainty signals with
    internal consistency checks.
    """

    dimension_id: str = "D3"
    dimension_name: str = "Accuracy"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        knowledge_base: Optional['KnowledgeBaseAdapter'] = None,
        uqlm_integration: Optional[UQLMIntegration] = None,
    ) -> None:
        """
        Initialize D3 Accuracy assessor.

        Args:
            config: Optional RiskConfig.
            knowledge_base: Optional adapter for factual verification.
                           If not provided, uses heuristics only.
            uqlm_integration: Optional UQLMIntegration.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the accuracy risk assessment.

        Returns:
            DimensionResult with:
                - score: 0.0–1.0 (0 = perfectly accurate, 1 = contains critical errors)
                - evidence: List of specific inaccuracies detected
                - metadata: {
                    "error_count": int,
                    "hallucination_signals": [...],
                    "fact_check_passed": bool,
                    "uqlm_uncertainty": float or None,
                  }
        """
        ...

    def check_fact(self, claim: str) -> FactCheckResult:
        """
        Check a single factual claim against the knowledge base.

        Args:
            claim: A factual assertion string.

        Returns:
            FactCheckResult with verdict and supporting evidence.
        """
        ...
```

#### FactCheckResult

```python
@dataclass
class FactCheckResult:
    claim: str
    verdict: Literal["supported", "contradicted", "unknown", "unsupported"]
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    confidence: float  # Confidence in the verdict
```

### 8.5 `dimensions/d4_robustness.py`

#### D4RobustnessAssessor

```python
class D4RobustnessAssessor(AbstractDimensionAssessor):
    """
    Assessor for Robustness risk (D4).

    Evaluates:
        - Stability under adversarial / perturbed inputs
        - Graceful degradation with out-of-distribution (OOD) inputs
        - Prompt evasion attacks (attempts to bypass content policies)
        - Output consistency under semantically equivalent re-phrasings
        - Edge case handling (empty inputs, extremely long inputs, etc.)

    Uses input perturbation analysis and, when UQLM is available,
    leverages its uncertainty quantification for OOD detection.
    """

    dimension_id: str = "D4"
    dimension_name: str = "Robustness"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        uqlm_integration: Optional[UQLMIntegration] = None,
        perturbation_strategies: Optional[List[PerturbationStrategy]] = None,
    ) -> None:
        """
        Initialize D4 Robustness assessor.

        Args:
            config: Optional RiskConfig.
            uqlm_integration: Optional UQLMIntegration.
            perturbation_strategies: List of perturbation strategies to apply.
                                     Defaults to built-in strategies.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the robustness risk assessment.

        Detection methods:
            1. Structural validation (input size, encoding, malformed structure)
            2. Adversarial pattern detection (known bypass technique signatures)
            3. Perturbation testing: re-phrase input and check output consistency
            4. OOD detection via UQLM uncertainty signals

        Returns:
            DimensionResult with:
                - score: 0.0–1.0
                - evidence: List of robustness failure modes detected
                - metadata: {
                    "perturbation_results": [...],
                    "ood_detected": bool,
                    "adversarial_patterns_matched": [...],
                    "uqlm_uncertainty": float or None,
                  }
        """
        ...
```

### 8.6 `dimensions/d5_privacy.py`

#### D5PrivacyAssessor

```python
class D5PrivacyAssessor(AbstractDimensionAssessor):
    """
    Assessor for Privacy risk (D5).

    Evaluates:
        - Presence of personally identifiable information (PII) in output
        - Re-identification risk from quasi-identifiers
        - Data exfiltration via output (training data leakage signals)
        - Sensitive entity detection (medical, financial, biometric)
        - Compliance with data minimization principles

    Uses NER (Named Entity Recognition) and pattern matching for
    PII detection, with configurable entity types and thresholds.
    """

    dimension_id: str = "D5"
    dimension_name: str = "Privacy"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        ner_adapter: Optional['NERAdapter'] = None,
        pii_patterns: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize D5 Privacy assessor.

        Args:
            config: Optional RiskConfig.
            ner_adapter: Optional NER adapter for entity recognition.
            pii_patterns: Optional custom PII regex patterns.
                         Defaults to built-in patterns covering:
                         email, phone, SSN, credit card, IP address, etc.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the privacy risk assessment.

        Returns:
            DimensionResult with:
                - score: 0.0–1.0
                - evidence: List of detected PII categories and locations
                - metadata: {
                    "pii_types_detected": [...],
                    "pii_count": int,
                    "reidentification_risk": float,
                    "compliance_flags": [...],
                  }
        """
        ...

    def redact(self, content: str) -> Tuple[str, List[PIILocation]]:
        """
        Redact PII from content and return redaction map.

        Args:
            content: Text content to redact.

        Returns:
            Tuple of (redacted_content, list_of_PIILocation objects).
        """
        ...
```

#### PIILocation

```python
@dataclass
class PIILocation:
    pii_type: str           # e.g., "email", "phone"
    start_char: int         # Inclusive start position
    end_char: int           # Exclusive end position
    redacted_form: str      # e.g., "[EMAIL_REDACTED]"
    confidence: float       # Detection confidence
```

### 8.7 `dimensions/d6_performance.py`

#### D6PerformanceAssessor

```python
class D6PerformanceAssessor(AbstractDimensionAssessor):
    """
    Assessor for Performance risk (D6).

    Evaluates:
        - Latency (response time vs. SLA thresholds)
        - Throughput (tokens per second)
        - Resource consumption (memory, CPU)
        - Cost efficiency (per-call cost vs. value delivered)
        - Timeout rates

    Note: This assessor primarily integrates with EffortTracker metrics
    rather than analyzing content directly. It computes risk from
    operational telemetry.
    """

    dimension_id: str = "D6"
    dimension_name: str = "Performance"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        effort_tracker: Optional[EffortTracker] = None,
        latency_sla_ms: float = 5000.0,
        throughput_min_tokens_per_sec: float = 10.0,
    ) -> None:
        """
        Initialize D6 Performance assessor.

        Args:
            config: Optional RiskConfig.
            effort_tracker: EffortTracker instance to pull metrics from.
            latency_sla_ms: Maximum acceptable latency in milliseconds.
            throughput_min_tokens_per_sec: Minimum acceptable token throughput.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the performance risk assessment.

        Reads effort metrics from EffortTracker for the given assessment_id.
        If effort metrics are not available, returns a neutral score (0.0).

        Returns:
            DimensionResult with:
                - score: 0.0–1.0 (0 = well within SLA, 1 = SLA breached / critical)
                - evidence: List of SLA breaches or resource warnings
                - metadata: {
                    "elapsed_time_ms": int,
                    "tokens_used": int,
                    "tokens_per_second": float,
                    "sla_latency_ms": float,
                    "sla_breached": bool,
                    "api_calls": int,
                  }
        """
        ...

    def evaluate_telemetry(
        self,
        effort_summary: EffortSummary,
    ) -> DimensionResult:
        """
        Evaluate performance risk from an EffortSummary directly.

        Args:
            effort_summary: Pre-computed EffortSummary.

        Returns:
            DimensionResult for performance risk.
        """
        ...
```

### 8.8 `dimensions/d7_maintainability.py`

#### D7MaintainabilityAssessor

```python
class D7MaintainabilityAssessor(AbstractDimensionAssessor):
    """
    Assessor for Maintainability risk (D7).

    Evaluates:
        - Code quality (if output is code): cyclomatic complexity, duplication, style violations
        - Documentation quality: docstring presence, comment relevance
        - Testability signals: whether the output contains or suggests tests
        - Technical debt indicators: hardcoded values, magic numbers, anti-patterns
        - Architectural signals: coupling, separation of concerns

    This assessor processes output content directly and produces
    risk scores based on code quality heuristics.
    """

    dimension_id: str = "D7"
    dimension_name: str = "Maintainability"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        complexity_thresholds: Optional[Dict[str, int]] = None,
        include_suggestions: bool = True,
    ) -> None:
        """
        Initialize D7 Maintainability assessor.

        Args:
            config: Optional RiskConfig.
            complexity_thresholds: Optional override of complexity thresholds
                                  (e.g., max_cyclomatic_complexity).
            include_suggestions: Whether to populate remediation_suggestions in metadata.
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the maintainability risk assessment.

        Returns:
            DimensionResult with:
                - score: 0.0–1.0
                - evidence: List of maintainability issues detected
                - metadata: {
                    "is_code": bool,
                    "language": Optional[str],
                    "issues": [
                        {"type": str, "location": str, "severity": str, "message": str},
                        ...
                    ],
                    "complexity_metrics": {...},
                    "remediation_suggestions": [...],
                  }
        """
        ...

    def detect_language(self, content: str) -> Optional[str]:
        """
        Attempt to detect the programming language of the content.

        Args:
            content: Text content to analyze.

        Returns:
            Language name (e.g., "python", "javascript") or None if not detected.
        """
        ...
```

### 8.9 `dimensions/d8_compliance.py`

#### D8ComplianceAssessor

```python
class D8ComplianceAssessor(AbstractDimensionAssessor):
    """
    Assessor for Compliance risk (D8).

    Evaluates alignment with:
        - Regulatory frameworks (GDPR, HIPAA, SOC2, CCPA, etc.)
        - Licensing constraints (permissive vs. copyleft licenses in generated code)
        - Internal policy adherence ( configurable rule sets)
        - Copyright and trademark signals
        - Data residency and sovereignty requirements

    Uses a rule-based engine with configurable compliance rule definitions.
    """

    dimension_id: str = "D8"
    dimension_name: str = "Compliance"
    version: str = "1.0.0"

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        compliance_rules: Optional[List['ComplianceRule']] = None,
        jurisdiction: Optional[str] = None,
    ) -> None:
        """
        Initialize D8 Compliance assessor.

        Args:
            config: Optional RiskConfig.
            compliance_rules: Optional list of ComplianceRule objects.
                             Defaults to built-in rules for common frameworks.
            jurisdiction: Optional primary jurisdiction string
                         (e.g., "EU", "US-CA", "GLOBAL").
        """
        ...

    def run(
        self,
        sanitized_input: SanitizedInput,
        assessment_id: str,
    ) -> DimensionResult:
        """
        Run the compliance risk assessment.

        Returns:
            DimensionResult with:
                - score: 0.0–1.0
                - evidence: List of compliance violations or warnings
                - metadata: {
                    "violations": [
                        {
                            "rule_id": str,
                            "framework": str,
                            "severity": str,
                            "description": str,
                            "recommendation": str,
                        },
                        ...
                    ],
                    "applicable_frameworks": [...],
                    "jurisdiction": str,
                    "overall_compliance_status": "compliant" | "partial" | "non_compliant",
                  }
        """
        ...

    def add_rule(self, rule: 'ComplianceRule') -> None:
        """Add a compliance rule at runtime."""
        ...

    def evaluate_license(self, license_text: str) -> LicenseAnalysisResult:
        """
        Analyze a license string for compliance implications.

        Args:
            license_text: License content or SPDX identifier.

        Returns:
            LicenseAnalysisResult with compliance assessment.
        """
        ...
```

#### ComplianceRule

```python
@dataclass
class ComplianceRule:
    rule_id: str
    framework: str                    # e.g., "GDPR", "HIPAA", "SOC2"
    severity: str                     # "critical", "high", "medium", "low"
    description: str
    detection_pattern: Optional[str]   # Regex or keyword pattern
    recommendation: str
    jurisdiction: Optional[str] = None  # Optional geographic scope
```

#### LicenseAnalysisResult

```python
@dataclass
class LicenseAnalysisResult:
    license_name: Optional[str]
    spdx_id: Optional[str]
    compliance_status: Literal["permissive", "copyleft", "proprietary", "unknown"]
    restrictions: List[str]
    attribution_required: bool
    commercial_use_allowed: bool
    modify_allowed: bool
    distribute_allowed: bool
    sublicense_allowed: bool
    confidence: float
```

---

## 9. Integration Points

### 9.1 UQLM Integration Flow

```
RiskAssessmentEngine.assess()
       │
       ├──▶ UQLMIntegration.quantify_uncertainty()
       │           │
       │           ├── Request → UQLM API endpoint
       │           │
       │           └── Response → UncertaintyResult
       │                        │
       │                        ├── overall_uncertainty
       │                        ├── dimension_uncertainty
       │                        └── confidence_interval_95
       │
       └──▶ Store UncertaintyResult in AssessmentRecord.metadata
```

### 9.2 AlertManager Callback Contract

```python
# AlertManager dispatches to CALLBACK channels via HTTP POST:
#
# POST {callback_url}
# Headers:
#   Content-Type: application/json
#   X-Alert-ID: {alert_id}
#   X-Alert-Severity: {severity}
#   X-Assessment-ID: {assessment_id}
#
# Body (JSON):
# {
#   "alert_id": "uuid",
#   "assessment_id": "uuid",
#   "dimension_id": "D1" | null,
#   "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
#   "threshold": 0.75,
#   "actual_score": 0.82,
#   "message": "Security dimension score 0.82 exceeds threshold 0.75",
#   "created_at": "2026-04-19T22:00:00Z",
#   "remediation": {
#     "dimension_id": "D1",
#     "suggestions": ["...", "..."]
#   }
# }
```

### 9.3 KnowledgeBaseAdapter Interface (for D3 Accuracy)

```python
class KnowledgeBaseAdapter(ABC):
    """
    Abstract adapter for factual knowledge verification in D3.

    Implement this to connect to a specific knowledge base
    (Wikipedia, internal KB, custom graph DB, etc.).
    """

    @abstractmethod
    def verify_fact(self, claim: str) -> FactCheckResult:
        """Check a factual claim against the knowledge base."""
        ...

    @abstractmethod
    def batch_verify(self, claims: List[str]) -> List[FactCheckResult]:
        """Check multiple claims in a single batched request."""
        ...

    @abstractmethod
    def get_related_facts(self, entity: str, limit: int = 10) -> List[str]:
        """Get facts related to a given entity."""
        ...
```

### 9.4 NERAdapter Interface (for D5 Privacy)

```python
class NERAdapter(ABC):
    """
    Abstract adapter for Named Entity Recognition in D5.

    Implement this to use a specific NER model or service
    (spaCy, HuggingFace, AWS Comprehend, etc.).
    """

    @abstractmethod
    def detect_pii(
        self,
        text: str,
        entity_types: Optional[List[str]] = None,
    ) -> List[PIILocation]:
        """
        Detect PII entities in text.

        Args:
            text: Text to analyze.
            entity_types: Optional list of PII types to detect.
                         Defaults to all supported types.

        Returns:
            List of PIILocation objects.
        """
        ...

    @abstractmethod
    def supported_entity_types(self) -> List[str]:
        """Return list of supported PII entity types."""
        ...
```

### 9.5 External System Integration Summary

| Integration Point         | Direction | Protocol        | FR Tags |
|---------------------------|-----------|-----------------|---------|
| UQLM API                  | Outbound  | HTTP REST       | FR-R-11, FR-R-12 |
| Alert Callback Webhook    | Outbound  | HTTP POST       | FR-R-6 |
| Alert Queue (future)      | Outbound  | AMQP / Kafka    | FR-R-6 |
| Knowledge Base (D3)       | Outbound  | Abstract Adapter| FR-R-13 |
| NER Service (D5)          | Outbound  | Abstract Adapter| FR-R-13 |
| Persistence (DecisionLog) | Outbound  | Abstract Adapter| FR-R-3, FR-R-10 |

---

## 10. Error Handling Strategy

### 10.1 Exception Hierarchy

```
RiskAssessmentError (base)
├── InputValidationError      # Invalid input (FR-R-1 pre-condition)
├── DimensionAssessmentError  # Individual assessor failure
│   ├── D1AssessmentError
│   ├── D2AssessmentError
│   └── ... (D8AssessmentError)
├── AssessmentPipelineError   # Pipeline-level failures (orchestrator)
├── QuarantineError           # Quarantine logic failure
├── AlertDispatchError        # Alert delivery failure
├── LogPersistenceError       # DecisionLog write/read failure
├── CalibrationError          # ConfidenceCalibration failure
├── DriftDetectionError       # Drift detection computation failure
├── UQLMConnectionError       # Cannot reach UQLM endpoint
├── UQLMTimeoutError          # UQLM request timed out
├── UQLMResponseError         # UQLM returned malformed response
└── ConfigurationError        # Invalid RiskConfig
```

### 10.2 Error Handling Principles

| Principle | Implementation |
|-----------|---------------|
| **Fail gracefully** | `RiskAssessmentEngine.assess()` catches all assessor exceptions and returns `status=FAILED` with error details in `AssessmentResult.metadata["error"]`, rather than propagating exceptions to the caller. |
| **Partial results preserved** | If D3 fails but D1/D2 succeed, dimension results for D1/D2 are preserved in `dimension_results` and only D3 is marked as `FAILED` in metadata. |
| **No silent drops** | Any error condition that prevents full assessment is logged to `DecisionLog` at `ERROR` level and included in the returned `AssessmentResult`. |
| **UQLM is optional** | If `UQLMIntegration` is unavailable or returns an error, the pipeline continues without UQLM signals. `uqlm_uncertainty` is `None` in `DimensionResult.metadata`. |
| **Idempotent operations** | All write operations (`DecisionLog.append`, `EffortTracker.finalize`) are idempotent w.r.t. `assessment_id`; retrying a failed `assess()` call with the same `assessment_id` will not duplicate log entries. |

### 10.3 Retry Strategy

| Operation              | Retry Policy              | Fallback                              |
|------------------------|--------------------------|---------------------------------------|
| UQLM API call          | 3× exponential backoff    | Continue without UQLM signal          |
| Alert callback POST    | 3× exponential backoff    | Log failure; do not block assessment  |
| Persistence write      | 3× retry with same record| Raise `LogPersistenceError` (caller must handle) |

### 10.4 Validation Rules

| Check                               | Error Type               | Behavior                                     |
|-------------------------------------|--------------------------|----------------------------------------------|
| `raw_input` is None or empty        | `InputValidationError`   | Raise immediately; do not assess             |
| `raw_input.content` exceeds 1M chars | `InputValidationError`   | Raise; configurable via `max_content_length`|
| `profile_name` not in config        | `ConfigurationError`    | Raise immediately                            |
| Unknown `dimension_id` in config    | `ConfigurationError`     | Warn on load; reject at assessment time      |
| `assessment_id` collision           | `LogPersistenceError`    | Reject; caller must use a new UUID           |
| UQLM endpoint unreachable           | `UQLMConnectionError`    | Log warning; continue without UQLM            |
| NER adapter returns invalid result  | `DimensionAssessmentError`| Log error; score dimension as 0.5 (neutral) |

---

## 11. Acceptance Criteria

### 11.1 FR Tag Compliance Checklist

| Tag      | Criterion                                                                 | Verification Method                              |
|----------|---------------------------------------------------------------------------|--------------------------------------------------|
| FR-R-1   | All 8 dimensions are always evaluated; no dimension is skipped           | Unit test: mock each assessor; verify all 8 called |
| FR-R-2   | Composite score is weighted sum in [0.0, 1.0]; weights sum to 1.0       | Unit test: multiple profiles with known weights  |
| FR-R-3   | Every `assess()` call creates exactly one `AssessmentRecord` in DecisionLog | Integration test: count records per assess() call |
| FR-R-4   | Calibration reduces ECE over time; `is_calibrated()` returns True after min_samples | Simulation: inject known accuracy; verify ECE decreases |
| FR-R-5   | EffortSummary contains elapsed_time_ms, tokens_used, api_calls           | Unit test: verify all fields populated          |
| FR-R-6   | Alert fires when dimension score > alert_threshold                       | Unit test: set threshold 0.5; score 0.6 → alert created |
| FR-R-7   | Different profiles produce different composite scores                    | Unit test: same input, two profiles → different scores |
| FR-R-8   | Dashboard data is available via `get_recent_assessments()` query          | Integration test: query DecisionLog; verify structure |
| FR-R-9   | `status=QUARANTINED` when any score ≥ quarantine_threshold                | Unit test: score 0.86 ≥ 0.85 → QUARANTINED      |
| FR-R-10  | Export produces valid JSON/CSV with all required fields                   | Integration test: round-trip export → parse      |
| FR-R-11  | UQLM `quantify_uncertainty()` is called when integration is configured    | Mock test: verify UQLMIntegration called         |
| FR-R-12  | Drift detection produces `DriftReport` with z-scores                     | Unit test: inject shifted distribution; verify z_score > 0 |
| FR-R-13  | `AlertManager.evaluate()` populates `remediation_suggestions` in metadata  | Unit test: trigger alert; verify suggestions non-empty |

### 11.2 Non-Functional Requirements

| Requirement        | Target                                           | Measurement          |
|--------------------|--------------------------------------------------|----------------------|
| Latency (P50)      | < 500ms per assessment (excluding UQLM)          | Benchmark test       |
| Latency (P99)      | < 2000ms per assessment (excluding UQLM)          | Benchmark test       |
| Throughput         | ≥ 10 assessments/second (parallel D1–D8)         | Load test            |
| Memory (idle)      | < 100MB baseline                                  | Memory profiling     |
| Memory (per assess)| < 10MB per assessment                             | Memory profiling     |
| Availability       | UQLM failure does not block assessment           | Chaos test           |
| Audit log durability | Append-only; no record loss on crash           | Crash recovery test  |
| Config hot-reload  | Config updates apply without restart              | Runtime update test  |

### 11.3 Test Coverage Requirements

| Component                  | Minimum Coverage |
|----------------------------|------------------|
| RiskAssessmentEngine       | 90% lines        |
| DecisionLog                | 90% lines        |
| ConfidenceCalibration      | 90% lines        |
| EffortTracker              | 90% lines        |
| AlertManager               | 90% lines        |
| Dimensions (each D1–D8)   | 85% lines each   |
| UQLMIntegration            | 80% lines        |
| Config validation          | 90% lines        |
| Error paths (all classes)  | 80% lines        |

### 11.4 Compatibility Requirements

| Item                     | Requirement                                          |
|--------------------------|------------------------------------------------------|
| Python version           | 3.10 – 3.13 (tested in CI)                           |
| PyYAML                   | ≥ 6.0                                               |
| pydantic                 | ≥ 2.0 (for dataclasses and validation)              |
| numpy                    | ≥ 1.24 (for calibration statistics)                  |
| typing_extensions        | ≥ 4.5                                               |
| Optional: scikit-learn   | ≥ 1.3 (for isotonic regression calibration)         |
| Optional: spacy           | ≥ 3.7 (for NER adapter default implementation)       |
| Optional: aiohttp         | ≥ 3.9 (for async UQLM client)                       |

### 11.5 Deliverables Checklist

- [ ] `SPEC.md` — complete specification
- [ ] `ARCHITECTURE.md` — this document
- [ ] `risk_assessment_engine.py` — orchestrator with full implementation
- [ ] `decision_log.py` — append-only log with persistence adapter interface
- [ ] `confidence_calibration.py` — Platt / Isotonic calibration
- [ ] `effort_tracker.py` — effort metrics tracking
- [ ] `alert_manager.py` — threshold evaluation and alert routing
- [ ] `config.py` — typed, serializable configuration
- [ ] `uqlm_integration.py` — UQLM client wrapper
- [ ] `dimensions/base.py` — abstract assessor
- [ ] `dimensions/d1_security.py` through `dimensions/d8_compliance.py` — all 8 assessors
- [ ] `tests/` — unit tests with ≥ 85% coverage per component
- [ ] `05-integration/test_uqlm_integration.py` — integration test for UQLM
- [ ] Configuration file (`config.yaml` or `config.json`) with default profile
- [ ] README with usage examples and API reference
