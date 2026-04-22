# Feature #10: LangGraph Integration — Specification

**Version:** 1.0.0  
**Feature ID:** FR-10X  
**Phase:** 01-spec  
**Author:** methodology-v2 Agent  
**Date:** 2026-04-21  
**Status:** Draft  

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Functional Requirements](#2-functional-requirements)
3. [Non-Functional Requirements](#3-non-functional-requirements)
4. [User Scenarios](#4-user-scenarios)
5. [Dependencies](#5-dependencies)
6. [Out of Scope](#6-out-of-scope)
7. [Glossary](#7-glossary)

---

## 1. Feature Overview

### 1.1 What is LangGraph?

LangGraph is a library built on top of LangChain that enables the construction of **stateful, multi-actor applications** through directed acyclic graph (DAG)-based workflows. Unlike traditional linear chains (LangChain Chains), LangGraph introduces:

- **Graph-based execution model**: Nodes represent computational steps; edges represent data flow and control flow.
- **Persistent state across steps**: A shared `State` object flows through the graph, mutated by each node.
- **Cycles support**: Unlike DAGs, LangGraph allows conditional loops — essential for iterative refinement, retry logic, and agentic loops.
- **Checkpointing and memory**: Built-in support for saving and resuming graph execution state.

LangGraph is the graph computation backbone that powers complex agentic systems where multiple actors (tools, models, human-in-the-loop nodes) interact, share state, branch conditionally, and recover from failures.

### 1.2 Why Integrate LangGraph into methodology-v2?

methodology-v2 is a framework for building AI-driven research and analysis pipelines. As the framework evolves from linear workflows (Feature #08) to more complex agentic behaviors, it needs:

| Capability Gap | How LangGraph Fills It |
|----------------|------------------------|
| Non-linear execution paths | Conditional edges route execution based on state |
| Shared state across pipeline stages | Graph-level `State` object propagates context |
| Iterative refinement loops | Cycles enable "generate → review → revise" patterns |
| Failure isolation and recovery | Nodes fail independently; graph resumes from checkpoint |
| Auditability and traceability | All state transitions are logged |
| Human-in-the-loop pauses | `interrupt` nodes halt graph for external input |

LangGraph integration positions methodology-v2 for advanced agentic use cases: multi-agent research teams, self-correcting pipelines, and interactive analysis sessions.

### 1.3 Core Concepts

#### 1.3.1 Graph Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      StateGraph                            │
│                                                             │
│   ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐   │
│   │ Node A │───▶│ Node B │───▶│ Node C │───▶│ Node D │   │
│   └────────┘    └────────┘    └────────┘    └────────┘   │
│                    │                           │           │
│                    ▼                           ▼           │
│              ┌────────┐                   ┌────────┐      │
│              │ Node E │                   │ Node F  │      │
│              └────────┘                   └────────┘      │
│                                                             │
│   Conditional edges: B → {E, F} based on state.condition  │
└─────────────────────────────────────────────────────────────┘
```

#### 1.3.2 Key LangGraph Primitives

| Primitive | Description |
|-----------|-------------|
| `StateGraph` | The main graph container that holds nodes and edges |
| `State` | A TypedDict or Pydantic model shared across all nodes |
| `Node` | A Python function that receives state, optionally calls tools/LLM, returns state updates |
| `Edge` | Directional connection between nodes (`START`, `END`, or another node) |
| `ConditionalEdge` | Edge whose destination is determined by a routing function |
| `Command` | Used to interrupt and resume graph execution |
| `checkpoint` | Persisted snapshot of graph state for resume |

#### 1.3.3 State Flow Example

```python
class AgentState(TypedDict):
    messages: list[BaseMessage]       # Conversation history
    context: dict                     # Shared research context
    current_task: str                 # Active task description
    intermediate_results: dict        # Node outputs
    errors: list[ErrorRecord]         # Captured errors
    retry_count: dict                 # Per-node retry counters
    checkpoints: list[str]            # Snapshot IDs

def node_a(state: AgentState) -> AgentState:
    result = do_something(state["current_task"])
    return {"intermediate_results": {"a": result}}

def node_b(state: AgentState) -> AgentState:
    result = process_a_output(state["intermediate_results"]["a"])
    return {"intermediate_results": {"b": result}}
```

### 1.4 Design Philosophy

The LangGraph integration follows these principles:

1. **Non-invasive**: Existing pipeline components (Hunter Agent, UQLM, evaluator agents) are wrapped as LangGraph nodes without refactoring their internal logic.
2. **Typed state contract**: All graph state is defined via a Pydantic/TypedDict schema, making data flow explicit and statically analyzable.
3. **Configuration-driven**: Graph topology, retry policies, and checkpoint intervals are defined in YAML/JSON config files, not hardcoded.
4. **Debuggable**: Every state transition is traceable; execution history is queryable.
5. **Resilient by default**: Every node has built-in error handling, with configurable retry and fallback strategies.

---

## 2. Functional Requirements

### [FR-101] Graph Definition API

**Description:** The framework MUST provide a programmatic API for defining LangGraph `StateGraph` instances with type-safe node and edge registration.

**Acceptance Criteria:**

- [ ] `GraphBuilder` class accepts a Pydantic `AgentState` model as its state schema
- [ ] Nodes are registered via `graph_builder.add_node(name, func, config?)` where `func` is a callable `Callable[[AgentState], AgentState]`
- [ ] Edges are added via `graph_builder.add_edge(source, target)` for direct edges
- [ ] Conditional edges are added via `graph_builder.add_conditional_edges(source, routing_fn, mapping)` where `mapping: dict[str, list[str]]` maps route names to target node lists
- [ ] Special nodes `START` and `END` are implicitly available
- [ ] `graph_builder.compile()` returns a `CompiledStateGraph` ready for invocation
- [ ] Graph definition is serializable to and deserializable from a JSON/YAML representation
- [ ] Type hints are enforced at registration time (mypy/Pyright compatible)

**API Surface:**

```python
class GraphBuilder(Generic[StateT]):
    def __init__(self, state_schema: type[StateT], name: str = "main") -> None: ...
    def add_node(self, name: str, func: NodeFunction[StateT], config?: NodeConfig) -> GraphBuilder[StateT]: ...
    def add_edge(self, source: str, target: str) -> GraphBuilder[StateT]: ...
    def add_conditional_edges(
        self,
        source: str,
        routing_fn: RoutingFunction[StateT],
        mapping: dict[str, list[str]]
    ) -> GraphBuilder[StateT]: ...
    def add_health_check(self, node_name: str, health_fn: Callable[[StateT], bool]) -> GraphBuilder[StateT]: ...
    def compile(self, config?: GraphCompileConfig) -> CompiledStateGraph[StateT]: ...
    def to_json(self) -> str: ...
    @classmethod
    def from_json(cls, json_str: str) -> GraphBuilder[StateT]: ...
```

**Rationale:** Provides the foundational API for constructing any LangGraph workflow. The generic `StateT` ensures type safety across the entire graph lifecycle.

---

### [FR-102] Node Registration

**Description:** The framework MUST support registering nodes with rich metadata including description, retry policy, timeout, and optional health checks.

**Acceptance Criteria:**

- [ ] Nodes can be registered with a `description` string used for auto-documentation and tracing
- [ ] Each node can have an individual `retry_policy` dict: `{"max_attempts": int, "backoff": "exponential|linear", "initial_delay_ms": int}`
- [ ] Nodes can specify a `timeout_ms` after which the node execution is cancelled
- [ ] Nodes can be annotated with `tags: list[str]` for filtering during execution tracing
- [ ] Built-in wrapper nodes are provided: `ToolNode`, `LLMNode`, `HumanInTheLoopNode`, `ConditionalRouterNode`
- [ ] Custom node types can be registered via a plugin registry pattern
- [ ] Node registration validates that function signatures match the state schema (input keys must exist in state, output keys must be assignable)
- [ ] Duplicate node name registration raises `DuplicateNodeError`

**Node Metadata Schema:**

```python
@dataclass
class NodeConfig:
    description: str = ""
    retry_policy: RetryPolicy | None = None
    timeout_ms: int | None = None
    tags: list[str] = field(default_factory=list)
    human_in_the_loop: bool = False
    interrupt_before: list[str] = field(default_factory=list)  # node names to interrupt before
    interrupt_after: list[str] = field(default_factory=list)   # node names to interrupt after
```

**Rationale:** Rich node metadata enables operational concerns (retries, timeouts, tracing) to be separated from business logic, keeping nodes pure and testable.

---

### [FR-103] Edge Configuration

**Description:** The framework MUST provide flexible edge configuration including directed edges, conditional edges, entry/exit point configuration, and edge metadata.

**Acceptance Criteria:**

- [ ] Direct edges connect exactly two nodes: `add_edge("node_a", "node_b")`
- [ ] Multiple outgoing edges from a single node are allowed (parallel fan-out)
- [ ] Multiple incoming edges to a single node are allowed (parallel fan-in)
- [ ] Conditional edges select among multiple targets based on a routing function return value
- [ ] Routing functions receive `(state: AgentState) -> str` and return a route key present in the mapping dict
- [ ] Default edge routing is supported: if routing function returns a key not in mapping, a `default` fallback target is used
- [ ] `START` pseudo-node can be connected to any node(s) as entry points
- [ ] `END` pseudo-node can be connected from any node(s) as terminal points
- [ ] Multiple `END` connections are allowed (graph can terminate from different nodes)
- [ ] Edge metadata (description, condition description) can be attached for tracing
- [ ] Circular references are allowed only within bounded retry loops (configurable max cycle count)
- [ ] Disconnected nodes in a compiled graph raise `OrphanedNodeError`

**Conditional Edge Example:**

```python
def route_based_on_confidence(state: AgentState) -> str:
    score = state["intermediate_results"].get("confidence_score", 0.0)
    if score >= 0.9:
        return "high_confidence"
    elif score >= 0.7:
        return "medium_confidence"
    else:
        return "low_confidence"

graph.add_conditional_edges(
    source="evaluation",
    routing_fn=route_based_on_confidence,
    mapping={
        "high_confidence": ["finalize"],
        "medium_confidence": ["human_review"],
        "low_confidence": ["retry_generation"]
    },
    default="low_confidence"
)
```

**Rationale:** Conditional edges are essential for agentic workflows where different paths are taken based on intermediate results (e.g., confidence scores, tool outputs, user preferences).

---

### [FR-104] State Schema Definition

**Description:** The framework MUST provide a typed, versioned, and extensible state schema system that all nodes use for input/output.

**Acceptance Criteria:**

- [ ] State schema is defined as a Pydantic v2 model or TypedDict with field-level type annotations
- [ ] Required fields are enforced at graph compilation time and runtime entry
- [ ] Optional fields have default values; missing output keys from a node do not remove existing state values
- [ ] `StateValidator` class validates state transitions after each node execution
- [ ] State schema versioning is supported: `state_schema_version: str` field in state allows forward/backward compatibility handling
- [ ] Nodes declare which state keys they `read` and which they `write` via type-annotated `StateReads` / `StateWrites` decorators or class attributes
- [ ] Read-only access violation (node writes to a key it didn't declare) raises `StateAccessViolation`
- [ ] Built-in state fields always present:
    - `messages: list[BaseMessage]` — conversation history
    - `context: dict[str, Any]` — shared research context
    - `errors: list[ErrorRecord]` — accumulated errors
    - `metadata: StateMetadata` — graph name, run id, timestamps
- [ ] Custom state fields can be added via config or subclassing
- [ ] State snapshots (checkpoints) preserve the full state object

**State Schema Example:**

```python
from pydantic import BaseModel, Field
from typing import Annotated, Any
from langgraph.graph import add_messages

class ErrorRecord(BaseModel):
    node_name: str
    error_type: str
    error_message: str
    timestamp: datetime
    recoverable: bool = True

class StateMetadata(BaseModel):
    graph_name: str
    run_id: str
    step_count: int = 0
    state_schema_version: str = "1.0"

class AgentState(BaseModel):
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    current_task: str = ""
    intermediate_results: dict[str, Any] = Field(default_factory=dict)
    errors: list[ErrorRecord] = Field(default_factory=list)
    retry_count: dict[str, int] = Field(default_factory=dict)
    metadata: StateMetadata = Field(default_factory=StateMetadata)
```

**Rationale:** A well-defined, enforced state schema prevents subtle bugs from misaligned state keys between nodes and provides a clear contract for node authors.

---

### [FR-105] Conditional Routing

**Description:** The framework MUST support expressive conditional routing based on state values, with support for combinators, priority ordering, and default fallbacks.

**Acceptance Criteria:**

- [ ] Routing functions are pure functions: `(state: AgentState) -> str` returning a route key
- [ ] Combinator helpers are provided: `any_of(*routing_fns)`, `all_of(*routing_fns)`, `priority_of(*routing_fns, default=...)`
- [ ] Pre-built route evaluators for common patterns:
    - `route_by_threshold(state, key, thresholds: list[tuple[float, str]])`
    - `route_by_value(state, key, mapping: dict[Any, str])`
    - `route_by_error_count(state, threshold: int, error_node: str)`
    - `route_by_message_type(state, message_type: type) -> str`
- [ ] Route functions are traceable: each invocation logs input state hash, output route, and evaluation time
- [ ] Unreachable routes (no node maps to returned key) raise `UnreachableRouteError` at runtime
- [ ] Cycles are detected and prevented at compile time unless `allow_cycles: bool` is set in config
- [ ] Max cycle count can be enforced: after N cycles through the same path, graph terminates or routes to error handler

**Routing Combinator Example:**

```python
from methodology_v2.langgraph.routing import route_by_threshold, any_of, priority_of

def complex_router(state: AgentState) -> str:
    return priority_of(
        route_by_error_count(state, threshold=3, error_node="generation"),
        route_by_threshold(state, "confidence_score", [
            (0.95, "finalize"),
            (0.80, "light_review"),
            (0.60, "heavy_review"),
        ]),
        default="human_review"
    )(state)
```

**Rationale:** Complex workflows require sophisticated routing logic. Providing combinators and pre-built evaluators reduces boilerplate and standardizes routing patterns across the codebase.

---

### [FR-106] Checkpoint / Resume

**Description:** The framework MUST provide persistent checkpointing that allows graph execution to be paused, saved, and later resumed from the exact saved state.

**Acceptance Criteria:**

- [ ] Checkpoints are created automatically at configurable intervals: every N steps, or after each node, or only at `checkpoint` nodes
- [ ] Manual checkpoint creation is triggered via `graph.checkpoint()` or state update with `{"_checkpoint": True}`
- [ ] Checkpoint storage backends: `MemorySaver` (in-process), `SQLiteSaver`, `PostgresSaver` (for distributed scenarios)
- [ ] Each checkpoint stores: full state object, current node name, step count, run_id, timestamp, parent checkpoint ID
- [ ] `graph.resume(checkpoint_id: str)` restores state and continues execution from the interrupted node
- [ ] Checkpoint metadata is queryable: list all checkpoints for a run, filter by timestamp, step count
- [ ] Checkpoints can be exported to and imported from JSON for debugging and audit
- [ ] Checkpoint retention policy: configurable max checkpoints per run; old checkpoints are pruned
- [ ] Resume with outdated checkpoint (state schema mismatch) attempts migration via registered migration functions
- [ ] Concurrent resume attempts on the same checkpoint are serialized (lock mechanism)

**Checkpoint API:**

```python
class CheckpointManager(Generic[StateT]):
    def checkpoint(self, state: StateT, node_name: str, metadata: CheckpointMetadata) -> str: ...
    def resume(self, checkpoint_id: str) -> StateT: ...
    def list_checkpoints(self, run_id: str, limit?: int) -> list[CheckpointRecord]: ...
    def delete_checkpoint(self, checkpoint_id: str) -> None: ...
    def export_checkpoint(self, checkpoint_id: str) -> dict: ...
    def import_checkpoint(self, data: dict) -> str: ...

# Usage
graph = builder.compile(checkpointer=PostgresSaver(conn_string))
checkpoint_id = graph.checkpoint()  # manual checkpoint
result = graph.resume(checkpoint_id)
```

**Rationale:** Checkpointing is essential for long-running research pipelines where intermediate results need to be preserved against crashes, timeouts, or user-initiated pauses for review.

---

### [FR-107] Error Handling and Retries

**Description:** The framework MUST implement a comprehensive error handling and retry system where nodes can fail gracefully without crashing the entire graph.

**Acceptance Criteria:**

- [ ] Node-level error handling: unhandled exceptions in a node are caught, recorded in `state.errors`, and optionally trigger retry
- [ ] Retry policy per node: `max_attempts`, `backoff_strategy` (exponential, linear, jitter), `retry_on` (list of exception types to retry on)
- [ ] Circuit breaker pattern: if a node fails N times consecutively, it is "open" and bypassed for subsequent calls (fallback path used)
- [ ] Fallback nodes: when a node fails or is bypassed, execution can route to a designated `fallback_node`
- [ ] Global error policy: `on_node_error: "retry" | "fallback" | "skip" | "halt"` configurable per graph
- [ ] Error classification: `ErrorRecord.recoverable: bool` distinguishes recoverable (network timeout) from non-recoverable (TypeError, assertion) errors
- [ ] Dead letter queue (DLQ): failed steps after all retries are appended to a DLQ for later inspection
- [ ] `halt_on_error` mode stops the graph and returns current state with error details when any node fails
- [ ] Error events are emitted to the tracing system (see [FR-108])
- [ ] Timeout handling: nodes that exceed `timeout_ms` are cancelled (thread interruption or asyncio timeout) and treated as failures

**Error Handling Config:**

```python
@dataclass
class ErrorPolicy:
    on_node_error: Literal["retry", "fallback", "skip", "halt"] = "retry"
    default_retry_policy: RetryPolicy = field(
        default_factory=lambda: RetryPolicy(
            max_attempts=3,
            backoff="exponential",
            initial_delay_ms=1000,
            max_delay_ms=30000,
        )
    )
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_ms: int = 60000
    dead_letter_queue: bool = True
    halt_on_non_recoverable: bool = True

@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff: Literal["exponential", "linear", "jitter"] = "exponential"
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    retry_on: list[type[Exception]] = field(default_factory=lambda: [Exception])
```

**Rationale:** Resilient error handling distinguishes production-grade workflows from fragile scripts. Nodes should be able to fail without losing the entire pipeline's progress.

---

### [FR-108] Execution Tracing

**Description:** The framework MUST provide comprehensive execution tracing that records every state transition, node invocation, and error for debugging, audit, and performance analysis.

**Acceptance Criteria:**

- [ ] Each node invocation generates a `NodeTrace` record: `node_name`, `input_state_hash`, `output_state_hash`, `start_time`, `end_time`, `duration_ms`, `status: success|failure|retry|skipped`, `error: ErrorRecord | None`
- [ ] Each state transition generates a `StateTransition` record: `from_state_hash`, `to_state_hash`, `changed_keys: list[str]`, `trigger_node`, `timestamp`
- [ ] Traces are emitted to configurable sinks: in-memory (for testing), stdout (for development), OTLP-compatible endpoint (for production), LangSmith (optional integration)
- [ ] Trace context (`run_id`, `parent_span_id`) is propagated through nested graph calls
- [ ] `GraphTracer` class provides `start_span()`, `end_span()`, `add_event()` methods
- [ ] Performance metrics per node: p50, p95, p99 latency across all invocations
- [ ] Execution graph visualization: generate Mermaid/Graphviz diagram from trace data showing node durations and failure rates
- [ ] Trace data is queryable: filter by `node_name`, `run_id`, `status`, `time_range`
- [ ] Sensitive data in traces (message content, context values) can be redacted via configured redaction functions
- [ ] `get_last_trace()` and `get_trace_summary()` convenience methods for debugging

**Trace Schema:**

```python
@dataclass
class NodeTrace:
    trace_id: str
    span_id: str
    run_id: str
    node_name: str
    status: Literal["success", "failure", "retry", "skipped", "interrupted"]
    input_state_hash: str
    output_state_hash: str | None
    start_time: datetime
    end_time: datetime
    duration_ms: float
    error: ErrorRecord | None = None
    retryAttempt: int = 0
    tags: list[str] = field(default_factory=list)

@dataclass
class StateTransition:
    transition_id: str
    run_id: str
    from_state_hash: str
    to_state_hash: str
    changed_keys: list[str]
    trigger_node: str | None
    timestamp: datetime
```

**Rationale:** Without tracing, complex agentic workflows are black boxes. Comprehensive tracing enables debugging of non-deterministic LLM outputs, performance tuning, and compliance auditing.

---

### [FR-109] Integration with Existing Framework Components

**Description:** The framework MUST provide seamless integration between LangGraph nodes and existing methodology-v2 components: Hunter Agent, UQLM, evaluator agents, and report generators.

**Acceptance Criteria:**

- [ ] `HunterAgentNode`: wraps `HunterAgent` as a LangGraph node that takes `current_task` from state, outputs `research_results` to `intermediate_results`
- [ ] `UQLMNode`: wraps `UQLMProcessor` as a node that reads raw content from `context["raw_content"]`, writes structured data to `context["structured_data"]`
- [ ] `EvaluatorNode`: wraps any evaluator agent as a node that reads `intermediate_results`, writes `evaluation_result` and `confidence_score` to `intermediate_results`
- [ ] `ReportGeneratorNode`: wraps the report generation component as a node that assembles final output from all `intermediate_results` into `context["final_report"]`
- [ ] Integration nodes preserve existing component interfaces (no refactoring of Hunter Agent, UQLM, etc.)
- [ ] Each integration node has a default retry policy (3 attempts, exponential backoff)
- [ ] LLM model configuration (model name, temperature, API base) is injected from graph-level config into each node
- [ ] Tool definitions from Hunter Agent are automatically registered as LangGraph tools in the graph
- [ ] State keys used by integration nodes are documented in the state schema

**Integration Pattern:**

```python
from methodology_v2.langgraph.integrations import HunterAgentNode, UQLMNode, EvaluatorNode

builder = GraphBuilder[AgentState](state_schema=AgentState, name="research_pipeline")

hunter_node = HunterAgentNode(
    agent=existing_hunter_agent_instance,
    state_read=["current_task"],
    state_write=["intermediate_results"],
    config=NodeConfig(description="Web research agent", tags=["research"])
)

builder.add_node("hunter", hunterNode, config=NodeConfig(retry_policy=RetryPolicy(max_attempts=3)))
builder.add_node("uqlm", UQLMNode(processor=existing_uqlm_instance))
builder.add_node("evaluator", EvaluatorNode(evaluator=existing_evaluator))
builder.add_edge("hunter", "uqlm")
builder.add_edge("uqlm", "evaluator")
```

**Rationale:** Integration nodes are adapters that bridge the existing methodology-v2 component ecosystem with the LangGraph execution model, enabling incremental adoption without rewrites.

---

### [FR-110] Configuration Management

**Description:** The framework MUST provide a unified configuration system that manages graph-level, node-level, and runtime configurations through declarative files and programmatic overrides.

**Acceptance Criteria:**

- [ ] All configuration is defined in YAML or JSON files following a schema defined in `GraphConfig`, `NodeConfig`, `RuntimeConfig`
- [ ] `GraphConfig` fields:
    - `graph_name: str`
    - `state_schema_version: str`
    - `default_error_policy: ErrorPolicy`
    - `default_retry_policy: RetryPolicy`
    - `checkpoint_interval: int | "node" | "never"`
    - `max_concurrent_nodes: int` (for parallel execution)
    - `tracing_sink: TracingConfig`
    - `llm_config: LLMConfig`
- [ ] Configuration is loaded via `GraphConfigLoader.load(path: str) -> GraphConfig`
- [ ] Environment variable substitution in config: `${ENV_VAR}` syntax resolved at load time
- [ ] Config validation: unknown fields raise `ConfigValidationError`, missing required fields raise `MissingConfigFieldError`
- [ ] Runtime config overrides via `graph.invoke(initial_state, config=RuntimeConfig(debug=True))`
- [ ] Secrets management: sensitive fields (API keys) are loaded from environment or a secrets manager (AWS Secrets Manager, HashiCorp Vault), never hardcoded
- [ ] Configuration is immutable after graph compilation (prevents runtime config drift)
- [ ] `graph.get_config()` returns the current configuration snapshot
- [ ] Config diffing: compare two config versions and produce a human-readable changelog

**Config Example (YAML):**

```yaml
# config/research_pipeline.yaml
graph_name: "research_pipeline"
state_schema_version: "1.0"

llm_config:
  provider: "openai"
  model: "gpt-4o"
  temperature: 0.0
  api_base: "${OPENAI_API_BASE}"  # env var substitution
  api_key: "${OPENAI_API_KEY}"     # secret from env

tracing:
  enabled: true
  sink: "otlp"
  endpoint: "${OTEL_EXPORTER_OTLP_ENDPOINT}"
  redact_keys: ["messages[*].content", "context.raw_content"]

checkpoint:
  backend: "postgres"
  connection_string: "${DATABASE_URL}"
  interval: "node"  # checkpoint after every node

error_policy:
  on_node_error: "retry"
  default_retry_policy:
    max_attempts: 3
    backoff: "exponential"
    initial_delay_ms: 1000
    max_delay_ms: 30000

nodes:
  hunter:
    timeout_ms: 60000
    retry_policy:
      max_attempts: 5
  evaluator:
    timeout_ms: 30000
    human_in_the_loop: false
```

**Rationale:** Declarative configuration enables infrastructure-as-code practices, reproducible pipeline deployments, and operational clarity about pipeline behavior without inspecting code.

---

## 3. Non-Functional Requirements

### 3.1 Performance

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Graph compilation time | < 500ms for graphs with ≤50 nodes | Benchmark suite |
| Node execution overhead | < 10ms per node (state serialization + validation) | Trace data |
| Checkpoint save latency | < 50ms (MemorySaver), < 500ms (SQLiteSaver) | Benchmark suite |
| Conditional routing evaluation | < 1ms | Trace data |
| State validation per node | < 5ms for state with ≤100 keys | Unit test |
| Concurrent node throughput | ≥ 10 nodes/second for parallelized graphs | Load test |

**NFR-P1:** Graph execution latency per node (excluding node business logic) MUST be < 100ms as measured from entry to state update commit.

### 3.2 Reliability

| Metric | Target |
|--------|--------|
| Node failure isolation | A node failure MUST NOT crash the entire graph; error is recorded and handled per policy |
| Checkpoint integrity | Checkpointed state MUST be identical to pre-checkpoint state (byte-for-byte verified on restore) |
| Retry correctness | Retry attempts MUST use the same input state; state mutations from failed attempts MUST be rolled back |
| Circuit breaker | Circuit breaker open state MUST persist across graph restarts (if using persistent checkpointer) |
| Recovery RTO | Resuming from checkpoint to continued execution MUST complete within 5 seconds |

**NFR-R1:** Nodes that fail with a non-recoverable error MUST NOT be retried; they MUST route to the configured fallback or error handler.

**NFR-R2:** Graph execution MUST maintain ACID-like properties within a single checkpoint-to-checkpoint interval: either all state mutations in an interval are applied, or none are (atomic intervals).

### 3.3 Extensibility

| Dimension | Mechanism |
|-----------|-----------|
| Custom node types | `NodePluginRegistry` with `@register_node(name, node_class)` decorator |
| Custom state fields | Subclass `AgentState` or configure via `custom_state_fields: dict` in config |
| Custom routing combinators | Extend `RoutingCombinator` ABC |
| Custom checkpointer backends | Implement `CheckpointerBackend` ABC |
| Custom tracing sinks | Implement `TracingSink` ABC |
| Custom error handlers | Register via `error_handler_registry` |

**NFR-E1:** Adding a new node type MUST NOT require modifications to `GraphBuilder`, `CompiledStateGraph`, or any core class.

**NFR-E2:** Plugin registration MUST be idempotent (registering the same node type twice does not raise an error).

### 3.4 Observability

| Metric | Target |
|--------|--------|
| Trace coverage | 100% of node invocations are traced |
| Trace retention | Traces are queryable for at least 7 days in production |
| Metrics export | Prometheus-compatible `/metrics` endpoint exposed |
| Health endpoints | `/health`, `/ready`, `/live` for container orchestration |

### 3.5 Security

| Concern | Mitigation |
|---------|------------|
| State injection | All state keys are validated against schema; arbitrary key injection prevented |
| Secret exposure in traces | Redaction functions applied to sensitive keys before trace emission |
| API key management | All keys loaded from environment or secrets manager; never in config files |
| Graph topology protection | Compiled graphs are immutable; topology cannot be modified post-compilation |

### 3.6 Compatibility

| Concern | Requirement |
|---------|------------|
| LangChain version | Compatible with LangChain ≥ 0.2.0 and LangGraph ≥ 0.0.20 |
| Python version | Python 3.10+ |
| Pydantic version | Pydantic v2 (using `model_validator`, `Field`, `BaseModel`) |
| Async support | Full async/await support; nodes can be sync or async functions |

---

## 4. User Scenarios

### 4.1 Scenario 1: Multi-Stage Research Pipeline with Self-Correction

**Actor:** Research Analyst  
**Goal:** Produce a comprehensive market research report with automated quality checks and iterative refinement.

**Flow:**

```
[START] → hunter (web research) → uqlm (structuring)
    ↓                                    ↓
evaluator (quality check) ←──────────────┘
    ↓
[confidence ≥ 0.9?] ──YES──→ finalize → [END]
    │
    NO
    ↓
[confidence ≥ 0.7?] ──YES──→ human_review → finalize → [END]
    │
    NO
    ↓
retry (refine search) → hunter (loop back)
```

**Steps:**

1. User submits a research query via CLI/API
2. Graph is compiled with checkpointer enabled
3. `hunter` node performs web research, outputs to `intermediate_results["research"]`
4. `uqlm` node structures the raw findings into a schema
5. `evaluator` node assesses confidence score
6. Conditional routing:
   - `score ≥ 0.9` → `finalize` → report generated
   - `score ≥ 0.7 and < 0.9` → `human_review` node pauses for user feedback → `finalize`
   - `score < 0.7` → `retry` node issues new search terms → loops back to `hunter`
7. Checkpoints are saved after each node; user can resume if process is interrupted

**Key Features Exercised:** [FR-101], [FR-103], [FR-104], [FR-105], [FR-106], [FR-107], [FR-108], [FR-109]

---

### 4.2 Scenario 2: Parallel Tool Execution with Aggregated Results

**Actor:** Data Engineering Team  
**Goal:** Run multiple data sources simultaneously, aggregate results, and proceed only when all sources respond.

**Flow:**

```
[START] → [source_a, source_b, source_c] (parallel fan-out)
    ↓           ↓           ↓
wait_all ←─────────────────────────────── (synchronization barrier)
    ↓
aggregator (merge and deduplicate)
    ↓
[errors > threshold?] ──YES──→ alert_human → [END]
    │
    NO
    ↓
finalize → [END]
```

**Steps:**

1. Three `DataSourceNode` instances are registered with the same node name prefix pattern, triggering parallel execution
2. LangGraph's built-in `Send` interface fan-out sends the same state to each source node concurrently
3. `wait_all` is a custom synchronization node that aggregates results only when all three have completed
4. `aggregator` merges results, removes duplicates, resolves conflicts
5. If >50% of sources failed, `alert_human` sends a notification and halts
6. All intermediate results are checkpointed; the graph can be resumed from the `wait_all` node if a downstream step fails

**Key Features Exercised:** [FR-101], [FR-102], [FR-103], [FR-104], [FR-106], [FR-107], [FR-110]

---

### 4.3 Scenario 3: Human-in-the-Loop Approval Workflow

**Actor:** Compliance Reviewer  
**Goal:** Ensure every generated report passes a human compliance check before publication.

**Flow:**

```
[START] → generate → evaluate
    ↓                  ↓
[confidence ≥ 0.95?] ──YES──→ compliance_check (HIL interrupt)
    ↓                                      ↓
[revisions_requested?] ──YES──→ revise ───┘
    │                        ↓
    NO                       evaluate (loop)
    ↓                        ↓
publish → [END]
```

**Steps:**

1. `generate` node creates an initial draft report
2. `evaluate` node scores it on multiple dimensions (accuracy, completeness, style)
3. If overall confidence ≥ 0.95, execution pauses at `compliance_check` node
4. Human reviewer receives a notification with the report content and a Slack/email summary
5. Reviewer approves, requests revisions, or rejects via a web UI backed by the framework's API
6. If revisions requested, `revise` node incorporates feedback and loops back to `evaluate`
7. Approved reports proceed to `publish` node
8. Full trace of the approval decision (reviewer ID, timestamp, comments) is stored in state metadata

**Key Features Exercised:** [FR-101], [FR-102], [FR-104], [FR-105], [FR-106], [FR-108], [FR-109], [FR-109], [FR-110]

**Key Benefits:**
- Compliance is guaranteed via mandatory human checkpoint
- Loop detection prevents infinite revision cycles
- Complete audit trail of review decisions
- Parallel paths for high-confidence vs. low-confidence outputs

---

### 4.4 Scenario 4: Distributed Multi-Agent Research Team

**Actor:** Research Team Lead  
**Goal:** Coordinate multiple specialized agents (financial analyst, technical analyst, market analyst) that work in parallel and synthesize findings into a unified report.

**Flow:**

```
[START]
    ↓
[dispatcher] (fan-out to specialist agents)
    ↓         ↓         ↓
[fin_agent] [tech_agent] [market_agent]  (parallel)
    ↓         ↓         ↓
[aggregator] (synchronization + synthesis)
    ↓
[fact_checker]
    ↓
[score ≥ 0.85?] ──YES──→ [END]
    │
    NO
    ↓
[return_discrepancies] → [END]
```

**Steps:**

1. `dispatcher` node reads the research query and spawns 3 concurrent sub-graph invocations via LangGraph's `Send` API
2. Each specialist agent operates independently, writing to its own `intermediate_results` key (`fin`, `tech`, `market`)
3. `aggregator` node waits for all three to complete, then synthesizes findings into a unified context
4. `fact_checker` node validates claims against known data sources
5. If fact-check score ≥ 0.85, the report is finalized; otherwise, discrepancies are flagged and returned
6. Each specialist agent run is independently checkpointed and recoverable

**Key Features Exercised:** [FR-101], [FR-103], [FR-104], [FR-105], [FR-106], [FR-107], [FR-108], [FR-109], [FR-110]

---

## 5. Dependencies

### 5.1 Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | ≥ 0.0.20 | Graph-based workflow execution |
| `langchain-core` | ≥ 0.2.0 | Base classes for chains, prompts, and memory |
| `langchain` | ≥ 0.2.0 | LLM integrations and tool abstractions |
| `langchain-community` | ≥ 0.2.0 | Third-party integrations (Airtable, Notion, etc.) |
| `pydantic` | ≥ 2.0 | State schema definition and validation |
| `python-dotenv` | ≥ 1.0 | Environment variable loading |
| `structlog` | ≥ 24.0 | Structured logging for tracing |
| `orjson` | ≥ 3.9 | Fast JSON serialization for state |
| `tenacity` | ≥ 8.2 | Retry and backoff utilities |

### 5.2 Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langsmith` | ≥ 0.1.0 | Tracing and evaluation platform (optional) |
| `psycopg2-binary` | ≥ 2.9 | PostgreSQL checkpointer backend |
| `aiosqlite` | ≥ 0.19 | Async SQLite checkpointer backend |
| `opentelemetry-api` | ≥ 1.20 | OTLP trace export |
| `opentelemetry-sdk` | ≥ 1.20 | OTLP trace export |
| `prometheus-client` | ≥ 0.19 | Metrics export |

### 5.3 Internal Framework Dependencies

| Feature | Dependency Type | Notes |
|---------|----------------|-------|
| Hunter Agent integration | Required | FR-109 adapter requires `HunterAgent` class |
| UQLM integration | Required | FR-109 adapter requires `UQLMProcessor` class |
| Evaluator integration | Required | FR-109 adapter requires evaluator base class |
| Report Generator | Required | FR-109 adapter requires `ReportGenerator` class |
| Config Loader | Required | Relies on `methodology_v2.config` module |
| Logging infrastructure | Required | Relies on `methodology_v2.logging` module |
| Feature #08 (Pipeline) | Soft dependency | LangGraph nodes can wrap Feature #08 pipeline stages |
| Feature #06 (Memory) | Soft dependency | Long-term memory can be integrated as a graph node |

### 5.4 Peer v3 Features

| Feature | Relationship | Integration Points |
|---------|-------------|-------------------|
| Feature #11: Observability | Peer | LangGraph traces feed into the observability dashboard |
| Feature #12: Memory Management | Peer | Long-term memory backed by Feature #12 storage |
| Feature #13: Security | Peer | Security policies enforced at node execution level |

---

## 6. Out of Scope

The following items are explicitly **NOT** part of this feature:

1. **LLM provider implementation**: LangGraph handles workflow orchestration, not LLM inference. LLM calls are delegated to LangChain's model abstractions.
2. **Tool implementation**: Individual tools (web search, file I/O, database queries) are not built here; only the adapter interface to LangGraph's tool system.
3. **UI/UX**: This feature defines the programmatic API and configuration schema; any interactive UI (graph visualizer, node editor, trace inspector) is a separate feature.
4. **Deployment infrastructure**: Kubernetes manifests, Dockerfiles, Helm charts, and CI/CD pipelines are out of scope.
5. **Multi-language support**: LangGraph is Python-only; non-Python agent runtimes are not addressed.
6. **Real-time streaming**: Streaming of individual token outputs from LLM nodes is handled by LangChain; this feature focuses on graph-level execution control.
7. **Horizontal scaling**: Graph execution within a single process is the initial scope; distributed graph execution across multiple machines is a future roadmap item.
8. **Graph optimization**: Automatic node fusion, constant folding, or graph-level JIT compilation are out of scope.
9. **Federated graphs**: Multiple graphs running across different trust boundaries is out of scope.
10. **LLM-specific prompt management**: Prompt templates, few-shot examples, and message history management are handled by LangChain components.

---

## 7. Glossary

| Term | Definition |
|------|------------|
| **Agent** | An autonomous program that uses an LLM to decide which actions to take, often with tool access and memory. |
| **Checkpoint** | A persisted snapshot of the graph's full state at a specific point in execution, enabling resume. |
| **Conditional Edge** | An edge whose destination is determined dynamically by a routing function at runtime. |
| **DAG** | Directed Acyclic Graph. A graph structure with directed edges and no cycles. |
| **Dead Letter Queue (DLQ)** | A storage mechanism for recording node invocations that failed after all retry attempts. |
| **Error Policy** | A configuration that determines how the graph responds when a node raises an exception. |
| **Fan-out / Fan-in** | Parallel execution pattern where one node triggers multiple downstream nodes (fan-out) and waits for all to complete (fan-in). |
| **Graph Builder** | The programmatic API for constructing a LangGraph StateGraph by adding nodes and edges. |
| **Human-in-the-Loop (HIL)** | A pattern where graph execution pauses to await human input before proceeding. |
| **Node** | A named computational step in a LangGraph. Receives state, performs work, returns state updates. |
| **Retry Policy** | Configuration specifying how many times and with what backoff strategy a failed node should be retried. |
| **Routing Function** | A pure function `(state) -> str` that determines which edge to follow based on current state. |
| **State** | The shared data object that flows through all nodes in a graph. Defined by a Pydantic model. |
| **State Transition** | The change in state produced by a node's execution. |
| **Trace / Span** | A record of a single node invocation including input, output, timing, and status. |
| **Circuit Breaker** | A pattern that stops calling a failing node after a threshold of consecutive failures. |

---

## Appendix A: File Structure

```
skills/methodology-v2/
└── implement/
    └── feature-10-langgraph/
        └── 01-spec/
            └── SPEC.md              ← This document
        └── 02-architecture/
            └── ARCHITECTURE.md       ← System design (future phase)
        └── 03-implement/
            └── README.md             ← Implementation guide (future phase)
        └── 04-testing/
            └── README.md             ← Test strategy (future phase)
```

## Appendix B: References

1. LangGraph Documentation — https://langchain-langgraph.readthedocs.io/
2. LangChain Core — https://python.langchain.com/docs/concepts/
3. Pydantic v2 — https://docs.pydantic.dev/
4. LangGraph Checkpointers — https://langchain-langgraph.readthedocs.io/en/latest/concepts/checkpointing/
5. LangGraph Persistence — https://langchain-langgraph.readthedocs.io/en/latest/concepts/persistence/
6. methodology-v2 Feature #08 (Pipeline) — internal reference
7. methodology-v2 Feature #06 (Memory) — internal reference

---

**End of SPEC.md — Feature #10 Phase 01-spec**
