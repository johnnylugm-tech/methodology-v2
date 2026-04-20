#!/usr/bin/env python3
"""
test_tracker.py - Tests for Risk Tracker
[FR-04] Risk status tracking and history tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from implement.feature_09_risk_assessment.engine.tracker import RiskTracker, RiskHistoryEntry
from implement.feature_09_risk_assessment.models.risk import Risk
from implement.feature_09_risk_assessment.models.enums import RiskDimension, RiskLevel, RiskStatus


class TestRiskTracker:
    """Tests for RiskTracker [FR-04]"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.tracker = RiskTracker(str(self.project_root))

        # Create .methodology directory
        (self.project_root / ".methodology").mkdir(exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_init_database(self):
        """[FR-04] Database initialization"""
        # Database should exist after init
        assert self.tracker.db_path.exists()

    def test_save_and_load_risk(self):
        """[FR-04] Save and load risk"""
        risk = Risk(
            title="Test Risk",
            description="Test description",
            dimension=RiskDimension.TECHNICAL,
            probability=0.5,
            impact=3,
        )

        # Save
        success = self.tracker.save_risk(risk)
        assert success

        # Load
        loaded = self.tracker.load_risk(risk.id)
        assert loaded is not None
        assert loaded.title == "Test Risk"
        assert loaded.dimension == RiskDimension.TECHNICAL

    def test_load_all_risks(self):
        """[FR-04] Load all risks"""
        # Save multiple risks
        for i in range(3):
            risk = Risk(
                title=f"Risk {i}",
                description="Test",
                dimension=RiskDimension.TECHNICAL,
            )
            self.tracker.save_risk(risk)

        # Load all
        risks = self.tracker.load_all_risks()
        assert len(risks) >= 3

    def test_update_status_valid_transition(self):
        """[FR-04] Valid status transition"""
        risk = Risk(
            title="Test Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.OPEN,
        )
        self.tracker.save_risk(risk)

        # Transition OPEN -> MITIGATED
        success, msg = self.tracker.update_status(
            risk.id,
            RiskStatus.MITIGATED,
            changed_by="Test",
            note="Testing transition"
        )

        assert success
        assert "MITIGATED" in msg

    def test_update_status_invalid_transition(self):
        """[FR-04] Invalid status transition"""
        risk = Risk(
            title="Test Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.CLOSED,  # Terminal state
        )
        self.tracker.save_risk(risk)

        # Try to transition from CLOSED
        success, msg = self.tracker.update_status(
            risk.id,
            RiskStatus.OPEN,
            changed_by="Test"
        )

        assert not success
        assert "Invalid transition" in msg

    def test_get_history(self):
        """[FR-04] Get risk change history"""
        risk = Risk(
            title="Test Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
        )
        self.tracker.save_risk(risk)

        # Make some transitions
        self.tracker.update_status(risk.id, RiskStatus.MITIGATED, "Test", "First")
        self.tracker.update_status(risk.id, RiskStatus.CLOSED, "Test", "Second")

        # Get history
        history = self.tracker.get_history(risk.id)

        assert len(history) >= 2
        # Most recent first
        assert history[0].new_status == RiskStatus.CLOSED

    def test_get_open_risks(self):
        """[FR-04] Get all open risks"""
        # Create open and closed risks
        open_risk = Risk(
            title="Open Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.OPEN,
        )
        closed_risk = Risk(
            title="Closed Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.CLOSED,
        )

        self.tracker.save_risk(open_risk)
        self.tracker.save_risk(closed_risk)

        open_risks = self.tracker.get_open_risks()

        assert any(r.id == open_risk.id for r in open_risks)
        assert not any(r.id == closed_risk.id for r in open_risks)

    def test_get_closed_risks(self):
        """[FR-04] Get all closed risks"""
        closed_risk = Risk(
            title="Closed Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.CLOSED,
        )
        self.tracker.save_risk(closed_risk)

        closed_risks = self.tracker.get_closed_risks()

        assert any(r.id == closed_risk.id for r in closed_risks)

    def test_get_by_level(self):
        """[FR-04] Filter risks by level"""
        high_risk = Risk(
            title="High Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            level=RiskLevel.HIGH,
        )
        low_risk = Risk(
            title="Low Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            level=RiskLevel.LOW,
        )

        self.tracker.save_risk(high_risk)
        self.tracker.save_risk(low_risk)

        high_risks = self.tracker.get_by_level(RiskLevel.HIGH)

        assert any(r.id == high_risk.id for r in high_risks)
        assert not any(r.id == low_risk.id for r in high_risks)

    def test_export_to_register(self):
        """[FR-04] Export risk register summary"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            level=RiskLevel.HIGH,
            status=RiskStatus.OPEN,
        )
        self.tracker.save_risk(risk)

        export = self.tracker.export_to_register()

        assert "total" in export
        assert "open" in export
        assert "closed" in export
        assert "by_level" in export
        assert export["total"] >= 1

    def test_validate_state_machine_valid(self):
        """[FR-04] Validate valid state machine"""
        risk = Risk(
            title="Valid Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.CLOSED,
            closed_at=datetime.now(),
        )
        self.tracker.save_risk(risk)

        result = self.tracker.validate_state_machine()

        assert result["valid"]
        assert len(result["violations"]) == 0

    def test_validate_state_machine_violations(self):
        """[FR-04] Detect state machine violations"""
        # Create risk with violation: CLOSED but no closed_at
        risk = Risk(
            title="Invalid Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            status=RiskStatus.CLOSED,
            closed_at=None,  # Violation!
        )
        self.tracker.save_risk(risk)

        result = self.tracker.validate_state_machine()

        assert not result["valid"]
        assert len(result["violations"]) > 0


class TestRiskStatusTransitions:
    """Tests for RiskStatus state machine"""

    def test_open_can_transition(self):
        """[FR-04] OPEN can transition to MITIGATED, ACCEPTED, ESCALATED"""
        open_status = RiskStatus.OPEN

        assert open_status.can_transition_to(RiskStatus.MITIGATED)
        assert open_status.can_transition_to(RiskStatus.ACCEPTED)
        assert open_status.can_transition_to(RiskStatus.ESCALATED)

    def test_open_cannot_transition_to_closed(self):
        """[FR-04] OPEN cannot go directly to CLOSED"""
        open_status = RiskStatus.OPEN

        # Must go through MITIGATED or ACCEPTED first
        assert not open_status.can_transition_to(RiskStatus.CLOSED)

    def test_closed_is_terminal(self):
        """[FR-04] CLOSED is terminal state"""
        closed_status = RiskStatus.CLOSED

        # Cannot transition from CLOSED
        for target in RiskStatus:
            if target != RiskStatus.CLOSED:
                assert not closed_status.can_transition_to(target)

    def test_mitigated_can_close(self):
        """[FR-04] MITIGATED can transition to CLOSED"""
        mitigated = RiskStatus.MITIGATED

        assert mitigated.can_transition_to(RiskStatus.CLOSED)
        assert mitigated.can_transition_to(RiskStatus.ESCALATED)


class TestRiskHistoryEntry:
    """Tests for RiskHistoryEntry"""

    def test_history_entry_creation(self):
        """[FR-04] Create history entry"""
        entry = RiskHistoryEntry(
            risk_id="R-001",
            changed_at=datetime.now(),
            old_status=RiskStatus.OPEN,
            new_status=RiskStatus.MITIGATED,
            changed_by="Test",
            note="Testing",
        )

        assert entry.risk_id == "R-001"
        assert entry.old_status == RiskStatus.OPEN
        assert entry.new_status == RiskStatus.MITIGATED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])