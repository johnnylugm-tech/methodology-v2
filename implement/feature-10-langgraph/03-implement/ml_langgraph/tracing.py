"""
Execution tracing module for LangGraph workflow instrumentation.

Provides span-based execution tracking, event logging, and trace serialization
for monitoring and debugging LangGraph workflows.

FR-108: Tracing Infrastructure
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Generator, Optional


class SpanStatus(Enum):
    """Span completion status constants."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Module-level constants for convenience
SPAN_STATUS_SUCCESS = SpanStatus.SUCCESS
SPAN_STATUS_FAILED = SpanStatus.FAILED
SPAN_STATUS_TIMEOUT = SpanStatus.TIMEOUT


@dataclass
class SpanEvent:
    """A timestamped event that occurred during a span's execution."""
    name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Span:
    """Represents a single unit of work within a trace."""
    span_id: str
    parent_id: Optional[str]
    node_name: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: Optional[SpanStatus] = None
    events: list[SpanEvent] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def duration_ms(self) -> Optional[float]:
        """Calculate span duration in milliseconds."""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000

    def add_event(self, event_name: str, metadata: Optional[dict[str, Any]] = None) -> None:
        """Add an event to this span."""
        self.events.append(SpanEvent(
            name=event_name,
            metadata=metadata or {}
        ))

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "node_name": self.node_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value if self.status else None,
            "duration_ms": self.duration_ms(),
            "events": [e.to_dict() for e in self.events],
            "metadata": self.metadata,
        }


@dataclass
class TraceRecord:
    """Complete record of a single trace execution."""
    trace_id: str
    execution_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    spans: list[Span] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_span(self, span: Span) -> None:
        """Register a span within this trace."""
        self.spans.append(span)

    def get_span(self, span_id: str) -> Optional[Span]:
        """Retrieve a span by its ID."""
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_root_spans(self) -> list[Span]:
        """Return spans with no parent (top-level spans)."""
        return [s for s in self.spans if s.parent_id is None]

    def finalize(self) -> None:
        """Compute final duration and mark trace complete."""
        self.end_time = datetime.utcnow()
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.total_duration_ms = delta.total_seconds() * 1000

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "execution_id": self.execution_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "span_count": len(self.spans),
            "spans": [s.to_dict() for s in self.spans],
            "metadata": self.metadata,
        }


