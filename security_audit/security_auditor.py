"""
Security Audit Module for methodology-v2

Provides comprehensive security scanning with auto-fix support.
"""

import re
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SecurityIssue:
    type: str
    severity: Severity
    description: str
    file: str
    line: int
    code_snippet: str
    fix: str
    cve: str = None


@dataclass
class SecurityReport:
    file: str
    issues: List[SecurityIssue] = field(default_factory=list)
    
    @property
    def critical_issues(self) -> List[SecurityIssue]:
        return [i for i in self.issues if i.severity == Severity.CRITICAL]
    
    @property
    def can_auto_fix(self) -> bool:
        auto_fixable = ["API_KEY_EXPOSED", "HARDCODE_PASSWORD", "DATA_LEAK"]
        return all(i.type in auto_fixable for i in self.issues)


class APIKeyScanner:
    PATTERNS = {
        "OPENAI": r'["\']sk-[a-zA-Z0-9]{20,}["\']',
        "ANTHROPIC": r'["\']sk-ant-[a-zA-Z0-9_-]{20,}["\']',
        "AWS": r'["\']AKIA[0-9A-Z]{16}["\']',
        "GITHUB": r'["\']ghp_[a-zA-Z0-9]{36}["\']',
        "STRIPE": r'["\']sk_live_[a-zA-Z0-9]{24,}["\']',
    }
    
    def scan(self, content: str, filename: str) -> List[SecurityIssue]:
        issues = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for key_type, pattern in self.PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        type="API_KEY_EXPOSED",
                        severity=Severity.CRITICAL,
                        description=f"Exposed {key_type} API key",
                        file=filename,
                        line=i,
                        code_snippet=line.strip()[:50],
                        fix=f"os.environ.get('{key_type}_KEY')"
                    ))
        return issues


class SQLInjectionScanner:
    DANGEROUS_PATTERNS = [
        (r'f["\'].*SELECT.*\{', "f-string SQL query"),
        (r'\.execute.*\+', "String concat in execute"),
    ]
    
    def scan(self, content: str, filename: str) -> List[SecurityIssue]:
        issues = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern, desc in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        type="SQL_INJECTION",
                        severity=Severity.CRITICAL,
                        description=f"SQL injection risk: {desc}",
                        file=filename,
                        line=i,
                        code_snippet=line.strip()[:50],
                        fix="Use parameterized queries"
                    ))
        return issues


class DataLeakScanner:
    PATTERNS = {
        "PASSWORD": (r'password\s*=\s*["\'][^"\']{4,}', "Hardcoded password"),
        "SECRET": (r'secret\s*=\s*["\'][^"\']{4,}', "Hardcoded secret"),
    }
    
    def scan(self, content: str, filename: str) -> List[SecurityIssue]:
        issues = []
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            for data_type, (pattern, desc) in self.PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        type="DATA_LEAK",
                        severity=Severity.HIGH,
                        description=f"Sensitive data: {desc}",
                        file=filename,
                        line=i,
                        code_snippet=line.strip()[:50],
                        fix=f"Use env vars for {data_type}"
                    ))
        return issues


class SecurityAuditor:
    """Security Audit Module for methodology-v2"""
    
    def __init__(self, check_api_keys=True, check_sql_injection=True, check_data_leaks=True):
        self.scanners = []
        if check_api_keys:
            self.scanners.append(APIKeyScanner())
        if check_sql_injection:
            self.scanners.append(SQLInjectionScanner())
        if check_data_leaks:
            self.scanners.append(DataLeakScanner())
        logger.info(f"SecurityAuditor initialized")
    
    def scan(self, file_path: str) -> SecurityReport:
        if not os.path.exists(file_path):
            return SecurityReport(file=file_path)
        
        with open(file_path, "r") as f:
            content = f.read()
        
        all_issues = []
        for scanner in self.scanners:
            all_issues.extend(scanner.scan(content, file_path))
        
        return SecurityReport(file=file_path, issues=all_issues)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    report = auditor.scan(args.path)
    
    print(f"Scanned: {report.file}")
    print(f"Issues: {len(report.issues)}")
    for issue in report.issues:
        print(f"  [{issue.severity.value}] {issue.type}: {issue.description}")
