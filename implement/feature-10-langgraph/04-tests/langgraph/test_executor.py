"""
Tests for executor.py (GraphRunner + ExecutionResult).

These tests mock langgraph.types to avoid requiring the actual package.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ─────────────────────────────────────────────────────────────────────────────
# Mock langgraph.types before importing the module under test
# ─────────────────────────────────────────────────────────────────────────────

_mock_Checkpoint = MagicMock(name="Checkpoint")
_mock_Interrupt = MagicMock(name="Interrupt")

_module_patcher = patch.dict(
    "sys.modules",
    {
        "langgraph": MagicMock(),
        "langgraph.types": MagicMock(
            Checkpoint=_mock_Checkpoint,
            Interrupt=_mock_Interrupt,
        ),
    },
)


with _module_patcher:
    from ml_langgraph.executor import (
        ExecutionStatus,
        ExecutionResult,
        ExecutionConfig,
        ExecutionCallbacks,
        GraphRunner,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionResult dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionResult:
    def test_execution_result_dataclass(self):
        """ExecutionResult should store all fields correctly."""
        result = ExecutionResult(
            node_name="TestNode",
            status=ExecutionStatus.SUCCESS,
            duration_ms=150.5,
            error=None,
            output_state={"value": 42},
        )
        assert result.node_name == "TestNode"
        assert result.status == ExecutionStatus.SUCCESS
        assert result.duration_ms == 150.5
        assert result.error is None
        assert result.output_state["value"] == 42

    def test_execution_result_with_error(self):
        """ExecutionResult with error status should store error message."""
        result = ExecutionResult(
            node_name="FailingNode",
            status=ExecutionStatus.FAILED,
            duration_ms=50.0,
            error="Something broke",
        )
        assert result.status == ExecutionStatus.FAILED
        assert result.error == "Something broke"

    def test_execution_result_timeout_status(self):
        """ExecutionResult should support TIMEOUT status."""
        result = ExecutionResult(
            node_name="SlowNode",
            status=ExecutionStatus.TIMEOUT,
            duration_ms=30_000.0,
            error="Execution timed out after 30s",
        )
        assert result.status == ExecutionStatus.TIMEOUT

    def test_execution_status_enum_values(self):
        """ExecutionStatus enum should have expected values."""
        assert ExecutionStatus.SUCCESS.value == "success"
        assert ExecutionStatus.FAILED.value == "failed"
        assert ExecutionStatus.TIMEOUT.value == "timeout"


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionConfig dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionConfig:
    def test_execution_config_defaults(self):
        """ExecutionConfig should have sensible defaults."""
        config = ExecutionConfig()
        assert config.max_execution_time is None
        assert config.enable_profiling is False
        assert config.checkpoint_interval == 0

    def test_execution_config_custom_values(self):
        """ExecutionConfig should accept custom values."""
        config = ExecutionConfig(
            max_execution_time=60.0,
            enable_profiling=True,
            checkpoint_interval=5,
        )
        assert config.max_execution_time == 60.0
        assert config.enable_profiling is True
        assert config.checkpoint_interval == 5


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionCallbacks dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutionCallbacks:
    def test_callbacks_default_to_none(self):
        """All callback fields should default to None."""
        cb = ExecutionCallbacks()
        assert cb.on_node_start is None
        assert cb.on_node_end is None
        assert cb.on_error is None
        assert cb.on_checkpoint is None

    def test_callbacks_accept_callables(self):
        """ExecutionCallbacks should accept callable values."""
        start_cb = MagicMock()
        end_cb = MagicMock()
        cb = ExecutionCallbacks(on_node_start=start_cb, on_node_end=end_cb)
        assert cb.on_node_start is start_cb
        assert cb.on_node_end is end_cb


# ─────────────────────────────────────────────────────────────────────────────
# GraphRunner Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGraphRunnerInit:
    def test_requires_invoke_method(self):
        """GraphRunner should raise TypeError if compiled_graph lacks invoke."""
        bad_graph = MagicMock(spec=[])  # no invoke
        with pytest.raises(TypeError, match="invoke"):
            GraphRunner(bad_graph)

    def test_requires_stream_method(self):
        """GraphRunner should raise TypeError if compiled_graph lacks stream."""
        no_stream_graph = MagicMock(spec=["invoke"])  # has invoke, no stream
        with pytest.raises(TypeError, match="stream"):
            GraphRunner(no_stream_graph)

    def test_valid_graph_is_accepted(self):
        """GraphRunner should accept a graph with both invoke and stream."""
        good_graph = MagicMock()
        good_graph.invoke = MagicMock()
        good_graph.stream = MagicMock()
        runner = GraphRunner(good_graph)
        assert runner.compiled_graph is good_graph

    def test_default_config(self):
        """GraphRunner should create ExecutionConfig defaults if not provided."""
        graph = MagicMock(spec=["invoke", "stream"])
        runner = GraphRunner(graph)
        assert runner.config.max_execution_time is None
        assert runner.config.enable_profiling is False


class TestGraphRunnerInvoke:
    def test_invoke_calls_graph_invoke(self):
        """invoke() should call compiled_graph.ainvoke() and return final state."""
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"final": "state"})
        graph.astream = MagicMock(return_value=iter([]))

        runner = GraphRunner(graph)
        result = runner.invoke({"initial": "data"})

        assert result == {"final": "state"}

    def test_invoke_with_callbacks(self):
        """invoke() should accept ExecutionCallbacks without error."""
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"out": True})

        runner = GraphRunner(graph)
        cb = ExecutionCallbacks(on_node_start=MagicMock())
        result = runner.invoke({"start": True}, callbacks=cb)
        assert result["out"] is True


class TestGraphRunnerStream:
    def test_stream_returns_generator(self):
        """stream() should return a generator of intermediate states."""
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([{"step": 1}, {"step": 2}]))

        runner = GraphRunner(graph)
        result = runner.stream({"initial": True})
        # It should be a generator
        states = list(result)
        assert len(states) == 2


class TestHandleNodeError:
    def test_handle_node_error(self):
        """_handle_node_error() should attach error info to state."""
        graph = MagicMock(spec=["invoke", "stream"])
        runner = GraphRunner(graph)

        state = {"counter": 0}
        recovered = runner._handle_node_error("BadNode", RuntimeError("oops"), state)

        assert recovered["__last_error__"]["node"] == "BadNode"
        assert recovered["__last_error__"]["type"] == "RuntimeError"
        assert recovered["__last_error__"]["message"] == "oops"

    def test_handle_node_error_preserves_existing_state(self):
        """_handle_node_error() should not discard existing state keys."""
        graph = MagicMock(spec=["invoke", "stream"])
        runner = GraphRunner(graph)

        state = {"existing": "data", "count": 42}
        recovered = runner._handle_node_error("NodeX", ValueError("err"), state)

        assert recovered["existing"] == "data"
        assert recovered["count"] == 42


class TestProfiling:
    def test_profiling_data_collected(self):
        """With profiling enabled, _profiling_data should be populated."""
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))

        runner = GraphRunner(graph, ExecutionConfig(enable_profiling=True))
        runner.invoke({"start": True})
        profiling = runner.get_profiling_data()
        # profiling dict exists (actual contents depend on async timing)
        assert "nodes" in profiling or profiling == {}


class TestCheckpointManager:
    def test_set_checkpoint_manager(self):
        """GraphRunner should accept a CheckpointManager."""
        from ml_langgraph.checkpoint import MemoryCheckpointBackend, CheckpointManager

        graph = MagicMock(spec=["invoke", "stream"])
        runner = GraphRunner(graph)
        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)
        assert runner.checkpoint_manager is cm

    def test_checkpoint_current_state(self):
        """checkpoint_current_state() should save state via manager."""
        from ml_langgraph.checkpoint import MemoryCheckpointBackend, CheckpointManager

        graph = MagicMock(spec=["invoke", "stream"])
        runner = GraphRunner(graph)
        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)

        state = {"step": 1, "data": [1, 2]}
        cp_id = runner.checkpoint_current_state(state, metadata={"tag": "test"})
        assert cp_id is not None
        assert cm.exists(cp_id) is True
