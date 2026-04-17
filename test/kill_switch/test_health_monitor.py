"""
Tests for HealthMonitor component.
"""

import pytest

from implement.kill_switch.exceptions import AgentNotFoundError, MetricsUnavailableError
from implement.kill_switch.health_monitor import HealthMonitor
from implement.kill_switch.models import HealthMetrics, MonitorConfig


@pytest.fixture
def health_monitor():
    """Create a HealthMonitor instance for testing."""
    return HealthMonitor()


@pytest.fixture
def monitor_config():
    """Create a MonitorConfig for testing."""
    return MonitorConfig(
        agent_id="test-agent",
        error_rate_threshold=0.10,
        failure_threshold=5,
        cooldown_seconds=60,
    )


class TestHealthMonitor:
    """Tests for HealthMonitor class."""

    def test_start_monitoring_creates_monitor(self, health_monitor, monitor_config):
        """start_monitoring adds agent to active set."""
        agent_id = "test-agent-1"

        # Before starting, should not be monitoring
        assert not health_monitor.is_monitoring(agent_id)

        # Start monitoring
        health_monitor.start_monitoring(agent_id, monitor_config)

        # After starting, should be monitoring
        assert health_monitor.is_monitoring(agent_id)

    def test_stop_monitoring_removes_agent(self, health_monitor, monitor_config):
        """stop_monitoring removes agent from active set."""
        agent_id = "test-agent-2"

        # Start monitoring
        health_monitor.start_monitoring(agent_id, monitor_config)
        assert health_monitor.is_monitoring(agent_id)

        # Stop monitoring
        health_monitor.stop_monitoring(agent_id)

        # After stopping, should not be monitoring
        assert not health_monitor.is_monitoring(agent_id)

    def test_get_metrics_returns_health_metrics(self, health_monitor, monitor_config):
        """get_metrics returns valid HealthMetrics."""
        agent_id = "test-agent-3"
        health_monitor.start_monitoring(agent_id, monitor_config)

        # Get metrics
        metrics = health_monitor.get_metrics(agent_id)

        # Should return a HealthMetrics object
        assert isinstance(metrics, HealthMetrics)
        assert metrics.agent_id == agent_id

    def test_is_monitoring_returns_correct_status(self, health_monitor, monitor_config):
        """is_monitoring reflects actual state."""
        agent_id = "test-agent-4"

        # Not monitoring initially
        assert health_monitor.is_monitoring(agent_id) is False

        # After start
        health_monitor.start_monitoring(agent_id, monitor_config)
        assert health_monitor.is_monitoring(agent_id) is True

        # After stop
        health_monitor.stop_monitoring(agent_id)
        assert health_monitor.is_monitoring(agent_id) is False

    def test_metrics_include_all_fields(self, health_monitor, monitor_config):
        """HealthMetrics has all required fields."""
        agent_id = "test-agent-5"
        health_monitor.start_monitoring(agent_id, monitor_config)

        metrics = health_monitor.get_metrics(agent_id)

        # Check all required fields are present and have valid types
        assert isinstance(metrics.agent_id, str)
        assert isinstance(metrics.error_rate, float)
        assert isinstance(metrics.latency_p99_ms, float)
        assert isinstance(metrics.memory_usage_percent, float)
        assert isinstance(metrics.output_rate_kbps, float)
        assert metrics.last_health_check is not None
        assert metrics.timestamp is not None

        # Validate ranges
        assert 0.0 <= metrics.error_rate <= 1.0
        assert metrics.latency_p99_ms >= 0.0
        assert 0.0 <= metrics.memory_usage_percent <= 100.0
        assert metrics.output_rate_kbps >= 0.0

    def test_start_monitoring_with_empty_agent_id_raises(self, health_monitor):
        """start_monitoring raises error for empty agent ID."""
        config = MonitorConfig(agent_id="")

        with pytest.raises(AgentNotFoundError):
            health_monitor.start_monitoring("", config)

    def test_get_metrics_raises_for_unmonitored_agent(self, health_monitor):
        """get_metrics raises error for agent not being monitored."""
        with pytest.raises(AgentNotFoundError):
            health_monitor.get_metrics("nonexistent-agent")

    def test_multiple_agents_independent(self, health_monitor, monitor_config):
        """Each agent's monitoring state is independent."""
        agent_a = "agent-a"
        agent_b = "agent-b"

        config_a = MonitorConfig(agent_id=agent_a)
        config_b = MonitorConfig(agent_id=agent_b)

        # Start monitoring only agent A
        health_monitor.start_monitoring(agent_a, config_a)

        assert health_monitor.is_monitoring(agent_a)
        assert not health_monitor.is_monitoring(agent_b)

        # Start monitoring agent B
        health_monitor.start_monitoring(agent_b, config_b)

        assert health_monitor.is_monitoring(agent_a)
        assert health_monitor.is_monitoring(agent_b)

        # Stop agent A, B should still be running
        health_monitor.stop_monitoring(agent_a)

        assert not health_monitor.is_monitoring(agent_a)
        assert health_monitor.is_monitoring(agent_b)
