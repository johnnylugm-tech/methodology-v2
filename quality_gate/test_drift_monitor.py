"""
Tests for drift_monitor.py
Covers: DriftAlert, DriftMonitor, _score_to_severity, run_and_alert
"""
import pytest
from unittest.mock import MagicMock, patch
from quality_gate.drift_monitor import DriftAlert, DriftMonitor


# ---------------------------------------------------------------------------
# DriftAlert tests
# ---------------------------------------------------------------------------

class TestDriftAlert:
    def test_default_fields(self):
        alert = DriftAlert(
            message="Test drift",
            drift_score=0.6,
            severity="high",
        )
        assert alert.severity == "high"
        assert alert.source == "drift_detector"
        assert alert.drift_score == 0.6
        assert "drift-" in alert.id
        assert alert.artifacts == []

    def test_to_dict(self):
        alert = DriftAlert(
            alert_id="test-001",
            message="dir structure changed",
            drift_score=0.4,
            severity="medium",
            artifacts=["src/"],
            recommended_action="Update baseline",
            details={"foo": "bar"},
        )
        d = alert.to_dict()
        assert d["id"] == "test-001"
        assert d["severity"] == "medium"
        assert d["drift_score"] == 0.4
        assert d["artifacts"] == ["src/"]
        assert d["details"]["foo"] == "bar"

    def test_to_feedback_format(self):
        alert = DriftAlert(
            alert_id="fb-001",
            severity="high",
            source="drift_detector",
            message="Structure drift on src/",
            drift_score=0.7,
            artifacts=["src/"],
            recommended_action="Update baseline",
            details={"key": "value"},
        )
        fb = alert.to_feedback()
        # StandardFeedback required fields
        assert fb["id"] == "fb-001"
        assert fb["source"] == "drift_detector"
        assert fb["source_detail"] == "architecture_drift"
        assert fb["type"] == "alert"
        assert fb["category"] == "architecture"
        assert fb["severity"] == "high"
        assert fb["title"] == "Architecture Drift: high"
        assert fb["description"] == "Structure drift on src/"
        # context
        assert fb["context"]["drift_score"] == 0.7
        assert fb["context"]["artifacts"] == ["src/"]
        assert fb["context"]["recommended_action"] == "Update baseline"
        # defaults
        assert fb["status"] == "pending"
        assert fb["sla_deadline"] is None
        assert fb["assignee"] is None
        assert fb["confidence"] == 0.95
        assert "drift" in fb["tags"]
        assert "architecture" in fb["tags"]


# ---------------------------------------------------------------------------
# _score_to_severity tests
# ---------------------------------------------------------------------------

class TestScoreToSeverity:
    def test_critical_threshold(self):
        assert DriftMonitor._score_to_severity(0.8) == "critical"
        assert DriftMonitor._score_to_severity(1.0) == "critical"
        assert DriftMonitor._score_to_severity(0.81) == "critical"

    def test_high_threshold(self):
        assert DriftMonitor._score_to_severity(0.5) == "high"
        assert DriftMonitor._score_to_severity(0.79) == "high"
        assert DriftMonitor._score_to_severity(0.51) == "high"

    def test_medium_threshold(self):
        assert DriftMonitor._score_to_severity(0.3) == "medium"
        assert DriftMonitor._score_to_severity(0.49) == "medium"
        assert DriftMonitor._score_to_severity(0.31) == "medium"

    def test_low_threshold(self):
        assert DriftMonitor._score_to_severity(0.0) == "low"
        assert DriftMonitor._score_to_severity(0.29) == "low"
        assert DriftMonitor._score_to_severity(0.1) == "low"


# ---------------------------------------------------------------------------
# DriftMonitor.run_and_alert tests
# ---------------------------------------------------------------------------

