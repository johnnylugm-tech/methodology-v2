"""Integration tests for full governance flow."""

import pytest
from datetime import datetime, timedelta
from implement.governance import (
    TierClassifier,
    GovernanceTrigger,
    EscalationEngine,
    AuditLogger,
    OverrideManager,
    Tier,
    GovernanceDecision,
    ApprovalStatus,
    RiskLevel,
    OperationType,
    OperationScope,
)
from implement.governance.models import GovernanceContext, Identity, OperationSummary
from implement.governance.enums import DEFAULT_HITL_SLA_HOURS


@pytest.fixture
def identity():
    return Identity(identity_id="id-001", name="Test User", role=None)


@pytest.fixture
def admin_identity():
    return Identity(identity_id="admin-001", name="Admin User", role=None)


@pytest.fixture
def classifier():
    return TierClassifier()


@pytest.fixture
def trigger():
    return GovernanceTrigger()


@pytest.fixture
def engine():
    return EscalationEngine()


@pytest.fixture
def audit_logger():
    return AuditLogger()


@pytest.fixture
def override_manager():
    return OverrideManager()


def make_context(operation_id, op_type, risk, scope, identity, metadata=None):
    return GovernanceContext(
        operation_id=operation_id,
        operation_type=op_type,
        risk_level=risk,
        scope=scope,
        requester_identity=identity,
        metadata=metadata or {},
    )


def make_operation(operation_id, op_type=OperationType.CODE_GENERATION):
    return OperationSummary(
        operation_id=operation_id,
        operation_type=op_type,
        description=f"Test operation {operation_id}",
    )


class TestFullHotlFlow:
    def test_full_hotl_flow(
        self, classifier, trigger, audit_logger, identity
    ):
        """
        Full HOTL flow: classify → auto-execute → log → complete.
        """
        operation_id = "op-inthotl-001"
        ctx = make_context(
            operation_id,
            OperationType.CODE_GENERATION,
            RiskLevel.ROUTINE,
            OperationScope.SINGLE_AGENT,
            identity,
            metadata={"data_classification": "public"},
        )
        operation = make_operation(operation_id)

        # Step 1: Classify
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HOTL

        # Step 2: Trigger evaluation
        result = trigger.evaluate_triggers(operation_id, ctx, decision)
        assert result.decision == GovernanceDecision.AUTO_APPROVE

        # Step 3: Fire workflow
        handle = trigger.fire_workflow(result.decision, operation, ctx)
        assert handle.tier == Tier.HOTL
        assert handle.status == "active"

        # Step 4: Log classification
        audit_logger.log_classification(operation_id, decision, ctx)

        # Step 5: Log workflow start
        audit_logger.log_workflow_start(operation_id, Tier.HOTL, "HOTL_AUTOMATED")

        # Step 6: Complete workflow
        audit_logger.log_workflow_complete(
            operation_id,
            outcome="success",
            tier=Tier.HOTL,
            duration_ms=50,
        )

        # Verify audit log
        entries = audit_logger.get_operation_log(operation_id)
        assert len(entries) == 3
        assert entries[0].decision.startswith("CLASSIFIED_AS")
        assert "WORKFLOW_START" in entries[1].decision
        assert "WORKFLOW_COMPLETE" in entries[2].decision

        # Complete the workflow
        trigger.complete_workflow(operation_id)
        assert operation_id not in trigger.get_active_workflows()


class TestFullHitlFlow:
    def test_full_hitl_flow(
        self, classifier, trigger, audit_logger, identity
    ):
        """
        Full HITL flow: classify → queue → approve → execute → log.
        """
        operation_id = "op-inthitl-001"
        ctx = make_context(
            operation_id,
            OperationType.REFACTORING,
            RiskLevel.ELEVATED,
            OperationScope.SINGLE_AGENT,
            identity,
        )
        operation = make_operation(operation_id, op_type=OperationType.REFACTORING)

        # Step 1: Classify
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HITL

        # Step 2: Trigger evaluation
        result = trigger.evaluate_triggers(operation_id, ctx, decision)
        assert result.decision == GovernanceDecision.PENDING_APPROVAL

        # Step 3: Fire workflow (creates approval request)
        handle = trigger.fire_workflow(result.decision, operation, ctx)
        assert handle.tier == Tier.HITL
        assert handle.workflow_type == "HITL_APPROVAL_QUEUE"

        # Verify approval request is in queue
        queue = trigger.get_hitl_queue()
        assert operation_id in queue
        req = queue[operation_id].request
        assert req.status == ApprovalStatus.PENDING
        assert req.requested_tier == Tier.HITL
        assert req.sla_deadline > datetime.utcnow()

        # Step 4: Log everything
        audit_logger.log_classification(operation_id, decision, ctx)
        audit_logger.log_workflow_start(operation_id, Tier.HITL, "HITL_APPROVAL_QUEUE")

        # Step 5: Approve (simulate human approval)
        audit_logger.log_human_action(
            operation_id=operation_id,
            action="Approved",
            actor_identity="approver@example.com",
            tier=Tier.HITL,
            details={"status": "APPROVED"},
        )
        req.status = ApprovalStatus.APPROVED

        # Step 6: Complete
        audit_logger.log_workflow_complete(
            operation_id,
            outcome="success",
            tier=Tier.HITL,
            duration_ms=3600000,  # 1 hour
        )

        # Verify audit log has all steps
        entries = audit_logger.get_operation_log(operation_id)
        assert len(entries) >= 4
        assert any("HUMAN_ACTION" in e.decision for e in entries)
        assert any("WORKFLOW_COMPLETE" in e.decision for e in entries)

        trigger.complete_workflow(operation_id)


