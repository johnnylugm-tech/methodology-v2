"""Data models for Hunter Agent."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .enums import (
        MessageType, TamperPattern, Severity, AuthStatus,
        DetectionType, ActionType
    )


@dataclass
class AgentMessage:
    """Represents an agent-to-agent message."""
    agent_id: str
    conversation_id: str
    content: str
    timestamp: datetime
    message_type: "MessageType"


@dataclass
class TamperResult:
    """FR-H-1: Result of instruction tampering detection."""
    is_tampered: bool
    pattern_type: "TamperPattern"
    severity: "Severity"
    matched_tokens: List[str]
    evidence_hash: str


@dataclass
class FabricateResult:
    """FR-H-2: Result of dialogue fabrication detection."""
    is_fabricated: bool
    claim: str
    audit_reference: Optional[str]
    confidence: float


@dataclass
class PoisonResult:
    """FR-H-3: Result of memory poisoning detection."""
    is_poisoned: bool
    fact: "MemoryFact"
    auth_status: "AuthStatus"
    source: str
    timestamp: datetime


@dataclass
class AbuseResult:
    """FR-H-4: Result of tool abuse detection."""
    is_abused: bool
    tool_name: str
    whitelisted_tools: List[str]
    severity: "Severity"
    requested_permissions: List[str]


@dataclass
class IntegrityResult:
    """FR-H-5: Result of runtime integrity validation."""
    is_valid: bool
    source: str
    actual_hash: str
    expected_hash: str
    anomaly_score: float
    requires_hitl: bool


@dataclass
class HunterAlert:
    """Unified alert dataclass produced by HunterAgent."""
    alert_id: str
    detection_type: "DetectionType"
    severity: "Severity"
    agent_id: str
    evidence: Dict[str, Any]
    timestamp: datetime
    action_taken: "ActionType"


@dataclass
class MemoryFact:
    """Represents a fact stored in agent memory."""
    fact_id: str
    content: str
    source_agent: str
    created_at: datetime


@dataclass
class AuthorizationChain:
    """Authorization chain for memory operations."""
    authorized_by: str
    authorized_at: datetime
    auth_token: Optional[str] = None


@dataclass
class ToolCall:
    """Represents a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    called_at: datetime
    caller_agent: str
