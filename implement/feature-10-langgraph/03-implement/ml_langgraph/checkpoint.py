"""
Checkpoint system for LangGraph workflow state persistence.

Provides CheckpointManager with pluggable storage backends (Memory, SQLite, FileSystem).
"""

import json
import os
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class CheckpointAlreadyExistsError(Exception):
    """Raised when attempting to save a checkpoint that already exists."""

    pass


class CheckpointNotFoundError(Exception):
    """Raised when a checkpoint ID is not found."""

    pass


class CheckpointBackend(ABC):
    """Abstract base class for checkpoint storage backends."""

    @abstractmethod
    def save(self, checkpoint_id: str, state: dict) -> None:
        """Save a checkpoint state."""
        pass

    @abstractmethod
    def load(self, checkpoint_id: str) -> dict:
        """Load a checkpoint state by ID."""
        pass

    @abstractmethod
    def list(self) -> list[dict]:
        """List all checkpoints with metadata."""
        pass

    @abstractmethod
    def delete(self, checkpoint_id: str) -> None:
        """Delete a checkpoint by ID."""
        pass

    @abstractmethod
    def exists(self, checkpoint_id: str) -> bool:
        """Check if a checkpoint exists."""
        pass


class MemoryCheckpointBackend(CheckpointBackend):
    """In-memory checkpoint storage backend (non-persistent)."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, dict] = {}

    def save(self, checkpoint_id: str, state: dict) -> None:
        if checkpoint_id in self._checkpoints:
            raise CheckpointAlreadyExistsError(f"Checkpoint '{checkpoint_id}' already exists")
        self._checkpoints[checkpoint_id] = {
            "id": checkpoint_id,
            "state": state,
            "created_at": datetime.now().isoformat(),
        }

    def load(self, checkpoint_id: str) -> dict:
        if checkpoint_id not in self._checkpoints:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")
        return self._checkpoints[checkpoint_id]["state"]

    def list(self) -> list[dict]:
        return sorted(
            self._checkpoints.values(),
            key=lambda x: x["created_at"],
            reverse=False,
        )

    def delete(self, checkpoint_id: str) -> None:
        if checkpoint_id not in self._checkpoints:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")
        del self._checkpoints[checkpoint_id]

    def exists(self, checkpoint_id: str) -> bool:
        return checkpoint_id in self._checkpoints


class SqliteCheckpointBackend(CheckpointBackend):
    """SQLite-based checkpoint storage backend (persistent)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at
            ON checkpoints(created_at DESC)
        """)
        conn.commit()

    def save(self, checkpoint_id: str, state: dict) -> None:
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        if existing is not None:
            raise CheckpointAlreadyExistsError(f"Checkpoint '{checkpoint_id}' already exists")
        state_json = json.dumps(state, default=str)
        created_at = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO checkpoints (id, state, created_at) VALUES (?, ?, ?)",
            (checkpoint_id, state_json, created_at),
        )
        conn.commit()

    def load(self, checkpoint_id: str) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT state FROM checkpoints WHERE id = ?", (checkpoint_id,)
        ).fetchone()
        if row is None:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")
        return json.loads(row["state"])

    def list(self) -> list[dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT id, created_at FROM checkpoints ORDER BY created_at DESC"
        ).fetchall()
        return [{"id": row["id"], "created_at": row["created_at"]} for row in rows]

    def delete(self, checkpoint_id: str) -> None:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM checkpoints WHERE id = ?", (checkpoint_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")

    def exists(self, checkpoint_id: str) -> bool:
        conn = self._get_conn()
        row = conn.execute("SELECT 1 FROM checkpoints WHERE id = ?", (checkpoint_id,)).fetchone()
        return row is not None

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None


class FileSystemCheckpointBackend(CheckpointBackend):
    """File system-based checkpoint storage backend (persistent, JSON files)."""

    def __init__(self, checkpoint_dir: str = "./checkpoints") -> None:
        self._checkpoint_dir = Path(checkpoint_dir)
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = self._checkpoint_dir / "_metadata.json"
        self._load_metadata()

    def _load_metadata(self) -> None:
        if self._metadata_file.exists():
            with open(self._metadata_file, "r") as f:
                self._metadata = json.load(f)
        else:
            self._metadata = {}

    def _save_metadata(self) -> None:
        with open(self._metadata_file, "w") as f:
            json.dump(self._metadata, f, indent=2)

    def _get_checkpoint_path(self, checkpoint_id: str) -> Path:
        safe_id = checkpoint_id.replace("/", "_").replace("\\", "_")
        return self._checkpoint_dir / f"{safe_id}.json"

    def save(self, checkpoint_id: str, state: dict) -> None:
        if checkpoint_id in self._metadata:
            raise CheckpointAlreadyExistsError(f"Checkpoint '{checkpoint_id}' already exists")
        checkpoint_path = self._get_checkpoint_path(checkpoint_id)
        created_at = datetime.now().isoformat()
        with open(checkpoint_path, "w") as f:
            json.dump(state, f, indent=2, default=str)
        self._metadata[checkpoint_id] = {
            "id": checkpoint_id,
            "created_at": created_at,
            "file": str(checkpoint_path),
        }
        self._save_metadata()

    def load(self, checkpoint_id: str) -> dict:
        if checkpoint_id not in self._metadata:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")
        checkpoint_path = Path(self._metadata[checkpoint_id]["file"])
        with open(checkpoint_path, "r") as f:
            return json.load(f)

    def list(self) -> list[dict]:
        return sorted(
            self._metadata.values(),
            key=lambda x: x["created_at"],
            reverse=False,
        )

    def delete(self, checkpoint_id: str) -> None:
        if checkpoint_id not in self._metadata:
            raise CheckpointNotFoundError(f"Checkpoint '{checkpoint_id}' not found")
        checkpoint_path = Path(self._metadata[checkpoint_id]["file"])
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        del self._metadata[checkpoint_id]
        self._save_metadata()

    def exists(self, checkpoint_id: str) -> bool:
        return checkpoint_id in self._metadata


class CheckpointManager:
    """
    Manages workflow state checkpoints with pluggable storage backends.

    Provides a unified interface for saving, loading, listing, and deleting
    workflow state snapshots across different storage implementations.

    Example:
        >>> backend = MemoryCheckpointBackend()
        >>> manager = CheckpointManager(backend)
        >>> manager.save("run-001", {"step": 1, "data": [1, 2, 3]})
        >>> state = manager.load("run-001")
        >>> manager.list_checkpoints()
        [{'id': 'run-001', 'created_at': '2024-01-01T00:00:00'}]
    """

    def __init__(self, storage_backend: CheckpointBackend) -> None:
        """
        Initialize CheckpointManager with a storage backend.

        Args:
            storage_backend: An implementation of CheckpointBackend
                           (MemoryCheckpointBackend, SqliteCheckpointBackend,
                            or FileSystemCheckpointBackend)
        """
        self._backend = storage_backend

    def save(self, checkpoint_id: str, state: dict) -> str:
        """
        Save a workflow state snapshot.

        Args:
            checkpoint_id: Unique identifier for this checkpoint.
                          If None, a UUID will be generated.
            state: Dictionary representing the workflow state to save.

        Returns:
            The checkpoint_id used for this save operation.

        Raises:
            CheckpointAlreadyExistsError: If checkpoint_id already exists.
        """
        if checkpoint_id is None:
            checkpoint_id = str(uuid.uuid4())
        self._backend.save(checkpoint_id, state)
        return checkpoint_id

    def load(self, checkpoint_id: str) -> dict:
        """
        Load a workflow state snapshot.

        Args:
            checkpoint_id: The unique identifier of the checkpoint to load.

        Returns:
            Dictionary representing the saved workflow state.

        Raises:
            CheckpointNotFoundError: If checkpoint_id does not exist.
        """
        return self._backend.load(checkpoint_id)

    def list_checkpoints(self) -> list[dict]:
        """
        List all checkpoints ordered by creation time (newest first).

        Returns:
            List of dictionaries containing checkpoint metadata.
            Each dict has at least 'id' and 'created_at' keys.
        """
        return self._backend.list()

    def delete(self, checkpoint_id: str) -> None:
        """
        Delete a checkpoint by ID.

        Args:
            checkpoint_id: The unique identifier of the checkpoint to delete.

        Raises:
            CheckpointNotFoundError: If checkpoint_id does not exist.
        """
        self._backend.delete(checkpoint_id)

    def get_latest(self) -> Optional[dict]:
        """
        Get the most recently created checkpoint.

        Returns:
            Dictionary with 'id' and 'state' keys, or None if no checkpoints exist.

        Raises:
            CheckpointNotFoundError: If no checkpoints exist.
        """
        checkpoints = self._backend.list()
        if not checkpoints:
            return None
        latest = checkpoints[-1]  # newest (last in ascending-sorted list)
        state = self._backend.load(latest["id"])
        return {"id": latest["id"], "state": state}

    def exists(self, checkpoint_id: str) -> bool:
        """
        Check if a checkpoint exists.

        Args:
            checkpoint_id: The unique identifier to check.

        Returns:
            True if checkpoint exists, False otherwise.
        """
        return self._backend.exists(checkpoint_id)

    def save_with_metadata(
        self,
        checkpoint_id: Optional[str],
        state: dict,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Save a checkpoint with additional metadata.

        Args:
            checkpoint_id: Unique identifier, or None to auto-generate.
            state: Workflow state dictionary.
            metadata: Optional metadata dict (workflow_name, step, tags, etc.)

        Returns:
            The checkpoint_id used.
        """
        if checkpoint_id is None:
            checkpoint_id = str(uuid.uuid4())
        full_state = {
            "state": state,
            "metadata": metadata or {},
        }
        self._backend.save(checkpoint_id, full_state)
        return checkpoint_id

    def load_with_metadata(self, checkpoint_id: str) -> dict:
        """
        Load a checkpoint and return full state including metadata.

        Args:
            checkpoint_id: The checkpoint ID to load.

        Returns:
            Full state dict with 'state' and 'metadata' keys.
        """
        return self._backend.load(checkpoint_id)
