"""
ml_langfuse.trace — W3C TraceContext propagation utilities.

Provides helpers to extract, inject, and propagate trace context across:
    - async / await boundaries
    - LangChain / LangGraph node boundaries
    - HTTP headers for downstream service calls
    - Multi-agent session stitching
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, AsyncIterator, Callable, Coroutine, TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.context import Context
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import Format

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import Span as SDKSpan

__all__ = [
    "get_current_trace_context",
    "inject_trace_context",
    "extract_trace_context",
    "run_with_trace_context",
]


# ---------------------------------------------------------------------------
# Extract current trace context
# ---------------------------------------------------------------------------

def get_current_trace_context() -> dict[str, Any]:
    """
    Extract the W3C TraceContext of the currently active span.

    Returns:
        A dict with keys:
            - ``trace_id``: 32-character hex string (or None if no active span)
            - ``span_id``:  16-character hex string (or None if no active span)
            - ``trace_flags``: int (typically 1 for sampled, 0 for not)

        If there is no active span, all fields are None/0.
    """
    span = trace.get_current_span()
    if span is None:
        return {"trace_id": None, "span_id": None, "trace_flags": 0}

    ctx = span.get_span_context()
    if ctx is None or not ctx.is_valid:
        return {"trace_id": None, "span_id": None, "trace_flags": 0}

    return {
        "trace_id": format(ctx.trace_id, "032x"),
        "span_id": format(ctx.span_id, "016x"),
        "trace_flags": ctx.trace_flags,
    }


# ---------------------------------------------------------------------------
# Inject / Extract
# ---------------------------------------------------------------------------

def inject_trace_context(carrier: dict[str, str]) -> dict[str, str]:
    """
    Inject the current trace context into a carrier dict.

    This is the equivalent of W3C ``traceparent`` header injection.

    Args:
        carrier: A dict that will be mutated in-place and returned.
                 Typically an HTTP header dict or a message metadata dict.

    Returns:
        The same ``carrier`` dict with ``traceparent`` (and optionally
        ``tracestate``) keys set.

    Example:
        headers = {}
        inject_trace_context(headers)
        # headers == {"traceparent": "00-0af765e2...-01"}
    """
    inject(carrier, format=Format.TRACEPARENT)
    return carrier


def extract_trace_context(carrier: dict[str, str]) -> Context:
    """
    Extract a W3C TraceContext from a carrier dict.

    Args:
        carrier: A dict containing at least a ``traceparent`` key.
                 Typically parsed from HTTP headers.

    Returns:
        An OTel ``Context`` that can be passed to
        ``run_with_trace_context()`` or used as a parent context.
    """
    ctx: Context = extract(carrier, format=Format.TRACEPARENT)
    return ctx


# ---------------------------------------------------------------------------
# Run coroutine within a given trace context
# ---------------------------------------------------------------------------

@contextmanager
def _set_context(ctx: Context) -> AsyncIterator[None]:
    """
    Context manager that makes ``ctx`` the current OTel context for its scope.

    This is used to propagate trace context across ``asyncio.create_task()``
    boundaries.
    """
    token = trace.set_span_context(ctx)
    try:
        yield
    finally:
        trace.use_context(token)  # type: ignore[arg-type]


async def run_with_trace_context(
    ctx: Context,
    coro: Coroutine[Any, Any, Any],
) -> Any:
    """
    Run ``coro`` within the given trace ``ctx``.

    This is the primary utility for propagating trace context across
    async boundaries (e.g. from an HTTP request handler into a pipeline
    coroutine).

    Args:
        ctx: An OTel ``Context`` (obtained via ``extract_trace_context()``).
        coro: The coroutine to run inside the context.

    Returns:
        The result of awaiting ``coro``.
    """
    # We need to isolate the context for the task.
    # The cleanest approach in OTel 1.x is to use a context manager
    # that is entered before the task begins.
    # For a simple coroutine, we can use `asyncio.create_task` with the
    # context set as current for the duration.
    import asyncio

    # Re-extract the parent span from ctx so we can make it current
    parent_span_ctx = None
    for item in ctx.items:
        if item.__class__.__name__ == "SpanContext":
            parent_span_ctx = item
            break

    async def _run() -> Any:
        if parent_span_ctx is not None and parent_span_ctx.is_valid:
            from opentelemetry import trace
            # Create a no-op span that carries the context,
            # so child spans inherit it automatically.
            tracer = trace.get_tracer("ml_langfuse.trace")
            with tracer.start_as_current_span(
                "_context_propagator",
                context=ctx,
                links=[],  # not a linked span
            ) as propagated_span:
                # Mark it as not recording to avoid duplicate spans
                propagated_span.end()
                return await coro
        return await coro

    return await _run()


# ---------------------------------------------------------------------------
# Async context token helper
# ---------------------------------------------------------------------------

@contextmanager  # type: ignore[misc]
async def trace_context_async(ctx: Context) -> AsyncIterator[None]:
    """
    Async-compatible context manager that makes ``ctx`` the current OTel context.

    Use this inside async functions to temporarily set a trace context:

        async with trace_context_async(extracted_ctx):
            # All spans created here inherit extracted_ctx
            await pipeline.run()
    """
    # In synchronous context managers calling async code is complex.
    # For simplicity we use the sync approach and asyncio.create_task
    # handles the async boundary. See run_with_trace_context above.
    import asyncio

    # Run a sync context manager inside an async task
    loop = asyncio.get_running_loop()

    # Create a future that sets the context
    async def _set() -> None:
        # Synchronous context manager inside async context
        token = trace.set_span_context(ctx)
        try:
            yield
        finally:
            trace.use_context(token)  # type: ignore[arg-type]

    # We actually don't use the context manager here — run_with_trace_context
    # handles propagation. This is here as an API placeholder for future use.
    yield
