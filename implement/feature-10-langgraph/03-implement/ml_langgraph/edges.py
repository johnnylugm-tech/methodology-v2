"""
edges.py - Edge Configuration for LangGraph Workflows

Provides data structures and utilities for defining node transitions,
including conditional routing and edge validation.

Author: Agent
Date: 2026-04-21
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Any, Union
from enum import Enum

# Type alias for router functions
RouterFunction = Callable[["StateT"], str]


class StateT(dict):
    """
    TypedDict-like state container for routing decisions.
    In practice this would be typed properly via TypedDict.
    """

    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key, default)


# ----------------------------------------------------------------------
# Edge Item
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class EdgeItem:
    """
    Represents a directed edge between two nodes in the graph.

    Attributes:
        source: Name of the source node
        target: Name of the target node
    """

    source: str
    target: str

    def __repr__(self) -> str:
        return f"EdgeItem(source={self.source!r}, target={self.target!r})"

    def __hash__(self) -> int:
        return hash((self.source, self.target))


# ----------------------------------------------------------------------
# Conditional Edge Item
# ----------------------------------------------------------------------


@dataclass
class ConditionalEdgeItem:
    """
    Represents a conditional edge that routes to different nodes
    based on a routing function's output.

    Attributes:
        source: Name of the source node
        routing_fn: Callable that takes state and returns a routing key
        mapping: Dict mapping routing keys to target node names
        default: Default target node name when routing key not in mapping
    """

    source: str
    routing_fn: RouterFunction
    mapping: Dict[str, str] = field(default_factory=dict)
    default: Optional[str] = None

    def route(self, state: StateT) -> str:
        """
        Execute routing function and resolve target node.

        Args:
            state: Current workflow state

        Returns:
            Target node name based on routing function output
        """
        key = self.routing_fn(state)
        return self.mapping.get(key, self.default)

    def __repr__(self) -> str:
        return (
            f"ConditionalEdgeItem(source={self.source!r}, "
            f"routing_fn={self.routing_fn.__name__}, "
            f"mapping={list(self.mapping.keys())!r}, "
            f"default={self.default!r})"
        )


# ----------------------------------------------------------------------
# Helper Router Functions
# ----------------------------------------------------------------------


def route_by_confidence(state: StateT, threshold: float) -> str:
    """
    Route based on confidence score in state.

    Args:
        state: Must contain 'confidence' key with float value [0.0, 1.0]
        threshold: Minimum confidence to route to 'high_confidence' path

    Returns:
        'high_confidence' if confidence >= threshold, else 'low_confidence'

    Raises:
        KeyError: If 'confidence' key not found in state
    """
    confidence = state.get("confidence")
    if confidence is None:
        raise KeyError("State must contain 'confidence' key for route_by_confidence")
    return "high_confidence" if confidence >= threshold else "low_confidence"


def route_by_result_count(state: StateT, min_count: int) -> str:
    """
    Route based on the number of results in state.

    Args:
        state: Must contain 'results' key with list value
        min_count: Minimum number of results to route to 'sufficient' path

    Returns:
        'sufficient' if len(results) >= min_count, else 'insufficient'
    """
    results = state.get("results", [])
    if not isinstance(results, list):
        results = []
    return "sufficient" if len(results) >= min_count else "insufficient"


def route_by_error_count(state: StateT, max_errors: int) -> str:
    """
    Route based on the number of errors in state.

    Args:
        state: Must contain 'errors' key with list value
        max_errors: Maximum acceptable error count before routing to 'failed'

    Returns:
        'failed' if error count > max_errors, else 'success'
    """
    errors = state.get("errors", [])
    if not isinstance(errors, list):
        errors = []
    return "failed" if len(errors) > max_errors else "success"


# ----------------------------------------------------------------------
# Edge Validator
# ----------------------------------------------------------------------


class EdgeValidationError(Exception):
    """Raised when edge validation fails."""

    pass


class EdgeValidator:
    """
    Validates graph edges for structural integrity and consistency.

    Provides static methods for checking edge validity, detecting
    orphaned nodes, and ensuring the graph is well-formed.
    """

    @staticmethod
    def validate_edge(edges: List[EdgeItem], node_names: Set[str]) -> List[str]:
        """
        Validate a list of edges against known node names.

        Args:
            edges: List of EdgeItem to validate
            node_names: Set of valid node names in the graph

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []

        for edge in edges:
            if edge.source not in node_names:
                errors.append(
                    f"Edge source node '{edge.source}' is not in graph. "
                    f"Known nodes: {sorted(node_names)}"
                )
            if edge.target not in node_names:
                errors.append(
                    f"Edge target node '{edge.target}' is not in graph. "
                    f"Known nodes: {sorted(node_names)}"
                )

        # Check for duplicate edges
        edge_set = set()
        for edge in edges:
            if edge in edge_set:
                errors.append(f"Duplicate edge detected: {edge}")
            edge_set.add(edge)

        return errors

    @staticmethod
    def detect_orphaned_nodes(
        edges: List[EdgeItem], node_names: Set[str], entry_point: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Detect nodes that are unreachable or have no outgoing edges.

        An orphaned node is one that:
        - Is not reachable from the entry point (if specified)
        - Has no outgoing edges and is not the entry point

        Args:
            edges: List of EdgeItem to analyze
            node_names: Set of all node names in the graph
            entry_point: Optional name of the entry/start node

        Returns:
            Dict with keys:
                - 'unreachable': nodes not reachable from entry_point
                - 'no_outgoing': nodes with no outgoing edges (excluding entry)
                - 'no_incoming': nodes with no incoming edges (excluding entry)
        """
        # Build adjacency and reverse adjacency maps
        outgoing: Dict[str, List[str]] = {name: [] for name in node_names}
        incoming: Dict[str, List[str]] = {name: [] for name in node_names}

        for edge in edges:
            outgoing[edge.source].append(edge.target)
            incoming[edge.target].append(edge.source)

        result: Dict[str, List[str]] = {"unreachable": [], "no_outgoing": [], "no_incoming": []}

        # Find nodes unreachable from entry point
        if entry_point and entry_point in node_names:
            reachable = EdgeValidator._bfs_reachable(entry_point, outgoing)
            unreachable = node_names - reachable
            result["unreachable"] = sorted(unreachable)
        else:
            # If no entry point, consider all nodes without incoming edges as unreachable
            for node in node_names:
                if not incoming[node]:
                    result["no_incoming"].append(node)

        # Find nodes with no outgoing edges
        for node in node_names:
            if node != entry_point and not outgoing[node]:
                result["no_outgoing"].append(node)

        # Find nodes with no incoming edges (excluding entry point)
        for node in node_names:
            if node != entry_point and not incoming[node]:
                result["no_incoming"].append(node)

        # Sort all lists for consistent output
        for key in result:
            result[key] = sorted(result[key])

        return result

    @staticmethod
    def _bfs_reachable(start: str, adjacency: Dict[str, List[str]]) -> Set[str]:
        """
        BFS to find all nodes reachable from start node.

        Args:
            start: Starting node name
            adjacency: Dict mapping node names to their outgoing edges

        Returns:
            Set of reachable node names
        """
        visited = set()
        queue = [start]

        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        return visited

    @staticmethod
    def validate_conditional_edge(
        cond_edge: ConditionalEdgeItem, node_names: Set[str], valid_routes: Set[str]
    ) -> List[str]:
        """
        Validate a conditional edge's mapping covers expected routes.

        Args:
            cond_edge: ConditionalEdgeItem to validate
            node_names: Set of valid node names in the graph
            valid_routes: Set of routing keys that should be in mapping

        Returns:
            List of validation error messages
        """
        errors = []

        if cond_edge.source not in node_names:
            errors.append(
                f"ConditionalEdge source node '{cond_edge.source}' "
                f"is not in graph. Known nodes: {sorted(node_names)}"
            )

        # Check all mapping targets are valid nodes
        for route_key, target_node in cond_edge.mapping.items():
            if target_node not in node_names:
                errors.append(
                    f"ConditionalEdge mapping[{route_key}] = '{target_node}' "
                    f"is not a valid node. Known nodes: {sorted(node_names)}"
                )

        # Check default is valid
        if cond_edge.default and cond_edge.default not in node_names:
            errors.append(
                f"ConditionalEdge default '{cond_edge.default}' "
                f"is not a valid node. Known nodes: {sorted(node_names)}"
            )

        return errors


# ----------------------------------------------------------------------
# Edge Builder Utility
# ----------------------------------------------------------------------


class EdgeBuilder:
    """
    Fluent builder for constructing edges programmatically.

    Usage:
        builder = EdgeBuilder()
        edges = builder.add("node_a", "node_b") \\
                       .add("node_b", "node_c") \\
                       .build()
    """

    def __init__(self) -> None:
        self._edges: List[EdgeItem] = []

    def add(self, source: str, target: str) -> "EdgeBuilder":
        """
        Add a directed edge from source to target.

        Args:
            source: Source node name
            target: Target node name

        Returns:
            Self for method chaining
        """
        self._edges.append(EdgeItem(source=source, target=target))
        return self

    def build(self) -> List[EdgeItem]:
        """
        Finalize and return the list of edges.

        Returns:
            List of EdgeItem
        """
        return list(self._edges)


# ----------------------------------------------------------------------
# Composite Edge Operators
# ----------------------------------------------------------------------


def merge_edges(edges_list: List[List[EdgeItem]]) -> List[EdgeItem]:
    """
    Merge multiple edge lists into a single deduplicated list.

    Args:
        edges_list: List of edge lists to merge

    Returns:
        Deduplicated combined list of EdgeItem
    """
    seen: Set[EdgeItem] = set()
    result: List[EdgeItem] = []

    for edges in edges_list:
        for edge in edges:
            if edge not in seen:
                seen.add(edge)
                result.append(edge)

    return result


def get_all_nodes(edges: List[EdgeItem]) -> Set[str]:
    """
    Extract all unique node names from a list of edges.

    Args:
        edges: List of EdgeItem

    Returns:
        Set of all node names (both sources and targets)
    """
    nodes: Set[str] = set()
    for edge in edges:
        nodes.add(edge.source)
        nodes.add(edge.target)
    return nodes
