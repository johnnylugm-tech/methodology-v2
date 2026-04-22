"""Tests for DecisionLogWriter and DecisionLogReader using temp directories."""

import pytest
import tempfile
from pathlib import Path
from observability.decision_log import (
    DecisionLogWriter,
    DecisionLogReader,
    DecisionLogEntry,
)


def _make_entry(
    trace_id="t1",
    span_id="s1",
    agent_id="planner",
    timestamp="2026-04-22T10:00:00+08:00",
    decision="proceed",
    reasoning="low risk",
    options_considered=None,
    chosen_action="proceed",
    uaf_score=0.85,
    risk_score=0.15,
    hitl_gate="pass",
    metadata=None,
):
    if options_considered is None:
        options_considered = ["proceed", "block"]
    if metadata is None:
        metadata = {"session": "test"}
    return DecisionLogEntry(
        trace_id=trace_id,
        span_id=span_id,
        agent_id=agent_id,
        timestamp=timestamp,
        decision=decision,
        reasoning=reasoning,
        options_considered=options_considered,
        chosen_action=chosen_action,
        uaf_score=uaf_score,
        risk_score=risk_score,
        hitl_gate=hitl_gate,
        metadata=metadata,
    )


# ------------------------------------------------------------------
# Round-trip
# ------------------------------------------------------------------

def test_write_and_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        reader = DecisionLogReader(data_dir=tmpdir)
        entry = _make_entry()
        path = writer.write(entry)
        assert path.name == "planner_0001.yaml"
        read_back = reader.read(path)
        assert read_back.decision == "proceed"
        assert read_back.uaf_score == 0.85
        assert read_back.hitl_gate == "pass"          # must be str
        assert read_back.agent_id == "planner"


# ------------------------------------------------------------------
# Sequence counter increments
# ------------------------------------------------------------------

def test_sequence_counter_increments():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        for i in range(3):
            entry = _make_entry(
                timestamp=f"2026-04-22T10:0{i}:00+08:00",
                decision=f"dec-{i}",
            )
            path = writer.write(entry)
        assert path.name == "planner_0003.yaml"


def test_sequence_counter_different_agents():
    """Different agents share no sequence counter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        for agent in ("planner", "coder", "planner"):
            entry = _make_entry(
                agent_id=agent,
                timestamp="2026-04-22T10:00:00+08:00",
            )
            writer.write(entry)
        # planner has entries _0001 and _0003; coder has _0002
        entries = list((Path(tmpdir) / "decision_logs" / "2026-04-22").iterdir())
        assert len(entries) == 3


# ------------------------------------------------------------------
# Query by date
# ------------------------------------------------------------------

def test_query_by_date():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        reader = DecisionLogReader(data_dir=tmpdir)
        for i, date in enumerate(["2026-04-22", "2026-04-22", "2026-04-23"]):
            writer.write(_make_entry(
                timestamp=f"{date}T10:0{i}:00+08:00",
                agent_id="planner",
                decision=f"dec-{i}",
            ))
        results = reader.query_by_date("2026-04-22")
        assert len(results) == 2
        assert all(e.agent_id == "planner" for e in results)


def test_query_by_date_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        reader = DecisionLogReader(data_dir=tmpdir)
        assert reader.query_by_date("2099-01-01") == []


# ------------------------------------------------------------------
# Query by agent
# ------------------------------------------------------------------

def test_query_by_agent():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        reader = DecisionLogReader(data_dir=tmpdir)
        for agent in ("planner", "coder", "planner"):
            writer.write(_make_entry(
                agent_id=agent,
                timestamp="2026-04-22T10:00:00+08:00",
                decision=f"dec-{agent}",
            ))
        results = reader.query_by_agent("planner")
        assert len(results) == 2
        assert all(e.agent_id == "planner" for e in results)


def test_query_by_agent_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        reader = DecisionLogReader(data_dir=tmpdir)
        assert reader.query_by_agent("nobody") == []


# ------------------------------------------------------------------
# Serialisation / field types
# ------------------------------------------------------------------

def test_hitl_gate_stays_str():
    """hitl_gate must round-trip as a plain string, not a bool."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        reader = DecisionLogReader(data_dir=tmpdir)
        entry = _make_entry(hitl_gate="pass")
        writer.write(entry)
        path = writer.write(entry)   # second write — planner_0002.yaml
        read_back = reader.read(path)
        assert read_back.hitl_gate == "pass"
        assert isinstance(read_back.hitl_gate, str)


def test_options_considered_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DecisionLogWriter(data_dir=tmpdir)
        reader = DecisionLogReader(data_dir=tmpdir)
        entry = _make_entry(options_considered=["proceed", "block", "review"])
        path = writer.write(entry)
        read_back = reader.read(path)
        assert read_back.options_considered == ["proceed", "block", "review"]
