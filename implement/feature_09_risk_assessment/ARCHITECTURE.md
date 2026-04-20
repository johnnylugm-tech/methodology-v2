# Feature #9 Architecture Document

> **Version**: v1.0.0  
> **Feature**: Risk Assessment Engine  
> **Layer**: 4 - Executive Assurance  
> **Framework**: methodology-v2  
> **Status**: Implemented (Phase 1 Complete)

---

## 1. System Architecture

### 1.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RISK ASSESSMENT ENGINE                                │
│                         (engine/engine.py)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │   RiskAssessor  │───▶│  RiskStrategist │───▶│   RiskTracker   │        │
│  │ (engine/assessor)│    │(engine/strategist)│   │ (engine/tracker)│        │
│  │  [FR-01, FR-02] │    │    [FR-03]       │    │    [FR-04]      │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                      │                      │                   │
│           ▼                      ▼                      ▼                   │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │  RiskScorer     │    │ MitigationPlan │    │  SQLite DB      │        │
│  │  - patterns     │    │  - immediate    │    │  - risks table  │        │
│  │  - probability  │    │  - short_term   │    │  - history      │        │
│  │  - impact       │    │  - long_term    │    │                 │        │
│  └─────────────────┘    │  - fallback     │    └─────────────────┘        │
│                         └─────────────────┘                                │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                         REPORTS                                    │      │
│  │  ┌─────────────────────────┐  ┌─────────────────────────────┐    │      │
│  │  │  RiskAssessmentReport   │  │  DecisionGateReport         │    │      │
│  │  │  (assessor_report.py)    │  │  (decision_gate_report.py)  │    │      │
│  │  │  → RISK_ASSESSMENT.md   │  │  → Phase7_DecisionGate.md    │    │      │
│  │  │  → RISK_REGISTER.md     │  │                             │    │      │
│  │  └─────────────────────────┘  └─────────────────────────────┘    │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │                      CONSTITUTION LAYER                            │      │
│  │  ┌──────────────────────────────────────────────────────────────┐ │      │
│  │  │          RiskAssessmentConstitutionChecker                   │ │      │
│  │  │              (constitution/risk_assessment_checker.py)       │ │      │
│  │  │                                                              │ │      │
│  │  │  Checks:                                                     │ │      │
│  │  │  ├── Required files exist                                    │ │      │
│  │  │  ├── Required sections present                               │ │      │
│  │  │  ├── Mitigation plans complete                              │ │      │
│  │  │  ├── Risk register format valid                               │ │      │
│  │  │  └── Status tracking consistent                               │ │      │
│  │  └──────────────────────────────────────────────────────────────┘ │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │      OUTPUT ARTIFACTS         │
                    │  ┌─────────────────────────┐  │
                    │  │ RISK_ASSESSMENT.md      │  │
                    │  │ - Executive Summary     │  │
                    │  │ - Risk Register Table   │  │
                    │  │ - Detailed Assessments  │  │
                    │  │ - Recommendations        │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │ RISK_REGISTER.md       │  │
                    │  │ - Decision Gate Table   │  │
                    │  │ - Risk Entry Table      │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │ risk_assessment.db      │  │
                    │  │ - SQLite persistence    │  │
                    │  │ - Audit trail           │  │
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
```

### 1.2 Module Structure

```
feature-09-risk-assessment/
├── __init__.py
├── engine/
│   ├── __init__.py
│   ├── engine.py          # Main engine facade [FR-01, FR-02, FR-03, FR-04]
│   ├── assessor.py        # Risk identification & scoring [FR-01, FR-02]
│   ├── strategist.py      # Strategy generation [FR-03]
│   └── tracker.py         # Status tracking & persistence [FR-04]
├── models/
│   ├── __init__.py
│   ├── enums.py           # RiskDimension, RiskLevel, RiskStatus, StrategyType
│   └── risk.py            # Risk, MitigationPlan, RiskAssessmentResult
├── constitution/
│   ├── __init__.py
│   └── risk_assessment_checker.py  # Constitution compliance
├── reports/
│   ├── __init__.py
│   ├── assessor_report.py          # RISK_ASSESSMENT.md generation
│   └── decision_gate_report.py    # Phase 7 Decision Gate reports
└── tests/
    ├── __init__.py
    ├── test_assessor.py
    ├── test_strategist.py
    └── test_tracker.py
