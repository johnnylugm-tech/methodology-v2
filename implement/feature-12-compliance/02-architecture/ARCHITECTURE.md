# Feature #12 ARCHITECTURE.md — Compliance Layer

## Table of Contents
1. Architecture Overview
2. Component Design
3. API Specifications
4. Data Flow
5. Error Handling Strategy
6. Dependencies

---

## 1. Architecture Overview

### 1.1 Layer 6 Positioning

The Compliance Layer (Layer 6) is the topmost enforcement boundary in the Agent Garden architecture. It sits above Layer 5 (Security) and is responsible for ensuring that all agent behaviors conform to regulatory requirements, internal policy, and risk management tolerances before, during, and after execution.

Position in stack:
```
Layer 7: User Interface / API Gateway
Layer 6: Compliance Layer ← HERE
Layer 5: Security Layer
Layer 4: Routing Layer
Layer 3: Context Management Layer
Layer 2: Memory / State Layer
Layer 1: Foundation Layer
```

Layer 6 is not a passive observer — it is an active gatekeeper with kill-switch authority. It evaluates:
- **Pre-execution**: Is this project/task EU AI Act compliant? What ASL level applies?
- **In-execution**: Does the current operation violate any compliance boundary?
- **Post-execution**: Are audit logs complete? Did override events occur?

### 1.2 Relationships with Other Layers

| Layer | Relationship |
|-------|--------------|
| Layer 1 (Foundation) | Provides base infrastructure: config loading, env vars, logging |
| Layer 2 (Memory) | Reads session state, audit history, previous compliance decisions from memory |
| Layer 3 (Context) | Consumes execution context to build the compliance matrix |
| Layer 4 (Routing) | Receives compliance-verdict from Layer 6 before routing decisions are finalized |
| Layer 5 (Security) | Security and Compliance form a dual-enforcement boundary; Security checks credentials, Compliance checks regulatory alignment |
| Layer 7 (API) | Layer 6 reports feed into API responses and user-facing dashboards |

### 1.3 Design Principles

1. **Fail-closed by default**: Any compliance check that cannot be completed must default to blocking the operation.
2. **Audit everything, override nothing without trail**: OverrideAuditLogger captures every compliance-override event with full context.
3. **Kill-switch is non-negotiable**: KillSwitchMonitor has authority to halt any operation regardless of layer or priority.
4. **Modularity**: Each component (EUAIActChecker, NISTRMFMapper, etc.) is independently testable and replaceable.
5. **Policy-as-code**: All compliance rules are defined in machine-readable policy files, not hardcoded.
6. **Separation of concerns**: Rule evaluation (EUAIActChecker) is separate from verdict reporting (ComplianceReporter) and from override handling (OverrideAuditLogger).

---

## 2. Component Design

### 2.1 EUAIActChecker (`eu_ai_act.py`)

**Module**: `layer6_compliance.eu_ai_act`

**Responsibility**: Evaluate agent project configurations against the EU AI Act (Regulation (EU) 2024/1689). Determine risk classification (Unacceptable / High-Risk / Limited-Risk / Minimal-Risk) and generate a structured compliance verdict.

**Public API**:
```python
class EUAIActChecker:
    def check_compliance(self, project_config: dict) -> ComplianceResult
    """
    Evaluate a project config against EU AI Act categories.
    :param project_config: dict with keys: project_type, sector, autonomy_level,
                            data_inputs, output_type, deployment_context
    :returns: ComplianceResult with verdict, risk_category, applicable_articles
    """

    def generate_report(self) -> EUAIActReport
    """
    Generate a human-readable EU AI Act compliance report.
    :returns: EUAIActReport with full article citations and remediation guidance
    """

    def get_violations(self) -> list[Violation]
    """
    Return all detected EU AI Act violations from the last check.
    :returns: list[Violation] sorted by severity descending
    """

    def get_risk_category(self) -> str
    """
    Return the determined risk category: unacceptable | high_risk | limited_risk | minimal_risk
    """
```

**Internal State**:
- `self._last_config`: The config most recently evaluated
- `self._violations`: list[Violation] from last check
- `self._risk_category`: str determined from last check
- `self._policy_rules`: Loaded EU AI Act rule set (cached)