class TestFullHootlFlow:
    def test_full_hootl_flow(
        self, classifier, trigger, audit_logger, identity
    ):
        """
        Full HOOTL flow: classify → emergency → execute → alert → log.
        """
        operation_id = "op-inthootl-001"
        ctx = make_context(
            operation_id,
            OperationType.EMERGENCY,
            RiskLevel.CRITICAL,
            OperationScope.SINGLE_AGENT,
            identity,
        )
        operation = make_operation(operation_id, op_type=OperationType.EMERGENCY)

        # Step 1: Classify
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HOOTL

        # Step 2: Trigger evaluation
        result = trigger.evaluate_triggers(operation_id, ctx, decision)
        assert result.decision == GovernanceDecision.EMERGENCY_TRIGGER

        # Step 3: Fire emergency protocol
        handle = trigger.fire_workflow(result.decision, operation, ctx)
        assert hasattr(handle, "protocol_id")  # EmergencyProtocolHandle
        assert operation_id in trigger.get_hootl_active()

        # Step 4: Log
        audit_logger.log_classification(operation_id, decision, ctx)
        audit_logger.log_workflow_start(operation_id, Tier.HOOTL, "EMERGENCY_TRIGGER")

        # Step 5: Take emergency actions
        audit_logger.log_human_action(
            operation_id=operation_id,
            action="Emergency action taken",
            actor_identity="emergency-responder@example.com",
            tier=Tier.HOOTL,
            details={"actions": ["isolated_system", "notified_team"]},
        )

        # Step 6: Complete
        audit_logger.log_workflow_complete(
            operation_id,
            outcome="success",
            tier=Tier.HOOTL,
            duration_ms=500,
        )

        # Verify HOOTL entries exist
        entries = audit_logger.get_operation_log(operation_id)
        assert len(entries) >= 4
        hootl_entries = [e for e in entries if e.tier == Tier.HOOTL]
        assert len(hootl_entries) >= 4

        # Generate incident report
        report = audit_logger.get_incident_report(
            operation_id=operation_id,
            event_id="evt-inthootl-001",
            trigger_reason="Emergency protocol activated",
        )
        assert report.operation_id == operation_id
        assert len(report.timeline) >= 4

        trigger.complete_workflow(operation_id)


class TestHitlTimeoutEscalatesToHootl:
    def test_hitl_timeout_escalates_to_hootl(
        self, classifier, trigger, engine, audit_logger, identity
    ):
        """
        HITL SLA exceeded → escalation to HOOTL.
        """
        operation_id = "op-inttimeout-001"
        ctx = make_context(
            operation_id,
            OperationType.REFACTORING,
            RiskLevel.ELEVATED,
            OperationScope.SINGLE_AGENT,
            identity,
        )
        operation = make_operation(operation_id)

        # Classify
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HITL

        # Trigger and fire
        result = trigger.evaluate_triggers(operation_id, ctx, decision)
        handle = trigger.fire_workflow(result.decision, operation, ctx)

        queue_entry = trigger.get_hitl_queue()[operation_id]
        # Simulate SLA expiry by setting status to TIMEOUT
        queue_entry.request.status = ApprovalStatus.TIMEOUT

        # Escalate to HOOTL
        escalation_event = engine.escalate(
            operation_id=operation_id,
            from_tier=Tier.HITL,
            to_tier=Tier.HOOTL,
            reason="HITL SLA exceeded — auto-escalating to HOOTL",
            acted_by="system",
        )
        assert escalation_event.to_tier == Tier.HOOTL

        # Log escalation
        audit_logger.log_escalation(escalation_event)

        # Verify escalation is logged
        entries = audit_logger.get_operation_log(operation_id)
        escalation_entries = [e for e in entries if "ESCALATION" in e.decision]
        assert len(escalation_entries) >= 1

        # Verify escalation history in engine
        history = engine.get_escalation_history(operation_id)
        assert any(e.to_tier == Tier.HOOTL for e in history)


