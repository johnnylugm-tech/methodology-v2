"""Enums for Hunter Agent detection types and severity levels."""
from enum import Enum


class TamperPattern(Enum):
    """FR-H-1: Instruction tampering pattern types."""
    DIRECT_OVERRIDE = "direct_override"
    ROLE_HIJACK = "role_hijack"
    PERMISSION_ESCALATION = "permission_escalation"
    RULE_MODIFICATION = "rule_modification"
    CONTEXT_INJECTION = "context_injection"


class Severity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AuthStatus(Enum):
    """Authorization chain status."""
    AUTHORIZED = "authorized"
    UNAUTHORIZED = "unauthorized"
    PENDING = "pending"


class DetectionType(Enum):
    """Type of threat detected."""
    INSTRUCTION_TAMPERING = "instruction_tampering"
    DIALOGUE_FABRICATION = "dialogue_fabrication"
    MEMORY_POISONING = "memory_poisoning"
    TOOL_ABUSE = "tool_abuse"
    INTEGRITY_VIOLATION = "integrity_violation"


class ActionType(Enum):
    """Action taken in response to alert."""
    ALERT = "alert"
    HITL = "hitl"
    HALT = "halt"


class MessageType(Enum):
    """Agent message types."""
    REQUEST = "request"
    RESPONSE = "response"
    SYSTEM = "system"
    ALERT = "alert"
