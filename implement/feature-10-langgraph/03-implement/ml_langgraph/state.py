"""
state.py - Agent State and StateManager for LangGraph Workflow

Provides:
- ErrorRecord: Dataclass for tracking errors during workflow execution
- CheckpointRecord: Dataclass for state snapshots (checkpoints)
- AgentState: Pydantic model representing the full workflow state
- StateManager: Class managing state transitions, checkpoints, and retries

Author: methodology-v2
"""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypedDict

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses: ErrorRecord & CheckpointRecord
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ErrorRecord:
    """
    Records a single error that occurred during workflow execution.

    Attributes:
        node_name: Name of the node where the error originated.
        error_type: Type/classification of the error (e.g. "ValidationError").
        error_message: Human-readable error message.
        timestamp: ISO-format datetime string when error was recorded.
        retryable: Whether this error type is eligible for retry.
        context: Additional metadata about the error (stack trace, input, etc.).
    """

    node_name: str
    error_type: str
    error_message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    retryable: bool = False
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckpointRecord:
    """
    Represents a snapshot of the workflow state at a specific point in time.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint.
        node_name: Name of the node when checkpoint was created.
        timestamp: ISO-format datetime string when checkpoint was created.
        state_snapshot: Deep copy of the relevant state at this point.
    """

    checkpoint_id: str
    node_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    state_snapshot: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# TypedDicts for nested state fields
# ─────────────────────────────────────────────────────────────────────────────


class ExecutionTraceEntry(TypedDict):
    """Single entry in the execution trace."""

    node: str
    event: str
    timestamp: str
    data: dict[str, Any]


# ─────────────────────────────────────────────────────────────────────────────
# AgentState - Pydantic model for the full workflow state
# ─────────────────────────────────────────────────────────────────────────────


