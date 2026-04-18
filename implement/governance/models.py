"""Tiered Governance Data Models."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import (
    ApprovalStatus,
    AuthorizedRole,
    OperationScope,
    OperationType,
    RiskLevel,
    Tier,
)


# ─── Identity ─────────────────────────────────────────────────────────────────

@dataclass
class Identity:
    """Represents a human or system actor."""
    identity_id: str
    name: str
    email: Optional[str] = None
    role: Optional[AuthorizedRole] = None

    def __str__(self) -> str:
        return f"{self.name} ({self.identity_id})"


# ─── Operation Summary ────────────────────────────────────────────────────────

@dataclass
class OperationSummary:
    """Lightweight description of an operation for logging and display."""
    operation_id: str
    operation_type: OperationType
    description: str
    affected_systems: List[str] = field(default_factory=list)
    estimated_impact: Optional[str] = None


# ─── Override ─────────────────────────────────────────────────────────────────

@dataclass
class TierOverride:
    """Records a tier assignment override by an authorized role."""
    original_tier: Tier
    new_tier: Tier
    justification: str
    overridden_by: str          # actor_identity
    overridden_at: datetime
    role: AuthorizedRole


# ─── Tier Decision ───────────────────────────────────────────────────────────

@dataclass
class TierDecision:
    """
    Result of classifying an operation into a governance tier.

    Attributes:
        operation_id: Unique identifier for the operation.
        tier: The assigned oversight tier (HOTL, HITL, or HOOTL).
        classification_reason: Human-readable rationale for the classification.
        timestamp: When the classification was made.
        confidence: Classifier confidence score (0.0–1.0). Below 0.60 triggers
            auto-escalation to the next higher tier as a safety measure.
        overrides: Any tier overrides applied by authorized roles.
    """
    operation_id: str
    tier: Tier
    classification_reason: str
    timestamp: datetime
    confidence: float = 1.0
    overrides: List[TierOverride] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0–1.0, got {self.confidence}")


# ─── Governance Context ───────────────────────────────────────────────────────

@dataclass
class GovernanceContext:
    """
    Full context about an operation presented for tier classification.

    Attributes:
        operation_id: Unique identifier for the operation.
        operation_type: Category of operation (e.g., CODE_GENERATION, DATA_OPERATION).
        risk_level: Risk classification (ROUTINE, ELEVATED, CRITICAL).
        scope: Impact scope (SINGLE_AGENT, MULTI_AGENT, CROSS_WORKSPACE).
        requester_identity: Identity of the actor requesting the operation.
        historical_precedent: Prior classification decision for a similar operation.
        metadata: Arbitrary additional context (data_classification, affected_systems, etc.).
    """
    operation_id: str
    operation_type: OperationType
    risk_level: RiskLevel
    scope: OperationScope
    requester_identity: Identity
    historical_precedent: Optional[str] = None   # prior decision ID for lookback
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── Approval Request ──────────────────────────────────────────────────────────

@dataclass
class ApproverResponse:
    """Human approver's response to an HITL request."""
    decision: ApprovalStatus        # APPROVED, DENIED, MODIFIED, ESCALATED
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None   # for MODIFIED


@dataclass
class ApprovalRequest:
    """
    A pending HITL approval request queued for human review.

    Attributes:
        request_id: Unique identifier for this approval request.
        operation_id: The operation being approved.
        operation: Summary of the operation.
        requested_tier: The tier that was assigned (HITL).
        context: Full governance context for the approver.
        sla_deadline: UTC deadline for the approver to respond.
        status: Current status of the request.
        created_at: When the request was created.
        approver_identity: Identity of the responding approver (set on response).
        approver_response: The approver's decision and any modifications.
    """
    request_id: str
    operation_id: str
    operation: OperationSummary
    requested_tier: Tier
    context: GovernanceContext
    sla_deadline: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    approver_identity: Optional[Identity] = None
    approver_response: Optional[ApproverResponse] = None


# ─── Escalation Event ─────────────────────────────────────────────────────────

@dataclass
class EscalationEvent:
    """
    Records a tier transition event.

    Attributes:
        event_id: Unique identifier for this escalation.
        operation_id: The operation being escalated.
        from_tier: The tier before escalation.
        to_tier: The tier after escalation.
        trigger_reason: Why the escalation occurred.
        timestamp: When the escalation was triggered.
        acted_by: Identity or system component that triggered the escalation.
        escalated_to_channel: Whether the target tier's notification channel was reached.
        fallback_tier: If channel was unavailable, the next fallback tier used.
    """
    event_id: str
    operation_id: str
    from_tier: Tier
    to_tier: Tier
    trigger_reason: str
    timestamp: datetime
    acted_by: str                           # "system" or actor_identity
    escalated_to_channel: bool = True
    fallback_tier: Optional[Tier] = None


# ─── Audit Entry ─────────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """
    Immutable append-only record of a governance action.

    Attributes:
        entry_id: Monotonically increasing entry identifier.
        timestamp: When the event occurred.
        operation: Summary of the operation.
        tier: The tier active during this event.
        decision: Human-readable decision/description of the action.
        actor: Who or what performed the action (system or identity).
        outcome: The result of the action (success, failure, pending).
        metadata: Additional context (justification, overrides, etc.).
    """
    entry_id: str
    timestamp: datetime
    operation: OperationSummary
    tier: Tier
    decision: str
    actor: str
    outcome: str                            # success | failure | pending
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_id() -> str:
        """Generate a new unique entry ID."""
        return str(uuid.uuid4())


# ─── Supporting Models ────────────────────────────────────────────────────────

@dataclass
class GovernanceQueryFilters:
    """Filters for querying audit logs."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    tier: Optional[Tier] = None
    operation_type: Optional[OperationType] = None
    actor: Optional[str] = None
    outcome: Optional[str] = None
    operation_id: Optional[str] = None


@dataclass
class PaginationParams:
    """Pagination parameters for audit queries."""
    offset: int = 0
    limit: int = 100


@dataclass
class GovernanceHealthReport:
    """Weekly governance health metrics."""
    start_date: datetime
    end_date: datetime
    total_operations: int
    tier_distribution: Dict[Tier, int]
    escalation_count: int
    hitl_approval_rate: float
    mean_approval_time_hours: float
    report_generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IncidentReport:
    """Post-hoc HOOTL incident report."""
    operation_id: str
    event_id: str
    trigger_reason: str
    actions_taken: List[str]
    timeline: List[Dict[str, Any]]
    lessons_learned: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OverrideRecord:
    """Record of a tier override action."""
    operation_id: str
    original_tier: Tier
    new_tier: Tier
    justification: str
    actor_identity: str
    role: AuthorizedRole
    timestamp: datetime
    review_flagged: bool = False


@dataclass
class ReviewFlagStatus:
    """Status of review flagging for an actor."""
    actor_identity: str
    flagged: bool
    override_count: int
    last_override_at: Optional[datetime] = None


@dataclass
class OverrideResult:
    """Result of attempting a tier override."""
    success: bool
    message: str
    new_tier: Optional[Tier] = None
    review_flagged: bool = False
