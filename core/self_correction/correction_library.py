"""
Correction Library — Persistent Storage of Correction Experiences.

Stores past correction attempts so the engine can learn from history
and retrieve similar successful fixes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from os.path import exists
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from projects.methodology_v2.core.feedback.feedback import StandardFeedback
    from projects.methodology_v2.core.self_correction.self_correction_engine import CorrectionResult


@dataclass
class CorrectionEntry:
    """
    A single correction experience stored in the library.

    Attributes:
        error_signature: MD5 hash of the error key (source + source_detail + category).
        source: Feedback source (e.g., 'linter', 'test_failure').
        source_detail: Specific detail within the source (e.g., file path, rule id).
        category: Feedback category.
        error_description: Human-readable description of the error.
        patched_code: The code that was used to fix the error.
        confidence: Confidence score at time of correction.
        success: Whether the correction was successful.
        timestamp: ISO 8601 timestamp of when the correction was made.
        tags: Arbitrary tags for categorization.
        outcome: Outcome result ('success' / 'partial' / 'failed').
        failure_reason: Reason for failure if outcome='failed'.
    """

    error_signature: str
    source: str
    source_detail: str
    category: str
    error_description: str
    patched_code: str
    confidence: float
    success: bool
    timestamp: str
    tags: list[str]
    outcome: str = "success"
    failure_reason: str | None = None


class CorrectionLibrary:
    """
    Persistent library of correction experiences.

    Stores successful (and unsuccessful) correction attempts so the engine
    can retrieve similar past corrections to inform future fixes.

    The library is persisted to a JSON file at the specified path.
    """

    def __init__(self, storage_path: str = "correction_library.json") -> None:
        """
        Initialize the correction library.

        Args:
            storage_path: Path to the JSON file for persistence.
        """
        self.storage_path = storage_path
        self.library: list[CorrectionEntry] = []
        self._load()

    def store(
        self,
        feedback: StandardFeedback,
        result: "CorrectionResult",
    ) -> None:
        """
        Store a correction experience in the library.

        Args:
            feedback: The feedback item that was corrected.
            result: The correction result.
        """
        signature = self._make_signature(feedback)

        entry = CorrectionEntry(
            error_signature=signature,
            source=feedback.source,
            source_detail=feedback.source_detail,
            category=feedback.category,
            error_description=feedback.description,
            patched_code=result.patched_code or "",
            confidence=result.confidence,
            success=result.verification_status == "success",
            timestamp=datetime.now(timezone.utc).isoformat(),
            tags=feedback.tags,
        )

        self.library.append(entry)
        self._save()

    def store_with_outcome(
        self,
        feedback: StandardFeedback,
        result: "CorrectionResult",
        outcome: str,  # "success" / "partial" / "failed"
        failure_reason: str | None = None,
    ) -> None:
        """
        Store a correction experience with explicit outcome tracking.

        This method extends store() by recording the actual result,
        enabling weighted retrieval based on historical success rates.

        Args:
            feedback: The feedback item that was corrected.
            result: The correction result.
            outcome: "success" / "partial" / "failed"
            failure_reason: Reason for failure (only used if outcome="failed").
        """
        entry = CorrectionEntry(
            error_signature=self._make_signature(feedback),
            source=feedback.source,
            source_detail=feedback.source_detail,
            category=feedback.category,
            error_description=feedback.description,
            patched_code=result.patched_code or "",
            confidence=result.confidence,
            success=(outcome == "success"),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tags=feedback.tags,
            outcome=outcome,
            failure_reason=failure_reason,
        )

        self.library.append(entry)
        self._save()

    def retrieve_weighted(
        self,
        source: str,
        source_detail: str,
        category: str,
        limit: int = 5,
    ) -> list[CorrectionEntry]:
        """
        Retrieve similar past correction experiences, weighted by success rate.

        Relevance Score = (Similarity × 0.4) + (Success Rate × 0.3) + (Confidence × 0.3)

        Args:
            source: Feedback source to match.
            source_detail: Specific detail to match.
            category: Category to match.
            limit: Maximum number of entries to return.

        Returns:
            List of matching correction entries, ordered by relevance score.
        """
        # Try exact match (source + source_detail)
        candidates = [
            e for e in self.library
            if e.source == source and e.source_detail == source_detail
        ]

        # Fall back to category match if no exact match
        if not candidates:
            candidates = [
                e for e in self.library
                if e.source == source and e.category == category
            ]

        # Calculate relevance scores
        scored = []
        for c in candidates:
            # Similarity: exact source_detail match scores higher
            similarity = 1.0 if c.source_detail == source_detail else 0.5

            # Success rate weight
            success_rate = self._get_success_rate(c.source, c.source_detail)

            # Confidence weight: penalize failed corrections
            confidence_weight = c.confidence if c.success else c.confidence * 0.3

            relevance = (similarity * 0.4) + (success_rate * 0.3) + (confidence_weight * 0.3)
            scored.append((c, relevance))

        # Sort by relevance descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:limit]]

    def _get_success_rate(self, source: str, source_detail: str) -> float:
        """
        Calculate the success rate for a given source/source_detail combination.

        Args:
            source: Feedback source.
            source_detail: Feedback source_detail.

        Returns:
            Success rate between 0.0 and 1.0, default 0.5 if no history.
        """
        matches = [
            e for e in self.library
            if e.source == source and e.source_detail == source_detail
        ]
        if not matches:
            return 0.5

        successes = sum(
            1 for e in matches
            if getattr(e, "outcome", "success") == "success"
        )
        return successes / len(matches)

    def retrieve(
        self,
        source: str,
        source_detail: str,
        category: str,
        limit: int = 5,
    ) -> list[CorrectionEntry]:
        """
        Retrieve similar past correction experiences.

        Args:
            source: Feedback source to match.
            source_detail: Specific detail to match.
            category: Category to match.
            limit: Maximum number of entries to return.

        Returns:
            List of matching correction entries, ordered by confidence (highest first).
        """
        matches: list[CorrectionEntry] = []

        for entry in self.library:
            if (
                entry.source == source
                and entry.category == category
                and entry.success
            ):
                matches.append(entry)

        # Sort by confidence, highest first, then by recency
        matches.sort(key=lambda e: (e.confidence, e.timestamp), reverse=True)

        return matches[:limit]

    def retrieve_by_signature(
        self,
        signature: str,
        limit: int = 3,
    ) -> list[CorrectionEntry]:
        """
        Retrieve corrections by exact error signature.

        Args:
            signature: The error signature (MD5 hash).
            limit: Maximum number of entries to return.

        Returns:
            List of matching entries.
        """
        matches = [e for e in self.library if e.error_signature == signature]
        matches.sort(key=lambda e: (e.confidence, e.timestamp), reverse=True)
        return matches[:limit]

    def get_successful_count(self) -> int:
        """Return the count of successful corrections in the library."""
        return sum(1 for e in self.library if e.success)

    def get_hit_rate(self) -> float:
        """
        Calculate the 'learning hit rate' — proportion of retrievals
        that found a successful past correction.
        """
        # This is a simplified metric; in production you'd track retrieval stats
        if not self.library:
            return 0.0
        successful = sum(1 for e in self.library if e.success)
        return successful / len(self.library)

    def _make_signature(self, feedback: StandardFeedback) -> str:
        """
        Generate an error signature for a feedback item.

        The signature is an MD5 hash of the key identifying fields,
        used for fast lookup of similar past errors.

        Args:
            feedback: The feedback item.

        Returns:
            MD5 hex string signature.
        """
        key_parts = [
            feedback.source,
            feedback.source_detail,
            feedback.category,
        ]
        key_string = "|".join(str(p) for p in key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _save(self) -> None:
        """Persist the library to the JSON storage file."""
        with open(self.storage_path, "w") as f:
            json.dump([self._entry_to_dict(e) for e in self.library], f, indent=2)

    def _load(self) -> None:
        """Load the library from the JSON storage file."""
        if not exists(self.storage_path):
            return

        try:
            with open(self.storage_path) as f:
                raw = json.load(f)
            self.library = [self._dict_to_entry(d) for d in raw]
        except (json.JSONDecodeError, KeyError, TypeError):
            # Corrupt file — start fresh
            self.library = []

    @staticmethod
    def _entry_to_dict(entry: CorrectionEntry) -> dict:
        """Convert a CorrectionEntry to a plain dict for serialization."""
        return asdict(entry)

    @staticmethod
    def _dict_to_entry(data: dict) -> CorrectionEntry:
        """Reconstruct a CorrectionEntry from a plain dict."""
        # Handle backward compatibility for entries without outcome/failure_reason
        data.setdefault("outcome", "success")
        data.setdefault("failure_reason", None)
        return CorrectionEntry(**data)



