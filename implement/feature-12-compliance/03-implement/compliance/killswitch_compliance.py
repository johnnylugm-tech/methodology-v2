"""Kill-Switch Compliance Monitor.

FR-12-06: Monitors kill-switch functionality for regulatory compliance.

This module provides:
1. Kill-switch activation monitoring
2. Compliance verification for emergency stop mechanisms
3. Response time tracking and reporting
4. Article 14(d) compliance evidence generation

EU AI Act Article 14(2)(d) requires that high-risk AI systems allow
operators to override, disengage, or reverse system decisions. For
trading systems, the kill-switch is the primary mechanism for this.

References:
    - EU AI Act Article 14(2)(d)
    - MiFID II Algorithmic Trading Requirements
    - ESMA Guidelines on Algorithmic Trading
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Optional



class KillSwitchState(Enum):
    """States of the kill-switch mechanism."""
    ARMED = auto()      # Kill switch is active and monitoring
    TRIGGERED = auto()  # Kill switch has been activated
    COOLING_DOWN = auto()  # Post-trigger cooldown period
    DISABLED = auto()   # Kill switch is disabled (non-compliant state)
    UNKNOWN = auto()    # State cannot be determined


class KillSwitchEventType(Enum):
    """Types of kill-switch related events."""
    ACTIVATION = auto()       # Kill switch triggered
    DEACTIVATION = auto()      # Kill switch deactivated by human
    ARM_FAILURE = auto()      # Failed to arm kill switch
    TEST_TRIGGER = auto()     # Test activation
    OVERRIDE_USED = auto()    # Human override used (different from kill switch)


@dataclass
class KillSwitchEvent:
    """Record of a kill-switch related event."""
    event_id: str
    timestamp: datetime
    event_type: KillSwitchEventType
    triggered_by: str  # "system", "human", "test"
    reason: str
    response_time_ms: Optional[float] = None
    position_closed_value: Optional[float] = None
    orders_cancelled: int = 0
    duration_ms: Optional[float] = None
    notes: str = ""


@dataclass
class KillSwitchMetrics:
    """Performance metrics for kill-switch compliance."""
    total_activations: int
    mean_response_time_ms: float
    max_response_time_ms: float
    min_response_time_ms: float
    last_test_date: Optional[datetime]
    next_required_test: Optional[datetime]
    uptime_hours: float
    failures: int
    compliance_score: float  # 0.0 to 1.0


class KillSwitchMonitor:
    """Monitor and verify kill-switch compliance.

    The kill-switch is a critical safety mechanism required by EU AI Act
    for high-risk AI systems. This monitor provides:
    1. Real-time state tracking
    2. Response time measurement
    3. Compliance reporting for Article 14(2)(d)
    4. Alerting for potential issues

    Example:
        monitor = KillSwitchMonitor()
        monitor.start_monitoring()

        # Simulate kill switch activation
        result = monitor.record_activation(
            triggered_by="human",
            reason="Manual stop requested"
        )
        print(f"Response time: {result.response_time_ms}ms")
    """

    # Maximum acceptable response time in milliseconds (EU AI Act compliance)
    MAX_RESPONSE_TIME_MS = 5000  # 5 seconds for Article 14 compliance

    # Required test frequency (weekly recommended)
    TEST_INTERVAL_DAYS = 7

    def __init__(
        self,
        on_activation: Optional[Callable[[KillSwitchEvent], None]] = None,
        on_failure: Optional[Callable[[str], None]] = None
    ):
        """Initialize kill-switch monitor.

        Args:
            on_activation: Callback when kill switch is activated
            on_failure: Callback when kill switch failure detected
        """
        self._state = KillSwitchState.UNKNOWN
        self._events: list[KillSwitchEvent] = []
        self._on_activation = on_activation
        self._on_failure = on_failure
        self._last_state_change = datetime.now()
        self._monitoring_start = datetime.now()
        self._response_time_samples: list[float] = []

    @property
    def state(self) -> KillSwitchState:
        """Current state of the kill-switch."""
        return self._state

    def arm(self) -> bool:
        """Arm the kill-switch mechanism.

        Returns:
            True if successfully armed, False otherwise
        """
        if self._state == KillSwitchState.TRIGGERED:
            # Cannot arm while triggered
            return False

        self._state = KillSwitchState.ARMED
        self._last_state_change = datetime.now()
        return True

    def disarm(self) -> bool:
        """Disarm the kill-switch mechanism.

        Returns:
            True if successfully disarmed, False if prohibited (e.g., in trigger)

        Warning: Disarming the kill-switch may create non-compliance with
        EU AI Act Article 14 for high-risk trading systems.
        """
        if self._state == KillSwitchState.TRIGGERED:
            return False

        self._state = KillSwitchState.DISABLED
        self._last_state_change = datetime.now()
        return True

    def trigger(
        self,
        triggered_by: str,
        reason: str,
        current_positions: Optional[list[dict]] = None,
        open_orders: Optional[list[dict]] = None
    ) -> KillSwitchEvent:
        """Trigger the kill-switch.

        Args:
            triggered_by: Who/what triggered the kill switch
                         ("system", "human", "test", "risk_limit")
            reason: Reason for triggering
            current_positions: Current position data for closure tracking
            open_orders: Open orders for cancellation tracking

        Returns:
            KillSwitchEvent with details of the activation
        """
        trigger_time = datetime.now()
        event_id = f"KSE-{trigger_time.strftime('%Y%m%d-%H%M%S')}-{len(self._events)}"

        # Calculate response time from last state change
        response_time_ms = None
        if self._last_state_change:
            response_time_ms = (trigger_time - self._last_state_change).total_seconds() * 1000

        # Track position value and orders
        position_closed_value = None
        if current_positions:
            position_closed_value = sum(p.get("value", 0) for p in current_positions)

        orders_cancelled = len(open_orders) if open_orders else 0

        # Create event
        event = KillSwitchEvent(
            event_id=event_id,
            timestamp=trigger_time,
            event_type=KillSwitchEventType.ACTIVATION,
            triggered_by=triggered_by,
            reason=reason,
            response_time_ms=response_time_ms,
            position_closed_value=position_closed_value,
            orders_cancelled=orders_cancelled
        )

        # Update state
        self._state = KillSwitchState.TRIGGERED
        self._last_state_change = trigger_time
        self._events.append(event)

        # Track response time for metrics
        if response_time_ms is not None:
            self._response_time_samples.append(response_time_ms)

        # Call activation callback
        if self._on_activation:
            self._on_activation(event)

        return event

    def record_deactivation(
        self,
        deactivated_by: str,
        duration_ms: Optional[float] = None
    ) -> KillSwitchEvent:
        """Record kill-switch deactivation (return to normal operation).

        Args:
            deactivated_by: Who deactivated the kill switch
            duration_ms: How long the kill switch was active

        Returns:
            KillSwitchEvent for the deactivation
        """
        deactivation_time = datetime.now()

        event = KillSwitchEvent(
            event_id=f"KSD-{deactivation_time.strftime('%Y%m%d-%H%M%S')}-{len(self._events)}",
            timestamp=deactivation_time,
            event_type=KillSwitchEventType.DEACTIVATION,
            triggered_by=deactivated_by,
            reason="Manual deactivation after safe state confirmed",
            duration_ms=duration_ms
        )

        self._state = KillSwitchState.ARMED
        self._last_state_change = deactivation_time
        self._events.append(event)

        return event

    def record_test(self, test_result: bool) -> KillSwitchEvent:
        """Record a kill-switch test.

        Args:
            test_result: True if test passed, False if failed

        Returns:
            KillSwitchEvent for the test
        """
        test_time = datetime.now()

        event = KillSwitchEvent(
            event_id=f"KST-{test_time.strftime('%Y%m%d-%H%M%S')}-{len(self._events)}",
            timestamp=test_time,
            event_type=KillSwitchEventType.TEST_TRIGGER,
            triggered_by="system",
            reason="Periodic compliance test",
            response_time_ms=0.0  # Test doesn't count as real activation
        )

        if test_result:
            self._state = KillSwitchState.ARMED
        else:
            self._state = KillSwitchState.DISABLED
            if self._on_failure:
                self._on_failure("Kill switch test failed")

        self._last_state_change = test_time
        self._events.append(event)

        return event

    def get_metrics(self) -> KillSwitchMetrics:
        """Calculate kill-switch compliance metrics.

        Returns:
            KillSwitchMetrics with performance and compliance data
        """
        activations = [e for e in self._events if e.event_type == KillSwitchEventType.ACTIVATION]

        # Calculate response times
        response_times = [e.response_time_ms for e in activations if e.response_time_ms is not None]

        mean_response = sum(response_times) / len(response_times) if response_times else 0.0
        max_response = max(response_times) if response_times else 0.0
        min_response = min(response_times) if response_times else 0.0

        # Calculate uptime
        uptime = (datetime.now() - self._monitoring_start).total_seconds() / 3600

        # Find last test
        test_events = [e for e in self._events if e.event_type == KillSwitchEventType.TEST_TRIGGER]
        last_test = test_events[-1].timestamp if test_events else None

        # Calculate next required test
        next_test = None
        if last_test:
            next_test = last_test + timedelta(days=self.TEST_INTERVAL_DAYS)

        # Count failures
        failures = sum(
            1 for e in self._events
            if e.event_type == KillSwitchEventType.ARM_FAILURE
            or (e.response_time_ms and e.response_time_ms > self.MAX_RESPONSE_TIME_MS)
        )

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(
            response_times, last_test, failures, self._state
        )

        return KillSwitchMetrics(
            total_activations=len(activations),
            mean_response_time_ms=mean_response,
            max_response_time_ms=max_response,
            min_response_time_ms=min_response,
            last_test_date=last_test,
            next_required_test=next_test,
            uptime_hours=uptime,
            failures=failures,
            compliance_score=compliance_score
        )

    def _calculate_compliance_score(
        self,
        response_times: list[float],
        last_test: Optional[datetime],
        failures: int,
        current_state: KillSwitchState
    ) -> float:
        """Calculate Article 14 compliance score for kill-switch."""
        score = 1.0

        # State penalty (DISABLED is non-compliant)
        if current_state == KillSwitchState.DISABLED:
            score -= 0.5
        elif current_state == KillSwitchState.UNKNOWN:
            score -= 0.3

        # Response time penalty
        if response_times:
            exceed_count = sum(1 for t in response_times if t > self.MAX_RESPONSE_TIME_MS)
            if exceed_count > 0:
                score -= 0.2 * (exceed_count / len(response_times))

        # Test frequency penalty
        if last_test:
            days_since_test = (datetime.now() - last_test).days
            if days_since_test > self.TEST_INTERVAL_DAYS:
                score -= 0.2 * (days_since_test - self.TEST_INTERVAL_DAYS) / 30
        else:
            score -= 0.1  # Never tested

        # Failure penalty
        if failures > 0:
            score -= 0.1 * min(failures, 5)  # Cap at 0.5 penalty

        return max(0.0, min(1.0, score))

    def get_recent_events(
        self,
        hours: int = 24,
        event_types: Optional[list[KillSwitchEventType]] = None
    ) -> list[KillSwitchEvent]:
        """Get recent kill-switch events.

        Args:
            hours: Number of hours to look back
            event_types: Optional filter for event types

        Returns:
            List of recent KillSwitchEvent objects
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        events = [
            e for e in self._events
            if e.timestamp >= cutoff
        ]

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        return events

    def check_compliance(self) -> dict[str, Any]:
        """Check kill-switch compliance with Article 14(2)(d).

        Returns:
            Dict with compliance status and evidence
        """
        metrics = self.get_metrics()
        recent_activations = self.get_recent_events(hours=168)  # Last week

        issues = []
        evidence = []

        # Check state
        if self._state == KillSwitchState.ARMED:
            evidence.append("Kill switch is armed and active")
        elif self._state == KillSwitchState.DISABLED:
            issues.append("Kill switch is DISABLED - Article 14 non-compliance")
        else:
            issues.append(f"Kill switch state is {self._state.name} - unknown")

        # Check response time compliance
        if metrics.mean_response_time_ms > self.MAX_RESPONSE_TIME_MS:
            issues.append(
                f"Mean response time ({metrics.mean_response_time_ms:.0f}ms) exceeds "
                f"5 second limit"
            )
        else:
            evidence.append(
                f"Mean response time ({metrics.mean_response_time_ms:.0f}ms) is compliant"
            )

        # Check test frequency
        if metrics.next_required_test and datetime.now() > metrics.next_required_test:
            issues.append("Kill switch test is overdue")
        else:
            evidence.append(f"Last test: {metrics.last_test_date}")

        # Check for recent activations
        if recent_activations:
            evidence.append(f"{len(recent_activations)} activations in past week")
            for act in recent_activations[-3:]:
                evidence.append(
                    f"  - {act.timestamp}: {act.triggered_by} triggered "
                    f"(response: {act.response_time_ms}ms)"
                )

        return {
            "is_compliant": len(issues) == 0,
            "state": self._state.name,
            "issues": issues,
            "evidence": evidence,
            "metrics": {
                "total_activations": metrics.total_activations,
                "mean_response_time_ms": metrics.mean_response_time_ms,
                "compliance_score": metrics.compliance_score
            }
        }

    def get_article_14_evidence(self) -> dict[str, Any]:
        """Generate evidence for EU AI Act Article 14(2)(d) compliance.

        Returns:
            Dict with evidence suitable for audit documentation
        """
        metrics = self.get_metrics()
        compliance = self.check_compliance()

        return {
            "article": "14(2)(d)",
            "requirement": "Override, disengage, or reverse system decisions",
            "evidence_type": "Kill-switch mechanism",
            "compliance_status": "COMPLIANT" if compliance["is_compliant"] else "NON_COMPLIANT",
            "mechanism_state": self._state.name,
            "response_time_compliance": {
                "max_acceptable_ms": self.MAX_RESPONSE_TIME_MS,
                "actual_mean_ms": metrics.mean_response_time_ms,
                "actual_max_ms": metrics.max_response_time_ms,
                "is_compliant": metrics.mean_response_time_ms <= self.MAX_RESPONSE_TIME_MS
            },
            "test_compliance": {
                "last_test": metrics.last_test_date.isoformat() if metrics.last_test_date else None,
                "next_required": metrics.next_required_test.isoformat() if metrics.next_required_test else None,
                "interval_days": self.TEST_INTERVAL_DAYS
            },
            "recent_activations": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "triggered_by": e.triggered_by,
                    "reason": e.reason,
                    "response_time_ms": e.response_time_ms
                }
                for e in self.get_recent_events(hours=168)
            ],
            "compliance_score": metrics.compliance_score
        }