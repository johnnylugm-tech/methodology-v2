"""EscalationEngine — FR-TG-3: Escalation Pathways.

Manages upward (HOTL→HITL→HOOTL) and downward (de-escalation) tier transitions.
Ensures escalation is never blocked; escalates to next available tier if channel is down.
Enforces maximum escalation depth (max 3) and detects circular escalation patterns.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .enums import (
    MAX_ESCALATION_DEPTH,
    Tier,
    TIER_ORDER,
)
from .exceptions import (
    CircularEscalationError,
    EscalationDepthExceeded,
    InvalidTierTransitionError,
)
from .models import (
    EscalationEvent,
    GovernanceContext,
    TierDecision,
)


@dataclass
class EscalationRecord:
    """Internal record tracking an escalation for a specific operation."""
    events: List[EscalationEvent] = field(default_factory=list)
    depth: int = 0


class EscalationEngine:
    """
    Manages tier transitions for operations.

    Upward escalation (HOTL→HITL→HOOTL) occurs when an operation crosses
    a boundary or anomaly is detected during execution. Escalation is
    always allowed and never blocked — if the target tier's channel is
    unavailable, the system escalates to the next available tier.

    Downward de-escalation is rare and requires explicit HITL sign-off.
    """

    def __init__(self) -> None:
        self._escalation_records: Dict[str, EscalationRecord] = {}
        self._escalation_queue: List[EscalationEvent] = []   # priority queue (simple list for now)
        self._circuit_breaker_state: Dict[Tier, bool] = {
            Tier.HOTL: False,
            Tier.HITL: False,
            Tier.HOOTL: False,
        }

    def escalate(
        self,
        operation_id: str,
        from_tier: Tier,
        to_tier: Tier,
        reason: str,
        acted_by: str = "system",
    ) -> EscalationEvent:
        """
        Escalate an operation to a higher oversight tier.

        Args:
            operation_id: The operation being escalated.
            from_tier: Current tier before escalation.
            to_tier: Target tier after escalation.
            reason: Why the escalation occurred.
            acted_by: Who/what triggered the escalation.

        Returns:
            EscalationEvent recording the transition.

        Raises:
            InvalidTierTransitionError: If the transition is not valid.
            EscalationDepthExceeded: If max escalation depth is exceeded.
            CircularEscalationError: If a circular escalation pattern is detected.
        """
        # Validate transition is upward
        if TIER_ORDER.get(to_tier, 0) <= TIER_ORDER.get(from_tier, 0):
            if TIER_ORDER.get(from_tier, 0) == TIER_ORDER.get(to_tier, 0):
                raise InvalidTierTransitionError(
                    f"Cannot escalate from {from_tier.name} to same tier {to_tier.name}"
                )
            raise InvalidTierTransitionError(
                f"Cannot de-escalate from {from_tier.name} to {to_tier.name} "
                f"without explicit HITL sign-off. Use deescalate() instead."
            )

        # Check circular escalation
        self._check_circular_pattern(operation_id)

        # Check depth
        record = self._escalation_records.get(operation_id)
        if record is not None:
            if record.depth >= MAX_ESCALATION_DEPTH:
                raise EscalationDepthExceeded(
                    f"Operation {operation_id} has exceeded max escalation depth "
                    f"({MAX_ESCALATION_DEPTH}). Escalating to HOOTL as final tier."
                )
            if record.depth >= MAX_ESCALATION_DEPTH - 1:
                # Auto-cap at HOOTL
                to_tier = Tier.HOOTL

        # Check if escalation channel is degraded
        escalated_to_channel = not self._circuit_breaker_state.get(to_tier, False)
        fallback_tier: Optional[Tier] = None
        if not escalated_to_channel:
            fallback_tier = self._get_next_available_tier(to_tier)
            if fallback_tier is None:
                fallback_tier = Tier.HOOTL

        event = EscalationEvent(
            event_id=str(uuid.uuid4()),
            operation_id=operation_id,
            from_tier=from_tier,
            to_tier=to_tier,
            trigger_reason=reason,
            timestamp=datetime.utcnow(),
            acted_by=acted_by,
            escalated_to_channel=escalated_to_channel,
            fallback_tier=fallback_tier,
        )

        # Store record
        if operation_id not in self._escalation_records:
            self._escalation_records[operation_id] = EscalationRecord()
        self._escalation_records[operation_id].events.append(event)
        self._escalation_records[operation_id].depth += 1

        # Add to queue
        self._escalation_queue.append(event)

        return event

    def deescalate(
        self,
        operation_id: str,
        from_tier: Tier,
        to_tier: Tier,
        justification: str,
        approver_identity: str,
    ) -> EscalationEvent:
        """
        De-escalate an operation to a lower tier.

        This is rare and requires explicit HITL sign-off from an authorized approver.

        Args:
            operation_id: The operation being de-escalated.
            from_tier: Current tier.
            to_tier: Target lower tier.
            justification: Required justification for the de-escalation.
            approver_identity: Identity of the approver authorizing de-escalation.

        Returns:
            EscalationEvent recording the transition.

        Raises:
            InvalidTierTransitionError: If the transition is not a valid downward move.
        """
        if TIER_ORDER.get(to_tier, 0) >= TIER_ORDER.get(from_tier, 0):
            raise InvalidTierTransitionError(
                f"Cannot de-escalate to same or higher tier. "
                f"from={from_tier.name}, to={to_tier.name}"
            )

        event = EscalationEvent(
            event_id=str(uuid.uuid4()),
            operation_id=operation_id,
            from_tier=from_tier,
            to_tier=to_tier,
            trigger_reason=f"DEESCALATION: {justification}",
            timestamp=datetime.utcnow(),
            acted_by=approver_identity,
            escalated_to_channel=True,
            fallback_tier=None,
        )

        if operation_id not in self._escalation_records:
            self._escalation_records[operation_id] = EscalationRecord()
        self._escalation_records[operation_id].events.append(event)
        # Note: de-escalation doesn't count toward depth limit

        self._escalation_queue.append(event)
        return event

    def get_escalation_depth(self, operation_id: str) -> int:
        """
        Return the current escalation depth for an operation.

        Args:
            operation_id: The operation to check.

        Returns:
            Number of escalation events (upward) for this operation.
        """
        record = self._escalation_records.get(operation_id)
        if record is None:
            return 0
        return record.depth

    def get_escalation_history(self, operation_id: str) -> List[EscalationEvent]:
        """
        Return the full escalation history for an operation.

        Args:
            operation_id: The operation to query.

        Returns:
            List of EscalationEvents, oldest first.
        """
        record = self._escalation_records.get(operation_id)
        if record is None:
            return []
        return list(record.events)

    def get_pending_escalations(
        self,
        tier: Optional[Tier] = None,
    ) -> List[EscalationEvent]:
        """
        Return pending escalation events, optionally filtered by target tier.

        Args:
            tier: Filter to escalations targeting this tier.

        Returns:
            List of matching EscalationEvents.
        """
        if tier is None:
            return list(self._escalation_queue)
        return [e for e in self._escalation_queue if e.to_tier == tier]

    def check_escalation_path(
        self,
        operation_id: str,
        from_tier: Tier,
        to_tier: Tier,
    ) -> bool:
        """
        Check if a tier transition is valid without raising.

        Args:
            operation_id: The operation being transitioned.
            from_tier: Current tier.
            to_tier: Desired target tier.

        Returns:
            True if the path is valid.

        Raises:
            CircularEscalationError: If a circular pattern is detected.
            EscalationDepthExceeded: If max depth would be exceeded.
        """
        try:
            self._check_circular_pattern(operation_id)
            record = self._escalation_records.get(operation_id)
            if record is not None and record.depth >= MAX_ESCALATION_DEPTH:
                raise EscalationDepthExceeded(
                    f"Operation {operation_id} at max escalation depth"
                )
        except (CircularEscalationError, EscalationDepthExceeded):
            raise
        return True

    def set_circuit_breaker(self, tier: Tier, degraded: bool) -> None:
        """
        Mark a tier's notification channel as degraded/unavailable.

        When a channel is degraded, escalations to that tier will
        automatically fall back to the next available tier.

        Args:
            tier: The tier whose channel is affected.
            degraded: True if channel is degraded.
        """
        self._circuit_breaker_state[tier] = degraded

    def is_channel_available(self, tier: Tier) -> bool:
        """Check if a tier's notification channel is available."""
        return not self._circuit_breaker_state.get(tier, False)

    # ─── Internal Helpers ───────────────────────────────────────────────────────

    def _check_circular_pattern(self, operation_id: str) -> None:
        """
        Detect circular escalation patterns.

        Raises CircularEscalationError if the last 2 escalations form a back-and-forth
        pattern between two tiers.
        """
        record = self._escalation_records.get(operation_id)
        if record is None or len(record.events) < 2:
            return

        # Check last 4 events for circular pattern
        recent = record.events[-4:]
        if len(recent) >= 2:
            # If the last two events ping-pong between the same two tiers, flag it
            if (
                recent[-2].from_tier == recent[-1].to_tier
                and recent[-2].to_tier == recent[-1].from_tier
            ):
                raise CircularEscalationError(
                    f"Detected circular escalation pattern for operation {operation_id}: "
                    f"{recent[-2].from_tier.name}→{recent[-2].to_tier.name}→"
                    f"{recent[-1].to_tier.name}"
                )

    def _get_next_available_tier(self, target_tier: Tier) -> Optional[Tier]:
        """
        Find the next available tier above the given target.

        Returns the next tier up that doesn't have a degraded channel,
        or None if none is available.
        """
        tier_order = sorted(TIER_ORDER.items(), key=lambda x: x[1])
        target_level = TIER_ORDER.get(target_tier, 0)

        for tier, level in tier_order:
            if level > target_level and not self._circuit_breaker_state.get(tier, False):
                return tier
        return None
