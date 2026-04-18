"""
Tests for StateManager component.
"""

import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from implement.kill_switch.enums import CircuitState
from implement.kill_switch.models import CircuitBreakerState
from implement.kill_switch.state_manager import StateManager


@pytest.fixture
def temp_state_path():
    """Create a temporary directory for state storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "state"


@pytest.fixture
def state_manager(temp_state_path):
    """Create a StateManager instance for testing."""
    return StateManager(state_path=temp_state_path)


class TestStateManager:
    """Tests for StateManager class."""

    def test_save_and_load_state(self, state_manager):
        """State persists and loads correctly."""
        agent_id = "test-agent"
        now = datetime.now(timezone.utc)

        state = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.OPEN,
            failure_count=5,
            last_failure_time=now,
            opened_at=now,
        )

        # Save state
        state_manager.save_state(agent_id, state)

        # Load state
        loaded = state_manager.load_state(agent_id)

        assert loaded is not None
        assert loaded.agent_id == agent_id
        assert loaded.state == CircuitState.OPEN
        assert loaded.failure_count == 5
        assert loaded.last_failure_time is not None
        assert loaded.opened_at is not None

    def test_is_agent_killed_returns_correct_status(self, state_manager):
        """Reflects persisted KILLED state."""
        agent_id = "test-agent"
        now = datetime.now(timezone.utc)

        # Initially not killed
        assert state_manager.is_agent_killed(agent_id) is False

        # Save KILLED (OPEN) state
        state = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.OPEN,
            opened_at=now,
        )
        state_manager.save_state(agent_id, state)

        # Now should be killed
        assert state_manager.is_agent_killed(agent_id) is True

        # Save CLOSED state
        state_closed = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.CLOSED,
        )
        state_manager.save_state(agent_id, state_closed)

        # Should not be killed
        assert state_manager.is_agent_killed(agent_id) is False

    def test_clear_state_removes_persistence(self, state_manager):
        """clear_state deletes file."""
        agent_id = "test-agent"

        # Save state
        state = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.OPEN,
        )
        state_manager.save_state(agent_id, state)

        # Verify saved
        assert state_manager.load_state(agent_id) is not None

        # Clear state
        state_manager.clear_state(agent_id)

        # Should be gone
        assert state_manager.load_state(agent_id) is None

    def test_load_state_returns_none_if_missing(self, state_manager):
        """load_state returns None for missing agent."""
        result = state_manager.load_state("nonexistent-agent")
        assert result is None

    def test_multiple_agents_independent(self, state_manager):
        """Each agent's state is independent."""
        now = datetime.now(timezone.utc)

        # Save states for multiple agents
        state_a = CircuitBreakerState(
            agent_id="agent-a",
            state=CircuitState.OPEN,
            failure_count=3,
        )
        state_b = CircuitBreakerState(
            agent_id="agent-b",
            state=CircuitState.CLOSED,
            failure_count=0,
        )

        state_manager.save_state("agent-a", state_a)
        state_manager.save_state("agent-b", state_b)

        # Verify they are independent
        loaded_a = state_manager.load_state("agent-a")
        loaded_b = state_manager.load_state("agent-b")

        assert loaded_a.state == CircuitState.OPEN
        assert loaded_a.failure_count == 3
        assert loaded_b.state == CircuitState.CLOSED
        assert loaded_b.failure_count == 0

        # Clearing one doesn't affect the other
        state_manager.clear_state("agent-a")

        assert state_manager.load_state("agent-a") is None
        assert state_manager.load_state("agent-b") is not None
        assert state_manager.load_state("agent-b").state == CircuitState.CLOSED

    def test_state_persists_across_manager_instances(self, temp_state_path):
        """State persists when creating new StateManager instance."""
        agent_id = "test-agent"

        # Save state with first manager
        manager1 = StateManager(state_path=temp_state_path)
        state = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.HALF_OPEN,
            failure_count=2,
        )
        manager1.save_state(agent_id, state)

        # Create new manager with same path
        manager2 = StateManager(state_path=temp_state_path)

        # Load should succeed
        loaded = manager2.load_state(agent_id)
        assert loaded is not None
        assert loaded.state == CircuitState.HALF_OPEN
        assert loaded.failure_count == 2

    def test_circuit_state_serialization_roundtrip(self, state_manager):
        """All CircuitState values serialize and deserialize correctly."""
        agent_id = "test-agent"

        for circuit_state in [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]:
            state = CircuitBreakerState(
                agent_id=agent_id,
                state=circuit_state,
            )
            state_manager.save_state(agent_id, state)

            loaded = state_manager.load_state(agent_id)
            assert loaded.state == circuit_state

    def test_datetime_fields_serialize_correctly(self, state_manager):
        """Datetime fields are correctly serialized and deserialized."""
        agent_id = "test-agent"
        now = datetime.now(timezone.utc)

        state = CircuitBreakerState(
            agent_id=agent_id,
            state=CircuitState.OPEN,
            last_failure_time=now,
            cooldown_end=now,
            last_success_time=now,
            opened_at=now,
            closed_at=now,
        )

        state_manager.save_state(agent_id, state)
        loaded = state_manager.load_state(agent_id)

        # All datetime fields should be preserved
        assert loaded.last_failure_time is not None
        assert loaded.cooldown_end is not None
        assert loaded.last_success_time is not None
        assert loaded.opened_at is not None
        assert loaded.closed_at is not None

    def test_clear_nonexistent_agent_does_not_raise(self, state_manager):
        """clear_state on nonexistent agent does not raise."""
        # Should not raise
        state_manager.clear_state("nonexistent-agent")
