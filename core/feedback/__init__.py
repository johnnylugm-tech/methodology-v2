"""
Feedback Loop Core Module.

Exports:
    - StandardFeedback
    - FEEDBACK_SOURCES
    - calculate_severity
    - FeedbackStore
    - route_and_assign
    - get_pending_by_sla
    - verify_and_close
    - get_metrics
"""

from .sources_schema import FEEDBACK_SOURCES, FeedbackSource
from .feedback import (
    StandardFeedback,
    FeedbackStore,
    FeedbackCreate,
    FeedbackUpdate,
)
from .severity import (
    SEVERITY_MATRIX,
    SeverityMatrix,
    calculate_severity,
)
from .router import (
    SLA_CONFIG,
    ROUTING_RULES,
    SLAConfig,
    RoutingRule,
    route_and_assign,
    get_pending_by_sla,
)
from .closure import (
    VerificationResult,
    ClosureResult,
    verify_and_close,
    reopen_feedback,
    get_metrics,
)

__all__ = [
    # sources_schema
    "FEEDBACK_SOURCES",
    "FeedbackSource",
    # feedback
    "StandardFeedback",
    "FeedbackStore",
    "FeedbackCreate",
    "FeedbackUpdate",
    # severity
    "SEVERITY_MATRIX",
    "SeverityMatrix",
    "calculate_severity",
    # router
    "SLA_CONFIG",
    "ROUTING_RULES",
    "SLAConfig",
    "RoutingRule",
    "route_and_assign",
    "get_pending_by_sla",
    # closure
    "VerificationResult",
    "ClosureResult",
    "verify_and_close",
    "reopen_feedback",
    "get_metrics",
]