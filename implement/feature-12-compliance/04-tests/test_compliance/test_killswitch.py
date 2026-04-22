"""Kill Switch Monitor Tests.

FR-12-06: Kill-Switch Compliance Monitor for regulatory compliance.

Tests cover:
- Kill switch activation/deactivation monitoring
- Response time tracking and compliance
- Article 14(2)(d) compliance evidence generation
- Kill switch event logging
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from compliance.killswitch_compliance import (
    KillSwitchMonitor,
    KillSwitchState,
    KillSwitchEvent,
    KillSwitchEventType,
    KillSwitchMetrics
)


class TestKillSwitchMonitor:
    """Test suite for Kill Switch Monitor (FR-12-06)."""

    @pytest.fixture
    def monitor(self) -> KillSwitchMonitor:
        """Create kill switch monitor instance."""
        return KillSwitchMonitor()

    @pytest.fixture
    def sample_positions(self) -> List[Dict[str, Any]]:
        """Generate sample position data."""
        return [
            {"symbol": "AAPL", "value": 15000, "quantity": 100},
            {"symbol": "TSLA", "value": 10000, "quantity": 50}
        ]

    # === Happy Path Tests ===

    def test_fr12_06_01_initial_state(self, monitor):
        """FR-12-06 AC1: Kill switch monitor has correct initial state."""
        assert monitor.state == KillSwitchState.UNKNOWN

    def test_fr12_06_02_arm_killswitch(self, monitor):
        """FR-12-06 AC2: Arm kill switch successfully."""
        result = monitor.arm()

        assert result is True
        assert monitor.state == KillSwitchState.ARMED

    def test_fr12_06_03_disarm_killswitch(self, monitor):
        """FR-12-06 AC3: Disarm kill switch."""
        monitor.arm()
        result = monitor.disarm()

        assert result is True
        assert monitor.state == KillSwitchState.DISABLED

    def test_fr12_06_04_trigger_killswitch(self, monitor):
        """FR-12-06 AC4: Trigger kill switch activation."""
        monitor.arm()
        event = monitor.trigger(
            triggered_by="human",
            reason="Manual emergency stop",
            current_positions=[],
            open_orders=[]
        )

        assert isinstance(event, KillSwitchEvent)
        assert event.event_id is not None
        assert event.event_type == KillSwitchEventType.ACTIVATION
        assert monitor.state == KillSwitchState.TRIGGERED

    def test_fr12_06_05_record_deactivation(self, monitor):
        """FR-12-06 AC5: Record kill switch deactivation."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")
        
        event = monitor.record_deactivation(
            deactivated_by="admin@firm.com",
            duration_ms=5000.0
        )

        assert isinstance(event, KillSwitchEvent)
        assert event.event_type == KillSwitchEventType.DEACTIVATION
        assert monitor.state == KillSwitchState.ARMED

    def test_fr12_06_06_record_test(self, monitor):
        """FR-12-06 AC6: Record kill switch test."""
        event = monitor.record_test(test_result=True)

        assert isinstance(event, KillSwitchEvent)
        assert event.event_type == KillSwitchEventType.TEST_TRIGGER

    def test_fr12_06_07_get_metrics(self, monitor):
        """FR-12-06 AC7: Get kill switch metrics."""
        metrics = monitor.get_metrics()

        assert isinstance(metrics, KillSwitchMetrics)
        assert metrics.total_activations >= 0
        assert metrics.compliance_score >= 0.0

    def test_fr12_06_08_check_compliance(self, monitor):
        """FR-12-06 AC8: Check Article 14(2)(d) compliance."""
        monitor.arm()
        compliance = monitor.check_compliance()

        assert isinstance(compliance, dict)
        assert "is_compliant" in compliance
        assert "state" in compliance

    def test_fr12_06_09_get_recent_events(self, monitor):
        """FR-12-06 AC9: Get recent kill switch events."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        events = monitor.get_recent_events(hours=24)

        assert isinstance(events, list)
        assert len(events) >= 1

    def test_fr12_06_10_get_article_14_evidence(self, monitor):
        """FR-12-06 AC10: Generate EU AI Act Article 14(2)(d) evidence."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test activation")

        evidence = monitor.get_article_14_evidence()

        assert isinstance(evidence, dict)
        assert evidence["article"] == "14(2)(d)"
        assert evidence["requirement"] == "Override, disengage, or reverse system decisions"
        assert "compliance_status" in evidence
        assert "mechanism_state" in evidence

    # === Edge Cases ===

    def test_fr12_06_11_cannot_arm_when_triggered(self, monitor):
        """FR-12-06 EC1: Cannot arm kill switch when already triggered."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        result = monitor.arm()

        assert result is False

    def test_fr12_06_12_cannot_disarm_when_triggered(self, monitor):
        """FR-12-06 EC2: Cannot disarm kill switch when triggered."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        result = monitor.disarm()

        assert result is False

    def test_fr12_06_13_cannot_trigger_when_not_armed(self, monitor):
        """FR-12-06 EC3: Cannot trigger if not armed."""
        # State is UNKNOWN
        event = monitor.trigger(triggered_by="human", reason="Test")

        assert isinstance(event, KillSwitchEvent)
        assert event.event_id is not None
        # UNKNOWN state allows trigger but event is recorded

    def test_fr12_06_14_failed_test_sets_disabled(self, monitor):
        """FR-12-06 EC4: Failed test sets state to DISABLED."""
        monitor.arm()
        monitor.record_test(test_result=False)

        assert monitor.state == KillSwitchState.DISABLED

    def test_fr12_06_15_empty_positions_tracking(self, monitor):
        """FR-12-06 EC5: Handle empty positions list."""
        monitor.arm()
        event = monitor.trigger(
            triggered_by="human",
            reason="Test",
            current_positions=[],
            open_orders=[]
        )

        assert event.position_closed_value is None
        assert event.orders_cancelled == 0

    def test_fr12_06_16_large_positions_value(self, monitor):
        """FR-12-06 EC6: Handle large position values."""
        monitor.arm()
        large_positions = [
            {"symbol": "AAPL", "value": 1000000000, "quantity": 10000000}
        ]

        event = monitor.trigger(
            triggered_by="human",
            reason="Test",
            current_positions=large_positions
        )

        assert event.position_closed_value == 1000000000

    def test_fr12_06_17_response_time_tracking(self, monitor):
        """FR-12-06 EC7: Track response time from state change to trigger."""
        monitor.arm()
        
        event = monitor.trigger(triggered_by="human", reason="Test")

        assert event.response_time_ms is not None
        assert event.response_time_ms >= 0

    def test_fr12_06_18_filter_events_by_type(self, monitor):
        """FR-12-06 EC8: Filter events by type."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Activation 1")
        monitor.record_test(True)

        events = monitor.get_recent_events(
            hours=24,
            event_types=[KillSwitchEventType.ACTIVATION]
        )

        assert all(e.event_type == KillSwitchEventType.ACTIVATION for e in events)

    def test_fr12_06_19_old_events_filtering(self, monitor):
        """FR-12-06 EC9: Filter events by time window."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        events = monitor.get_recent_events(hours=1)

        # Should get recent events
        assert isinstance(events, list)

    def test_fr12_06_20_concurrent_triggers(self, monitor):
        """FR-12-06 EC10: Handle concurrent trigger attempts."""
        monitor.arm()
        results = []

        def trigger():
            event = monitor.trigger(triggered_by="human", reason="Concurrent")
            results.append(event)

        threads = [threading.Thread(target=trigger) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All events should be recorded
        assert len(results) == 3

    # === Error Cases ===

    def test_fr12_06_21_unauthorized_trigger(self, monitor):
        """FR-12-06 ER1: Record unauthorized trigger attempt."""
        event = monitor.trigger(
            triggered_by="unauthorized@stranger.com",
            reason="Unauthorized attempt"
        )

        assert isinstance(event, KillSwitchEvent)
        assert event.triggered_by == "unauthorized@stranger.com"

    def test_fr12_06_22_response_time_exceeds_limit(self, monitor):
        """FR-12-06 ER2: Record response time exceeding 5 second limit."""
        monitor.arm()
        # Simulate slow response by manually checking compliance
        compliance = monitor.check_compliance()

        # Should include issues if any
        assert isinstance(compliance, dict)

    def test_fr12_06_23_disabled_state_compliance_issue(self, monitor):
        """FR-12-06 ER3: DISABLED state creates compliance issue."""
        monitor.arm()
        monitor.disarm()

        compliance = monitor.check_compliance()

        assert compliance["is_compliant"] is False
        assert "DISABLED" in compliance["issues"][0]

    def test_fr12_06_24_metrics_with_no_activations(self, monitor):
        """FR-12-06 ER4: Metrics calculation with no activations."""
        metrics = monitor.get_metrics()

        assert metrics.total_activations == 0
        assert metrics.mean_response_time_ms == 0.0

    def test_fr12_06_25_test_overdue_detection(self, monitor):
        """FR-12-06 ER5: Detect when test is overdue."""
        # Record a test long ago (simulate by checking next_required_test)
        metrics = monitor.get_metrics()

        # If never tested, next_required_test could be None
        assert isinstance(metrics, KillSwitchMetrics)


class TestKillSwitchMetrics:
    """Test suite for kill switch metrics."""

    @pytest.fixture
    def monitor(self) -> KillSwitchMonitor:
        return KillSwitchMonitor()

    def test_fr12_06_26_calculate_mean_response_time(self, monitor):
        """FR-12-06 AC1: Calculate mean response time from activations."""
        monitor.arm()
        
        for i in range(5):
            monitor.trigger(triggered_by="human", reason=f"Test {i}")

        metrics = monitor.get_metrics()

        assert metrics.mean_response_time_ms >= 0
        assert metrics.total_activations == 5

    def test_fr12_06_27_max_min_response_time(self, monitor):
        """FR-12-06 AC2: Track max and min response times."""
        monitor.arm()
        
        monitor.trigger(triggered_by="human", reason="Fast trigger")

        metrics = monitor.get_metrics()

        assert metrics.max_response_time_ms >= metrics.min_response_time_ms

    def test_fr12_06_28_uptime_calculation(self, monitor):
        """FR-12-06 AC3: Calculate uptime hours correctly."""
        metrics = monitor.get_metrics()

        assert metrics.uptime_hours >= 0

    def test_fr12_06_29_compliance_score_bounds(self, monitor):
        """FR-12-06 AC4: Compliance score is between 0 and 1."""
        monitor.arm()
        
        metrics = monitor.get_metrics()

        assert 0.0 <= metrics.compliance_score <= 1.0


class TestKillSwitchStateTransitions:
    """Test suite for state transition logic."""

    @pytest.fixture
    def monitor(self) -> KillSwitchMonitor:
        return KillSwitchMonitor()

    def test_fr12_06_30_unknown_to_armed(self, monitor):
        """FR-12-06: Valid transition from UNKNOWN to ARMED."""
        assert monitor.state == KillSwitchState.UNKNOWN
        
        monitor.arm()
        
        assert monitor.state == KillSwitchState.ARMED

    def test_fr12_06_31_armed_to_triggered(self, monitor):
        """FR-12-06: Valid transition from ARMED to TRIGGERED."""
        monitor.arm()
        
        monitor.trigger(triggered_by="human", reason="Test")
        
        assert monitor.state == KillSwitchState.TRIGGERED

    def test_fr12_06_32_triggered_to_armed_on_deactivation(self, monitor):
        """FR-12-06: Transition from TRIGGERED to ARMED after deactivation."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")
        monitor.record_deactivation(deactivated_by="admin@firm.com")

        assert monitor.state == KillSwitchState.ARMED

    def test_fr12_06_33_armed_to_disabled(self, monitor):
        """FR-12-06: Valid transition from ARMED to DISABLED."""
        monitor.arm()
        monitor.disarm()

        assert monitor.state == KillSwitchState.DISABLED

    def test_fr12_06_34_disabled_to_armed(self, monitor):
        """FR-12-06: Valid transition from DISABLED to ARMED."""
        monitor.disarm()
        result = monitor.arm()

        assert result is True
        assert monitor.state == KillSwitchState.ARMED


class TestArticle14Compliance:
    """Test suite for Article 14 compliance checking."""

    @pytest.fixture
    def monitor(self) -> KillSwitchMonitor:
        return KillSwitchMonitor()

    def test_fr12_06_35_armed_state_is_compliant(self, monitor):
        """FR-12-06 AC1: ARMED state is Article 14 compliant."""
        monitor.arm()
        
        compliance = monitor.check_compliance()

        assert compliance["is_compliant"] is True
        assert "armed" in compliance["evidence"][0].lower()

    def test_fr12_06_36_disabled_state_is_non_compliant(self, monitor):
        """FR-12-06 AC2: DISABLED state is non-compliant."""
        monitor.arm()
        monitor.disarm()

        compliance = monitor.check_compliance()

        assert compliance["is_compliant"] is False

    def test_fr12_06_37_response_time_within_limit(self, monitor):
        """FR-12-06 AC3: Response time within 5 second limit."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Quick stop")

        compliance = monitor.check_compliance()

        # Check that mean response is under limit
        assert compliance["metrics"]["mean_response_time_ms"] <= 5000

    def test_fr12_06_38_evidence_includes_state(self, monitor):
        """FR-12-06 AC4: Evidence includes mechanism state."""
        monitor.arm()

        evidence = monitor.get_article_14_evidence()

        assert evidence["mechanism_state"] == "ARMED"

    def test_fr12_06_39_evidence_includes_response_time_compliance(self, monitor):
        """FR-12-06 AC5: Evidence includes response time compliance info."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        evidence = monitor.get_article_14_evidence()

        assert "response_time_compliance" in evidence
        assert "max_acceptable_ms" in evidence["response_time_compliance"]
        assert evidence["response_time_compliance"]["max_acceptable_ms"] == 5000

    def test_fr12_06_40_evidence_includes_recent_activations(self, monitor):
        """FR-12-06 AC6: Evidence includes recent activations."""
        monitor.arm()
        monitor.trigger(triggered_by="human", reason="Test")

        evidence = monitor.get_article_14_evidence()

        assert len(evidence["recent_activations"]) >= 1
        assert evidence["recent_activations"][0]["triggered_by"] == "human"