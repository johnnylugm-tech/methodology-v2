"""
Tiered Governance — Feature #3 of methodology-v3.

Implements HOTL (Human On The Loop), HITL (Human In The Loop), and
HOOTL (Human Out Of The Loop) oversight tiers for agent operations.
"""

from .enums import (
    Tier,
    GovernanceDecision,
    ApprovalStatus,
    RiskLevel,
    AuthorizedRole,
    OperationType,
    OperationScope,
    LOW_CONFIDENCE_THRESHOLD,
    MAX_ESCALATION_DEPTH,
    DEFAULT_HITL_SLA_HOURS,
    HOOTL_ACTIVATION_TARGET_MS,
    CLASSIFICATION_LATENCY_P99_MS,
    TIER_ORDER,
)

from .models import (
    Identity,
    OperationSummary,
    TierOverride,
    TierDecision,
    GovernanceContext,
    ApprovalRequest,
    ApproverResponse,
    EscalationEvent,
    AuditEntry,
    GovernanceQueryFilters,
    PaginationParams,
    GovernanceHealthReport,
    IncidentReport,
    OverrideRecord,
    ReviewFlagStatus,
    OverrideResult,
)

from .exceptions import (
    GovernanceError,
    TierClassificationError,
    ApprovalClosedError,
    UnauthorizedOverrideError,
    EscalationDepthExceeded,
    AuditLogError,
    CircularEscalationError,
    InvalidTierTransitionError,
    SLAExpiredError,
)

from .tier_classifier import TierClassifier
from .governance_trigger import (
    GovernanceTrigger,
    TriggerResult,
    MonitoringResult,
    WorkflowHandle,
    EmergencyProtocolHandle,
    HITLQueueEntry,
)
from .escalation_engine import EscalationEngine, EscalationRecord
from .audit_logger import AuditLogger
from .override_manager import OverrideManager


__all__ = [
    # ── Enums ──────────────────────────────────────────────────────────────────
    "Tier",
    "GovernanceDecision",
    "ApprovalStatus",
    "RiskLevel",
    "AuthorizedRole",
    "OperationType",
    "OperationScope",
    "LOW_CONFIDENCE_THRESHOLD",
    "MAX_ESCALATION_DEPTH",
    "DEFAULT_HITL_SLA_HOURS",
    "HOOTL_ACTIVATION_TARGET_MS",
    "CLASSIFICATION_LATENCY_P99_MS",
    "TIER_ORDER",
    # ── Models ─────────────────────────────────────────────────────────────────
    "Identity",
    "OperationSummary",
    "TierOverride",
    "TierDecision",
    "GovernanceContext",
    "ApprovalRequest",
    "ApproverResponse",
    "EscalationEvent",
    "AuditEntry",
    "GovernanceQueryFilters",
    "PaginationParams",
    "GovernanceHealthReport",
    "IncidentReport",
    "OverrideRecord",
    "ReviewFlagStatus",
    "OverrideResult",
    # ── Exceptions ──────────────────────────────────────────────────────────────
    "GovernanceError",
    "TierClassificationError",
    "ApprovalClosedError",
    "UnauthorizedOverrideError",
    "EscalationDepthExceeded",
    "AuditLogError",
    "CircularEscalationError",
    "InvalidTierTransitionError",
    "SLAExpiredError",
    # ── Components ──────────────────────────────────────────────────────────────
    "TierClassifier",
    "GovernanceTrigger",
    "TriggerResult",
    "MonitoringResult",
    "WorkflowHandle",
    "EmergencyProtocolHandle",
    "HITLQueueEntry",
    "EscalationEngine",
    "EscalationRecord",
    "AuditLogger",
    "OverrideManager",
]