**Boundaries**:
- Inputs from: Layer 3 context (via project_config dict)
- Outputs to: ComplianceMatrixGenerator (risk category input), ComplianceReporter (violation list)
- Reads from: Policy files at `policies/eu_ai_act_v1.json`

---

### 2.2 NISTRMFMapper (`nist_rmf.py`)

**Module**: `layer6_compliance.nist_rmf`

**Responsibility**: Map EU AI Act risk classifications and operational scenarios to NIST Risk Management Framework (R800-37) control families. Generates a control-mapping table used for compliance reporting and audit evidence.

**Public API**:
```python
class NISTRMFMapper:
    def map_controls(self, eu_risk_category: str, scenario: dict) -> list[NISTControl]
    """
    Map an EU AI Act risk category + operational scenario to NIST RMF controls.
    :param eu_risk_category: str from EUAIActChecker (unacceptable|high_risk|limited_risk|minimal_risk)
    :param scenario: dict with keys: autonomy_level, data_sensitivity, output_impact, sector
    :returns: list of matched NISTControl objects
    """

    def get_control_families(self) -> list[str]
    """
    Return all NIST RMF control family identifiers (e.g. AC, AU, RA, SC).
    """

    def get_control_details(self, control_id: str) -> NISTControl
    """
    Get full detail for a specific control ID (e.g. 'AC-2', 'AU-6').
    :param control_id: str
    :returns: NISTControl with description, enhancement, applicability
    """

    def generate_mapping_report(self) -> NISTMappingReport
    """
    Generate a full NIST RMF mapping report for the last mapped scenario.
    """
```

**Internal State**:
- `self._current_mappings`: list[NISTControl] from last map_controls call
- `self._control_catalog`: NIST RMF control database (loaded from `policies/nist_rmf_controls.json`)
- `self._last_scenario`: dict

**Boundaries**:
- Inputs from: EUAIActChecker (risk category), Layer 3 context
- Outputs to: ComplianceMatrixGenerator (control list), ComplianceReporter (mapping report)
- Policy file: `policies/nist_rmf_controls.json`

---

### 2.3 ASLLevelDetector (embedded in `compliance_matrix.py`)

**Module**: `layer6_compliance.compliance_matrix`

**Responsibility**: Determine the Agent Safety Level (ASL) for a given project/task based on the output of EUAIActChecker and NISTRMFMapper. ASL levels gate what operations are permitted and what kill-switch thresholds apply.

ASL Levels:
- **ASL-0**: Minimal risk (no special restrictions)
- **ASL-1**: Limited risk (disclosure requirements apply)
- **ASL-2**: High risk (human oversight required, enhanced logging)
- **ASL-3**: High risk + autonomous capability (kill-switch mandatory, 3-party review)
- **ASL-4**: Unacceptable risk (operation prohibited)

**Public API**:
```python
class ASLLevelDetector:
    def detect_level(self, eu_risk_category: str, nist_controls: list[NISTControl], 
                     project_metadata: dict) -> ASLLevel:
    """
    Determine the ASL level for a project.
    :param eu_risk_category: str from EUAIActChecker
    :param nist_controls: list of NISTControl from NISTRMFMapper
    :param project_metadata: dict with autonomy_score, capability_flags, deployment_context
    :returns: ASLLevel enum value (ASL0–ASL4)
    """

    def get_level_requirements(self, level: ASLLevel) -> ASLRequirements
    """
    Return the full requirements spec for a given ASL level.
    :param level: ASLLevel enum
    :returns: ASLRequirements with permitted_ops, required_oversight, kill_switch_config
    """

    def is_operation_allowed(self, operation: str, current_level: ASLLevel) -> bool
    """
    Check if a specific operation is permitted at the given ASL level.
    :param operation: str operation identifier
    :param current_level: ASLLevel enum
    :returns: bool
    """
```

**Internal State**:
- `self._current_level`: ASLLevel enum
- `self._level_requirements`: ASLRequirements cache
- `self._aslm_table`: ASL determination table loaded from `policies/aslm_table.json`

**Boundaries**:
- Inputs from: EUAIActChecker, NISTRMFMapper
- Outputs to: ComplianceMatrixGenerator, KillSwitchMonitor

---

### 2.4 ComplianceMatrixGenerator (`compliance_matrix.py`)

