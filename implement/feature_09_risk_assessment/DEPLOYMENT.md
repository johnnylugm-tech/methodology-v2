# Feature #9 DEPLOYMENT.md

> **Feature**: Risk Assessment Engine  
> **Phase**: 8 - Deployment Documentation  
> **Date**: 2026-04-20  
> **Status**: ✅ READY FOR DEPLOYMENT

---

## 1. Overview

Feature #9 is the Risk Assessment Engine for Layer 4 (Executive Assurance) of the methodology-v2 framework. It provides:
- Risk identification from project artifacts
- Risk evaluation with quantified scores
- Strategy generation for risk response
- State tracking until risk closure

---

## 2. Installation

### 2.1 Prerequisites

- Python 3.10+
- SQLite 3.x
- No external dependencies beyond standard library

### 2.2 Module Import

```python
import sys
sys.path.insert(0, '/path/to/methodology-v2')

from implement.feature_09_risk_assessment.engine.engine import RiskAssessmentEngine
from implement.feature_09_risk_assessment.models.risk import Risk
from implement.feature_09_risk_assessment.models.enums import RiskDimension, RiskLevel, RiskStatus
```

### 2.3 Project Integration

Add to your `pyproject.toml` or import path:
```toml
[tool.pythonpath]
paths = ["implement"]
```

---

## 3. Usage Examples

### 3.1 Basic Assessment

```python
from pathlib import Path
from implement.feature_09_risk_assessment.engine.engine import RiskAssessmentEngine

# Initialize engine
project_root = Path("/path/to/your/project")
engine = RiskAssessmentEngine(project_root=str(project_root))

# Run full risk assessment
result = engine.assess()

print(f"Total risks identified: {len(result.risks)}")
print(f"Average risk score: {result.average_score:.2f}")

for risk in result.risks:
    print(f"  [{risk.level.value}] {risk.title}: {risk.score:.2f}")
```

### 3.2 Risk Tracking

```python
from implement.feature_09_risk_assessment.engine.tracker import RiskTracker
from implement.feature_09_risk_assessment.models.enums import RiskStatus

# Initialize tracker
tracker = RiskTracker(str(project_root / ".methodology" / "risk_assessment.db"))

# Get all open risks
open_risks = tracker.get_open_risks()
print(f"Open risks: {len(open_risks)}")

# Update risk status
tracker.update_status("R-01", RiskStatus.MITIGATED)
```

### 3.3 Strategy Generation

```python
from implement.feature_09_risk_assessment.engine.strategist import RiskStrategist
from implement.feature_09_risk_assessment.models.risk import Risk
from implement.feature_09_risk_assessment.models.enums import RiskDimension, RiskLevel

# Create a risk
risk = Risk(
    id="R-99",
    title="Database performance degradation",
    description="Query response time increasing",
    dimension=RiskDimension.TECHNICAL,
    level=RiskLevel.HIGH,
    status=RiskStatus.OPEN,
    probability=0.7,
    impact=4,
    score=0.0,
    owner="Backend Team",
    mitigation="",
    created_at=None,
    updated_at=None,
    closed_at=None,
    evidence=["slow_query_log.txt"],
    strategy=None
)

# Generate mitigation plan
strategist = RiskStrategist()
plan = strategist.generate_mitigation_plan(risk, "Database performance issue")

print(plan.summary)
# Output:
# ================================================================
# MITIGATION PLAN: Database performance degradation
# ...
```

---

## 4. Monitoring Metrics

### 4.1 Key Metrics to Track

| Metric | Description | Target |
|--------|-------------|--------|
| `total_risks` | Number of identified risks | - |
| `critical_risks` | Critical-level risks | 0 |
| `high_risks` | High-level risks | < 3 |
| `average_score` | Mean risk score | < 0.3 |
| `open_risks_count` | Currently open risks | Decreasing |
| `closed_risks_count` | Closed risks | Increasing |
| `avg_days_to_close` | Average days to close a risk | < 14 days |

### 4.2 Database Queries

```sql
-- Risk distribution by level
SELECT level, COUNT(*) as count FROM risks GROUP BY level;

-- Open risks by dimension
SELECT dimension, COUNT(*) as count FROM risks 
WHERE status != 'CLOSED' GROUP BY dimension;

-- Average time to close
SELECT AVG(julianday(closed_at) - julianday(created_at)) as avg_days 
FROM risks WHERE closed_at IS NOT NULL;

-- Risk score distribution
SELECT 
  CASE 
    WHEN score < 0.2 THEN 'LOW'
    WHEN score < 0.4 THEN 'MEDIUM'
    WHEN score < 0.6 THEN 'HIGH'
    ELSE 'CRITICAL'
  END as category,
  COUNT(*) as count
FROM risks GROUP BY category;
```

