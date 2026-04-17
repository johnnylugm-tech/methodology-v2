"""Tiered Governance Enums and Constants."""

from enum import Enum, auto


class Tier(Enum):
    """Three-tier human oversight classification."""
    HOTL = auto()   # Human On The Loop — passive monitoring, automated execution
    HITL = auto()   # Human In The Loop — requires explicit approval
    HOOTL = auto()  # Human Out Of The Loop — emergency protocols, act first


class GovernanceDecision(Enum):
    """Possible governance decisions for an operation."""
    AUTO_APPROVE = auto()         # HOTL: proceed automatically
    PENDING_APPROVAL = auto()     # HITL: queue for human approval
    BLOCK = auto()                # Denied / blocked
    ESCALATE = auto()             # Escalate to higher tier
    EMERGENCY_TRIGGER = auto()     # HOOTL: emergency protocol activated


class ApprovalStatus(Enum):
    """Status of an HITL approval request."""
    PENDING = auto()
    APPROVED = auto()
    DENIED = auto()
    MODIFIED = auto()             # Approved with modifications
    ESCALATED = auto()             # Escalated to HOOTL
    TIMEOUT = auto()              # SLA exceeded, auto-handled


class RiskLevel(Enum):
    """Risk classification for an operation."""
    ROUTINE = auto()      # Standard operation, minimal risk
    ELEVATED = auto()     # Above-normal risk, requires attention
    CRITICAL = auto()     # Existential or irreversible risk


class AuthorizedRole(Enum):
    """Roles authorized to perform governance actions."""
    ADMIN = auto()
    SECURITY_ADMIN = auto()
    COMPLIANCE_OFFICER = auto()
    OPERATOR = auto()


class OperationType(Enum):
    """Categories of agent operations."""
    CODE_GENERATION = auto()
    REFACTORING = auto()
    AUTOMATED_TESTING = auto()
    CONFIGURATION = auto()
    DATA_OPERATION = auto()
    MULTI_AGENT_COORDINATION = auto()
    SECURITY = auto()
    COMPLIANCE = auto()
    SYSTEM_HEALTH = auto()
    AGENT_LIFECYCLE = auto()
    CONSTITUTION_MODIFICATION = auto()
    EMERGENCY = auto()
    UNKNOWN = auto()


class OperationScope(Enum):
    """Scope of an operation's impact."""
    SINGLE_AGENT = auto()
    MULTI_AGENT = auto()
    CROSS_WORKSPACE = auto()


# ─── Constants ────────────────────────────────────────────────────────────────

# Confidence threshold below which we default to higher (safer) tier
LOW_CONFIDENCE_THRESHOLD = 0.60

# Maximum escalation depth per operation
MAX_ESCALATION_DEPTH = 3

# Default HITL SLA in hours
DEFAULT_HITL_SLA_HOURS = 24

# HOOTL activation target in milliseconds
HOOTL_ACTIVATION_TARGET_MS = 100

# Classification latency target in milliseconds (p99)
CLASSIFICATION_LATENCY_P99_MS = 10

# Tier ordering for escalation comparisons (lowest → highest)
TIER_ORDER = {
    Tier.HOTL: 0,
    Tier.HITL: 1,
    Tier.HOOTL: 2,
}
