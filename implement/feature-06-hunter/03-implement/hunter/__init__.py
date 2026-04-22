"""Hunter Agent Package.

Exports:
- HunterAgent
- IntegrityValidator
- AnomalyDetector
- RuleCompliance
- RuntimeMonitor
- All enums, models, and exceptions
"""
from .enums import (
    TamperPattern,
    Severity,
    AuthStatus,
    DetectionType,
    ActionType,
    MessageType,
)
from .models import (
    AgentMessage,
    TamperResult,
    FabricateResult,
    PoisonResult,
    AbuseResult,
    IntegrityResult,
    HunterAlert,
    MemoryFact,
    AuthorizationChain,
    ToolCall,
)
from .exceptions import (
    HunterError,
    TamperingDetectionError,
    IntegrityValidationError,
    RuleComplianceError,
    AnomalyDetectionError,
    AuditLogError,
)
from .hunter_agent import HunterAgent

__version__ = "1.0.0"

__all__ = [
    "HunterAgent",
    "TamperPattern",
    "Severity",
    "AuthStatus",
    "DetectionType",
    "ActionType",
    "MessageType",
    "AgentMessage",
    "TamperResult",
    "FabricateResult",
    "PoisonResult",
    "AbuseResult",
    "IntegrityResult",
    "HunterAlert",
    "MemoryFact",
    "AuthorizationChain",
    "ToolCall",
    "HunterError",
    "TamperingDetectionError",
    "IntegrityValidationError",
    "RuleComplianceError",
    "AnomalyDetectionError",
    "AuditLogError",
]
