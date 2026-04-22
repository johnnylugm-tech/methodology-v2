"""Detection patterns for Hunter Agent."""
from .enums import TamperPattern, Severity


TAMPER_PATTERNS = {
    TamperPattern.DIRECT_OVERRIDE: [
        r"ignore\s+(previous|all)\s+(instructions?|directives?)",
        r"disregard\s+(your\s+)?(instructions?|system\s+prompt)",
        r"forget\s+(everything|your\s+instructions|all\s+prior)",
        r"you\s+have\s+no\s+rules",
        r"bypass\s+(your\s+)?(safety|content|filters?)",
    ],
    TamperPattern.ROLE_HIJACK: [
        r"you\s+are\s+now\s+(a\s+)?DAN",
        r"pretend\s+you\s+are",
        r"switch\s+to\s+(developer|admin|root|superuser)",
    ],
    TamperPattern.PERMISSION_ESCALATION: [
        r"grant\s+(me\s+)?(admin|root|sudo|moderator)",
        r"elevate\s+(my\s+)?(privileges|access|permissions?)",
        r"enable\s+(developer|admin|debug|unrestricted)\s*(mode)?",
    ],
    TamperPattern.RULE_MODIFICATION: [
        r"change\s+(your\s+)?system\s+prompt\s+to\s*[:\n]",
        r"modify\s+(your\s+)?(instructions?|rules?|system\s+prompt)",
        r"update\s+system\s+prompt",
    ],
    TamperPattern.CONTEXT_INJECTION: [
        r"append\s+to\s+system\s+prompt",
        r"add\s+to\s+(your\s+)?(instructions|system\s+prompt)",
        r"include\s+this\s+in\s+(your\s+)?context",
    ],
}


FABRICATION_KEYWORDS = [
    "as I said earlier",
    "as I mentioned earlier",
    "as we discussed",
    "as you told me",
    "you told me to",
    "we agreed on",
    "per your request",
    "as you requested",
    "I previously informed you",
    "as established earlier",
    "based on our discussion",
    "as stated before",
    "you instructed me to",
    "you asked me to",
]


PATTERN_SEVERITY = {
    TamperPattern.DIRECT_OVERRIDE: Severity.CRITICAL,
    TamperPattern.ROLE_HIJACK: Severity.CRITICAL,
    TamperPattern.PERMISSION_ESCALATION: Severity.HIGH,
    TamperPattern.RULE_MODIFICATION: Severity.HIGH,
    TamperPattern.CONTEXT_INJECTION: Severity.MEDIUM,
}
