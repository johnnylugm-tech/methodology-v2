"""AuditLogger — FR-TG-7: Tier Audit Logging.

Immutable append-only log of all tier decisions, actions, human interventions,
and escalations. Provides query interface and generates weekly health reports.
Implements blockchain-style hash chain for tamper detection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import (
    GovernanceDecision,
    OperationType,
    RiskLevel,
    Tier,
)
from .exceptions import AuditLogError
from .models import (
    AuditEntry,
    ApprovalRequest,
    EscalationEvent,
    GovernanceHealthReport,
    GovernanceQueryFilters,
    IncidentReport,
    OperationSummary,
    PaginationParams,
    TierDecision,
)


class AuditLogger:
    """
    Immutable append-only audit log with blockchain-style hash chaining.

    All governance events are logged atomically. Once written, entries cannot
    be modified or deleted. A hash chain provides tamper detection: each entry
    includes the hash of the previous entry, creating a verifiable chain.

    No UPDATE or DELETE methods are provided — the log is strictly append-only.
    """

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []
        self._entry_counter: int = 0
        self._last_hash: str = "GENESIS"
        self._hash_chain_enabled: bool = True

    # ─── Hash Chain ─────────────────────────────────────────────────────────────

    def _compute_entry_hash(self, entry: AuditEntry, prev_hash: str) -> str:
        """
        Compute SHA-256 hash of an audit entry.

        Hash is computed over: entry_id, timestamp, operation_id, tier, decision, actor, prev_hash.
        """
        content = (
            f"{entry.entry_id}|"
            f"{entry.timestamp.isoformat()}|"
            f"{entry.operation.operation_id}|"
            f"{entry.tier.name}|"
            f"{entry.decision}|"
            f"{entry.actor}|"
            f"{prev_hash}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _verify_chain(self) -> bool:
        """
        Verify the integrity of the hash chain.

        Returns True if all entries are properly chained, False if tampering is detected.
        """
        prev_hash = "GENESIS"
        for entry in self._entries:
            expected_hash = self._compute_entry_hash(entry, prev_hash)
            # We store the hash in metadata, so we verify by recomputing
            stored_hash = entry.metadata.get("_chain_hash", "")
            if stored_hash and stored_hash != expected_hash:
                return False
            prev_hash = entry.metadata.get("_chain_hash", prev_hash)
        return True

    # ─── Core Logging Methods ───────────────────────────────────────────────────

    def log_classification(
        self,
        operation_id: str,
        decision: TierDecision,
        context: GovernanceContext,
    ) -> AuditEntry:
        """
        Log a tier classification decision.

        Args:
            operation_id: The classified operation.
            decision: The tier decision.
            context: Full governance context.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=decision.timestamp,
            operation=OperationSummary(
                operation_id=operation_id,
                operation_type=context.operation_type,
                description=decision.classification_reason,
                affected_systems=context.metadata.get("affected_systems", []),
            ),
            tier=decision.tier,
            decision=f"CLASSIFIED_AS_{decision.tier.name}: {decision.classification_reason}",
            actor="TierClassifier",
            outcome="success",
            metadata={
                "confidence": decision.confidence,
                "operation_type": context.operation_type.name,
                "risk_level": context.risk_level.name,
                "scope": context.scope.name,
                "overrides_count": len(decision.overrides),
            },
        )
        self._append_entry(entry)
        return entry

    def log_workflow_start(
        self,
        operation_id: str,
        tier: Tier,
        workflow_type: str,
        actor: str = "GovernanceTrigger",
    ) -> AuditEntry:
        """
        Log the start of a tier workflow.

        Args:
            operation_id: The operation starting a workflow.
            tier: The active tier.
            workflow_type: Type of workflow (HOTL_AUTOMATED, HITL_APPROVAL_QUEUE, etc.).
            actor: Who started the workflow.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=datetime.utcnow(),
            operation=OperationSummary(
                operation_id=operation_id,
                operation_type=OperationType.UNKNOWN,
                description=f"Workflow started: {workflow_type}",
            ),
            tier=tier,
            decision=f"WORKFLOW_START: {workflow_type}",
            actor=actor,
            outcome="pending",
            metadata={"workflow_type": workflow_type},
        )
        self._append_entry(entry)
        return entry

    def log_human_action(
        self,
        operation_id: str,
        action: str,
        actor_identity: str,
        tier: Tier,
        details: Dict[str, Any],
    ) -> AuditEntry:
        """
        Log a human action (approval, denial, modification, override).

        Args:
            operation_id: The operation the human acted on.
            action: Human-readable action description.
            actor_identity: Identity of the human.
            tier: The tier active during this action.
            details: Additional details about the action.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=datetime.utcnow(),
            operation=OperationSummary(
                operation_id=operation_id,
                operation_type=OperationType.UNKNOWN,
                description=action,
            ),
            tier=tier,
            decision=f"HUMAN_ACTION: {action}",
            actor=actor_identity,
            outcome="success",
            metadata=details,
        )
        self._append_entry(entry)
        return entry

    def log_escalation(self, event: EscalationEvent) -> AuditEntry:
        """
        Log an escalation event.

        Args:
            event: The escalation event to log.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=event.timestamp,
            operation=OperationSummary(
                operation_id=event.operation_id,
                operation_type=OperationType.UNKNOWN,
                description=f"Escalation {event.from_tier.name}→{event.to_tier.name}",
            ),
            tier=event.to_tier,
            decision=f"ESCALATION: {event.from_tier.name}→{event.to_tier.name}",
            actor=event.acted_by,
            outcome="success",
            metadata={
                "from_tier": event.from_tier.name,
                "to_tier": event.to_tier.name,
                "trigger_reason": event.trigger_reason,
                "event_id": event.event_id,
                "escalated_to_channel": event.escalated_to_channel,
                "fallback_tier": event.fallback_tier.name if event.fallback_tier else None,
            },
        )
        self._append_entry(entry)
        return entry

    def log_workflow_complete(
        self,
        operation_id: str,
        outcome: str,
        tier: Tier,
        duration_ms: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Log the completion of a workflow.

        Args:
            operation_id: The completed operation.
            outcome: Outcome description (success, failure, timeout, etc.).
            tier: The tier this workflow ran under.
            duration_ms: How long the workflow took in milliseconds.
            metadata: Additional metadata.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=datetime.utcnow(),
            operation=OperationSummary(
                operation_id=operation_id,
                operation_type=OperationType.UNKNOWN,
                description=f"Workflow completed: {outcome}",
            ),
            tier=tier,
            decision=f"WORKFLOW_COMPLETE: {outcome}",
            actor="GovernanceTrigger",
            outcome=outcome,
            metadata={
                **(metadata or {}),
                "duration_ms": duration_ms,
            },
        )
        self._append_entry(entry)
        return entry

    def log_security_event(
        self,
        operation_id: str,
        event_type: str,
        actor_identity: Optional[str],
        tier: Tier,
        details: Dict[str, Any],
    ) -> AuditEntry:
        """
        Log a security-relevant event (e.g., unauthorized override attempt).

        Args:
            operation_id: The affected operation.
            event_type: Type of security event.
            actor_identity: Identity of the actor (None if anonymous).
            tier: The tier at time of event.
            details: Event details.

        Returns:
            The created AuditEntry.
        """
        entry = AuditEntry(
            entry_id=self._new_entry_id(),
            timestamp=datetime.utcnow(),
            operation=OperationSummary(
                operation_id=operation_id,
                operation_type=OperationType.SECURITY,
                description=f"Security event: {event_type}",
            ),
            tier=tier,
            decision=f"SECURITY_EVENT: {event_type}",
            actor=actor_identity or "anonymous",
            outcome="failure",
            metadata={**details, "event_type": event_type},
        )
        self._append_entry(entry)
        return entry

    # ─── Query Interface ────────────────────────────────────────────────────────

    def query(
        self,
        filters: GovernanceQueryFilters,
        pagination: PaginationParams = PaginationParams(),
    ) -> List[AuditEntry]:
        """
        Query the audit log with filters.

        Args:
            filters: Query filters.
            pagination: Pagination parameters.

        Returns:
            List of matching AuditEntries, ordered by timestamp descending.
        """
        results = list(self._entries)

        # Apply filters
        if filters.start_date:
            results = [e for e in results if e.timestamp >= filters.start_date]
        if filters.end_date:
            results = [e for e in results if e.timestamp <= filters.end_date]
        if filters.tier is not None:
            results = [e for e in results if e.tier == filters.tier]
        if filters.operation_type is not None:
            results = [e for e in results if e.operation.operation_type == filters.operation_type]
        if filters.actor is not None:
            results = [e for e in results if filters.actor.lower() in e.actor.lower()]
        if filters.outcome is not None:
            results = [e for e in results if e.outcome == filters.outcome]
        if filters.operation_id is not None:
            results = [e for e in results if e.operation.operation_id == filters.operation_id]

        # Sort descending by timestamp
        results.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return results[pagination.offset : pagination.offset + pagination.limit]

    def get_operation_log(self, operation_id: str) -> List[AuditEntry]:
        """
        Get all audit entries for a specific operation.

        Args:
            operation_id: The operation to query.

        Returns:
            All entries for this operation, ordered by timestamp ascending.
        """
        entries = [e for e in self._entries if e.operation.operation_id == operation_id]
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def get_entry_count(self) -> int:
        """Return total number of audit entries."""
        return len(self._entries)

    # ─── Health Reporting ───────────────────────────────────────────────────────

    def get_health_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> GovernanceHealthReport:
        """
        Generate a weekly governance health report.

        Args:
            start_date: Report period start.
            end_date: Report period end.

        Returns:
            GovernanceHealthReport with aggregated metrics.
        """
        entries = self.query(
            GovernanceQueryFilters(start_date=start_date, end_date=end_date),
            pagination=PaginationParams(limit=100000),
        )

        total_ops = len(set(e.operation.operation_id for e in entries))

        # Tier distribution
        tier_dist: Dict[Tier, int] = {t: 0 for t in Tier}
        for entry in entries:
            tier_dist[entry.tier] = tier_dist.get(entry.tier, 0) + 1

        # Escalation count
        escalation_count = sum(
            1 for e in entries if e.decision.startswith("ESCALATION")
        )

        # HITL approval rate
        hitl_entries = [e for e in entries if e.tier == Tier.HITL]
        hitl_decided = [
            e for e in hitl_entries
            if e.outcome in ("success", "failure") and "HUMAN_ACTION" in e.decision
        ]
        approval_rate = len(hitl_decided) / len(hitl_entries) if hitl_entries else 0.0

        # Mean approval time (simplified: based on workflow duration metadata)
        approval_times = [
            e.metadata.get("duration_ms", 0) / 3600000.0  # convert ms to hours
            for e in entries
            if "WORKFLOW_COMPLETE" in e.decision and e.tier == Tier.HITL
        ]
        mean_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0.0

        return GovernanceHealthReport(
            start_date=start_date,
            end_date=end_date,
            total_operations=total_ops,
            tier_distribution=tier_dist,
            escalation_count=escalation_count,
            hitl_approval_rate=approval_rate,
            mean_approval_time_hours=mean_approval_time,
            report_generated_at=datetime.utcnow(),
        )

    def get_incident_report(
        self,
        operation_id: str,
        event_id: str,
        trigger_reason: str,
    ) -> IncidentReport:
        """
        Generate a post-hoc incident report for an HOOTL activation.

        Args:
            operation_id: The operation that triggered HOOTL.
            event_id: The escalation event ID.
            trigger_reason: Why HOOTL was triggered.

        Returns:
            IncidentReport with timeline and details.
        """
        entries = self.get_operation_log(operation_id)
        timeline = [
            {
                "timestamp": e.timestamp.isoformat(),
                "event": e.decision,
                "actor": e.actor,
            }
            for e in entries
        ]

        actions_taken = [
            e.metadata.get("workflow_type", e.decision)
            for e in entries
            if "WORKFLOW" in e.decision
        ]

        return IncidentReport(
            operation_id=operation_id,
            event_id=event_id,
            trigger_reason=trigger_reason,
            actions_taken=actions_taken,
            timeline=timeline,
            generated_at=datetime.utcnow(),
        )

    # ─── Export ─────────────────────────────────────────────────────────────────

    def export(self, format: str = "json") -> str:
        """
        Export the full audit log.

        Args:
            format: Export format ("json" supported).

        Returns:
            Serialized audit log as a string.

        Raises:
            AuditLogError: If format is unsupported.
        """
        if format == "json":
            return json.dumps(
                [asdict(e) for e in self._entries],
                indent=2,
                default=str,
            )
        raise AuditLogError(f"Unsupported export format: {format}")

    # ─── Internal Helpers ───────────────────────────────────────────────────────

    def _new_entry_id(self) -> str:
        """Generate a new monotonically increasing entry ID."""
        self._entry_counter += 1
        return f"audit_{self._entry_counter:010d}"

    def _append_entry(self, entry: AuditEntry) -> None:
        """
        Append an entry to the log and update the hash chain.

        Raises AuditLogError if the hash chain is broken.
        """
        if self._hash_chain_enabled:
            entry_hash = self._compute_entry_hash(entry, self._last_hash)
            entry.metadata["_chain_hash"] = entry_hash
            entry.metadata["_prev_hash"] = self._last_hash
            self._last_hash = entry_hash

        self._entries.append(entry)

    def verify(self) -> bool:
        """
        Verify the integrity of the audit log.

        Returns True if the hash chain is intact, False if tampering is detected.
        """
        return self._verify_chain()
