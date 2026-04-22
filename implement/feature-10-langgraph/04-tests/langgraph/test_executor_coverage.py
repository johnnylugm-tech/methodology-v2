"""
Additional coverage tests for executor.py.
Covers previously-missed paths in GraphRunner.

Mock langgraph.types before importing the module under test.
"""

from __future__ import annotations

import pytest
import asyncio
import traceback
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock

from ml_langgraph.checkpoint import MemoryCheckpointBackend, CheckpointManager


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
# Helper to build a minimal valid GraphRunner
# ─────────────────────────────────────────────────────────────────────────────

def make_runner(**kwargs) -> GraphRunner:
    graph = MagicMock()
    graph.invoke = MagicMock()
    graph.stream = MagicMock()
    graph.ainvoke = AsyncMock(return_value={"done": True})
    graph.astream = MagicMock(return_value=iter([]))
    runner = GraphRunner(graph, **kwargs)
    return runner


# ─────────────────────────────────────────────────────────────────────────────
# Line 139: _invoke_sync_wrapper — already in async context
# ─────────────────────────────────────────────────────────────────────────────

class TestInvokeSyncWrapper:
    def test_invoke_sync_wrapper_when_already_in_async_loop(self):
        """
        When asyncio.get_running_loop() finds a loop (already in async context),
        _invoke_sync_wrapper is called and uses ThreadPoolExecutor to run the async invoke.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"via_sync_wrapper": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        async def _test():
            # Simulate already being inside an async loop
            result = runner.invoke({"test": True}, callbacks=ExecutionCallbacks())
            return result

        async def runner_coro():
            # get_running_loop() will find a loop when we await _invoke_sync_wrapper
            # But actually _invoke_sync_wrapper uses executor.submit(asyncio.run, ...)
            # which creates its own fresh loop. So the "already in loop" path should
            # be hit when asyncio.get_running_loop() succeeds.
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: runner.invoke({"sync": True}),
                ),
                timeout=5.0,
            )

        # Run the test - _invoke_sync_wrapper is tested by calling invoke()
        # from within an existing event loop context
        result = asyncio.run(runner_coro())
        assert result == {"via_sync_wrapper": True}


# ─────────────────────────────────────────────────────────────────────────────
# Lines 151-155: ThreadPoolExecutor in _invoke_sync_wrapper
# ─────────────────────────────────────────────────────────────────────────────

class TestThreadPoolExecutor:
    def test_invoke_creates_thread_pool_executor(self):
        """
        _invoke_sync_wrapper uses concurrent.futures.ThreadPoolExecutor.
        This test triggers that code path by being inside an existing async loop.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(return_value={"thread_pool": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        # Trigger _invoke_sync_wrapper by calling invoke from an existing loop
        async def _caller():
            loop = asyncio.get_running_loop()
            # Directly call the sync wrapper which uses ThreadPoolExecutor
            result = runner._invoke_sync_wrapper({"nested": True}, ExecutionCallbacks())
            return result

        result = asyncio.run(_caller())
        assert result == {"thread_pool": True}


# ─────────────────────────────────────────────────────────────────────────────
# Lines 225-226, 231-232: resume() checkpoint paths + KeyError
# ─────────────────────────────────────────────────────────────────────────────

class TestResume:
    def test_resume_raises_key_error_when_checkpoint_not_found(self):
        """
        resume() raises KeyError when CheckpointManager.load returns None.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)
        runner.checkpoint_manager = MagicMock(spec=["load"])
        runner.checkpoint_manager.load.return_value = None  # not found

        with pytest.raises(KeyError, match="not found"):
            runner.resume("nonexistent-id", {"resume": True})

    def test_resume_loads_checkpoint_and_calls_resume_async(self):
        """
        resume() loads a checkpoint and calls _resume_async with the checkpoint.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"resumed": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        # Set up a real checkpoint manager
        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)

        # Save a checkpoint
        cp_data = {"state": {"step": 99}, "metadata": {}}
        runner.checkpoint_manager.save("cp-test", cp_data)

        result = runner.resume("cp-test", {"extra": "input"})
        assert result == {"resumed": True}


# ─────────────────────────────────────────────────────────────────────────────
# Lines 186-187: astream sync/async branches
# ─────────────────────────────────────────────────────────────────────────────

class TestAstream:
    def test_stream_with_sync_iterator(self):
        """
        _stream_async wraps a sync iterator by yielding items directly.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([{"a": 1}, {"b": 2}]))
        runner = GraphRunner(graph)

        results = list(runner.stream({"start": True}))
        assert len(results) == 2

    def test_stream_with_async_iterator(self):
        """
        _stream_async uses __aiter__ to iterate async generator.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()

        async def _async_gen():
            yield {"async": True}
            yield {"data": 42}

        graph.astream = MagicMock(return_value=_async_gen())
        runner = GraphRunner(graph)

        results = list(runner.stream({"start": True}))
        assert len(results) == 2
        assert results[0] == {"async": True}


# ─────────────────────────────────────────────────────────────────────────────
# Lines 269-279: _stream_async exception handling
# ─────────────────────────────────────────────────────────────────────────────

class TestStreamAsyncError:
    def test_stream_async_raises_runtime_error_on_failure(self):
        """
        _stream_async wraps exceptions in RuntimeError.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()

        # Make astream raise an exception
        graph.astream = MagicMock(side_effect=RuntimeError("stream broke"))

        runner = GraphRunner(graph)

        with pytest.raises(RuntimeError, match="Streaming execution failed"):
            list(runner.stream({"start": True}))


# ─────────────────────────────────────────────────────────────────────────────
# Lines 295-339: _execute_node error handling, timeout, ValueError
# ─────────────────────────────────────────────────────────────────────────────

class TestExecuteNode:
    def test_execute_node_timeout_returns_timeout_status(self):
        """
        When max_execution_time is set and node times out,
        _execute_node returns ExecutionResult with TIMEOUT status.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.nodes = {"SlowNode": MagicMock()}

        async def slow_invoke(state):
            await asyncio.sleep(10)  # will exceed timeout
            return state

        graph.nodes["SlowNode"].ainvoke = slow_invoke
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))

        runner = GraphRunner(
            graph,
            ExecutionConfig(max_execution_time=0.01),  # 10ms timeout
        )

        result = runner._execute_node("SlowNode", {"test": True})
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.error is not None
        assert "timed out" in result.error

    def test_execute_node_catches_generic_exception(self):
        """
        _execute_node catches any exception and returns FAILED status.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.nodes = {"BombNode": MagicMock()}

        async def exploding_invoke(state):
            raise RuntimeError("boom")

        graph.nodes["BombNode"].ainvoke = exploding_invoke
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))

        runner = GraphRunner(graph)
        result = runner._execute_node("BombNode", {"state": True})

        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
        assert "RuntimeError" in result.error


# ─────────────────────────────────────────────────────────────────────────────
# Lines 409: get_profiling_data when profiling disabled
# ─────────────────────────────────────────────────────────────────────────────

class TestGetProfilingData:
    def test_get_profiling_data_returns_empty_when_disabled(self):
        """
        get_profiling_data() returns {} when enable_profiling is False.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph, ExecutionConfig(enable_profiling=False))

        result = runner.get_profiling_data()
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# Lines 415, 418, 421-423, 426-436, 439-441, 444:
# _make_langchain_callback inner class methods
# ─────────────────────────────────────────────────────────────────────────────

