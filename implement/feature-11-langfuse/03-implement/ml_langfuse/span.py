"""
ml_langfuse.span — OTel span creation utilities with all 7 required attributes.

All AI decision points in methodology-v2 Phase 6/7 must emit spans containing
these 7 required attributes:
    1. uaf_score          : float  (0.0 – 1.0)
    2. clap_flag          : bool
    3. risk_score         : float  (0.0 – 1.0)
    4. hitl_gate          : str    ("pass" | "review" | "block")
    5. human_decision     : str | None
    6. decided_by         : str    ("agent" | "human" | "system")
    7. compliance_tags    : list[str]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import Tracer

__all__ = ["create_decision_span", "end_span_with_status"]

# ---------------------------------------------------------------------------
# Valid value constants
# ---------------------------------------------------------------------------

VALID_HITL_GATES = ("pass", "review", "block")
VALID_DECIDED_BY = ("agent", "human", "system")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_hitl_gate(value: str) -> None:
    if value not in VALID_HITL_GATES:
        raise ValueError(
            f"hitl_gate must be one of {VALID_HITL_GATES!r}, got {value!r}"
        )


def _validate_decided_by(value: str) -> None:
    if value not in VALID_DECIDED_BY:
        raise ValueError(
            f"decided_by must be one of {VALID_DECIDED_BY!r}, got {value!r}"
        )


def _validate_score(name: str, value: float) -> None:
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a float, got {type(value).__name__}")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0.0, 1.0], got {value}")


# ---------------------------------------------------------------------------
# Core span creation
# ---------------------------------------------------------------------------

def create_decision_span(
    name: str,
    uaf_score: float,
    clap_flag: bool,
    risk_score: float,
    hitl_gate: str,
    human_decision: Optional[str],
    decided_by: str,
    compliance_tags: list[str],
    parent_span: Optional[Span] = None,
    tracer: Optional["Tracer"] = None,
    attributes: Optional[dict[str, object]] = None,
) -> Span:
    """
    Create and start an OTel span with all 7 required decision attributes.

    This is the primary entry point for span creation in methodology-v2
    decision points.

    Args:
        name:
            Span name following ``{phase}.{node_name}`` convention.
            Examples: ``"phase6.risk_evaluation"``, ``"phase7.hitl_gate"``.
        uaf_score:
            User Authorization Factor score, range ``[0.0, 1.0]``.
        clap_flag:
            Content Legitimacy Assessment Protocol result (``True`` = content
            passed CLAP review, ``False`` = content flagged).
        risk_score:
            Aggregated risk score, range ``[0.0, 1.0]``.
        hitl_gate:
            HITL gate status. Must be one of ``"pass"``, ``"review"``,
            ``"block"``.
        human_decision:
            Human override decision string if applicable, otherwise ``None``.
            Common values: ``"approved"``, ``"rejected"``, ``"escalate"``.
        decided_by:
            Decision authority. Must be one of ``"agent"``, ``"human"``,
            ``"system"``.
        compliance_tags:
            List of compliance tag strings applicable to this span.
            Examples: ``["GDPR Art.22"]``, ``["SOX", "HIPAA"]``.
        parent_span:
            Optional parent span for hierarchical tracing.
            If provided, the new span is created as a child of parent_span.
        tracer:
            Optional OTel Tracer to use. If not provided, the global
            TracerProvider is used.
        attributes:
            Optional dict of additional OTel attributes to set on the span.
            These are merged with (and override) the standard attributes.

    Returns:
        The started ``Span`` object. The caller is responsible for calling
        ``span.end()`` when the operation completes.

    Raises:
        ValueError: If any of the 7 required fields fail validation.
        TypeError: If field types are incorrect.

    Example:
        span = create_decision_span(
            name="phase7.hitl_gate",
            uaf_score=0.85,
            clap_flag=True,
            risk_score=0.32,
            hitl_gate="review",
            human_decision=None,
            decided_by="agent",
            compliance_tags=["GDPR Art.22"],
        )
        # ... do work ...
        end_span_with_status(span, StatusCode.OK)
    """
    # ── Validate all 7 required fields ──────────────────────────────────
    _validate_score("uaf_score", uaf_score)
    _validate_score("risk_score", risk_score)
    _validate_hitl_gate(hitl_gate)
    _validate_decided_by(decided_by)

    if not isinstance(clap_flag, bool):
        raise TypeError(f"clap_flag must be bool, got {type(clap_flag).__name__}")
    if not isinstance(compliance_tags, list):
        raise TypeError(
            f"compliance_tags must be list[str], got {type(compliance_tags).__name__}"
        )
    if not all(isinstance(t, str) for t in compliance_tags):
        raise TypeError("compliance_tags must contain only str elements")
    if human_decision is not None and not isinstance(human_decision, str):
        raise TypeError(
            f"human_decision must be str or None, got {type(human_decision).__name__}"
        )

    # ── Select tracer ───────────────────────────────────────────────────
    if tracer is None:
        tracer = trace.get_tracer("ml_langfuse.span")

    # ── Build attributes dict ───────────────────────────────────────────
    span_attrs: dict[str, object] = {
        "ml_langfuse.uaf_score": uaf_score,
        "ml_langfuse.clap_flag": clap_flag,
        "ml_langfuse.risk_score": risk_score,
        "ml_langfuse.hitl_gate": hitl_gate,
        "ml_langfuse.human_decision": human_decision,
        "ml_langfuse.decided_by": decided_by,
        "ml_langfuse.compliance_tags": compliance_tags,
    }

    # Merge additional attributes (additional attrs can override standard ones)
    if attributes:
        span_attrs.update(attributes)

    # ── Create span ──────────────────────────────────────────────────────
    if parent_span is not None:
        # Use parent context
        ctx = trace.set_span_in_context(parent_span)
        span: Span = tracer.start_span(name, context=ctx, attributes=span_attrs)
    else:
        span = tracer.start_span(name, attributes=span_attrs)

    return span


# ---------------------------------------------------------------------------
# Span status helpers
# ---------------------------------------------------------------------------

def end_span_with_status(
    span: Span,
    status: StatusCode,
    exception: Optional[Exception] = None,
) -> None:
    """
    End an OTel span with appropriate status and optional exception recording.

    Args:
        span: The span to end (must not already be ended).
        status: ``StatusCode.OK`` or ``StatusCode.ERROR``.
        exception: Optional exception to record as a span event.
                   If ``status`` is ``ERROR`` and no exception is provided,
                   a generic ``RuntimeError("Span ended with ERROR")`` is recorded.
    """
    if status == StatusCode.ERROR:
        span.set_status(status)
        if exception is not None:
            span.record_exception(exception)
        else:
            # Record a generic error to ensure ERROR status is meaningful
            span.record_exception(RuntimeError("Span ended with ERROR status"))
    else:
        span.set_status(status)
        span.end()


def end_span_ok(span: Span) -> None:
    """Convenience: end a span with StatusCode.OK."""
    end_span_with_status(span, StatusCode.OK)


def end_span_error(span: Span, exception: Optional[Exception] = None) -> None:
    """Convenience: end a span with StatusCode.ERROR."""
    end_span_with_status(span, StatusCode.ERROR, exception)
