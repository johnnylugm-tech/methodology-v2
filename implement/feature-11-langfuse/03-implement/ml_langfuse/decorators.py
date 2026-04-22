"""
ml_langfuse.decorators — Zero-boilerplate auto-instrumentation decorators.

Provides four decorators:
    @observe_llm_call      — wraps LLM invocations
    @observe_decision_point / @observe_decision_point_async  — decision nodes
    @observe_tool_call     — tool / function calls
    @observe_span          — generic span wrapper

Each decorator:
    1. Acquires the global Tracer
    2. Opens an OTel span
    3. Sets decorator-specific attributes
    4. Calls the wrapped function
    5. Returns / yields normally (span remains open for caller to end)
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Coroutine, Optional, TypeVar, overload

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from ml_langfuse.client import get_langfuse_client
from ml_langfuse.span import create_decision_span, end_span_with_status

__all__ = [
    "observe_llm_call",
    "observe_decision_point",
    "observe_decision_point_async",
    "observe_tool_call",
    "observe_span",
]

logger = logging.getLogger("ml_langfuse")


F = TypeVar("F", bound=Callable[..., Any])
AF = TypeVar("AF", bound=Callable[..., Coroutine[Any, Any, Any]])


# ---------------------------------------------------------------------------
# Base helpers
# ---------------------------------------------------------------------------

def _get_tracer() -> trace.Tracer:
    """Return the global ML Langfuse tracer."""
    try:
        client = get_langfuse_client()
        return client.get_tracer("ml_langfuse.decorators")
    except Exception as exc:
        logger.warning("Could not acquire Langfuse client: %s. Using no-op tracer.", exc)
        return trace.get_tracer("ml_langfuse.noop")


# ---------------------------------------------------------------------------
# @observe_llm_call
# ---------------------------------------------------------------------------

def observe_llm_call(
    model_name: str,
    model_version: Optional[str] = None,
) -> Callable[[F], F]:
    """
    Decorator that wraps an LLM call and auto-captures tracing attributes.

    Creates a span named ``llm.{model_name}`` with the following attributes:
        - ``llm.model``
        - ``llm.model_version`` (if provided)
        - ``llm.latency_ms`` (set on span end)
        - ``ml_langfuse.decided_by`` = ``"agent"``

    The decorator does NOT set the 7 required decision fields — use
    ``@observe_decision_point`` for decision nodes.

    Args:
        model_name: The LLM model identifier (e.g. ``"claude-3-opus"``).
        model_version: Optional version string (e.g. ``"2024-06"``).

    Example:
        @observe_llm_call(model_name="claude-3-opus", model_version="2024-06")
        async def claude_completion(prompt: str) -> str:
            return await llm.acall(prompt)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"llm.{model_name}"
            t0 = time.perf_counter()
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("llm.model", model_name)
                if model_version:
                    span.set_attribute("llm.model_version", model_version)
                span.set_attribute("ml_langfuse.decided_by", "agent")
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("llm.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_attribute("llm.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"llm.{model_name}"
            t0 = time.perf_counter()
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("llm.model", model_name)
                if model_version:
                    span.set_attribute("llm.model_version", model_version)
                span.set_attribute("ml_langfuse.decided_by", "agent")
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("llm.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_attribute("llm.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# @observe_decision_point  (sync)
# ---------------------------------------------------------------------------

def observe_decision_point(
    point: str,
    phase: str = "phase6",
) -> Callable[[F], F]:
    """
    Decorator that marks a synchronous decision node and emits all
    7 required OTel attributes.

    The decorated function must return a ``dict`` containing at least:
        - ``uaf_score``: float
        - ``clap_flag``: bool
        - ``risk_score``: float
        - ``hitl_gate``: str
        - ``human_decision``: str | None
        - ``decided_by``: str
        - ``compliance_tags``: list[str]

    The decorator reads these from the return value and sets them on the span.

    Args:
        point: The node name, e.g. ``"risk_evaluation"``, ``"uaf_check"``.
        phase: The phase prefix, e.g. ``"phase6"``, ``"phase7"``.
               The span name is ``{phase}.{point}``.

    Example:
        @observe_decision_point(point="risk_evaluation", phase="phase6")
        def risk_evaluation(state: dict) -> dict:
            score = evaluate_risk(state)
            return {
                "uaf_score": 0.85,
                "clap_flag": True,
                "risk_score": score,
                "hitl_gate": "pass" if score < 0.5 else "review",
                "human_decision": None,
                "decided_by": "agent",
                "compliance_tags": ["GDPR Art.22"],
            }
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"{phase}.{point}"

            # Pre-create span so we can pass it for child creation if needed
            result = func(*args, **kwargs)

            if not isinstance(result, dict):
                logger.warning(
                    "%s: decorated function did not return a dict; "
                    "skipping decision span attributes",
                    span_name,
                )
                return result

            try:
                span = create_decision_span(
                    name=span_name,
                    uaf_score=float(result.get("uaf_score", 0.0)),
                    clap_flag=bool(result.get("clap_flag", False)),
                    risk_score=float(result.get("risk_score", 0.0)),
                    hitl_gate=str(result.get("hitl_gate", "pass")),
                    human_decision=result.get("human_decision"),
                    decided_by=str(result.get("decided_by", "agent")),
                    compliance_tags=list(result.get("compliance_tags", [])),
                    tracer=tracer,
                )
                end_span_with_status(span, StatusCode.OK)
            except (ValueError, TypeError) as exc:
                logger.error(
                    "%s: failed to create decision span: %s",
                    span_name,
                    exc,
                )
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# @observe_decision_point_async  (async)
# ---------------------------------------------------------------------------

def observe_decision_point_async(
    point: str,
    phase: str = "phase6",
) -> Callable[[AF], AF]:
    """
    Async variant of ``@observe_decision_point``.

    Decorator that marks an asynchronous decision node and emits all
    7 required OTel attributes.

    Same return-value contract as ``@observe_decision_point``.

    Args:
        point: The node name.
        phase: The phase prefix (default: ``"phase6"``).
    """
    def decorator(func: AF) -> AF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"{phase}.{point}"
            result = await func(*args, **kwargs)

            if not isinstance(result, dict):
                logger.warning(
                    "%s: decorated async function did not return a dict; "
                    "skipping decision span attributes",
                    span_name,
                )
                return result

            try:
                span = create_decision_span(
                    name=span_name,
                    uaf_score=float(result.get("uaf_score", 0.0)),
                    clap_flag=bool(result.get("clap_flag", False)),
                    risk_score=float(result.get("risk_score", 0.0)),
                    hitl_gate=str(result.get("hitl_gate", "pass")),
                    human_decision=result.get("human_decision"),
                    decided_by=str(result.get("decided_by", "agent")),
                    compliance_tags=list(result.get("compliance_tags", [])),
                    tracer=tracer,
                )
                end_span_with_status(span, StatusCode.OK)
            except (ValueError, TypeError) as exc:
                logger.error(
                    "%s: failed to create decision span: %s",
                    span_name,
                    exc,
                )
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# @observe_tool_call
# ---------------------------------------------------------------------------

def observe_tool_call(
    tool_name: str,
) -> Callable[[F], F]:
    """
    Decorator that wraps a tool / function invocation with I/O tracking.

    Creates a span named ``tool.{tool_name}`` with attributes:
        - ``tool.name``
        - ``tool.input_size`` (bytes, estimated via repr)
        - ``tool.latency_ms`` (set on span end)

    Args:
        tool_name: The tool identifier, e.g. ``"search"``, ``"db_query"``.

    Example:
        @observe_tool_call(tool_name="web_search")
        def web_search(query: str) -> dict:
            return search_engine.query(query)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"tool.{tool_name}"
            t0 = time.perf_counter()
            input_repr = repr(kwargs) if kwargs else repr(args)
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.input_size", len(input_repr))
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("tool.latency_ms", (time.perf_counter() - t0) * 1000)
                    span.set_attribute("tool.output_size", len(repr(result)))
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_attribute("tool.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            span_name = f"tool.{tool_name}"
            t0 = time.perf_counter()
            input_repr = repr(kwargs) if kwargs else repr(args)
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("tool.name", tool_name)
                span.set_attribute("tool.input_size", len(input_repr))
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("tool.latency_ms", (time.perf_counter() - t0) * 1000)
                    span.set_attribute("tool.output_size", len(repr(result)))
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_attribute("tool.latency_ms", (time.perf_counter() - t0) * 1000)
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# @observe_span
# ---------------------------------------------------------------------------

def observe_span(
    name: str,
    attributes: Optional[dict[str, object]] = None,
) -> Callable[[F], F]:
    """
    Generic span wrapper for arbitrary operations.

    Creates a span named ``name`` and sets any additional attributes
    passed via the ``attributes`` dict.

    Args:
        name: The span name.
        attributes: Optional dict of OTel attributes to set on every span
                    created by this decorator.

    Example:
        @observe_span(name="data_preprocessing", attributes={"data.source": "s3"})
        def preprocess(raw_data: bytes) -> pd.DataFrame:
            return parse(raw_data)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = await func(*args, **kwargs)
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = _get_tracer()
            with tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = func(*args, **kwargs)
                    end_span_with_status(span, StatusCode.OK)
                    return result
                except Exception as exc:
                    end_span_with_status(span, StatusCode.ERROR, exc)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator
