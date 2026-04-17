"""GovernanceTrigger — FR-TG-2: Governance Trigger System.

Evaluates trigger conditions for all three tiers and fires tier-appropriate workflows.
Continuously monitors HOTL operations for mid-execution boundary crossings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .enums import (
    DEFAULT_HITL_SLA_HOURS,
    GovernanceDecision,
    RiskLevel,
    Tier,
)
from .exceptions import GovernanceError
from .models import (
    ApprovalRequest,
    GovernanceContext,
    OperationSummary,
    TierDecision,
)


# ─── Trigger Result ────────────────────────────────────────────────────────────

@dataclass
class TriggerResult:
    """Result of evaluating governance triggers."""
    operation_id: str
    decision: GovernanceDecision
    tier: Tier
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringResult:
    """Result of monitoring an operation's execution."""
    operation_id: str
    anomaly_detected: bool
    anomaly_type: Optional[str] = None
    severity: Optional[RiskLevel] = None
    recommended_action: Optional[str] = None


@dataclass
class WorkflowHandle:
    """Handle to an active workflow."""
    workflow_id: str
    operation_id: str
    tier: Tier
    workflow_type: str
    started_at: datetime
    status: str = "active"


@dataclass
class EmergencyProtocolHandle:
    """Handle to an active emergency protocol."""
    protocol_id: str
    operation_id: str
    activated_at: datetime
    responders_notified: List[str] = field(default_factory=list)
    actions_taken: List[str] = field(default_factory=list)


# ─── HITL Queue Entry ──────────────────────────────────────────────────────────

@dataclass
class HITLQueueEntry:
    """Internal tracking for HITL approval queue."""
    request: ApprovalRequest
    workflow_handle: WorkflowHandle
    sla_reminders_sent: List[datetime] = field(default_factory=list)


# ─── Static Trigger Rules ─────────────────────────────────────────────────────

def _evaluate_hotl_triggers(context: GovernanceContext, decision: TierDecision) -> Optional[TriggerResult]:
    """
    HOTL triggers: operation is within defined safe parameters — auto-approved
    unless an exception is detected.
    """
    # Check data classification in metadata
    data_class = context.metadata.get("data_classification", "public")
    if data_classification_is_restricted(data_class):
        return TriggerResult(
            operation_id=context.operation_id,
            decision=GovernanceDecision.ESCALATE,
            tier=Tier.HITL,
            reason=f"Restricted data classification '{data_class}' escalates to HITL",
        )

    # Check for anomaly flag in metadata
    if context.metadata.get("anomaly_detected"):
        return TriggerResult(
            operation_id=context.operation_id,
            decision=GovernanceDecision.ESCALATE,
            tier=Tier.HITL,
            reason="Anomaly detected during execution, escalating to HITL",
        )

    return TriggerResult(
        operation_id=context.operation_id,
        decision=GovernanceDecision.AUTO_APPROVE,
        tier=Tier.HOTL,
        reason="Operation within defined HOTL parameters",
    )


def _evaluate_hitl_triggers(context: GovernanceContext, decision: TierDecision) -> TriggerResult:
    """
    HITL triggers: operations crossing defined boundaries require explicit approval.
    """
    # Scope-based escalation
    scope_escalation = context.metadata.get("scope_crossed", False)
    if scope_escalation:
        return TriggerResult(
            operation_id=context.operation_id,
            decision=GovernanceDecision.PENDING_APPROVAL,
            tier=Tier.HITL,
            reason="Operation scope crossed during execution — requires HITL approval",
        )

    # Risk elevation mid-execution
    if context.metadata.get("risk_elevated"):
        return TriggerResult(
            operation_id=context.operation_id,
            decision=GovernanceDecision.PENDING_APPROVAL,
            tier=Tier.HITL,
            reason="Risk level elevated during execution — requires HITL approval",
        )

    return TriggerResult(
        operation_id=context.operation_id,
        decision=GovernanceDecision.PENDING_APPROVAL,
        tier=Tier.HITL,
        reason="Operation requires explicit human approval per policy",
    )


def _evaluate_hootl_triggers(context: GovernanceContext, decision: TierDecision) -> TriggerResult:
    """
    HOOTL triggers: extreme scenarios trigger emergency protocol immediately.
    """
    return TriggerResult(
        operation_id=context.operation_id,
        decision=GovernanceDecision.EMERGENCY_TRIGGER,
        tier=Tier.HOOTL,
        reason="Emergency condition detected — triggering HOOTL protocol",
        metadata={"auto_triggered": True},
    )


