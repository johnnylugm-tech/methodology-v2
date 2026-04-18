"""Anomaly detection for Hunter Agent (FR-H-2, FR-H-3)."""
from typing import List, Optional

from .models import FabricateResult, PoisonResult, MemoryFact, AuthorizationChain
from .enums import AuthStatus
from .patterns import FABRICATION_KEYWORDS


class AnomalyDetector:
    """FR-H-2: Dialogue fabrication. FR-H-3: Memory poisoning."""

    def __init__(self, config: Optional[dict] = None) -> None:
        """Initialize anomaly detector."""
        self._config = config or {}
        self._audit_cache: dict = {}
        self._confidence_threshold = 0.6

    def detect_fabrication(
        self, agent_id: str, claim: str, conversation_id: str
    ) -> FabricateResult:
        """
        Detect if an agent's claim contradicts the audit log.

        Args:
            agent_id: Agent making the claim
            claim: Raw claim string
            conversation_id: Conversation context ID

        Returns:
            FabricateResult with confidence score
        """
        if not claim:
            return FabricateResult(
                is_fabricated=False,
                claim="",
                audit_reference=None,
                confidence=0.0
            )

        # Check if claim contains fabrication keywords
        is_suspicious = any(
            keyword.lower() in claim.lower()
            for keyword in FABRICATION_KEYWORDS
        )

        if is_suspicious:
            # Query audit log
            audit_ref = self._query_audit(conversation_id)
            if audit_ref is None:
                # Fabrication detected - claim not in audit
                return FabricateResult(
                    is_fabricated=True,
                    claim=claim,
                    audit_reference=None,
                    confidence=0.85
                )
            else:
                return FabricateResult(
                    is_fabricated=False,
                    claim=claim,
                    audit_reference=audit_ref,
                    confidence=0.9
                )

        return FabricateResult(
            is_fabricated=False,
            claim=claim,
            audit_reference=None,
            confidence=0.0
        )

    def detect_poisoning(
        self, fact: MemoryFact, auth_chain: AuthorizationChain
    ) -> PoisonResult:
        """
        Detect unauthorized memory poisoning.

        Args:
            fact: MemoryFact being written
            auth_chain: AuthorizationChain claiming approval

        Returns:
            PoisonResult with auth_status
        """
        if auth_chain.authorized_by:
            return PoisonResult(
                is_poisoned=False,
                fact=fact,
                auth_status=AuthStatus.AUTHORIZED,
                source=fact.source_agent,
                timestamp=fact.created_at
            )

        return PoisonResult(
            is_poisoned=True,
            fact=fact,
            auth_status=AuthStatus.UNAUTHORIZED,
            source=fact.source_agent,
            timestamp=fact.created_at
        )

    def extract_claims(self, content: str) -> List[str]:
        """
        Extract potential fabrication claims from content.

        Args:
            content: Message content

        Returns:
            List of claim strings found
        """
        if not content:
            return []

        claims = []
        lower_content = content.lower()

        for keyword in FABRICATION_KEYWORDS:
            if keyword.lower() in lower_content:
                idx = lower_content.find(keyword.lower())
                # Extract sentence containing keyword
                start = max(0, content.rfind('.', 0, idx) + 1)
                end = content.find('.', idx)
                if end == -1:
                    end = len(content)
                claim = content[start:end].strip()
                if claim:
                    claims.append(claim)

        return claims

    def _query_audit(self, conversation_id: str) -> Optional[str]:
        """Query audit log for conversation."""
        return self._audit_cache.get(conversation_id)
