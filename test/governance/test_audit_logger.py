"""Tests for AuditLogger."""

import pytest
import json
from datetime import datetime, timedelta
from implement.governance.enums import Tier, GovernanceDecision, OperationType, RiskLevel, OperationScope
from implement.governance.models import (
    GovernanceContext,
    Identity,
    OperationSummary,
    TierDecision,
    GovernanceQueryFilters,
    PaginationParams,
    EscalationEvent,
)
from implement.governance.audit_logger import AuditLogger


@pytest.fixture
def audit_logger():
    return AuditLogger()


@pytest.fixture
def identity():
    return Identity(identity_id="id-001", name="Test User")


@pytest.fixture
def governance_context(identity):
    return GovernanceContext(
        operation_id="op-audit-001",
        operation_type=OperationType.CODE_GENERATION,
        risk_level=RiskLevel.ROUTINE,
        scope=OperationScope.SINGLE_AGENT,
        requester_identity=identity,
        metadata={"affected_systems": ["system-a"]},
    )


@pytest.fixture
def tier_decision():
    return TierDecision(
        operation_id="op-audit-001",
        tier=Tier.HOTL,
        classification_reason="Routine code generation",
        timestamp=datetime.utcnow(),
        confidence=0.95,
        overrides=[],
    )


class TestLogCreatesEntry:
    def test_log_creates_entry(self, audit_logger, governance_context, tier_decision):
        """log_classification appends an entry and it is retrievable."""
        initial_count = audit_logger.get_entry_count()
        entry = audit_logger.log_classification(
            operation_id="op-audit-001",
            decision=tier_decision,
            context=governance_context,
        )
        assert audit_logger.get_entry_count() == initial_count + 1
        assert entry.entry_id is not None
        assert entry.tier == Tier.HOTL
        assert entry.decision.startswith("CLASSIFIED_AS_HOTL")


class TestQueryByDateRange:
    def test_query_by_date_range(self, audit_logger, governance_context, tier_decision):
        """query() filters entries by date range."""
        # Log an entry
        audit_logger.log_classification(
            operation_id="op-date-001",
            decision=tier_decision,
            context=governance_context,
        )
        now = datetime.utcnow()
        past = now - timedelta(days=30)
        future = now + timedelta(days=1)

        # Should find the entry in range
        results = audit_logger.query(
            GovernanceQueryFilters(start_date=past, end_date=future)
        )
        assert len(results) >= 1

        # Should not find entries outside range
        old = now - timedelta(days=60)
        older = now - timedelta(days=59)
        results_empty = audit_logger.query(
            GovernanceQueryFilters(start_date=old, end_date=older)
        )
        assert len(results_empty) == 0


class TestQueryByTier:
    def test_query_by_tier(self, audit_logger, governance_context, tier_decision):
        """query() filters entries by tier."""
        audit_logger.log_classification(
            operation_id="op-tier-001",
            decision=tier_decision,
            context=governance_context,
        )
        results = audit_logger.query(GovernanceQueryFilters(tier=Tier.HOTL))
        assert all(e.tier == Tier.HOTL for e in results)


class TestQueryByOperationId:
    def test_query_by_operation_id(self, audit_logger, governance_context, tier_decision):
        """query() filters entries by operation_id."""
        audit_logger.log_classification(
            operation_id="op-query-001",
            decision=tier_decision,
            context=governance_context,
        )
        results = audit_logger.query(
            GovernanceQueryFilters(operation_id="op-query-001")
        )
        assert all(e.operation.operation_id == "op-query-001" for e in results)


class TestGetOperationLog:
    def test_get_operation_log(self, audit_logger, governance_context, tier_decision):
        """get_operation_log returns all entries for a specific operation."""
        op_id = "op-log-001"
        audit_logger.log_classification(
            operation_id=op_id,
            decision=tier_decision,
            context=governance_context,
        )
        audit_logger.log_workflow_start(
            operation_id=op_id,
            tier=Tier.HOTL,
            workflow_type="HOTL_AUTOMATED",
        )
        entries = audit_logger.get_operation_log(op_id)
        assert len(entries) == 2
        assert all(e.operation.operation_id == op_id for e in entries)


class TestHashChainIntegrity:
    def test_hash_chain_integrity(self, audit_logger, governance_context, tier_decision):
        """GENESIS block is present; first entry hashes GENESIS as prev_hash."""
        # The first entry should have prev_hash = "GENESIS"
        entry = audit_logger.log_classification(
            operation_id="op-chain-001",
            decision=tier_decision,
            context=governance_context,
        )
        assert entry.metadata.get("_prev_hash") == "GENESIS", (
            "First entry should have GENESIS as previous hash"
        )
        assert entry.metadata.get("_chain_hash") is not None, (
            "Entry should have a chain hash computed"
        )
        # Verify the chain is intact
        assert audit_logger.verify() is True, "Hash chain should be valid"