**Module**: `layer6_compliance.compliance_matrix`

**Responsibility**: Aggregate outputs from EUAIActChecker, NISTRMFMapper, and ASLLevelDetector into a single, canonical ComplianceMatrix object. This matrix is the single source of truth for all compliance decisions during the lifecycle of a project.

**Public API**:
```python
class ComplianceMatrixGenerator:
    def generate_matrix(self, project_config: dict) -> ComplianceMatrix
    """
    Generate a full ComplianceMatrix for a project.
    :param project_config: dict with project_type, sector, autonomy_level, etc.
    :returns: ComplianceMatrix with all sub-results assembled
    """

    def update_matrix(self, matrix_id: str, delta: dict) -> ComplianceMatrix
    """
    Apply an incremental update to an existing matrix (e.g. new NIST controls discovered).
    :param matrix_id: str UUID of existing matrix
    :param delta: dict of changed fields
    :returns: Updated ComplianceMatrix
    """

    def get_matrix(self, matrix_id: str) -> ComplianceMatrix
    """
    Retrieve an existing ComplianceMatrix by ID.
    """

    def validate_matrix(self, matrix: ComplianceMatrix) -> ValidationResult
    """
    Validate matrix completeness and internal consistency.
    :returns: ValidationResult with errors/warnings
    """
```

**Internal State**:
- `self._matrices`: dict[str, ComplianceMatrix] — in-memory matrix store
- `self._eu_checker`: EUAIActChecker instance
- `self._nist_mapper`: NISTRMFMapper instance
- `self._asl_detector`: ASLLevelDetector instance

**Boundaries**:
- Inputs from: All three sub-components
- Outputs to: ComplianceReporter, KillSwitchMonitor, Layer 4 (Routing)
- Stores matrices in: Layer 2 (Memory) for persistence

---

### 2.5 ComplianceReporter (`compliance_reporter.py`)

**Module**: `layer6_compliance.compliance_reporter`

**Responsibility**: Generate structured compliance reports for human consumption (auditors, regulators, stakeholders). Supports multiple output formats: JSON (machine-readable), PDF (regulatory submission), HTML (internal dashboard).

**Public API**:
```python
class ComplianceReporter:
    def generate_audit_report(self, matrix_id: str, format: str = "json") -> ComplianceAuditReport
    """
    Generate a full audit report from a ComplianceMatrix.
    :param matrix_id: str UUID
    :param format: json|pdf|html
    :returns: ComplianceAuditReport (subclass of base Report)
    """

    def generate_delta_report(self, matrix_id: str, since_date: datetime) -> DeltaReport
    """
    Generate a delta report covering changes since a given date.
    :param matrix_id: str
    :param since_date: datetime
    """

    def generate_violation_summary(self, matrix_id: str) -> ViolationSummary
    """
    Generate a violation summary report.
    """

    def export_to_policy_doc(self, matrix_id: str, output_path: str) -> bool
    """
    Export compliance matrix to a policy document at the given path.
    :param output_path: str local file path
    :returns: bool success
    """
```

**Internal State**:
- `self._reports`: dict[str, ComplianceAuditReport]
- `self._formatter_registry`: dict[str, ReportFormatter] (json, pdf, html)
- `self._last_matrix_id`: str

**Boundaries**:
- Inputs from: ComplianceMatrixGenerator, OverrideAuditLogger
- Outputs to: File system (reports/), API responses, regulatory submission endpoints

---

### 2.6 KillSwitchMonitor (`killswitch_compliance.py`)

**Module**: `layer6_compliance.killswitch_compliance`

**Responsibility**: Active monitoring of running agent operations for compliance boundary violations. Has kill-switch authority — can terminate any operation that crosses an ASL-defined boundary. Monitors both pre-configured thresholds and dynamic anomaly signals.

**Public API**:
```python
class KillSwitchMonitor:
    def __init__(self, killswitch_config: KillswitchConfig):
        """
        Initialize with kill-switch thresholds per ASL level.
        """

    def monitor(self, operation_context: OperationContext) -> KillSwitchVerdict
    """
        Monitor an ongoing operation and return a verdict.
        :param operation_context: OperationContext with current_operation, elapsed_time,
                                   memory_snapshot, output_samples
        :returns: KillSwitchVerdict (pass | warning | halt)
        """

    def halt(self, operation_id: str, reason: str, halt_type: HaltType) -> HaltRecord
        """
        Execute a kill-switch halt. Records the halt event and signals Layer 4 to terminate.
        :param operation_id: str
        :param reason: str human-readable reason
        :param halt_type: HaltType (soft_halt | hard_halt | emergency_stop)
        :returns: HaltRecord with timestamp, snapshot, and context
        """

    def get_killswitch_status(self) -> KillswitchStatus
        """
        Return current kill-switch system status (active/inactive/triggered).
        """

    def register_health_check(self, health_check_fn: Callable) -> None
        """
        Register a health-check callback invoked before each monitoring cycle.
        """
```

**Internal State**:
- `self._config`: KillswitchConfig with per-ASL thresholds
- `self._status`: KillswitchStatus enum
- `self._halt_history`: list[HaltRecord]
- `self._health_checks`: list[Callable]
- `self._last_verdict`: KillSwitchVerdict

**Boundaries**:
- Inputs from: Layer 3 (operation context), Layer 2 (memory snapshots), ASLLevelDetector
- Outputs to: Layer 4 (routing — halt signal), OverrideAuditLogger (halt events), ComplianceReporter (halt reports)
- External: OS signals, process termination APIs

**Halt Types**:
- `soft_halt`: Pause operation, retain state, require compliance review before resume
- `hard_halt`: Terminate operation immediately, retain memory state for audit
- `emergency_stop`: Immediate termination with minimal state retention (reserved for ASL-4 violations)

---

### 2.7 OverrideAuditLogger (`audit_trail.py`)

**Module**: `layer6_compliance.audit_trail`

**Responsibility**: Immutable audit trail for all compliance override events. Any time a human or privileged process overrides a compliance verdict or kill-switch determination, this component logs the event with full context including: who/what/when/why/后果. This log is the primary evidence artifact for regulatory audits.

**Public API**:
```python
class OverrideAuditLogger:
    def log_override(self, override_event: OverrideEvent) -> str
        """
        Record a compliance override event and return the audit entry ID.
        :param override_event: OverrideEvent with actor, original_verdict, override_reason,
                                override_authority, consequence_preview
        :returns: str audit_entry_id (UUID)
        """

    def log_killswitch_bypass(self, bypass_event: KillswitchBypassEvent) -> str
        """
        Log a deliberate kill-switch bypass (requires elevated privilege).
        :param bypass_event: KillswitchBypassEvent with actor, target_operation,
                            bypass_reason, escalation_chain
        :returns: str audit_entry_id
        """

    def query_audit_log(self, query: AuditQuery) -> list[AuditEntry]
        """
        Query the audit log with filters.
        :param query: AuditQuery with filters: actor, time_range, event_type, operation_id
        :returns: list[AuditEntry] matching query
        """

    def get_chain_of_custody(self, operation_id: str) -> list[AuditEntry]
        """
        Get the full chain-of-custody record for an operation.
        :param operation_id: str
        :returns: list[AuditEntry] in chronological order
        """

    def verify_integrity(self, log_id: str) -> IntegrityVerificationResult
        """
        Verify the integrity of an audit log entry (hash chain verification).
        :param log_id: str
        :returns: IntegrityVerificationResult with status, computed_hash, stored_hash
        """
```

**Internal State**:
- `self._log_store`: AuditLogStore (append-only, backed by Layer 2 memory)
- `self._hash_chain`: dict[str, str] — entry_id → SHA-256 of (previous_entry_hash + current_entry_payload)
- `self._pending_flush`: list[AuditEntry] — buffered entries awaiting persistence
- `self._integrity_salt`: str — per-instance salt for hash chain

**Boundaries**:
- Inputs from: All Layer 6 components (as source of override events), Layer 4 (routing overrides)
- Outputs to: ComplianceReporter (audit data), Layer 2 (persistence), regulatory submission endpoint
- External: SIEM integration endpoint (optional), immutable log archival

