"""Runtime monitor for Hunter Agent (FR-H-5)."""
import hashlib
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import OrderedDict

from .models import IntegrityResult


class AccessRecord:
    """Record of an agent's access to a source."""
    def __init__(self, agent_id: str, source: str, accessed_at: datetime):
        self.agent_id = agent_id
        self.source = source
        self.accessed_at = accessed_at


class RuntimeMonitor:
    """FR-H-5: Runtime integrity validation on memory/context read."""

    def __init__(self, config: Optional[dict] = None) -> None:
        """Initialize runtime monitor."""
        self._config = config or {}
        self._hash_cache: OrderedDict = OrderedDict()
        self._cache_max = 10000
        self._access_window: Dict[str, List[AccessRecord]] = {}
        self._window_max = 1000
        self._anomaly_threshold = 0.3

    def validate_read(
        self, agent_id: str, source: str, expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """
        Validate an agent's read operation on memory/context/knowledge.

        Args:
            agent_id: Agent performing the read
            source: Source identifier
            expected_hash: Optional hash to verify

        Returns:
            IntegrityResult with anomaly_score and requires_hitl flag
        """
        actual_hash = self._compute_hash(source)

        if expected_hash and actual_hash != expected_hash:
            anomaly = self.detect_anomaly(agent_id)
            return IntegrityResult(
                is_valid=False,
                source=source,
                actual_hash=actual_hash,
                expected_hash=expected_hash,
                anomaly_score=anomaly,
                requires_hitl=anomaly >= self._anomaly_threshold
            )

        return IntegrityResult(
            is_valid=True,
            source=source,
            actual_hash=actual_hash,
            expected_hash=expected_hash or "",
            anomaly_score=0.0,
            requires_hitl=False
        )

    def record_access(self, agent_id: str, source: str) -> None:
        """
        Record an access event in the sliding window.

        Args:
            agent_id: Agent that accessed
            source: Source accessed
        """
        if agent_id not in self._access_window:
            self._access_window[agent_id] = []

        record = AccessRecord(
            agent_id=agent_id,
            source=source,
            accessed_at=datetime.now()
        )
        self._access_window[agent_id].append(record)

        # Sliding window limit
        if len(self._access_window[agent_id]) > self._window_max:
            self._access_window[agent_id].pop(0)

    def detect_anomaly(self, agent_id: str) -> float:
        """
        Detect anomalous access patterns using sliding window analysis.

        Args:
            agent_id: Agent to analyze

        Returns:
            Anomaly score 0.0-1.0 (>= 0.3 triggers HITL)
        """
        if agent_id not in self._access_window:
            return 0.0

        records = self._access_window[agent_id]
        if len(records) < 5:
            return 0.0

        # Simple anomaly: burst access
        recent = [
            r for r in records
            if r.accessed_at > datetime.now() - timedelta(seconds=1)
        ]
        if len(recent) > 20:
            return 0.4

        return 0.0

    def _compute_hash(self, source: str) -> str:
        """Compute SHA-256 hash."""
        return hashlib.sha256(source.encode()).hexdigest()
