"""
Tests for checkpoint.py (CheckpointManager + backends).

No langgraph dependency required.
"""

from __future__ import annotations

import json
import pathlib
import pytest
import tempfile
from unittest.mock import MagicMock

from ml_langgraph.checkpoint import (
    CheckpointAlreadyExistsError,
    CheckpointNotFoundError,
    CheckpointBackend,
    MemoryCheckpointBackend,
    SqliteCheckpointBackend,
    FileSystemCheckpointBackend,
    CheckpointManager,
)


# ─────────────────────────────────────────────────────────────────────────────
# MemoryCheckpointBackend Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMemoryCheckpointBackend:
    def test_save_and_load(self):
        backend = MemoryCheckpointBackend()
        state = {"step": 1, "data": [1, 2, 3]}
        backend.save("cp-001", state)
        loaded = backend.load("cp-001")
        assert loaded == state

    def test_save_duplicate_raises(self):
        backend = MemoryCheckpointBackend()
        backend.save("cp-dup", {"a": 1})
        with pytest.raises(CheckpointAlreadyExistsError):
            backend.save("cp-dup", {"b": 2})

    def test_load_not_found_raises(self):
        backend = MemoryCheckpointBackend()
        with pytest.raises(CheckpointNotFoundError):
            backend.load("nonexistent")

    def test_exists(self):
        backend = MemoryCheckpointBackend()
        backend.save("cp-exists", {"x": 1})
        assert backend.exists("cp-exists") is True
        assert backend.exists("cp-missing") is False

    def test_list_sorted_by_created_at(self):
        backend = MemoryCheckpointBackend()
        backend.save("first", {"order": 1})
        backend.save("second", {"order": 2})
        listed = backend.list()
        ids = [item["id"] for item in listed]
        assert ids == ["first", "second"]  # reverse chronological

    def test_delete(self):
        backend = MemoryCheckpointBackend()
        backend.save("cp-del", {"val": 1})
        assert backend.exists("cp-del") is True
        backend.delete("cp-del")
        assert backend.exists("cp-del") is False

    def test_delete_not_found_raises(self):
        backend = MemoryCheckpointBackend()
        with pytest.raises(CheckpointNotFoundError):
            backend.delete("nonexistent")


# ─────────────────────────────────────────────────────────────────────────────
# SqliteCheckpointBackend Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSqliteCheckpointBackend:
    def test_save_and_load(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        state = {"step": 2, "info": "test"}
        backend.save("sql-cp-001", state)
        loaded = backend.load("sql-cp-001")
        assert loaded == state

    def test_save_and_load_with_special_chars(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        state = {"text": "日本語 émoji 🎉"}
        backend.save("unicode-cp", state)
        loaded = backend.load("unicode-cp")
        assert loaded["text"] == "日本語 émoji 🎉"

    def test_exists(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        backend.save("sql-ex", {"val": 1})
        assert backend.exists("sql-ex") is True
        assert backend.exists("sql-no") is False

    def test_list(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        backend.save("sql-first", {"n": 1})
        backend.save("sql-second", {"n": 2})
        listed = backend.list()
        assert len(listed) == 2

    def test_delete(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        backend.save("sql-del", {"x": 9})
        backend.delete("sql-del")
        assert backend.exists("sql-del") is False

    def test_delete_not_found_raises(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        with pytest.raises(CheckpointNotFoundError):
            backend.delete("nonexistent")

    def test_save_duplicate_raises(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        backend.save("sql-dup", {"a": 1})
        with pytest.raises(CheckpointAlreadyExistsError):
            backend.save("sql-dup", {"b": 2})

    def test_close(self):
        backend = SqliteCheckpointBackend(db_path=":memory:")
        backend.close()
        # Should not raise; calling again is also safe
        backend.close()


# ─────────────────────────────────────────────────────────────────────────────
# FileSystemCheckpointBackend Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestFileSystemCheckpointBackend:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileSystemCheckpointBackend(checkpoint_dir=tmpdir)
            state = {"file": "test", "values": [1, 2]}
            backend.save("fs-cp-001", state)
            loaded = backend.load("fs-cp-001")
            assert loaded == state

    def test_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileSystemCheckpointBackend(checkpoint_dir=tmpdir)
            backend.save("fs-ex", {"ok": True})
            assert backend.exists("fs-ex") is True
            assert backend.exists("fs-no") is False

    def test_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileSystemCheckpointBackend(checkpoint_dir=tmpdir)
            backend.save("fs-a", {"a": 1})
            backend.save("fs-b", {"b": 2})
            listed = backend.list()
            assert len(listed) == 2

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileSystemCheckpointBackend(checkpoint_dir=tmpdir)
            backend.save("fs-del", {"x": 1})
            backend.delete("fs-del")
            assert backend.exists("fs-del") is False

    def test_save_duplicate_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = FileSystemCheckpointBackend(checkpoint_dir=tmpdir)
            backend.save("fs-dup", {"a": 1})
            with pytest.raises(CheckpointAlreadyExistsError):
                backend.save("fs-dup", {"b": 2})


# ─────────────────────────────────────────────────────────────────────────────
# CheckpointManager Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCheckpointManager:
    def test_save_auto_generates_id(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        state = {"step": 0}
        cp_id = manager.save(None, state)
        assert cp_id is not None
        assert len(cp_id) > 0

    def test_save_load_roundtrip(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        state = {"counter": 42, "items": ["a", "b"]}
        cp_id = manager.save("my-checkpoint", state)
        loaded = manager.load("my-checkpoint")
        assert loaded == state

    def test_get_latest(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        manager.save("first", {"n": 1})
        manager.save("second", {"n": 2})
        latest = manager.get_latest()
        assert latest["id"] == "second"
        assert latest["state"]["n"] == 2

    def test_get_latest_empty_returns_none(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        assert manager.get_latest() is None

    def test_exists(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        manager.save("ex-check", {"ok": True})
        assert manager.exists("ex-check") is True
        assert manager.exists("missing") is False

    def test_list_checkpoints(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        manager.save("l1", {"a": 1})
        manager.save("l2", {"b": 2})
        listed = manager.list_checkpoints()
        assert len(listed) == 2
        ids = [item["id"] for item in listed]
        assert ids == ["l1", "l2"]

    def test_delete(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        manager.save("to-delete", {"gone": True})
        manager.delete("to-delete")
        assert manager.exists("to-delete") is False

    def test_delete_not_found_raises(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        with pytest.raises(CheckpointNotFoundError):
            manager.delete("nonexistent")

    def test_save_with_metadata(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        manager.save_with_metadata(
            None, {"step": 1}, {"workflow": "test", "tags": ["unit"]}
        )
        latest = manager.get_latest()
        assert latest["state"]["metadata"]["workflow"] == "test"

    def test_load_not_found_raises(self):
        backend = MemoryCheckpointBackend()
        manager = CheckpointManager(backend)
        with pytest.raises(CheckpointNotFoundError):
            manager.load("does-not-exist")
