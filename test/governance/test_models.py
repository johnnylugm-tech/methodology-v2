"""Tests for governance data models."""

import pytest
from datetime import datetime, timedelta
from implement.governance.enums import (
    Tier,
    ApprovalStatus,
    AuthorizedRole,
    OperationType,
    OperationScope,
    RiskLevel,
)
from implement.governance.models import (
    Identity,
    OperationSummary,
    TierOverride,
    TierDecision,
    GovernanceContext,
    ApprovalRequest,
    ApproverResponse,
    EscalationEvent,
    AuditEntry,
)


class TestTierDecisionCreation:
    def test_tier_decision_creation(self):
        """TierDecision has all required fields."""
        now = datetime.utcnow()
        decision = TierDecision(
            operation_id="op-001",
            tier=Tier.HOTL,
            classification_reason="Routine operation",
            timestamp=now,
            confidence=0.95,
            overrides=[],
        )
        assert decision.operation_id == "op-001"
        assert decision.tier == Tier.HOTL
        assert decision.classification_reason == "Routine operation"
        assert decision.timestamp == now
        assert decision.confidence == 0.95
        assert decision.overrides == []


class TestGovernanceContextCreation:
    def test_governance_context_creation(self):
        """GovernanceContext has all required fields."""
        identity = Identity(identity_id="id-001", name="Test User")
        context = GovernanceContext(
            operation_id="op-002",
            operation_type=OperationType.CODE_GENERATION,
            risk_level=RiskLevel.ROUTINE,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=identity,
            historical_precedent="prev-decision-id",
            metadata={"key": "value"},
        )
        assert context.operation_id == "op-002"
        assert context.operation_type == OperationType.CODE_GENERATION
        assert context.risk_level == RiskLevel.ROUTINE
        assert context.scope == OperationScope.SINGLE_AGENT
        assert context.requester_identity == identity
        assert context.historical_precedent == "prev-decision-id"
        assert context.metadata == {"key": "value"}


class TestApprovalRequestCreation:
    def test_approval_request_creation(self):
        """ApprovalRequest has all required fields."""
        now = datetime.utcnow()
        identity = Identity(identity_id="id-001", name="Approver")
        context = GovernanceContext(
            operation_id="op-003",
            operation_type=OperationType.CODE_GENERATION,
            risk_level=RiskLevel.ELEVATED,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=identity,
        )
        operation = OperationSummary(
            operation_id="op-003",
            operation_type=OperationType.CODE_GENERATION,
            description="Write test",
        )
        sla = now + timedelta(hours=24)
        request = ApprovalRequest(
            request_id="req-001",
            operation_id="op-003",
            operation=operation,
            requested_tier=Tier.HITL,
            context=context,
            sla_deadline=sla,
            status=ApprovalStatus.PENDING,
            created_at=now,
            approver_identity=identity,
        )
        assert request.request_id == "req-001"
        assert request.operation_id == "op-003"
        assert request.requested_tier == Tier.HITL
        assert request.status == ApprovalStatus.PENDING
        assert request.sla_deadline == sla


class TestEscalationEventCreation:
    def test_escalation_event_creation(self):
        """EscalationEvent has all required fields."""
        now = datetime.utcnow()
        event = EscalationEvent(
            event_id="evt-001",
            operation_id="op-004",
            from_tier=Tier.HOTL,
            to_tier=Tier.HITL,
            trigger_reason="Anomaly detected",
            timestamp=now,
            acted_by="system",
            escalated_to_channel=True,
            fallback_tier=None,
        )
        assert event.event_id == "evt-001"
        assert event.operation_id == "op-004"
        assert event.from_tier == Tier.HOTL
        assert event.to_tier == Tier.HITL
        assert event.trigger_reason == "Anomaly detected"
        assert event.acted_by == "system"
        assert event.escalated_to_channel is True
        assert event.fallback_tier is None


class TestAuditEntryCreation:
    def test_audit_entry_creation(self):
        """AuditEntry has all required fields."""
        now = datetime.utcnow()
        operation = OperationSummary(
            operation_id="op-005",
            operation_type=OperationType.CODE_GENERATION,
            description="Generate code",
        )
        entry = AuditEntry(
            entry_id="audit-001",
            timestamp=now,
            operation=operation,
            tier=Tier.HOTL,
            decision="AUTO_APPROVE",
            actor="TierClassifier",
            outcome="success",
            metadata={"confidence": 0.95},
        )
        assert entry.entry_id == "audit-001"
        assert entry.timestamp == now
        assert entry.operation.operation_id == "op-005"
        assert entry.tier == Tier.HOTL
        assert entry.decision == "AUTO_APPROVE"
        assert entry.actor == "TierClassifier"
        assert entry.outcome == "success"
        assert entry.metadata["confidence"] == 0.95


class TestTierDecisionEquality:
    def test_tier_decision_equality(self):
        """Two TierDecision instances with same fields are equal."""
        now = datetime.utcnow()
        d1 = TierDecision(
            operation_id="op-001",
            tier=Tier.HOTL,
            classification_reason="Test",
            timestamp=now,
            confidence=0.95,
            overrides=[],
        )
        d2 = TierDecision(
            operation_id="op-001",
            tier=Tier.HOTL,
            classification_reason="Test",
            timestamp=now,
            confidence=0.95,
            overrides=[],
        )
        assert d1 == d2


class TestApprovalRequestStatusTransitions:
    def test_approval_request_status_transitions(self):
        """ApprovalStatus enum has all expected status values."""
        statuses = list(ApprovalStatus)
        assert ApprovalStatus.PENDING in statuses
        assert ApprovalStatus.APPROVED in statuses
        assert ApprovalStatus.DENIED in statuses
        assert ApprovalStatus.MODIFIED in statuses
        assert ApprovalStatus.ESCALATED in statuses
        assert ApprovalStatus.TIMEOUT in statuses


class TestTierOverrideModel:
    def test_tier_override_creation(self):
        """TierOverride records override details."""
        now = datetime.utcnow()
        override = TierOverride(
            original_tier=Tier.HOTL,
            new_tier=Tier.HITL,
            justification="Needs review",
            overridden_by="admin-001",
            overridden_at=now,
            role=AuthorizedRole.ADMIN,
        )
        assert override.original_tier == Tier.HOTL
        assert override.new_tier == Tier.HITL
        assert override.justification == "Needs review"
        assert override.overridden_by == "admin-001"
        assert override.overridden_at == now
        assert override.role == AuthorizedRole.ADMIN
