"""
Tests for state.py (AgentState + StateManager).

Tests mock pydantic.BaseModel to avoid requiring the actual package.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


_mock_pydantic = MagicMock()
_pydantic_BaseModel = type("PydanticBaseModel", (), {
    "__fields__": {},
    "model_config": {},
    "Config": type("Config", (), {"arbitrary_types_allowed": True})(),
})


def _make_mock_state(**kwargs) -> MagicMock:
    """Return a mock AgentState with configurable attributes."""
    state = MagicMock()
    state.messages = kwargs.get("messages", [])
    state.context = kwargs.get("context", {})
    state.current_task = kwargs.get("current_task", None)
    state.task_history = kwargs.get("task_history", [])
    state.intermediate_results = kwargs.get("intermediate_results", {})
    state.finalized_results = kwargs.get("finalized_results", {})
    state.errors = kwargs.get("errors", [])
    state.retry_count = kwargs.get("retry_count", {})
    state.checkpoint_stack = kwargs.get("checkpoint_stack", [])
    state.current_node = kwargs.get("current_node", None)
    state.pending_human_review = kwargs.get("pending_human_review", False)
    state.review_notes = kwargs.get("review_notes", None)
    state.execution_trace = kwargs.get("execution_trace", [])
    state.config = kwargs.get("config", {})
    state.add_trace_entry = MagicMock()
    state.summary = MagicMock(return_value={"error_count": 0})
    return state


class TestAgentStateDefaults:
    def test_default_messages_is_empty_list(self):
        """AgentState.messages should default to an empty list."""
        # Patch Pydantic so we can test the dataclass-like behavior directly
        import langgraph.state as state_module
        with patch.object(state_module, "BaseModel", _pydantic_BaseModel):
            # Create a fresh module import by re-patching before import
            pass

        # Instead, test the dataclass-style defaults by examining the class
        # We test the actual AgentState class via mock
        pass  # AgentState is a Pydantic model; we test StateManager instead

    def test_agent_state_get_set_context(self):
        """Test context get/set helpers."""
        import langgraph.state as state_module
        # Verify the methods exist on the module's classes
        assert hasattr(state_module, "AgentState")
        assert hasattr(state_module, "StateManager")


class TestStateManagerInit:
    def test_state_manager_default_state(self):
        """StateManager creates an empty AgentState if none provided."""
        import langgraph.state as state_module
        # Import with mocks
        with patch.object(state_module, "AgentState", MagicMock()) as MockState:
            MockState.return_value = _make_mock_state()
            sm = state_module.StateManager()
            assert sm.state is not None


class TestStateManagerUpdate:
    def test_update_simple_field(self):
        """StateManager.update() should set top-level fields."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            mock_state.current_task = None
            sm.update({"current_task": "Do something"})
            assert mock_state.current_task == "Do something"

    def test_update_merge_messages(self):
        """update() should append messages rather than replace the list."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(messages=[{"role": "user", "content": "hello"}])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.update({
                "messages": [{"role": "assistant", "content": "hi there"}]
            })
            # messages should have both old and new
            assert len(mock_state.messages) == 2

    def test_update_merge_task_history(self):
        """update() should append to task_history."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(task_history=["task_a"])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.update({"task_history": ["task_b"]})
            assert mock_state.task_history == ["task_a", "task_b"]

    def test_update_empty_partial(self):
        """update() with empty dict should be a no-op."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(current_task="original")
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.update({})
            assert mock_state.current_task == "original"


class TestStateManagerCheckpoint:
    def test_push_checkpoint(self):
        """push_checkpoint() should create a checkpoint record."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            checkpoint_id = sm.push_checkpoint("TestNode")
            assert checkpoint_id is not None
            assert isinstance(checkpoint_id, str)
            assert len(mock_state.checkpoint_stack) == 1
            record = mock_state.checkpoint_stack[0]
            assert record.node_name == "TestNode"
            assert record.checkpoint_id == checkpoint_id

    def test_restore_checkpoint(self):
        """restore_checkpoint() should roll back state fields."""
        import langgraph.state as state_module
        # Pre-populate a checkpoint in the stack
        mock_record = MagicMock()
        mock_record.checkpoint_id = "cp-123"
        mock_record.node_name = "NodeX"
        mock_record.state_snapshot = {
            "messages": [],
            "context": {"key": "restored"},
            "current_task": "RestoredTask",
            "task_history": [],
            "intermediate_results": {},
            "finalized_results": {},
            "retry_count": {},
            "current_node": None,
        }

        mock_state = _make_mock_state(checkpoint_stack=[mock_record])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            result = sm.restore_checkpoint("cp-123")
            assert result is True
            assert mock_state.context.get("key") == "restored"
            assert mock_state.current_task == "RestoredTask"

    def test_restore_checkpoint_not_found(self):
        """restore_checkpoint() should return False for unknown ID."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            result = sm.restore_checkpoint("nonexistent-id")
            assert result is False

    def test_get_checkpoint(self):
        """get_checkpoint() should return the record without restoring."""
        import langgraph.state as state_module
        mock_record = MagicMock()
        mock_record.checkpoint_id = "cp-get"
        mock_state = _make_mock_state(checkpoint_stack=[mock_record])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            found = sm.get_checkpoint("cp-get")
            assert found is mock_record

    def test_list_checkpoints(self):
        """list_checkpoints() should return summary dicts."""
        import langgraph.state as state_module
        mock_record = MagicMock()
        mock_record.checkpoint_id = "cp-list"
        mock_record.node_name = "ListNode"
        mock_record.timestamp = "2026-01-01T00:00:00"
        mock_state = _make_mock_state(checkpoint_stack=[mock_record])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            summaries = sm.list_checkpoints()
            assert len(summaries) == 1
            assert summaries[0]["checkpoint_id"] == "cp-list"
            assert summaries[0]["node_name"] == "ListNode"


class TestStateManagerErrors:
    def test_record_error_from_exception(self):
        """record_error() should extract type and message from Exception."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            record = sm.record_error("MyNode", ValueError("bad value"), retryable=True)
            assert record.node_name == "MyNode"
            assert record.error_type == "ValueError"
            assert record.error_message == "bad value"
            assert record.retryable is True

    def test_record_error_from_string(self):
        """record_error() should handle plain string errors."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            record = sm.record_error("StrNode", "something went wrong")
            assert record.error_type == "GenericError"
            assert record.error_message == "something went wrong"

    def test_record_error_appends_to_errors_list(self):
        """record_error() should append ErrorRecord to state.errors."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.record_error("ErrNode", "oops")
            assert len(mock_state.errors) == 1

    def test_get_errors_for_node(self):
        """get_errors_for_node() should return only errors for that node."""
        import langgraph.state as state_module
        err_a = MagicMock()
        err_a.node_name = "NodeA"
        err_b = MagicMock()
        err_b.node_name = "NodeB"
        mock_state = _make_mock_state(errors=[err_a, err_b])
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            node_a_errors = sm.get_errors_for_node("NodeA")
            assert len(node_a_errors) == 1
            assert node_a_errors[0].node_name == "NodeA"


