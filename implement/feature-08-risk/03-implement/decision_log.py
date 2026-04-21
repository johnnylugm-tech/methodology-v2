"""
Decision Log [FR-R-9]

Records all significant Planner decisions in structured YAML format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib
import json
import yaml
import os
from pathlib import Path


@dataclass
class DecisionInput:
    """
    Input data for logging a decision.

    Attributes:
        choice: The chosen option
        alternatives: List of rejected alternatives with reasons
        confidence_score: Initial confidence (0.0-10.0)
        effort_minutes: Time spent on decision
        tool_calls: Number of tool calls made
        tokens_consumed: Token count
        context: Full decision context
        agent_id: Which agent made the decision
        task_id: Associated task ID
    """

    choice: str
    alternatives: list[dict] = None
    confidence_score: float = 5.0
    effort_minutes: int = 0
    tool_calls: int = 0
    tokens_consumed: int = 0
    context: dict = None
    agent_id: str = "planner"
    task_id: str = ""

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.context is None:
            self.context = {}


@dataclass
class DecisionRecord:
    """
    Complete decision record as per schema [FR-R-9].

    Contains all fields from the specification's YAML schema.
    """

    # Identification
    decision_id: str = ""
    timestamp: str = ""
    agent_id: str = "planner"
    task_id: str = ""

    # Decision content
    choice: str = ""
    alternatives_considered: list[dict] = None

    # Scoring
    confidence_score: float = 5.0
    actual_outcome: Optional[float] = None
    confidence_calibrated: bool = False

    # Effort tracking
    effort_minutes: int = 0
    tool_calls: int = 0
    tokens_consumed: int = 0

    # Assumptions and uncertainties
    key_assumptions: list[dict] = None
    uncertainties: list[dict] = None

    # Evidence
    evidence_hash: str = ""
    evidence_payload: dict = None

    # Review
    reviewed_by: Optional[str] = None
    review_round: int = 0
    review_notes: str = ""

    # Metadata
    metadata: dict = None

    def __post_init__(self):
        if self.alternatives_considered is None:
            self.alternatives_considered = []
        if self.key_assumptions is None:
            self.key_assumptions = []
        if self.uncertainties is None:
            self.uncertainties = []
        if self.evidence_payload is None:
            self.evidence_payload = {}
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_input(cls, decision_id: str, input_data: DecisionInput) -> "DecisionRecord":
        """Create a DecisionRecord from DecisionInput."""
        now = datetime.utcnow()
        return cls(
            decision_id=decision_id,
            timestamp=now.isoformat(),
            agent_id=input_data.agent_id,
            task_id=input_data.task_id,
            choice=input_data.choice,
            alternatives_considered=input_data.alternatives,
            confidence_score=input_data.confidence_score,
            effort_minutes=input_data.effort_minutes,
            tool_calls=input_data.tool_calls,
            tokens_consumed=input_data.tokens_consumed,
            evidence_hash=cls._calculate_evidence_hash(input_data.context),
            evidence_payload=input_data.context,
            metadata={
                "model_version": input_data.context.get("model_version", "unknown"),
                "session_id": input_data.context.get("session_id", "unknown"),
            }
        )

    @staticmethod
    def _calculate_evidence_hash(context: dict) -> str:
        """Calculate SHA-256 hash of decision context."""
        if not context:
            return ""
        canonical = json.dumps(context, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def update_review(
        self,
        reviewed_by: str,
        review_round: int,
        review_notes: str,
        confidence_adjustment: float = 0.0
    ) -> None:
        """Update with devil's advocate review."""
        self.reviewed_by = reviewed_by
        self.review_round = review_round
        self.review_notes = review_notes
        self.confidence_score += confidence_adjustment

    def set_actual_outcome(self, outcome: float) -> None:
        """Set actual outcome for calibration."""
        self.actual_outcome = outcome
        self.confidence_calibrated = True

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "planner_decision_trace": {
                "decision_id": self.decision_id,
                "timestamp": self.timestamp,
                "agent_id": self.agent_id,
                "task_id": self.task_id,
                "choice": self.choice,
                "alternatives_considered": self.alternatives_considered,
                "confidence_score": self.confidence_score,
                "actual_outcome": self.actual_outcome,
                "confidence_calibrated": self.confidence_calibrated,
                "effort_minutes": self.effort_minutes,
                "tool_calls": self.tool_calls,
                "tokens_consumed": self.tokens_consumed,
                "key_assumptions": self.key_assumptions,
                "uncertainties": self.uncertainties,
                "evidence_hash": self.evidence_hash,
                "evidence_payload": self.evidence_payload,
                "reviewed_by": self.reviewed_by,
                "review_round": self.review_round,
                "review_notes": self.review_notes,
                "metadata": self.metadata,
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionRecord":
        """Create from dictionary (deserialization)."""
        trace = data.get("planner_decision_trace", data)
        return cls(
            decision_id=trace.get("decision_id", ""),
            timestamp=trace.get("timestamp", ""),
            agent_id=trace.get("agent_id", "planner"),
            task_id=trace.get("task_id", ""),
            choice=trace.get("choice", ""),
            alternatives_considered=trace.get("alternatives_considered", []),
            confidence_score=trace.get("confidence_score", 5.0),
            actual_outcome=trace.get("actual_outcome"),
            confidence_calibrated=trace.get("confidence_calibrated", False),
            effort_minutes=trace.get("effort_minutes", 0),
            tool_calls=trace.get("tool_calls", 0),
            tokens_consumed=trace.get("tokens_consumed", 0),
            key_assumptions=trace.get("key_assumptions", []),
            uncertainties=trace.get("uncertainties", []),
            evidence_hash=trace.get("evidence_hash", ""),
            evidence_payload=trace.get("evidence_payload", {}),
            reviewed_by=trace.get("reviewed_by"),
            review_round=trace.get("review_round", 0),
            review_notes=trace.get("review_notes", ""),
            metadata=trace.get("metadata", {}),
        )


class DecisionLog:
    """
    Append-only decision log with YAML storage [FR-R-9].

    Stores decisions in structured YAML format for auditability and review.
    """

    DECISION_ID_FORMAT = "{category}-{YYYYMMDD}-{sequence:03d}"

    def __init__(self, storage_path: str = "memory/decisions"):
        """
        Initialize DecisionLog.

        Args:
            storage_path: Base path for decision storage
        """
        self._storage_path = Path(storage_path)
        self._index_path = self._storage_path / "index.yaml"
        self._counters: dict[str, int] = {}  # category -> sequence counter
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _generate_decision_id(self, category: str = "dec") -> str:
        """Generate unique decision ID in format: {category}-{YYYYMMDD}-{sequence}."""
        today = datetime.utcnow().strftime("%Y%m%d")

        # Initialize counter for this category+date
        key = f"{category}-{today}"
        if key not in self._counters:
            self._counters[key] = 1
        else:
            self._counters[key] += 1

        return f"{category}-{today}-{self._counters[key]:03d}"

    def _get_decision_path(self, decision_id: str) -> Path:
        """Get file path for a decision ID."""
        # Parse decision_id to extract date
        parts = decision_id.split("-")
        if len(parts) >= 2:
            date_part = parts[1]
            year = date_part[:4]
            month = date_part[4:6]
        else:
            now = datetime.utcnow()
            year = now.strftime("%Y")
            month = now.strftime("%m")

        return self._storage_path / year / month / f"{decision_id}.yaml"

    def append(self, input_data: DecisionInput, category: str = "dec") -> str:
        """
        Log a new decision.

        Args:
            input_data: DecisionInput to log
            category: Decision category for ID generation

        Returns:
            decision_id: Unique identifier for the logged decision
        """
        if not self._enabled:
            return ""

        decision_id = self._generate_decision_id(category)
        record = DecisionRecord.from_input(decision_id, input_data)

        # Ensure directory exists
        decision_path = self._get_decision_path(decision_id)
        decision_path.parent.mkdir(parents=True, exist_ok=True)

        # Write decision YAML
        with open(decision_path, 'w', encoding='utf-8') as f:
            yaml.dump(record.to_dict(), f, default_flow_style=False, allow_unicode=True)

        # Update index
        self._update_index(decision_id, record.timestamp)

        return decision_id

    def _update_index(self, decision_id: str, timestamp: str) -> None:
        """Update the append-only index."""
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Read existing index or create new
        index_data = {"decisions": []}
        if self._index_path.exists():
            try:
                with open(self._index_path, 'r', encoding='utf-8') as f:
                    index_data = yaml.safe_load(f) or {"decisions": []}
            except Exception:
                index_data = {"decisions": []}

        # Append new entry
        index_data["decisions"].append({
            "decision_id": decision_id,
            "timestamp": timestamp,
            "path": str(self._get_decision_path(decision_id)),
        })

        # Write index
        with open(self._index_path, 'w', encoding='utf-8') as f:
            yaml.dump(index_data, f, default_flow_style=False)

    def get(self, decision_id: str) -> Optional[DecisionRecord]:
        """
        Retrieve a decision by ID.

        Args:
            decision_id: ID of decision to retrieve

        Returns:
            DecisionRecord if found, None otherwise
        """
        decision_path = self._get_decision_path(decision_id)

        if not decision_path.exists():
            return None

        try:
            with open(decision_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return DecisionRecord.from_dict(data)
        except Exception:
            return None

    def update_review(
        self,
        decision_id: str,
        reviewed_by: str,
        review_round: int,
        review_notes: str,
        confidence_adjustment: float = 0.0
    ) -> bool:
        """
        Update a decision with review information.

        Args:
            decision_id: ID of decision to update
            reviewed_by: Reviewer identifier
            review_round: Review round number
            review_notes: Notes from reviewer
            confidence_adjustment: Adjustment to confidence score

        Returns:
            True if updated successfully, False otherwise
        """
        record = self.get(decision_id)
        if not record:
            return False

        record.update_review(reviewed_by, review_round, review_notes, confidence_adjustment)

        # Write updated record
        decision_path = self._get_decision_path(decision_id)
        try:
            with open(decision_path, 'w', encoding='utf-8') as f:
                yaml.dump(record.to_dict(), f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception:
            return False

    def list_recent(self, limit: int = 10, category: str = None) -> list[DecisionRecord]:
        """
        List recent decisions.

        Args:
            limit: Maximum number to return
            category: Optional filter by category

        Returns:
            List of recent DecisionRecords
        """
        if not self._index_path.exists():
            return []

        try:
            with open(self._index_path, 'r', encoding='utf-8') as f:
                index_data = yaml.safe_load(f) or {"decisions": []}
        except Exception:
            return []

        decisions = index_data.get("decisions", [])
        if category:
            decisions = [d for d in decisions if d["decision_id"].startswith(category)]

        # Sort by timestamp descending and take limit
        decisions = sorted(decisions, key=lambda x: x["timestamp"], reverse=True)[:limit]

        # Load full records
        records = []
        for entry in decisions:
            record = self.get(entry["decision_id"])
            if record:
                records.append(record)

        return records

    def find_by_assumption(self, assumption_text: str) -> list[DecisionRecord]:
        """Find decisions with a specific assumption text."""
        # This would require scanning all decision files
        # For efficiency in production, use a search index
        results = []
        for record in self.list_recent(limit=100):
            for assumption in record.key_assumptions:
                if assumption_text.lower() in str(assumption).lower():
                    results.append(record)
                    break
        return results

    def count(self) -> int:
        """Get total number of logged decisions."""
        if not self._index_path.exists():
            return 0

        try:
            with open(self._index_path, 'r', encoding='utf-8') as f:
                index_data = yaml.safe_load(f) or {"decisions": []}
            return len(index_data.get("decisions", []))
        except Exception:
            return 0