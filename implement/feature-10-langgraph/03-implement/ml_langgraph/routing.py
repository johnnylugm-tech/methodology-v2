"""
Conditional routing for LangGraph state machines.

Provides a Router class that dispatches state to target nodes based on
routing functions, plus a collection of pre-built routing strategies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

# Type variable for the state dict shape accepted by all routers.
StateT = dict[str, Any]


# ----------------------------------------------------------------------
# RoutingFunction protocol
# ----------------------------------------------------------------------
class RoutingFunction(Protocol):
    """A callable that inspects state and returns a route key (str)."""

    def __call__(self, state: StateT) -> str: ...


# ----------------------------------------------------------------------
# RouteResult
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class RouteResult:
    """The result of a routing decision."""

    route_key: str
    """Key that identifies which branch was chosen."""

    target_nodes: list[str]
    """List of node names to execute next (may be empty)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Arbitrary auxiliary data about this routing decision."""


# ----------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------
class Router:
    """
    Routes state to one or more target nodes based on a RoutingFunction.

    Parameters
    ----------
    routes:
        Mapping from route keys to the list of nodes that should run
        when that key is returned by the routing function.

    Example
    -------
    >>> router = Router({"draft": ["write_node"], "revise": ["review_node"]})
    >>> result = router.route({"step": "draft"})
    >>> result.route_key
    'draft'
    >>> result.target_nodes
    ['write_node']
    """

    def __init__(self, routes: dict[str, list[str]]) -> None:
        self._routes = routes
        # Verify all referenced nodes are non-empty lists
        for key, nodes in routes.items():
            if not isinstance(nodes, list):
                raise TypeError(
                    f"Route '{key}' must map to a list of node names, got {type(nodes).__name__}"
                )
            if not all(isinstance(n, str) for n in nodes):
                raise TypeError(f"Route '{key}' must contain only string node names")

    def route(self, state: StateT, routing_fn: RoutingFunction | None = None) -> RouteResult:
        """
        Execute routing for the given state.

        Parameters
        ----------
        state:
            The current workflow state dictionary.
        routing_fn:
            Optional override for the default routing function. If not provided,
            the caller should have set ``self._routing_fn`` before calling ``route``.
            The signature is ``(state) -> route_key: str``.

        Returns
        -------
        RouteResult
            Contains the route key, target node list, and any metadata.

        Raises
        ------
        ValueError
            If the routing function returns a key not present in the routes map.
        """
        if routing_fn is None:
            routing_fn = getattr(self, "_routing_fn", None)
        if routing_fn is None:
            raise TypeError(
                "Router.route() requires a routing_fn argument or "
                "a `_routing_fn` attribute set on the Router instance."
            )

        route_key = routing_fn(state)

        if route_key not in self._routes:
            raise ValueError(
                f"Routing function returned unknown key '{route_key}'. "
                f"Available routes: {list(self._routes.keys())}"
            )

        return RouteResult(
            route_key=route_key,
            target_nodes=list(self._routes[route_key]),  # copy to prevent mutation
            metadata={"original_key": route_key},
        )

    def get_targets(self, route_key: str) -> list[str]:
        """
        Return the target node list for a given route key.

        Parameters
        ----------
        route_key:
            A key that exists in the routes map.

        Returns
        -------
        list[str]
            The node list for that key (empty list if key not found).
        """
        return list(self._routes.get(route_key, []))


# ----------------------------------------------------------------------
# Pre-built routing functions
# ----------------------------------------------------------------------
def confidence_router(thresholds: dict[str, float]) -> RoutingFunction:
    """
    Route based on a confidence score in state.

    Looks for a ``confidence`` key (float, 0.0–1.0) and maps ranges to route keys.

    Parameters
    ----------
    thresholds:
        Mapping from route key to the minimum confidence required.
        Thresholds are evaluated in sorted order so that the first matching
        key wins. Example: ``{"high": 0.8, "medium": 0.5, "low": 0.0}``.

    Returns
    -------
    RoutingFunction
        A callable that returns a route key based on confidence.

    Example
    -------
    >>> router_fn = confidence_router({"high": 0.8, "medium": 0.5, "low": 0.0})
    >>> router_fn({"confidence": 0.9})
    'high'
    >>> router_fn({"confidence": 0.6})
    'medium'
    """
    sorted_thresholds = sorted(thresholds.items(), key=lambda x: x[1], reverse=True)

    def _router(state: StateT) -> str:
        confidence: float = state.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)):
            raise TypeError(
                f"confidence_router: 'confidence' must be numeric, got {type(confidence).__name__}"
            )
        for key, threshold in sorted_thresholds:
            if confidence >= threshold:
                return key
        # Fallback to the last (lowest) threshold if none match
        if sorted_thresholds:
            return sorted_thresholds[-1][0]
        return "default"

    return _router


def count_router(min_count: int, below_key: str, above_key: str) -> RoutingFunction:
    """
    Route based on the length of a list in state.

    Looks for a ``results`` key (list) and compares its length to ``min_count``.

    Parameters
    ----------
    min_count:
        Threshold for the results list length.
    below_key:
        Route key when ``len(results) < min_count``.
    above_key:
        Route key when ``len(results) >= min_count``.

    Returns
    -------
    RoutingFunction

    Example
    -------
    >>> router_fn = count_router(3, "retry", "done")
    >>> router_fn({"results": [1, 2]})
    'retry'
    >>> router_fn({"results": [1, 2, 3]})
    'done'
    """

    def _router(state: StateT) -> str:
        results = state.get("results", [])
        if not isinstance(results, list):
            raise TypeError(f"count_router: 'results' must be a list, got {type(results).__name__}")
        return above_key if len(results) >= min_count else below_key

    return _router


def error_router(max_errors: int, error_key: str, ok_key: str) -> RoutingFunction:
    """
    Route based on error count in state.

    Looks for an ``errors`` key (list) and routes based on whether the count
    exceeds ``max_errors``.

    Parameters
    ----------
    max_errors:
        Maximum tolerated number of errors before routing to ``error_key``.
    error_key:
        Route key when error count > ``max_errors``.
    ok_key:
        Route key when error count <= ``max_errors``.

    Returns
    -------
    RoutingFunction

    Example
    -------
    >>> router_fn = error_router(2, "abort", "continue")
    >>> router_fn({"errors": ["timeout", "retry"]})
    'continue'
    >>> router_fn({"errors": ["timeout", "retry", "fatal"]})
    'abort'
    """

    def _router(state: StateT) -> str:
        errors = state.get("errors", [])
        if not isinstance(errors, list):
            raise TypeError(f"error_router: 'errors' must be a list, got {type(errors).__name__}")
        return error_key if len(errors) > max_errors else ok_key

    return _router


def bool_router(flag_key: str, true_key: str, false_key: str) -> RoutingFunction:
    """
    Route based on a boolean flag in state.

    Parameters
    ----------
    flag_key:
        Key in state whose truthiness determines routing.
    true_key:
        Route key when ``bool(state[flag_key])`` is ``True``.
    false_key:
        Route key when the flag is ``False`` or missing.

    Returns
    -------
    RoutingFunction

    Example
    -------
    >>> router_fn = bool_router("is_valid", "process", "reject")
    >>> router_fn({"is_valid": True})
    'process'
    >>> router_fn({"is_valid": False})
    'reject'
    >>> router_fn({})
    'reject'
    """

    def _router(state: StateT) -> str:
        flag = state.get(flag_key)
        return true_key if flag else false_key

    return _router


def regex_router(pattern: str, groups: dict[str, str]) -> RoutingFunction:
    """
    Route based on a regular-expression match against a ``text`` field in state.

    Parameters
    ----------
    pattern:
        Regex pattern (passed to ``re.compile``). Should contain named or
        positional groups that map to the keys in ``groups``.
    groups:
        Mapping from group name (or match group index as string) to route key.
        Example: ``{"(?P<category>\\w+)": "category_route", "0": "default_route"}``
        The pattern is matched against ``state["text"]``; the first matching
        group determines the route key.

    Returns
    -------
    RoutingFunction

    Example
    -------
    >>> router_fn = regex_router(
    ...     r"(?P<type>error|warn|info)",
    ...     {"type": "typed_route"}
    ... )
    >>> router_fn({"text": "error: out of memory"})
    'typed_route'
    >>> router_fn({"text": "something else"})
    Traces through all groups; falls back to ValueError if no match.
    """
    compiled = re.compile(pattern)

    def _router(state: StateT) -> str:
        text = state.get("text", "")
        if not isinstance(text, str):
            raise TypeError(f"regex_router: 'text' must be a string, got {type(text).__name__}")

        match = compiled.search(text)
        if not match:
            raise ValueError(f"regex_router: pattern '{pattern}' did not match text: {text!r}")

        # Try to resolve the route key via named groups first, then positional.
        for key, route_key in groups.items():
            if key == "0":
                # Positional group by index
                try:
                    group_val = match.group(int(key))
                    if group_val is not None:
                        return route_key
                except (IndexError, ValueError):
                    pass
            else:
                # Named group
                try:
                    group_val = match.group(key)
                    if group_val is not None:
                        return route_key
                except re.error:
                    pass

        raise ValueError(
            f"regex_router: no matching group found for text: {text!r} "
            f"(pattern: {pattern}, groups: {list(groups.keys())})"
        )

    return _router


# ----------------------------------------------------------------------
# Composite routing helpers
# ----------------------------------------------------------------------
def chain_routers(*routers: RoutingFunction) -> RoutingFunction:
    """
    Chain multiple routing functions; return the first non-``None`` result.

    Each router is called in order until one returns a non-empty string.
    If all return empty, raises ``ValueError``.

    Parameters
    ----------
    routers:
        Variable number of RoutingFunction callables.

    Returns
    -------
    RoutingFunction

    Example
    -------
    >>> primary = confidence_router({"high": 0.8, "low": 0.0})
    >>> secondary = bool_router("forced", "force", "auto")
    >>> combined = chain_routers(primary, secondary)
    """

    def _router(state: StateT) -> str:
        for router in routers:
            result = router(state)
            if result:
                return result
        raise ValueError("chain_routers: all routers returned empty string")

    return _router


def fallback_router(primary: RoutingFunction, fallback_key: str) -> RoutingFunction:
    """
    Wrap a primary router; return ``fallback_key`` if it raises an exception.

    Parameters
    ----------
    primary:
        The primary RoutingFunction to call.
    fallback_key:
        Route key to return when ``primary`` raises.

    Returns
    -------
    RoutingFunction
    """

    def _router(state: StateT) -> str:
        try:
            return primary(state)
        except Exception:
            return fallback_key

    return _router