---

## 5. Phase Integration

### 5.1 Phase 6 (Risk Management)

Insert at the end of Phase 6 workflow:

```python
def run_phase_6(project_root: str) -> None:
    """Execute Phase 6 risk management."""
    from implement.feature_09_risk_assessment.engine.engine import RiskAssessmentEngine
    
    engine = RiskAssessmentEngine(project_root)
    result = engine.assess()
    
    # Result automatically:
    # - Creates/updates RISK_ASSESSMENT.md
    # - Writes to .methodology/execution_registry.db
    # - Returns RiskAssessmentResult
    
    return result
```

### 5.2 Phase 7 (Decision Gate)

Insert at Phase 7 decision point:

```python
def evaluate_decision_gate(project_root: str) -> str:
    """Evaluate Phase 7 decision gate."""
    from implement.feature_09_risk_assessment.engine.engine import RiskAssessmentEngine
    
    engine = RiskAssessmentEngine(project_root)
    gate_result = engine.evaluate_gates()
    
    # gate_result.status: PASS | CONDITIONAL_PASS | BLOCK
    # gate_result.blocking_risks: List of risks blocking gate
    
    if gate_result.status == "BLOCK":
        raise Exception(f"Decision gate blocked by: {gate_result.blocking_risks}")
    
    return gate_result.status
```

---

## 6. Output Files

### 6.1 Generated Files

| File | Location | Purpose |
|------|----------|---------|
| `RISK_ASSESSMENT.md` | Project root | Human-readable risk report |
| `risk_assessment.db` | `.methodology/` | SQLite persistence |
| `execution_registry.db` | `.methodology/` | Phase execution tracking |

### 6.2 RISK_ASSESSMENT.md Format

```markdown
# Risk Assessment Report

**Project**: {project_name}
**Generated**: {timestamp}
**Phase**: Phase {n}

---

## Executive Summary

- Total Risks: {count}
- Critical: {count} | High: {count} | Medium: {count} | Low: {count}
- Average Score: {avg_score}

## Risk Register

| ID | Title | Dimension | Level | Score | Status | Owner |
|----|-------|-----------|-------|-------|--------|-------|
| R-01 | ... | TECHNICAL | HIGH | 0.72 | OPEN | Agent-A |

## Detailed Assessments

### R-01: {title}
...
```

---

## 7. Troubleshooting

### 7.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `No risks identified` | Empty project or no deliverables scanned | Check that Phase deliverables exist |
| `Risk score NaN` | Invalid probability/impact values | Ensure values are within valid ranges |
| `Status transition failed` | Invalid state machine transition | Check valid transitions in SPEC.md |
| `Database locked` | Multiple processes accessing DB | Use single instance or implement locking |

### 7.2 Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

engine = RiskAssessmentEngine(project_root, debug=True)
result = engine.assess()
```

---

## 8. Health Checks

### 8.1 Pre-Deployment Check

```python
import sys
sys.path.insert(0, '/path/to/methodology-v2')

from implement.feature_09_risk_assessment.engine.engine import RiskAssessmentEngine
from pathlib import Path

def health_check(project_root: str) -> dict:
    """Run pre-deployment health checks."""
    checks = {}
    
    try:
        engine = RiskAssessmentEngine(project_root)
        checks['engine_init'] = True
    except Exception as e:
        checks['engine_init'] = str(e)
    
    try:
        result = engine.assess()
        checks['assessment_run'] = True
        checks['risks_identified'] = len(result.risks)
    except Exception as e:
        checks['assessment_run'] = str(e)
    
    return checks

health = health_check("/path/to/project")
print(health)
```

### 8.2 Expected Output

```python
{
    'engine_init': True,
    'assessment_run': True,
    'risks_identified': 0  # Empty project is valid
}
```

---

## 9. Rollback Procedure

### 9.1 In Case of Issues

1. **Remove generated files**:
   ```bash
   rm -f /path/to/project/RISK_ASSESSMENT.md
   rm -f /path/to/project/.methodology/risk_assessment.db
   ```

2. **Restore previous state**:
   - Files are not overwritten during assessment
   - Only created if not existing or updated with delta

3. **Check execution registry**:
   ```bash
   sqlite3 .methodology/execution_registry.db "SELECT * FROM phase_executions WHERE phase=6"
   ```

---

## 10. Security Considerations

| Concern | Mitigation |
|---------|------------|
| Database injection | Use parameterized queries (SQLite handles this) |
| Path traversal | All paths resolved with `Path.resolve()` |
| Arbitrary code execution | Strategy prompts are sanitized |

---

*Generated: 2026-04-20 11:13 GMT+8*
