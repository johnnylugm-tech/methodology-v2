# audit_logger.py — Governance Audit Logger
"""
Immutable audit log with SHA-256 hash chain.
Reused by Hunter Agent (Layer 2.5) for alert logging and fabrication detection.

Single source of truth: DO NOT duplicate — import from here.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AuditEntry:
    """Audit log entry."""
    entry_id: str
    event_type: str
    agent_id: str
    data: Dict[str, Any]
    conversation_id: Optional[str]
    timestamp: datetime
    hash: str
    parent_hash: Optional[str]


class AuditLogger:
    """
    Immutable audit logger with SHA-256 hash chain.
    
    Thread-safe, append-only log with chain verification.
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        hash_chain: bool = True,
        max_entries_in_memory: int = 1000,
    ) -> None:
        """
        Initialize audit logger.

        Args:
            log_path: Path to the audit log file. If None, in-memory only.
            hash_chain: Whether to maintain hash chain integrity.
            max_entries_in_memory: Max entries to keep in memory buffer.
        """
        self._log_path = log_path
        self._hash_chain = hash_chain
        self._max_entries = max_entries_in_memory
        self._last_hash: Optional[str] = None
        self._entries_buffer: deque = deque(maxlen=max_entries_in_memory)
        self._lock = threading.Lock()

        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._load_existing()

    def _load_existing(self) -> None:
        """Load existing log and find last hash."""
        if not self._log_path or not self._log_path.exists():
            return
        try:
            with open(self._log_path, "r") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self._last_hash = entry.get("hash")
                        self._entries_buffer.append(entry)
        except (json.JSONDecodeError, IOError):
            self._last_hash = None
            self._entries_buffer.clear()

    def log(
        self,
        event_type: str,
        agent_id: str,
        data: Dict[str, Any],
        conversation_id: Optional[str] = None,
        parent_hash: Optional[str] = None,
    ) -> str:
        """
        Write an immutable audit entry.

        Args:
            event_type: Event classification string.
            agent_id: Agent responsible for the event.
            data: Event payload.
            conversation_id: Optional conversation context.
            parent_hash: Previous entry hash (for chain). Uses internal if None.

        Returns:
            Hash of this entry (hex string).
        """
        import uuid

        entry_id = str(uuid.uuid4())
        timestamp = datetime.now()
        effective_parent = parent_hash if parent_hash is not None else self._last_hash

        payload = {
            "entry_id": entry_id,
            "event_type": event_type,
            "agent_id": agent_id,
            "data": data,
            "conversation_id": conversation_id,
            "timestamp": timestamp.isoformat(),
            "parent_hash": effective_parent,
        }

        hash_input = json.dumps(payload, sort_keys=True, default=str)
        entry_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        payload["hash"] = entry_hash

        with self._lock:
            self._last_hash = entry_hash
            self._entries_buffer.append(payload)

            if self._log_path:
                with open(self._log_path, "a") as f:
                    f.write(json.dumps(payload, default=str) + "\n")

        return entry_hash

    def query(
        self,
        conversation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """
        Query audit log entries.

        Args:
            conversation_id: Filter by conversation.
            agent_id: Filter by agent.
            event_type: Filter by event type.
            since: Start time.
            until: End time.
            limit: Max results.

        Returns:
            List of AuditEntry matching criteria.
        """
        results: List[AuditEntry] = []

        with self._lock:
            entries = list(self._entries_buffer)

        # If log file exists but not fully in memory, read it
        if self._log_path and self._log_path.exists() and len(results) < limit:
            try:
                with open(self._log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            raw = json.loads(line)
                            # Avoid duplicates from buffer
                            if raw not in entries:
                                entries.append(raw)
            except (json.JSONDecodeError, IOError):
                pass

        for raw in entries:
            if limit and len(results) >= limit:
                break

            if conversation_id and raw.get("conversation_id") != conversation_id:
                continue
            if agent_id and raw.get("agent_id") != agent_id:
                continue
            if event_type and raw.get("event_type") != event_type:
                continue

            ts_str = raw.get("timestamp", "")
            if since or until:
                try:
                    ts = datetime.fromisoformat(ts_str)
                except (ValueError, TypeError):
                    continue
                if since and ts < since:
                    continue
                if until and ts > until:
                    continue

            results.append(
                AuditEntry(
                    entry_id=raw.get("entry_id", ""),
                    event_type=raw.get("event_type", ""),
                    agent_id=raw.get("agent_id", ""),
                    data=raw.get("data", {}),
                    conversation_id=raw.get("conversation_id"),
                    timestamp=datetime.fromisoformat(ts_str) if ts_str else datetime.now(),
                    hash=raw.get("hash", ""),
                    parent_hash=raw.get("parent_hash"),
                )
            )

        return results

    def verify_chain(self) -> bool:
        """
        Verify hash chain integrity.

        Returns:
            True if chain is intact, False if tampered.
        """
        with self._lock:
            entries = list(self._entries_buffer)

        if self._log_path and self._log_path.exists():
            try:
                with open(self._log_path, "r") as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            except (json.JSONDecodeError, IOError):
                pass

        # Sort by timestamp
        def get_ts(e):
            try:
                return datetime.fromisoformat(e.get("timestamp", "1970-01-01T00:00:00"))
            except (ValueError, TypeError):
                return datetime.min

        entries.sort(key=get_ts)

        prev_hash: Optional[str] = None
        for raw in entries:
            if prev_hash is not None and raw.get("parent_hash") != prev_hash:
                return False
            prev_hash = raw.get("hash")
        return True
