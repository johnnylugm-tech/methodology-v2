"""Tests for GovernanceTrigger."""

import pytest
from datetime import datetime, timedelta
from implement.governance.enums import (
    Tier,
    GovernanceDecision,
    RiskLevel,
    OperationType,
    OperationScope,
)
from implement.governance.models import (
    GovernanceContext,
    Identity,
    OperationSummary,
    TierDecision,
)
from implement.governance.governance_trigger import GovernanceTrigger


@pytest.fixture
def trigger():
    return GovernanceTrigger()


@pytest.fixture
def identity():
    return Identity(identity_id="id-001", name="Test User")


@pytest.fixture
def hotl_context(identity):
    """Context that will be classified as HOTL."""
    return GovernanceContext(
        operation_id="op-hotl-001",
        operation_type=OperationType.CODE_GENERATION,
        risk_level=RiskLevel.ROUTINE,
        scope=OperationScope.SINGLE_AGENT,
        requester_identity=identity,
        metadata={"data_classification": "public"},
    )


@pytest.fixture
def hitl_context(identity):
    """Context that will be classified as HITL."""
    return GovernanceContext(
        operation_id="op-hitl-001",
        operation_type=OperationType.REFACTORING,
        risk_level=RiskLevel.ELEVATED,
        scope=OperationScope.SINGLE_AGENT,
        requester_identity=identity,
    )


@pytest.fixture
def hootl_context(identity):
    """Context that will be classified as HOOTL."""
    return GovernanceContext(
        operation_id="op-hootl-001",
        operation_type=OperationType.EMERGENCY,
        risk_level=RiskLevel.CRITICAL,
        scope=OperationScope.SINGLE_AGENT,
        requester_identity=identity,
    )


@pytest.fixture
def hotl_decision():
    return TierDecision(
        operation_id="op-hotl-001",
        tier=Tier.HOTL,
        classification_reason="Routine operation",
        timestamp=datetime.utcnow(),
        confidence=0.95,
    )


@pytest.fixture
def hitl_decision():
    return TierDecision(
        operation_id="op-hitl-001",
        tier=Tier.HITL,
        classification_reason="Elevated risk operation",
        timestamp=datetime.utcnow(),
        confidence=0.95,
    )


@pytest.fixture
def hootl_decision():
    return TierDecision(
        operation_id="op-hootl-001",
        tier=Tier.HOOTL,
        classification_reason="Emergency operation",
        timestamp=datetime.utcnow(),
        confidence=0.95,
    )


class TestHotlTrigger:
    def test_hotl_trigger_fires_auto_approve(self, trigger, hotl_context, hotl_decision):
        """HOTL tier → AUTO_APPROVE decision."""
        result = trigger.evaluate_triggers(
            operation_id="op-hotl-001",
            context=hotl_context,
            tier=hotl_decision,
        )
        assert result.decision == GovernanceDecision.AUTO_APPROVE, (
            f"Expected AUTO_APPROVE, got {result.decision}"
        )
        assert result.tier == Tier.HOTL


class TestHitlTrigger:
    def test_hitl_trigger_fires_pending_approval(self, trigger, hitl_context, hitl_decision):
        """HITL tier → PENDING_APPROVAL decision."""
        result = trigger.evaluate_triggers(
            operation_id="op-hitl-001",
            context=hitl_context,
            tier=hitl_decision,
        )
        assert result.decision == GovernanceDecision.PENDING_APPROVAL, (
            f"Expected PENDING_APPROVAL, got {result.decision}"
        )
        assert result.tier == Tier.HITL


class TestHootlTrigger:
    def test_hootl_trigger_fires_emergency(self, trigger, hootl_context, hootl_decision):
        """HOOTL tier → EMERGENCY_TRIGGER decision."""
        result = trigger.evaluate_triggers(
            operation_id="op-hootl-001",
            context=hootl_context,
            tier=hootl_decision,
        )
        assert result.decision == GovernanceDecision.EMERGENCY_TRIGGER, (
            f"Expected EMERGENCY_TRIGGER, got {result.decision}"
        )
        assert result.tier == Tier.HOOTL


class TestBoundaryCrossingEscalates:
    def test_boundary_crossing_escalates(self, trigger, identity):
        """Mid-execution boundary breach triggers ESCALATE via restricted data classification.

        The trigger engine evaluates boundary crossing via the HOTL path:
        restricted data classification causes ESCALATE to HITL tier.
        """
        ctx = GovernanceContext(
            operation_id="op-scope-001",
            operation_type=OperationType.CODE_GENERATION,
            risk_level=RiskLevel.ROUTINE,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=identity,
            metadata={"scope_crossed": True, "data_classification": "restricted"},
        )
        decision = TierDecision(
            operation_id="op-scope-001",
            tier=Tier.HOTL,
            classification_reason="Routine",
            timestamp=datetime.utcnow(),
            confidence=0.95,
        )
        result = trigger.evaluate_triggers(
            operation_id="op-scope-001",
            context=ctx,
            tier=decision,
        )
        # restricted data_classification triggers ESCALATE from HOTL
        assert result.decision == GovernanceDecision.ESCALATE, (
            f"Expected ESCALATE for boundary/data breach, got {result.decision}"
        )


