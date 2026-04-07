---
name: governance
description: Governance and Compliance Module for methodology-v2. Provides policy enforcement, audit trails, compliance reporting, and risk management for enterprise AI agents.
---

# Governance

Enterprise governance and compliance for AI agents.

## Quick Start

```python
from governance import GovernanceEngine, PolicyEnforcer, ComplianceReporter

# Initialize governance
gov = GovernanceEngine()

# Define policies
policy = Policy(
    name="data_privacy",
    rules=["no_pii_storage", "encrypt_sensitive"],
    severity="high"
)
gov.add_policy(policy)

# Enforce
result = enforcer.check(agent_action)

# Compliance report
report = reporter.generate(quarter="Q1_2026")
```

## Features

### 1. Policy Engine

```python
from governance import Policy, PolicyEngine

policy = Policy(
    name="cost_control",
    rules=["max_tokens_per_day", "max_cost_per_request"],
    thresholds={"max_tokens": 100000, "max_cost": 10.0}
)

engine = PolicyEngine()
engine.add_policy(policy)
violations = engine.check(agent_usage)
```

### 2. Audit Trail

```python
from governance import AuditLogger

logger = AuditLogger()
logger.log(
    action="agent.execute",
    agent="coder",
    user="user123",
    result="success",
    metadata={"tokens": 500, "duration": 2.5}
)

# Query
logs = logger.query(start_date="2026-01-01", agent="coder")
```

### 3. Compliance Reporting

```python
from governance import ComplianceReporter

reporter = ComplianceReporter()

# Generate reports
report = reporter.generate(
    framework="SOC2",
    period="Q1_2026"
)

report = reporter.generate(
    framework="GDPR",
    period="2026"
)
```

### 4. Risk Management

```python
from governance import RiskManager

risk_mgr = RiskManager()

# Assess risk
risk_score = risk_mgr.assess(agent_action)
# 0-100 scale

# Get risk profile
profile = risk_mgr.get_profile()
# {'high_risk': 2, 'medium_risk': 5, 'low_risk': 10}
```

### 5. Access Control

```python
from governance import RBAC, Permission

# Define roles
rbac = RBAC()
rbac.add_role("admin", ["*"])
rbac.add_role("developer", ["agent.run", "agent.stop"])
rbac.add_role("viewer", ["agent.status"])

# Check permission
allowed = rbac.check("user123", "agent.run")
```

## CLI Usage

```bash
# Generate compliance report
python governance/reporter.py --framework SOC2 --output report.pdf

# Audit logs
python governance/audit.py --agent coder --start 2026-01-01
```

## Frameworks Supported

| Framework | Description |
|-----------|-------------|
| SOC2 | Service Organization Control |
| GDPR | General Data Protection Regulation |
| HIPAA | Health Insurance Portability |
| ISO27001 | Information Security |

## Best Practices

1. **Log everything** - Complete audit trail
2. **Enforce policies early** - Don't wait for violations
3. **Regular audits** - Monthly compliance checks
4. **Risk scoring** - Proactive risk management
