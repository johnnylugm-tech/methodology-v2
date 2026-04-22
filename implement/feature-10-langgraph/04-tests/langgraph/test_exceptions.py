"""Tests for ml_langgraph.exceptions."""

from __future__ import annotations

import pytest

from ml_langgraph.exceptions import (
    CheckpointAlreadyExistsError,
    CheckpointNotFoundError,
    CircularDependencyError,
    CycleExceededError,
    DuplicateNodeError,
    FeatureError,
    GraphValidationError,
    InvalidEdgeError,
    NodeNotFoundError,
    OrphanedNodeError,
    RetryExhaustedError,
    StateSchemaError,
    TimeoutError,
)


class TestFeatureError:
    def test_message_stored_and_returned(self):
        err = FeatureError("something went wrong")
        assert err.message == "something went wrong"
        assert str(err) == "something went wrong"

    def test_inherits_from_exception(self):
        err = FeatureError("test")
        assert isinstance(err, Exception)

    def test_custom_message_overrides_default(self):
        err = FeatureError("custom message")
        assert str(err) == "custom message"


class TestDuplicateNodeError:
    def test_default_message_includes_node_name(self):
        err = DuplicateNodeError("node_a")
        assert "node_a" in str(err)
        assert err.node_name == "node_a"

    def test_custom_message(self):
        err = DuplicateNodeError("node_a", message="custom error")
        assert str(err) == "custom error"
        assert err.node_name == "node_a"

    def test_inherits_from_feature_error(self):
        assert issubclass(DuplicateNodeError, FeatureError)


class TestOrphanedNodeError:
    def test_default_message_lists_all_orphaned_nodes(self):
        err = OrphanedNodeError(["node_x", "node_y"])
        assert "node_x" in str(err)
        assert "node_y" in str(err)
        assert err.node_names == ["node_x", "node_y"]

    def test_custom_message(self):
        err = OrphanedNodeError(["node_x"], message="custom orphaned msg")
        assert str(err) == "custom orphaned msg"
        assert err.node_names == ["node_x"]

    def test_inherits_from_feature_error(self):
        assert issubclass(OrphanedNodeError, FeatureError)


class TestCycleExceededError:
    def test_attributes_set(self):
        err = CycleExceededError(cycle_count=10, max_cycles=5)
        assert err.cycle_count == 10
        assert err.max_cycles == 5
        assert "10" in str(err)
        assert "5" in str(err)

    def test_custom_message(self):
        err = CycleExceededError(3, 1, message="too many cycles")
        assert str(err) == "too many cycles"

    def test_inherits_from_feature_error(self):
        assert issubclass(CycleExceededError, FeatureError)


class TestStateSchemaError:
    def test_attributes_set(self):
        err = StateSchemaError(schema="expected_schema", actual="got_this")
        assert err.schema == "expected_schema"
        assert err.actual == "got_this"
        assert "expected_schema" in str(err)
        assert "got_this" in str(err)

    def test_custom_message(self):
        err = StateSchemaError("s", "a", message="schema mismatch")
        assert str(err) == "schema mismatch"

    def test_inherits_from_feature_error(self):
        assert issubclass(StateSchemaError, FeatureError)


class TestCheckpointNotFoundError:
    def test_checkpoint_id_stored(self):
        err = CheckpointNotFoundError(checkpoint_id="chk_abc123")
        assert err.checkpoint_id == "chk_abc123"
        assert "chk_abc123" in str(err)

    def test_custom_message(self):
        err = CheckpointNotFoundError("chk1", message="checkpoint gone")
        assert str(err) == "checkpoint gone"

    def test_inherits_from_feature_error(self):
        assert issubclass(CheckpointNotFoundError, FeatureError)


class TestCheckpointAlreadyExistsError:
    def test_checkpoint_id_stored(self):
        err = CheckpointAlreadyExistsError(checkpoint_id="chk_exists")
        assert err.checkpoint_id == "chk_exists"
        assert "chk_exists" in str(err)

    def test_custom_message(self):
        err = CheckpointAlreadyExistsError("chk1", message="already exists!")
        assert str(err) == "already exists!"

    def test_inherits_from_feature_error(self):
        assert issubclass(CheckpointAlreadyExistsError, FeatureError)