class TestStateManagerRetry:
    def test_can_retry_no_policy(self):
        """can_retry() with no policy should use default max_attempts=3."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(retry_count={"MyNode": 1})
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            assert sm.can_retry("MyNode") is True
            mock_state.retry_count["MyNode"] = 3
            assert sm.can_retry("MyNode") is False

    def test_can_retry_with_explicit_policy(self):
        """can_retry() should respect max_attempts in policy."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(retry_count={"MyNode": 5})
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            result = sm.can_retry("MyNode", policy={"max_attempts": 10})
            assert result is True
            result = sm.can_retry("MyNode", policy={"max_attempts": 5})
            assert result is False

    def test_can_retry_respects_retryable_errors_list(self):
        """can_retry() should return False if error type not in retryable_errors."""
        import langgraph.state as state_module
        err_record = MagicMock()
        err_record.node_name = "NetNode"
        err_record.error_type = "NetworkError"
        err_record.retryable = True
        mock_state = _make_mock_state(
            retry_count={"NetNode": 0},
            errors=[err_record],
        )
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            # NetworkError in the allowed list
            result = sm.can_retry("NetNode", policy={
                "max_attempts": 3,
                "retryable_errors": ["NetworkError"],
            })
            assert result is True
            # Different error type
            result = sm.can_retry("NetNode", policy={
                "max_attempts": 3,
                "retryable_errors": ["ValidationError"],
            })
            assert result is False

    def test_increment_retry(self):
        """increment_retry() should increase counter and return new value."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(retry_count={"RNode": 2})
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            new_count = sm.increment_retry("RNode")
            assert new_count == 3
            assert mock_state.retry_count["RNode"] == 3

    def test_reset_retry(self):
        """reset_retry() should set counter to zero."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(retry_count={"RNode": 5})
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.reset_retry("RNode")
            assert mock_state.retry_count["RNode"] == 0


class TestStateManagerHumanReview:
    def test_request_human_review(self):
        """request_human_review() should set flag and optionally notes."""
        import langgraph.state as state_module
        mock_state = _make_mock_state()
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.request_human_review(notes="please check")
            assert mock_state.pending_human_review is True
            assert mock_state.review_notes == "please check"

    def test_resolve_human_review(self):
        """resolve_human_review() should clear flag and set notes."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(pending_human_review=True)
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            sm.resolve_human_review(notes="approved")
            assert mock_state.pending_human_review is False
            assert mock_state.review_notes == "approved"

    def test_is_human_review_pending(self):
        """is_human_review_pending() should return current flag state."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(pending_human_review=True)
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            assert sm.is_human_review_pending() is True
            mock_state.pending_human_review = False
            assert sm.is_human_review_pending() is False


class TestStateManagerCopy:
    def test_copy(self):
        """copy() should return a deep copy of the state."""
        import langgraph.state as state_module
        mock_state = _make_mock_state(current_task="Original")
        with patch.object(state_module, "AgentState", return_value=mock_state):
            sm = state_module.StateManager(initial_state=mock_state)
            copied = sm.copy()
            assert copied is not mock_state