class TestRunAndAlert:
    def test_no_drift_returns_none(self):
        """當 _check_drift 報告無 drift，run_and_alert 應回傳 None"""
        monitor = DriftMonitor(project_path="/fake/path")
        # Mock _check_drift to return no drift
        with patch.object(monitor, "_check_drift", return_value={"has_drift": False}):
            result = monitor.run_and_alert()
        assert result is None

    def test_has_drift_returns_alert(self):
        """當 _check_drift 報告有 drift，run_and_alert 應回傳 DriftAlert"""
        monitor = DriftMonitor(project_path="/fake/path")
        with patch.object(monitor, "_check_drift", return_value={
            "has_drift": True,
            "drift_score": 0.6,
            "message": "src/ directory changed",
            "drifted_artifacts": ["src/"],
            "recommendation": "Update baseline",
        }):
            result = monitor.run_and_alert()
        assert isinstance(result, DriftAlert)
        assert result.severity == "high"          # 0.6 → high
        assert result.drift_score == 0.6
        assert result.message == "src/ directory changed"
        assert result.artifacts == ["src/"]

    def test_feedback_store_called_on_drift(self):
        """有 drift 時，feedback_store.add 應被呼叫"""
        mock_store = MagicMock()
        monitor = DriftMonitor(project_path="/fake/path", feedback_store=mock_store)
        with patch.object(monitor, "_check_drift", return_value={
            "has_drift": True,
            "drift_score": 0.9,
            "message": "Critical structure drift",
            "drifted_artifacts": [],
            "recommendation": "Investigate",
        }):
            monitor.run_and_alert()
        mock_store.add.assert_called_once()
        fb = mock_store.add.call_args[0][0]
        assert fb["type"] == "alert"
        assert fb["category"] == "architecture"
        assert fb["severity"] == "critical"  # 0.9 → critical

    def test_feedback_store_not_called_when_no_drift(self):
        """無 drift 時，feedback_store.add 不應被呼叫"""
        mock_store = MagicMock()
        monitor = DriftMonitor(project_path="/fake/path", feedback_store=mock_store)
        with patch.object(monitor, "_check_drift", return_value={"has_drift": False}):
            monitor.run_and_alert()
        mock_store.add.assert_not_called()

    def test_feedback_store_optional(self):
        """feedback_store=None 時不應拋錯"""
        monitor = DriftMonitor(project_path="/fake/path", feedback_store=None)
        with patch.object(monitor, "_check_drift", return_value={
            "has_drift": True,
            "drift_score": 0.4,
            "message": "Minor drift",
            "drifted_artifacts": [],
            "recommendation": "Check",
        }):
            result = monitor.run_and_alert()
        assert isinstance(result, DriftAlert)


# ---------------------------------------------------------------------------
# DriftMonitor._check_drift with real BaselineManager mock
# ---------------------------------------------------------------------------

class TestCheckDrift:
    def test_check_drift_no_baseline_manager(self):
        """無 baseline_manager 時回傳 has_drift=False"""
        monitor = DriftMonitor(project_path="/fake/path", baseline_manager=None)
        result = monitor._check_drift()
        assert result["has_drift"] is False

    def test_check_drift_with_empty_drift(self):
        """BaselineManager 回傳空 drift"""
        mock_bm = MagicMock()
        # Mock DriftResult dataclass
        mock_result = MagicMock()
        mock_result.drift = {}
        mock_result.summary = "No drift"
        mock_bm.check_drift.return_value = mock_result

        monitor = DriftMonitor(project_path="/fake/path", baseline_manager=mock_bm)
        result = monitor._check_drift()
        assert result["has_drift"] is False
        assert result["drift_score"] == 0.0

    def test_check_drift_with_structure_drift(self):
        """有結構 drift 時回報正確資訊"""
        mock_bm = MagicMock()
        mock_result = MagicMock()
        # Simulate a DriftResult dataclass by marking it with __dataclass_fields__
        mock_result.__dataclass_fields__ = {}
        mock_result.drift = {
            "structure": {
                "baseline": {},
                "current": {"src/": "added"},
                "severity": "medium",
            }
        }
        mock_result.summary = "Structure drift detected"
        mock_bm.check_drift.return_value = mock_result
        monitor = DriftMonitor(project_path="/fake/path", baseline_manager=mock_bm)
        result = monitor._check_drift()
        assert result["has_drift"] is True
        assert "structure" in result["drifted_artifacts"]
        assert result["message"] == "Structure drift detected"

        monitor = DriftMonitor(project_path="/fake/path", baseline_manager=mock_bm)
        result = monitor._check_drift()
        assert result["has_drift"] is True
        assert "structure" in result["drifted_artifacts"]
        assert result["message"] == "Structure drift detected"


# ---------------------------------------------------------------------------
# run_cron tests
# ---------------------------------------------------------------------------

class TestRunCron:
    def test_run_cron_with_drift(self):
        """run_cron 有 drift 時回傳含 alert 的 list"""
        monitor = DriftMonitor(project_path="/fake/path")
        with patch.object(monitor, "run_and_alert") as mock_run:
            mock_run.return_value = DriftAlert(message="test", drift_score=0.5)
            result = monitor.run_cron()
        assert len(result) == 1
        assert isinstance(result[0], DriftAlert)

    def test_run_cron_no_drift(self):
        """run_cron 無 drift 時回傳空 list"""
        monitor = DriftMonitor(project_path="/fake/path")
        with patch.object(monitor, "run_and_alert", return_value=None):
            result = monitor.run_cron()
        assert result == []