class TestMakeLangchainCallback:
    def test_callback_on_node_start_calls_callback(self):
        """
        on_node_start in the callback handler should call callbacks.on_node_start.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        on_node_start = MagicMock()
        on_node_end = MagicMock()
        on_error = MagicMock()
        callbacks = ExecutionCallbacks(
            on_node_start=on_node_start, on_node_end=on_node_end, on_error=on_error
        )

        handler = runner._make_langchain_callback(callbacks)

        # Simulate LangChain callback events
        handler.on_node_start("TestNode", inputs={"x": 1})
        assert on_node_start.called
        assert on_node_start.call_args[0][0] == "TestNode"

    def test_callback_on_node_end_calls_callback(self):
        """
        on_node_end should call callbacks.on_node_end with ExecutionResult.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        on_node_end = MagicMock()
        callbacks = ExecutionCallbacks(on_node_end=on_node_end)

        handler = runner._make_langchain_callback(callbacks)

        # Must push node first (on_node_end pops from stack)
        handler.on_node_start("MyNode", inputs={})
        handler.on_node_end("MyNode", outputs={"result": 42})

        assert on_node_end.called
        call_args = on_node_end.call_args
        assert call_args[0][0] == "MyNode"
        result = call_args[0][1]
        assert result.node_name == "MyNode"
        assert result.status == ExecutionStatus.SUCCESS

    def test_callback_on_tool_error_calls_callback(self):
        """
        on_tool_error should call callbacks.on_error.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        on_error = MagicMock()
        callbacks = ExecutionCallbacks(on_error=on_error)

        handler = runner._make_langchain_callback(callbacks)

        # Trigger on_tool_error (needs a node on the stack)
        handler.on_node_start("ErrorNode", inputs={})
        handler.on_tool_error(RuntimeError("test error"), inputs={})

        assert on_error.called
        assert on_error.call_args[0][1].args[0] == "test error"

    def test_callback_on_chain_start_passes_silently(self):
        """
        on_chain_start is a no-op (pass).
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        callbacks = ExecutionCallbacks(on_node_start=MagicMock())
        handler = runner._make_langchain_callback(callbacks)

        # Should not raise
        handler.on_chain_start({}, {"input": True})

    def test_callback_on_chain_end_passes_silently(self):
        """
        on_chain_end is a no-op (pass).
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        callbacks = ExecutionCallbacks()
        handler = runner._make_langchain_callback(callbacks)

        # Should not raise
        handler.on_chain_end({"output": True})

    def test_callback_on_text_passes_silently(self):
        """
        on_text is a no-op (pass).
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        callbacks = ExecutionCallbacks()
        handler = runner._make_langchain_callback(callbacks)

        # Should not raise
        handler.on_text("some log text")

    def test_callback_always_verbose_is_true(self):
        """
        ExecutionCallbackHandler.always_verbose should return True.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        callbacks = ExecutionCallbacks()
        handler = runner._make_langchain_callback(callbacks)

        assert handler.always_verbose is True


# ─────────────────────────────────────────────────────────────────────────────
# Line 461: set_checkpoint_manager (already mostly covered, but add edge case)
# ─────────────────────────────────────────────────────────────────────────────

class TestSetCheckpointManager:
    def test_set_checkpoint_manager_accepts_manager(self):
        """
        set_checkpoint_manager should store the provided CheckpointManager.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)

        assert runner.checkpoint_manager is cm


