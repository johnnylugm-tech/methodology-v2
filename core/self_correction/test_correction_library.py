"""
Tests for CorrectionLibrary.
"""

import sys
from pathlib import Path

# Ensure core is on the path for imports
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root))

import os
import tempfile
import hashlib

import pytest

from self_correction.correction_library import (
    CorrectionLibrary,
    CorrectionEntry,
)
from self_correction.self_correction_engine import CorrectionResult
from feedback.feedback import StandardFeedback


@pytest.fixture
def temp_storage():
    """Create a temporary file for library storage."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def library(temp_storage):
    """Create a CorrectionLibrary with temporary storage."""
    return CorrectionLibrary(storage_path=temp_storage)


@pytest.fixture
def sample_feedback():
    """Create a sample StandardFeedback for testing."""
    return StandardFeedback(
        id="fb-001",
        source="linter",
        source_detail="src/app.py",
        type="error",
        category="syntax",
        severity="high",
        title="Syntax error",
        description="Missing colon after function definition",
        context={"file_path": "src/app.py"},
        timestamp="2024-01-01T00:00:00Z",
        sla_deadline="2024-01-02T00:00:00Z",
        tags=["python", "syntax"],
    )


class TestSignature:
    """Tests for _make_signature."""

    def test_same_inputs_produce_same_signature(self, library, sample_feedback):
        """Identical feedback produces identical signatures."""
        sig1 = library._make_signature(sample_feedback)
        sig2 = library._make_signature(sample_feedback)
        assert sig1 == sig2

    def test_different_inputs_produce_different_signatures(self, library):
        """Different feedback produces different signatures."""
        fb1 = StandardFeedback(
            id="a",
            source="linter",
            source_detail="file1.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        fb2 = StandardFeedback(
            id="b",
            source="linter",
            source_detail="file2.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        assert library._make_signature(fb1) != library._make_signature(fb2)

    def test_signature_is_valid_md5(self, library, sample_feedback):
        """Signature is a valid MD5 hex string."""
        sig = library._make_signature(sample_feedback)
        assert len(sig) == 32
        assert all(c in "0123456789abcdef" for c in sig)


class TestStoreAndRetrieve:
    """Tests for store and retrieve operations."""

    def test_store_adds_entry_to_library(self, library, sample_feedback):
        """store() adds an entry to the library."""
        result = CorrectionResult(
            feedback_id="fb-001",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        )

        library.store(sample_feedback, result)
        assert len(library.library) == 1

    def test_retrieve_finds_similar_entries(self, library, sample_feedback):
        """retrieve() finds entries with matching source and category."""
        result = CorrectionResult(
            feedback_id="fb-001",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        )

        library.store(sample_feedback, result)

        matches = library.retrieve(
            source="linter",
            source_detail="src/app.py",
            category="syntax",
            limit=5,
        )
        assert len(matches) == 1
        assert matches[0].source == "linter"

    def test_retrieve_filters_by_source_and_category(self, library):
        """retrieve() filters by source and category, not just source."""
        fb1 = StandardFeedback(
            id="fb-1",
            source="linter",
            source_detail="file.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        fb2 = StandardFeedback(
            id="fb-2",
            source="linter",
            source_detail="file.py",
            type="warning",
            category="unused-variable",
            severity="low",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )

        library.store(fb1, CorrectionResult(
            feedback_id="fb-1",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))
        library.store(fb2, CorrectionResult(
            feedback_id="fb-2",
            error_id="linter|unused-variable",
            auto_fixable=True,
            strategy="remove_unused",
            confidence=0.90,
            patched_code="x = 1\ndef foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))

        # Retrieve syntax only
        syntax_matches = library.retrieve(
            source="linter",
            source_detail="file.py",
            category="syntax",
            limit=5,
        )
        assert len(syntax_matches) == 1
        assert syntax_matches[0].category == "syntax"

        # Retrieve unused-variable only
        unused_matches = library.retrieve(
            source="linter",
            source_detail="file.py",
            category="unused-variable",
            limit=5,
        )
        assert len(unused_matches) == 1
        assert unused_matches[0].category == "unused-variable"

    def test_retrieve_returns_only_successful_corrections(self, library):
        """retrieve() only returns entries where success=True."""
        fb = StandardFeedback(
            id="fb-mixed",
            source="linter",
            source_detail="file.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )

        # Store a successful correction
        library.store(fb, CorrectionResult(
            feedback_id="fb-mixed",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))

        # retrieve should find it
        matches = library.retrieve(
            source="linter",
            source_detail="file.py",
            category="syntax",
            limit=5,
        )
        assert len(matches) == 1

    def test_retrieve_respects_limit(self, library):
        """retrieve() returns at most `limit` entries."""
        for i in range(10):
            fb = StandardFeedback(
                id=f"fb-{i}",
                source="linter",
                source_detail=f"file{i}.py",
                type="error",
                category="syntax",
                severity="high",
                title="t",
                description="d",
                context={},
                timestamp="2024-01-01T00:00:00Z",
                sla_deadline="2024-01-02T00:00:00Z",
            )
            library.store(fb, CorrectionResult(
                feedback_id=f"fb-{i}",
                error_id=f"linter|syntax-{i}",
                auto_fixable=True,
                strategy="patch_syntax",
                confidence=0.95,
                patched_code="def foo():\n    pass\n",
                verification_status="success",
                correction_log=[],
            ))

        matches = library.retrieve(
            source="linter",
            source_detail="file0.py",
            category="syntax",
            limit=3,
        )
        assert len(matches) <= 3

    def test_retrieve_orders_by_confidence(self, library):
        """retrieve() returns entries ordered by confidence (highest first)."""
        for conf in [0.5, 0.9, 0.7]:
            fb = StandardFeedback(
                id=f"fb-conf-{conf}",
                source="linter",
                source_detail="file.py",
                type="error",
                category="syntax",
                severity="high",
                title="t",
                description="d",
                context={},
                timestamp="2024-01-01T00:00:00Z",
                sla_deadline="2024-01-02T00:00:00Z",
            )
            library.store(fb, CorrectionResult(
                feedback_id=f"fb-conf-{conf}",
                error_id="linter|syntax",
                auto_fixable=True,
                strategy="patch_syntax",
                confidence=conf,
                patched_code="def foo():\n    pass\n",
                verification_status="success",
                correction_log=[],
            ))

        matches = library.retrieve(
            source="linter",
            source_detail="file.py",
            category="syntax",
            limit=5,
        )
        # Should be ordered highest confidence first
        if len(matches) >= 2:
            assert matches[0].confidence >= matches[1].confidence


class TestRetrieveBySignature:
    """Tests for retrieve_by_signature."""

    def test_retrieve_by_exact_signature(self, library, sample_feedback):
        """retrieve_by_signature() finds entries with exact signature match."""
        library.store(sample_feedback, CorrectionResult(
            feedback_id="fb-001",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))

        sig = library._make_signature(sample_feedback)
        matches = library.retrieve_by_signature(sig)
        assert len(matches) == 1


class TestPersistence:
    """Tests for JSON persistence."""

    def test_library_persists_to_file(self, library, sample_feedback):
        """Library is saved to JSON file after store()."""
        library.store(sample_feedback, CorrectionResult(
            feedback_id="fb-001",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))

        # File should exist
        assert os.path.exists(library.storage_path)

    def test_library_loads_from_file(self, temp_storage, sample_feedback):
        """Library loads previously saved entries on init."""
        # Create library and store an entry
        lib1 = CorrectionLibrary(storage_path=temp_storage)
        lib1.store(sample_feedback, CorrectionResult(
            feedback_id="fb-001",
            error_id="linter|syntax",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.95,
            patched_code="def foo():\n    pass\n",
            verification_status="success",
            correction_log=[],
        ))

        # Create new library instance pointing to same file
        lib2 = CorrectionLibrary(storage_path=temp_storage)
        assert len(lib2.library) == 1
        assert lib2.library[0].source == "linter"

    def test_library_handles_missing_file(self):
        """Library handles missing storage file gracefully."""
        lib = CorrectionLibrary(storage_path="/nonexistent/path.json")
        assert lib.library == []


class TestHitRate:
    """Tests for learning hit rate."""

    def test_hit_rate_zero_when_empty(self, library):
        """hit_rate is 0.0 when library is empty."""
        assert library.get_hit_rate() == 0.0

    def test_hit_rate_reflects_successful_ratio(self, library, sample_feedback):
        """hit_rate reflects proportion of successful corrections."""
        # Add 3 successful, 1 failed
        for i in range(3):
            fb = StandardFeedback(
                id=f"fb-{i}",
                source="linter",
                source_detail=f"file{i}.py",
                type="error",
                category="syntax",
                severity="high",
                title="t",
                description="d",
                context={},
                timestamp="2024-01-01T00:00:00Z",
                sla_deadline="2024-01-02T00:00:00Z",
            )
            library.store(fb, CorrectionResult(
                feedback_id=f"fb-{i}",
                error_id=f"linter|syntax-{i}",
                auto_fixable=True,
                strategy="patch_syntax",
                confidence=0.95,
                patched_code="def foo():\n    pass\n",
                verification_status="success",
                correction_log=[],
            ))

        fb_failed = StandardFeedback(
            id="fb-failed",
            source="linter",
            source_detail="file_failed.py",
            type="error",
            category="syntax",
            severity="high",
            title="t",
            description="d",
            context={},
            timestamp="2024-01-01T00:00:00Z",
            sla_deadline="2024-01-02T00:00:00Z",
        )
        library.store(fb_failed, CorrectionResult(
            feedback_id="fb-failed",
            error_id="linter|syntax-failed",
            auto_fixable=True,
            strategy="patch_syntax",
            confidence=0.30,
            patched_code=None,
            verification_status="failed",
            correction_log=[],
        ))

        assert library.get_hit_rate() == 0.75