class TestMonitorExecution:
    def test_monitor_detects_scope_creep(self, trigger):
        """monitor_execution detects scope_crossed anomaly."""
        result = trigger.monitor_execution(
            operation_id="op-001",
            execution_context={"scope_crossed": True},
        )
        assert result.anomaly_detected is True
        assert result.anomaly_type == "scope_creep"
        assert result.recommended_action == "ESCALATE_TO_HITL"

    def test_monitor_detects_risk_elevation(self, trigger):
        """monitor_execution detects risk_elevated anomaly."""
        result = trigger.monitor_execution(
            operation_id="op-002",
            execution_context={"risk_elevated": True},
        )
        assert result.anomaly_detected is True
        assert result.anomaly_type == "risk_elevation"
        assert result.severity == RiskLevel.CRITICAL

    def test_monitor_detects_security_anomaly(self, trigger):
        """monitor_execution detects security_anomaly."""
        result = trigger.monitor_execution(
            operation_id="op-003",
            execution_context={"security_anomaly": True},
        )
        assert result.anomaly_detected is True
        assert result.anomaly_type == "security_anomaly"
        assert result.severity == RiskLevel.CRITICAL

    def test_monitor_clean_execution(self, trigger):
        """monitor_execution returns no anomaly for clean execution."""
        result = trigger.monitor_execution(
            operation_id="op-clean",
            execution_context={"status": "running"},
        )
        assert result.anomaly_detected is False


class TestFireWorkflow:
    def test_fire_hotl_workflow(self, trigger):
        """fire_workflow with AUTO_APPROVE creates HOTL workflow handle."""
        operation = OperationSummary(
            operation_id="op-wf-001",
            operation_type=OperationType.CODE_GENERATION,
            description="Test operation",
        )
        ctx = GovernanceContext(
            operation_id="op-wf-001",
            operation_type=OperationType.CODE_GENERATION,
            risk_level=RiskLevel.ROUTINE,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=Identity(identity_id="id", name="Test"),
        )
        handle = trigger.fire_workflow(GovernanceDecision.AUTO_APPROVE, operation, ctx)
        assert handle.tier == Tier.HOTL
        assert handle.workflow_type == "HOTL_AUTOMATED"
        assert handle.status == "active"

    def test_fire_hitl_workflow(self, trigger):
        """fire_workflow with PENDING_APPROVAL creates HITL queue entry."""
        operation = OperationSummary(
            operation_id="op-wf-002",
            operation_type=OperationType.REFACTORING,
            description="Test operation",
        )
        ctx = GovernanceContext(
            operation_id="op-wf-002",
            operation_type=OperationType.REFACTORING,
            risk_level=RiskLevel.ELEVATED,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=Identity(identity_id="id", name="Test"),
        )
        handle = trigger.fire_workflow(GovernanceDecision.PENDING_APPROVAL, operation, ctx)
        assert handle.tier == Tier.HITL
        assert handle.workflow_type == "HITL_APPROVAL_QUEUE"

    def test_fire_hootl_protocol(self, trigger):
        """fire_workflow with EMERGENCY_TRIGGER creates emergency protocol handle."""
        operation = OperationSummary(
            operation_id="op-emerg-001",
            operation_type=OperationType.EMERGENCY,
            description="Emergency operation",
        )
        ctx = GovernanceContext(
            operation_id="op-emerg-001",
            operation_type=OperationType.EMERGENCY,
            risk_level=RiskLevel.CRITICAL,
            scope=OperationScope.SINGLE_AGENT,
            requester_identity=Identity(identity_id="id", name="Test"),
        )
        handle = trigger.fire_workflow(GovernanceDecision.EMERGENCY_TRIGGER, operation, ctx)
        # EmergencyProtocolHandle has protocol_id, operation_id, activated_at
        assert hasattr(handle, "protocol_id")
        assert handle.operation_id == "op-emerg-001"
        assert "op-emerg-001" in trigger.get_hootl_active()


class TestTriggerMetrics:
    def test_trigger_metrics_updated(self, trigger, hotl_context, hotl_decision):
        """Trigger metrics are incremented after evaluate_triggers."""
        trigger.evaluate_triggers("op-hotl-001", hotl_context, hotl_decision)
        metrics = trigger.get_trigger_metrics()
        assert metrics[GovernanceDecision.AUTO_APPROVE] >= 1
