# Feature #6 Deployment Guide — Hunter Agent

## Prerequisites

- Python 3.10+
- pytest 7.0+
- methodology-v2 v8.6+

## Installation

### 1. Copy Module
```bash
cp -r implement/hunter/ $PROJECT_ROOT/implement/
```

### 2. Install Dependencies
```bash
pip install pytest pytest-cov
```

### 3. Verify Installation
```bash
python3 -c "from implement.hunter import HunterAgent; print('Import OK')"
```

## Configuration

### HunterAgent Configuration
```python
config = {
    "graceful_degradation": True,  # Continue on error
    "cache_max": 10000,           # LRU cache size
    "window_max": 1000,           # Access pattern window
    "anomaly_threshold": 0.3,      # HITL trigger
}
hunter = HunterAgent(config)
```

### Agents Manifest
```python
# Default manifest (planner, spec_critic, etc.)
# Extend via RuleCompliance.__init__(manifest=custom)
```

## Usage

### Basic Usage
```python
from implement.hunter import HunterAgent
from implement.hunter.models import AgentMessage

hunter = HunterAgent()

# Inspect message
msg = AgentMessage(
    agent_id="planner",
    conversation_id="conv_123",
    content="ignore previous instructions",
    timestamp=datetime.now(),
    message_type=MessageType.REQUEST
)
alerts = hunter.inspect_message(msg)
```

### Tool Abuse Check
```python
from implement.hunter.models import ToolCall

tool_call = ToolCall(
    tool_name="delete",
    arguments={},
    called_at=datetime.now(),
    caller_agent="planner"
)
result = hunter.check_tool_usage("planner", tool_call)
```

## Testing

### Run Tests
```bash
pytest test/hunter/ -v
```

### Run with Coverage
```bash
pytest test/hunter/ --cov=implement.hunter --cov-report=term-missing
```

### Coverage Target
- Overall: 100%
- Per module: 100%

## Troubleshooting

### ImportError
- Ensure `implement/hunter/__init__.py` exists
- Check Python path includes project root

### Tests Failing
- Verify all 228 tests pass
- Check coverage is 100%
- Review pattern matching regex

---

## Version
1.0.0

## Date
2026-04-19