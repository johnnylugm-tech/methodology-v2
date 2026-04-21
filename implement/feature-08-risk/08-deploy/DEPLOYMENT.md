# Feature #8 Phase 8: Deployment Guide

**Date:** 2026-04-20  
**Phase:** 08-deploy  
**Feature:** 8-Dimensional Risk Assessment Engine

---

## Overview

The Risk Assessment Engine provides comprehensive, multi-dimensional risk evaluation for agent-based system decisions. This guide covers installation, configuration, and integration.

---

## Installation

### Option 1: Copy Module (Recommended for development)

```bash
# Copy the entire feature module
cp -r implement/feature-08-risk/03-implement/ /your/project/

# Verify installation
python3 -c "from risk_assessment_engine import RiskAssessmentEngine; print('OK')"
```

### Option 2: Add to Python Path

```python
import sys
from pathlib import Path

# Add to sys.path before imports
sys.path.insert(0, '/path/to/feature-08-risk/03-implement')

from risk_assessment_engine import RiskAssessmentEngine
```

---

## Configuration

### RiskConfig Options

```python
from config import RiskConfig, create_config

# Default configuration
config = RiskConfig()

# Custom configuration
config = create_config(
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
    },
    uqlm_settings={
        "enabled": True,
        "uncertainty_threshold": 0.3,
        "auto_calibrate": True,
    },
    effort_settings={
        "enabled": True,
        "track_detailed": True,
        "quality_threshold": 0.7,
    },
    limits={
        "max_agent_depth": 5,
        "max_context_window": 200000,
        "max_tokens_per_task": 500000,
        "max_execution_time_minutes": 60,
    }
)
```

### Pre-configured Profiles

```python
from config import create_config

# High security profile
high_security = create_config(
    dimension_weights={"D2": 2.0, "D6": 2.0, "D1": 1.5}
)

# Low latency profile
low_latency = create_config(
    dimension_weights={"D7": 2.0},
    limits={"max_execution_time_minutes": 30}
)
```

---

## Usage

### Basic: Full 8-Dimensional Assessment

```python
from risk_assessment_engine import RiskAssessmentEngine, create_config

# Initialize engine
config = create_config()
engine = RiskAssessmentEngine(config)

# Prepare context
context = {
    "data": user_provided_data,
    "agent_interactions": current_agents,
    "memory_state": current_memory,
    "compliance_context": regulatory_requirements,
}

# Perform risk assessment
result = engine.assess_risk(context)

print(f"Composite Score: {result.composite_score}")
print(f"Risk Level: {result.risk_level.name}")
for dim_id, score in result.dimension_scores.items():
    print(f"  {dim_id}: {score:.2f}")

# Check alerts
for alert in result.alerts:
    print(f"  [{alert.severity}] {alert.alert_type}: {alert.message}")
```

### Single Dimension Assessment

```python
from dimensions.privacy import PrivacyAssessor

assessor = PrivacyAssessor()
score = assessor.assess(context)
print(f"Data Privacy Risk: {score:.2f}")
```

### Decision Logging

```python
from decision_log import DecisionLog, DecisionInput

log = DecisionLog()
decision = DecisionInput(
    choice="Use cached memory for context",
    alternatives=["Fresh fetch from API"],
    confidence_score=7.5,
    effort_minutes=15,
    context={"data": some_data}
)
decision_id = log.log_decision(decision)
print(f"Decision logged: {decision_id}")
```

### Confidence Calibration

```python
from confidence_calibration import ConfidenceCalibrator

calibrator = ConfidenceCalibrator()
result = calibrator.calibrate(
    decision_id="arch-001",
    initial_confidence=7.5,
    actual_outcome=6.8
)
print(f"Calibration error: {result.calibration_error:.2f}")
print(f"Status: {result.calibration_status}")
```

### Effort Tracking

