---
name: test-framework
description: Test Framework for methodology-v2. Use when: (1) Writing unit tests for agents, (2) Integration testing, (3) CI/CD integration. Provides testing utilities and test generation.
---

# Test Framework

Testing utilities for methodology-v2.

## Quick Start

```python
from test_framework import AgentTest, TestSuite

# Unit test
test = AgentTest("test_coder")
test.assert_equals(agent.run("2+2"), "4")

# Run suite
suite = TestSuite()
suite.add_test(test)
suite.run()
```

## Features

### 1. Agent Testing

```python
from test_framework import AgentTest

test = AgentTest("math_agent")
test.assert_equals("2+2", "4", "Basic math")
test.assert_contains("hello world", "hello", "Contains check")
test.assert_error("invalid input", "Error", "Error handling")
```

### 2. Integration Testing

```python
from test_framework import IntegrationTest

test = IntegrationTest("workflow")
test.test_workflow([
    {"agent": "coder", "input": "hello", "expected": "response"}
])
```

### 3. CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pytest tests/
```

## Test Types

| Type | Description |
|------|-------------|
| UnitTest | Single agent test |
| IntegrationTest | Multi-agent workflow test |
| E2ETest | Full end-to-end test |
| LoadTest | Performance testing |

## CLI Usage

```bash
# Run tests
python test_framework.py run

# Generate tests
python test_framework.py generate --agent my_agent

# Coverage
python test_framework.py coverage
```

## Best Practices

1. **Test edge cases** - Not just happy path
2. **Mock external services** - Use fixtures
3. **Keep tests fast** - < 1 second per test
4. **CI/CD** - Run on every push
