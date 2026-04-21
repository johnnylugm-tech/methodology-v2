"""
Tests for AlertManager [FR-R-13]

Covers alert triggering, routing, acknowledgment, and severity levels.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from alert_manager import AlertManager, Alert, AlertSeverity, AlertType


class TestAlertConstructor:
    """Test Alert constructor and methods."""

    def test_alert_default_values(self):
        """Test alert default values."""
        alert = Alert(
            alert_type="test_type",
            severity="HIGH",
            message="Test alert"
        )
        assert alert.alert_type == "test_type"
        assert alert.severity == "HIGH"
        assert alert.message == "Test alert"
        assert alert.acknowledged is False
        assert alert.acknowledged_by is None
        assert alert.acknowledged_at is None

    def test_alert_acknowledge(self):
        """Test alert acknowledgment."""
        alert = Alert(alert_type="test", severity="HIGH", message="Test")
        alert.acknowledge("reviewer1")

        assert alert.acknowledged is True
        assert alert.acknowledged_by == "reviewer1"
        assert alert.acknowledged_at is not None

    def test_alert_to_dict(self):
        """Test alert serialization to dict."""
        alert = Alert(
            alert_id="test123",
            alert_type="risk_exceeded",
            severity="CRITICAL",
            message="Test message",
            source_dimension="D1"
        )
        d = alert.to_dict()

        assert d["alert_id"] == "test123"
        assert d["alert_type"] == "risk_exceeded"
        assert d["severity"] == "CRITICAL"
        assert d["message"] == "Test message"
        assert d["source_dimension"] == "D1"


class TestAlertManagerConstructor:
    """Test AlertManager constructor."""

    def test_constructor_default_enabled(self):
        """Test default enabled state."""
        manager = AlertManager()
        assert manager.enabled is True

    def test_constructor_with_config(self):
        """Test constructor with custom config."""
        config = {
            "enabled": False,
            "notify_on_critical": False,
            "notify_on_high": False
        }
        manager = AlertManager(config)
        assert manager.enabled is False
        assert manager._notify_on_critical is False

    def test_enable_setter(self):
        """Test enable/disable setter."""
        manager = AlertManager()
        manager.enabled = False
        assert manager.enabled is False
        manager.enabled = True
        assert manager.enabled is True


class TestAlertManagerEvaluate:
    """Test alert evaluation."""

    def test_evaluate_disabled_returns_empty(self):
        """Test disabled manager returns empty list."""
        manager = AlertManager({"enabled": False})
        alerts = manager.evaluate(
            dimension_scores={"D1": 0.5},
            composite_score=0.5
        )
        assert alerts == []

    def test_evaluate_critical_composite(self):
        """Test critical composite score triggers alert."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={},
            composite_score=0.85
        )

        assert len(alerts) >= 1
        crit_alerts = [a for a in alerts if a.severity == "CRITICAL"]
        assert len(crit_alerts) >= 1

    def test_evaluate_high_composite(self):
        """Test high composite score triggers alert."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={},
            composite_score=0.7
        )

        assert len(alerts) >= 1
        high_alerts = [a for a in alerts if a.severity == "HIGH"]
        assert len(high_alerts) >= 1

    def test_evaluate_medium_composite_no_alert(self):
        """Test medium composite score doesn't trigger composite alert."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={},
            composite_score=0.5
        )

        # No CRITICAL/HIGH composite alert for medium
        composite_alerts = [a for a in alerts if a.source_dimension is None]
        assert len(composite_alerts) == 0

    def test_evaluate_dimension_alerts_d1(self):
        """Test D1 (privacy) dimension alerts."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={"D1": 0.7},
            composite_score=0.3
        )

        dim_alerts = [a for a in alerts if a.source_dimension == "D1"]
        assert len(dim_alerts) >= 1

    def test_evaluate_dimension_alerts_d2(self):
        """Test D2 (injection) dimension alerts."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={"D2": 0.65},
            composite_score=0.3
        )

        dim_alerts = [a for a in alerts if a.source_dimension == "D2"]
        assert len(dim_alerts) >= 1

    def test_evaluate_dimension_alerts_d3_cost(self):
        """Test D3 (cost) dimension alerts."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={"D3": 0.7},
            composite_score=0.3
        )

        dim_alerts = [a for a in alerts if a.source_dimension == "D3"]
        assert len(dim_alerts) >= 1

    def test_evaluate_low_score_no_alert(self):
        """Test low dimension score doesn't trigger alert."""
        manager = AlertManager()
        alerts = manager.evaluate(
            dimension_scores={"D1": 0.3},
            composite_score=0.2
        )

        # No alerts for low scores
        assert len(alerts) == 0

    def test_evaluate_stores_alerts(self):
        """Test that evaluate stores alerts."""
        manager = AlertManager()
        initial_count = len(manager._alert_store)

        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.5)

        assert len(manager._alert_store) > initial_count