```

---

## 2. Module Responsibilities

### 2.1 engine/engine.py — Main Engine Facade

**Purpose**: Unified interface for Phase 6/7 consumption

**Key Responsibilities**:
- Orchestrate assessor, strategist, tracker components
- Provide single `assess()` entry point
- Generate `DecisionGateResult` for Phase 7
- Compute risk summary statistics

**Public API**:
```python
class RiskAssessmentEngine:
    def __init__(self, project_root: str)
    def assess() -> RiskAssessmentResult      # [FR-01, FR-02]
    def generate_strategies(risk_id: str)       # [FR-03]
    def update_status(risk_id, new_status)      # [FR-04]
    def evaluate_gates() -> DecisionGateResult  # [FR-04]
    def get_risk_summary() -> Dict[str, Any]
```

**Key Design Decision**: Facade pattern chosen to provide single entry point while delegating to specialized components. This decouples Phase 6/7 consumers from internal implementation details.

---

### 2.2 engine/assessor.py — Risk Identification & Scoring

**Purpose**: Identify risks from project artifacts and compute scores

**Components**:

#### RiskScorer
- **calculate()**: `Score = (Probability × Impact × Detectability_Factor) / 5`
  - Normalized to 0-1 range
  - Probability: 0.0-1.0
  - Impact: 1-5
  - Detectability_Factor: 0.5-1.0
- **assess_probability()**: Adjust probability based on pattern matches
- **assess_impact()**: Dimension-specific impact adjustment
- **detect_patterns()**: Regex-based risk pattern detection

**Pattern Dictionaries** (by dimension):
```
TECHNICAL_PATTERNS:
  - complexity: cyclomatic complexity, cognitive load
  - dependency: circular dependencies, tight coupling
  - quality: technical debt, code smells, dead code
  - stability: flaky tests, race conditions

OPERATIONAL_PATTERNS:
  - resource: understaffed, skill gaps, knowledge transfer
  - process: manual deploys, missing monitoring, docs
  - knowledge: single points of failure, bus factor

EXTERNAL_PATTERNS:
  - market: competitor releases, technology obsolescence
  - regulatory: compliance risks, legal issues
  - third_party: vendor lock-in, API deprecation
```

#### RiskAssessor
- **assess()**: Main entry — scans artifacts, identifies risks, computes scores
- **identify_from_code()**: Scan Python files for risk signals
- **identify_from_documentation()**: Find TODOs/FIXMEs as risk signals
- **_scan_code_artifacts()**: Recursive scan of `src/` directory
- **_scan_documentation()**: Check required docs existence
- **_scan_phase_deliverables()**: Phase-specific risk indicator scanning
- **_enrich_with_patterns()**: Pattern matching to strengthen risk assessment
- **_detect_current_phase()**: Determine current project phase

**Key Design Decision**: Pattern-based identification chosen over ML/nlp for deterministic, auditable results. Regex patterns are version-controllable and explainable.

---

### 2.3 engine/strategist.py — Strategy Generation

**Purpose**: Generate risk response strategies and mitigation plans

**Strategy Selection**:
```
Score > 0.6  → AVOID     (eliminate risk source)
Score 0.3-0.6 → MITIGATE  (reduce probability or impact)
Score < 0.3  → ACCEPT    (monitoring list)
```

**MitigationPlan Structure**:
- **immediate** (24h): Document, notify owner, assess exposure
- **short_term** (1 week): Detailed analysis, develop remediation
- **long_term** (1 month): Integrate into monitoring, update processes
- **fallback**: Escalation path, contingency planning

**Key Methods**:
- **generate()**: Select strategy based on score
- **generate_mitigation_plan()**: Create time-horizon-based action plan
- **generate_all_plans()**: Batch process all risks
- **evaluate_strategy_effectiveness()**: Compare expected vs actual outcomes

**Key Design Decision**: Time-horizon-based planning (immediate/short/long/fallback) aligns with standard project management terminology and provides actionable phased responses.

---

### 2.4 engine/tracker.py — Status Tracking & Persistence

**Purpose**: Manage risk lifecycle state transitions with full audit trail

**State Machine**:
```
OPEN → MITIGATED → CLOSED
  │        │          (terminal)
  │        └──────────→ ESCALATED → CLOSED
  │
  └───────────────────→ ACCEPTED → CLOSED
                          └────────→ ESCALATED
