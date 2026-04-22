"""Tests for ml_langfuse.trace — TraceContext propagation utilities."""

from __future__ import annotations

import pytest

from opentelemetry.context import Context

from ml_langfuse.trace import (
    get_current_trace_context,
    inject_trace_context,
    extract_trace_context,
    run_with_trace_context,
)


class TestGetCurrentTraceContext:
    """Tests for get_current_trace_context()."""

    def test_no_active_span_returns_none_fields(self):
        """When no span is active, trace_id and span_id should be None."""
        ctx = get_current_trace_context()
        assert ctx["trace_id"] is None
        assert ctx["span_id"] is None
        assert ctx["trace_flags"] == 0

    def test_with_active_span_returns_valid_context(self):
        """When a span is active, context fields should be valid hex strings."""
        from opentelemetry import trace
        from ml_langfuse.client import get_langfuse_client
        import os

        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        client = get_langfuse_client()
        tracer = client.get_tracer("test.trace")

        with tracer.start_as_current_span("test_parent") as span:
            ctx = get_current_trace_context()
            assert ctx["trace_id"] is not None
            assert len(ctx["trace_id"]) == 32
            assert ctx["span_id"] is not None
            assert len(ctx["span_id"]) == 16
            assert isinstance(ctx["trace_flags"], int)


class TestInjectExtractTraceContext:
    """Tests for inject/extract trace context."""

    def test_inject_produces_traceparent_header(self):
        """inject_trace_context should produce a traceparent dict entry."""
        from opentelemetry import trace
        import os

        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        client = get_langfuse_client()
        tracer = client.get_tracer("test.inject")

        with tracer.start_as_current_span("test_span") as _:
            carrier = {}
            inject_trace_context(carrier)
            assert "traceparent" in carrier
            # Format: 00-{32hex}-{16hex}-{2hex}
            parts = carrier["traceparent"].split("-")
            assert len(parts) == 4
            assert parts[0] == "00"
            assert len(parts[1]) == 32
            assert len(parts[2]) == 16
            assert len(parts[3]) == 2

    def test_extract_trace_context_from_carrier(self):
        """extract_trace_context should return a valid OTel Context."""
        carrier = {
            "traceparent": "00-0af765e2cd75ef2d70dc673f96d12085-a21d4b1edb19f7a0-01"
        }
        ctx = extract_trace_context(carrier)
        assert isinstance(ctx, Context)

    def test_roundtrip_inject_extract(self):
        """Context should survive inject → extract roundtrip."""
        from opentelemetry import trace
        import os

        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        client = get_langfuse_client()
        tracer = client.get_tracer("test.roundtrip")

        with tracer.start_as_current_span("test_span") as _:
            carrier = {}
            inject_trace_context(carrier)
            extracted = extract_trace_context(carrier)
            assert isinstance(extracted, Context)


class TestRunWithTraceContext:
    """Tests for run_with_trace_context()."""

    @pytest.mark.asyncio
    async test_run_with_trace_context_executes_coro(self):
        """run_with_trace_context should execute the coroutine normally."""
        carrier = {
            "traceparent": "00-0af765e2cd75ef2d70dc673f96d12085-a21d4b1edb19f7a0-01"
        }
        ctx = extract_trace_context(carrier)

        async def dummy_coro() -> str:
            return "ok"

        result = await run_with_trace_context(ctx, dummy_coro())
        assert result == "ok"
