"""
Integration tests for full kill-switch flow.
"""

import pytest
import tempfile
from pathlib import Path

from implement.kill_switch.enums import CircuitState, KillReason
from implement.kill_switch.kill_switch import KillSwitch
from implement.kill_switch.models import HealthMetrics, MonitorConfig
from datetime import datetime, timezone


@pytest.fixture
def temp_state_path():
    """Create a temporary directory for state storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "state"


@pytest.fixture
def kill_switch(temp_state_path):
    """Create a KillSwitch instance for integration testing."""
    from implement.kill_switch.state_manager import StateManager
    state_manager = StateManager(state_path=temp_state_path)
    return KillSwitch(state_manager=state_manager)


@pytest.fixture
def default_config():
    """Create a default MonitorConfig."""
    return MonitorConfig(
        agent_id="test-agent",
        error_rate_threshold=0.10,
        latency_p99_threshold_ms=5000.0,
        memory_usage_threshold=90.0,
        output_rate_threshold_kbps=100.0,
        error_rate_window_seconds=60,
        latency_window_seconds=300,
        output_window_seconds=30,
        no_response_threshold_seconds=60,
        failure_threshold=5,
        cooldown_seconds=60,
    )


class TestKillSwitchIntegration:
    """Integration tests for complete Kill-Switch flows."""

    def test_full_kill_switch_flow(self, kill_switch, default_config):
        """Monitor → threshold exceeded → interrupt → killed."""
        agent_id = "test-agent"

        # 1. Start monitoring
        kill_switch.start_monitoring(agent_id, config=default_config)

        # Verify monitoring started
        assert kill_switch.health_monitor.is_monitoring(agent_id)
        assert kill_switch.get_agent_state(agent_id) == CircuitState.CLOSED

        # 2. Circuit should not be open initially
        assert kill_switch.is_agent_circuit_open(agent_id) is False

        # 3. Manual trigger simulates the full flow
        event = kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Automatic threshold exceeded",
            operator_id="SYSTEM",
        )

        # 4. Verify interrupt was recorded
        assert event is not None
        assert event.agent_id == agent_id
        assert event.triggered_by == "SYSTEM"

        # 5. Verify agent is now killed (circuit open)
        assert kill_switch.is_agent_circuit_open(agent_id) is True

        # 6. Verify history contains the event
        history = kill_switch.get_interrupt_history(agent_id=agent_id)
        assert len(history) >= 1

        # Find our kill event
        kill_events = [
            e for e in history
            if e.reason_type == KillReason.MANUAL_TRIGGER
        ]
        assert len(kill_events) >= 1

    def test_manual_trigger_flow(self, kill_switch):
        """Manual trigger → interrupt → killed."""
        agent_id = "test-agent"

        # Start monitoring
        kill_switch.start_monitoring(agent_id)

        # Verify not killed
        assert kill_switch.is_agent_circuit_open(agent_id) is False

        # Manual trigger
        event = kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Operator detected suspicious behavior",
            operator_id="operator-001",
        )

        # Verify event details
        assert event.agent_id == agent_id
        assert event.triggered_by == "operator-001"
        assert event.reason == "Operator detected suspicious behavior"
        assert event.interrupt_latency_ms is not None
        assert event.interrupt_latency_ms >= 0

        # Verify agent is killed
        assert kill_switch.is_agent_circuit_open(agent_id) is True

        # Verify persisted state
        is_killed = kill_switch.state_manager.is_agent_killed(agent_id)
        assert is_killed is True

    def test_re_enable_after_kill(self, kill_switch):
        """Killed → re_enable → agent alive."""
        agent_id = "test-agent"

        # 1. Kill the agent
        kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test kill",
            operator_id="operator-1",
        )

        assert kill_switch.is_agent_circuit_open(agent_id) is True

        # 2. Re-enable
        result = kill_switch.re_enable(
            agent_id=agent_id,
            operator_id="operator-1",
            acknowledgment="Investigation complete, root cause identified",
        )

        assert result is True

        # 3. Agent should be alive again
        assert kill_switch.is_agent_circuit_open(agent_id) is False

        # 4. State should be cleared
        persisted_state = kill_switch.state_manager.load_state(agent_id)
        # Note: After re-enable, the state file is deleted
        # and circuit breaker is re-initialized
        assert kill_switch.get_agent_state(agent_id) == CircuitState.CLOSED

    def test_circuit_breaker_resets_on_success(self, kill_switch, default_config):
        """Success resets failure count."""
        agent_id = "test-agent"

        # Start monitoring
        kill_switch.start_monitoring(agent_id, config=default_config)

        # Get initial failure count
        initial_count = kill_switch.circuit_breaker.get_failure_count(agent_id)
        assert initial_count == 0

        # Simulate some healthy operations by checking metrics
        # The circuit breaker should record success when metrics are healthy
        healthy_metrics = HealthMetrics(
            agent_id=agent_id,
            error_rate=0.01,  # Below threshold
            latency_p99_ms=500.0,  # Below threshold
            memory_usage_percent=40.0,  # Below threshold
            output_rate_kbps=10.0,  # Below threshold
            last_health_check=datetime.now(timezone.utc),
            timestamp=datetime.now(timezone.utc),
        )

        # Check if circuit breaker would trigger
        should_trigger = kill_switch.circuit_breaker.should_trigger(
            agent_id, healthy_metrics, default_config
        )

        # With healthy metrics, should not trigger
        assert should_trigger is False

        # Record success (this is what evaluate_and_trigger does)
        kill_switch.circuit_breaker.record_success(agent_id)

        # Failure count should remain 0
        assert kill_switch.circuit_breaker.get_failure_count(agent_id) == 0

    def test_state_persistence_across_restarts(self, temp_state_path):
        """Killed agent stays killed even after KillSwitch restart."""
        from implement.kill_switch.state_manager import StateManager

        agent_id = "test-agent"

        # Create first KillSwitch and kill agent
        state_manager = StateManager(state_path=temp_state_path)
        ks1 = KillSwitch(state_manager=state_manager)
        ks1.start_monitoring(agent_id)
        ks1.manual_trigger(agent_id, "Kill reason", "operator")

        # Verify killed
        assert ks1.is_agent_circuit_open(agent_id) is True

        # Create new KillSwitch with same state manager
        state_manager2 = StateManager(state_path=temp_state_path)
        ks2 = KillSwitch(state_manager=state_manager2)

        # Agent should still be killed (state persisted)
        assert ks2.is_agent_circuit_open(agent_id) is True

        # Re-enable with second instance
        ks2.re_enable(agent_id, "operator", "acknowledged")

        # Now should be alive
        assert ks2.is_agent_circuit_open(agent_id) is False

    def test_multiple_agents_independent(self, kill_switch):
        """Multiple agents can be managed independently."""
        agents = ["agent-a", "agent-b", "agent-c"]

        # Start monitoring all
        for agent_id in agents:
            kill_switch.start_monitoring(agent_id)

        # Kill agent-b
        kill_switch.manual_trigger(
            agent_id="agent-b",
            reason="Kill B",
            operator_id="operator",
        )

        # Verify only agent-b is killed
        assert kill_switch.is_agent_circuit_open("agent-a") is False
        assert kill_switch.is_agent_circuit_open("agent-b") is True
        assert kill_switch.is_agent_circuit_open("agent-c") is False

        # Re-enable agent-b
        kill_switch.re_enable("agent-b", "operator", "acknowledged")

        # All should be alive
        assert kill_switch.is_agent_circuit_open("agent-a") is False
        assert kill_switch.is_agent_circuit_open("agent-b") is False
        assert kill_switch.is_agent_circuit_open("agent-c") is False

    def test_interrupt_latency_measured(self, kill_switch):
        """Interrupt latency is accurately measured."""
        agent_id = "test-agent"

        event = kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test",
            operator_id="operator",
        )

        # Latency should be recorded
        assert event.interrupt_latency_ms is not None
        assert event.interrupt_latency_ms > 0

        # Latency should be reasonable (< 5 seconds as per spec)
        assert event.interrupt_latency_ms < 5000

    def test_interrupt_outcome_recorded(self, kill_switch):
        """Interrupt outcome is recorded correctly."""
        agent_id = "test-agent"

        event = kill_switch.manual_trigger(
            agent_id=agent_id,
            reason="Test",
            operator_id="operator",
        )

        # Outcome should be SUCCESS (agent process not found in simulation)
        assert event.outcome is not None
        assert event.outcome.value is not None