class ExecutionTracer:
    """
    Core tracing engine for LangGraph workflow execution.

    Supports span-based instrumentation with optional profiling mode.
    Spans can be created hierarchically via parent_id linking.
    Each trace is identified by a unique trace_id and execution_id pair.

    Example:
        tracer = ExecutionTracer(enable_profiling=True)
        tracer.start_trace(execution_id="run-001")
        with tracer.span("node_a"):
            # do work
            pass
        tracer.end_trace()
        print(tracer.to_json())
    """

    def __init__(self, enable_profiling: bool = False) -> None:
        """
        Initialize the execution tracer.

        Args:
            enable_profiling: If True, records additional timing metadata.
        """
        self._enable_profiling = enable_profiling
        self._active_trace: Optional[TraceRecord] = None
        self._active_span_stack: list[str] = []
        self._span_counter: int = 0

    @property
    def enable_profiling(self) -> bool:
        return self._enable_profiling

    @enable_profiling.setter
    def enable_profiling(self, value: bool) -> None:
        self._enable_profiling = value

    def _generate_id(self, prefix: str = "span") -> str:
        """Generate a unique identifier with optional prefix."""
        short_uuid = uuid.uuid4().hex[:12]
        return f"{prefix}-{short_uuid}"

    def start_trace(self, execution_id: str, metadata: Optional[dict[str, Any]] = None) -> str:
        """
        Begin a new trace session.

        Args:
            execution_id: Business-level identifier for this run (e.g., request ID).
            metadata: Optional initial metadata to attach to the trace.

        Returns:
            The generated trace_id.

        Raises:
            RuntimeError: If a trace is already active.
        """
        if self._active_trace is not None:
            raise RuntimeError(
                f"Trace already active (trace_id={self._active_trace.trace_id}). "
                "Call end_trace() before starting a new trace."
            )

        trace_id = self._generate_id(prefix="trace")
        self._active_trace = TraceRecord(
            trace_id=trace_id,
            execution_id=execution_id,
            metadata=metadata or {}
        )
        self._active_span_stack = []
        self._span_counter = 0

        return trace_id

    def end_trace(self, metadata: Optional[dict[str, Any]] = None) -> Optional[TraceRecord]:
        """
        Close the active trace and finalize its timing.

        Args:
            metadata: Optional metadata to merge into the trace before closing.

        Returns:
            The completed TraceRecord, or None if no trace was active.
        """
        if self._active_trace is None:
            return None

        if metadata:
            self._active_trace.metadata.update(metadata)

        self._active_trace.finalize()

        # Warn about unclosed spans
        if self._active_span_stack:
            unclosed = len(self._active_span_stack)
            # Log but don't fail — just close them implicitly
            for span_id in self._active_span_stack:
                span = self._active_trace.get_span(span_id)
                if span and span.end_time is None:
                    span.end_time = datetime.utcnow()
                    span.status = SpanStatus.FAILED

        record = self._active_trace
        self._active_trace = None
        self._active_span_stack = []
        return record

    def start_span(
        self,
        node_name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Open a new span for a node or sub-operation.

        Args:
            node_name: Identifier for the operation (e.g., node function name).
            parent_id: ID of the parent span for hierarchical linking.
                     If None, uses the current stack top if available.
            metadata: Optional span-level metadata.

        Returns:
            The generated span_id.

        Raises:
            RuntimeError: If no trace is active.
        """
        if self._active_trace is None:
            raise RuntimeError("No active trace. Call start_trace() first.")

        # Determine effective parent
        if parent_id is None and self._active_span_stack:
            parent_id = self._active_span_stack[-1]

        self._span_counter += 1
        span_id = self._generate_id(prefix=f"s{self._span_counter}")

        span = Span(
            span_id=span_id,
            parent_id=parent_id,
            node_name=node_name,
            metadata=metadata or {}
        )

        if self._enable_profiling:
            span.metadata["_profiling_enabled"] = True

        self._active_trace.add_span(span)
        self._active_span_stack.append(span_id)

        return span_id

    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.SUCCESS,
        metadata: Optional[dict[str, Any]] = None
    ) -> Optional[Span]:
        """
        Close a span and record its outcome.

        Args:
            span_id: ID of the span to close.
            status: Completion status (success/failed/timeout).
            metadata: Optional metadata to merge before closing.

        Returns:
            The closed Span, or None if not found.
        """
        if self._active_trace is None:
            return None

        span = self._active_trace.get_span(span_id)
        if span is None:
            return None

        span.end_time = datetime.utcnow()
        span.status = status

        if metadata:
            span.metadata.update(metadata)

        # Pop from stack if it's the current span
        if self._active_span_stack and self._active_span_stack[-1] == span_id:
            self._active_span_stack.pop()

        return span

    def add_event(
        self,
        span_id: str,
        event_name: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Append a named event to a span for custom instrumentation.

        Args:
            span_id: Target span ID.
            event_name: Name of the event (e.g., "cache_hit", "retry").
            metadata: Optional event payload.
        """
        if self._active_trace is None:
            return

        span = self._active_trace.get_span(span_id)
        if span is not None:
            span.add_event(event_name, metadata)

    def get_trace(self) -> Optional[TraceRecord]:
        """
        Retrieve the currently active trace without closing it.

        Returns:
            The active TraceRecord, or None if no trace is running.
        """
        return self._active_trace

    def to_json(self, indent: bool = True) -> str:
        """
        Serialize the active trace to a JSON string.

        Args:
            indent: If True, pretty-prints with indentation.

        Returns:
            JSON representation of the current trace.
        """
        if self._active_trace is None:
            return "{}"

        return json.dumps(
            self._active_trace.to_dict(),
            indent=2 if indent else None,
            ensure_ascii=False
        )

    @contextmanager
    def span(
        self,
        node_name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        status_on_error: SpanStatus = SpanStatus.FAILED
    ) -> Generator[str, None, None]:
        """
        Context-manager entry for defining a span with automatic lifecycle.

        Usage:
            tracer = ExecutionTracer()
            tracer.start_trace("exec-1")
            with tracer.span("my_node") as span_id:
                # work here
                pass
            tracer.end_trace()

        Args:
            node_name: Name of the node/operation.
            parent_id: Optional parent span ID.
            metadata: Optional span metadata.
            status_on_error: Status to set if an exception escapes the block.

        Yields:
            The span_id of the newly opened span.
        """
        span_id = self.start_span(node_name, parent_id, metadata)
        try:
            yield span_id
        except Exception:
            self.end_span(span_id, status=status_on_error, metadata={"error": str(Exception)})
            raise
        else:
            self.end_span(span_id, status=SpanStatus.SUCCESS)

    def clear(self) -> None:
        """
        Reset all state, abandoning any in-progress trace.

        Use with caution — prefer end_trace() for normal cleanup.
        """
        self._active_trace = None
        self._active_span_stack = []
        self._span_counter = 0


class TraceContext:
    """
    Token-based context manager for managing trace scope.

    Provides a clean separation between tracer configuration and
    the actual instrumentation calls, allowing pluggable strategy injection.

    Example:
        ctx = TraceContext(tracer, execution_id="req-123")
        with ctx:
            ctx.span("step_1")
            # ...
    """

    def __init__(
        self,
        tracer: ExecutionTracer,
        execution_id: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        self._tracer = tracer
        self._execution_id = execution_id
        self._initial_metadata = metadata or {}
        self._trace_id: Optional[str] = None

    def __enter__(self) -> "TraceContext":
        self._trace_id = self._tracer.start_trace(
            execution_id=self._execution_id,
            metadata=self._initial_metadata
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        metadata = {}
        if exc_type is not None:
            metadata["error"] = str(exc_val)
        self._tracer.end_trace(metadata=metadata if metadata else None)
        return False  # Do not suppress exceptions

    def span(
        self,
        node_name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """Create a span within this context."""
        return self._tracer.start_span(node_name, parent_id, metadata)

    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.SUCCESS,
        metadata: Optional[dict[str, Any]] = None
    ) -> Optional[Span]:
        """Close a span within this context."""
        return self._tracer.end_span(span_id, status, metadata)