**Audit Entry Schema**:
```python
@dataclass
class AuditEntry:
    entry_id: str           # UUID v4
    timestamp: datetime     # ISO 8601 with timezone
    event_type: str         # override | killswitch_bypass | killswitch_halt | verdict_change
    actor: str              # user_id or system_component
    operation_id: str
    original_state: dict    # snapshot before the override
    new_state: dict          # snapshot after the override
    reason: str             # human-provided justification
    authority_level: str    # user_override | admin_override | system_auto
    hash_previous: str      # SHA-256 of previous entry
    hash_current: str       # SHA-256 of this entry's payload
    metadata: dict          # additional context
```

---

## 3. API Specifications

### 3.1 Core Data Types

```python
# EU AI Act types
@dataclass
class ComplianceResult:
    verdict: str                    # compliant | non_compliant | conditional
    risk_category: str              # unacceptable | high_risk | limited_risk | minimal_risk
    applicable_articles: list[str]  # e.g. ["Art.5", "Art.10", "Art.14"]
    violations: list[Violation]
    timestamp: datetime
    matrix_id: str                 # links to the originating ComplianceMatrix

@dataclass
class Violation:
    id: str
    severity: str                  # critical | major | minor
    article: str                   # EU AI Act article reference
    description: str
    remediation: str
    affected_controls: list[str]   # NIST control IDs

@dataclass
class EUAIActReport:
    risk_category: str
    full_assessment: dict
    article_citations: list[dict]
    remediation_plan: list[dict]
    compliance_score: float         # 0.0–1.0

# NIST RMF types
@dataclass
class NISTControl:
    control_id: str                # e.g. "AC-2", "AU-6", "RA-5"
    family: str                    # e.g. "AC", "AU", "RA"
    title: str
    description: str
    enhancement: str | None
    applicability: str             # always | conditional | never
    maturity_level: str            # NIST defines this

@dataclass
class NISTMappingReport:
    eu_risk_category: str
    mapped_controls: list[NISTControl]
    control_coverage: dict         # control_id → coverage_percentage
    gaps: list[str]                # controls with no EU AI Act mapping

# ASL types
@dataclass
class ASLLevel:
    level: int                     # 0–4
    name: str                      # e.g. "ASL-0", "ASL-3"
    description: str

@dataclass
class ASLRequirements:
    level: ASLLevel
    permitted_operations: list[str]
    prohibited_operations: list[str]
    required_oversight: str        # none | human_in_loop | human_on_loop | three_party_review
    kill_switch_thresholds: dict
    logging_requirements: list[str]

# ComplianceMatrix
@dataclass
class ComplianceMatrix:
    matrix_id: str                 # UUID v4
    created_at: datetime
    updated_at: datetime
    project_config: dict
    eu_result: ComplianceResult
    nist_mappings: list[NISTControl]
    asl_level: ASLLevel
    asl_requirements: ASLRequirements
    kill_switch_config: KillswitchConfig
    status: str                    # active | archived | superseded

# Kill-switch types
@dataclass
class KillSwitchVerdict:
    status: str                    # pass | warning | halt
    active_thresholds: list[str]   # which thresholds are currently evaluated
    metrics: dict                  # current metric values
    reason: str | None

@dataclass
class HaltRecord:
    halt_id: str
    operation_id: str
    halt_type: str                 # soft_halt | hard_halt | emergency_stop
    timestamp: datetime
    reason: str
    state_snapshot: dict          # captured operation state at halt time

# Override types
@dataclass
class OverrideEvent:
    event_id: str                  # UUID v4
    timestamp: datetime
    actor: str
    operation_id: str
    original_verdict: str
    override_reason: str
    consequence_preview: str
    authority_level: str

@dataclass
class KillswitchBypassEvent:
    event_id: str
    timestamp: datetime
    actor: str
    target_operation: str
    bypass_reason: str
    escalation_chain: list[str]   # list of approver IDs
```

### 3.2 Component Method Signatures (Full Reference)

**EUAIActChecker**
```python
def check_compliance(self, project_config: dict) -> ComplianceResult
def generate_report(self) -> EUAIActReport
def get_violations(self) -> list[Violation]
def get_risk_category(self) -> str
def _load_policy_rules(self) -> dict   # internal
```

**NISTRMFMapper**
```python
def map_controls(self, eu_risk_category: str, scenario: dict) -> list[NISTControl]
def get_control_families(self) -> list[str]
def get_control_details(self, control_id: str) -> NISTControl
def generate_mapping_report(self) -> NISTMappingReport
def _load_control_catalog(self) -> dict  # internal
```

