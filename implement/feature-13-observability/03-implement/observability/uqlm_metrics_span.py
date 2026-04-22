"""UQLM metrics helpers for OpenTelemetry spans."""

from typing import Any, Optional


class UqlmMetricsSpan:
    """Attach UQLM metrics to an OTel span as attributes.

    Gracefully handles None span (no-op).
    """

    @staticmethod
    def _safe_setattr(span: Any, key: str, value: Any) -> None:
        """Set attribute only if the span supports it."""
        if span is None:
            return
        if hasattr(span, "set_attribute"):
            span.set_attribute(key, value)

    def attach_to_span(
        self,
        span: Any,
        uaf_score: float,
        decision: str,
        components: Optional[dict] = None,
        computation_time_ms: Optional[float] = None,
    ) -> None:
        """Write UQLM metrics as OTel span attributes.

        Args:
            span: OTel span (or None for no-op).
            uaf_score: Unified Quality / Fitness score (0–1).
            decision: Short decision label (e.g. "approve", "reject", "escalate").
            components: Optional dict of per-component scores.
            computation_time_ms: Optional elapsed time in milliseconds.
        """
        self._safe_setattr(span, "uqlm.uaf_score", uaf_score)
        self._safe_setattr(span, "uqlm.decision", decision)
        if components is not None:
            self._safe_setattr(span, "uqlm.components", components)
        if computation_time_ms is not None:
            self._safe_setattr(span, "uqlm.computation_time_ms", computation_time_ms)

    def create_span_with_uqlm(
        self,
        tracer: Any,
        name: str,
        uqlm_result: Any,
        parent_span: Optional[Any] = None,
    ) -> Any:
        """Create a child span and attach UQLM attributes from a result object.

        Args:
            tracer: OTel tracer (must have .start_span()).
            name: Span name.
            uqlm_result: Object with .score, .decision, .components,
                         and optionally .computation_time_ms attributes.
            parent_span: Optional parent span.

        Returns:
            The started span (caller should set status + end it).
        """
        if tracer is None:
            return None

        kwargs = {}
        if parent_span is not None:
            kwargs["parent"] = parent_span

        span = tracer.start_span(name, **kwargs)

        score = getattr(uqlm_result, "uaf_score", 0.0)
        decision = getattr(uqlm_result, "decision", "unknown")
        components = getattr(uqlm_result, "components", None)
        comp_time = getattr(uqlm_result, "computation_time_ms", None)

        self.attach_to_span(span, score, decision, components, comp_time)
        return span