class TestTimeoutError:
    def test_attributes_set(self):
        err = TimeoutError(node_name="my_node", timeout_seconds=30.0)
        assert err.node_name == "my_node"
        assert err.timeout_seconds == 30.0
        assert "my_node" in str(err)
        assert "30" in str(err)

    def test_custom_message(self):
        err = TimeoutError("node", 5.0, message="node timed out!")
        assert str(err) == "node timed out!"

    def test_inherits_from_feature_error(self):
        assert issubclass(TimeoutError, FeatureError)


class TestRetryExhaustedError:
    def test_all_attributes_set(self):
        err = RetryExhaustedError(
            node_name="worker_node",
            attempts=4,
            last_error="connection refused",
        )
        assert err.node_name == "worker_node"
        assert err.attempts == 4
        assert err.last_error == "connection refused"
        assert "worker_node" in str(err)
        assert "4" in str(err)
        assert "connection refused" in str(err)

    def test_custom_message(self):
        err = RetryExhaustedError("n", 1, "e", message="give up")
        assert str(err) == "give up"

    def test_inherits_from_feature_error(self):
        assert issubclass(RetryExhaustedError, FeatureError)


class TestGraphValidationError:
    def test_errors_list_stored(self):
        err = GraphValidationError(
            errors=["edge references missing node", "no terminal node"]
        )
        assert err.errors == ["edge references missing node", "no terminal node"]
        assert "edge references missing node" in str(err)

    def test_multiple_errors_formatted(self):
        err = GraphValidationError(errors=["e1", "e2", "e3"])
        assert "3 error(s)" in str(err)

    def test_custom_message(self):
        err = GraphValidationError(["e1"], message="invalid graph")
        assert str(err) == "invalid graph"

    def test_inherits_from_feature_error(self):
        assert issubclass(GraphValidationError, FeatureError)


class TestNodeNotFoundError:
    def test_node_name_stored(self):
        err = NodeNotFoundError(node_name="ghost_node")
        assert err.node_name == "ghost_node"
        assert "ghost_node" in str(err)

    def test_custom_message(self):
        err = NodeNotFoundError("n", message="node not found!")
        assert str(err) == "node not found!"

    def test_inherits_from_feature_error(self):
        assert issubclass(NodeNotFoundError, FeatureError)


class TestInvalidEdgeError:
    def test_all_attributes_set(self):
        err = InvalidEdgeError(
            source="node_a", target="node_b", reason="self-loop not allowed"
        )
        assert err.source == "node_a"
        assert err.target == "node_b"
        assert err.reason == "self-loop not allowed"
        assert "node_a" in str(err)
        assert "node_b" in str(err)
        assert "self-loop not allowed" in str(err)

    def test_custom_message(self):
        err = InvalidEdgeError("s", "t", "r", message="bad edge")
        assert str(err) == "bad edge"

    def test_inherits_from_feature_error(self):
        assert issubclass(InvalidEdgeError, FeatureError)


class TestCircularDependencyError:
    def test_cycle_list_stored(self):
        err = CircularDependencyError(cycle=["a", "b", "c", "a"])
        assert err.cycle == ["a", "b", "c", "a"]
        assert "a -> b -> c -> a" in str(err)

    def test_custom_message(self):
        err = CircularDependencyError(["x", "y"], message="cyclic!")
        assert str(err) == "cyclic!"

    def test_inherits_from_feature_error(self):
        assert issubclass(CircularDependencyError, FeatureError)


class TestExceptionHierarchy:
    def test_all_exceptions_inherit_from_feature_error(self):
        exception_classes = [
            DuplicateNodeError,
            OrphanedNodeError,
            CycleExceededError,
            StateSchemaError,
            CheckpointNotFoundError,
            CheckpointAlreadyExistsError,
            TimeoutError,
            RetryExhaustedError,
            GraphValidationError,
            NodeNotFoundError,
            InvalidEdgeError,
            CircularDependencyError,
        ]
        for cls in exception_classes:
            assert issubclass(cls, FeatureError)

    def test_all_exceptions_inherit_from_base_exception(self):
        exception_classes = [
            FeatureError,
            DuplicateNodeError,
            OrphanedNodeError,
            CycleExceededError,
            StateSchemaError,
            CheckpointNotFoundError,
            CheckpointAlreadyExistsError,
            TimeoutError,
            RetryExhaustedError,
            GraphValidationError,
            NodeNotFoundError,
            InvalidEdgeError,
            CircularDependencyError,
        ]
        for cls in exception_classes:
            assert issubclass(cls, BaseException)