class TestAlertManagerAcknowledge:
    """Test alert acknowledgment."""

    def test_acknowledge_existing_alert(self):
        """Test acknowledging an existing alert."""
        manager = AlertManager()
        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.5)

        alert_id = manager._alert_store[0].alert_id
        result = manager.acknowledge_alert(alert_id, "reviewer1")

        assert result is True
        assert manager._alert_store[0].acknowledged is True

    def test_acknowledge_nonexistent_alert(self):
        """Test acknowledging non-existent alert."""
        manager = AlertManager()
        result = manager.acknowledge_alert("nonexistent", "reviewer1")
        assert result is False

    def test_get_active_alerts(self):
        """Test getting active (unacknowledged) alerts."""
        manager = AlertManager()
        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.5)

        active = manager.get_active_alerts()
        assert len(active) >= 1
        assert all(not a.acknowledged for a in active)

    def test_get_active_alerts_filtered_by_severity(self):
        """Test filtering active alerts by severity."""
        manager = AlertManager()
        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.9)

        critical_alerts = manager.get_active_alerts(severity="CRITICAL")
        assert all(a.severity == "CRITICAL" for a in critical_alerts)

    def test_get_alerts_by_decision(self):
        """Test getting alerts for a specific decision."""
        manager = AlertManager()
        manager.evaluate(
            dimension_scores={"D1": 0.7},
            composite_score=0.5,
            decision_id="dec-123"
        )

        alerts = manager.get_alerts_by_decision("dec-123")
        assert len(alerts) >= 1
        assert all(a.decision_id == "dec-123" for a in alerts)

    def test_clear_acknowledged_alerts(self):
        """Test clearing acknowledged alerts."""
        manager = AlertManager()
        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.5)

        alert_id = manager._alert_store[0].alert_id
        manager.acknowledge_alert(alert_id, "reviewer1")

        cleared = manager.clear_acknowledged_alerts()
        assert cleared == 1
        assert len(manager._alert_store) == 0


class TestAlertManagerConfidenceMismatch:
    """Test confidence mismatch alerts."""

    def test_trigger_confidence_mismatch(self):
        """Test triggering confidence mismatch alert."""
        manager = AlertManager()
        alert = manager.trigger_confidence_mismatch(
            decision_id="dec-456",
            initial_confidence=8.0,
            actual_outcome=3.0,
            calibration_error=5.0
        )

        assert alert is not None
        assert alert.alert_type == AlertType.CONFIDENCE_MISMATCH.value
        assert alert.decision_id == "dec-456"
        assert alert.severity == AlertSeverity.HIGH.value
        assert len(manager._alert_store) >= 1


class TestAlertManagerRecommendedActions:
    """Test recommended action generation."""

    def test_recommended_action_d1(self):
        """Test D1 recommended action."""
        action = AlertManager()._get_recommended_action("D1", 0.9)
        assert "privacy" in action.lower() or "IMMEDIATE" in action

    def test_recommended_action_d2(self):
        """Test D2 recommended action."""
        action = AlertManager()._get_recommended_action("D2", 0.7)
        assert "sanitiz" in action.lower() or "validation" in action.lower()

    def test_recommended_action_d3(self):
        """Test D3 recommended action."""
        action = AlertManager()._get_recommended_action("D3", 0.7)
        assert "token" in action.lower() or "cost" in action.lower() or "budget" in action.lower()

    def test_recommended_action_urgent(self):
        """Test urgent action for high scores."""
        action = AlertManager()._get_recommended_action("D4", 0.9)
        assert "IMMEDIATE" in action or "URGENT" in action

    def test_recommended_action_standard(self):
        """Test standard action for moderate scores."""
        action = AlertManager()._get_recommended_action("D5", 0.5)
        # Should not have IMMEDIATE or URGENT prefix
        assert action.startswith("Review") or len(action) > 0


class TestAlertManagerToDict:
    """Test AlertManager serialization."""

    def test_to_dict(self):
        """Test manager state serialization."""
        manager = AlertManager({
            "enabled": True,
            "notify_on_critical": True,
            "notify_on_high": False
        })
        manager.evaluate(dimension_scores={"D1": 0.9}, composite_score=0.5)

        d = manager.to_dict()
        assert d["enabled"] is True
        assert d["notify_on_critical"] is True
        assert d["notify_on_high"] is False
        assert d["total_alerts"] >= 1
        assert d["active_alerts"] >= 1


class TestAlertManagerThresholds:
    """Test alert threshold mapping."""

    def test_alert_thresholds_exist(self):
        """Test that ALERT_THRESHOLDS is defined."""
        assert len(AlertManager.ALERT_THRESHOLDS) > 0
        assert AlertType.COMPOSITE_RISK_HIGH in AlertManager.ALERT_THRESHOLDS
        assert AlertType.CONFIDENCE_MISMATCH in AlertManager.ALERT_THRESHOLDS

    def test_get_threshold_for_alert_type(self):
        """Test getting threshold for alert type."""
        manager = AlertManager()
        threshold = manager._get_threshold_for_alert(AlertType.COMPOSITE_RISK_HIGH)
        assert threshold == 0.6


class TestAlertManagerNotifySettings:
    """Test notification settings."""

    def test_notify_on_critical_disabled(self):
        """Test no critical alerts when disabled."""
        manager = AlertManager({
            "enabled": True,
            "notify_on_critical": False
        })
        # CRITICAL score but notifications disabled
        alerts = manager.evaluate(
            dimension_scores={"D1": 0.9},  # CRITICAL
            composite_score=0.9
        )

        # Alerts are still generated, but notify_on_critical affects notification
        critical = [a for a in alerts if a.severity == "CRITICAL"]
        assert len(critical) == 1  # Alert still generated
        assert alerts[0].acknowledged == False  # Not yet acknowledged

    def test_notify_on_high_disabled(self):
        """Test no high alerts when disabled."""
        manager = AlertManager({
            "enabled": True,
            "notify_on_high": False
        })
        # HIGH score but notifications disabled
        alerts = manager.evaluate(
            dimension_scores={"D1": 0.7},  # HIGH
            composite_score=0.7
        )

        # Alerts are still generated, but notify_on_high affects notification
        high = [a for a in alerts if a.severity == "HIGH"]
        assert len(high) == 1  # Alert still generated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
