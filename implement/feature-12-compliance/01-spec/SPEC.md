# Feature #12 SPEC.md — Compliance Layer (EU AI Act · NIST AI RMF · RSP v3.0)

> **Version**: v1.0.0
> **Feature ID**: FR-12X
> **Layer**: 6 - Compliance
> **Framework**: methodology-v2
> **Status**: Draft
> **Author**: Developer Agent
> **Date**: 2026-04-22

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Regulatory Mapping](#2-regulatory-mapping)
3. [Functional Requirements](#3-functional-requirements)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [Acceptance Criteria](#5-acceptance-criteria)
6. [Compliance Matrix](#6-compliance-matrix)
7. [Component Specifications](#7-component-specifications)
8. [User Scenarios](#8-user-scenarios)
9. [Dependencies](#9-dependencies)
10. [Out of Scope](#10-out-of-scope)
11. [Glossary](#11-glossary)

---

## 1. Feature Overview

### 1.1 Purpose

Feature #12 is the Compliance Layer (Layer 6) of methodology-v2. Its purpose is to:

1. **Map** all methodology-v2 mechanisms to EU AI Act Article 14 requirements
2. **Map** methodology-v2 functions to NIST AI RMF (Risk Management Framework) functions
3. **Align** autonomous coding levels with Anthropic RSP v3.0 ASL (AI Safety Level)
4. **Generate** automated compliance reports for audit trails
5. **Enforce** regulatory constraints through the Gate policy and Kill-switch

### 1.2 Scope

| Dimension | Description |
|-----------|-------------|
| Layer | 6 (Compliance) |
| Phase Integration | All Phases (1-7) via TRACEABILITY_MATRIX |
| Output Artifacts | `compliance_matrix.json`, `compliance_report.md` |
| Regulatory Frameworks | EU AI Act Art.14, NIST AI RMF, Anthropic RSP v3.0 |
| Dependents | HITL/HOTL (Feature #6), Kill-switch (Feature #6), Langfuse (Feature #5) |

### 1.3 Relationship to Existing Components

```
Methodology-v2 Components          Compliance Layer
─────────────────────────────────────────────────────────────────
Agents.md                      →  eu_ai_act.py (Art.14(4)(a))
Constitution                   →  nist_rmf.py (Govern)
Phase 1 TRACEABILITY_MATRIX  →  nist_rmf.py (Map)
Langfuse metrics + UAF/CLAP   →  nist_rmf.py (Measure)
Gate policy + Kill-switch     →  nist_rmf.py (Manage)
HITL G1/G4                     →  rsp对接 (ASL-3 mandatory sign-off)
```

### 1.4 Implementation Structure

```
compliance/
├── __init__.py                    # Module exports
├── eu_ai_act.py                  # EU AI Act Article 14 mapping
├── nist_rmf.py                   # NIST AI RMF function mapping
├── compliance_matrix.py          # Unified compliance matrix
└── compliance_reporter.py        # Automated report generation
```

---

## 2. Regulatory Mapping

### 2.1 EU AI Act Article 14 — Human Oversight

Article 14 requires that high-risk AI systems are designed to allow effective human oversight. The following table maps each sub-requirement to methodology-v2 mechanisms:

| Article | Sub-Requirement | Description | v3.0 Mechanism | Implementation |
|---------|----------------|-------------|-----------------|-----------------|
| 14(1) | human oversight | Providers must ensure oversight by natural persons | HITL/HOTL分级 | G1=HOOTL, G2=HOTL, G3=HITL, G4=HITL+sign-off |
| 14(4)(a) | understand AI limits | Operators can understand AI capabilities and limitations | Agents.md + model card | `ModelCardGenerator` + `AgentsMetadataExporter` |
| 14(4)(b) | automation bias awareness | System prevents undue reliance on AI outputs | DA + UAF warnings | `DebateAgent` challenge + `UncertaintyAggregator` alerts |
| 14(4)(c) | interpret outputs | Operators can interpret AI outputs | Langfuse trace viewer | `TraceInterpreter` + Langfuse session export |
| 14(4)(d) | human override | Operators can override decisions | HITL Gate | `HumanOverrideGate` + `OverrideAuditLog` |
| 14(4)(e) | interrupt system | Operators can interrupt AI operation | Kill-switch (<5s) | `KillSwitchExecutor` with ≤5s shutdown |

### 2.2 NIST AI RMF Mapping

The NIST AI RMF provides a four-function framework: Govern, Map, Measure, Manage. Each is mapped to methodology-v2 mechanisms:

| NIST AI RMF Function | Description | v3.0 Mechanism | Component |
|---------------------|-------------|----------------|------------|
| **Govern** | Establish and oversee AI risk management governance | Constitution + Agents.md | `ConstitutionComplianceChecker`, `AgentsMetadataExporter` |
| **Map** | Characterize AI risks in context | TRACEABILITY_MATRIX (Phase 1) | `TraceabilityMatrixGenerator` |
| **Measure** | Analyze and assess AI risks | Langfuse metrics + UAF/CLAP | `LangfuseMetricsCollector`, `UncertaintyAggregator`, `CalibrationChecker` |
| **Manage** | Prioritize and act on AI risks | Gate policy + Kill-switch | `GatePolicyEngine`, `KillSwitchExecutor` |

### 2.3 Anthropic RSP v3.0 ASL Alignment

The Anthropic Responsible Scaling Policy v3.0 defines four AI Safety Levels (ASL). The following table maps ASL levels to methodology-v2 deployment conditions:

| ASL Level | Description | v3.0 Requirement | Trigger |
|-----------|-------------|-------------------|---------|
| **ASL-1** | Minimal risk | No special requirements | Default |
| **ASL-2** | Limited risk (chatbots, image generation) | HOTL (Human on the Loop) | `hotl_required=True` in project config |
| **ASL-3** | High risk (autonomous coding, scientific research) | HITL G1/G4 mandatory sign-off | `hitl_required=True` + `g4_approval=True` |
| **ASL-4** | Critical risk | **NOT RECOMMENDED** for v3.0 | `asl4_warning=True` in config |

**Note:** ASL-4 corresponds to AGI-level autonomous systems. Current methodology-v2 v3.0 does not support ASL-4 deployment due to insufficient safety guarantees. Organizations requiring ASL-4 must implement additional safeguards beyond this specification.

### 2.4 Regulatory Cross-Reference Matrix

| Requirement | EU AI Act Art.14 | NIST Govern | NIST Map | NIST Measure | NIST Manage | RSP ASL-3 |
|-------------|:----------------:|:-----------:|:--------:|:------------:|:-----------:|:---------:|
| Human oversight分级 | 14(1) | ✅ | — | — | — | ✅ |
| AI limits documentation | 14(4)(a) | ✅ | — | — | — | — |
| Automation bias prevention | 14(4)(b) | — | — | ✅ | — | — |
| Output interpretability | 14(4)(c) | — | — | ✅ | — | — |
| Human override capability | 14(4)(d) | — | — | — | ✅ | ✅ |
| Interrupt/Kill-switch | 14(4)(e) | — | — | — | ✅ | ✅ |

---

## 3. Functional Requirements

### 3.1 Core Features

#### [FR-12-01] EU AI Act Article 14 Compliance Checker

**Description:** Verify that all AI system operations comply with EU AI Act Article 14 human oversight requirements.

**Inputs:**
- Project configuration (`project_config.yaml`)
- HITL/HOTL assignment records
- Kill-switch configuration
- Model cards and Agents.md metadata

**Processing:**
1. Validate HITL/HOTL分级 has been assigned to all AI system tasks
2. Verify model cards exist for all deployed models
3. Confirm Kill-switch response time ≤5 seconds
4. Check human override mechanisms are in place

**Outputs:**
- `eu_ai_act_compliance_report.json`
- Compliance score (0-100%)
- List of non-compliant items with remediation guidance

**Acceptance Criteria:**
- [ ] FR-12-01 AC1: All AI tasks without HITL/HOTL assignment are flagged as non-compliant
- [ ] FR-12-01 AC2: Missing model cards trigger non-compliance flag
- [ ] FR-12-01 AC3: Kill-switch response time >5s triggers critical non-compliance
- [ ] FR-12-01 AC4: Report includes specific Article 14 subsection for each finding

---

#### [FR-12-02] NIST AI RMF Function Mapper

**Description:** Map every methodology-v2 mechanism to NIST AI RMF functions (Govern, Map, Measure, Manage).

**Inputs:**
- All Phase deliverables (Phase 1-7)
- Constitution rules
- Gate policy definitions

**Processing:**
1. Parse each mechanism and classify under NIST AI RMF function
2. Identify gaps where no mechanism covers a required function
3. Generate coverage matrix

**Outputs:**
- `nist_rmf_coverage_matrix.json`
- Gap analysis report
- Recommended remediation for uncovered functions

**Acceptance Criteria:**
- [ ] FR-12-02 AC1: Every NIST AI RMF function has at least one mapped mechanism
- [ ] FR-12-02 AC2: Unmapped functions are flagged as "coverage gap"
- [ ] FR-12-02 AC3: Matrix output is machine-readable (JSON/YAML)

---

#### [FR-12-03] Anthropic RSP ASL Level Detector

**Description:** Automatically determine the required ASL level based on project configuration and operations.

**Inputs:**
- Project configuration (tasks, autonomy level, risk category)
- Agent behavior logs (autonomous coding events)

**Processing:**
1. Analyze project tasks for ASL-3 triggers:
   - Autonomous coding (code generation + execution)
   - Scientific research (hypothesis generation +实验 design)
   - Decision-making with economic impact
2. Count ASL-3 trigger events per session
3. If ASL-3 threshold exceeded without G1/G4 sign-off → flag violation

**Outputs:**
- `asl_level_assessment.json`
- ASL-3 trigger event log
- Sign-off status (approved/pending/violated)

**Acceptance Criteria:**
- [ ] FR-12-03 AC1: ASL-2 assigned when project has chatbot/image-gen tasks only
- [ ] FR-12-03 AC2: ASL-3 assigned when autonomous coding tasks are detected
- [ ] FR-12-03 AC3: ASL-4 triggered → warning + recommendation to not proceed
- [ ] FR-12-03 AC4: Missing G1/G4 sign-off for ASL-3 → violation flag

---

#### [FR-12-04] Unified Compliance Matrix Generator

**Description:** Generate a unified compliance matrix that cross-references all three regulatory frameworks (EU AI Act, NIST AI RMF, Anthropic RSP).

**Inputs:**
- EU AI Act compliance data (from FR-12-01)
- NIST AI RMF coverage data (from FR-12-02)
- RSP ASL assessment data (from FR-12-03)

**Processing:**
1. Consolidate all compliance findings
2. Normalize terminology across frameworks
3. Generate a single source of truth for auditors

**Outputs:**
- `compliance_matrix.json` — machine-readable matrix
- `compliance_matrix.md` — human-readable summary
- Export API for integration with external compliance tools

**Acceptance Criteria:**
- [ ] FR-12-04 AC1: Matrix includes all three frameworks with cross-references
- [ ] FR-12-04 AC2: Each cell contains: compliant (yes/no/partial), evidence, remediation
- [ ] FR-12-04 AC3: Export formats: JSON, YAML, Markdown
- [ ] FR-12-04 AC4: Last-updated timestamp and version number in output

---

#### [FR-12-05] Automated Compliance Reporter

**Description:** Generate periodic and on-demand compliance reports for internal audits and external regulators.

**Report Types:**
1. **On-Demand Report**: Triggered by `compliance report --type=full`
2. **Periodic Report**: Weekly digest of compliance status
3. **Incident Report**: Triggered by Kill-switch activation or ASL violation
4. **Audit Package**: Comprehensive evidence package for external auditors

**Inputs:**
- All compliance data from FR-12-01 through FR-12-04
- Langfuse trace data
- Override audit logs
- Sign-off records (G1/G4)

**Outputs:**
- `compliance_report_{timestamp}.md`
- `compliance_evidence_{timestamp}.zip` (archive of evidence)
- `compliance_dashboard.json` (for web-based dashboard)

**Acceptance Criteria:**
- [ ] FR-12-05 AC1: On-demand report generated within 30 seconds
- [ ] FR-12-05 AC2: Periodic report auto-scheduled (configurable interval)
- [ ] FR-12-05 AC3: Incident report generated within 60 seconds of trigger event
- [ ] FR-12-05 AC4: Audit package includes all evidence with SHA-256 checksums
- [ ] FR-12-05 AC5: Reports are versioned and append-only (no overwrites)

---

#### [FR-12-06] Kill-Switch Compliance Monitor

**Description:** Ensure the Kill-switch meets EU AI Act Article 14(4)(e) requirement of system interruption within 5 seconds.

**Inputs:**
- Kill-switch activation logs
- System shutdown timing data

**Processing:**
1. Record timestamp when Kill-switch is triggered
2. Record timestamp when all AI operations cease
3. Calculate elapsed time
4. If elapsed > 5000ms → flag as non-compliant

**Outputs:**
- `killswitch_compliance_log.json`
- Alert when response time exceeds threshold
- Statistics: average response time, p95, p99

**Acceptance Criteria:**
- [ ] FR-12-06 AC1: Kill-switch response time tracked for every activation
- [ ] FR-12-06 AC2: Exceeding 5s threshold triggers immediate alert
- [ ] FR-12-06 AC3: Response time statistics available for compliance review
- [ ] FR-12-06 AC4: Log is immutable (append-only with cryptographic integrity)

---

#### [FR-12-07] Human Override Audit Trail

**Description:** Maintain immutable audit trail of all human override events for Article 14(4)(d) compliance.

**Inputs:**
- Human override events (from HITL Gate)
- Override justification (user-provided or system-prompted)
- System state before/after override

**Processing:**
1. Capture override event with timestamp, user identity, system state
2. Require justification text (minimum 10 characters)
3. Store evidence in append-only log

**Outputs:**
- `override_audit_log.json` — per-override records
- `override_summary.md` — human-readable audit summary
- Export API for compliance auditors

**Acceptance Criteria:**
- [ ] FR-12-07 AC1: Every override event is logged with timestamp, user, reason, state diff
- [ ] FR-12-07 AC2: Missing justification → override rejected with prompt
- [ ] FR-12-07 AC3: Audit log is cryptographically signed (tamper-evident)
- [ ] FR-12-07 AC4: Log supports filtering by date range, user, task type

---

### 3.2 Data Handling Requirements

#### [DHR-12-01] Traceability Data Retention

| Data Type | Retention Period | Justification |
|-----------|-----------------|---------------|
| Override audit logs | 7 years | EU AI Act Art.14(4)(d) + financial audit requirements |
| Kill-switch activation logs | 7 years | EU AI Act Art.14(4)(e) + incident investigation |
| Compliance reports | 5 years | NIST AI RMF + internal audit cycle |
| ASL assessment records | 5 years | Anthropic RSP v3.0 documentation requirement |
| Langfuse trace data | 90 days (rolling) | GDPR data minimization principle |
| Model cards | Permanent (versioned) | EU AI Act Art.14(4)(a) + model lifecycle |

#### [DHR-12-02] Data Protection Requirements

- All PII (user identities in override logs) must be encrypted at rest (AES-256)
- Compliance reports must be accessible only to authorized roles
- Audit logs must be append-only with cryptographic integrity (SHA-256 chain)
- Data subject access requests (DSAR) must be fulfilled within 30 days

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric | Requirement | Measurement Method |
|--------|-------------|-------------------|
| Report generation (on-demand) | ≤30 seconds | Timer from trigger to file write |
| Report generation (audit package) | ≤120 seconds | Timer from trigger to ZIP completion |
| Kill-switch response time | ≤5,000 ms (EU AI Act Art.14(4)(e)) | Elapsed time between trigger signal and last AI operation ceased |
| Compliance check latency | ≤5 seconds per check | Per FR-12-01 through FR-12-07 |
| Matrix generation | ≤60 seconds | Full compliance matrix from all data sources |

### 4.2 Reliability

| Requirement | Target |
|-------------|--------|
| System availability | 99.9% (excluding planned maintenance) |
| Audit log integrity | Zero data loss on Kill-switch activation |
| Report completeness | 100% of required fields populated |
| Recovery Point Objective (RPO) | ≤1 minute (logs) |
| Recovery Time Objective (RTO) | ≤15 minutes |

### 4.3 Security

| Requirement | Implementation |
|-------------|----------------|
| Confidentiality | Role-based access control (RBAC) for compliance reports |
| Integrity | Cryptographic signatures on audit logs (HMAC-SHA256) |
| Availability | Kill-switch operates independently of main system (hardware-backed) |
| Authentication | All compliance operations require authenticated user context |
| Auditability | All access to compliance data is itself logged |

### 4.4 Scalability

| Dimension | Requirement |
|-----------|-------------|
| Concurrent compliance checks | Support 10 simultaneous checks |
| Log volume | Support up to 1M override events per year |
| Report size | Support audit packages up to 500MB |
| Multi-tenant |隔离 tenant data in compliance reporting |

### 4.5 Compliance

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art.14 | All requirements from Section 2.1 must be implemented |
| NIST AI RMF | All four functions (Govern, Map, Measure, Manage) must be mapped |
| Anthropic RSP v3.0 | ASL-3 and below must be supported; ASL-4 must produce warning |
| GDPR | Data retention and subject rights respected per DHR-12-01 and DHR-12-02 |
| SOC 2 Type II | Availability, confidentiality, and integrity controls documented |

---

## 5. Acceptance Criteria

### 5.1 Functional Acceptance

| ID | Criterion | Verification Method |
|----|-----------|-------------------|
| AC-12-01 | EU AI Act compliance checker identifies all 6 Article 14 sub-requirements | Run checker against known non-compliant project → all 6 flagged |
| AC-12-02 | NIST AI RMF coverage matrix maps all 4 functions | Cross-reference with NIST AI RMF官方文档 → 100% coverage |
| AC-12-03 | ASL-3 trigger detection: autonomous coding without sign-off → violation | Simulate autonomous coding event → violation flagged within 10s |
| AC-12-04 | Unified compliance matrix includes all 3 frameworks with evidence | Manual review of matrix JSON → each cell has evidence pointer |
| AC-12-05 | Compliance report generated in ≤30 seconds for on-demand type | Measure elapsed time → ≤30s |
| AC-12-06 | Kill-switch response time ≤5s (p99) | 100 consecutive activations → p99 ≤5000ms |
| AC-12-07 | Override audit log tamper-evident (HMAC chain unbroken) | Modify log entry → detected by integrity check |
| AC-12-08 | ASL-4 detected → warning message + not proceed recommendation | Set project to ASL-4 mode → warning displayed |
| AC-12-09 | Periodic reports scheduled and delivered | Configure 1-minute interval → verify delivery |
| AC-12-10 | Export formats JSON/YAML/Markdown all produce valid output | Parse all 3 formats → no errors |

### 5.2 Non-Functional Acceptance

| ID | Criterion | Verification Method |
|----|-----------|-------------------|
| NFR-12-01 | Report generation ≤30s (on-demand) | Benchmark 10 runs → median ≤30s |
| NFR-12-02 | Kill-switch response ≤5s (EU AI Act Art.14(4)(e)) | 100 activations → p99 ≤5000ms |
| NFR-12-03 | Audit log integrity (HMAC chain valid) | 1000 entries → 100% valid chain |
| NFR-12-04 | Availability 99.9% | 30-day monitoring → uptime ≥99.9% |
| NFR-12-05 | RBAC enforced on compliance reports | Unauthorized user attempt → 403 Forbidden |

---

## 6. Compliance Matrix

### 6.1 EU AI Act Article 14 Full Mapping

| Article | Sub-Article | Requirement | v3.0 Implementation | Evidence | Status |
|---------|-------------|-------------|---------------------|----------|--------|
| 14 | (1) | Human oversight measures implemented | HITL/HOTL分级 in `agent_hierarchy.py` | Gate policy config | ✅ Compliant |
| 14 | (4)(a) | Operators can understand AI limits | Model cards + Agents.md metadata | `model_card.json`, `Agents.md` | ✅ Compliant |
| 14 | (4)(b) | Prevent undue reliance (automation bias) | DA challenge + UAF warnings | `debate_agent.py`, `uncertainty_aggregator.py` | ✅ Compliant |
| 14 | (4)(c) | Interpret AI outputs | Langfuse trace viewer + `TraceInterpreter` | Langfuse dashboard URL | ✅ Compliant |
| 14 | (4)(d) | Human override capability | `HumanOverrideGate` + audit log | `override_audit_log.json` | ✅ Compliant |
| 14 | (4)(e) | Interrupt system capability (≤5s) | Kill-switch with timing monitor | `killswitch_compliance_log.json` | ✅ Compliant |

### 6.2 NIST AI RMF Coverage Matrix

| Function | Sub-Function | v3.0 Mechanism | Component | Coverage |
|---------|-------------|---------------|-----------|----------|
| Govern | Establish context | Constitution | `constitution_compliance_checker.py` | 100% |
| Govern | Risk assessment | Agents.md metadata | `agents_metadata_exporter.py` | 100% |
| Map | Risk identification | Phase 1 TRACEABILITY_MATRIX | `traceability_matrix_generator.py` | 100% |
| Map | Risk analysis | Risk assessment engine | `risk_assessment_engine.py` | 100% |
| Measure | Risk analysis | Langfuse metrics + UAF/CLAP | `langfuse_metrics_collector.py`, `uncertainty_aggregator.py` | 100% |
| Measure | Risk monitoring | CLAP calibration checks | `calibration_checker.py` | 100% |
| Manage | Risk response | Gate policy | `gate_policy_engine.py` | 100% |
| Manage | Risk monitoring | Kill-switch | `kill_switch_executor.py` | 100% |
| Manage | Continuous monitoring | Periodic compliance reports | `compliance_reporter.py` | 100% |

### 6.3 Anthropic RSP v3.0 ASL Coverage Matrix

| ASL Level | Trigger Condition | v3.0 Enforcement | Sign-off Required | Status |
|-----------|-------------------|------------------|------------------|--------|
| ASL-1 | Default (no high-risk tasks) | No special enforcement | None | ✅ Supported |
| ASL-2 | Chatbot, image generation tasks | HOTL enforcement | None | ✅ Supported |
| ASL-3 | Autonomous coding, scientific research | HITL G1/G4 mandatory | G1 + G4 approval | ✅ Supported |
| ASL-4 | AGI-level autonomous systems | Warning + not-proceed recommendation | N/A | ⚠️ Not Recommended |

### 6.4 Cross-Framework Compliance Summary

| Framework | Total Requirements | Implemented | Coverage | Gaps |
|-----------|-------------------|------------|----------|------|
| EU AI Act Art.14 | 7 (1 + 6 sub-articles) | 7 | 100% | None |
| NIST AI RMF | 9 (4 functions × sub-functions) | 9 | 100% | None |
| Anthropic RSP v3.0 | 4 (ASL-1 through ASL-4) | 3 (ASL-4 warning only) | 75% | ASL-4 full support |
| **Overall** | **20** | **19** | **95%** | **ASL-4 full support** |

---

## 7. Component Specifications

### 7.1 compliance/eu_ai_act.py

**Purpose:** EU AI Act Article 14 compliance checker and mapper.

**Class: `EUAIActChecker` (inherits `BaseComplianceChecker`)**

```python
class EUAIActChecker(BaseComplianceChecker):
    """
    EU AI Act Article 14 compliance verification.
    Maps methodology-v2 mechanisms to Article 14 requirements.
    """

    # Article 14 sub-requirements mapped
    ARTICLE_14_ARTICLES = {
        "14_1": "human_oversight_measures",
        "14_4_a": "understand_ai_limits",
        "14_4_b": "automation_bias_awareness",
        "14_4_c": "interpret_outputs",
        "14_4_d": "human_override",
        "14_4_e": "interrupt_system",
    }

    def check_article_14_compliance(
        self,
        project_config: ProjectConfig,
        hitl_assignments: dict[str, str],
        model_cards: list[ModelCard],
        killswitch_config: KillSwitchConfig
    ) -> EUAIActComplianceResult:
        """
        Verify EU AI Act Article 14 compliance for a given project.

        Args:
            project_config: Project configuration (YAML loaded)
            hitl_assignments: Mapping of task_id -> HITL level
            model_cards: List of ModelCard objects for deployed models
            killswitch_config: Kill-switch configuration with response time SLA

        Returns:
            EUAIActComplianceResult with compliance score and findings
        """
        ...

    def generate_eu_ai_act_report(
        self,
        result: EUAIActComplianceResult
    ) -> EUAIActReport:
        """
        Generate human-readable EU AI Act compliance report.

        Returns:
            EUAIActReport with structured findings per Article 14 subsection
        """
        ...
```

**Key Methods:**
- `check_article_14_compliance()` — Core compliance verification
- `generate_eu_ai_act_report()` — Human-readable report generation
- `get_required_evidence()` — List evidence required for each Article

**Dependencies:**
- `BaseComplianceChecker` from `compliance_matrix.py`
- `ProjectConfig` from `agent_hierarchy.py`
- `ModelCard` from `model_card.py`

---

### 7.2 compliance/nist_rmf.py

**Purpose:** NIST AI RMF function mapper and coverage analyzer.

**Class: `NISTRMfMapper` (inherits `BaseComplianceChecker`)**

```python
class NISTRMfMapper(BaseComplianceChecker):
    """
    NIST AI Risk Management Framework (AI RMF) mapper.
    Maps methodology-v2 mechanisms to NIST AI RMF four functions:
    Govern, Map, Measure, Manage.
    """

    NIST_AI_RMF_FUNCTIONS = {
        "govern": ["establish_context", "risk_assessment", "risk_response_strategy"],
        "map": ["risk_identification", "risk_analysis"],
        "measure": ["risk_analysis", "risk_determination", "risk_monitoring"],
        "manage": ["risk_response", "risk_monitoring", "continuous_monitoring"],
    }

    def map_mechanisms_to_functions(
        self,
        methodology_mechanisms: list[Mechanism]
    ) -> NISTCoverageMatrix:
        """
        Map each methodology-v2 mechanism to corresponding NIST AI RMF function.

        Returns:
            NISTCoverageMatrix with coverage percentage per function
        """
        ...

    def identify_coverage_gaps(
        self,
        matrix: NISTCoverageMatrix
    ) -> list[CoverageGap]:
        """
        Identify NIST AI RMF functions not covered by any mechanism.

        Returns:
            List of CoverageGap objects with remediation guidance
        """
        ...

    def generate_nist_rmf_report(
        self,
        matrix: NISTCoverageMatrix
    ) -> NISTRMFReport:
        """
        Generate NIST AI RMF compliance report for auditors.

        Returns:
            NISTRMFReport with structured coverage analysis
        """
        ...
```

**Key Methods:**
- `map_mechanisms_to_functions()` — Core mapping logic
- `identify_coverage_gaps()` — Gap detection and remediation
- `generate_nist_rmf_report()` — Structured report for auditors

**Dependencies:**
- `BaseComplianceChecker` from `compliance_matrix.py`
- `Mechanism` from `methodology_core.py`

---

### 7.3 compliance/compliance_matrix.py

**Purpose:** Unified compliance matrix combining all regulatory frameworks.

**Class: `UnifiedComplianceMatrix` (inherits `BaseComplianceChecker`)**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

@dataclass
class ComplianceCell:
    """
    Single cell in the unified compliance matrix.
    """
    framework: str           # e.g., "EU_AI_ACT", "NIST_AI_RMF", "RSP_V3"
    requirement_id: str      # e.g., "14_4_e", "govern_1"
    requirement_text: str     # Human-readable requirement
    status: ComplianceStatus
    evidence: list[str]       # Pointers to evidence (file paths, record IDs)
    remediation: Optional[str]  # Required fix if non-compliant
    last_verified: str        # ISO timestamp
    verified_by: str          # User/system that performed check

class UnifiedComplianceMatrix:
    """
    Unified compliance matrix cross-referencing all regulatory frameworks.
    Provides single source of truth for compliance audits.
    """

    def __init__(self):
        self._cells: dict[tuple[str, str], ComplianceCell] = {}
        self._version: str = "1.0.0"
        self._last_updated: Optional[str] = None

    def add_cell(self, cell: ComplianceCell) -> None:
        """Add or update a compliance matrix cell."""
        key = (cell.framework, cell.requirement_id)
        self._cells[key] = cell
        self._last_updated = datetime.now().isoformat()

    def get_cell(self, framework: str, requirement_id: str) -> Optional[ComplianceCell]:
        """Retrieve a single cell from the matrix."""
        return self._cells.get((framework, requirement_id))

    def get_framework_compliance(self, framework: str) -> dict[str, ComplianceStatus]:
        """Get all compliance statuses for a given framework."""
        return {
            req_id: cell.status
            for (fw, req_id), cell in self._cells.items()
            if fw == framework
        }

    def to_json(self) -> dict:
        """Export matrix as JSON for machine processing."""
        return {
            "version": self._version,
            "last_updated": self._last_updated,
            "cells": [
                {
                    "framework": framework,
                    "requirement_id": req_id,
                    "requirement_text": cell.requirement_text,
                    "status": cell.status.value,
                    "evidence": cell.evidence,
                    "remediation": cell.remediation,
                    "last_verified": cell.last_verified,
                    "verified_by": cell.verified_by,
                }
                for (framework, req_id), cell in self._cells.items()
            ],
        }

    def to_markdown(self) -> str:
        """Export matrix as Markdown for human review."""
        ...  # Full implementation in compliance_matrix.py
```

**Key Methods:**
- `add_cell()` — Add/update compliance cell
- `get_framework_compliance()` — Per-framework status summary
- `to_json()` / `to_yaml()` / `to_markdown()` — Multi-format export
- `generate_dashboard()` — Web dashboard data

**Dependencies:**
- `EUAIActChecker` from `eu_ai_act.py`
- `NISTRMfMapper` from `nist_rmf.py`
- `RSPASLDetector` from `rsp_mapper.py`

---

### 7.4 compliance/compliance_reporter.py

**Purpose:** Automated compliance report generation for various audiences and triggers.

**Enum: `ReportType`**

```python
from enum import Enum

class ReportType(Enum):
    ON_DEMAND = "on_demand"           # Triggered by user request
    PERIODIC = "periodic"              # Scheduled digest (weekly/monthly)
    INCIDENT = "incident"              # Triggered by Kill-switch or ASL violation
    AUDIT_PACKAGE = "audit_package"    # Comprehensive package for external auditors
```

**Class: `ComplianceReporter`**

```python
class ComplianceReporter:
    """
    Automated compliance report generator.
    Supports on-demand, periodic, incident, and audit package reports.
    """

    def __init__(
        self,
        eu_ai_act_checker: EUAIActChecker,
        nist_rmf_mapper: NISTRMfMapper,
        rsp_asl_detector: RSPASLDetector,
        unified_matrix: UnifiedComplianceMatrix,
    ):
        ...

    def generate_report(
        self,
        report_type: ReportType,
        filters: Optional[ReportFilters] = None,
    ) -> ComplianceReport:
        """
        Generate compliance report of the specified type.

        Args:
            report_type: Type of report to generate
            filters: Optional filters (date range, framework, etc.)

        Returns:
            ComplianceReport with content and metadata
        """
        ...

    def generate_audit_package(
        self,
        audit_id: str,
        date_range: tuple[str, str]
    ) -> AuditPackage:
        """
        Generate comprehensive audit package with evidence archive.

        Args:
            audit_id: Unique identifier for this audit
            date_range: Start and end dates (ISO format)

        Returns:
            AuditPackage containing report + evidence ZIP
        """
        ...

    def schedule_periodic_report(
        self,
        interval_hours: int,
        framework: Optional[str] = None
    ) -> ScheduledReport:
        """
        Schedule periodic compliance report generation.

        Args:
            interval_hours: Hours between report generations
            framework: Optional filter to specific framework

        Returns:
            ScheduledReport object with scheduling metadata
        """
        ...

    def export_dashboard_json(self) -> dict:
        """
        Export dashboard data for web-based compliance dashboard.

        Returns:
            dict with metrics, charts data, and status indicators
        """
        ...
```

**Key Methods:**
- `generate_report()` — Main report generation (all types)
- `generate_audit_package()` — Full evidence package with ZIP archive
- `schedule_periodic_report()` — Cron-style periodic report scheduling
- `export_dashboard_json()` — Dashboard data for visualization

**Dependencies:**
- `EUAIActChecker` from `eu_ai_act.py`
- `NISTRMfMapper` from `nist_rmf.py`
- `RSPASLDetector` from `rsp_mapper.py` (internal)
- `UnifiedComplianceMatrix` from `compliance_matrix.py`

---

## 8. User Scenarios

### Scenario 1: EU AI Act Compliance Audit

**Actor:** Compliance Officer

**Precondition:** Project has been running for 2 weeks with HITL/HOTL enforcement.

**Steps:**
1. Compliance officer triggers: `compliance report --type=on_demand --framework=EU_AI_ACT`
2. System runs EU AI Act Article 14 checker (FR-12-01)
3. System generates `eu_ai_act_compliance_report.json`
4. System displays compliance score: 95% (1 finding: model card missing for model-003)
5. Officer reviews finding → updates model card
6. Officer re-runs checker → score: 100%

**Expected Result:** Full compliance achieved and documented.

---

### Scenario 2: NIST AI RMF Coverage Gap Detection

**Actor:** Risk Manager

**Precondition:** New methodology-v2 feature deployed (without mapping to NIST).

**Steps:**
1. Risk manager triggers: `compliance check --framework=NIST_AI_RMF --type=coverage`
2. System identifies new mechanism not mapped to any NIST function → coverage gap flagged
3. System generates `nist_rmf_gap_analysis.json` with remediation:
   - "New mechanism 'X' not mapped → add mapping to 'Measure' function via UAF/CLAP"
4. Risk manager reviews → updates TRACEABILITY_MATRIX
5. System re-evaluates → coverage: 100%

**Expected Result:** All NIST AI RMF functions have at least one mapped mechanism.

---

### Scenario 3: ASL-3 Violation Detection

**Actor:** Security Team

**Precondition:** Developer runs autonomous coding task without G1/G4 sign-off.

**Steps:**
1. Developer triggers autonomous code generation task
2. RSP ASL Detector (FR-12-03) identifies ASL-3 trigger (autonomous coding)
3. System checks for G1/G4 sign-off → not present
4. System flags ASL-3 violation: `ASL_VIOLATION_DETECTED`
5. System prevents task from proceeding until sign-off obtained
6. Developer obtains G1 + G4 approval
7. System re-evaluates → sign-off confirmed → task allowed

**Expected Result:** ASL-3 tasks cannot proceed without mandatory sign-off.

---

### Scenario 4: Kill-Switch Response Time Verification

**Actor:** Compliance Officer

**Precondition:** Kill-switch has been activated 50 times in past month.

**Steps:**
1. Officer triggers: `compliance check --type=killswitch_performance`
2. System retrieves `killswitch_compliance_log.json`
3. System calculates statistics: avg=2.3s, p95=3.8s, p99=4.5s
4. System verifies: all activations < 5s threshold
5. System generates `killswitch_compliance_report.json` with chart data

**Expected Result:** EU AI Act Art.14(4)(e) compliance confirmed with evidence.

---

### Scenario 5: External Audit Package Generation

**Actor:** External Auditor

**Precondition:** Annual external audit scheduled.

**Steps:**
1. Compliance officer triggers: `compliance report --type=audit_package --audit-id=AUDIT_2026_Q2 --date-range=2026-01-01,2026-06-30`
2. System collects all compliance data for date range
3. System generates `compliance_report_AUDIT_2026_Q2.md`
4. System archives evidence: model cards, override logs, Langfuse traces, kill-switch logs
5. System computes SHA-256 checksums for all files
6. System creates `compliance_evidence_AUDIT_2026_Q2.zip`
7. System delivers report + package to auditor portal

**Expected Result:** Audit package delivered within 120 seconds, all evidence integrity-verified.

---

## 9. Dependencies

### 9.1 Internal Dependencies (methodology-v2 components)

| Component | Feature | Required For |
|-----------|--------|-------------|
| `agent_hierarchy.py` | Feature #6 | HITL/HOTL assignment data |
| `kill_switch_executor.py` | Feature #6 | Kill-switch timing logs |
| `langfuse_tracer.py` | Feature #5 | Trace data for interpretability |
| `model_card.py` | Feature #4 | Model card exports |
| `Agents.md` | Feature #1 | Agents metadata |
| `Constitution` | Feature #2 | Governance rules |
| `TRACEABILITY_MATRIX.md` | Feature #1 | NIST Map function mapping |
| `gate_policy_engine.py` | Feature #6 | Gate decision logs |
| `debate_agent.py` | Feature #3 | Automation bias detection |
| `uncertainty_aggregator.py` | Feature #4 | UAF warnings |
| `calibration_checker.py` | Feature #4 | CLAP calibration data |

### 9.2 External Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| Python | ≥3.11 | Language runtime |
| pydantic | ≥2.0 | Data validation and serialization |
| pyyaml | ≥6.0 | YAML configuration parsing |
| hashlib | (stdlib) | SHA-256 checksums, HMAC |
| json | (stdlib) | JSON serialization |
| datetime | (stdlib) | Timestamp handling |
| logging | (stdlib) | Audit logging |

### 9.3 Optional Integrations

| Integration | Purpose | Required |
|------------|---------|----------|
| Langfuse | Trace storage and visualization | Recommended (for Art.14(4)(c)) |
| Prometheus | Metrics export | Optional |
| Grafana | Dashboard integration | Optional |
| SIEM (e.g., Splunk) | Security event aggregation | Optional |

---

## 10. Out of Scope

The following are explicitly **NOT** in scope for Feature #12:

1. **ASL-4 full implementation**: v3.0 does not support ASL-4 due to insufficient safety guarantees. A future feature may address ASL-4.
2. **GDPR Article 17 (Right to Erasure)**: While data retention policies are defined, implementing actual data deletion across all systems is out of scope.
3. **EU AI Act Article 10 (Data Governance)**: Data quality requirements for training data are not addressed.
4. **EU AI Act Article 11 (Technical Documentation)**: Full technical documentation requirements for high-risk systems are not fully specified.
5. **Cross-border data transfer compliance**: EU AI Act Chapter IX requirements are not addressed.
6. **Third-party AI component audit**: Auditing external AI services integrated into methodology-v2 is out of scope.
7. **Real-time compliance monitoring**: Continuous monitoring with live alerts is partially addressed but full SOC 2 controls are not in scope.
8. **Penetration testing**: Security testing of compliance mechanisms is handled by separate security review process.

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **ASL** | AI Safety Level (Anthropic RSP v3.0). Levels 1-4 classify AI system risk. |
| **CLAP** | Calibration metric measuring how well model's confidence matches actual accuracy. |
| **Compliance Matrix** | Cross-reference table mapping regulatory requirements to implemented mechanisms. |
| **DA** | Debate Agent. Challenge mechanism that questions agent outputs. |
| **EU AI Act** | European Union Artificial Intelligence Act (Regulation 2024/1689). Effective 2026. |
| **G1/G4** | Gate 1 and Gate 4. Approval checkpoints in HITL workflow. |
| **HITL** | Human-in-the-Loop. Human approval required for each significant action. |
| **HOOTL** | Human-out-of-the-Loop. Fully autonomous operation with monitoring. |
| **HOTL** | Human-on-the-Loop. Human monitors and can intervene but does not approve each action. |
| **Kill-switch** | Emergency stop mechanism that halts all AI operations within 5 seconds. |
| **NIST AI RMF** | National Institute of Standards and Technology AI Risk Management Framework. |
| **RSP** | Responsible Scaling Policy (Anthropic). Policy governing AI deployment safety levels. |
| **TRACEABILITY_MATRIX** | Document mapping requirements to Phase 1 deliverables. |
| **UAF** | Uncertainty Aggregation Framework. Measures and reports model uncertainty. |

---

## Appendix A: EU AI Act Article 14 Full Text Reference

> **Article 14 — Human oversight**
> 
> 1. High-risk AI systems shall be designed to allow for effective human oversight.
> 2. Human oversight shall be ensured through appropriate human-machine interface tools.
> 3. The human oversight measures shall be tailored to the risk profile of the AI system.
> 4. For high-risk AI systems, operators shall:
>    (a) understand the capabilities and limitations of the AI system;
>    (b) be aware of the possible automation bias;
>    (c) be able to interpret the outputs of the AI system;
>    (d) be able to override the AI system's decisions;
>    (e) be able to interrupt the AI system's operation.

---

## Appendix B: NIST AI RMF Four Functions

| Function | Description |
|----------|-------------|
| **Govern** | Establish and oversee AI risk management governance |
| **Map** | Characterize AI risks in context of the organization's operations |
| **Measure** | Analyze and assess identified AI risks |
| **Manage** | Prioritize and act on AI risks |

---

## Appendix C: Anthropic RSP v3.0 ASL Levels

| Level | Description | Example Use Cases |
|-------|-------------|-------------------|
| ASL-1 | Minimal risk | Spam filters, recommenders |
| ASL-2 | Limited risk | Chatbots, image generators |
| ASL-3 | High risk | Autonomous coding, scientific research, medical diagnosis |
| ASL-4 | Critical risk | AGI-level systems with potential for catastrophic harm |

---

*End of SPEC.md*

---
**Document Metadata:**
- Version: 1.0.0
- Created: 2026-04-22
- Status: Draft
- Next Review: 2026-04-29
- Owner: Compliance Layer Team
- Approver: To Be Determined