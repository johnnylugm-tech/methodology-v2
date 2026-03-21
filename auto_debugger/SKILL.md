---
name: auto-debugger
description: Auto Debugger for methodology-v2. Systematic debugging for AI agents with error classification, root cause analysis, auto-recovery, and debugging dashboard.
---

# Auto Debugger

Systematic debugging for AI agents - inspired by Microsoft's AgentRx.

## Quick Start

```python
from auto_debugger import AutoDebugger, ErrorClassifier, RootCauseAnalyzer

# Initialize debugger
debugger = AutoDebugger()

# Analyze error
result = debugger.analyze(error, agent_state)

# Auto-recover
recovery = debugger.suggest_recovery(error_type)
debugger.auto_recover(agent, error)
```

## Features

### 1. Error Classification (L1-L4)

```python
from auto_debugger import ErrorClassifier

classifier = ErrorClassifier()

error_type = classifier.classify(error)
# L1: Transient (retry)
# L2: Prompt (fix prompt)
# L3: Tool (fix tool)
# L4: System (internal)
```

### 2. Root Cause Analysis

```python
from auto_debugger import RootCauseAnalyzer

analyzer = RootCauseAnalyzer()
cause = analyzer.find_cause(error, trace)

# Returns:
# - missing_context
# - tool_failure
# - model_limitation
# - prompt_issue
# - rate_limit
```

### 3. Auto Recovery

```python
from auto_debugger import AutoRecovery

recovery = AutoRecovery()
action = recovery.suggest_action(error_type)

# Actions:
# - retry_with_backoff
# - simplify_prompt
# - switch_tool
# - reduce_context
# - escalate_to_human
```

### 4. Debug Dashboard

```python
from auto_debugger import DebugDashboard

dashboard = DebugDashboard(port=8080)
dashboard.start()

# Shows:
# - Error frequency
# - Recovery success rate
# - Agent health
# - Trace viewer
```

## CLI Usage

```bash
# Start dashboard
python auto_debugger/dashboard.py

# Analyze error log
python auto_debugger.py analyze --file errors.json
```

## Error Classification

| Level | Type | Example | Action |
|-------|------|---------|--------|
| L1 | Transient | Network timeout | Retry |
| L2 | Prompt | Ambiguous instruction | Fix prompt |
| L3 | Tool | Tool not found | Fix tool |
| L4 | System | Model error | Escalate |

## Integration

```python
# Wrap agent execution
with debugger.trace(agent):
    result = agent.run(task)
    
# On error
if error:
    debugger.log_error(error, agent.state)
    recovery = debugger.suggest_recovery(error)
```

## Best Practices

1. **Always classify errors** - Know the severity
2. **Log traces** - For root cause analysis
3. **Auto-recover when possible** - Reduce manual intervention
4. **Escalate L4** - Don't waste time on system errors