**ASLLevelDetector**
```python
def detect_level(self, eu_risk_category: str, nist_controls: list[NISTControl],
                 project_metadata: dict) -> ASLLevel
def get_level_requirements(self, level: ASLLevel) -> ASLRequirements
def is_operation_allowed(self, operation: str, current_level: ASLLevel) -> bool
def _load_aslm_table(self) -> dict  # internal
```

**ComplianceMatrixGenerator**
```python
def generate_matrix(self, project_config: dict) -> ComplianceMatrix
def update_matrix(self, matrix_id: str, delta: dict) -> ComplianceMatrix
def get_matrix(self, matrix_id: str) -> ComplianceMatrix
def validate_matrix(self, matrix: ComplianceMatrix) -> ValidationResult
```

**ComplianceReporter**
```python
def generate_audit_report(self, matrix_id: str, format: str = "json") -> ComplianceAuditReport
def generate_delta_report(self, matrix_id: str, since_date: datetime) -> DeltaReport
def generate_violation_summary(self, matrix_id: str) -> ViolationSummary
def export_to_policy_doc(self, matrix_id: str, output_path: str) -> bool
```

**KillSwitchMonitor**
```python
def __init__(self, killswitch_config: KillswitchConfig)
def monitor(self, operation_context: OperationContext) -> KillSwitchVerdict
def halt(self, operation_id: str, reason: str, halt_type: HaltType) -> HaltRecord
def get_killswitch_status(self) -> KillswitchStatus
def register_health_check(self, health_check_fn: Callable) -> None
```

**OverrideAuditLogger**
```python
def log_override(self, override_event: OverrideEvent) -> str
def log_killswitch_bypass(self, bypass_event: KillswitchBypassEvent) -> str
def query_audit_log(self, query: AuditQuery) -> list[AuditEntry]
def get_chain_of_custody(self, operation_id: str) -> list[AuditEntry]
def verify_integrity(self, log_id: str) -> IntegrityVerificationResult
```

---

## 4. Data Flow

### 4.1 Compliance Matrix Generation Flow

```
User/API Request (project_config)
        │
        ▼
ComplianceMatrixGenerator.generate_matrix(config)
        │
        ├──────────────────────────────┐
        ▼                              ▼
EUAIActChecker                    NISTRMFMapper
.check_compliance(config)        .map_controls(risk_category, scenario)
        │                              │
        ▼                              │
EU Risk Category                      ▼
        │                   NIST Controls List
        │                              │
        └──────────┬───────────────────┘
                   ▼
          ASLLevelDetector.detect_level()
                   │
                   ▼
             ASL Level (ASL0-4)
                   │
                   ▼
          ComplianceMatrix (assembled)
                   │
        ┌──────────┴──────────────┐
        ▼                         ▼
ComplianceReporter              KillSwitchMonitor
.generate_audit_report()       .configure(matrix)
        │                         │
        ▼                         ▼
  JSON/PDF/HTML Report      Kill-Switch Thresholds Set
                                 │
                                 ▼
                         Layer 4 Routing Layer
                        (receives kill-switch config)
```

### 4.2 Runtime Monitoring Flow

```
Agent Operation Running
        │
        ▼
KillSwitchMonitor.monitor(operation_context)
        │
        ├── [verdict=pass] ──► Continue execution
        │
        ├── [verdict=warning] ──► Log to OverrideAuditLogger
        │                            Log alert to ComplianceReporter
        │                            Continue (with warning flag)
        │
        └── [verdict=halt] ──► KillSwitchMonitor.halt()
                                    │
                                    ▼
                            HaltRecord created
                                    │
                ┌───────────────────┼────────────────────┐
                ▼                   ▼                    ▼
        OverrideAuditLogger   ComplianceReporter   Layer 4 Routing
        .log_halt_event()      .generate_halt_report()  (terminate op)
```

### 4.3 Override Audit Flow

```
Human/Admin Override Request
        │
        ▼
OverrideAuditLogger.log_override(override_event)
        │
        ├── Validate authority_level (must be user_override or admin_override)
        ├── Compute hash chain entry
        ├── Append to audit log (append-only)
        ├── Notify ComplianceReporter of override event
        │
        ▼
ComplianceReporter.include_in_next_report(override_event)
        │
        ▼
Regulatory Submission / Audit Pack
```

