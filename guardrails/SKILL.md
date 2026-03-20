---
name: guardrails
description: Built-in Guardrails for methodology-v2. Use when: (1) Protecting against prompt injection attacks, (2) Filtering sensitive data (PII), (3) Content moderation, (4) Security scanning. Provides zero-config security filters that work out of the box.
---

# Built-in Guardrails

Enterprise-grade security guardrails that work out of the box.

## Quick Start

```python
from guardrails import Guard, GuardrailsSuite

# Simple one-liner
guard = Guard()
result = guard.check(user_input)

# Full suite
suite = GuardrailsSuite()
suite.enable_all()
result = suite.scan(user_input)
```

## Features

### 1. Prompt Injection Detection

```python
from guardrails import PromptInjectionGuard

guard = PromptInjectionGuard()

# Check input
result = guard.check("Ignore previous instructions and...")
# → {"safe": False, "threat": "prompt_injection"}

# Detection patterns
patterns = [
    "ignore previous",
    "system prompt",
    "you are now",
    "forget all instructions",
]
```

### 2. PII (Personally Identifiable Information) Filter

```python
from guardrails import PIIFilter

filter = PIIFilter()

# Detect and mask
result = filter.mask("My email is john@example.com")
# → "My email is [EMAIL]"

# Supported types
pii_types = [
    "email",
    "phone",
    "credit_card",
    "ssn",
    "address",
    "name",
]
```

### 3. Content Moderation

```python
from guardrails import ContentModerator

mod = ContentModerator()

# Check content
result = mod.check("This is a great product!")
# → {"safe": True, "categories": []}

result = mod.check("You should kill yourself")
# → {"safe": False, "categories": ["self_harm"]}
```

### 4. SQL Injection Prevention

```python
from guardrails import SQLInjectionGuard

guard = SQLInjectionGuard()

result = guard.check("SELECT * FROM users WHERE id = " + user_input)
# → {"safe": False, "threat": "sql_injection"}
```

### 5. Security Scanner

```python
from guardrails import SecurityScanner

scanner = SecurityScanner()

# Scan code
result = scanner.scan_code('''
api_key = "sk-1234567890"
password = "secret123"
''')
# → {"safe": False, "issues": ["api_key_exposed", "password_exposed"]}
```

## Usage Patterns

### Zero-Config (Recommended)

```python
from guardrails import Guard

# Enable all guards with defaults
guard = Guard()
guard.enable_all()

# Check input
result = guard.check(user_input)
```

### Fine-Grained Control

```python
from guardrails import GuardrailsSuite

suite = GuardrailsSuite()

# Enable specific guards
suite.enable("prompt_injection")
suite.enable("pii_filter")
suite.enable("content_moderation")

# Disable specific checks
suite.disable("url_check")

# Set sensitivity
suite.set_sensitivity("high")  # strict
suite.set_sensitivity("medium")  # balanced
suite.set_sensitivity("low")  # permissive

result = suite.scan(user_input)
```

### Integration with QualityGate

```python
from methodology import QualityGate
from guardrails import Guard

# Add guard to quality gate
gate = QualityGate()
gate.add_check("security", Guard().check)

# Use in workflow
result = gate.check(user_input)
```

## Guard Types

| Guard | Description | Default |
|-------|-------------|---------|
| PromptInjectionGuard | Detect prompt injection | Enabled |
| PIIFilter | Mask personal data | Enabled |
| ContentModerator | Check harmful content | Enabled |
| SQLInjectionGuard | Prevent SQL injection | Enabled |
| XSSGuard | Cross-site scripting | Enabled |
| URLValidator | Validate URLs | Disabled |
| FileTypeGuard | Check file types | Disabled |
| CodeScanner | Scan for secrets | Enabled |

## Configuration

```python
from guardrails import GuardrailsSuite, GuardConfig

config = GuardConfig(
    enabled_guards=["prompt_injection", "pii_filter", "content_moderation"],
    sensitivity="medium",
    custom_patterns=[...],
    logging=True,
)

suite = GuardrailsSuite(config=config)
```

## CLI Usage

```bash
# Check input
python guardrails.py check "your input here"

# Scan file
python guardrails.py scan input.txt

# Server mode
python guardrails.py server --port 8080
```

## Response Format

```python
{
    "safe": True/False,
    "threats": [
        {
            "type": "prompt_injection",
            "severity": "high",
            "message": "Potential prompt injection detected"
        }
    ],
    "masked": "Input with sensitive data masked",
    "action": "allow/block/mask"
}
```

## Performance

| Guard | Latency | Accuracy |
|-------|---------|----------|
| Prompt Injection | <5ms | 95% |
| PII Filter | <10ms | 99% |
| Content Moderation | <20ms | 97% |
| SQL Injection | <2ms | 99% |

## Best Practices

1. **Enable all guards in production** - Zero-config security
2. **Log all blocks** - Monitor attack patterns
3. **Test with real inputs** - Validate guard effectiveness
4. **Keep patterns updated** - Threats evolve

## See Also

- [security-audit/](security-audit/) - Full security suite
- [examples/guardrails_examples.py](examples/guardrails_examples.py)