def data_classification_is_restricted(classification: str) -> bool:
    """Check if a data classification level is considered restricted."""
    restricted = {"restricted", "confidential", "top_secret", "pii", "phi"}
    return classification.lower() in restricted


# ─── GovernanceTrigger ────────────────────────────────────────────────────────

class GovernanceTrigger:
    """
    Evaluates trigger conditions for all three tiers and fires workflows.

    The trigger engine is the central dispatcher: it receives a classified operation
    and determines which governance workflow to activate (HOTL, HITL, or HOOTL).

    It also provides continuous monitoring for HOTL operations, detecting
    mid-execution boundary crossings that may require escalation.
    """

    def __init__(self) -> None:
        self._active_workflows: Dict[str, WorkflowHandle] = {}
        self._hitl_queue: Dict[str, HITLQueueEntry] = {}
        self._hootl_active: Dict[str, EmergencyProtocolHandle] = {}
        self._trigger_metrics: Dict[GovernanceDecision, int] = {
            d: 0 for d in GovernanceDecision
        }

    def evaluate_triggers(
        self,
        operation_id: str,
        context: GovernanceContext,
        tier: TierDecision,
    ) -> TriggerResult:
        """
        Evaluate which trigger conditions are active for a classified operation.

        Args:
            operation_id: The operation being evaluated.
            context: Full governance context.
            tier: The tier decision from TierClassifier.

        Returns:
            TriggerResult with the governance decision and reason.
        """
        result: Optional[TriggerResult] = None

        if tier.tier == Tier.HOTL:
            result = _evaluate_hotl_triggers(context, tier)
        elif tier.tier == Tier.HITL:
            result = _evaluate_hitl_triggers(context, tier)
        elif tier.tier == Tier.HOOTL:
            result = _evaluate_hootl_triggers(context, tier)
        else:
            result = TriggerResult(
                operation_id=operation_id,
                decision=GovernanceDecision.BLOCK,
                tier=tier.tier,
                reason="Unknown tier, blocking operation",
            )

        self._trigger_metrics[result.decision] = (
            self._trigger_metrics.get(result.decision, 0) + 1
        )
        return result

    def monitor_execution(
        self,
        operation_id: str,
        execution_context: Dict[str, Any],
    ) -> MonitoringResult:
        """
        Monitor a running operation for mid-execution anomalies.

        Used for HOTL operations to detect boundary crossings that would
        require escalation to HITL or HOOTL.

        Args:
            operation_id: The operation being monitored.
            execution_context: Current execution state and metrics.

        Returns:
            MonitoringResult indicating whether an anomaly was detected.
        """
        anomaly_detected = False
        anomaly_type: Optional[str] = None
        severity: Optional[RiskLevel] = None
        recommended_action: Optional[str] = None

        # Check for scope creep
        if execution_context.get("scope_crossed"):
            anomaly_detected = True
            anomaly_type = "scope_creep"
            severity = RiskLevel.ELEVATED
            recommended_action = "ESCALATE_TO_HITL"

        # Check for risk elevation
        if execution_context.get("risk_elevated"):
            anomaly_detected = True
            anomaly_type = "risk_elevation"
            severity = RiskLevel.CRITICAL
            recommended_action = "ESCALATE_TO_HOOTL"

        # Check for security anomaly
        if execution_context.get("security_anomaly"):
            anomaly_detected = True
            anomaly_type = "security_anomaly"
            severity = RiskLevel.CRITICAL
            recommended_action = "ESCALATE_TO_HOOTL"

        # Check for cascade failure signal
        if execution_context.get("cascade_failure_signal"):
            anomaly_detected = True
            anomaly_type = "cascade_failure"
            severity = RiskLevel.CRITICAL
            recommended_action = "TRIGGER_HOOTL_PROTOCOL"

        return MonitoringResult(
            operation_id=operation_id,
            anomaly_detected=anomaly_detected,
            anomaly_type=anomaly_type,
            severity=severity,
            recommended_action=recommended_action,
        )

    def fire_workflow(
        self,
        decision: GovernanceDecision,
        operation: OperationSummary,
        context: GovernanceContext,
    ) -> WorkflowHandle:
        """
        Fire the appropriate workflow based on the governance decision.

        Args:
            decision: The trigger decision.
            operation: Summary of the operation.
            context: Full governance context.

        Returns:
            WorkflowHandle for the activated workflow.

        Raises:
            GovernanceError: If the workflow type is unrecognized.
        """
        workflow_id = f"wf_{operation.operation_id}"

        if decision == GovernanceDecision.AUTO_APPROVE:
            handle = self._fire_hotl_workflow(operation, context)
        elif decision == GovernanceDecision.PENDING_APPROVAL:
            handle = self._fire_hitl_workflow(operation, context)
        elif decision == GovernanceDecision.EMERGENCY_TRIGGER:
            handle = self._fire_hootl_protocol(operation, context)
        elif decision == GovernanceDecision.BLOCK:
            handle = self._fire_block_workflow(operation, context)
        else:
            raise GovernanceError(f"Unrecognized governance decision: {decision}")

        return handle

    def _fire_hotl_workflow(
        self,
        operation: OperationSummary,
        context: GovernanceContext,
    ) -> WorkflowHandle:
        """Fire the HOTL (automated) workflow."""
        workflow_id = f"hotl_{operation.operation_id}"
        handle = WorkflowHandle(
            workflow_id=workflow_id,
            operation_id=operation.operation_id,
            tier=Tier.HOTL,
            workflow_type="HOTL_AUTOMATED",
            started_at=datetime.utcnow(),
        )
        self._active_workflows[operation.operation_id] = handle
        return handle

    def _fire_hitl_workflow(
        self,
        operation: OperationSummary,
        context: GovernanceContext,
        sla_hours: int = DEFAULT_HITL_SLA_HOURS,
    ) -> WorkflowHandle:
        """
        Fire the HITL (approval-required) workflow and create an ApprovalRequest.

        The request is queued and the approver notified. SLA timer starts now.
        """
        from .enums import ApprovalStatus

        request_id = f"hitl_{operation.operation_id}"
        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours)

        approval_request = ApprovalRequest(
            request_id=request_id,
            operation_id=operation.operation_id,
            operation=operation,
            requested_tier=Tier.HITL,
            context=context,
            sla_deadline=sla_deadline,
            status=ApprovalStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        workflow_id = f"hitl_{operation.operation_id}"
        handle = WorkflowHandle(
            workflow_id=workflow_id,
            operation_id=operation.operation_id,
            tier=Tier.HITL,
            workflow_type="HITL_APPROVAL_QUEUE",
            started_at=datetime.utcnow(),
        )

        self._active_workflows[operation.operation_id] = handle
        self._hitl_queue[operation.operation_id] = HITLQueueEntry(
            request=approval_request,
            workflow_handle=handle,
        )

        return handle

    def _fire_hootl_protocol(
        self,
        operation: OperationSummary,
        context: GovernanceContext,
    ) -> EmergencyProtocolHandle:
        """Fire the HOOTL (emergency) protocol — no pre-approval, act immediately."""
        protocol_id = f"hootl_{operation.operation_id}"
        handle = EmergencyProtocolHandle(
            protocol_id=protocol_id,
            operation_id=operation.operation_id,
            activated_at=datetime.utcnow(),
        )
        self._hootl_active[operation.operation_id] = handle
        return handle

    def _fire_block_workflow(
        self,
        operation: OperationSummary,
        context: GovernanceContext,
    ) -> WorkflowHandle:
        """Fire a blocking workflow (operation denied/blocked)."""
        workflow_id = f"block_{operation.operation_id}"
        return WorkflowHandle(
            workflow_id=workflow_id,
            operation_id=operation.operation_id,
            tier=Tier.HOOTL,
            workflow_type="BLOCKED",
            started_at=datetime.utcnow(),
            status="blocked",
        )

    def get_active_workflows(self) -> Dict[str, WorkflowHandle]:
        """Return all currently active workflows."""
        return dict(self._active_workflows)

    def get_hitl_queue(self) -> Dict[str, HITLQueueEntry]:
        """Return the current HITL approval queue."""
        return dict(self._hitl_queue)

    def get_hootl_active(self) -> Dict[str, EmergencyProtocolHandle]:
        """Return all active HOOTL protocols."""
        return dict(self._hootl_active)

    def get_trigger_metrics(self) -> Dict[GovernanceDecision, int]:
        """Return trigger decision metrics."""
        return dict(self._trigger_metrics)

    def complete_workflow(self, operation_id: str) -> None:
        """Mark a workflow as completed and remove from active tracking."""
        self._active_workflows.pop(operation_id, None)
        self._hitl_queue.pop(operation_id, None)
        self._hootl_active.pop(operation_id, None)
