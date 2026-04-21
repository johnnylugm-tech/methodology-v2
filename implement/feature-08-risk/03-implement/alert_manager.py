"""
Alert Manager [FR-R-13]

Handles alert triggering, routing, and acknowledgment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AlertType(Enum):
    """Types of alerts supported."""
    CONFIDENCE_MISMATCH = "confidence_mismatch"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    COMPOSITE_RISK_HIGH = "composite_risk_high"
    COST_OVERRUN = "cost_overrun"
    UAF_DEPTH_EXCEEDED = "uaf_depth_exceeded"
    MEMORY_TAMPERING_DETECTED = "memory_tampering_detected"
    COMPLIANCE_VIOLATION = "compliance_violation"
    LATENCY_SLO_BREACH = "latency_slo_breach"


@dataclass
class Alert:
    """
    Alert payload.

    Attributes:
        alert_id: Unique identifier
        alert_type: Type of alert
        severity: Alert severity
        timestamp: When alert was generated
        source_dimension: Which dimension triggered (if applicable)
        decision_id: Associated decision ID (if applicable)
        message: Human-readable message
        details: Additional details
        recommended_action: Suggested remediation
        acknowledged: Whether alert has been acknowledged
        acknowledged_by: Who acknowledged it
        acknowledged_at: When it was acknowledged
    """

    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    alert_type: str = ""
    severity: str = "HIGH"
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Source info
    source_dimension: Optional[str] = None
    decision_id: Optional[str] = None

    # Content
    message: str = ""
    details: dict = field(default_factory=dict)
    recommended_action: str = ""

    # Acknowledgment
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def acknowledge(self, by: str) -> None:
        """Mark alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_by = by
        self.acknowledged_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "source_dimension": self.source_dimension,
            "decision_id": self.decision_id,
            "message": self.message,
            "details": self.details,
            "recommended_action": self.recommended_action,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
        }


