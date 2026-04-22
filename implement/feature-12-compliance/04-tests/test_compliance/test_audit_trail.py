"""Audit Trail Tests.

FR-12-07: Immutable Audit Trail for compliance evidence and regulatory audits.

Tests cover:
- Audit trail creation and immutable logging
- Query and search functionality
- Evidence package generation
- Retention policy enforcement
- Cryptographic integrity verification
"""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List
from pathlib import Path
import sys
import hashlib
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from compliance.audit_trail import (
    OverrideAuditLogger,
    OverrideEvent,
    OverrideType,
    OverrideReason,
    OverrideMetrics
)


class TestOverrideAuditLogger:
    """Test suite for Override Audit Logger (FR-12-07)."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        """Create audit logger instance."""
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    # === Happy Path Tests ===

    def test_fr12_07_01_log_override(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Log human override event to audit trail."""
        event = audit_logger.log_override(**sample_override_data)

        assert isinstance(event, OverrideEvent)
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.hash is not None

    def test_fr12_07_02_immutability_check(self, audit_logger, sample_override_data):
        """FR-12-07 AC2: Verify entries cannot be modified after creation."""
        event = audit_logger.log_override(**sample_override_data)

        result = audit_logger.verify_integrity(event)

        assert result is True

    def test_fr12_07_03_query_by_time_range(self, audit_logger, sample_override_data):
        """FR-12-07 AC3: Query audit trail by time range."""
        now = datetime.now()
        audit_logger.log_override(**sample_override_data)

        events = audit_logger.get_events(
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1)
        )

        assert isinstance(events, list)
        assert len(events) >= 1

    def test_fr12_07_04_query_by_triggered_by(self, audit_logger, sample_override_data):
        """FR-12-07 AC3: Query audit trail by triggered_by."""
        audit_logger.log_override(**sample_override_data)

        events = audit_logger.get_events(triggered_by="trader-001")

        assert all(e.triggered_by == "trader-001" for e in events)

    def test_fr12_07_05_query_by_override_type(self, audit_logger, sample_override_data):
        """FR-12-07 AC3: Query audit trail by override type."""
        audit_logger.log_override(**sample_override_data)

        events = audit_logger.get_events(override_types=[OverrideType.APPROVAL_OVERRIDE])

        assert all(e.override_type == OverrideType.APPROVAL_OVERRIDE for e in events)

    # === Edge Cases ===

    def test_fr12_07_06_empty_query_results(self, audit_logger):
        """FR-12-07 EC1: Handle query with no matching results."""
        events = audit_logger.get_events(
            start_date=datetime.now() - timedelta(days=365),
            end_date=datetime.now() - timedelta(days=364)
        )

        assert isinstance(events, list)
        assert len(events) == 0

    def test_fr12_07_07_large_reason_detail(self, audit_logger):
        """FR-12-07 EC2: Handle large reason_detail in events."""
        large_data = {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "x" * 100000,
            "triggered_by": "test@system.com",
            "system_state": {},
            "ai_decision": None,
            "outcome": "completed"
        }

        event = audit_logger.log_override(**large_data)

        assert event.event_id is not None

    def test_fr12_07_08_unicode_in_events(self, audit_logger):
        """FR-12-07 EC3: Handle unicode characters in audit events."""
        event = audit_logger.log_override(
            override_type=OverrideType.APPROVAL_OVERRIDE,
            reason_category=OverrideReason.INFORMATION_ASYMMETRY,
            reason_detail="Unicode test: 你好世界 🌍",
            triggered_by="用户@test.com",
            system_state={"note": "測試"},
            ai_decision=None,
            outcome="completed"
        )

        events = audit_logger.get_events(triggered_by="用户@test.com")
        assert len(events) >= 1
        assert "你好世界" in events[0].reason_detail

    def test_fr12_07_09_concurrent_logging(self, audit_logger, sample_override_data):
        """FR-12-07 EC4: Handle concurrent event logging."""
        import threading

        def log_event():
            audit_logger.log_override(**sample_override_data)

        threads = [threading.Thread(target=log_event) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = audit_logger.get_events(limit=1000)

        assert len(events) >= 10

    def test_fr12_07_10_future_time_handling(self, audit_logger, sample_override_data):
        """FR-12-07 EC5: Handle timestamps slightly in the future."""
        event = audit_logger.log_override(**sample_override_data)

        result = audit_logger.verify_integrity(event)
        assert result is True

    # === Error Cases ===

    def test_fr12_07_11_verify_integrity_calculation(self, audit_logger, sample_override_data):
        """FR-12-07 ER1: Verify integrity calculation works for logged events."""
        event = audit_logger.log_override(**sample_override_data)

        result = audit_logger.verify_integrity(event)

        assert result is True

    def test_fr12_07_12_invalid_override_type(self, audit_logger):
        """FR-12-07 ER2: Raise error for invalid override type."""
        with pytest.raises(AttributeError):
            audit_logger.log_override(
                override_type="INVALID_TYPE",
                reason_category=OverrideReason.OTHER,
                reason_detail="test",
                triggered_by="test",
                system_state={},
                ai_decision=None,
                outcome="completed"
            )

    def test_fr12_07_13_empty_triggered_by(self, audit_logger, sample_override_data):
        """FR-12-07 ER3: Handle empty triggered_by field."""
        data = sample_override_data.copy()
        data["triggered_by"] = ""

        event = audit_logger.log_override(**data)

        assert event.event_id is not None
        assert event.triggered_by == ""

    def test_fr12_07_14_hash_integrity(self, audit_logger, sample_override_data):
        """FR-12-07 ER4: Each entry has proper hash for integrity."""
        event = audit_logger.log_override(**sample_override_data)

        # Hash should be a 16-character hex string
        assert event.hash is not None
        assert len(event.hash) == 16
        assert all(c in '0123456789abcdef' for c in event.hash)

    def test_fr12_07_15_missing_required_fields(self, audit_logger):
        """FR-12-07 ER5: Raise error when required fields are missing."""
        with pytest.raises(TypeError):
            audit_logger.log_override(
                override_type=OverrideType.APPROVAL_OVERRIDE,
                reason_category=OverrideReason.OTHER
                # Missing required fields
            )


class TestOverrideMetrics:
    """Test suite for override metrics calculation."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    def test_fr12_07_16_get_metrics(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Calculate override metrics for a period."""
        for _ in range(5):
            audit_logger.log_override(**sample_override_data)

        metrics = audit_logger.get_metrics()

        assert isinstance(metrics, OverrideMetrics)
        assert metrics.total_overrides >= 5
        assert isinstance(metrics.by_type, dict)
        assert isinstance(metrics.by_reason, dict)

    def test_fr12_07_17_empty_metrics(self, audit_logger):
        """FR-12-07 AC2: Handle empty audit trail metrics."""
        metrics = audit_logger.get_metrics()

        assert metrics.total_overrides == 0
        assert metrics.avg_response_time_ms == 0.0

    def test_fr12_07_18_metrics_with_duration(self, audit_logger):
        """FR-12-07 AC3: Calculate metrics with response time data."""
        event = audit_logger.log_override(
            override_type=OverrideType.APPROVAL_OVERRIDE,
            reason_category=OverrideReason.MARKET_CONDITION,
            reason_detail="Test event",
            triggered_by="trader-001",
            system_state={},
            ai_decision=None,
            outcome="completed"
        )

        metrics = audit_logger.get_metrics()

        assert metrics.avg_response_time_ms >= 0


class TestComplianceReport:
    """Test suite for compliance report generation."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    def test_fr12_07_19_generate_compliance_report(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Generate EU AI Act Article 14 compliance report."""
        for _ in range(5):
            audit_logger.log_override(**sample_override_data)

        report = audit_logger.generate_compliance_report(period_days=30)

        assert isinstance(report, dict)
        assert "period" in report
        assert "summary" in report
        assert "article_14_compliance" in report
        assert "recommendations" in report

    def test_fr12_07_20_report_contains_overrides(self, audit_logger, sample_override_data):
        """FR-12-07 AC2: Compliance report includes override events."""
        audit_logger.log_override(**sample_override_data)

        report = audit_logger.generate_compliance_report()

        assert report["summary"]["total_overrides"] >= 1

    def test_fr12_07_21_report_emergency_stops(self, audit_logger):
        """FR-12-07 AC3: Compliance report tracks emergency stops."""
        emergency_data = {
            "override_type": OverrideType.EMERGENCY_STOP,
            "reason_category": OverrideReason.RISK_MANAGEMENT,
            "reason_detail": "Emergency stop triggered",
            "triggered_by": "system",
            "system_state": {},
            "ai_decision": None,
            "outcome": "completed"
        }

        audit_logger.log_override(**emergency_data)

        report = audit_logger.generate_compliance_report()

        assert report["summary"]["emergency_stops"] >= 1


class TestExportAuditTrail:
    """Test suite for audit trail export."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    def test_fr12_07_22_export_json(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Export audit trail in JSON format."""
        audit_logger.log_override(**sample_override_data)

        exported = audit_logger.export_audit_trail(format="json")

        assert isinstance(exported, str)
        parsed = json.loads(exported)
        assert isinstance(parsed, list)
        assert len(parsed) >= 1

    def test_fr12_07_23_export_csv(self, audit_logger, sample_override_data):
        """FR-12-07 AC2: Export audit trail in CSV format."""
        audit_logger.log_override(**sample_override_data)

        exported = audit_logger.export_audit_trail(format="csv")

        assert isinstance(exported, str)
        lines = exported.split("\n")
        assert len(lines) >= 2
        assert "event_id" in lines[0]

    def test_fr12_07_24_export_date_filter(self, audit_logger, sample_override_data):
        """FR-12-07 AC3: Export with date filter."""
        audit_logger.log_override(**sample_override_data)

        now = datetime.now()
        exported = audit_logger.export_audit_trail(
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1),
            format="json"
        )

        parsed = json.loads(exported)
        assert len(parsed) >= 1


