"""
Tests for CircuitBreaker component.
"""

import pytest
from datetime import datetime, timezone, timedelta

from implement.kill_switch.circuit_breaker import CircuitBreaker
from implement.kill_switch.enums import CircuitState
from implement.kill_switch.exceptions import AgentNotFoundError
from implement.kill_switch.models import HealthMetrics, MonitorConfig


@pytest.fixture
def circuit_breaker():
    """Create a CircuitBreaker instance for testing."""
    return CircuitBreaker()


@pytest.fixture
def monitor_config():
    """Create a MonitorConfig for testing."""
    return MonitorConfig(
        agent_id="test-agent",
        error_rate_threshold=0.10,
        failure_threshold=5,
        cooldown_seconds=60,
    )


@pytest.fixture
def healthy_metrics():
    """Create healthy metrics below threshold."""
    now = datetime.now(timezone.utc)
    return HealthMetrics(
        agent_id="test-agent",
        error_rate=0.05,
        latency_p99_ms=1000.0,
        memory_usage_percent=50.0,
        output_rate_kbps=20.0,
        last_health_check=now,
        timestamp=now,
    )


@pytest.fixture
def unhealthy_metrics():
    """Create unhealthy metrics above threshold."""
    now = datetime.now(timezone.utc)
    return HealthMetrics(
        agent_id="test-agent",
        error_rate=0.15,
        latency_p99_ms=6000.0,
        memory_usage_percent=95.0,
        output_rate_kbps=150.0,
        last_health_check=now,
        timestamp=now,
    )


