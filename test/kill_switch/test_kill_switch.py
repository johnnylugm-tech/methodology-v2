"""
Tests for KillSwitch facade.
"""

import pytest
import tempfile
from pathlib import Path

from implement.kill_switch.enums import CircuitState, KillReason
from implement.kill_switch.kill_switch import KillSwitch
from implement.kill_switch.models import MonitorConfig


@pytest.fixture
def temp_state_path():
    """Create a temporary directory for state storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "state"


@pytest.fixture
def kill_switch(temp_state_path):
    """Create a KillSwitch instance for testing."""
    from implement.kill_switch.state_manager import StateManager
    state_manager = StateManager(state_path=temp_state_path)
    return KillSwitch(state_manager=state_manager)


@pytest.fixture
def default_config():
    """Create a default MonitorConfig."""
    return MonitorConfig(
        agent_id="test-agent",
        error_rate_threshold=0.10,
        failure_threshold=5,
        cooldown_seconds=60,
    )


class TestKillSwitch:
    """Tests for KillSwitch facade class."""

    def test_start_monitoring_delegates_to_health_monitor(self, kill_switch, default_config):
        """Monitoring starts correctly."""
        agent_id = "test-agent"

        # Before start
        assert not kill_switch.health_monitor.is_monitoring(agent_id)

        # Start monitoring
        kill_switch.start_monitoring(agent_id, config=default_config)

        # After start - should be delegated to health_monitor
        assert kill_switch.health_monitor.is_monitoring(agent_id)

        # Circuit should also be initialized
        assert kill_switch.circuit_breaker.get_state(agent_id) == CircuitState.CLOSED

    def test_manual_trigger_calls_interrupt_engine(self, kill_switch):
        """Manual trigger executes interrupt."""
        agent_id = "test-agent"

        # Trigger manual kill
        event = kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Suspicious behavior",
            operator_id="operator-1",
        )

        assert event is not None
        assert event.agent_id == agent_id
        assert event.reason == "Suspicious behavior"
        assert event.triggered_by == "operator-1"
        assert event.reason_type == KillReason.MANUAL_TRIGGER

    def test_re_enable_clears_killed_state(self, kill_switch):
        """re_enable allows agent to restart."""
        agent_id = "test-agent"

        # First, kill the agent
        kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test kill",
            operator_id="operator-1",
        )

        # Agent should be killed
        assert kill_switch.is_agent_circuit_open(agent_id) is True

        # Re-enable
        result = kill_switch.re_enable(
            agent_id=agent_id,
            operator_id="operator-1",
            acknowledgment="User acknowledged kill reason",
        )

        assert result is True

        # After re-enable, agent should not be circuit open
        # Note: The circuit breaker state is reset, but state_manager
        # is also cleared, so is_agent_circuit_open should return False
        assert kill_switch.is_agent_circuit_open(agent_id) is False

    def test_is_agent_circuit_open_delegates(self, kill_switch):
        """Circuit state check delegated correctly."""
        agent_id = "test-agent"

        # Start monitoring (initial state should be closed)
        kill_switch.start_monitoring(agent_id)

        # Should not be open initially
        assert kill_switch.is_agent_circuit_open(agent_id) is False

        # Manual trigger should open the circuit
        kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test",
            operator_id="operator-1",
        )

        # Now circuit should be open
        assert kill_switch.is_agent_circuit_open(agent_id) is True

    def test_get_interrupt_history_returns_events(self, kill_switch):
        """History retrieval works."""
        agent_id = "test-agent"

        # Trigger an interrupt
        kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test reason",
            operator_id="operator-1",
        )

        # Get history
        history = kill_switch.get_interrupt_history()

        assert len(history) >= 1

        # Find our event
        agent_events = [e for e in history if e.agent_id == agent_id]
        assert len(agent_events) >= 1

        event = agent_events[-1]
        assert event.reason == "Test reason"

    def test_get_interrupt_history_with_agent_filter(self, kill_switch):
        """History can be filtered by agent_id."""
        agent_a = "agent-a"
        agent_b = "agent-b"

        kill_switch.manual_trigger(agent_id=agent_a, reason="A", operator_id="op")
        kill_switch.manual_trigger(agent_id=agent_b, reason="B", operator_id="op")

        # Filter by agent
        history_a = kill_switch.get_interrupt_history(agent_id=agent_a)
        assert all(e.agent_id == agent_a for e in history_a)

    def test_stop_monitoring_removes_agent(self, kill_switch, default_config):
        """stop_monitoring removes agent from health monitor."""
        agent_id = "test-agent"

        kill_switch.start_monitoring(agent_id, config=default_config)
        assert kill_switch.health_monitor.is_monitoring(agent_id)

        kill_switch.stop_monitoring(agent_id)
        assert not kill_switch.health_monitor.is_monitoring(agent_id)

    def test_get_agent_state(self, kill_switch):
        """get_agent_state returns correct circuit state."""
        agent_id = "test-agent"

        # Start monitoring
        kill_switch.start_monitoring(agent_id)

        # Initial state should be CLOSED
        assert kill_switch.get_agent_state(agent_id) == CircuitState.CLOSED

    def test_re_enable_without_kill_noops(self, kill_switch):
        """re_enable on non-killed agent is a no-op."""
        agent_id = "test-agent"

        # Start monitoring but don't kill
        kill_switch.start_monitoring(agent_id)

        # Re-enable should still work (no-op)
        result = kill_switch.re_enable(
            agent_id=agent_id,
            operator_id="operator-1",
            acknowledgment="acknowledged",
        )

        assert result is True

    def test_manual_trigger_with_different_reason_types(self, kill_switch):
        """Manual trigger can use different reason types."""
        # This tests that the facade correctly passes reason_type
        # We can't easily test auto-trigger reasons, but we can verify
        # the manual trigger path works

        event = kill_switch.manual_trigger(
            agent_id="test-agent",
            reason="Testing",
            operator_id="operator-1",
        )

        assert event.reason_type == KillReason.MANUAL_TRIGGER

    def test_get_agent_health_returns_metrics(self, kill_switch):
        """get_agent_health returns health metrics from health_monitor."""
        agent_id = "test-agent"

        kill_switch.start_monitoring(agent_id)

        metrics = kill_switch.get_agent_health(agent_id)

        assert metrics is not None
        assert metrics.agent_id == agent_id
        assert hasattr(metrics, 'error_rate')
        assert hasattr(metrics, 'latency_p99_ms')
        assert hasattr(metrics, 'memory_usage_percent')
        assert hasattr(metrics, 'output_rate_kbps')