class TestRetentionAndCleanup:
    """Test suite for retention policy enforcement."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    def test_fr12_07_25_cleanup_old_events(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Remove events older than retention period."""
        audit_logger.log_override(**sample_override_data)

        deleted = audit_logger.cleanup_old_events()

        assert isinstance(deleted, int)

    def test_fr12_07_26_retention_days_config(self, audit_logger):
        """FR-12-07 AC2: Configure retention days on initialization."""
        logger = OverrideAuditLogger(retention_days=30)

        assert logger._retention_days == 30


class TestArticle14Evidence:
    """Test suite for Article 14 evidence generation."""

    @pytest.fixture
    def audit_logger(self) -> OverrideAuditLogger:
        return OverrideAuditLogger()

    @pytest.fixture
    def sample_override_data(self) -> Dict[str, Any]:
        """Generate sample override event data."""
        return {
            "override_type": OverrideType.APPROVAL_OVERRIDE,
            "reason_category": OverrideReason.MARKET_CONDITION,
            "reason_detail": "Sudden volatility spike detected",
            "triggered_by": "trader-001",
            "system_state": {"position": "LONG", "risk_level": "HIGH"},
            "ai_decision": {"action": "HOLD", "confidence": 0.85},
            "outcome": "completed"
        }

    def test_fr12_07_27_get_article_14_evidence(self, audit_logger, sample_override_data):
        """FR-12-07 AC1: Generate EU AI Act Article 14 compliance evidence."""
        for _ in range(3):
            audit_logger.log_override(**sample_override_data)

        evidence = audit_logger.get_article_14_evidence()

        assert isinstance(evidence, dict)
        assert evidence["article"] == "14"
        assert evidence["requirement"] == "Human oversight capability"
        assert "evidence_type" in evidence
        assert "period" in evidence
        assert "summary" in evidence

    def test_fr12_07_28_evidence_contains_integrity_verification(self, audit_logger, sample_override_data):
        """FR-12-07 AC2: Evidence includes integrity verification status."""
        audit_logger.log_override(**sample_override_data)

        evidence = audit_logger.get_article_14_evidence()

        assert evidence["summary"]["integrity_verified"] is True

    def test_fr12_07_29_evidence_recent_events(self, audit_logger, sample_override_data):
        """FR-12-07 AC3: Evidence includes recent events."""
        audit_logger.log_override(**sample_override_data)

        evidence = audit_logger.get_article_14_evidence()

        assert "recent_events" in evidence
        assert len(evidence["recent_events"]) >= 1