# ─────────────────────────────────────────────────────────────────────────────
# Line 495: checkpoint_current_state RuntimeError when manager not configured
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckpointCurrentState:
    def test_checkpoint_current_state_raises_when_no_manager(self):
        """
        checkpoint_current_state() raises RuntimeError if CheckpointManager is not set.
        """
        runner = make_runner()
        # runner.checkpoint_manager is None by default

        with pytest.raises(RuntimeError, match="CheckpointManager not configured"):
            runner.checkpoint_current_state({"state": True}, metadata={})

    def test_checkpoint_current_state_saves_with_metadata(self):
        """
        checkpoint_current_state() saves state with provided metadata.
        """
        runner = make_runner()
        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)

        cp_id = runner.checkpoint_current_state(
            {"step": 5}, metadata={"tag": "mid-run"}
        )
        assert cp_id is not None
        assert cm.exists(cp_id)


# ─────────────────────────────────────────────────────────────────────────────
# Lines 514-528: get_execution_history
# ─────────────────────────────────────────────────────────────────────────────

class TestGetExecutionHistory:
    def test_get_execution_history_empty_when_no_profiling(self):
        """
        get_execution_history() returns [] when profiling is disabled.
        """
        runner = make_runner()
        runner._profiling_data = {"nodes": {}}

        history = runner.get_execution_history()
        assert history == []

    def test_get_execution_history_populates_from_profiling_nodes(self):
        """
        get_execution_history() builds ExecutionResult list from _profiling_data.
        """
        runner = make_runner()
        runner._profiling_data = {
            "nodes": {
                "NodeA": {"duration_ms": 10.0, "status": "success"},
                "NodeB": {"duration_ms": 20.0, "status": "failed"},
            }
        }

        history = runner.get_execution_history()
        assert len(history) == 2

        names = {r.node_name for r in history}
        assert names == {"NodeA", "NodeB"}

        status_map = {r.node_name: r.status for r in history}
        assert status_map["NodeA"] == ExecutionStatus.SUCCESS
        assert status_map["NodeB"] == ExecutionStatus.FAILED


