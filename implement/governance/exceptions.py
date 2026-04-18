"""Tiered Governance Custom Exceptions."""


class GovernanceError(Exception):
    """Base exception for all governance-related errors."""
    pass


class TierClassificationError(GovernanceError):
    """Raised when tier classification fails or produces invalid results."""
    pass


class ApprovalClosedError(GovernanceError):
    """Raised when attempting to respond to an already-closed approval request."""
    pass


class UnauthorizedOverrideError(GovernanceError):
    """Raised when an unauthorized role attempts a tier override."""
    pass


class EscalationDepthExceeded(GovernanceError):
    """Raised when an operation exceeds the maximum allowed escalation depth."""
    pass


class AuditLogError(GovernanceError):
    """Raised when an audit logging operation fails."""
    pass


class CircularEscalationError(GovernanceError):
    """Raised when a circular escalation pattern is detected."""
    pass


class InvalidTierTransitionError(GovernanceError):
    """Raised when an invalid tier transition is attempted."""
    pass


class SLAExpiredError(GovernanceError):
    """Raised when an HITL SLA deadline has passed without response."""
    pass
