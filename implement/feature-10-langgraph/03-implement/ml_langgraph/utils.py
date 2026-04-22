"""
Shared utility functions for LangGraph workflow engine.
"""

from __future__ import annotations

import re
import time
import uuid
import importlib
from typing import Any, Callable, Type
from copy import deepcopy

from .builder import NodeConfig
from .state import RetryPolicy

# ----------------------------------------------------------------------
# ID generation
# ----------------------------------------------------------------------


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix.

    Args:
        prefix: Optional string prefix for the ID.

    Returns:
        A unique ID string, e.g. "node_abc123" or "abc123" if no prefix.
    """
    uid = uuid.uuid4().hex[:8]
    if prefix:
        return f"{prefix}_{uid}"
    return uid


# ----------------------------------------------------------------------
# State merging
# ----------------------------------------------------------------------


def merge_state(base: dict, update: dict, mode: str = "deep") -> dict:
    """Merge update dict into base dict.

    Args:
        base: Base state dictionary.
        update: Update to apply.
        mode: "deep" for recursive merge, "shallow" for top-level only.

    Returns:
        Merged dictionary (new instance, original untouched).

    Raises:
        TypeError: If mode is not "deep" or "shallow".
    """
    if mode not in ("deep", "shallow"):
        raise TypeError(f"mode must be 'deep' or 'shallow', got '{mode}'")

    result = dict(base)
    for key, val in update.items():
        if (
            mode == "deep"
            and key in result
            and isinstance(result[key], dict)
            and isinstance(val, dict)
        ):
            result[key] = merge_state(result[key], val, mode="deep")
        else:
            result[key] = deepcopy(val)
    return result


# ----------------------------------------------------------------------
# Node signature validation
# ----------------------------------------------------------------------


def validate_node_signature(func: Callable, state_schema: Type) -> bool:
    """Validate that a node function accepts the expected state schema.

    Checks that the function's first parameter is annotated or can be
    bound to the state schema type.

    Args:
        func: The node function to validate.
        state_schema: The expected state schema type (e.g., TypedDict).

    Returns:
        True if the function's first parameter is compatible, False otherwise.
    """
    sig = None
    try:
        import inspect

        sig = inspect.signature(func)
    except (ValueError, TypeError):
        return False

    params = list(sig.parameters.values())
    if not params:
        return False

    first_param = params[0]
    # Accept if annotation matches, or if unannotated (assume Any)
    annotation = first_param.annotation
    if annotation is inspect.Parameter.empty:
        return True
    # Check if annotation is or is a subclass of state_schema
    try:
        if issubclass(annotation, state_schema):
            return True
    except TypeError:
        pass
    # Handle Union types
    if hasattr(annotation, "__args__"):
        if state_schema in annotation.__args__:
            return True
    return False


# ----------------------------------------------------------------------
# Retry policy resolution
# ----------------------------------------------------------------------


def get_node_retry_policy(config: NodeConfig | None, default: RetryPolicy) -> RetryPolicy:
    """Get effective retry policy for a node.

    Args:
        config: Node configuration (may contain retry_policy).
        default: Default retry policy to use if config is None or has no retry policy.

    Returns:
        The resolved retry policy.
    """
    if config is None:
        return default
    if config.retry_policy is not None:
        return config.retry_policy
    return default


# ----------------------------------------------------------------------
# Duration formatting
# ----------------------------------------------------------------------


def format_duration(ms: float) -> str:
    """Format a millisecond duration as human-readable string.

    Args:
        ms: Duration in milliseconds.

    Returns:
        Formatted string like "1.23s", "456ms", "1h 2m 3s".
    """
    if ms < 1:
        return f"{ms:.2f}ms"
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = int(seconds // 60)
    seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {seconds:.0f}s"
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {seconds:.0f}s"


# ----------------------------------------------------------------------
# Node name sanitization
# ----------------------------------------------------------------------


def sanitize_node_name(name: str) -> str:
    """Ensure a node name is a valid Python identifier.

    Replaces invalid characters with underscores and ensures the result
    starts with a letter or underscore.

    Args:
        name: The raw node name (may contain spaces, special chars, etc.).

    Returns:
        A valid Python identifier string.
    """
    # Replace non-alphanumeric chars (except underscore) with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Strip leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Ensure it doesn't start with a digit (prepend _ if needed)
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    if not sanitized:
        sanitized = "node"
    return sanitized


# ----------------------------------------------------------------------
# LangGraph checkpointer dynamic import
# ----------------------------------------------------------------------

_LANGGRAPH_CHECKPOINTER_BACKENDS: dict[str, str] = {
    "memory": "langgraph.checkpoint.memory",
    "sqlite": "langgraph.checkpoint.sqlite",
    "postgres": "langgraph.checkpoint.postgres",
    "postgres-bornless": "langgraph.checkpoint.postgres.pg",
}


def import_langgraph_checkpointer(backend: str):
    """Dynamically import a LangGraph checkpointer backend.

    Args:
        backend: Backend name (e.g., "memory", "sqlite", "postgres").

    Returns:
        The checkpointer class/creator from the specified backend module.

    Raises:
        ImportError: If the backend is not supported or not installed.
        ValueError: If the backend name is unknown.
    """
    if backend not in _LANGGRAPH_CHECKPOINTER_BACKENDS:
        raise ValueError(
            f"Unknown checkpointer backend: '{backend}'. "
            f"Supported: {list(_LANGGRAPH_CHECKPOINTER_BACKENDS.keys())}"
        )
    module_path = _LANGGRAPH_CHECKPOINTER_BACKENDS[backend]
    try:
        module = importlib.import_module(module_path)
        return module
    except ImportError as e:
        raise ImportError(
            f"Failed to import checkpointer '{backend}' from '{module_path}'. "
            "Make sure langgraph is installed with the correct extras: "
            f"pip install langgraph[{backend}]"
        ) from e


# ----------------------------------------------------------------------
# Miscellaneous helpers
# ----------------------------------------------------------------------


def safe_get(dictionary: dict, *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        dictionary: Source dictionary.
        *keys: Sequence of keys to traverse.
        default: Default value if any key is missing.

    Returns:
        The value at the nested path, or default if not found.
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    if value < min_val:
        return min_val
    if value > max_val:
        return max_val
    return value
