"""Tests for UqlmMetricsSpan (no real OTel SDK — uses FakeSpan/FakeTracer)."""

import pytest
from observability.uqlm_metrics_span import UqlmMetricsSpan


class FakeSpan:
    """Minimal span mock that stores attributes in a dict."""

    def __init__(self):
        self.attrs = {}

    def set_attribute(self, key, value):
        self.attrs[key] = value


class FakeTracer:
    """Minimal tracer mock that creates FakeSpan instances."""

    def start_span(self, name, parent=None, **kwargs):
        return FakeSpan()


class FakeResult:
    """Result-like object with uqlm fields."""

    def __init__(self, uaf_score, decision, components, computation_time_ms):
        self.uaf_score = uaf_score
        self.decision = decision
        self.components = components
        self.computation_time_ms = computation_time_ms


# ------------------------------------------------------------------
# attach_to_span
# ------------------------------------------------------------------

def test_attach_to_span_writes_all_attributes():
    span = FakeSpan()
    UqlmMetricsSpan().attach_to_span(
        span,
        uaf_score=0.82,
        decision="proceed",
        components={"uqlm": 0.8, "clap": 0.6},
        computation_time_ms=12.5,
    )
    assert span.attrs["uqlm.uaf_score"] == 0.82
    assert span.attrs["uqlm.decision"] == "proceed"
    assert span.attrs["uqlm.components"] == {"uqlm": 0.8, "clap": 0.6}
    assert span.attrs["uqlm.computation_time_ms"] == 12.5


def test_attach_to_span_none_span_noop():
    """Attaching to a None span must not raise."""
    UqlmMetricsSpan().attach_to_span(None, 0.5, "review", None, None)


def test_attach_to_span_minimal():
    """Only required fields — optional fields must not be set."""
    span = FakeSpan()
    UqlmMetricsSpan().attach_to_span(span, uaf_score=0.5, decision="block")
    assert span.attrs["uqlm.uaf_score"] == 0.5
    assert span.attrs["uqlm.decision"] == "block"
    assert "uqlm.components" not in span.attrs
    assert "uqlm.computation_time_ms" not in span.attrs


# ------------------------------------------------------------------
# create_span_with_uqlm
# ------------------------------------------------------------------

def test_create_span_with_uqlm():
    tracer = FakeTracer()
    result = FakeResult(
        uaf_score=0.75,
        decision="review",
        components={"total": 0.75},
        computation_time_ms=8.0,
    )
    span = UqlmMetricsSpan().create_span_with_uqlm(tracer, "test-span", result)
    assert isinstance(span, FakeSpan)
    assert span.attrs["uqlm.uaf_score"] == 0.75
    assert span.attrs["uqlm.decision"] == "review"
    assert span.attrs["uqlm.components"] == {"total": 0.75}
    assert span.attrs["uqlm.computation_time_ms"] == 8.0


def test_create_span_with_uqlm_null_tracer():
    """Null tracer returns None without raising."""
    span = UqlmMetricsSpan().create_span_with_uqlm(None, "span-name", FakeResult(0.5, "x", None, None))
    assert span is None
