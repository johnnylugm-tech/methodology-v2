"""Custom exceptions for Hunter Agent."""


class HunterError(Exception):
    """Base exception for Hunter Agent."""
    pass


class TamperingDetectionError(HunterError):
    """Raised when tampering detection fails."""
    pass


class IntegrityValidationError(HunterError):
    """Raised when integrity validation fails."""
    pass


class RuleComplianceError(HunterError):
    """Raised when rule compliance check fails."""
    pass


class AnomalyDetectionError(HunterError):
    """Raised when anomaly detection fails."""
    pass


class AuditLogError(HunterError):
    """Raised when audit logging fails."""
    pass
