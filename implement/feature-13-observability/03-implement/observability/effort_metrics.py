"""Effort tracker backed by SQLite for agent task instrumentation."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import threading
import uuid
import json
from typing import Optional


@dataclass
class EffortRecord:
    trace_id: str
    span_id: str
    agent_id: str
    timestamp: str  # ISO 8601
    time_spent_ms: float
    tokens_consumed: int
    iteration_count: int
    calls_count: int
    metadata: dict = field(default_factory=dict)


def _data_dir(db_path: Optional[str] = None) -> Path:
    if db_path:
        return Path(db_path)
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env) / "effort.db"
    # walk up from this file: .../observability/effort_metrics.py
    base = Path(__file__).resolve().parents[2] / "data"
    return base / "effort.db"


class EffortTracker:
    """Track per-agent effort with an SQLite backend and an in-memory buffer.

    A background timer flushes buffered records every 30 seconds.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = str(_data_dir(db_path))
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._cursor = self._conn.cursor()
        self._init_schema()
        self._lock = threading.RLock()
        self._buffer: list[EffortRecord] = []
        self._active: dict[str, datetime] = {}  # effort_id -> start_time
        self._stats: dict[str, dict] = {}  # effort_id -> running stats
        self._timer = threading.Timer(30.0, self._flush_timer)
        self._timer.daemon = True
        self._timer.start()

    def _init_schema(self) -> None:
        self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS effort_records ("
            "  trace_id TEXT, span_id TEXT, agent_id TEXT, timestamp TEXT,"
            "  time_spent_ms REAL, tokens_consumed INTEGER,"
            "  iteration_count INTEGER, calls_count INTEGER, metadata TEXT"
            ")"
        )
        self._cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_trace_id ON effort_records(trace_id)"
        )
        self._cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_agent_id ON effort_records(agent_id)"
        )
        self._conn.commit()

    def start(self, agent_id: str, trace_id: str = "") -> str:
        effort_id = str(uuid.uuid4())
        self._active[effort_id] = datetime.now()
        self._stats[effort_id] = {
            "agent_id": agent_id,
            "trace_id": trace_id if trace_id else agent_id,
            "span_id": "",
            "tokens_consumed": 0,
            "iteration_count": 0,
            "calls_count": 0,
            "metadata": {},
        }
        return effort_id

    def stop(self, effort_id: str) -> EffortRecord:
        start_time = self._active.pop(effort_id, None)
        stats = self._stats.pop(effort_id, {})
        if start_time is None:
            start_time = datetime.now()
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000.0
        record = EffortRecord(
            trace_id=stats.get("trace_id", ""),
            span_id=stats.get("span_id", ""),
            agent_id=stats.get("agent_id", ""),
            timestamp=datetime.now().isoformat(),
            time_spent_ms=elapsed_ms,
            tokens_consumed=stats.get("tokens_consumed", 0),
            iteration_count=stats.get("iteration_count", 0),
            calls_count=stats.get("calls_count", 0),
            metadata=stats.get("metadata", {}),
        )
        self._buffer.append(record)
        return record

    def increment_iteration(self, effort_id: str) -> None:
        s = self._stats.get(effort_id)
        if s is not None:
            s["iteration_count"] = s.get("iteration_count", 0) + 1

    def increment_calls(self, effort_id: str) -> None:
        s = self._stats.get(effort_id)
        if s is not None:
            s["calls_count"] = s.get("calls_count", 0) + 1

    def add_tokens(self, effort_id: str, count: int) -> None:
        s = self._stats.get(effort_id)
        if s is not None:
            s["tokens_consumed"] = s.get("tokens_consumed", 0) + count

    def record(self, record: EffortRecord) -> None:
        self._buffer.append(record)

    def query(self, trace_id: str) -> list[EffortRecord]:
        rows = self._cursor.execute(
            "SELECT * FROM effort_records WHERE trace_id = ?", (trace_id,)
        ).fetchall()
        cols = ["trace_id","span_id","agent_id","timestamp",
                "time_spent_ms","tokens_consumed","iteration_count","calls_count","metadata"]
        records = []
        for row in rows:
            d = dict(zip(cols, row))
            d["metadata"] = json.loads(d["metadata"]) if d["metadata"] else {}
            records.append(EffortRecord(**d))
        return records

    def flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            rows = []
            for rec in self._buffer:
                rows.append((
                    rec.trace_id, rec.span_id, rec.agent_id, rec.timestamp,
                    rec.time_spent_ms, rec.tokens_consumed,
                    rec.iteration_count, rec.calls_count,
                    json.dumps(rec.metadata),
                ))
            try:
                self._cursor.executemany(
                    "INSERT INTO effort_records VALUES (?,?,?,?,?,?,?,?,?)", rows
                )
                self._conn.commit()
            except Exception:
                import sys
                print("[EffortTracker] flush failed:", sys.exc_info()[1], file=sys.stderr)
            finally:
                self._buffer.clear()

    def _flush_timer(self) -> None:
        self.flush()
        with self._lock:
            self._timer = threading.Timer(30.0, self._flush_timer)
            self._timer.daemon = True
            self._timer.start()