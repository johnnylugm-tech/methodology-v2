"""
Tests for enhanced CorrectionLibrary features:
- store_with_outcome()
- retrieve_weighted()
- _get_success_rate()
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from dataclasses import dataclass, field

# Ensure core is on the path for imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

from self_correction.correction_library import CorrectionEntry, CorrectionLibrary
from self_correction.self_correction_engine import CorrectionResult
from feedback.feedback import StandardFeedback



@dataclass
class MockFeedback:
    """Minimal mock for StandardFeedback."""
    source: str
    source_detail: str
    category: str
    description: str
    tags: list[str] = field(default_factory=list)


@dataclass
class MockCorrectionResult:
    """Minimal mock for CorrectionResult."""
    patched_code: str = "fixed code"
    confidence: float = 0.8
    verification_status: str = "success"


class TestStoreWithOutcome:
    """Tests for store_with_outcome()."""

    def test_store_with_outcome_success(self, tmp_path):
        """store_with_outcome records outcome='success' correctly."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        feedback = MockFeedback(
            source="linter",
            source_detail="PY001",
            category="style",
            description="Line too long",
            tags=["python"],
        )
        result = MockCorrectionResult(patched_code="x = 1", confidence=0.9)

        lib.store_with_outcome(feedback, result, outcome="success")

        assert len(lib.library) == 1
        entry = lib.library[0]
        assert entry.outcome == "success"
        assert entry.failure_reason is None
        assert entry.success is True
        assert entry.source == "linter"
        assert entry.source_detail == "PY001"

    def test_store_with_outcome_failed(self, tmp_path):
        """store_with_outcome records outcome='failed' with reason."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        feedback = MockFeedback(
            source="test_failure",
            source_detail="test_foo",
            category="unit_test",
            description="AssertionError",
            tags=["bug"],
        )
        result = MockCorrectionResult(patched_code="", confidence=0.5)

        lib.store_with_outcome(
            feedback, result,
            outcome="failed",
            failure_reason="Wrong assertion logic",
        )

        assert len(lib.library) == 1
        entry = lib.library[0]
        assert entry.outcome == "failed"
        assert entry.failure_reason == "Wrong assertion logic"
        assert entry.success is False

    def test_store_with_outcome_partial(self, tmp_path):
        """store_with_outcome records outcome='partial' correctly."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        feedback = MockFeedback(
            source="linter",
            source_detail="C001",
            category="style",
            description="Unused import",
            tags=["python"],
        )
        result = MockCorrectionResult(patched_code="import os  # noqa", confidence=0.6)

        lib.store_with_outcome(feedback, result, outcome="partial")

        assert len(lib.library) == 1
        entry = lib.library[0]
        assert entry.outcome == "partial"
        assert entry.success is False  # partial is not success


class TestRetrieveWeighted:
    """Tests for retrieve_weighted()."""

    def test_retrieve_weighted_exact_match(self, tmp_path):
        """Exact source+source_detail match returns highest-scored entries."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        # Add entries with different outcomes and confidences
        for i, (conf, outcome) in enumerate([(0.9, "success"), (0.5, "failed"), (0.7, "success")]):
            fb = MockFeedback("linter", "PY001", "style", f"Error {i}", tags=[])
            res = MockCorrectionResult(patched_code=f"fix{i}", confidence=conf)
            lib.store_with_outcome(fb, res, outcome=outcome)

        results = lib.retrieve_weighted("linter", "PY001", "style", limit=3)

        assert len(results) == 3
        # The success+high-confidence entry should be first
        assert results[0].outcome == "success"
        assert results[0].confidence == 0.9

    def test_retrieve_weighted_partial_match(self, tmp_path):
        """Fallback to source-only match when no exact match exists."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        # Add entry with different source_detail
        fb = MockFeedback("linter", "PY999", "style", "Different rule", tags=[])
        res = MockCorrectionResult(patched_code="fix", confidence=0.9)
        lib.store_with_outcome(fb, res, outcome="success")

        # Query for non-existent exact match
        results = lib.retrieve_weighted("linter", "PY001", "style", limit=5)

        assert len(results) == 1
        assert results[0].source_detail == "PY999"

    def test_retrieve_weighted_empty_library(self, tmp_path):
        """Empty library returns empty list."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))
        results = lib.retrieve_weighted("linter", "PY001", "style")
        assert results == []

    def test_retrieve_weighted_no_match_fallback(self, tmp_path):
        """No source match either returns empty list."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        fb = MockFeedback("linter", "PY001", "style", "Error", tags=[])
        res = MockCorrectionResult(patched_code="fix", confidence=0.9)
        lib.store_with_outcome(fb, res, outcome="success")

        results = lib.retrieve_weighted("compiler", "ERR001", "syntax", limit=5)
        assert results == []


