"""
StandardFeedback Dataclass and In-Memory Store.

Defines the canonical feedback structure and provides storage operations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any


class FeedbackStatus(str, Enum):
    """Feedback lifecycle status."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    CLOSED = "closed"


class FeedbackCategory(str, Enum):
    """Feedback category classification."""

    BUG = "bug"
    PERFORMANCE = "performance"
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    COMPLIANCE = "compliance"
    UX = "ux"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    OPERATIONAL = "operational"


@dataclass
class StandardFeedback:
    """
    Canonical feedback dataclass.

    Attributes:
        id: Unique identifier (UUID).
        source: Feedback source name (e.g., 'linter', 'test_failure').
        source_detail: Specific location within source (e.g., file path, rule id).
        type: Feedback type (error, warning, info, suggestion).
        category: Broad category for routing.
        severity: Severity level (critical/high/medium/low/info).
        title: Short summary of the issue.
        description: Detailed description.
        context: Arbitrary metadata dict (file, line, commit, etc.).
        timestamp: ISO 8601 creation timestamp.
        sla_deadline: ISO 8601 SLA deadline timestamp.
        status: Current lifecycle status.
        assignee: Assigned person or team (None if unassigned).
        resolution: How the issue was resolved (None if open).
        verified_at: ISO 8601 verification timestamp.
        related_feedbacks: IDs of related feedback items.
        recurrence_count: How many times this issue has recurred.
        confidence: Confidence score 0.0-1.0.
        tags: Arbitrary tags for filtering/search.
    """

    id: str
    source: str
    source_detail: str
    type: str
    category: FeedbackCategory
    severity: str
    title: str
    description: str
    context: dict[str, Any]
    timestamp: str
    sla_deadline: str
    status: FeedbackStatus = FeedbackStatus.PENDING
    assignee: str | None = None
    resolution: str | None = None
    verified_at: str | None = None
    related_feedbacks: list[str] = field(default_factory=list)
    recurrence_count: int = 0
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dict (useful for serialization)."""
        return {
            "id": self.id,
            "source": self.source,
            "source_detail": self.source_detail,
            "type": self.type,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "timestamp": self.timestamp,
            "sla_deadline": self.sla_deadline,
            "status": self.status,
            "assignee": self.assignee,
            "resolution": self.resolution,
            "verified_at": self.verified_at,
            "related_feedbacks": self.related_feedbacks,
            "recurrence_count": self.recurrence_count,
            "confidence": self.confidence,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StandardFeedback:
        """Reconstruct from dict."""
        return cls(**data)


@dataclass
class FeedbackCreate:
    """Input payload for creating a new feedback."""

    source: str
    source_detail: str
    type: str
    category: str
    severity: str
    title: str
    description: str
    context: dict[str, Any] = field(default_factory=dict)
    assignee: str | None = None
    tags: list[str] = field(default_factory=list)
    related_feedbacks: list[str] = field(default_factory=list)
    confidence: float = 1.0
    sla_deadline: str | None = None


@dataclass
class FeedbackUpdate:
    """Fields that can be updated on existing feedback."""

    status: FeedbackStatus | None = None
    assignee: str | None = None
    severity: str | None = None
    resolution: str | None = None
    tags: list[str] | None = None
    related_feedbacks: list[str] | None = None


class FeedbackStore:
    """
    In-memory storage for feedback items.

    Thread-unsafe; use in single-threaded contexts or wrap with locks.
    """

    def __init__(self) -> None:
        self._store: dict[str, StandardFeedback] = {}
        self._by_source: dict[str, list[str]] = {}
        self._by_status: dict[str, list[str]] = {}
        self._by_assignee: dict[str, list[str]] = {}

    def add(self, feedback: StandardFeedback) -> None:
        """Add a feedback item to the store."""
        self._store[feedback.id] = feedback

        # Index by source
        if feedback.source not in self._by_source:
            self._by_source[feedback.source] = []
        if feedback.id not in self._by_source[feedback.source]:
            self._by_source[feedback.source].append(feedback.id)

        # Index by status
        if feedback.status not in self._by_status:
            self._by_status[feedback.status] = []
        if feedback.id not in self._by_status[feedback.status]:
            self._by_status[feedback.status].append(feedback.id)

        # Index by assignee
        if feedback.assignee:
            if feedback.assignee not in self._by_assignee:
                self._by_assignee[feedback.assignee] = []
            if feedback.id not in self._by_assignee[feedback.assignee]:
                self._by_assignee[feedback.assignee].append(feedback.id)

    def get(self, feedback_id: str) -> StandardFeedback | None:
        """Get a feedback item by ID."""
        return self._store.get(feedback_id)

    def update(self, feedback_id: str, update: FeedbackUpdate) -> StandardFeedback | None:
        """Update fields of an existing feedback."""
        fb = self._store.get(feedback_id)
        if fb is None:
            return None

        # Remove from old status index
        if fb.status in self._by_status:
            if feedback_id in self._by_status[fb.status]:
                self._by_status[fb.status].remove(feedback_id)

        # Apply updates
        if update.status is not None:
            fb.status = update.status
        if update.assignee is not None:
            # Remove from old assignee index
            if fb.assignee and fb.assignee in self._by_assignee:
                if feedback_id in self._by_assignee[fb.assignee]:
                    self._by_assignee[fb.assignee].remove(feedback_id)
            fb.assignee = update.assignee
        if update.severity is not None:
            fb.severity = update.severity
        if update.resolution is not None:
            fb.resolution = update.resolution
        if update.tags is not None:
            fb.tags = update.tags
        if update.related_feedbacks is not None:
            fb.related_feedbacks = update.related_feedbacks

        # Re-index by new status
        if fb.status not in self._by_status:
            self._by_status[fb.status] = []
        if feedback_id not in self._by_status[fb.status]:
            self._by_status[fb.status].append(feedback_id)

        # Re-index by new assignee
        if fb.assignee:
            if fb.assignee not in self._by_assignee:
                self._by_assignee[fb.assignee] = []
            if feedback_id not in self._by_assignee[fb.assignee]:
                self._by_assignee[fb.assignee].append(feedback_id)

        return fb

    def list_by_source(self, source: str) -> list[StandardFeedback]:
        """List all feedback from a given source."""
        ids = self._by_source.get(source, [])
        return [self._store[fid] for fid in ids if fid in self._store]

    def list_by_status(self, status: str) -> list[StandardFeedback]:
        """List all feedback with given status."""
        ids = self._by_status.get(status, [])
        return [self._store[fid] for fid in ids if fid in self._store]

    def list_by_assignee(self, assignee: str) -> list[StandardFeedback]:
        """List all feedback assigned to a person."""
        ids = self._by_assignee.get(assignee, [])
        return [self._store[fid] for fid in ids if fid in self._store]

    def list_all(self) -> list[StandardFeedback]:
        """List all feedback items."""
        return list(self._store.values())

    def list_open(self) -> list[StandardFeedback]:
        """List all feedback that is not closed or verified."""
        closed_statuses = {"closed", "verified"}
        return [fb for fb in self._store.values() if fb.status not in closed_statuses]

    def delete(self, feedback_id: str) -> bool:
        """Remove a feedback item from the store."""
        fb = self._store.pop(feedback_id, None)
        if fb is None:
            return False

        # Clean up indices
        for idx in (self._by_source, self._by_status, self._by_assignee):
            for bucket in idx.values():
                if feedback_id in bucket:
                    bucket.remove(feedback_id)

        return True

    def __len__(self) -> int:
        return len(self._store)


# Global singleton store — can be replaced for testing
_global_store: FeedbackStore = FeedbackStore()


def get_store() -> FeedbackStore:
    """Get the global feedback store instance."""
    return _global_store


def reset_store() -> None:
    """Reset the global store (primarily for testing)."""
    global _global_store
    _global_store = FeedbackStore()