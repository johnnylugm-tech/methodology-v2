"""
Tests for Kill-Switch dataclass models.
"""

import pytest
from datetime import datetime, timezone

from implement.kill_switch.enums import (
    CircuitState,
    InterruptOutcome,
    KillReason,
)
from implement.kill_switch.models import (
    CircuitBreakerState,
    HealthMetrics,
    InterruptEvent,
    MonitorConfig,
)


class TestHealthMetrics:
    """Tests for HealthMetrics dataclass."""

    def test_health_metrics_creation(self):
        """All fields are present and correctly typed."""
        now = datetime.now(timezone.utc)
        metrics = HealthMetrics(
            agent_id="agent-1",
            error_rate=0.15,
            latency_p99_ms=3500.0,
            memory_usage_percent=75.5,
            output_rate_kbps=50.0,
            last_health_check=now,
            timestamp=now,
        )

        assert metrics.agent_id == "agent-1"
        assert metrics.error_rate == 0.15
        assert metrics.latency_p99_ms == 3500.0
        assert metrics.memory_usage_percent == 75.5
        assert metrics.output_rate_kbps == 50.0
        assert metrics.last_health_check == now
        assert metrics.timestamp == now

    def test_health_metrics_defaults(self):
        """Default values work - all fields required (no defaults)."""
        # HealthMetrics has no defaults - all fields are required
        now = datetime.now(timezone.utc)
        metrics = HealthMetrics(
            agent_id="agent-2",
            error_rate=0.0,
            latency_p99_ms=0.0,
            memory_usage_percent=0.0,
            output_rate_kbps=0.0,
            last_health_check=now,
            timestamp=now,
        )

        assert metrics.error_rate == 0.0
        assert metrics.latency_p99_ms == 0.0
        assert metrics.memory_usage_percent == 0.0
        assert metrics.output_rate_kbps == 0.0


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState dataclass."""

    def test_circuit_breaker_state_creation(self):
        """All fields are present and correctly typed."""
        now = datetime.now(timezone.utc)
        state = CircuitBreakerState(
            agent_id="agent-1",
            state=CircuitState.CLOSED,
            failure_count=3,
            last_failure_time=now,
            cooldown_end=now,
            last_success_time=now,
            opened_at=now,
            closed_at=now,
        )

        assert state.agent_id == "agent-1"
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 3
        assert state.last_failure_time == now
        assert state.cooldown_end == now
        assert state.last_success_time == now
        assert state.opened_at == now
        assert state.closed_at == now

    def test_circuit_breaker_state_defaults(self):
        """Default values are applied correctly."""
        state = CircuitBreakerState(agent_id="agent-2")

        assert state.agent_id == "agent-2"
        assert state.state == CircuitState.CLOSED
        assert state.failure_count == 0
        assert state.last_failure_time is None
        assert state.cooldown_end is None
        assert state.last_success_time is None
        assert state.opened_at is None
        assert state.closed_at is None


class TestInterruptEvent:
    """Tests for InterruptEvent dataclass."""

    def test_interrupt_event_creation(self):
        """All fields are present and correctly typed."""
        now = datetime.now(timezone.utc)
        event = InterruptEvent(
            event_id="uuid-123",
            agent_id="agent-1",
            reason="High error rate",
            reason_type=KillReason.ERROR_RATE_EXCEEDED,
            triggered_by="operator-1",
            triggered_at=now,
            interrupt_started_at=now,
            interrupt_completed_at=now,
            interrupt_latency_ms=500.0,
            outcome=InterruptOutcome.SUCCESS,
            error_message=None,
        )

        assert event.event_id == "uuid-123"
        assert event.agent_id == "agent-1"
        assert event.reason == "High error rate"
        assert event.reason_type == KillReason.ERROR_RATE_EXCEEDED
        assert event.triggered_by == "operator-1"
        assert event.triggered_at == now
        assert event.interrupt_started_at == now
        assert event.interrupt_completed_at == now
        assert event.interrupt_latency_ms == 500.0
        assert event.outcome == InterruptOutcome.SUCCESS
        assert event.error_message is None

    def test_interrupt_event_minimal(self):
        """Minimal required fields work."""
        now = datetime.now(timezone.utc)
        event = InterruptEvent(
            event_id="uuid-456",
            agent_id="agent-2",
            reason="Manual trigger",
            reason_type=KillReason.MANUAL_TRIGGER,
            triggered_by="SYSTEM",
            triggered_at=now,
        )

        assert event.event_id == "uuid-456"
        assert event.interrupt_started_at is None
        assert event.interrupt_completed_at is None
        assert event.interrupt_latency_ms is None
        assert event.outcome is None
        assert event.error_message is None


class TestMonitorConfig:
    """Tests for MonitorConfig dataclass."""

    def test_monitor_config_creation(self):
        """All fields are present and correctly typed."""
        config = MonitorConfig(
            agent_id="agent-1",
            error_rate_threshold=0.10,
            error_rate_window_seconds=60,
            latency_p99_threshold_ms=5000.0,
            latency_window_seconds=300,
            memory_usage_threshold=90.0,
            output_rate_threshold_kbps=100.0,
            output_window_seconds=30,
            no_response_threshold_seconds=60,
            failure_threshold=5,
            cooldown_seconds=60,
        )

        assert config.agent_id == "agent-1"
        assert config.error_rate_threshold == 0.10
        assert config.error_rate_window_seconds == 60
        assert config.latency_p99_threshold_ms == 5000.0
        assert config.latency_window_seconds == 300
        assert config.memory_usage_threshold == 90.0
        assert config.output_rate_threshold_kbps == 100.0
        assert config.output_window_seconds == 30
        assert config.no_response_threshold_seconds == 60
        assert config.failure_threshold == 5
        assert config.cooldown_seconds == 60

    def test_monitor_config_defaults(self):
        """Default values are applied correctly."""
        config = MonitorConfig(agent_id="agent-2")

        assert config.agent_id == "agent-2"
        assert config.error_rate_threshold == 0.10
        assert config.error_rate_window_seconds == 60
        assert config.latency_p99_threshold_ms == 5000.0
        assert config.latency_window_seconds == 300
        assert config.memory_usage_threshold == 90.0
        assert config.output_rate_threshold_kbps == 100.0
        assert config.output_window_seconds == 30
        assert config.no_response_threshold_seconds == 60
        assert config.failure_threshold == 5
        assert config.cooldown_seconds == 60