### 4.4 Kill-Switch Bypass Flow (Elevated Privilege Required)

```
KillSwitchMonitor verdict = halt
        │
        ▼
Privileged actor requests bypass
        │
        ▼
OverrideAuditLogger.log_killswitch_bypass(bypass_event)
        ├── Requires escalation_chain (list of approvers)
        ├── Actor must have system_admin authority
        ├── All approvals must be recorded
        │
        ▼
KillSwitchMonitor acknowledges bypass (temporary)
        │
        ▼
Operation resumes with bypass flag set
        │
        ▼
Post-incident review flagged automatically
```

---

## 5. Error Handling Strategy

### 5.1 Component-Level Exception Handling

| Component | Exception Types | Handling Strategy |
|----------|---------------|-------------------|
| `EUAIActChecker` | `PolicyLoadError`, `InvalidConfigError`, `UnknownRiskCategoryError` | Fall back to `minimal_risk` as default (fail-open for risk category only; violations are still captured); raise `ComplianceCheckError` if policy file is missing or corrupt |
| `NISTRMFMapper` | `ControlNotFoundError`, `PolicyLoadError` | Log warning and return empty control list; log to `ComplianceReporter` as partial mapping; do not block matrix generation |
| `ASLLevelDetector` | `ASLMTableError`, `AmbiguousLevelError` | Raise `ComplianceCheckError`; do not guess ASL level; operation must not proceed without a valid ASL level |
| `ComplianceMatrixGenerator` | `MatrixNotFoundError`, `ValidationError`, `SubComponentError` | If sub-component fails, mark matrix as `partial`; generate partial matrix with available data; report partial status via `ValidationResult` |
| `ComplianceReporter` | `ReportGenerationError`, `FormatNotSupportedError`, `FileWriteError` | Return error report in JSON format (fallback); attempt file write to error log directory if primary output fails |
| `KillSwitchMonitor` | `MonitorError`, `HealthCheckError`, `HaltExecutionError` | On health-check failure: pause monitoring for 60s and retry; if retry fails, trigger `soft_halt` on all active operations as precaution; never let monitoring silently fail |
| `OverrideAuditLogger` | `LogWriteError`, `IntegrityError`, `AuditQueryError` | If log write fails: buffer in-memory (max 100 entries); attempt async flush to Layer 2; if integrity check fails on existing entry: flag entry as `integrity_warning` (do not delete); raise `AuditLogError` for query errors on corrupted entries |

### 5.2 Cross-Component Error Propagation

```
Sub-component error
        │
        ▼
ComplianceMatrixGenerator catches SubComponentError
        │
        ├── Marks matrix as partial
        ├── Logs sub-component failure detail
        │
        ▼
ComplianceReporter generates partial matrix report
        │
        ▼
KillSwitchMonitor receives partial matrix
        │
        ├── Sets heightened monitoring mode (more conservative thresholds)
        └── Does not block monitoring, but logs "matrix incomplete" warning
```

### 5.3 Fallback Strategy Matrix

| Failure Scenario | Fallback Behavior |
|-----------------|------------------|
| EU AI Act policy file missing | Block EU AI Act checks; fall back to NIST-only assessment; flag as `conditional` |
| NIST control catalog missing | Use minimal NIST control set (AC-2, AU-6, RA-5); flag gaps in report |
| ASL determination table missing | Default to ASL-2 (conservative); require human review before operation |
| Kill-switch config missing | Use conservative defaults (all operations monitored at 30s intervals) |
| Memory (Layer 2) unavailable | Buffer audit logs in memory; block generation of ComplianceMatrix until Layer 2 is restored |
| Regulatory submission endpoint unavailable | Queue reports locally; retry with exponential backoff (max 3 retries); alert via OverrideAuditLogger |

### 5.4 Circuit Breaker Configuration

```python
class CircuitBreakerConfig:
    # For KillSwitchMonitor's health check circuit breaker
    failure_threshold: int = 3          # Open circuit after 3 consecutive health-check failures
    recovery_timeout_seconds: int = 60  # Attempt recovery after 60 seconds
    half_open_max_calls: int = 1        # Allow 1 probe call in half-open state

    # For external dependency (regulatory submission)
    failure_threshold: int = 5
    recovery_timeout_seconds: int = 300
    half_open_max_calls: int = 2
```

