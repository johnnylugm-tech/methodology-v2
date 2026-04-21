"""
LangGraph executor module.
Provides GraphRunner for executing compiled LangGraph graphs with callbacks,
checkpointing, timeout, and profiling support.
"""

import asyncio
import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generator, Optional

# Checkpoint type alias (maps to the dict-based checkpoint format used by CheckpointManager)
Checkpoint = dict[str, Any]

from .checkpoint import CheckpointManager


class ExecutionStatus(str, Enum):
    """Execution status for a node."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """
    Result of a node execution.
    
    Attributes:
        node_name: Name of the executed node.
        status: Execution status (success/failed/timeout).
        duration_ms: Execution time in milliseconds.
        error: Error message if failed/timeout, else None.
        output_state: Graph state after node execution.
    """
    node_name: str
    status: ExecutionStatus
    duration_ms: float
    error: Optional[str] = None
    output_state: Optional[dict[str, Any]] = None


@dataclass
class ExecutionConfig:
    """
    Configuration for graph execution.
    
    Attributes:
        max_execution_time: Maximum execution time per node in seconds (None = no limit).
        enable_profiling: Whether to collect execution profiling data.
        checkpoint_interval: Number of nodes between automatic checkpoints (0 = disabled).
    """
    max_execution_time: Optional[float] = None
    enable_profiling: bool = False
    checkpoint_interval: int = 0


@dataclass
class ExecutionCallbacks:
    """
    Callback hooks for execution lifecycle events.
    
    All callbacks are optional and default to no-op.
    
    Attributes:
        on_node_start: Called before a node executes. Signature: (node_name: str, state: dict).
        on_node_end: Called after a node completes. Signature: (node_name: str, result: ExecutionResult).
        on_error: Called when a node raises an exception. Signature: (node_name: str, error: Exception, state: dict).
        on_checkpoint: Called after a checkpoint is saved. Signature: (checkpoint_id: str, state: dict).
    """
    on_node_start: Optional[Callable[[str, dict[str, Any]], None]] = None
    on_node_end: Optional[Callable[[str, ExecutionResult], None]] = None
    on_error: Optional[Callable[[str, Exception, dict[str, Any]], None]] = None
    on_checkpoint: Optional[Callable[[str, dict[str, Any]], None]] = None


class GraphRunner:
    """
    Executes compiled LangGraph graphs with lifecycle callbacks,
    checkpoint/resume support, timeout handling, and optional profiling.
    
    Example:
        runner = GraphRunner(compiled_graph, ExecutionConfig(max_execution_time=30.0))
        result = runner.invoke(initial_state, callbacks)
    """
    
    def __init__(
        self,
        compiled_graph: Any,
        config: Optional[ExecutionConfig] = None
    ) -> None:
        """
        Initialize the GraphRunner.
        
        Args:
            compiled_graph: A compiled LangGraph graph (from compile()).
            config: Execution configuration. Uses defaults if None.
        """
        self.compiled_graph = compiled_graph
        self.config = config or ExecutionConfig()
        self.checkpoint_manager: Optional[CheckpointManager] = None
        self._profiling_data: dict[str, Any] = {}
        self._node_count: int = 0
        
        # Validate compiled graph has required methods
        if not hasattr(compiled_graph, "invoke"):
            raise TypeError("compiled_graph must have an 'invoke' method")
        if not hasattr(compiled_graph, "stream"):
            raise TypeError("compiled_graph must have a 'stream' method")
    
    def invoke(
        self,
        initial_state: dict[str, Any],
        callbacks: Optional[ExecutionCallbacks] = None,
    ) -> dict[str, Any]:
        """
        Execute the graph synchronously (blocking) from initial_state.
        
        Args:
            initial_state: Initial graph state as a dict.
            callbacks: Optional execution callbacks.
        
        Returns:
            Final graph state after execution completes.
        
        Raises:
            RuntimeError: If graph execution fails entirely.
        """
        callbacks = callbacks or ExecutionCallbacks()
        self._reset_profiling()
        
        # Create async event loop if not already in one
        try:
            loop = asyncio.get_running_loop()
            # Already in async context - need to use different approach
            return self._invoke_sync_wrapper(initial_state, callbacks)
        except RuntimeError:
            # Not in async context, safe to create new loop
            return asyncio.run(self._invoke_async(initial_state, callbacks))
    
    def _invoke_sync_wrapper(
        self,
        initial_state: dict[str, Any],
        callbacks: ExecutionCallbacks
    ) -> dict[str, Any]:
        """
        Fallback wrapper when already inside an async loop.
        Uses a temporary thread to run the async invoke.
        """
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                self._invoke_async(initial_state, callbacks)
            )
            return future.result()
    
    async def _invoke_async(
        self,
        initial_state: dict[str, Any],
        callbacks: ExecutionCallbacks
    ) -> dict[str, Any]:
        """
        Internal async implementation of invoke.
        """
        current_state = dict(initial_state)
        node_results: list[ExecutionResult] = []
        
        try:
            # Use the graph's invoke method directly with callbacks support
            # The compiled graph's invoke already handles node iteration internally
            # We wrap it to inject our callbacks per node
            
            config = {"callbacks": self._make_langchain_callback(callbacks)}
            
            if self.config.enable_profiling:
                start_time = time.perf_counter()
            
            # Invoke the graph - this iterates through nodes internally
            final_state = await self.compiled_graph.ainvoke(current_state, config)
            
            if self.config.enable_profiling:
                elapsed = (time.perf_counter() - start_time) * 1000
                self._profiling_data["total_duration_ms"] = elapsed
                self._profiling_data["total_nodes"] = self._node_count
            
            return final_state
            
        except Exception as e:
            raise RuntimeError(f"Graph execution failed: {e}") from e
    
    def stream(
        self,
        initial_state: dict[str, Any]
    ) -> Generator[dict[str, Any], None, None]:
        """
        Execute the graph and yield intermediate states (streaming).
        
        Args:
            initial_state: Initial graph state.
        
        Yields:
            Intermediate graph states as each node completes.
        
        Raises:
            RuntimeError: If streaming execution fails.
        """
        try:
            loop = asyncio.get_running_loop()
            # Already in async context
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    self._stream_async,
                    initial_state
                )
                for item in future.result():
                    yield item
        except RuntimeError:
            # Not in async context
            for item in asyncio.run(self._stream_async(initial_state)):
                yield item
    
    async def _stream_async(
        self,
        initial_state: dict[str, Any]
    ) -> Generator[dict[str, Any], None, None]:
        """
        Internal async implementation of stream.
        """
        current_state = dict(initial_state)
        
        try:
            async for event in self.compiled_graph.astream(current_state):
                # event is a dict mapping node_name -> node output
                yield event
        except Exception as e:
            raise RuntimeError(f"Streaming execution failed: {e}") from e
    
    def resume(
        self,
        checkpoint_id: str,
        resume_input: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Resume execution from a checkpoint with new input.
        
        Args:
            checkpoint_id: ID of the checkpoint to resume from.
            resume_input: Input to provide when resuming.
        
        Returns:
            Final graph state after resumed execution.
        
        Raises:
            KeyError: If checkpoint_id not found.
            RuntimeError: If resume execution fails.
        """
        if self.checkpoint_manager is None:
            raise RuntimeError("CheckpointManager not configured - cannot resume")
        
        checkpoint: Checkpoint = self.checkpoint_manager.get_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise KeyError(f"Checkpoint '{checkpoint_id}' not found")
        
        # Replay from checkpoint
        try:
            return asyncio.run(self._resume_async(checkpoint, resume_input))
        except Exception as e:
            raise RuntimeError(f"Resume execution failed: {e}") from e
    
    async def _resume_async(
        self,
        checkpoint: Checkpoint,
        resume_input: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Internal async implementation of resume.
        """
        # Resume uses the checkpoint's saved state as the base
        base_state = checkpoint.get("state", {})
        merged_state = {**base_state, **resume_input}
        
        # Continue graph execution from checkpoint
        # This requires the graph to support resume via interrupt handling
        try:
            config = {"resume": True}
            result = await self.compiled_graph.ainvoke(merged_state, config)
            return result
        except Exception as e:
            raise RuntimeError(f"Resume failed: {e}") from e
    
    def _execute_node(
        self,
        node_name: str,
        state: dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute a single node in the graph.
        
        This is the core execution primitive used for per-node timing
        and error handling when iterating through nodes manually.
        
        Args:
            node_name: Name of the node to execute.
            state: Current graph state.
        
        Returns:
            ExecutionResult with status, timing, and output state.
        """
        if self.config.enable_profiling:
            start_time = time.perf_counter()
        
        error_msg = None
        output_state = None
        
        try:
            # Get the node from the graph
            node = self.compiled_graph.nodes.get(node_name)
            if node is None:
                raise ValueError(f"Node '{node_name}' not found in graph")
            
            # Execute the node with optional timeout
            if self.config.max_execution_time is not None:
                # Use asyncio.run with timeout
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, node.ainvoke(state))
                    try:
                        output_state = future.result(timeout=self.config.max_execution_time)
                    except concurrent.futures.TimeoutError:
                        return ExecutionResult(
                            node_name=node_name,
                            status=ExecutionStatus.TIMEOUT,
                            duration_ms=self.config.max_execution_time * 1000,
                            error=f"Node execution timed out after {self.config.max_execution_time}s",
                            output_state=state
                        )
            else:
                output_state = asyncio.run(node.ainvoke(state))
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            output_state = state
        finally:
            if self.config.enable_profiling:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._profiling_data.setdefault("nodes", {})[node_name] = {
                    "duration_ms": duration_ms,
                    "status": "failed" if error_msg else "success"
                }
        
        status = ExecutionStatus.FAILED if error_msg else ExecutionStatus.SUCCESS
        return ExecutionResult(
            node_name=node_name,
            status=status,
            duration_ms=duration_ms if self.config.enable_profiling else 0,
            error=error_msg,
            output_state=output_state
        )
    
    def _handle_node_error(
        self,
        node_name: str,
        error: Exception,
        state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle an error that occurred during node execution.
        
        Provides centralized error handling with:
        - Error logging
        - State recovery
        - Optional retry logic
        
        Args:
            node_name: Name of the node that raised the error.
            error: The exception that was raised.
            state: Graph state at time of error.
        
        Returns:
            Potentially modified state (error recovery, logging, etc.).
        """
        error_type = type(error).__name__
        error_msg = str(error)
        stack_trace = traceback.format_exc()
        
        # Log error details
        error_record = {
            "node": node_name,
            "error_type": error_type,
            "message": error_msg,
            "stack": stack_trace,
            "state_keys": list(state.keys())
        }
        
        self._profiling_data.setdefault("errors", []).append(error_record)
        
        # Default behavior: attach error to state for downstream handling
        # This allows the graph to define custom error-handling nodes
        recovered_state = {
            **state,
            "__last_error__": {
                "node": node_name,
                "type": error_type,
                "message": error_msg
            }
        }
        
        return recovered_state
    
    def _make_langchain_callback(
        self,
        callbacks: ExecutionCallbacks
    ) -> Any:
        """
        Create a LangChain-compatible callback handler from our ExecutionCallbacks.
        
        LangChain uses a BaseCallbackHandler chain for its own callback system.
        We adapt our callbacks to that interface.
        """
        from langgraph.callbacks.base import BaseCallbackHandler
        
        class ExecutionCallbackHandler(BaseCallbackHandler):
            """Adapter that bridges ExecutionCallbacks to LangChain's callback system."""
            
            def __init__(inner_self):
                super().__init__()
                inner_self._callbacks = callbacks
                inner_self._node_stack: list[str] = []
            
            @property
            def always_verbose(inner_self) -> bool:
                return True
            
            def on_chain_start(
                inner_self,
                serialized: dict[str, Any],
                inputs: dict[str, Any],
                **kwargs: Any
            ) -> None:
                # LangChain calls this at various levels; we filter for node-level
                pass
            
            def on_chain_end(
                inner_self,
                outputs: dict[str, Any],
                **kwargs: Any
            ) -> None:
                pass
            
            def on_node_start(
                inner_self,
                name: str,
                **kwargs: Any
            ) -> None:
                inner_self._node_stack.append(name)
                if callbacks.on_node_start:
                    callbacks.on_node_start(name, kwargs.get("inputs", {}))
            
            def on_node_end(
                inner_self,
                name: str,
                **kwargs: Any
            ) -> None:
                if callbacks.on_node_end:
                    # Construct ExecutionResult from available info
                    outputs = kwargs.get("outputs", {})
                    result = ExecutionResult(
                        node_name=name,
                        status=ExecutionStatus.SUCCESS,
                        duration_ms=0,
                        output_state=outputs if isinstance(outputs, dict) else None
                    )
                    callbacks.on_node_end(name, result)
                inner_self._node_stack.pop()
            
            def on_tool_error(
                inner_self,
                error: Exception,
                **kwargs: Any
            ) -> None:
                if callbacks.on_error:
                    node_name = inner_self._node_stack[-1] if inner_self._node_stack else "unknown"
                    callbacks.on_error(node_name, error, kwargs.get("inputs", {}))
            
            def on_text(
                inner_self,
                text: str,
                **kwargs: Any
            ) -> None:
                pass
        
        return ExecutionCallbackHandler()
    
    def _reset_profiling(self) -> None:
        """Reset profiling data for a new execution run."""
        self._profiling_data = {
            "nodes": {},
            "errors": [],
            "start_time": time.time()
        }
    
    def get_profiling_data(self) -> dict[str, Any]:
        """
        Get collected profiling data from the last execution.
        
        Returns:
            Profiling data dict with node timings and errors.
            Returns empty dict if profiling is not enabled.
        """
        if not self.config.enable_profiling:
            return {}
        
        result = dict(self._profiling_data)
        if "start_time" in result:
            result["wall_clock_duration_s"] = time.time() - result["start_time"]
        
        return result
    
    def set_checkpoint_manager(self, manager: CheckpointManager) -> None:
        """
        Attach a CheckpointManager to enable checkpoint/resume functionality.
        
        Args:
            manager: A CheckpointManager instance.
        """
        self.checkpoint_manager = manager
    
    def checkpoint_current_state(
        self,
        state: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Manually save a checkpoint of the current state.
        
        Args:
            state: Graph state to checkpoint.
            metadata: Optional metadata to attach.
        
        Returns:
            The checkpoint ID.
        
        Raises:
            RuntimeError: If CheckpointManager is not configured.
        """
        if self.checkpoint_manager is None:
            raise RuntimeError("CheckpointManager not configured")
        
        checkpoint_data = {
            "state": state,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        import uuid
        checkpoint_id = str(uuid.uuid4())[:8]
        
        self.checkpoint_manager.save_checkpoint(checkpoint_id, checkpoint_data)
        
        return checkpoint_id
    
    def get_execution_history(self) -> list[ExecutionResult]:
        """
        Get the execution history from the last invoke/stream call.
        
        Returns:
            List of ExecutionResults for each node executed.
        """
        history = []
        for node_name, node_data in self._profiling_data.get("nodes", {}).items():
            history.append(ExecutionResult(
                node_name=node_name,
                status=ExecutionStatus.SUCCESS if node_data.get("status") == "success" else ExecutionStatus.FAILED,
                duration_ms=node_data.get("duration_ms", 0),
                output_state=None
            ))
        return history
    
    def __repr__(self) -> str:
        return (
            f"GraphRunner(graph={self.compiled_graph.graph.name if hasattr(self.compiled_graph, 'graph') else 'unknown'}, "
            f"config={self.config})"
        )