```

**State Transition Rules**:
- `can_transition_to()` validates all transitions
- Invalid transitions are rejected with error message

**Database Schema**:
```sql
CREATE TABLE risks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    dimension TEXT,
    level TEXT,
    status TEXT DEFAULT 'OPEN',
    probability REAL,
    impact INTEGER,
    detectability_factor REAL,
    score REAL,
    owner TEXT,
    mitigation TEXT,
    mitigation_plan TEXT,  -- JSON
    created_at TEXT,
    updated_at TEXT,
    closed_at TEXT,
    evidence TEXT           -- JSON array
);

CREATE TABLE risk_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id TEXT,
    changed_at TEXT,
    old_status TEXT,
    new_status TEXT,
    changed_by TEXT,
    note TEXT,
    FOREIGN KEY (risk_id) REFERENCES risks (id)
);
```

**Key Methods**:
- **save_risk()**: Persist risk to SQLite
- **load_risk()**: Retrieve single risk by ID
- **load_all_risks()**: Load all risks ordered by creation date
- **update_status()**: Transition with history recording
- **get_history()**: Retrieve audit trail
- **validate_state_machine()**: Consistency check for all risks

**Key Design Decision**: SQLite chosen over JSON files for:
- Atomic updates (no partial writes)
- Query capability (filter by status, level)
- Audit history (automatic with risk_history table)
- Concurrent access support

---

### 2.5 models/risk.py — Data Models

**Risk Dataclass**:
```python
@dataclass
class Risk:
    # Identification [FR-01]
    id: str                      # Auto-generated: R-{8-char-hex}
    title: str
    description: str
    dimension: RiskDimension
    
    # Evaluation [FR-02]
    probability: float           # 0.0-1.0
    impact: int                  # 1-5
    detectability_factor: float  # 0.5-1.0
    _score: float                # Computed, read-only
    
    # Response [FR-03]
    level: RiskLevel
    strategy: StrategyType
    mitigation: str              # Summary
    mitigation_plan: MitigationPlan
    
    # Tracking [FR-04]
    status: RiskStatus
    owner: str
    evidence: List[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
```

**MitigationPlan Dataclass**:
```python
@dataclass
class MitigationPlan:
    immediate: List[str]     # 24h actions
    short_term: List[str]    # 1 week actions
    long_term: List[str]     # 1 month actions
    fallback: List[str]      # Escalation path
```

**Enums** (models/enums.py):
- `RiskDimension`: TECHNICAL, OPERATIONAL, EXTERNAL
- `RiskLevel`: LOW, MEDIUM, HIGH, CRITICAL
- `RiskStatus`: OPEN, MITIGATED, ACCEPTED, ESCALATED, CLOSED
- `StrategyType`: AVOID, MITIGATE, TRANSFER, ACCEPT

**RiskAssessmentResult**:
- Aggregates all risks with computed statistics
- Provides computed properties: `critical_count`, `high_count`, `open_count`, etc.

---

### 2.6 constitution/risk_assessment_checker.py — Constitution Compliance

**Purpose**: Verify risk assessment meets methodology-v2 Constitution standards

**Constitution Thresholds**:
```python
CONSTITUTION_THRESHOLDS = {
    "correctness": 1.0,      # 100% required for risk management
    "security": 1.0,         # 100% - risk countermeasures in place
    "maintainability": 0.7,  # >70% - risk record tracking
}
```

**Required Files**:
- `RISK_ASSESSMENT.md`
- `RISK_REGISTER.md`

**Required Sections** (in RISK_ASSESSMENT.md):
- `## Executive Summary`
- `## Risk Register`
- `## Detailed Assessments`

**Check Methods**:
- `_check_required_files()`: Verify file existence
- `_check_assessment_sections()`: Verify section headers
- `_check_mitigation_plans()`: Verify HIGH/CRITICAL risks have plans
- `_check_register_format()`: Verify table columns
- `_check_status_tracking()`: Validate state machine consistency

**Key Design Decision**: Score-based pass/fail with maintainability threshold of 70% allows flexibility while ensuring critical requirements are met.

---

### 2.7 reports/assessor_report.py — Assessment Report Generation

**Purpose**: Generate human-readable risk assessment markdown files

**Output Files**:
1. `RISK_ASSESSMENT.md` — Full assessment report
2. `RISK_REGISTER.md` — Compact risk register table

**RISK_ASSESSMENT.md Sections**:
1. Header with project, date, phase
2. Executive Summary with statistics
3. Risk Level Legend
4. Risk Register Table (sorted by score)
5. Detailed Assessments per risk
6. Recommendations

**Risk Level Icons**:
- 🔴 CRITICAL (score >= 0.7)
- 🟠 HIGH (score 0.5-0.69)
- 🟡 MEDIUM (score 0.3-0.49)
- 🟢 LOW (score < 0.3)

---

### 2.8 reports/decision_gate_report.py — Decision Gate Reports

**Purpose**: Generate Phase 7 decision gate reports

**Decision States**:
- 🟢 PASS: No blockers, proceed
- 🟡 CONDITIONAL_PASS: Conditions exist, proceed with awareness
- 🔴 BLOCKED: Blockers exist, cannot proceed

**Report Sections**:
1. Decision badge with status
2. Summary text
3. Blockers list (if any)
4. Conditions list (if any)
5. Recommendations list
6. Risk Context summary
7. Sign-off table

---

## 3. Data Flow Design

### 3.1 Risk Assessment Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RISK ASSESSMENT FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Phase 6/7   │
  │ Entry Point │
  └──────┬───────┘
         │ RiskAssessmentEngine.assess()
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  STEP 1: IDENTIFY RISKS (RiskAssessor.assess)                          │
  │                                                                          │
  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
  │  │ scan_code_      │  │ scan_           │  │ scan_phase_     │           │
  │  │ artifacts()     │  │ documentation() │  │ deliverables()  │           │
  │  │                 │  │                 │  │                 │           │
  │  │ • src/*.py      │  │ • docs/*.md     │  │ • 01- to 07-*/  │           │
  │  │ • complexity    │  │ • TODOs/FIXMEs  │  │ • Phase-        │           │
  │  │ • debt patterns │  │ • Missing docs  │  │   specific      │           │
  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘           │
  │           │                    │                    │                    │
  │           └────────────────────┴────────────────────┘                    │
  │                                │                                           │
  │                                ▼                                           │
  │                    ┌───────────────────────┐                             │
  │                    │  enrich_with_patterns │                             │
  │                    │  (pattern matching)    │                             │
  │                    └───────────┬───────────┘                             │
  │                                │                                           │
  └────────────────────────────────┼────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  STEP 2: ASSESS RISKS (RiskScorer)                                      │
  │                                                                          │
  │  For each Risk:                                                         │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  score = calculate(probability, impact, detectability_factor)     │  │
  │  │           = (P × I × D) / 5                                        │  │
  │  │                                                                          │  │
  │  │  level = RiskLevel.from_score(score)                               │  │
  │  │                                                                          │  │
  │  │  # RiskLevel thresholds:                                           │  │
  │  │  #   >= 0.7 → CRITICAL                                              │  │
  │  │  #   >= 0.5 → HIGH                                                  │  │
  │  │  #   >= 0.3 → MEDIUM                                                │  │
  │  │  #   < 0.3  → LOW                                                   │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  STEP 3: GENERATE STRATEGIES (RiskStrategist.generate_all_plans)       │
  │                                                                          │
  │  For each Risk:                                                         │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  strategy = select_by_score(score)                                │  │
  │  │                                                                          │  │
  │  │  # Strategy thresholds:                                          │  │
  │  │  #   > 0.6  → AVOID                                               │  │
  │  │  #   0.3-0.6 → MITIGATE (technical/operational) or TRANSFER      │  │
  │  │  #   < 0.3  → ACCEPT                                              │  │
  │  │                                                                          │  │
  │  │  mitigation_plan = generate_mitigation_plan(risk)                │  │
  │  │                                                                          │  │
  │  │  # Plan structure:                                                │  │
  │  │  #   immediate:  (24h)  Document, notify, assess                  │  │
  │  │  #   short_term: (1w)  Analysis, develop, identify resources     │  │
  │  │  #   long_term:  (1m)  Monitor integration, process updates         │  │
  │  │  #   fallback:       Escalation path                              │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  STEP 4: PERSIST RISKS (RiskTracker.save_risk)                          │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  SQLite: risk_assessment.db                                      │  │
  │  │                                                                  │  │
  │  │  INSERT OR REPLACE INTO risks (...)                              │  │
  │  │                                                                  │  │
  │  │  Also records history:                                           │  │
  │  │  INSERT INTO risk_history (risk_id, old_status, new_status, ...) │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  STEP 5: GENERATE REPORTS (RiskAssessmentReportGenerator)               │
  │                                                                          │
  │  ┌─────────────────────────────────┐  ┌──────────────────────────────┐  │
  │  │  RISK_ASSESSMENT.md             │  │  RISK_REGISTER.md             │  │
  │  │                                 │  │                              │  │
  │  │  • Executive Summary            │  │  • Decision Gate table       │  │
  │  │  • Risk Register Table          │  │  • Risk Entry Table          │  │
  │  │  • Detailed Assessments         │  │                              │  │
  │  │  • Recommendations               │  │                              │  │
  │  └─────────────────────────────────┘  └──────────────────────────────┘  │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │  RiskAssessment │
                         │     Result      │
                         └─────────────────┘
```

### 3.2 Decision Gate Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DECISION GATE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Phase 7     │
  │ Entry Point │
  └──────┬───────┘
         │ RiskAssessmentEngine.evaluate_gates()
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  LOAD ALL RISKS (RiskTracker.load_all_risks)                            │
  │                                                                          │
  │  SELECT * FROM risks ORDER BY created_at DESC                           │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  EVALUATE GATES                                                         │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  BLOCKERS (Critical Path):                                        │  │
  │  │                                                                  │  │
  │  │  IF any risk.level == CRITICAL AND risk.status == OPEN:          │  │
  │  │     → BLOCKER: "{n} CRITICAL risks remain OPEN"                  │  │
  │  │                                                                  │  │
  │  │  Result: can_proceed = False                                      │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  CONDITIONS (Warning Path):                                       │  │
  │  │                                                                  │  │
  │  │  IF any risk.level == HIGH AND no mitigation_plan.short_term:    │  │
  │  │     → CONDITION: "{n} HIGH risks need mitigation plans"         │  │
  │  │                                                                  │  │
  │  │  IF resolution_rate < 50% AND open_count > 5:                    │  │
  │  │     → CONDITION: "Risk resolution rate is low"                    │  │
  │  │                                                                  │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐  │
  │  │  RECOMMENDATIONS (Info Path):                                    │  │
  │  │                                                                  │  │
  │  │  IF any OPEN risk.updated_at > 30 days ago:                       │  │
  │  │     → RECOMMENDATION: "{n} OPEN risks stale > 30 days"          │  │
  │  │                                                                  │  │
  │  └──────────────────────────────────────────────────────────────────┘  │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  RETURN DecisionGateResult                                              │
  │                                                                          │
  │  {                                                                       │
  │    can_proceed: bool,                                                   │
  │    conditions: List[str],  # 🟡 Warnings                                 │
  │    blockers: List[str],    # 🔴 Critical blocks                          │
  │    recommendations: List[str],  # 💡 Suggestions                        │
  │    assessed_at: datetime,                                               │
  │    status: "PASS" | "CONDITIONAL_PASS" | "BLOCKED"                     │
  │  }                                                                       │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  GENERATE REPORT (DecisionGateReportGenerator)                          │
  │                                                                          │
  │  Phase7_DecisionGate_Report.md                                          │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Status Update Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STATUS UPDATE FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Manual/API  │
  │ Call        │
  └──────┬───────┘
         │ RiskAssessmentEngine.update_status(risk_id, new_status, ...)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  VALIDATE TRANSITION (RiskStatus.can_transition_to)                     │
  │                                                                          │
  │  Valid transitions:                                                       │
  │                                                                          │
  │  OPEN        → MITIGATED, ACCEPTED, ESCALATED                           │
  │  MITIGATED   → CLOSED, ESCALATED, OPEN                                  │
  │  ACCEPTED    → CLOSED, ESCALATED                                        │
  │  ESCALATED   → CLOSED, OPEN                                             │
  │  CLOSED      → (terminal state, no transitions)                         │
  │                                                                          │
  │  IF invalid: return (False, "Invalid transition: {old} → {new}")         │
  │                                                                          │
  └─────────────────────────────────────────────────────────────────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │ Valid?            │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │ NO                                    │ YES
              ▼                                        ▼
  ┌───────────────────────┐              ┌───────────────────────────────┐
  │ return (False, error) │              │ UPDATE RISK (RiskTracker)     │
  │                       │              │                               │
  │                       │              │ 1. risk.status = new_status   │
  │                       │              │ 2. risk.updated_at = now()     │
  │                       │              │ 3. IF CLOSED: risk.closed_at   │
  │                       │              │                               │
  │                       │              │ 4. save_risk(risk)            │
  │                       │              │                               │
  │                       │              │ 5. _record_history(...)        │
  │                       │              │                               │
  └───────────────────────┘              └───────────────────────────────┘
                                                       │
                                                       ▼
                                            ┌───────────────────────┐
                                            │ return (True, message) │
                                            └───────────────────────┘
```

---

## 4. Integration Points

### 4.1 Phase Integration

| Phase | Integration Point | Data Flow |
|-------|------------------|-----------|
| Phase 1 | Requirements risks | Scanned via _scan_phase_deliverables |
| Phase 2 | Architecture drift | Detected via TECHNICAL_PATTERNS |
| Phase 3 | Code quality | Scanned via identify_from_code |
| Phase 4 | Test coverage | Flaky tests detected via patterns |
| Phase 5 | Deployment risks | Detected via OPERATIONAL_PATTERNS |
| Phase 6 | Risk management | Primary consumer of engine |
| Phase 7 | Decision gate | Uses evaluate_gates() |

### 4.2 Feature Integration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FEATURE INTEGRATION MAP                                  │
│                                                                              │
│  ┌─────────────┐                                                             │
│  │ Feature #1  │                                                             │
│  │ Quality Gate│                                                             │
│  └──────┬──────┘                                                             │
│         │ Constitution checker                                               │
│         │ ┌─────────────────────────────────────────────────────────────┐  │
│         └►│ risk_management_constitution_checker.py                      │  │
│           │ (quality_gate/constitution/)                                 │  │
│           └─────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    RiskAssessmentConstitutionChecker                 │  │
│  │                                                                     │  │
│  │  Uses thresholds from: quality_gate                                  │  │
│  │  ├── correctness: 1.0                                               │  │
│  │  ├── security: 1.0                                                  │  │
│  │  └── maintainability: 0.7                                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    RiskAssessmentEngine                                │  │
│  │                                                                     │  │
│  │  Integrates with:                                                   │  │
│  │  ├── Feature #2: Phase state (detect current phase)                │  │
│  │  ├── Feature #3: Execution artifacts (scan deliverables)           │  │
│  │  ├── Feature #4: Quality metrics (test coverage, etc.)              │  │
│  │  ├── Feature #5: Deployment configs (operational risks)             │  │
│  │  ├── Feature #6: Monitoring data (alerting patterns)                │  │
│  │  └── Feature #7: Decision records (Phase 7 gates)                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Output Artifacts                                   │  │
│  │                                                                     │  │
│  │  RISK_ASSESSMENT.md ──────────────────────────────────────────► Phase 6 │
│  │  RISK_REGISTER.md   ──────────────────────────────────────────► Phase 7│
│  │  risk_assessment.db ────────────────────────────────────────► Reporting │
│  │                                                                     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 External Data Sources

| Source | Type | Purpose |
|--------|------|---------|
| `src/` directory | Code | Technical risk detection |
| `docs/` directory | Documentation | Operational risk detection |
| `01-` to `07-` directories | Phase artifacts | Phase-specific risk indicators |
| `.methodology/state.json` | State | Current phase detection |
| `RISK_ASSESSMENT.md` | Report | Human-readable assessment |
| `RISK_REGISTER.md` | Register | Risk tracking table |
| `risk_assessment.db` | SQLite | Persistence and audit |

---

## 5. Key Design Decisions

### D-001: Score Formula Normalization

**Decision**: `Score = (P × I × D) / 5` normalized to 0-1 range

**Context**: 
- Risk scores needed to be comparable across different risk dimensions
- Raw multiplication would yield 0-25 range
- Normalization to 0-1 provides intuitive probability-like interpretation

**Options Considered**:
1. Raw multiplication (0-25): Rejected — unintuitive, hard to compare
2. Division by 25: Considered — yields 0-1 but peaks at 1.0
3. Division by 5: Chosen — yields 0-1 with better distribution

**Outcome**: Implemented as `round(prob * imp * det / 5, 3)`

---

### D-002: State Machine Design

**Decision**: Explicit allow-list state transitions instead of implicit deny

**Context**:
- Risk status transitions need strict control
- Invalid transitions (e.g., CLOSED → OPEN) would corrupt data

**Options Considered**:
1. Implicit deny (all transitions allowed): Rejected — data integrity risk
2. Explicit allow-list: Chosen — clear, auditable, maintainable
3. Transition matrix: Over-engineered for this use case

**Outcome**: Dictionary-based `valid_transitions` mapping in `RiskStatus.can_transition_to()`

---

### D-003: Persistence Strategy

**Decision**: SQLite over JSON files for risk storage

**Context**:
- Risk data needs atomic updates
- History tracking requires relational schema
- Multiple concurrent readers expected

**Options Considered**:
1. JSON files: Rejected — no atomic updates, no querying
2. SQLite: Chosen — ACID compliant, queryable, auditable
3. PostgreSQL: Over-engineered — single project, no network needed

**Outcome**: SQLite with `risks` and `risk_history` tables

---

### D-004: Pattern-Based Risk Identification

**Decision**: Regex patterns over ML/NLP for risk detection

**Context**:
- Deterministic results required for audit
- Patterns need version control
- Explainability critical for methodology compliance

**Options Considered**:
1. ML-based classification: Rejected — not deterministic, requires training
2. Rule-based regex: Chosen — deterministic, versioned, explainable
3. LLM-based: Rejected — non-deterministic, expensive, no audit trail

**Outcome**: Pattern dictionaries by dimension in `RiskScorer`

---

### D-005: Mitigation Plan Time Horizons

**Decision**: Four-tier time horizon (immediate/short_term/long_term/fallback)

**Context**:
- Standard project management terminology preferred
- Actions needed at different urgency levels
- Fallback/escalation path required

**Options Considered**:
1. Two-tier (immediate/long-term): Rejected — loses granularity
2. Three-tier (immediate/short/long): Rejected — no explicit escalation
3. Four-tier with fallback: Chosen — complete coverage

**Outcome**: Implemented in `MitigationPlan` dataclass

---

### D-006: Strategy Selection Heuristic

**Decision**: Score-based strategy selection with dimension override

**Context**:
- High scores require AVOID strategy
- Medium scores benefit from MITIGATE
- External risks may warrant TRANSFER

**Options Considered**:
1. Pure score-based: Rejected — doesn't account for risk type
2. Score + dimension override: Chosen — more nuanced
3. Full decision tree: Over-engineered

**Outcome**: `RiskStrategist.generate()` with threshold-based selection and dimension consideration

---

### D-007: Report Format Choice

**Decision**: Markdown files for human output, SQLite for machine output

**Context**:
- Phase deliverables need human-readable format
- Risk register needs machine-processable format
- Constitution requires markdown artifacts

**Options Considered**:
1. Markdown only: Rejected — no querying capability
2. Database only: Rejected — no human review capability
3. Both: Chosen — best of both worlds

**Outcome**: Markdown reports + SQLite persistence

---

### D-008: Constitution Check Threshold

**Decision**: 70% maintainability threshold, 100% correctness/security

**Context**:
- Risk assessment is critical for project success
- Some flexibility needed for non-critical requirements
- Constitution mandates high standards

**Options Considered**:
1. 100% across board: Rejected — too rigid, phase-dependent
2. Tiered thresholds: Chosen — appropriate rigor for each aspect

**Outcome**: `CONSTITUTION_THRESHOLDS` with tiered values

---

## 6. File Inventory

| File | Purpose | Lines | Dependencies |
|------|---------|-------|--------------|
| `engine/engine.py`| File | Purpose | Dependencies |
|------|---------|--------------|
| `engine/engine.py` | Main engine facade | assessor, strategist, tracker |
| `engine/assessor.py` | Risk identification & scoring | models/risk, models/enums |
| `engine/strategist.py` | Strategy generation | models/risk, models/enums |
| `engine/tracker.py` | Status tracking & persistence | models/risk, models/enums, sqlite3 |
| `models/enums.py` | Enumeration types | — |
| `models/risk.py` | Risk data models | models/enums |
| `constitution/risk_assessment_checker.py` | Constitution compliance | engine/tracker |
| `reports/assessor_report.py` | Assessment report generation | models/risk |
| `reports/decision_gate_report.py` | Decision gate reports | engine/engine |

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Module | Test File | Coverage |
|--------|-----------|----------|
| assessor.py | `tests/test_assessor.py` | Pattern detection, score calculation |
| strategist.py | `tests/test_strategist.py` | Strategy selection, plan generation |
| tracker.py | `tests/test_tracker.py` | CRUD operations, state transitions |

### 7.2 Test Scenarios

**RiskScorer Tests**:
- Score calculation: `(P × I × D) / 5` boundary conditions
- Probability adjustment: pattern match counting
- Impact assessment: dimension-specific factors

**RiskAssessor Tests**:
- Code scanning: identifies technical debt patterns
- Documentation scanning: identifies TODOs/FIXMEs
- Phase detection: reads `.methodology/state.json`

**RiskStrategist Tests**:
- Strategy selection: score thresholds
- Mitigation plan structure: all four tiers present
- Plan summarization: single-line output

**RiskTracker Tests**:
- Save/load: roundtrip serialization
- State transitions: valid/invalid transitions
- History recording: audit trail completeness

---

## 8. Usage Examples

### 8.1 Basic Assessment

```python
from feature_09_risk_assessment import RiskAssessmentEngine

# Initialize engine
engine = RiskAssessmentEngine(project_root="/path/to/project")

# Run full assessment
result = engine.assess()

print(f"Total risks: {result.total_risks}")
print(f"Critical: {result.critical_count}")
print(f"Average score: {result.average_score:.3f}")
```

### 8.2 Decision Gate Evaluation

```python
# Evaluate Phase 7 gates
gate_result = engine.evaluate_gates()

if gate_result.can_proceed:
    print("✅ Can proceed to next phase")
elif gate_result.status == "CONDITIONAL_PASS":
    print("⚠️ Proceed with conditions:")
    for cond in gate_result.conditions:
        print(f"  - {cond}")
else:
    print("❌ BLOCKED:")
    for blocker in gate_result.blockers:
        print(f"  - {blocker}")
```

### 8.3 Status Update

```python
# Update risk status
from feature_09_risk_assessment.models.enums import RiskStatus

success, message = engine.update_status(
    risk_id="R-A1B2C3D4",
    new_status=RiskStatus.MITIGATED,
    changed_by="alice",
    note="Applied security patch"
)

print(message)
```

---

## 9. Error Handling

### 9.1 Known Error Cases

| Error | Detection | Handling |
|-------|-----------|----------|
| Database corruption | SQLite integrity check | Recreate schema, log warning |
| Invalid state transition | `can_transition_to()` | Return error, no state change |
| Missing project root | Path check | Raise `FileNotFoundError` |
| Missing required files | Constitution check | Log violation, continue |
| Score calculation overflow | try/except | Default to 0.3 (MEDIUM) |

### 9.2 Graceful Degradation

If database is unavailable:
1. Try markdown-based risk loading
2. Generate reports from in-memory data
3. Log warning about degraded mode

---

## 10. Maintenance Notes

### 10.1 Adding New Risk Patterns

To add a new pattern:
1. Edit `engine/assessor.py`
2. Add regex to appropriate `*_PATTERNS` dict
3. Add test case in `tests/test_assessor.py`
4. Document in this ARCHITECTURE.md

### 10.2 Adding New Risk Dimensions

To add a new dimension:
1. Edit `models/enums.py` — add to `RiskDimension`
2. Edit `engine/assessor.py` — add pattern dict
3. Edit `engine/strategist.py` — add context mapping
4. Update constitution checker if needed

### 10.3 Schema Migrations

SQLite schema changes require migration script:
1. Create `migrations/` directory
2. Name scripts `001_add_column.py`, etc.
3. Include upgrade and downgrade functions
4. Test on sample database

---

*Document generated: 2026-04-20*  
*Feature #9 Risk Assessment Engine v1.0.0*