### 5.5 Kill-Switch Failure Modes

| Mode | Trigger Condition | Behavior |
|------|-----------------|----------|
| Silent skip | Monitoring thread dies silently | External watchdog detects no heartbeat for 30s → triggers OS-level process alert → graceful shutdown |
| False negative | All checks pass but violation exists | Post-execution audit by OverrideAuditLogger flags discrepancy → triggers compliance review |
| False positive | Operation wrongly halted | OverrideAuditLogger logs override with full context → human review required before operation resumes |
| Bypass without log | External actor bypasses without audit | Integrity verification in OverrideAuditLogger detects missing entries → alerts and flags chain-of-custody gap |

---

## 6. Dependencies

### 6.1 Internal Dependencies (Intra-Framework)

| Dependency | Source Module | Target Module | Type |
|-----------|--------------|---------------|------|
| ComplianceMatrix | compliance_matrix.py | all Layer 6 | Data |
| KillswitchConfig | killswitch_compliance.py | KillSwitchMonitor | Config |
| ASLLevel | compliance_matrix.py | KillSwitchMonitor | Enum |
| NISTControl | nist_rmf.py | ComplianceMatrixGenerator | Data |
| ComplianceResult | eu_ai_act.py | ComplianceMatrixGenerator | Data |
| AuditEntry | audit_trail.py | ComplianceReporter | Data |
| HaltRecord | killswitch_compliance.py | OverrideAuditLogger | Data |
| Layer 2 Memory | memory layer | All Layer 6 components | Persistence |
| Layer 3 Context | context layer | EUAIActChecker, NISTRMFMapper | Context input |
| Layer 4 Routing | routing layer | KillSwitchMonitor (halt signal) | Control flow |
| Layer 5 Security | security layer | KillSwitchMonitor (credential check) | Auth |

### 6.2 External Dependencies

| Library | Version | Purpose | Fallback if Unavailable |
|---------|---------|--------|----------------------|
| Python standard library | 3.11+ | Core runtime | N/A (required) |
| `pydantic` | ≥ 2.0 | Data validation for ComplianceResult, Violation, NISTControl, etc. | Use `dataclasses` with manual validation |
| `cryptography` | ≥ 41.0 | SHA-256 hash chain for audit integrity | Use `hashlib` (standard library) |
| `uuid` | standard lib | UUID generation for matrix_id, entry_id | Use `secrets` module |
| `datetime` | standard lib | Timestamps | Use `time.time()` as fallback |
| `json` | standard lib | Policy file loading | Use `yaml` if JSON unavailable |
| `yaml` | ≥ 6.0 | Policy file parsing (optional) | JSON-only if unavailable |
| `logging` | standard lib | Component-level logging | Use `print` as fallback |
| `threading` | standard lib | KillSwitchMonitor health-check thread | Use `multiprocessing` if unavailable |
| `hashlib` | standard lib | SHA-256 for audit hash chain | N/A (standard library) |
| `functools` | standard lib | `lru_cache` for control catalog caching | Manual memoization |

### 6.3 Policy Files (Data Dependencies)

| File | Location | Format | Loaded By |
|------|---------|--------|----------|
| `eu_ai_act_v1.json` | `policies/` | JSON | EUAIActChecker |
| `nist_rmf_controls.json` | `policies/` | JSON | NISTRMFMapper |
| `aslm_table.json` | `policies/` | JSON | ASLLevelDetector |
| `killswitch_thresholds.json` | `policies/` | JSON | KillSwitchMonitor |
| `audit_trail_schema.json` | `policies/` | JSON | OverrideAuditLogger |

### 6.4 Test Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥ 7.0 | Unit testing for all components |
| `pytest-cov` | ≥ 4.0 | Coverage reporting |
| `pytest-mock` | ≥ 3.0 | Mocking for sub-component dependencies |
| `hypothesis` | ≥ 6.0 | Property-based testing for compliance logic |

---

*Document version: 1.0 — Feature #12 Phase 2 (Architecture)*
*Next: Component Implementation → Feature #12 Phase 3*
