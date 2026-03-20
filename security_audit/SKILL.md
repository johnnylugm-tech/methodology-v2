---
name: security-audit
description: Security Audit Module for methodology-v2. Use when: (1) Scanning code for security vulnerabilities, (2) Performing security audit before enterprise deployment, (3) Checking API key exposure, (4) Detecting prompt injection attacks, (5) Following methodology-v2 development framework. Provides comprehensive security scanning with fix suggestions.
---

# Security Audit Module

Enterprise-grade security scanning for AI agents, built on methodology-v2.

## Quick Start

```python
import sys
sys.path.insert(0, '/workspace/methodology-v2')
sys.path.insert(0, '/workspace/security-audit/scripts')

from security_auditor import SecurityAuditor

auditor = SecurityAuditor()

# Scan code for security issues
report = auditor.scan("your_agent_code.py")

# Check results
if report.critical_issues:
    print(f"🚨 {len(report.critical_issues)} Critical issues found!")
    for issue in report.critical_issues:
        print(f"  - {issue['type']}: {issue['description']}")
        print(f"    Fix: {issue['fix']}")
```

## Features

| Feature | Description | Threat Level |
|---------|-------------|--------------|
| APIKeyScanner | Detect hardcoded API keys | 🔴 Critical |
| PermissionAuditor | Check excessive permissions | 🔴 Critical |
| DataLeakDetector | Detect sensitive data leaks | 🟠 High |
| PromptInjectionGuard | Detect prompt injection | 🟠 High |
| SQLInjectionScanner | Detect SQL injection risks | 🔴 Critical |
| DependencyChecker | Check vulnerable dependencies | 🟡 Medium |

## Supported Languages

- Python
- JavaScript/TypeScript
- Java
- Go

## Integration with methodology-v2

```python
from methodology import QualityGate
from security_auditor import SecurityAuditor

# Add security check to quality gate
auditor = SecurityAuditor()

def security_check(code_path):
    report = auditor.scan(code_path)
    return len(report.critical_issues) == 0

# Use in workflow
gate = QualityGate()
gate.add_check("security", security_check)
```

## Configuration

```python
from security_auditor import SecurityConfig

config = SecurityConfig(
    check_api_keys=True,
    check_permissions=True,
    check_data_leaks=True,
    check_prompt_injection=True,
    check_sql_injection=True,
    severity_threshold="medium"  # or "high", "critical"
)
```

## CLI Usage

```bash
# Scan file
python security_auditor.py scan path/to/code.py

# Scan with auto-fix
python security_auditor.py scan path/to/code.py --fix

# Generate report
python security_auditor.py report --format json

# Check dependencies
python security_auditor.py deps requirements.txt
```

## Issue Types

| Type | Severity | Example |
|------|----------|---------|
| API_KEY_EXPOSED | Critical | `api_key = "sk-xxx"` |
| HARDCODE_PASSWORD | Critical | `password = "xxx"` |
| PROMPT_INJECTION | High | User input in system prompt |
| SQL_INJECTION | Critical | f"SELECT * FROM {user_input}" |
| DATA_LEAK | High | Logging sensitive data |
| EXCESSIVE_PERMISSION | Medium | Admin access without check |
| DEPENDENCY_VULN | Medium | Known CVE in package |

## Auto-Fix Support

```python
# Auto-fix issues
auditor = SecurityAuditor(auto_fix=True)
report = auditor.scan("code.py")

# Apply fixes
if report.can_auto_fix:
    auditor.apply_fixes(report)
```

## Enterprise Features

| Feature | Description |
|---------|-------------|
| Compliance Reports | SOC2, ISO 27001, GDPR reports |
| Integration | GitHub Actions, GitLab CI |
| Notifications | Slack, PagerDuty alerts |
| Audit Log | Full audit trail |

## See Also

- [references/security_patterns.md](references/security_patterns.md)
- [references/compliance_checks.md](references/compliance_checks.md)
