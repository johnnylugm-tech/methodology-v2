"""
Custom exceptions for the graph execution framework.

This module defines a hierarchy of exceptions used throughout the graph
system to provide clear, actionable error messages when failures occur.
"""


class FeatureError(Exception):
    """Base exception for all graph-related errors.

    All custom exceptions in this module inherit from this class.
    Use this exception when the error doesn't fit a more specific category.

    Args:
        message: Human-readable description of the error.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class DuplicateNodeError(FeatureError):
    """Raised when a node with the same name is already present in the graph.

    This occurs when attempting to add a node with a name that already exists
    in the graph's registry. Each node must have a unique identifier.

    Args:
        node_name: The name of the duplicate node.
        message: Optional custom error message.
    """

    def __init__(self, node_name: str, message: str | None = None) -> None:
        if message is None:
            message = f"Node with name '{node_name}' already exists in the graph"
        super().__init__(message)
        self.node_name = node_name


class OrphanedNodeError(FeatureError):
    """Raised when one or more nodes have no incoming edges.

    An orphaned node is a node that exists in the graph but has no other
    nodes pointing to it. This usually indicates a configuration error
    where nodes were defined but never connected to the graph structure.

    Args:
        node_names: List of node names that are orphaned.
        message: Optional custom error message.
    """

    def __init__(self, node_names: list[str], message: str | None = None) -> None:
        if message is None:
            names = ", ".join(f"'{n}'" for n in node_names)
            message = f"Orphaned nodes found with no incoming edges: {names}"
        super().__init__(message)
        self.node_names = node_names


class CycleExceededError(FeatureError):
    """Raised when the maximum number of graph traversal cycles is exceeded.

    This occurs when executing the graph would require more iterations than
    the configured maximum to reach a terminal state. This is a safety
    mechanism to prevent infinite loops in cyclic graphs.

    Args:
        cycle_count: The number of cycles attempted before hitting the limit.
        max_cycles: The maximum allowed number of cycles.
        message: Optional custom error message.
    """

    def __init__(self, cycle_count: int, max_cycles: int, message: str | None = None) -> None:
        if message is None:
            message = (
                f"Graph execution exceeded maximum cycles: "
                f"attempted {cycle_count} cycles, limit is {max_cycles}"
            )
        super().__init__(message)
        self.cycle_count = cycle_count
        self.max_cycles = max_cycles


class StateSchemaError(FeatureError):
    """Raised when state schema validation fails.

    This occurs when the graph's state doesn't match the expected schema,
    such as when a required field is missing, a field has an incorrect type,
    or a value violates a constraint.

    Args:
        schema: The expected schema definition.
        actual: The actual state that failed validation.
        message: Optional custom error message.
    """

    def __init__(self, schema: str, actual: str, message: str | None = None) -> None:
        if message is None:
            message = (
                f"State schema validation failed.\n" f"  Expected: {schema}\n" f"  Actual: {actual}"
            )
        super().__init__(message)
        self.schema = schema
        self.actual = actual


class CheckpointNotFoundError(FeatureError):
    """Raised when a requested checkpoint does not exist.

    This occurs when attempting to restore from a checkpoint that was never
    created or has been garbage collected. Checkpoints are identified by
    a unique ID assigned at creation time.

    Args:
        checkpoint_id: The ID of the missing checkpoint.
        message: Optional custom error message.
    """

    def __init__(self, checkpoint_id: str, message: str | None = None) -> None:
        if message is None:
            message = f"Checkpoint with ID '{checkpoint_id}' not found"
        super().__init__(message)
        self.checkpoint_id = checkpoint_id


class CheckpointAlreadyExistsError(FeatureError):
    """Raised when attempting to create a checkpoint that already exists.

    This occurs when a checkpoint with the same ID is already stored.
    Each checkpoint must have a unique identifier to prevent accidental
    overwrites of important save points.

    Args:
        checkpoint_id: The ID of the existing checkpoint.
        message: Optional custom error message.
    """

    def __init__(self, checkpoint_id: str, message: str | None = None) -> None:
        if message is None:
            message = f"Checkpoint with ID '{checkpoint_id}' already exists"
        super().__init__(message)
        self.checkpoint_id = checkpoint_id


class TimeoutError(FeatureError):
    """Raised when a node execution exceeds its time limit.

    This occurs when a node takes longer than the configured timeout
    to complete execution. Timeout is typically set per-node to prevent
    runaway tasks from blocking graph progress.

    Args:
        node_name: The name of the node that timed out.
        timeout_seconds: The configured timeout in seconds.
        message: Optional custom error message.
    """

    def __init__(self, node_name: str, timeout_seconds: float, message: str | None = None) -> None:
        if message is None:
            message = f"Node '{node_name}' execution timed out after " f"{timeout_seconds} seconds"
        super().__init__(message)
        self.node_name = node_name
        self.timeout_seconds = timeout_seconds


class RetryExhaustedError(FeatureError):
    """Raised when all retry attempts for a node have been exhausted.

    This occurs when a node fails execution and the configured maximum
    number of retries has been exceeded without successful completion.
    Each retry attempt will raise this exception upon its own failure.

    Args:
        node_name: The name of the node that failed.
        attempts: The number of attempts made before exhausting retries.
        last_error: The error message from the last failed attempt.
        message: Optional custom error message.
    """

    def __init__(
        self,
        node_name: str,
        attempts: int,
        last_error: str,
        message: str | None = None,
    ) -> None:
        if message is None:
            message = (
                f"Node '{node_name}' failed after {attempts} attempts. " f"Last error: {last_error}"
            )
        super().__init__(message)
        self.node_name = node_name
        self.attempts = attempts
        self.last_error = last_error


class GraphValidationError(FeatureError):
    """Raised when graph structure validation fails.

    This occurs when the graph topology is invalid, such as when
    edges reference non-existent nodes, the graph has no terminal
    nodes, or the graph contains structural issues that would prevent
    execution.

    Args:
        errors: List of validation error messages.
        message: Optional custom error message.
    """

    def __init__(self, errors: list[str], message: str | None = None) -> None:
        if message is None:
            error_list = "\n  - ".join(errors)
            message = f"Graph validation failed with {len(errors)} error(s):\n  - {error_list}"
        super().__init__(message)
        self.errors = errors


class NodeNotFoundError(FeatureError):
    """Raised when a referenced node does not exist in the graph.

    This occurs when an edge references a source or target node
    that has not been registered in the graph.

    Args:
        node_name: The name of the missing node.
        message: Optional custom error message.
    """

    def __init__(self, node_name: str, message: str | None = None) -> None:
        if message is None:
            message = f"Node '{node_name}' not found in graph"
        super().__init__(message)
        self.node_name = node_name


class InvalidEdgeError(FeatureError):
    """Raised when an edge configuration is invalid.

    This occurs when an edge is added with invalid parameters,
    such as connecting a node to itself or using reserved names
    incorrectly.

    Args:
        source: The source node of the invalid edge.
        target: The target node of the invalid edge.
        reason: The reason the edge is invalid.
        message: Optional custom error message.
    """

    def __init__(self, source: str, target: str, reason: str, message: str | None = None) -> None:
        if message is None:
            message = f"Invalid edge from '{source}' to '{target}': {reason}"
        super().__init__(message)
        self.source = source
        self.target = target
        self.reason = reason


class CircularDependencyError(FeatureError):
    """Raised when a circular dependency is detected in the graph.

    This occurs when a cycle is detected during graph construction
    that is not allowed under the current configuration.

    Args:
        cycle: The list of node names forming the cycle.
        message: Optional custom error message.
    """

    def __init__(self, cycle: list[str], message: str | None = None) -> None:
        if message is None:
            cycle_str = " -> ".join(cycle)
            message = f"Circular dependency detected: {cycle_str}"
        super().__init__(message)
        self.cycle = cycle