class TestGetSuccessRate:
    """Tests for _get_success_rate()."""

    def test_get_success_rate_all_success(self, tmp_path):
        """100% success rate when all entries are successful."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        for i in range(3):
            fb = MockFeedback("linter", "RULE1", "style", f"Err{i}", tags=[])
            res = MockCorrectionResult(patched_code=f"fix{i}", confidence=0.8)
            lib.store_with_outcome(fb, res, outcome="success")

        rate = lib._get_success_rate("linter", "RULE1")
        assert rate == 1.0

    def test_get_success_rate_all_failed(self, tmp_path):
        """0% success rate when all entries failed."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        for i in range(4):
            fb = MockFeedback("linter", "RULE2", "style", f"Err{i}", tags=[])
            res = MockCorrectionResult(patched_code=f"fix{i}", confidence=0.5)
            lib.store_with_outcome(fb, res, outcome="failed", failure_reason="Bad fix")

        rate = lib._get_success_rate("linter", "RULE2")
        assert rate == 0.0

    def test_get_success_rate_mixed(self, tmp_path):
        """Correct rate for mixed outcomes."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))

        for outcome in ["success", "failed", "success", "partial"]:
            fb = MockFeedback("linter", "RULE3", "style", "Err", tags=[])
            res = MockCorrectionResult(patched_code="fix", confidence=0.7)
            lib.store_with_outcome(fb, res, outcome=outcome)

        rate = lib._get_success_rate("linter", "RULE3")
        # Only "success" counts as success; partial and failed don't
        assert rate == 0.5  # 2 success out of 4

    def test_get_success_rate_unknown(self, tmp_path):
        """Unknown source/detail returns default 0.5."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))
        rate = lib._get_success_rate("unknown", "unknown")
        assert rate == 0.5

    def test_get_success_rate_no_history(self, tmp_path):
        """No entries at all returns default 0.5."""
        lib = CorrectionLibrary(str(tmp_path / "test.json"))
        rate = lib._get_success_rate("linter", "NORULE")
        assert rate == 0.5


class TestOutcomeFieldPersistence:
    """Tests for outcome and failure_reason persistence."""

    def test_outcome_persists_to_json(self, tmp_path):
        """Outcome is correctly serialized to JSON."""
        storage = tmp_path / "library.json"
        lib = CorrectionLibrary(str(storage))

        fb = MockFeedback("test", "T1", "cat", "Desc", tags=[])
        res = MockCorrectionResult(patched_code="fix", confidence=0.8)
        lib.store_with_outcome(fb, res, outcome="failed", failure_reason="Bad logic")

        # Read raw JSON
        with open(storage) as f:
            raw = json.load(f)

        assert len(raw) == 1
        assert raw[0]["outcome"] == "failed"
        assert raw[0]["failure_reason"] == "Bad logic"

    def test_outcome_loads_from_json(self, tmp_path):
        """Outcome is correctly deserialized from JSON."""
        storage = tmp_path / "library.json"
        lib = CorrectionLibrary(str(storage))

        fb = MockFeedback("test", "T1", "cat", "Desc", tags=[])
        res = MockCorrectionResult(patched_code="fix", confidence=0.8)
        lib.store_with_outcome(fb, res, outcome="partial")

        # Create new instance to reload
        lib2 = CorrectionLibrary(str(storage))
        assert len(lib2.library) == 1
        assert lib2.library[0].outcome == "partial"
        assert lib2.library[0].failure_reason is None

    def test_backward_compatibility_no_outcome(self, tmp_path):
        """Entries without outcome field load with default 'success'."""
        storage = tmp_path / "library.json"

        # Manually write old-format entry (no outcome field)
        with open(storage, "w") as f:
            json.dump([{
                "error_signature": "abc123",
                "source": "linter",
                "source_detail": "R1",
                "category": "style",
                "error_description": "Old entry",
                "patched_code": "x=1",
                "confidence": 0.8,
                "success": True,
                "timestamp": "2024-01-01T00:00:00Z",
                "tags": [],
                # No "outcome" or "failure_reason" fields
            }], f)

        lib = CorrectionLibrary(str(storage))
        assert len(lib.library) == 1
        assert lib.library[0].outcome == "success"
        assert lib.library[0].failure_reason is None
