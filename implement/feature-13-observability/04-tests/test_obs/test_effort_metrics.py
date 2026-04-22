"""Tests for EffortTracker using isolated temporary SQLite databases."""

import json
import tempfile
import time
import pytest
from pathlib import Path
from observability.effort_metrics import EffortTracker, EffortRecord


def _db_path():
    """Return path to an isolated temp SQLite file (delete=False so we can inspect)."""
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_path = f.name
    f.close()
    return db_path


# ------------------------------------------------------------------
# start / stop — basic timing
# ------------------------------------------------------------------

def test_start_stop_records_time():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("planner", "trace-abc")
        time.sleep(0.11)          # ~110 ms
        record = tracker.stop(effort_id)
        assert record.agent_id == "planner"
        assert record.trace_id == "trace-abc"
        assert record.time_spent_ms >= 100
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


def test_start_stop_returns_effort_record():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("coder", "trace-xyz")
        record = tracker.stop(effort_id)
        assert isinstance(record, EffortRecord)
        assert record.agent_id == "coder"
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# Iteration tracking
# ------------------------------------------------------------------

def test_increment_iteration():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("coder", "trace-xyz")
        tracker.increment_iteration(effort_id)
        tracker.increment_iteration(effort_id)
        tracker.increment_iteration(effort_id)
        record = tracker.stop(effort_id)
        assert record.iteration_count == 3
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# Calls tracking
# ------------------------------------------------------------------

def test_increment_calls():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("reviewer", "trace-r")
        tracker.increment_calls(effort_id)
        tracker.increment_calls(effort_id)
        record = tracker.stop(effort_id)
        assert record.calls_count == 2
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# Token tracking
# ------------------------------------------------------------------

def test_add_tokens():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("planner", "trace-t")
        tracker.add_tokens(effort_id, 1500)
        tracker.add_tokens(effort_id, 500)
        record = tracker.stop(effort_id)
        assert record.tokens_consumed == 2000
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# flush — records written to DB and queryable
# ------------------------------------------------------------------

def test_flush_inserts_to_db():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("planner", "trace-flush")
        time.sleep(0.05)
        record = tracker.stop(effort_id)
        tracker.flush()
        # After flush the buffer is empty; query by trace_id
        stored = tracker.query("trace-flush")
        assert len(stored) == 1
        assert stored[0].agent_id == "planner"
        assert stored[0].iteration_count == 0
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


def test_flush_multiple_records():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        ids = []
        for i in range(3):
            eid = tracker.start(f"agent-{i}", f"trace-{i}")
            tracker.increment_iteration(eid)
            tracker.stop(eid)
        tracker.flush()
        for i in range(3):
            rows = tracker.query(f"trace-{i}")
            assert len(rows) == 1
            assert rows[0].iteration_count == 1
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# record() — direct record insertion
# ------------------------------------------------------------------

def test_record_direct_insert():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        effort_id = tracker.start("planner", "trace-direct")
        rec = tracker.stop(effort_id)
        # Simulate a second record inserted via .record()
        extra = EffortRecord(
            trace_id="trace-manual",
            span_id="sp-manual",
            agent_id="manual-agent",
            timestamp="2026-04-22T10:00:00+08:00",
            time_spent_ms=42.0,
            tokens_consumed=100,
            iteration_count=5,
            calls_count=3,
            metadata={},
        )
        tracker.record(extra)
        tracker.flush()
        manual = tracker.query("trace-manual")
        assert len(manual) == 1
        assert manual[0].iteration_count == 5
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()


# ------------------------------------------------------------------
# Multiple concurrent effort IDs (sequential start/stop)
# ------------------------------------------------------------------

def test_multiple_effort_ids():
    db_path = _db_path()
    tracker = EffortTracker(db_path=db_path)
    try:
        ids = [tracker.start(f"a{i}", f"t{i}") for i in range(4)]
        for _id in ids:
            tracker.increment_iteration(_id)
        records = [tracker.stop(_id) for _id in ids]
        assert len(records) == 4
        assert all(r.iteration_count == 1 for r in records)
        Path(db_path).unlink(missing_ok=True)
    finally:
        tracker._timer.cancel()
