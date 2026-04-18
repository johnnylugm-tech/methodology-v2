"""
Tests for Kill-Switch enums.
"""

import pytest

from implement.kill_switch.enums import (
    CircuitState,
    InterruptOutcome,
    KillReason,
    KillSwitchEventType,
)


class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_circuit_state_values(self):
        """CLOSED, OPEN, HALF_OPEN exist and are distinct."""
        assert CircuitState.CLOSED is not None
        assert CircuitState.OPEN is not None
        assert CircuitState.HALF_OPEN is not None

        # Verify they are distinct
        assert CircuitState.CLOSED != CircuitState.OPEN
        assert CircuitState.OPEN != CircuitState.HALF_OPEN
        assert CircuitState.CLOSED != CircuitState.HALF_OPEN

        # Verify count
        assert len(CircuitState) == 3


class TestKillSwitchEventType:
    """Tests for KillSwitchEventType enum."""

    def test_kill_switch_event_type_values(self):
        """All event types exist and are distinct."""
        expected_types = [
            "TRIGGERED",
            "INTERRUPT_STARTED",
            "INTERRUPT_COMPLETED",
            "INTERRUPT_FAILED",
            "AGENT_KILLED",
            "AGENT_RE_ENABLED",
            "CIRCUIT_OPENED",
            "CIRCUIT_CLOSED",
            "CIRCUIT_HALF_OPEN",
        ]

        for type_name in expected_types:
            enum_member = getattr(KillSwitchEventType, type_name)
            assert enum_member is not None

        # Verify all are distinct
        assert len(KillSwitchEventType) == len(expected_types)


class TestKillReason:
    """Tests for KillReason enum."""

    def test_kill_reason_values(self):
        """All kill reasons exist and are distinct."""
        expected_reasons = [
            "ERROR_RATE_EXCEEDED",
            "LATENCY_EXCEEDED",
            "MEMORY_EXCEEDED",
            "OUTPUT_EXCEEDED",
            "NO_RESPONSE",
            "MANUAL_TRIGGER",
        ]

        for reason_name in expected_reasons:
            enum_member = getattr(KillReason, reason_name)
            assert enum_member is not None

        # Verify all are distinct
        assert len(KillReason) == len(expected_reasons)


class TestInterruptOutcome:
    """Tests for InterruptOutcome enum."""

    def test_interrupt_outcome_values(self):
        """SUCCESS, FAILED, TIMEOUT exist and are distinct."""
        assert InterruptOutcome.SUCCESS is not None
        assert InterruptOutcome.FAILED is not None
        assert InterruptOutcome.TIMEOUT is not None

        # Verify they are distinct
        assert InterruptOutcome.SUCCESS != InterruptOutcome.FAILED
        assert InterruptOutcome.FAILED != InterruptOutcome.TIMEOUT
        assert InterruptOutcome.SUCCESS != InterruptOutcome.TIMEOUT

        # Verify count
        assert len(InterruptOutcome) == 3
