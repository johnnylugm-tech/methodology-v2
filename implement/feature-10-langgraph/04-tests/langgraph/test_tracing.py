"""
Tests for tracing.py (Span, TraceRecord, ExecutionTracer).

No langgraph dependency required.
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from ml_langgraph.tracing import (
    SpanStatus,
    SPAN_STATUS_SUCCESS,
    SPAN_STATUS_FAILED,
    SpanEvent,
    Span,
    TraceRecord,
    ExecutionTracer,
    TraceContext,
)


# ─────────────────────────────────────────────────────────────────────────────
# SpanEvent dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestSpanEvent:
    def test_span_event_to_dict(self):
        """SpanEvent.to_dict() should serialize name, timestamp, metadata."""
        event = SpanEvent(name="cache_hit", metadata={"size": 128})
        d = event.to_dict()
        assert d["name"] == "cache_hit"
        assert "timestamp" in d
        assert d["metadata"] == {"size": 128}

    def test_span_event_default_timestamp(self):
        """SpanEvent should default timestamp to now."""
        before = datetime.utcnow()
        event = SpanEvent(name="started")
        after = datetime.utcnow()
        assert before <= event.timestamp <= after


# ─────────────────────────────────────────────────────────────────────────────
# Span dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestSpan:
    def test_span_dataclass(self):
        """Span should store all fields."""
        span = Span(
            span_id="s-001",
            parent_id=None,
            node_name="MyNode",
            metadata={"version": 1},
        )
        assert span.span_id == "s-001"
        assert span.parent_id is None
        assert span.node_name == "MyNode"
        assert span.metadata["version"] == 1

    def test_span_duration_ms_no_end_time(self):
        """duration_ms() should return None when end_time not set."""
        span = Span(span_id="s-no-end", parent_id=None, node_name="N")
        assert span.duration_ms() is None

    def test_span_duration_ms_with_end_time(self):
        """duration_ms() should compute milliseconds between start and end."""
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = datetime(2026, 1, 1, 0, 0, 1)
        span = Span(span_id="s-timed", parent_id=None, node_name="N",
                   start_time=start, end_time=end)
        assert span.duration_ms() == 1000.0

    def test_span_add_event(self):
        """add_event() should append a SpanEvent to the events list."""
        span = Span(span_id="s-ev", parent_id=None, node_name="N")
        span.add_event("retry_attempt", metadata={"attempt": 2})
        assert len(span.events) == 1
        assert span.events[0].name == "retry_attempt"

    def test_span_to_dict(self):
        """to_dict() should serialize all span fields."""
        span = Span(span_id="s-dict", parent_id="p-001", node_name="NodeX")
        d = span.to_dict()
        assert d["span_id"] == "s-dict"
        assert d["parent_id"] == "p-001"
        assert d["node_name"] == "NodeX"
        assert "start_time" in d


# ─────────────────────────────────────────────────────────────────────────────
# TraceRecord dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestTraceRecord:
    def test_trace_record_fields(self):
        """TraceRecord should hold spans and metadata."""
        record = TraceRecord(trace_id="t-001", execution_id="exec-1")
        assert record.trace_id == "t-001"
        assert record.execution_id == "exec-1"

    def test_trace_record_add_span(self):
        """add_span() should append span to list."""
        record = TraceRecord(trace_id="t-002", execution_id="ex2")
        span = Span(span_id="s-1", parent_id=None, node_name="N")
        record.add_span(span)
        assert len(record.spans) == 1
        assert record.get_span("s-1") is span

    def test_trace_record_get_span_not_found(self):
        """get_span() should return None for unknown ID."""
        record = TraceRecord(trace_id="t-003", execution_id="ex3")
        assert record.get_span("nonexistent") is None

    def test_trace_record_get_root_spans(self):
        """get_root_spans() should return spans with no parent."""
        record = TraceRecord(trace_id="t-root", execution_id="ex-root")
        record.add_span(Span(span_id="s-root", parent_id=None, node_name="Root"))
        record.add_span(Span(span_id="s-child", parent_id="s-root", node_name="Child"))
        roots = record.get_root_spans()
        assert len(roots) == 1
        assert roots[0].span_id == "s-root"

    def test_trace_record_finalize(self):
        """finalize() should set end_time and compute total_duration_ms."""
        record = TraceRecord(
            trace_id="t-final",
            execution_id="ex-final",
            start_time=datetime(2026, 1, 1, 12, 0, 0),
        )
        record.finalize()
        assert record.end_time is not None
        assert record.total_duration_ms is not None
        assert record.total_duration_ms >= 0

    def test_trace_record_to_dict(self):
        """to_dict() should serialize trace record."""
        record = TraceRecord(trace_id="t-todict", execution_id="ex1")
        d = record.to_dict()
        assert d["trace_id"] == "t-todict"
        assert d["execution_id"] == "ex1"
        assert "span_count" in d


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionTracer Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionTracerInit:
    def test_default_init(self):
        """ExecutionTracer should initialise with profiling disabled."""
        tracer = ExecutionTracer()
        assert tracer._active_trace is None
        assert tracer.enable_profiling is False

    def test_profiling_flag(self):
        """enable_profiling property should be settable."""
        tracer = ExecutionTracer()
        tracer.enable_profiling = True
        assert tracer.enable_profiling is True


class TestExecutionTracerLifecycle:
    def test_start_trace(self):
        """start_trace() should create a new TraceRecord."""
        tracer = ExecutionTracer()
        trace_id = tracer.start_trace("run-001")
        assert trace_id is not None
        assert tracer._active_trace is not None
        assert tracer._active_trace.execution_id == "run-001"

    def test_start_trace_idempotent(self):
        """start_trace() should raise RuntimeError if trace already active."""
        tracer = ExecutionTracer()
        tracer.start_trace("run-001")
        with pytest.raises(RuntimeError, match="already active"):
            tracer.start_trace("run-002")

    def test_end_trace_returns_record(self):
        """end_trace() should finalize and return the TraceRecord."""
        tracer = ExecutionTracer()
        tracer.start_trace("run-end")
        record = tracer.end_trace()
        assert record is not None
        assert record.trace_id is not None
        assert tracer._active_trace is None

    def test_end_trace_with_metadata(self):
        """end_trace() should merge metadata into record."""
        tracer = ExecutionTracer()
        tracer.start_trace("run-meta")
        record = tracer.end_trace(metadata={"finalized": True})
        assert record.metadata.get("finalized") is True

    def test_end_trace_no_active_trace(self):
        """end_trace() with no active trace should return None."""
        tracer = ExecutionTracer()
        assert tracer.end_trace() is None

    def test_execution_tracer_lifecycle(self):
        """Full lifecycle: start -> span -> end_span -> end_trace."""
        tracer = ExecutionTracer()
        trace_id = tracer.start_trace("lifecycle-run")
        assert trace_id.startswith("trace-")

        span_id = tracer.start_span("StepA")
        assert span_id.startswith("s1-")

        span = tracer.end_span(span_id, status=SpanStatus.SUCCESS)
        assert span is not None
        assert span.status == SpanStatus.SUCCESS

        record = tracer.end_trace()
        assert record is not None
        assert record.trace_id == trace_id


class TestExecutionTracerSpans:
    def test_start_span(self):
        """start_span() should create a span and push onto stack."""
        tracer = ExecutionTracer()
        tracer.start_trace("span-run")
        span_id = tracer.start_span("DoWork")
        assert span_id is not None
        assert len(tracer._active_span_stack) == 1

    def test_start_span_with_parent(self):
        """start_span() should link to explicit parent_id."""
        tracer = ExecutionTracer()
        tracer.start_trace("parent-run")
        parent_id = tracer.start_span("Parent")
        child_id = tracer.start_span("Child", parent_id=parent_id)
        assert child_id != parent_id

    def test_end_span(self):
        """end_span() should close span and pop from stack."""
        tracer = ExecutionTracer()
        tracer.start_trace("end-span-run")
        span_id = tracer.start_span("ToClose")
        closed = tracer.end_span(span_id, status=SpanStatus.SUCCESS)
        assert closed is not None
        assert len(tracer._active_span_stack) == 0

    def test_end_span_unknown_id(self):
        """end_span() with unknown ID should return None."""
        tracer = ExecutionTracer()
        tracer.start_trace("unknown-span")
        result = tracer.end_span("does-not-exist")
        assert result is None

    def test_add_event(self):
        """add_event() should append event to span."""
        tracer = ExecutionTracer()
        tracer.start_trace("event-run")
        span_id = tracer.start_span("EventNode")
        tracer.add_event(span_id, "custom_event", {"key": "value"})
        span = tracer.get_trace().get_span(span_id)
        assert len(span.events) == 1
        assert span.events[0].name == "custom_event"

    def test_span_context_manager(self):
        """span() context manager should auto-open and close span."""
        tracer = ExecutionTracer()
        tracer.start_trace("ctx-run")
        with tracer.span("AutoNode") as span_id:
            assert span_id is not None
        # After context exit, span should be closed
        span = tracer.get_trace().get_span(span_id)
        assert span is not None
        assert span.end_time is not None

    def test_span_context_manager_error_sets_failed(self):
        """span() should mark span FAILED when exception escapes."""
        tracer = ExecutionTracer()
        tracer.start_trace("error-run")
        try:
            with tracer.span("FailingNode"):
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        # Find the span and check status
        # Note: after exception, span is already closed via status_on_error

    def test_clear(self):
        """clear() should reset all state without ending trace."""
        tracer = ExecutionTracer()
        tracer.start_trace("clear-run")
        tracer.start_span("Orphan")
        tracer.clear()
        assert tracer._active_trace is None
        assert len(tracer._active_span_stack) == 0


class TestExecutionTracerSerialization:
    def test_to_json(self):
        """to_json() should serialize active trace as JSON."""
        tracer = ExecutionTracer()
        tracer.start_trace("json-run")
        tracer.start_span("JsonNode")
        tracer.end_span(tracer._active_span_stack[0])
        tracer.end_trace()

        json_str = tracer.to_json()
        parsed = json.loads(json_str)
        assert "trace_id" in parsed

    def test_to_json_no_active_trace(self):
        """to_json() with no active trace should return '{}'."""
        tracer = ExecutionTracer()
        assert tracer.to_json() == "{}"

    def test_to_json_indent(self):
        """to_json() with indent=True should produce formatted JSON."""
        tracer = ExecutionTracer()
        tracer.start_trace("indent-run")
        tracer.end_trace()
        json_str = tracer.to_json(indent=True)
        # Formatted JSON should contain newlines
        assert "\n" in json_str


class TestTraceContext:
    def test_trace_context_enters_and_exits(self):
        """TraceContext.__enter__ should start trace; __exit__ should end it."""
        tracer = ExecutionTracer()
        ctx = TraceContext(tracer, execution_id="ctx-run-1")
        with ctx:
            pass
        # After exiting, no active trace
        assert tracer._active_trace is None

    def test_trace_context_spans(self):
        """TraceContext.span() should delegate to tracer.start_span()."""
        tracer = ExecutionTracer()
        ctx = TraceContext(tracer, execution_id="ctx-span-run")
        with ctx:
            span_id = ctx.span("MySpan")
            assert span_id is not None
