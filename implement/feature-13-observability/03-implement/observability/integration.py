"""Observability integration: wire together UQLM metrics, decision log, and effort tracker."""

from .uqlm_metrics_span import UqlmMetricsSpan
from .decision_log import DecisionLogWriter
from .effort_metrics import EffortTracker


def setup_observability(tracer=None):
    """Set up all observability components.

    Args:
        tracer: Optional OTel tracer for UQLM span helpers.

    Returns:
        (UqlmMetricsSpan, DecisionLogWriter, EffortTracker) tuple.
    """
    uqlm = UqlmMetricsSpan()
    decision_log = DecisionLogWriter()
    effort = EffortTracker()
    return uqlm, decision_log, effort