class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""

    def test_initial_state_is_closed(self, circuit_breaker):
        """New agent starts in CLOSED state."""
        agent_id = "new-agent"

        # Before initialization
        state = circuit_breaker.get_state(agent_id)
        assert state == CircuitState.CLOSED

        # Initialize circuit
        circuit_breaker.initialize_circuit(agent_id)

        # After initialization
        state = circuit_breaker.get_state(agent_id)
        assert state == CircuitState.CLOSED

    def test_record_success_resets_failure_count(self, circuit_breaker):
        """Success resets count to 0 when in HALF_OPEN state."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        # Record some failures first
        circuit_breaker.record_failure(agent_id)
        circuit_breaker.record_failure(agent_id)
        assert circuit_breaker.get_failure_count(agent_id) == 2

        # Force to HALF_OPEN state (simulating cooldown elapsed)
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=0)
        circuit_breaker._circuits[agent_id].state = CircuitState.HALF_OPEN

        # Record success from HALF_OPEN
        circuit_breaker.record_success(agent_id)

        # Count should be reset and state should be CLOSED
        assert circuit_breaker.get_failure_count(agent_id) == 0
        assert circuit_breaker.get_state(agent_id) == CircuitState.CLOSED

    def test_record_failure_increments_count(self, circuit_breaker):
        """Failure increments count."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        assert circuit_breaker.get_failure_count(agent_id) == 0

        circuit_breaker.record_failure(agent_id)
        assert circuit_breaker.get_failure_count(agent_id) == 1

        circuit_breaker.record_failure(agent_id)
        assert circuit_breaker.get_failure_count(agent_id) == 2

    def test_circuit_opens_after_threshold(self, circuit_breaker, monitor_config):
        """open_circuit transitions state to OPEN after threshold."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        # Record failures up to threshold
        for i in range(monitor_config.failure_threshold - 1):
            circuit_breaker.record_failure(agent_id)
            assert circuit_breaker.get_failure_count(agent_id) == i + 1

        # After threshold, call open_circuit to actually open
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=60)

        # Circuit should be OPEN
        assert circuit_breaker.get_state(agent_id) == CircuitState.OPEN
        assert circuit_breaker.is_open(agent_id) is True

    def test_half_open_after_cooldown(self, circuit_breaker):
        """State transitions to HALF_OPEN after cooldown."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        # Open the circuit
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=1)

        # Immediately after opening, should be OPEN
        assert circuit_breaker.get_state(agent_id) == CircuitState.OPEN

        # Wait for cooldown to elapse
        import time
        time.sleep(1.1)

        # Should transition to HALF_OPEN when checked
        circuit_breaker.is_open(agent_id)  # This triggers the transition check
        state = circuit_breaker.get_state(agent_id)
        assert state == CircuitState.HALF_OPEN

    def test_record_success_closes_circuit(self, circuit_breaker):
        """Success from HALF_OPEN closes circuit."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        # Open and then move to half-open by simulating cooldown
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=0)

        # Force to HALF_OPEN state (simulate cooldown elapsed)
        circuit_breaker._circuits[agent_id].state = CircuitState.HALF_OPEN

        # Record success
        circuit_breaker.record_success(agent_id)

        # Circuit should be CLOSED
        assert circuit_breaker.get_state(agent_id) == CircuitState.CLOSED
        assert circuit_breaker.get_failure_count(agent_id) == 0

    def test_record_failure_reopens_circuit(self, circuit_breaker):
        """Failure from HALF_OPEN reopens circuit."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        # Open and move to HALF_OPEN
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=0)
        circuit_breaker._circuits[agent_id].state = CircuitState.HALF_OPEN

        # Record failure in HALF_OPEN
        circuit_breaker.record_failure(agent_id)

        # Circuit should be OPEN again
        assert circuit_breaker.get_state(agent_id) == CircuitState.OPEN

    def test_record_success_raises_for_unknown_agent(self, circuit_breaker):
        """record_success raises AgentNotFoundError for unknown agent."""
        with pytest.raises(AgentNotFoundError):
            circuit_breaker.record_success("nonexistent-agent")

    def test_record_failure_raises_for_unknown_agent(self, circuit_breaker):
        """record_failure raises AgentNotFoundError for unknown agent."""
        with pytest.raises(AgentNotFoundError):
            circuit_breaker.record_failure("nonexistent-agent")

    def test_open_circuit_sets_cooldown(self, circuit_breaker):
        """open_circuit sets cooldown_end timestamp."""
        agent_id = "test-agent"
        circuit_breaker.initialize_circuit(agent_id)

        before_open = datetime.now(timezone.utc)
        circuit_breaker.open_circuit(agent_id, cooldown_seconds=60)
        after_open = datetime.now(timezone.utc)

        state = circuit_breaker._circuits[agent_id]

        # Cooldown should be set to ~60 seconds from now
        assert state.cooldown_end is not None
        assert state.cooldown_end > before_open
        assert state.cooldown_end > after_open

        # Cooldown should be approximately 60 seconds later
        expected_cooldown = before_open + timedelta(seconds=60)
        assert abs((state.cooldown_end - expected_cooldown).total_seconds()) < 5

    def test_should_trigger_with_healthy_metrics(self, circuit_breaker, healthy_metrics):
        """should_trigger returns False for healthy metrics."""
        agent_id = "test-agent"
        config = MonitorConfig(
            agent_id=agent_id,
            error_rate_threshold=0.10,
            latency_p99_threshold_ms=5000.0,
            memory_usage_threshold=90.0,
            output_rate_threshold_kbps=100.0,
        )

        circuit_breaker.initialize_circuit(agent_id)
        assert circuit_breaker.should_trigger(agent_id, healthy_metrics, config) is False

    def test_should_trigger_with_unhealthy_metrics(self, circuit_breaker, unhealthy_metrics):
        """should_trigger returns True for unhealthy metrics."""
        agent_id = "test-agent"
        config = MonitorConfig(
            agent_id=agent_id,
            error_rate_threshold=0.10,
            latency_p99_threshold_ms=5000.0,
            memory_usage_threshold=90.0,
            output_rate_threshold_kbps=100.0,
        )

        circuit_breaker.initialize_circuit(agent_id)
        assert circuit_breaker.should_trigger(agent_id, unhealthy_metrics, config) is True