class AlertManager:
    """
    Manages alert lifecycle: evaluation, triggering, routing, and acknowledgment.

    [FR-R-13]
    """

    # Threshold mappings for alert triggers
    ALERT_THRESHOLDS = {
        AlertType.CONFIDENCE_MISMATCH: {"calibration_error": 0.3},
        AlertType.RISK_THRESHOLD_EXCEEDED: {"score": 0.6},
        AlertType.COMPOSITE_RISK_HIGH: {"composite": 0.6},
        AlertType.COST_OVERRUN: {"cost_ratio": 1.1},
        AlertType.UAF_DEPTH_EXCEEDED: {"depth_ratio": 1.0},
        AlertType.MEMORY_TAMPERING_DETECTED: {"tampering_score": 0.7},
        AlertType.COMPLIANCE_VIOLATION: {"compliance_score": 0.5},
        AlertType.LATENCY_SLO_BREACH: {"latency_ratio": 1.2},
    }

    def __init__(self, config: dict = None):
        """
        Initialize AlertManager.

        Args:
            config: Alert configuration settings
        """
        self.config = config or {}
        self._enabled = self.config.get("enabled", True)
        self._notify_on_critical = self.config.get("notify_on_critical", True)
        self._notify_on_high = self.config.get("notify_on_high", True)
        self._alert_store: list[Alert] = []

    @property
    def enabled(self) -> bool:
        """Check if alerting is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable alerting."""
        self._enabled = value

    def evaluate(
        self,
        dimension_scores: dict[str, float],
        composite_score: float,
        decision_id: Optional[str] = None,
        additional_context: dict = None
    ) -> list[Alert]:
        """
        Evaluate risk results and trigger appropriate alerts.

        Args:
            dimension_scores: Map of dimension ID to score
            composite_score: Overall composite risk score
            decision_id: Associated decision ID
            additional_context: Additional context for alert details

        Returns:
            List of triggered alerts
        """
        if not self._enabled:
            return []

        alerts = []
        context = additional_context or {}

        # Check composite risk
        if composite_score >= 0.8:
            alerts.append(self._create_alert(
                AlertType.COMPOSITE_RISK_HIGH,
                AlertSeverity.CRITICAL,
                f"Composite risk CRITICAL: {composite_score:.2f}",
                source_dimension=None,
                decision_id=decision_id,
                details={"composite_score": composite_score},
                recommended_action="Immediate halt and review required"
            ))
        elif composite_score >= 0.6:
            alerts.append(self._create_alert(
                AlertType.COMPOSITE_RISK_HIGH,
                AlertSeverity.HIGH,
                f"Composite risk HIGH: {composite_score:.2f}",
                source_dimension=None,
                decision_id=decision_id,
                details={"composite_score": composite_score},
                recommended_action="Block execution and alert team"
            ))

        # Check individual dimensions
        for dim_id, score in dimension_scores.items():
            dim_alerts = self._evaluate_dimension_alerts(dim_id, score, decision_id, context)
            alerts.extend(dim_alerts)

        # Store alerts
        self._alert_store.extend(alerts)

        return alerts

    def _evaluate_dimension_alerts(
        self,
        dimension_id: str,
        score: float,
        decision_id: Optional[str],
        context: dict
    ) -> list[Alert]:
        """Evaluate alerts for a specific dimension."""
        alerts = []

        # Map dimension to alert type
        dimension_alert_map = {
            "D1": AlertType.RISK_THRESHOLD_EXCEEDED,
            "D2": AlertType.RISK_THRESHOLD_EXCEEDED,
            "D3": AlertType.COST_OVERRUN,
            "D4": AlertType.UAF_DEPTH_EXCEEDED,
            "D5": AlertType.MEMORY_TAMPERING_DETECTED,
            "D6": AlertType.RISK_THRESHOLD_EXCEEDED,
            "D7": AlertType.LATENCY_SLO_BREACH,
            "D8": AlertType.COMPLIANCE_VIOLATION,
        }

        alert_type = dimension_alert_map.get(dimension_id, AlertType.RISK_THRESHOLD_EXCEEDED)

        # Determine severity based on score
        if score >= 0.8:
            severity = AlertSeverity.CRITICAL
        elif score >= 0.6:
            severity = AlertSeverity.HIGH
        elif score >= 0.4:
            severity = AlertSeverity.MEDIUM
        else:
            return []  # No alert for low scores

        # Check if we should notify based on severity
        if severity == AlertSeverity.CRITICAL and not self._notify_on_critical:
            return []
        if severity == AlertSeverity.HIGH and not self._notify_on_high:
            return []

        message = f"{dimension_id} risk {severity.value}: {score:.2f}"
        recommended = self._get_recommended_action(dimension_id, score)

        alerts.append(self._create_alert(
            alert_type,
            severity,
            message,
            source_dimension=dimension_id,
            decision_id=decision_id,
            details={"score": score, "threshold": self._get_threshold_for_alert(alert_type)},
            recommended_action=recommended
        ))

        return alerts

    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        source_dimension: Optional[str],
        decision_id: Optional[str],
        details: dict,
        recommended_action: str
    ) -> Alert:
        """Create an alert instance."""
        return Alert(
            alert_type=alert_type.value,
            severity=severity.value,
            source_dimension=source_dimension,
            decision_id=decision_id,
            message=message,
            details=details,
            recommended_action=recommended_action,
        )

    def _get_threshold_for_alert(self, alert_type: AlertType) -> float:
        """Get threshold value for an alert type."""
        thresholds = {
            AlertType.CONFIDENCE_MISMATCH: 0.3,
            AlertType.RISK_THRESHOLD_EXCEEDED: 0.6,
            AlertType.COMPOSITE_RISK_HIGH: 0.6,
            AlertType.COST_OVERRUN: 1.1,
            AlertType.UAF_DEPTH_EXCEEDED: 1.0,
            AlertType.MEMORY_TAMPERING_DETECTED: 0.7,
            AlertType.COMPLIANCE_VIOLATION: 0.5,
            AlertType.LATENCY_SLO_BREACH: 1.2,
        }
        return thresholds.get(alert_type, 0.5)

    def _get_recommended_action(self, dimension_id: str, score: float) -> str:
        """Get recommended action for a dimension."""
        actions = {
            "D1": "Review data privacy controls and encryption settings",
            "D2": "Implement input sanitization and validation",
            "D3": "Optimize token usage or increase budget",
            "D4": "Check for infinite loops and enforce depth limits",
            "D5": "Verify memory sources and check for tampering",
            "D6": "Review agent isolation and message sanitization",
            "D7": "Investigate performance issues and optimize",
            "D8": "Review compliance requirements and audit trail",
        }
        base_action = actions.get(dimension_id, "Review and remediate")

        if score >= 0.8:
            return f"IMMEDIATE ACTION: {base_action}"
        elif score >= 0.6:
            return f"URGENT: {base_action}"
        return base_action

    def acknowledge_alert(self, alert_id: str, by: str) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: ID of alert to acknowledge
            by: Who is acknowledging

        Returns:
            True if found and acknowledged, False otherwise
        """
        for alert in self._alert_store:
            if alert.alert_id == alert_id:
                alert.acknowledge(by)
                return True
        return False

    def get_active_alerts(self, severity: Optional[str] = None) -> list[Alert]:
        """
        Get all active (unacknowledged) alerts.

        Args:
            severity: Optional filter by severity level

        Returns:
            List of active alerts
        """
        alerts = [a for a in self._alert_store if not a.acknowledged]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alerts_by_decision(self, decision_id: str) -> list[Alert]:
        """Get all alerts for a specific decision."""
        return [a for a in self._alert_store if a.decision_id == decision_id]

    def clear_acknowledged_alerts(self) -> int:
        """Remove acknowledged alerts from store."""
        original_count = len(self._alert_store)
        self._alert_store = [a for a in self._alert_store if not a.acknowledged]
        return original_count - len(self._alert_store)

    def trigger_confidence_mismatch(
        self,
        decision_id: str,
        initial_confidence: float,
        actual_outcome: float,
        calibration_error: float
    ) -> Alert:
        """Trigger a confidence mismatch alert."""
        alert = Alert(
            alert_type=AlertType.CONFIDENCE_MISMATCH.value,
            severity=AlertSeverity.HIGH.value,
            source_dimension=None,
            decision_id=decision_id,
            message=f"Confidence mismatch: initial={initial_confidence:.2f}, actual={actual_outcome:.2f}",
            details={
                "initial_confidence": initial_confidence,
                "actual_outcome": actual_outcome,
                "calibration_error": calibration_error,
            },
            recommended_action="Review confidence calibration and adjust thresholds"
        )
        self._alert_store.append(alert)
        return alert

    def to_dict(self) -> dict:
        """Export alert state for serialization."""
        return {
            "enabled": self._enabled,
            "notify_on_critical": self._notify_on_critical,
            "notify_on_high": self._notify_on_high,
            "total_alerts": len(self._alert_store),
            "active_alerts": len(self.get_active_alerts()),
        }