class AgentState(BaseModel):
    """
    Central state object for the LangGraph workflow.

    Tracks messages, context, task progress, errors, checkpoints, and
    execution trace. Passed through each node in the graph.

    Attributes:
        messages: List of message dicts (role, content, etc.).
        context: Shared context dictionary for cross-node data.
        current_task: Description of the task currently being executed.
        task_history: Ordered list of task descriptions that have been processed.
        intermediate_results: Node outputs not yet finalized/returned to user.
        finalized_results: Final outputs confirmed ready for delivery.
        errors: List of ErrorRecord instances encountered during execution.
        retry_count: Map of node_name -> number of retries attempted.
        checkpoint_stack: Stack of CheckpointRecord snapshots for rollback.
        current_node: Name of the node currently executing.
        pending_human_review: Whether execution is paused awaiting human review.
        review_notes: Notes/comments from human reviewer.
        execution_trace: List of trace entries for debugging/audit.
        config: Workflow configuration (timeouts, retry policies, etc.).
    """

    messages: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    current_task: str | None = None
    task_history: list[str] = Field(default_factory=list)
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    finalized_results: dict[str, Any] = Field(default_factory=dict)
    errors: list[ErrorRecord] = Field(default_factory=list)
    retry_count: dict[str, int] = Field(default_factory=dict)
    checkpoint_stack: list[CheckpointRecord] = Field(default_factory=list)
    current_node: str | None = None
    pending_human_review: bool = False
    review_notes: str | None = None
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Allow arbitrary types (ErrorRecord, CheckpointRecord) in fields."""

        arbitrary_types_allowed = True

    # ─────────────────────────────────────────────────────────────────────────
    # Utility methods on AgentState
    # ─────────────────────────────────────────────────────────────────────────

    def get_messages(self) -> list[dict[str, Any]]:
        """Return a copy of the messages list."""
        return list(self.messages)

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Append a message dict to the messages list."""
        msg = {"role": role, "content": content, **kwargs}
        self.messages.append(msg)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from context with optional default."""
        return self.context.get(key, default)

    def set_context(self, key: str, value: Any) -> None:
        """Set a key in the context dict."""
        self.context[key] = value

    def add_trace_entry(self, node: str, event: str, data: dict[str, Any] | None = None) -> None:
        """Append an entry to the execution trace."""
        entry: dict[str, Any] = {
            "node": node,
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data or {},
        }
        self.execution_trace.append(entry)

    def summary(self) -> dict[str, Any]:
        """Return a human-readable summary of the current state."""
        return {
            "current_node": self.current_node,
            "current_task": self.current_task,
            "pending_human_review": self.pending_human_review,
            "error_count": len(self.errors),
            "checkpoint_count": len(self.checkpoint_stack),
            "message_count": len(self.messages),
            "task_history_length": len(self.task_history),
        }


# ─────────────────────────────────────────────────────────────────────────────
# RetryPolicy TypedDict
# ─────────────────────────────────────────────────────────────────────────────


class RetryPolicy(TypedDict, total=False):
    """
    TypedDict defining retry behavior for a node.

    Attributes:
        max_attempts: Maximum number of attempts (default 3).
        initial_delay_seconds: Delay before first retry (default 1.0).
        backoff_multiplier: Exponential backoff factor (default 2.0).
        max_delay_seconds: Cap on delay between retries (default 60.0).
        retryable_errors: List of error_type strings that are retryable.
    """

    max_attempts: int
    initial_delay_seconds: float
    backoff_multiplier: float
    max_delay_seconds: float
    retryable_errors: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# StateManager - Manages state transitions, checkpoints, and retries
# ─────────────────────────────────────────────────────────────────────────────


class StateManager:
    """
    Manages AgentState lifecycle: updates, checkpoints, rollback, and retries.

    StateManager wraps an AgentState instance and provides:
    - Atomic partial updates (merge dict into state)
    - Checkpoint creation and restoration (snapshot/restore)
    - Error recording with context
    - Retry eligibility checking with backoff support

    Example:
        sm = StateManager(initial_state=AgentState())
        sm.update({"current_task": "Summarize report"})
        sm.push_checkpoint("SummarizerNode")
        sm.record_error("SummarizerNode", ValueError("LLM timeout"))
        if not sm.can_retry("SummarizerNode", {"max_attempts": 3}):
            raise ExecutionError("max retries exceeded")
    """

    def __init__(self, initial_state: AgentState | None = None) -> None:
        """
        Initialize StateManager with an optional starting state.

        Args:
            initial_state: AgentState instance to wrap. Creates a new empty
                AgentState if not provided.
        """
        self._state = initial_state if initial_state is not None else AgentState()

    @property
    def state(self) -> AgentState:
        """Expose the underlying AgentState (read-only reference)."""
        return self._state

    # ─────────────────────────────────────────────────────────────────────────
    # update - merge partial state updates
    # ─────────────────────────────────────────────────────────────────────────

    def update(self, partial: dict[str, Any]) -> None:
        """
        Merge a partial dict update into the current state.

        Handles top-level keys and nested dicts:
        - For 'errors', 'checkpoint_stack', 'messages', 'task_history':
          append items rather than replace.
        - For 'retry_count': increment existing values instead of overwrite.
        - For all other keys: shallow-replace the value.

        Args:
            partial: Dict of state fields to update.

        Example:
            sm.update({
                "current_task": "Write summary",
                "intermediate_results": {"summary": "..."}
            })
        """
        if not partial:
            return

        # Messages: append new messages instead of replacing list
        if "messages" in partial:
            incoming = partial["messages"]
            if isinstance(incoming, list):
                self._state.messages.extend(m for m in incoming if isinstance(m, dict))
            del partial["messages"]

        # Task history: append new tasks
        if "task_history" in partial:
            incoming = partial["task_history"]
            if isinstance(incoming, list):
                self._state.task_history.extend(t for t in incoming if isinstance(t, str))
            del partial["tasks_history"]

        # Errors: append ErrorRecord instances
        if "errors" in partial:
            incoming = partial["errors"]
            if isinstance(incoming, list):
                for err in incoming:
                    if isinstance(err, ErrorRecord):
                        self._state.errors.append(err)
                    elif isinstance(err, dict):
                        self._state.errors.append(ErrorRecord(**err))
            del partial["errors"]

        # Checkpoint stack: append CheckpointRecord instances
        if "checkpoint_stack" in partial:
            incoming = partial["checkpoint_stack"]
            if isinstance(incoming, list):
                for cp in incoming:
                    if isinstance(cp, CheckpointRecord):
                        self._state.checkpoint_stack.append(cp)
                    elif isinstance(cp, dict):
                        self._state.checkpoint_stack.append(CheckpointRecord(**cp))
            del partial["checkpoint_stack"]

        # Retry count: increment rather than replace
        if "retry_count" in partial:
            incoming = partial["retry_count"]
            if isinstance(incoming, dict):
                for node, count in incoming.items():
                    if node in self._state.retry_count:
                        self._state.retry_count[node] += count
                    else:
                        self._state.retry_count[node] = count
            del partial["retry_count"]

        # Remaining keys: direct assignment (shallow)
        for key, value in partial.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
            else:
                # Fallback: store in context
                self._state.context[key] = value

    # ─────────────────────────────────────────────────────────────────────────
    # push_checkpoint - create a state snapshot
    # ─────────────────────────────────────────────────────────────────────────

    def push_checkpoint(self, node_name: str) -> str:
        """
        Create a checkpoint of the current state and push onto the stack.

        The checkpoint captures a deep-copy snapshot of key state fields,
        allowing later restoration.

        Args:
            node_name: Name of the node creating this checkpoint.

        Returns:
            The checkpoint_id (UUID string) of the created checkpoint.
        """
        checkpoint_id = str(uuid.uuid4())

        # Deep-copy key fields for the snapshot
        snapshot: dict[str, Any] = {
            "messages": copy.deepcopy(self._state.messages),
            "context": copy.deepcopy(self._state.context),
            "current_task": self._state.current_task,
            "task_history": list(self._state.task_history),
            "intermediate_results": copy.deepcopy(self._state.intermediate_results),
            "finalized_results": copy.deepcopy(self._state.finalized_results),
            "retry_count": dict(self._state.retry_count),
            "current_node": self._state.current_node,
        }

        record = CheckpointRecord(
            checkpoint_id=checkpoint_id,
            node_name=node_name,
            timestamp=datetime.now().isoformat(),
            state_snapshot=snapshot,
        )

        self._state.checkpoint_stack.append(record)

        # Trace entry
        self._state.add_trace_entry(
            node=node_name,
            event="checkpoint_created",
            data={"checkpoint_id": checkpoint_id},
        )

        return checkpoint_id

    # ─────────────────────────────────────────────────────────────────────────
    # restore_checkpoint - rollback to a previous snapshot
    # ─────────────────────────────────────────────────────────────────────────

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Restore state to the snapshot identified by checkpoint_id.

        If the checkpoint is found, overwrites the current state fields
        with the snapshot values. Returns False if checkpoint_id not found.

        Args:
            checkpoint_id: UUID string of the checkpoint to restore.

        Returns:
            True if restoration succeeded, False if checkpoint not found.
        """
        target: CheckpointRecord | None = None
        for cp in self._state.checkpoint_stack:
            if cp.checkpoint_id == checkpoint_id:
                target = cp
                break

        if target is None:
            return False

        snapshot = target.state_snapshot

        # Restore each field from snapshot
        self._state.messages = snapshot.get("messages", [])
        self._state.context = snapshot.get("context", {})
        self._state.current_task = snapshot.get("current_task")
        self._state.task_history = snapshot.get("task_history", [])
        self._state.intermediate_results = snapshot.get("intermediate_results", {})
        self._state.finalized_results = snapshot.get("finalized_results", {})
        self._state.retry_count = snapshot.get("retry_count", {})
        self._state.current_node = snapshot.get("current_node")

        # Trace entry
        self._state.add_trace_entry(
            node=target.node_name,
            event="checkpoint_restored",
            data={"checkpoint_id": checkpoint_id, "from_node": target.node_name},
        )

        return True

    def get_checkpoint(self, checkpoint_id: str) -> CheckpointRecord | None:
        """
        Retrieve a checkpoint record by its ID without restoring state.

        Args:
            checkpoint_id: UUID string of the checkpoint.

        Returns:
            CheckpointRecord if found, None otherwise.
        """
        for cp in self._state.checkpoint_stack:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    def list_checkpoints(self) -> list[dict[str, str]]:
        """
        Return a summary list of all checkpoints (id, node, timestamp).

        Returns:
            List of dicts with 'checkpoint_id', 'node_name', 'timestamp'.
        """
        return [
            {
                "checkpoint_id": cp.checkpoint_id,
                "node_name": cp.node_name,
                "timestamp": cp.timestamp,
            }
            for cp in self._state.checkpoint_stack
        ]

    # ─────────────────────────────────────────────────────────────────────────
    # record_error - record an error with context
    # ─────────────────────────────────────────────────────────────────────────

    def record_error(
        self,
        node_name: str,
        error: Exception | str | dict[str, Any],
        retryable: bool = False,
        context: dict[str, Any] | None = None,
    ) -> ErrorRecord:
        """
        Record an error that occurred during node execution.

        Accepts an Exception, an error string, or a pre-built dict.
        Appends an ErrorRecord to self._state.errors.

        Args:
            node_name: Name of the node where error occurred.
            error: The error (Exception instance, string, or dict).
            retryable: Whether this error should be considered retryable.
            context: Additional metadata to attach to the error record.

        Returns:
            The ErrorRecord instance that was created and appended.
        """
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error_message = str(error)
        elif isinstance(error, str):
            error_type = "GenericError"
            error_message = error
        elif isinstance(error, dict):
            error_type = error.get("error_type", "UnknownError")
            error_message = error.get("error_message", str(error))
        else:
            error_type = "UnknownError"
            error_message = str(error)

        record = ErrorRecord(
            node_name=node_name,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now().isoformat(),
            retryable=retryable,
            context=context or {},
        )

        self._state.errors.append(record)

        # Trace entry for the error
        self._state.add_trace_entry(
            node=node_name,
            event="error_recorded",
            data={
                "error_type": error_type,
                "error_message": error_message,
                "retryable": retryable,
            },
        )

        return record

    # ─────────────────────────────────────────────────────────────────────────
    # can_retry - check if a node may be retried under the given policy
    # ─────────────────────────────────────────────────────────────────────────

    def can_retry(
        self,
        node_name: str,
        policy: RetryPolicy | dict[str, Any] | None = None,
    ) -> bool:
        """
        Determine whether a node can be retried based on its retry count.

        Compares the number of attempts made against the policy's
        max_attempts limit. Also checks whether the most recent error
        for the node is marked as retryable.

        Args:
            node_name: Name of the node to check.
            policy: RetryPolicy dict. Supports keys:
                - max_attempts (int): maximum retry attempts allowed.
                  Defaults to 3 if not specified.
                - retryable_errors (list[str]): error types that can be retried.
                  If provided, checks the latest error's error_type against
                  this list; non-listed error types return False.

        Returns:
            True if retries are allowed under the policy, False otherwise.
        """
        if policy is None:
            policy = {}

        max_attempts: int = policy.get("max_attempts", 3)
        retryable_errors: list[str] | None = policy.get("retryable_errors")

        current_attempts = self._state.retry_count.get(node_name, 0)

        # Check attempt limit
        if current_attempts >= max_attempts:
            return False

        # If retryable_errors list is provided, verify error type is allowed
        if retryable_errors is not None:
            # Find most recent error for this node
            last_error: ErrorRecord | None = None
            for err in reversed(self._state.errors):
                if err.node_name == node_name:
                    last_error = err
                    break

            if last_error is not None and last_error.error_type not in retryable_errors:
                return False

            # Also check the error's retryable flag
            if last_error is not None and not last_error.retryable:
                return False

        return True

    def increment_retry(self, node_name: str) -> int:
        """
        Increment the retry counter for a node and return the new count.

        Args:
            node_name: Name of the node to increment.

        Returns:
            New retry count after incrementing.
        """
        current = self._state.retry_count.get(node_name, 0)
        new_count = current + 1
        self._state.retry_count[node_name] = new_count
        return new_count

    def reset_retry(self, node_name: str) -> None:
        """Reset the retry counter for a node to zero."""
        self._state.retry_count[node_name] = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Convenience helpers
    # ─────────────────────────────────────────────────────────────────────────

    def clear_errors(self, node_name: str | None = None) -> int:
        """
        Clear errors from the state.

        Args:
            node_name: If provided, only clear errors from this node.
                If None, clear all errors.

        Returns:
            Number of errors cleared.
        """
        if node_name is None:
            cleared = len(self._state.errors)
            self._state.errors.clear()
        else:
            original_len = len(self._state.errors)
            self._state.errors = [e for e in self._state.errors if e.node_name != node_name]
            cleared = original_len - len(self._state.errors)
        return cleared

    def pop_checkpoint(self) -> CheckpointRecord | None:
        """
        Pop and return the most recent checkpoint without restoring state.

        Returns:
            The CheckpointRecord that was removed, or None if stack is empty.
        """
        if not self._state.checkpoint_stack:
            return None
        return self._state.checkpoint_stack.pop()

    def is_human_review_pending(self) -> bool:
        """Return True if workflow is waiting for human review."""
        return self._state.pending_human_review

    def request_human_review(self, notes: str | None = None) -> None:
        """Set pending_human_review to True and optionally store review notes."""
        self._state.pending_human_review = True
        if notes is not None:
            self._state.review_notes = notes

    def resolve_human_review(self, notes: str | None = None) -> None:
        """Clear the human review flag and optionally store resolution notes."""
        self._state.pending_human_review = False
        if notes is not None:
            self._state.review_notes = notes

    def get_errors_for_node(self, node_name: str) -> list[ErrorRecord]:
        """Return all ErrorRecord instances for a given node."""
        return [e for e in self._state.errors if e.node_name == node_name]

    def latest_error_for_node(self, node_name: str) -> ErrorRecord | None:
        """Return the most recent ErrorRecord for a node, or None."""
        for err in reversed(self._state.errors):
            if err.node_name == node_name:
                return err
        return None

    def summary(self) -> dict[str, Any]:
        """Return a summary dict of the current state."""
        return self._state.summary()

    def copy(self) -> AgentState:
        """
        Return a deep copy of the underlying AgentState.

        Useful for branching/exploring state without mutating the original.
        """
        return copy.deepcopy(self._state)
