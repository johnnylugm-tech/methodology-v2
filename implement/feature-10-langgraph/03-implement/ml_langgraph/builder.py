"""
LangGraph Builder - Phase 3 (FR-101)

Provides a fluent API for constructing LangGraph state machines.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
)

# LangGraph imports
try:
    from langgraph.graph.state import StateGraph
    from langgraph.graph import END
    from langgraph.graph.state import CompiledStateGraph
except ImportError as e:
    raise ImportError(
        "langgraph is required. Install: pip install langgraph"
    ) from e

# Pydantic for config validation
try:
    from pydantic import BaseModel, Field, ConfigDict
except ImportError as e:
    raise ImportError(
        "pydantic is required. Install: pip install pydantic"
    ) from e

# Custom exceptions
from .exceptions import (
    GraphValidationError,
    NodeNotFoundError,
    DuplicateNodeError,
    InvalidEdgeError,
    CircularDependencyError,
)


# ---------------------------------------------------------------------------
# Internal Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NodeItem:
    """Represents a node in the graph."""
    name: str
    func: Callable[..., Any]
    config: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name}
        if self.config:
            result["config"] = self.config
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], func: Callable[..., Any]) -> NodeItem:
        return cls(
            name=data["name"],
            func=func,
            config=data.get("config"),
        )


@dataclass
class EdgeItem:
    """Represents a directed edge between two nodes."""
    source: str
    target: str

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EdgeItem:
        return cls(source=data["source"], target=data["target"])


@dataclass
class ConditionalEdgeItem:
    """Represents a conditional edge with routing function."""
    source: str
    routing_fn: Callable[..., str]
    mapping: Dict[str, str] = field(default_factory=dict)
    default: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "mapping": self.mapping,
            "default": self.default,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        routing_fn: Callable[..., Any],
    ) -> ConditionalEdgeItem:
        return cls(
            source=data["source"],
            routing_fn=routing_fn,
            mapping=data.get("mapping", {}),
            default=data.get("default"),
        )


# ---------------------------------------------------------------------------
# Config Models (Pydantic)
# ---------------------------------------------------------------------------

class NodeConfig(BaseModel):
    """Configuration for a graph node."""
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    input_schema: Optional[type] = None
    output_schema: Optional[type] = None
    retry_policy: Optional[Dict[str, Any]] = None


class GraphCompileConfig(BaseModel):
    """Configuration for graph compilation."""
    model_config = ConfigDict(extra="allow")

    checkpointer: Optional[Any] = None
    interrupt_before: Optional[List[str]] = None
    interrupt_after: Optional[List[str]] = None
    debug: bool = False
    cache: bool = True
    recursion_limit: int = 25


# ---------------------------------------------------------------------------
# GraphBuilder
# ---------------------------------------------------------------------------

class GraphBuilder:
    """
    Fluent builder for constructing LangGraph state machines.

    Example usage:
        builder = GraphBuilder(state_schema=AgentState, name="agent")
        builder.add_node("research", research_agent)
        builder.add_node("decide", decide_agent)
        builder.add_edge("research", "decide")
        builder.add_conditional_edges(
            source="decide",
            routing_fn=route_based_on_confidence,
            mapping={
                "high": "execute",
                "low": "research",
            },
            default="research",
        )
        graph = builder.compile()

    Attributes:
        state_schema: The Pydantic model or TypedDict defining graph state.
        name: Optional name for the graph.
    """

    def __init__(
        self,
        state_schema: Union[type, Dict[str, Any]],
        name: Optional[str] = None,
        config: Optional[GraphCompileConfig] = None,
    ) -> None:
        """
        Initialize the GraphBuilder.

        Args:
            state_schema: A Pydantic model class or TypedDict representing state.
            name: Optional name for this graph (used in LangGraph visualization).
            config: Optional GraphCompileConfig for default compilation settings.
        """
        self._state_schema = state_schema
        self._name = name or "graph"
        self._default_config = config or GraphCompileConfig()

        # Internal storage
        self._nodes: Dict[str, NodeItem] = {}
        self._edges: List[EdgeItem] = []
        self._conditional_edges: List[ConditionalEdgeItem] = []
        self._entry_point: Optional[str] = None
        self._compiled: Optional[CompiledStateGraph] = None

    # -------------------------------------------------------------------------
    # Node Management
    # -------------------------------------------------------------------------

    def add_node(
        self,
        name: str,
        func: Callable[..., Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> "GraphBuilder":
        """
        Register a node in the graph.

        Args:
            name: Unique identifier for this node.
            func: Callable that processes state and returns updates.
            config: Optional node configuration dict.

        Returns:
            Self for method chaining.

        Raises:
            DuplicateNodeError: If node name already registered.
        """
        if name in self._nodes:
            raise DuplicateNodeError(
                f"Node '{name}' is already registered. "
                f"Existing nodes: {list(self._nodes.keys())}"
            )

        node_config = config or {}
        self._nodes[name] = NodeItem(name=name, func=func, config=node_config)
        return self

    def add_nodes(
        self,
        nodes: Dict[str, Callable[..., Any]],
    ) -> "GraphBuilder":
        """
        Register multiple nodes at once.

        Args:
            nodes: Dict mapping node names to callables.

        Returns:
            Self for method chaining.
        """
        for name, func in nodes.items():
            self.add_node(name, func)
        return self

    # -------------------------------------------------------------------------
    # Edge Management
    # -------------------------------------------------------------------------

    def add_edge(self, source: str, target: str) -> "GraphBuilder":
        """
        Add a directed edge from source to target.

        Args:
            source: Source node name.
            target: Target node name.

        Returns:
            Self for method chaining.

        Raises:
            NodeNotFoundError: If source or target node not found.
            InvalidEdgeError: If edge would create invalid graph structure.
        """
        self._validate_node_exists(source, "add_edge (source)")
        self._validate_node_exists(target, "add_edge (target)")

        edge = EdgeItem(source=source, target=target)
        self._edges.append(edge)
        return self

    def add_conditional_edges(
        self,
        source: str,
        routing_fn: Callable[..., str],
        mapping: Dict[str, str],
        default: Optional[str] = None,
    ) -> "GraphBuilder":
        """
        Add conditional edges from a source node.

        The routing_fn should return a key from `mapping` or `default`.
        LangGraph will route to the corresponding target node.

        Args:
            source: Source node name.
            routing_fn: Function that takes state and returns a routing key.
            mapping: Dict mapping routing keys to target node names.
            default: Default target node name when key not in mapping.

        Returns:
            Self for method chaining.

        Raises:
            NodeNotFoundError: If source node not found or targets not found.
        """
        self._validate_node_exists(source, "add_conditional_edges (source)")

        # Validate all target nodes in mapping
        for target in mapping.values():
            self._validate_node_exists(target, "add_conditional_edges (mapping)")

        if default:
            self._validate_node_exists(default, "add_conditional_edges (default)")

        conditional = ConditionalEdgeItem(
            source=source,
            routing_fn=routing_fn,
            mapping=mapping,
            default=default,
        )
        self._conditional_edges.append(conditional)
        return self

    def set_entry_point(self, node_name: str) -> "GraphBuilder":
        """
        Set the entry point node (starting node for the graph).

        Args:
            node_name: Name of the node to start from.

        Returns:
            Self for method chaining.
        """
        self._validate_node_exists(node_name, "set_entry_point")
        self._entry_point = node_name
        return self

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def _validate_node_exists(self, name: str, operation: str) -> None:
        """Raise NodeNotFoundError if node not registered."""
        if name not in self._nodes:
            raise NodeNotFoundError(
                f"{operation}: Node '{name}' not found. "
                f"Registered nodes: {list(self._nodes.keys())}"
            )

    def _validate_graph_integrity(self) -> None:
        """
        Validate the graph structure before compilation.

        Raises:
            GraphValidationError: If graph structure is invalid.
            CircularDependencyError: If cycles detected (optional check).
        """
        # Ensure at least one node exists
        if not self._nodes:
            raise GraphValidationError(
                "Cannot compile empty graph. Add at least one node."
            )

        # Ensure entry point is set (or use first node as fallback)
        if self._entry_point is None:
            self._entry_point = next(iter(self._nodes.keys()))

        # Validate all edges reference existing nodes
        for edge in self._edges:
            if edge.source not in self._nodes:
                raise NodeNotFoundError(f"Edge source node '{edge.source}' not found")
            if edge.target not in self._nodes:
                raise NodeNotFoundError(f"Edge target node '{edge.target}' not found")

        # Validate conditional edges
        for cond in self._conditional_edges:
            if cond.source not in self._nodes:
                raise NodeNotFoundError(
                    f"Conditional edge source '{cond.source}' not found"
                )
            for target in cond.mapping.values():
                if target not in self._nodes:
                    raise NodeNotFoundError(
                        f"Conditional edge target '{target}' not found"
                    )
            if cond.default and cond.default not in self._nodes:
                raise NodeNotFoundError(
                    f"Conditional edge default '{cond.default}' not found"
                )

        # Detect unconnected nodes (warning only, not error)
        connected = self._get_connected_nodes()
        orphaned = set(self._nodes.keys()) - connected
        if orphaned:
            # Log warning but don't block compilation
            import warnings
            warnings.warn(
                f"Unconnected nodes detected: {orphaned}. "
                "These nodes cannot be reached from the entry point.",
                UserWarning,
            )

    def _get_connected_nodes(self) -> set:
        """Return set of nodes reachable from entry point via edges."""
        if self._entry_point is None:
            return set()

        reachable = {self._entry_point}
        queue = [self._entry_point]

        while queue:
            current = queue.pop(0)
            # Regular edges
            for edge in self._edges:
                if edge.source == current and edge.target not in reachable:
                    reachable.add(edge.target)
                    queue.append(edge.target)
            # Conditional edges
            for cond in self._conditional_edges:
                if cond.source == current:
                    for target in cond.mapping.values():
                        if target not in reachable:
                            reachable.add(target)
                            queue.append(target)
                    if cond.default and cond.default not in reachable:
                        reachable.add(cond.default)
                        queue.append(cond.default)

        return reachable

    # -------------------------------------------------------------------------
    # Build LangGraph
    # -------------------------------------------------------------------------

    def _build_langgraph_stategraph(self) -> StateGraph:
        """
        Construct the underlying LangGraph StateGraph.

        Returns:
            Configured StateGraph ready for compilation.
        """
        # Create the base StateGraph
        graph = StateGraph(self._state_schema)

        # Add all nodes
        for name, node_item in self._nodes.items():
            graph.add_node(name, node_item.func, **node_item.config or {})

        # Add regular edges
        for edge in self._edges:
            graph.add_edge(edge.source, edge.target)

        # Add conditional edges
        for cond in self._conditional_edges:
            if cond.default:
                graph.add_conditional_edges(
                    cond.source,
                    cond.routing_fn,
                    cond.mapping,
                    cond.default,
                )
            else:
                graph.add_conditional_edges(
                    cond.source,
                    cond.routing_fn,
                    cond.mapping,
                )

        # Set entry point
        if self._entry_point:
            graph.set_entry_point(self._entry_point)

        # Set finish point (END) - if nodes have no outgoing edges
        self._add_finish_point(graph)

        return graph

    def _add_finish_point(self, graph: StateGraph) -> None:
        """Automatically set END for nodes with no outgoing edges."""
        # Collect all nodes that have outgoing edges
        has_outgoing: Dict[str, bool] = {name: False for name in self._nodes}

        for edge in self._edges:
            has_outgoing[edge.source] = True

        for cond in self._conditional_edges:
            has_outgoing[cond.source] = True

        # Add END for nodes with no outgoing edges
        for name, outgoing in has_outgoing.items():
            if not outgoing:
                graph.add_edge(name, END)

    # -------------------------------------------------------------------------
    # Compilation
    # -------------------------------------------------------------------------

    def compile(
        self,
        config: Optional[GraphCompileConfig] = None,
    ) -> CompiledStateGraph:
        """
        Compile the graph into an executable LangGraph.

        Args:
            config: Optional compile-time configuration overrides.

        Returns:
            CompiledStateGraph ready for invocation.

        Raises:
            GraphValidationError: If graph structure is invalid.
        """
        # Validate before compilation
        self._validate_graph_integrity()

        # Merge configs
        compile_config = config or self._default_config

        # Build and compile
        base_graph = self._build_langgraph_stategraph()

        # Extract compile kwargs
        compile_kwargs: Dict[str, Any] = {
            "debug": compile_config.debug,
        }

        if compile_config.checkpointer:
            compile_kwargs["checkpointer"] = compile_config.checkpointer
        if compile_config.interrupt_before:
            compile_kwargs["interrupt_before"] = compile_config.interrupt_before
        if compile_config.interrupt_after:
            compile_kwargs["interrupt_after"] = compile_config.interrupt_after
        if compile_config.cache:
            compile_kwargs["cache"] = compile_config.cache
        compile_kwargs["recursion_limit"] = compile_config.recursion_limit

        try:
            compiled = base_graph.compile(**compile_kwargs)
            self._compiled = compiled
            return compiled
        except Exception as e:
            raise GraphValidationError(
                f"Failed to compile graph: {e}"
            ) from e

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_json(self) -> str:
        """
        Serialize the graph builder configuration to JSON.

        Note:
            Functions (callables) cannot be serialized.
            This returns the structural configuration only.

        Returns:
            JSON string representation of the graph structure.
        """
        data = {
            "name": self._name,
            "state_schema": str(self._state_schema),
            "nodes": [
                {"name": name, "config": item.config}
                for name, item in self._nodes.items()
            ],
            "edges": [edge.to_dict() for edge in self._edges],
            "conditional_edges": [
                {
                    "source": cond.source,
                    "mapping": cond.mapping,
                    "default": cond.default,
                }
                for cond in self._conditional_edges
            ],
            "entry_point": self._entry_point,
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(
        cls,
        json_str: str,
        node_functions: Dict[str, Callable[..., Any]],
        state_schema: Optional[type] = None,
        name: Optional[str] = None,
    ) -> "GraphBuilder":
        """
        Deserialize a GraphBuilder from JSON.

        Args:
            json_str: JSON string previously produced by to_json().
            node_functions: Dict mapping node names to callable functions.
            state_schema: State schema (required if not stored in JSON).
            name: Optional override for graph name.

        Returns:
            Reconstructed GraphBuilder instance.

        Raises:
            GraphValidationError: If JSON is malformed or functions missing.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise GraphValidationError(f"Invalid JSON: {e}") from e

        # Extract schema if not provided
        if state_schema is None:
            schema_repr = data.get("state_schema", "")
            raise GraphValidationError(
                f"state_schema is required to reconstruct GraphBuilder. "
                f"Got: {schema_repr}"
            )

        # Reconstruct builder
        graph_name = name or data.get("name", "graph")
        builder = cls(state_schema=state_schema, name=graph_name)

        # Re-add nodes
        for node_data in data.get("nodes", []):
            node_name = node_data["name"]
            if node_name not in node_functions:
                raise GraphValidationError(
                    f"Missing function for node '{node_name}'. "
                    f"Provided functions: {list(node_functions.keys())}"
                )
            builder.add_node(
                name=node_name,
                func=node_functions[node_name],
                config=node_data.get("config"),
            )

        # Re-add edges
        for edge_data in data.get("edges", []):
            builder.add_edge(edge_data["source"], edge_data["target"])

        # Re-add conditional edges (routing functions must be in node_functions)
        for cond_data in data.get("conditional_edges", []):
            source = cond_data["source"]
            routing_key = f"{source}_router"
            if routing_key not in node_functions:
                raise GraphValidationError(
                    f"Missing routing function for conditional edge from '{source}'. "
                    f"Expected key '{routing_key}' in node_functions."
                )
            builder.add_conditional_edges(
                source=source,
                routing_fn=node_functions[routing_key],
                mapping=cond_data.get("mapping", {}),
                default=cond_data.get("default"),
            )

        # Restore entry point
        if data.get("entry_point"):
            builder.set_entry_point(data["entry_point"])

        return builder

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Graph name."""
        return self._name

    @property
    def node_names(self) -> List[str]:
        """List of registered node names."""
        return list(self._nodes.keys())

    @property
    def compiled(self) -> Optional[CompiledStateGraph]:
        """Compiled graph if compile() has been called."""
        return self._compiled

    # -------------------------------------------------------------------------
    # Debugging
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"GraphBuilder(name={self._name!r}, "
            f"nodes={list(self._nodes.keys())}, "
            f"edges={len(self._edges)}, "
            f"conditional_edges={len(self._conditional_edges)}, "
            f"entry_point={self._entry_point!r})"
        )

    def describe(self) -> str:
        """
        Return a human-readable description of the graph structure.

        Returns:
            Multi-line string describing the graph.
        """
        lines = [f"Graph: {self._name}", "=" * 40]

        lines.append(f"\nNodes ({len(self._nodes)}):")
        for name in self._nodes:
            lines.append(f"  - {name}")

        if self._edges:
            lines.append(f"\nEdges ({len(self._edges)}):")
            for edge in self._edges:
                lines.append(f"  {edge.source} -> {edge.target}")

        if self._conditional_edges:
            lines.append(f"\nConditional Edges ({len(self._conditional_edges)}):")
            for cond in self._conditional_edges:
                targets = " | ".join(
                    f"{k}→{v}" for k, v in cond.mapping.items()
                )
                if cond.default:
                    targets += f" | DEFAULT→{cond.default}"
                lines.append(f"  {cond.source} --[{targets}]")

        if self._entry_point:
            lines.append(f"\nEntry Point: {self._entry_point}")

        return "\n".join(lines)