class TestOotlBypassPendingHitl:
    def test_ootl_bypass_pending_hitl(
        self, classifier, trigger, engine, audit_logger, identity
    ):
        """
        Emergency during HITL → HOOTL override bypasses pending HITL.
        """
        operation_id = "op-intbypass-001"
        ctx = make_context(
            operation_id,
            OperationType.REFACTORING,
            RiskLevel.ELEVATED,
            OperationScope.SINGLE_AGENT,
            identity,
        )
        operation = make_operation(operation_id)

        # Start as HITL
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HITL

        result = trigger.evaluate_triggers(operation_id, ctx, decision)
        trigger.fire_workflow(result.decision, operation, ctx)

        queue = trigger.get_hitl_queue()
        assert operation_id in queue

        # Emergency override triggers HOOTL protocol (bypass HITL)
        override_result = engine.escalate(
            operation_id=operation_id,
            from_tier=Tier.HITL,
            to_tier=Tier.HOOTL,
            reason="Emergency override: security incident during HITL pending approval",
            acted_by="emergency-responder@example.com",
        )
        assert override_result.to_tier == Tier.HOOTL
        assert "Emergency" in override_result.trigger_reason or "emergency" in override_result.trigger_reason.lower()

        # Log and verify
        audit_logger.log_escalation(override_result)
        entries = audit_logger.get_operation_log(operation_id)
        escalation_entries = [e for e in entries if "ESCALATION" in e.decision]
        assert len(escalation_entries) >= 1


class TestEndToEndWithOverride:
    def test_end_to_end_with_tier_override(
        self, classifier, trigger, audit_logger, override_manager, admin_identity
    ):
        """
        Full flow with tier override by authorized admin.
        """
        operation_id = "op-int-override-001"
        ctx = make_context(
            operation_id,
            OperationType.CODE_GENERATION,
            RiskLevel.ROUTINE,
            OperationScope.SINGLE_AGENT,
            admin_identity,
        )
        operation = make_operation(operation_id)

        # Classify → HOTL
        decision = classifier.classify_operation(ctx)
        assert decision.tier == Tier.HOTL

        # Admin overrides to HITL
        override_result = override_manager.override_tier(
            operation_id=operation_id,
            new_tier=Tier.HITL,
            justification="Operation touches production-adjacent system",
            role=admin_identity.role or __import__(
                "implement.governance.enums", fromlist=["AuthorizedRole"]
            ).AuthorizedRole.ADMIN,
            actor_identity=admin_identity.identity_id,
            original_tier=Tier.HOTL,
        )
        assert override_result.success is True
        assert override_result.new_tier == Tier.HITL

        # Trigger with overridden tier
        from implement.governance.models import TierDecision
        overridden_decision = TierDecision(
            operation_id=operation_id,
            tier=Tier.HITL,
            classification_reason=decision.classification_reason + " [OVERRIDDEN]",
            timestamp=datetime.utcnow(),
            confidence=decision.confidence,
        )
        result = trigger.evaluate_triggers(operation_id, ctx, overridden_decision)
        assert result.decision == GovernanceDecision.PENDING_APPROVAL

        # Log
        audit_logger.log_classification(operation_id, overridden_decision, ctx)
        override_records = override_manager.get_override_history(operation_id=operation_id)
        assert len(override_records) == 1


class TestEscalationDepthEndToEnd:
    def test_escalation_depth_tracking(
        self, classifier, engine, audit_logger, identity
    ):
        """
        Escalation depth is tracked correctly across multiple escalations.
        """
        operation_id = "op-intdepth-001"
        ctx = make_context(
            operation_id,
            OperationType.CODE_GENERATION,
            RiskLevel.ROUTINE,
            OperationScope.SINGLE_AGENT,
            identity,
        )

        # Escalate: HOTL → HITL
        e1 = engine.escalate(
            operation_id=operation_id,
            from_tier=Tier.HOTL,
            to_tier=Tier.HITL,
            reason="First escalation",
            acted_by="system",
        )
        audit_logger.log_escalation(e1)
        assert engine.get_escalation_depth(operation_id) == 1

        # Escalate: HITL → HOOTL
        e2 = engine.escalate(
            operation_id=operation_id,
            from_tier=Tier.HITL,
            to_tier=Tier.HOOTL,
            reason="Second escalation",
            acted_by="system",
        )
        audit_logger.log_escalation(e2)
        assert engine.get_escalation_depth(operation_id) == 2

        # Verify history
        history = engine.get_escalation_history(operation_id)
        assert len(history) == 2
        assert history[0].to_tier == Tier.HITL
        assert history[1].to_tier == Tier.HOOTL