class TestTamperDetection:
    def test_tamper_detection(self, audit_logger, governance_context, tier_decision):
        """Modified entry causes integrity check to fail."""
        entry = audit_logger.log_classification(
            operation_id="op tamper-001",
            decision=tier_decision,
            context=governance_context,
        )
        # Simulate tampering by modifying an entry's metadata
        audit_logger._entries[0].metadata["_chain_hash"] = "tampered_hash"
        assert audit_logger.verify() is False, (
            "Tampered entry should cause verify() to return False"
        )


class TestExportJsonFormat:
    def test_export_json_format(self, audit_logger, governance_context, tier_decision):
        """export() returns valid JSON string."""
        audit_logger.log_classification(
            operation_id="op-export-001",
            decision=tier_decision,
            context=governance_context,
        )
        exported = audit_logger.export(format="json")
        # Should be parseable JSON
        data = json.loads(exported)
        assert isinstance(data, list)
        assert len(data) >= 1


class TestAppendOnlyNoDelete:
    def test_append_only_no_delete(self, audit_logger):
        """AuditLogger has no delete method."""
        assert not hasattr(audit_logger, "delete"), (
            "AuditLogger should not have a delete method — it is append-only"
        )
        assert not hasattr(audit_logger, "remove"), (
            "AuditLogger should not have a remove method — it is append-only"
        )


class TestHealthReport:
    def test_health_report(self, audit_logger, governance_context, tier_decision):
        """get_health_report returns a dict with required fields."""
        audit_logger.log_classification(
            operation_id="op-health-001",
            decision=tier_decision,
            context=governance_context,
        )
        now = datetime.utcnow()
        past = now - timedelta(days=1)
        future = now + timedelta(days=1)
        report = audit_logger.get_health_report(start_date=past, end_date=future)
        assert hasattr(report, "start_date")
        assert hasattr(report, "end_date")
        assert hasattr(report, "total_operations")
        assert hasattr(report, "tier_distribution")
        assert hasattr(report, "escalation_count")
        assert hasattr(report, "hitl_approval_rate")
        assert hasattr(report, "mean_approval_time_hours")


class TestLogWorkflowComplete:
    def test_log_workflow_complete(self, audit_logger):
        """log_workflow_complete appends a completion entry."""
        initial = audit_logger.get_entry_count()
        entry = audit_logger.log_workflow_complete(
            operation_id="op-complete-001",
            outcome="success",
            tier=Tier.HOTL,
            duration_ms=150,
        )
        assert audit_logger.get_entry_count() == initial + 1
        assert "WORKFLOW_COMPLETE" in entry.decision
        assert entry.metadata["duration_ms"] == 150


class TestLogEscalation:
    def test_log_escalation(self, audit_logger):
        """log_escalation creates an audit entry for an escalation event."""
        event = EscalationEvent(
            event_id="evt-001",
            operation_id="op-esc-001",
            from_tier=Tier.HOTL,
            to_tier=Tier.HITL,
            trigger_reason="Scope creep detected",
            timestamp=datetime.utcnow(),
            acted_by="system",
        )
        entry = audit_logger.log_escalation(event)
        assert entry.decision.startswith("ESCALATION")
        assert entry.metadata["from_tier"] == "HOTL"
        assert entry.metadata["to_tier"] == "HITL"


class TestLogHumanAction:
    def test_log_human_action(self, audit_logger):
        """log_human_action creates an entry for human intervention."""
        entry = audit_logger.log_human_action(
            operation_id="op-human-001",
            action="Approved with modifications",
            actor_identity="admin@example.com",
            tier=Tier.HITL,
            details={"modifications": {"param": "value"}},
        )
        assert "HUMAN_ACTION" in entry.decision
        assert entry.actor == "admin@example.com"
        assert entry.outcome == "success"


class TestLogSecurityEvent:
    def test_log_security_event(self, audit_logger):
        """log_security_event creates a security-themed audit entry."""
        entry = audit_logger.log_security_event(
            operation_id="op-sec-001",
            event_type="unauthorized_override_attempt",
            actor_identity="unknown@example.com",
            tier=Tier.HOTL,
            details={"attempted_role": "OPERATOR"},
        )
        assert "SECURITY_EVENT" in entry.decision
        assert entry.outcome == "failure"
