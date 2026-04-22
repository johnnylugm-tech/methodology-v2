# Feature #10: LangGraph Integration — Architecture

**Version:** 1.0.0
**Feature ID:** FR-10X
**Phase:** 02-architecture
**Author:** methodology-v2 Agent
**Date:** 2026-04-21
**Status:** Draft

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Components](#2-core-components)
3. [Data Flow](#3-data-flow)
4. [API Design](#4-api-design)
5. [Integration Points](#5-integration-points)
6. [Error Handling Strategy](#6-error-handling-strategy)
7. [File Structure](#7-file-structure)
8. [Dependencies](#8-dependencies)

---

## 1. Architecture Overview

### 1.1 High-Level Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        methodology-v2 Layer                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    User Code Layer                          │   │
│  │  (Hunter Agent, UQLM, Gap Detector, Risk Assessment)         │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  LangGraph Integration Layer                 │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │ GraphBuilder │  │   Executor   │  │  Checkpoint   │   │   │
│  │  │    (FR-101)  │  │   (FR-105)   │  │   Manager     │   │   │
│  │  └──────────────┘  └──────────────┘  │   (FR-106)   │   │   │
│  │                                      └──────────────┘   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │     State    │  │    Nodes     │  │   Tracing    │   │   │
│  │  │   (FR-104)   │  │   (FR-102)   │  │   (FR-108)   │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                             │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    LangGraph Core                          │   │
│  │         (StateGraph, CompiledGraph, Checkpointers)          │   │
│  └──────────────────────────┬────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Storage Layer                           │   │
│  │         (SQLite, FileSystem, or LangChain Memory)          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Description |
|-----------|-------------|
| **Non-invasive wrapping** | Existing framework components are wrapped as LangGraph nodes without modifying their internal logic |
| **Typed state contract** | All graph state is defined via Pydantic v2 model, making data flow explicit |
| **Configuration-driven** | Graph topology, retry policies, checkpoint intervals from YAML/JSON config |
| **Debuggable** | Every state transition is logged via ExecutionTracer |
| **Resilient by default** | Every node has built-in error handling with retry/fallback |

### 1.3 Component Responsibility Matrix

| Component | Responsibility | FR Mapping |
|-----------|----------------|-------------|
| `GraphBuilder` | Programmatic DAG construction | FR-101 |
| `AgentState` | Typed state schema and validation | FR-104 |
| `nodes.py` | Built-in node types (ToolNode, LLMNode, HILNode) | FR-102 |
| `edges.py` | Edge configuration and conditional routing | FR-103 |
| `CheckpointManager` | Save/restore graph execution state | FR-106 |
| `GraphRunner` | Execute compiled graph with error handling | FR-105 |
| `ExecutionTracer` | Log and trace state transitions | FR-108 |
| `config.py` | Load and validate configuration | FR-110 |

### 1.4 How LangGraph Fits into methodology-v2

```
Traditional Pipeline (Feature #08):
  Input → Node A → Node B → Node C → Output

LangGraph Pipeline (Feature #10):
  Input → Node A → [conditional] → Node B → Output
                    ↓
               Node C (parallel)

Multi-Agent Pipeline (with LangGraph):
  Input → [StateGraph]
              ├── Agent 1 (Hunter) ──→ Node B ──┐
              ├── Agent 2 (UQLM)   ──→ Node D ──┼──→ HIL ──→ Output
              └── Agent 3 (Risk)   ──→ Node F ──┘
```

---

## 2. Core Components

### 2.1 `builder.py` — GraphBuilder (FR-101)

**Purpose:** Provides the programmatic API for constructing LangGraph `StateGraph` instances.

**Class: `GraphBuilder`**

```python
from typing import Generic, TypeVar, Callable, Any
from pydantic import BaseModel

StateT = TypeVar("StateT", bound=BaseModel)

class GraphBuilder(Generic[StateT]):
    """Builds a LangGraph StateGraph with type-safe node and edge registration."""

    def __init__(
        self,
        state_schema: type[StateT],
        name: str = "main",
        config: GraphCompileConfig | None = None,
    ) -> None:
        """
        Initialize GraphBuilder.

        Args:
            state_schema: Pydantic model class for graph state.
            name: Graph name for identification.
            config: Optional compile-time configuration.
        """
        self._state_schema = state_schema
        self._name = name
        self._nodes: dict[str, NodeItem] = {}
        self._edges: list[EdgeItem] = []
        self._conditional_edges: list[ConditionalEdgeItem] = []
        self._compiled: CompiledStateGraph[StateT] | None = None

    def add_node(
        self,
        name: str,
        func: Callable[[StateT], StateT],
        config: NodeConfig | None = None,
    ) -> "GraphBuilder[StateT]":
        """
        Register a node in the graph.

        Args:
            name: Unique node identifier.
            func: Callable that receives state and returns state updates.
            config: Optional node configuration (retry, timeout, tags).

        Returns:
            self for method chaining.

        Raises:
            DuplicateNodeError: If node name already registered.
            StateSchemaError: If func signature doesn't match state schema.
        """
        if name in self._nodes:
            raise DuplicateNodeError(f"Node '{name}' already registered")

        # Validate function signature against state schema
        self._validate_node_signature(name, func)

        self._nodes[name] = NodeItem(func=func, config=config or NodeConfig())
        return self

    def add_edge(self, source: str, target: str) -> "GraphBuilder[StateT]":
        """Add a directed edge from source to target."""
        self._edges.append(EdgeItem(source=source, target=target))
        return self

    def add_conditional_edges(
        self,
        source: str,
        routing_fn: Callable[[StateT], str],
        mapping: dict[str, list[str]],
        default: str | None = None,
    ) -> "GraphBuilder[StateT]":
        """
        Add conditional edges from source.

        Args:
            source: Node emitting these edges.
            routing_fn: Function that receives state and returns route key.
            mapping: Maps route keys to lists of target node names.
            default: Fallback target if routing_fn returns unknown key.
        """
        self._conditional_edges.append(
            ConditionalEdgeItem(
                source=source,
                routing_fn=routing_fn,
                mapping=mapping,
                default=default,
            )
        )
        return self

    def compile(self, config: GraphCompileConfig | None = None) -> "CompiledStateGraph[StateT]":
        """
        Compile the graph into an executable form.

        Returns:
            CompiledStateGraph ready for invocation.

        Raises:
            OrphanedNodeError: If any node has no incoming edges (except START).
            CycleWithoutBoundError: If a cycle exists without max_cycle_count.
        """
        self._validate_graph_integrity()
        self._compiled = self._build_langgraph_stategraph(config or GraphCompileConfig())
        return self._compiled

    def _validate_graph_integrity(self) -> None:
        """Validate graph has no orphaned nodes or invalid cycles."""
        # Nodes with incoming edges
        nodes_with_incoming = {e.target for e in self._edges}
        for ce in self._conditional_edges:
            for targets in ce.mapping.values():
                nodes_with_incoming.update(targets)

        # Find orphaned nodes (not START, not END, no incoming edges)
        orphaned = set(self._nodes.keys()) - nodes_with_incoming
        if orphaned and not self._has_explicit_start(orphaned):
            raise OrphanedNodeError(f"Orphaned nodes found: {orphaned}")

    def _build_langgraph_stategraph(self, config: GraphCompileConfig) -> CompiledStateGraph[StateT]:
        """Build the underlying LangGraph StateGraph."""
        from langgraph.graph import StateGraph as LGStateGraph

        graph = LGStateGraph(self._state_schema, name=self._name)

        # Register nodes
        for name, item in self._nodes.items():
            graph.add_node(name, item.func)

        # Register edges
        for edge in self._edges:
            graph.add_edge(edge.source, edge.target)

        # Register conditional edges
        for ce in self._conditional_edges:
            graph.add_conditional_edges(
                ce.source,
                ce.routing_fn,
                ce.mapping,
            )

        # Add START and END
        graph.add_edge("__start__", self._get_entry_node())

        return graph.compile()

    def to_json(self) -> str:
        """Serialize graph definition to JSON."""
        import json
        return json.dumps(self._serialize(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "GraphBuilder[StateT]":
        """Deserialize graph definition from JSON."""
        import json
        data = json.loads(json_str)
        builder = cls.__new__(cls)
        builder._restore(data)
        return builder
```

**Internal Data Structures:**

```python
@dataclass
class NodeItem:
    func: Callable[[StateT], StateT]
    config: NodeConfig

@dataclass
class EdgeItem:
    source: str
    target: str

@dataclass
class ConditionalEdgeItem:
    source: str
    routing_fn: Callable[[StateT], str]
    mapping: dict[str, list[str]]
    default: str | None = None

@dataclass
class NodeConfig:
    description: str = ""
    retry_policy: RetryPolicy | None = None
    timeout_ms: int | None = None
    tags: list[str] = field(default_factory=list)
    human_in_the_loop: bool = False
    interrupt_before: list[str] = field(default_factory=list)
    interrupt_after: list[str] = field(default_factory=list)

@dataclass
class GraphCompileConfig:
    max_cycle_count: int | None = None
    enable_state_persistence: bool = False
    checkpoint_interval: int = 1
    debug: bool = False
```

---

### 2.2 `state.py` — AgentState Schema (FR-104)

**Purpose:** Defines the typed state schema that flows through all nodes in the graph.

**AgentState Model:**

```python
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime

class ErrorRecord(BaseModel):
    """Records a node execution error."""
    node_name: str
    error_type: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    retryable: bool = True
    context: dict[str, Any] = Field(default_factory=dict)

class CheckpointRecord(BaseModel):
    """Records a checkpoint snapshot."""
    checkpoint_id: str
    node_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    state_snapshot: dict[str, Any]

class AgentState(BaseModel):
    """
    The shared state that flows through all nodes in a LangGraph.

    This is the central data contract — every node receives this state
    and returns partial updates that get merged into the state.
    """
    # ─── Conversation / Messages ────────────────────────────────────────
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation history, appended by each node"
    )

    # ─── Shared Context ─────────────────────────────────────────────────
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared research context propagated across nodes"
    )

    # ─── Task Tracking ──────────────────────────────────────────────────
    current_task: str | None = Field(
        default=None,
        description="Active task description for the current node"
    )
    task_history: list[str] = Field(
        default_factory=list,
        description="Ordered list of task descriptions processed"
    )

    # ─── Node Outputs ───────────────────────────────────────────────────
    intermediate_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Results from each node, keyed by node name"
    )
    finalized_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Results approved for final output"
    )

    # ─── Error Tracking ──────────────────────────────────────────────────
    errors: list[ErrorRecord] = Field(
        default_factory=list,
        description="All errors encountered during graph execution"
    )
    retry_count: dict[str, int] = Field(
        default_factory=dict,
        description="Per-node retry attempt counters"
    )

    # ─── Control Flow ───────────────────────────────────────────────────
    checkpoint_stack: list[CheckpointRecord] = Field(
        default_factory=list,
        description="Stack of checkpoints for resume capability"
    )
    current_node: str | None = Field(
        default=None,
        description="Name of the currently executing node"
    )
    pending_human_review: bool = Field(
        default=False,
        description="True when graph is paused awaiting human input"
    )
    review_notes: str | None = Field(
        default=None,
        description="Human review notes when resuming from HIL"
    )

    # ─── Execution Metadata ──────────────────────────────────────────────
    execution_trace: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Full execution history for debugging"
    )
    node_tags: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Tags associated with node executions"
    )

    # ─── Configuration ───────────────────────────────────────────────────
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Graph-level configuration overrides"
    )
```

**StateManager Class:**

```python
class StateManager:
    """
    Manages state transitions and validation for AgentState.

    Responsible for:
    - Merging partial state updates from nodes
    - Validating state transitions
    - Managing checkpoint stack
    - Tracking execution metadata
    """

    def __init__(self, initial_state: AgentState | None = None):
        self._state = initial_state or AgentState()
        self._history: list[AgentState] = []

    @property
    def state(self) -> AgentState:
        """Current state."""
        return self._state

    def update(self, partial: dict[str, Any]) -> AgentState:
        """
        Merge partial state update from a node.

        Args:
            partial: Partial state dict returned by a node.

        Returns:
            Updated full state.
        """
        # Save history for undo
        self._history.append(self._state.model_copy(deep=True))

        # Merge with validation
        for key, value in partial.items():
            if hasattr(self._state, key):
                current = getattr(self._state, key)
                if isinstance(current, list) and isinstance(value, list):
                    # Append lists (messages, errors, etc.)
                    getattr(self._state, key).extend(value)
                elif isinstance(current, dict) and isinstance(value, dict):
                    # Deep merge dicts
                    getattr(self._state, key).update(value)
                else:
                    setattr(self._state, key, value)
            else:
                # Allow extending state with custom fields
                self._state.config[key] = value

        return self._state

    def push_checkpoint(self, node_name: str) -> str:
        """Create a checkpoint and return its ID."""
        import uuid
        checkpoint_id = str(uuid.uuid4())[:8]
        record = CheckpointRecord(
            checkpoint_id=checkpoint_id,
            node_name=node_name,
            state_snapshot=self._state.model_dump(mode="json"),
        )
        self._state.checkpoint_stack.append(record)
        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> AgentState:
        """Restore state from a checkpoint."""
        for record in reversed(self._state.checkpoint_stack):
            if record.checkpoint_id == checkpoint_id:
                # Reconstruct state from snapshot
                self._state = AgentState.model_validate(record.state_snapshot)
                return self._state
        raise ValueError(f"Checkpoint '{checkpoint_id}' not found")

    def record_error(self, node_name: str, error: Exception) -> None:
        """Record an error from a node."""
        self._state.errors.append(ErrorRecord(
            node_name=node_name,
            error_type=type(error).__name__,
            error_message=str(error),
        ))
        self._state.retry_count[node_name] = self._state.retry_count.get(node_name, 0) + 1

    def can_retry(self, node_name: str, policy: RetryPolicy) -> bool:
        """Check if a node can be retried based on its policy."""
        attempts = self._state.retry_count.get(node_name, 0)
        return attempts < policy.max_attempts
```

---

## 3. Data Flow

### 3.1 State Flow Through a Graph

```
                    ┌──────────────────────────────────┐
                    │         Graph Execution          │
                    │                                  │
  Input ────────────▶  AgentState                     │
                    │     │                             │
                    │     ▼                             │
                    │  ┌─────────────┐                 │
                    │  │   Node A    │◄──────────────│
                    │  │ (updates    │  AgentState   │
                    │  │  partial)   │                 │
                    │  └──────┬──────┘                 │
                    │         │                        │
                    │         │ AgentState            │
                    │         ▼                        │
                    │  ┌─────────────┐                 │
                    │  │  Edge Router│                 │
                    │  └──────┬──────┘                 │
                    │         │                        │
                    │    ┌────┴────┐                   │
                    │    ▼         ▼                   │
                    │ ┌──────┐ ┌──────┐                │
                    │ │Node B│ │Node C│  (parallel)   │
                    │ └──────┘ └──────┘                │
                    │    │         │                   │
                    │    └────┬────┘                   │
                    │         │ AgentState            │
                    │         ▼                        │
                    │  ┌─────────────┐                 │
                    │  │  Aggregator │                 │
                    │  └──────┬──────┘                 │
                    │         │                        │
                    │    Checkpoint (optional)         │
                    │         │                        │
                    │         ▼                        │
                    │    Output / HIL Pause            │
                    │                                  │
                    └──────────────────────────────────┘
```

### 3.2 Checkpoint Timing

| Timing | Trigger | Action |
|--------|---------|--------|
| Before node execution | Node starts | `state_manager.push_checkpoint()` if node is checkpointable |
| After successful node | Node completes | Update state, merge partial results |
| On error | Node raises | `state_manager.record_error()`, check retry policy |
| Before HIL pause | `interrupt_before` node | Freeze state, await external input |
| After HIL resume | Human provides input | Merge `review_notes` into state |

### 3.3 State Update Merge Rules

| Field Type | Merge Strategy |
|-----------|-----------------|
| `list[messages]` | Extend (append new items) |
| `dict[intermediate_results]` | Shallow merge (node keys) |
| `dict[context]` | Deep merge |
| `list[errors]` | Append new errors |
| `dict[retry_count]` | Set max (per node) |
| Scalar fields | Overwrite |

---

## 4. API Design

### 4.1 High-Level Usage API

```python
from langgraph import GraphBuilder, AgentState, GraphCompileConfig
from langgraph.nodes import ToolNode, LLMNode
from langgraph.edges import conditional_edge

# 1. Define state schema
class MyState(AgentState):
    query: str
    search_results: list[str] = []
    final_answer: str | None = None

# 2. Define nodes
def search_node(state: MyState) -> MyState:
    results = search_tool(state["query"])
    return {"search_results": results}

def answer_node(state: MyState) -> MyState:
    answer = llm_answer(state["query"], state["search_results"])
    return {"final_answer": answer}

# 3. Build graph
graph = (
    GraphBuilder(state_schema=MyState, name="research-graph")
    .add_node("search", search_node)
    .add_node("answer", answer_node)
    .add_edge("__start__", "search")
    .add_edge("search", "answer")
    .add_edge("answer", "__end__")
    .compile()
)

# 4. Execute
result = graph.invoke({"query": "What is LangGraph?"})
print(result["final_answer"])
```

### 4.2 Conditional Routing API

```python
def route_by_confidence(state: MyState) -> str:
    if len(state["search_results"]) >= 5:
        return "has_results"
    return "no_results"

graph = (
    GraphBuilder(state_schema=MyState)
    .add_node("search", search_node)
    .add_node("expand", expand_node)
    .add_node("answer", answer_node)
    .add_conditional_edges(
        source="search",
        routing_fn=route_by_confidence,
        mapping={
            "has_results": ["answer"],
            "no_results": ["expand"],
        },
        default="no_results",
    )
    .add_edge("expand", "search")  # Re-run search
    .add_edge("answer", "__end__")
    .compile()
)
```

### 4.3 Checkpoint/Resume API

```python
# Save checkpoint
checkpoint_id = graph.checkpoint(state, "before-hil-node")

# Resume from checkpoint
result = graph.resume(checkpoint_id, {"review_notes": "Approved with edits"})
```

### 4.4 Node Configuration API

```python
from langgraph.config import RetryPolicy, NodeConfig

retry_3x = RetryPolicy(max_attempts=3, backoff="exponential", initial_delay_ms=500)

graph = (
    GraphBuilder(state_schema=MyState)
    .add_node(
        "search",
        search_node,
        config=NodeConfig(
            description="Web search node",
            retry_policy=retry_3x,
            timeout_ms=30000,
            tags=["search", "external"],
        ),
    )
    .add_node(
        "answer",
        answer_node,
        config=NodeConfig(
            description="LLM answer generation",
            human_in_the_loop=True,
            interrupt_before=["answer"],  # Pause before this node
        ),
    )
    .compile()
)
```

---

## 5. Integration Points

### 5.1 With Feature #06 (Hunter Agent)

```
Hunter Agent (Feature #06) → Wrapped as ToolNode
    │
    ├── Input: State.context["hunting_targets"]
    ├── Output: State.intermediate_results["hunter"] = {found_items: [...], metadata: {...}}
    └── Integration: HunterNode(hunter_agent_instance)

graph = (
    GraphBuilder(state_schema=AgentState)
    .add_node("hunter", HunterNode(agent=hunter_agent))
    .add_edge("__start__", "hunter")
    ...
)
```

### 5.2 With Feature #07 (UQLM)

```
UQLM (Feature #07) → Wrapped as LLMNode with structured output
    │
    ├── Input: State.intermediate_results["hunter"]
    ├── Output: State.intermediate_results["uqlm"] = {structured_items: [...], confidence: float}
    └── Integration: UQLMNode(uqlm_instance)

graph = (
    GraphBuilder(state_schema=AgentState)
    .add_node("uqlm", UQLMNode(model=uqlm_model))
    .add_edge("hunter", "uqlm")
    ...
)
```

### 5.3 With Feature #08 (Gap Detector)

```
Gap Detector (Feature #08) → Wrapped as ToolNode
    │
    ├── Input: State.finalized_results, State.context["coverage_map"]
    ├── Output: State.intermediate_results["gap_detector"] = {gaps: [...], coverage_pct: float}
    └── Integration: GapDetectorNode(gap_detector_instance)
```

### 5.4 With Feature #09 (Risk Assessment)

```
Risk Assessment (Feature #09) → Wrapped as ToolNode
    │
    ├── Input: State.finalized_results, State.intermediate_results["gap_detector"]
    ├── Output: State.intermediate_results["risk_assessment"] = {risks: [...], risk_score: float}
    └── Integration: RiskAssessmentNode(risk_assessor_instance)
```

### 5.5 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline                            │
│                                                                   │
│  START ──▶ Hunter ──▶ UQLM ──▶ Gap ──▶ Risk ──▶ HIL ──▶ END   │
│               │        │       │      │       │               │
│               ▼        ▼       ▼      ▼       ▼               │
│          [FR-102]  [FR-102] [FR-102] [FR-102] [FR-102]         │
│          ToolNode  LLMNode  ToolNode ToolNode HILNode           │
│              ▲        ▲       ▲      ▲       ▲                 │
│              │        │       │      │       │                 │
│         Hunter    UQLM    Gap     Risk   (external)            │
│         Agent     Model  Detector Assessor  Human                │
│         (#06)     (#07)  (#08)   (#09)                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Error Handling Strategy

### 6.1 Node Failure Flow

```
Node Execution
      │
      ▼
 ┌─────────┐
 │ Success │ ────────────────────▶ Next Node
 └────┬────┘
      │
      │ Exception
      ▼
 ┌─────────────────┐
 │ Record Error    │ ──▶ state.errors.append()
 │ Increment Retry │ ──▶ state.retry_count[node]++
 └────────┬────────┘
          │
          ▼
    ┌─────────────────┐
    │ Within Retry    │ ──yes──▶ Wait (backoff) ──▶ Re-execute node
    │ Policy Limits?  │
    └────────┬────────┘
             │ no
             ▼
    ┌─────────────────┐
    │ Mark as Failed  │
    │ Apply Fallback  │ ──▶ Execute fallback node or use cached result
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ Save Dead Letter│ ──▶ state.errors[last] with retryable=False
    │ (if configured)│
    └─────────────────┘
```

### 6.2 Retry Policy Configuration

```python
@dataclass
class RetryPolicy:
    """Configuration for node retry behavior."""
    max_attempts: int = 3
    backoff: Literal["exponential", "linear", "fixed"] = "exponential"
    initial_delay_ms: int = 500
    max_delay_ms: int = 30000
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        if self.backoff == "fixed":
            return self.initial_delay_ms / 1000
        elif self.backoff == "linear":
            return (self.initial_delay_ms * attempt) / 1000
        else:  # exponential
            delay = self.initial_delay_ms * (2 ** (attempt - 1))
            return min(delay, self.max_delay_ms) / 1000
```

### 6.3 Infinite Loop Detection

```python
class CycleDetector:
    """Detects and prevents infinite loops in graph execution."""

    def __init__(self, max_cycle_count: int = 100):
        self._max_cycle_count = max_cycle_count
        self._visit_counts: dict[str, int] = {}

    def record_visit(self, node_name: str) -> None:
        """Record a node visit and check for cycles."""
        self._visit_counts[node_name] = self._visit_counts.get(node_name, 0) + 1
        if self._visit_counts[node_name] > self._max_cycle_count:
            raise CycleExceededError(
                f"Node '{node_name}' visited {self._visit_counts[node_name]} times. "
                f"Max cycle count ({self._max_cycle_count}) exceeded."
            )

    def reset(self) -> None:
        """Reset visit counts for new graph execution."""
        self._visit_counts.clear()
```

### 6.4 Timeout Handling

```python
import signal
from contextlib import contextmanager

class TimeoutError(Exception):
    """Raised when a node exceeds its timeout."""

@contextmanager
def timeout_context(seconds: int, node_name: str):
    def handler(signum, frame):
        raise TimeoutError(f"Node '{node_name}' timed out after {seconds}s")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
```

---

## 7. File Structure

```
implement/feature-10-langgraph/
└── 03-implement/
    └── langgraph/
        ├── __init__.py              # Public API exports
        ├── builder.py               # GraphBuilder class (FR-101)
        ├── state.py                 # AgentState + StateManager (FR-104)
        ├── nodes.py                 # Built-in node types (FR-102)
        ├── edges.py                 # Edge configs (FR-103)
        ├── checkpoint.py            # CheckpointManager (FR-106)
        ├── executor.py              # GraphRunner (FR-105)
        ├── routing.py              # Conditional routing (FR-105)
        ├── tracing.py              # ExecutionTracer (FR-108)
        ├── exceptions.py           # Custom exceptions
        ├── config.py               # Config loading (FR-110)
        └── utils.py                # Shared utilities
```

### 7.1 Module Purpose Matrix

| File | Classes/Functions | FR |
|------|------------------|-----|
| `__init__.py` | `GraphBuilder`, `AgentState`, `ToolNode`, etc. | all |
| `builder.py` | `GraphBuilder`, `NodeItem`, `EdgeItem`, `GraphCompileConfig` | FR-101 |
| `state.py` | `AgentState`, `StateManager`, `ErrorRecord`, `CheckpointRecord` | FR-104 |
| `nodes.py` | `ToolNode`, `LLMNode`, `HumanInTheLoopNode`, `ConditionalRouterNode` | FR-102 |
| `edges.py` | `EdgeItem`, `ConditionalEdgeItem`, routing helpers | FR-103 |
| `checkpoint.py` | `CheckpointManager`, `MemoryCheckpoint`, `SqliteCheckpoint` | FR-106 |
| `executor.py` | `GraphRunner`, `ExecutionResult` | FR-105 |
| `routing.py` | `RouterFunction`, route utilities | FR-105 |
| `tracing.py` | `ExecutionTracer`, `TraceRecord`, `Span` | FR-108 |
| `exceptions.py` | `DuplicateNodeError`, `OrphanedNodeError`, `CycleExceededError`, etc. | all |
| `config.py` | `load_config`, `GraphConfig`, `NodeConfig` | FR-110 |

---

## 8. Dependencies

### 8.1 External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | >= 0.2.0 | Core graph execution engine |
| `langchain-core` | >= 0.3.0 | Base types for LangChain integration |
| `pydantic` | >= 2.0 | State schema validation |
| `pyyaml` | >= 6.0 | Configuration file loading |

### 8.2 Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain-openai` | >= 0.2.0 | OpenAI LLM integration for LLMNode |
| `langchain-anthropic` | >= 0.2.0 | Anthropic LLM integration |
| `aiosqlite` | >= 0.20 | Async SQLite for checkpoint storage |

### 8.3 Internal Dependencies (v3 Features)

| Feature | Module | Integration Point |
|---------|--------|-------------------|
| #06 Hunter Agent | `implement.feature_06_hunter` | Wrapped as `ToolNode` |
| #07 UQLM | `implement.feature_07_uqlm` | Wrapped as `LLMNode` |
| #08 Gap Detector | `implement.feature_08_gap_detector` | Wrapped as `ToolNode` |
| #09 Risk Assessment | `implement.feature_09_risk_assessment` | Wrapped as `ToolNode` |

### 8.4 Dependency Graph

```
langgraph/
│
├── builder.py ──────────────────────► langgraph.state
├── state.py ◄───────────────────────► langgraph.builder
├── nodes.py ────────────────────────► langgraph.state, langgraph.builder
├── edges.py ◄──────────────────────► langgraph.builder
├── executor.py ─────────────────────► langgraph.state, langgraph.checkpoint, langgraph.tracing
├── checkpoint.py ──────────────────► langgraph.state
├── routing.py ◄────────────────────► langgraph.edges
├── tracing.py ◄────────────────────► langgraph.state
└── config.py ◄────────────────────► all modules

External:
  langgraph.nodes.* ────────────────► langgraph (upstream)
  pydantic ─────────────────────────► all modules (validation)
  pyyaml ────────────────────────────► langgraph.config
```

---

*End of ARCHITECTURE.md — Feature #10 Phase 02-architecture*