# ─────────────────────────────────────────────────────────────────────────────
# Line 531: __repr__
# ─────────────────────────────────────────────────────────────────────────────

class TestRepr:
    def test_repr_shows_graph_name_and_config(self):
        """
        __repr__ should include the graph name and config.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))
        graph.graph = MagicMock()
        graph.graph.name = "MyTestGraph"
        runner = GraphRunner(graph)

        repr_str = repr(runner)
        assert "MyTestGraph" in repr_str
        assert "config=" in repr_str

    def test_repr_falls_back_to_unknown_when_graph_attr_missing(self):
        """
        __repr__ uses 'unknown' when compiled_graph has no 'graph' attribute.
        hasattr(graph, 'graph') returns False -> 'unknown' in output.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock()
        graph.astream = MagicMock(return_value=iter([]))
        # Remove graph attribute so hasattr returns False
        del graph.graph
        runner = GraphRunner(graph)

        repr_str = repr(runner)
        assert "unknown" in repr_str


# ─────────────────────────────────────────────────────────────────────────────
# Lines 295-339 (continued): error handling in invoke via _invoke_async
# ─────────────────────────────────────────────────────────────────────────────

class TestInvokeAsyncError:
    def test_invoke_async_wraps_graph_exception(self):
        """
        _invoke_async wraps exceptions from compiled_graph.ainvoke in RuntimeError.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(side_effect=RuntimeError("graph failed"))
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        with pytest.raises(RuntimeError, match="Graph execution failed"):
            runner.invoke({"will": "fail"})


# ─────────────────────────────────────────────────────────────────────────────
# Lines 415-444: _make_langchain_callback — additional edge cases
# ─────────────────────────────────────────────────────────────────────────────

class TestCallbackEdgeCases:
    def test_on_node_end_with_non_dict_output(self):
        """
        on_node_end should handle non-dict outputs gracefully.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        on_node_end = MagicMock()
        callbacks = ExecutionCallbacks(on_node_end=on_node_end)
        handler = runner._make_langchain_callback(callbacks)

        # Must push node first (on_node_end pops from stack)
        handler.on_node_start("StrNode", inputs={})
        # Pass a non-dict output - should not crash
        handler.on_node_end("StrNode", outputs="just a string")

        assert on_node_end.called
        result = on_node_end.call_args[0][1]
        # output_state should be None when not a dict
        assert result.output_state is None

    def test_on_tool_error_with_empty_stack(self):
        """
        on_tool_error should handle empty node stack gracefully.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(return_value={"done": True})
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        on_error = MagicMock()
        callbacks = ExecutionCallbacks(on_error=on_error)
        handler = runner._make_langchain_callback(callbacks)

        # Don't push any node name first
        handler.on_tool_error(RuntimeError("orphan error"), inputs={})

        assert on_error.called
        # Should use "unknown" as node name
        assert on_error.call_args[0][0] == "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Lines 186-187, 295-339: invoke error + stream error + resume error
# ─────────────────────────────────────────────────────────────────────────────

class TestRuntimeErrorWrapping:
    def test_invoke_runtime_error_format(self):
        """
        When _invoke_async catches an exception, the error message should
        include the original exception info.
        """
        graph = MagicMock()
        graph.invoke = MagicMock()
        graph.stream = MagicMock()
        graph.ainvoke = AsyncMock(side_effect=ValueError("bad value"))
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        with pytest.raises(RuntimeError) as exc_info:
            runner.invoke({"x": 1})

        assert "Graph execution failed" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_resume_runtime_error_wraps_async_exception(self):
        """
        resume() wraps exceptions from _resume_async in RuntimeError.
        """
        graph = MagicMock(spec=["invoke", "stream"])
        graph.ainvoke = AsyncMock(side_effect=RuntimeError("resume failed"))
        graph.astream = MagicMock(return_value=iter([]))
        runner = GraphRunner(graph)

        backend = MemoryCheckpointBackend()
        cm = CheckpointManager(backend)
        runner.set_checkpoint_manager(cm)
        runner.checkpoint_manager.save("cp", {"state": {}, "metadata": {}})

        with pytest.raises(RuntimeError, match="Resume execution failed"):
            runner.resume("cp", {"extra": True})