```python
from effort_tracker import EffortTracker

tracker = EffortTracker()
tracking_id = tracker.start_tracking("planner", "task-123")

# ... agent does work ...

tracker.record_tool_call(tracking_id, "web_search", 100, success=True)
tracker.record_token_usage(tracking_id, input_tokens=500, output_tokens=200)
tracker.finish_tracking(tracking_id, quality_score=0.85)

metrics = tracker.get_metrics(tracking_id)
print(f"Time: {metrics.time_spent_minutes:.1f} min")
print(f"Tokens: {metrics.tokens_consumed}")
```

---

## Integration

### With Feature #7 (UQLM Integration)

```python
from uqlm_integration import UQLMIntegration

uqlm = UQLMIntegration()
uncertainty = uqlm.get_uncertainty_score(context)

# Use uncertainty for confidence calibration
calibrated = calibrator.calibrate_with_uncertainty(
    decision_id=decision_id,
    initial_confidence=initial_confidence,
    uqlm_uncertainty=uncertainty
)
```

### With MAS-Hunt Hunter Agent (Feature #6)

```python
# Hunter Agent integration for runtime monitoring
from hunter_agent import HunterAgent

hunter = HunterAgent()
alerts = hunter.monitor_agent_communications(agent_messages)

# Feed Hunter alerts into risk assessment
if alerts:
    context["hunter_alerts"] = alerts
    result = engine.assess_risk(context)
```

### Alert Manager Integration

```python
from alert_manager import AlertManager

manager = AlertManager({
    "enabled": True,
    "notify_on_critical": True,
    "notify_on_high": True,
})

alerts = manager.evaluate(
    dimension_scores=result.dimension_scores,
    composite_score=result.composite_score
)

for alert in alerts:
    print(f"[{alert.severity}] {alert.message}")
    if alert.severity == "CRITICAL":
        # Trigger circuit breaker
        kill_switch.trigger()
```

---

## FastAPI Middleware Example

```python
from fastapi import FastAPI, Request
from risk_assessment_engine import RiskAssessmentEngine, create_config

app = FastAPI()
engine = RiskAssessmentEngine(create_config())

@app.middleware("http")
async def risk_assessment_middleware(request: Request, call_next):
    context = {
        "data": await request.body(),
        "agent_interactions": [],
        "memory_state": {},
        "compliance_context": {}
    }
    
    result = engine.assess_risk(context)
    
    if result.risk_level == "CRITICAL":
        return JSONResponse(
            status_code=403,
            content={"error": "Risk threshold exceeded"}
        )
    
    response = await call_next(request)
    return response
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Add `03-implement/` to `sys.path` |
| ImportError with relative paths | Use absolute import or add module to Python path |
| `datetime.utcnow()` warnings | Replace with `datetime.now(datetime.UTC)` |
| Collection errors in tests | Tests require proper package structure; 179 tests pass individually |
| Low coverage | Some modules (dimensions) cannot be tested due to import structure |

---

## File Structure

```
feature-08-risk/
├── 01-spec/
│   └── SPEC.md                    # Feature specification
├── 02-architecture/
│   └── ARCHITECTURE.md            # Architecture document
├── 03-implement/
│   ├── __init__.py
│   ├── risk_assessment_engine.py # Main engine
│   ├── decision_log.py           # Decision logging
│   ├── confidence_calibration.py  # Confidence calibration
│   ├── effort_tracker.py          # Effort metrics
│   ├── alert_manager.py           # Alert system
│   ├── uqlm_integration.py        # UQLM interface
│   ├── config.py                  # Configuration
│   └── dimensions/                # 8 dimension assessors
│       ├── privacy.py            # D1
│       ├── injection.py           # D2
│       ├── cost.py               # D3
│       ├── uaf_clap.py           # D4
│       ├── memory_poisoning.py    # D5
│       ├── cross_agent_leak.py    # D6
│       ├── latency.py             # D7
│       └── compliance.py         # D8
├── 04-tests/                      # Test files
├── 06-quality/
│   └── QUALITY_REPORT.md          # Quality report
├── 07-risk/
│   └── RISK_REGISTER.md           # Risk register
└── 08-deploy/
    └── DEPLOYMENT.md              # This file
```

---

*Generated: 2026-04-20*