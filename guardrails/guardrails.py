"""
Built-in Guardrails for methodology-v2

Enterprise-grade security filters that work out of the box.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardResult:
    """Result from guard check"""
    safe: bool
    threats: List[Dict] = None
    masked: str = None
    action: str = "allow"
    
    def __post_init__(self):
        if self.threats is None:
            self.threats = []


class PromptInjectionGuard:
    """Detect prompt injection attacks"""
    
    PATTERNS = [
        r"ignore\s+(all\s+)?(previous|earlier|above)\s+instructions",
        r"(forget|discard)\s+(all\s+)?(previous|earlier|your)\s+(instructions|prompt)",
        r"you\s+are\s+(now|currently)\s+(a|acting\s+as)",
        r"system\s+prompt",
        r"#{2,}\s*system\s*prompt",
        r"\.{3,}\s*system\s*message",
        r"override\s+(your\s+)?safety",
        r"bypass\s+(your\s+)?filters",
        r"new\s+instructions:",
        r"for the following purposes?,",
        r"pretend\s+to\s+be",
        r"roleplay\s+as",
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.PATTERNS]
    
    def check(self, text: str) -> GuardResult:
        """Check for prompt injection"""
        threats = []
        
        for i, pattern in enumerate(self.patterns):
            if pattern.search(text):
                threats.append({
                    "type": "prompt_injection",
                    "severity": ThreatLevel.HIGH.value,
                    "pattern_index": i,
                    "message": "Potential prompt injection detected"
                })
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            action="block" if threats else "allow"
        )


class PIIFilter:
    """Filter personally identifiable information"""
    
    PATTERNS = {
        "email": re.compile(r'[\w.-]+@[\w.-]+\.\w+'),
        "phone": re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
        "credit_card": re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    }
    
    def __init__(self, enabled_types: List[str] = None):
        self.enabled_types = enabled_types or list(self.PATTERNS.keys())
    
    def mask(self, text: str) -> GuardResult:
        """Mask PII in text"""
        masked_text = text
        threats = []
        
        for pii_type in self.enabled_types:
            if pii_type in self.PATTERNS:
                pattern = self.PATTERNS[pii_type]
                matches = pattern.findall(text)
                
                if matches:
                    masked_text = pattern.sub(f"[{pii_type.upper()}]", masked_text)
                    threats.append({
                        "type": "pii_detected",
                        "severity": ThreatLevel.MEDIUM.value,
                        "pii_type": pii_type,
                        "count": len(matches)
                    })
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            masked=masked_text,
            action="mask" if threats else "allow"
        )
    
    def check(self, text: str) -> GuardResult:
        """Check for PII without masking"""
        threats = []
        
        for pii_type in self.enabled_types:
            if pii_type in self.PATTERNS:
                pattern = self.PATTERNS[pii_type]
                if pattern.search(text):
                    threats.append({
                        "type": "pii_detected",
                        "severity": ThreatLevel.MEDIUM.value,
                        "pii_type": pii_type
                    })
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            action="block" if threats else "allow"
        )


class ContentModerator:
    """Content moderation for harmful content"""
    
    CATEGORIES = {
        "hate_speech": ["hate", "racist", "sexist", "discriminate"],
        "violence": ["kill", "attack", "murder", "weapon"],
        "self_harm": ["suicide", "self harm", "kill yourself"],
        "sexual": ["nsfw", "porn", "explicit"],
        "harassment": ["bully", "harass", "threaten"],
    }
    
    def __init__(self):
        self.category_weights = {
            "hate_speech": ThreatLevel.HIGH,
            "violence": ThreatLevel.HIGH,
            "self_harm": ThreatLevel.CRITICAL,
            "sexual": ThreatLevel.MEDIUM,
            "harassment": ThreatLevel.MEDIUM,
        }
    
    def check(self, text: str) -> GuardResult:
        """Check content for violations"""
        text_lower = text.lower()
        threats = []
        
        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    threats.append({
                        "type": "content_violation",
                        "severity": self.category_weights[category].value,
                        "category": category,
                        "keyword": keyword
                    })
                    break
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            action="block" if threats else "allow"
        )


class SQLInjectionGuard:
    """Prevent SQL injection"""
    
    DANGEROUS_PATTERNS = [
        r"'\s*OR\s+'?\d*'?\s*=\s*'?\d*'?",
        r"'\s*OR\s+'?\w+'?\s*=\s*'?\w*'?",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"INSERT\s+INTO",
        r"UPDATE\s+\w+\s+SET",
        r"EXEC(\s|\()+",
        r"UNION\s+SELECT",
        r"--\s*$",
        r";\s*DROP",
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
    
    def check(self, text: str) -> GuardResult:
        """Check for SQL injection"""
        threats = []
        
        for pattern in self.patterns:
            if pattern.search(text):
                threats.append({
                    "type": "sql_injection",
                    "severity": ThreatLevel.CRITICAL.value,
                    "message": "Potential SQL injection detected"
                })
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            action="block" if threats else "allow"
        )


class SecurityScanner:
    """Scan for exposed secrets"""
    
    SECRET_PATTERNS = {
        "api_key": re.compile(r'(api[_-]?key|apikey)\s*[:=]\s*["\']?[\w-]{20,}["\']?', re.IGNORECASE),
        "password": re.compile(r'password\s*[:=]\s*["\']?[^\s"\']{4,}["\']?', re.IGNORECASE),
        "secret": re.compile(r'(secret|private[_-]?key)\s*[:=]\s*["\']?[^\s"\']{10,}["\']?', re.IGNORECASE),
        "token": re.compile(r'(bearer\s+)?token\s*[:=]\s*["\']?[\w-]{20,}["\']?', re.IGNORECASE),
    }
    
    def check(self, text: str) -> GuardResult:
        """Check text for exposed secrets (alias for scan_code)"""
        return self.scan_code(text)
    
    def scan_code(self, code: str) -> GuardResult:
        """Scan code for exposed secrets"""
        threats = []
        
        for secret_type, pattern in self.SECRET_PATTERNS.items():
            if pattern.search(code):
                threats.append({
                    "type": "secret_exposed",
                    "severity": ThreatLevel.CRITICAL.value,
                    "secret_type": secret_type,
                    "message": f"Potential {secret_type} exposed"
                })
        
        return GuardResult(
            safe=len(threats) == 0,
            threats=threats,
            action="block" if threats else "allow"
        )


class Guard:
    """
    Main Guard class - zero-config security.
    
    Usage:
        guard = Guard()
        result = guard.check(user_input)
    """
    
    def __init__(self, enabled_guards: List[str] = None):
        self.enabled_guards = enabled_guards or [
            "prompt_injection",
            "pii_filter",
            "content_moderation",
            "sql_injection",
            "security_scanner",
        ]
        
        self.guards = {
            "prompt_injection": PromptInjectionGuard(),
            "pii_filter": PIIFilter(),
            "content_moderation": ContentModerator(),
            "sql_injection": SQLInjectionGuard(),
            "security_scanner": SecurityScanner(),
        }
    
    def enable_all(self):
        """Enable all guards"""
        self.enabled_guards = list(self.guards.keys())
    
    def check(self, text: str, mask_pii: bool = True) -> GuardResult:
        """Check text against all enabled guards"""
        all_threats = []
        
        for guard_name in self.enabled_guards:
            if guard_name not in self.guards:
                continue
            
            guard = self.guards[guard_name]
            
            if guard_name == "pii_filter" and mask_pii:
                result = guard.mask(text)
            else:
                result = guard.check(text)
            
            all_threats.extend(result.threats)
        
        # Determine action
        if any(t.get("severity") == ThreatLevel.CRITICAL.value for t in all_threats):
            action = "block"
        elif any(t.get("severity") == ThreatLevel.HIGH.value for t in all_threats):
            action = "review"
        elif all_threats:
            action = "mask"
        else:
            action = "allow"
        
        return GuardResult(
            safe=len(all_threats) == 0,
            threats=all_threats,
            action=action
        )


class GuardrailsSuite:
    """
    Full-featured guardrails suite with configuration.
    
    Usage:
        suite = GuardrailsSuite()
        suite.enable_all()
        result = suite.scan(user_input)
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.guard = Guard(
            enabled_guards=self.config.get("enabled_guards")
        )
        self.sensitivity = self.config.get("sensitivity", "medium")
    
    def enable(self, guard_name: str):
        """Enable specific guard"""
        if guard_name not in self.guard.enabled_guards:
            self.guard.enabled_guards.append(guard_name)
    
    def disable(self, guard_name: str):
        """Disable specific guard"""
        if guard_name in self.guard.enabled_guards:
            self.guard.enabled_guards.remove(guard_name)
    
    def enable_all(self):
        """Enable all guards"""
        self.guard.enable_all()
    
    def set_sensitivity(self, level: str):
        """Set sensitivity level"""
        self.sensitivity = level
        
        # Adjust guards based on sensitivity
        if level == "low":
            self.disable("content_moderation")
            self.disable("pii_filter")
        elif level == "high":
            self.enable_all()
    
    def scan(self, text: str) -> GuardResult:
        """Scan text"""
        return self.guard.check(text)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Guardrails CLI")
    parser.add_argument("command", choices=["check", "scan"])
    parser.add_argument("input", help="Text or file to check")
    
    args = parser.parse_args()
    
    guard = Guard()
    guard.enable_all()
    
    if args.command == "check":
        result = guard.check(args.input)
        print(f"Safe: {result.safe}")
        print(f"Action: {result.action}")
        if result.threats:
            print(f"Threats: {result.threats}")
    elif args.command == "scan":
        with open(args.input, "r") as f:
            content = f.read()
        result = guard.check(content)
        print(f"Safe: {result.safe}")
        print(f"Threats: {len(result.threats)}")
