"""Decision log writer and reader for agent decisions."""

from dataclasses import dataclass, field
from pathlib import Path
import os
import asyncio
from typing import Optional
import yaml


@dataclass
class DecisionLogEntry:
    trace_id: str
    span_id: str
    agent_id: str
    timestamp: str  # ISO 8601
    decision: str
    reasoning: str
    options_considered: list
    chosen_action: str
    uaf_score: float
    risk_score: float
    hitl_gate: str
    metadata: dict = field(default_factory=dict)


def _data_dir(data_dir: Optional[str] = None) -> Path:
    if data_dir:
        return Path(data_dir)
    env = os.environ.get("DATA_DIR")
    if env:
        return Path(env)
    # walk up from this file: .../observability/decision_log.py
    return Path(__file__).resolve().parents[2] / "data"


class DecisionLogWriter:
    """Synchronous and async writer for decision log entries.

    Sequence counters are kept in-memory per (agent_id, date) pair.
    If a counter is not in-memory, we scan the directory to find the
    highest existing sequence number for that (agent_id, date).
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = _data_dir(data_dir)
        # in-memory counters: key = (agent_id, date_str)
        self._counters: dict[tuple[str, str], int] = {}

    def _resolve_path(self, entry: DecisionLogEntry) -> Path:
        date_str = entry.timestamp[:10]  # "YYYY-MM-DD"
        key = (entry.agent_id, date_str)

        if key not in self._counters:
            # scan directory to find max seq for this agent/date
            seq = 1
            log_dir = self._data_dir / "decision_logs" / date_str
            if log_dir.is_dir():
                for p in log_dir.iterdir():
                    if p.name.startswith(f"{entry.agent_id}_") and p.suffix == ".yaml":
                        try:
                            s = int(p.stem.split("_")[1])
                            if s >= seq:
                                seq = s + 1
                        except (ValueError, IndexError):
                            pass
            self._counters[key] = seq

        seq = self._counters[key]
        self._counters[key] = seq + 1
        filename = f"{entry.agent_id}_{seq:04d}.yaml"
        return self._data_dir / "decision_logs" / date_str / filename

    def _serialize(self, entry: DecisionLogEntry) -> str:
        return yaml.dump(entry.__dict__, default_flow_style=False, sort_keys=False)

    def write(self, entry: DecisionLogEntry) -> Path:
        path = self._resolve_path(entry)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._serialize(entry), encoding="utf-8")
        return path

    def write_async(self, entry: DecisionLogEntry) -> asyncio.Task:
        return asyncio.create_task(self._async_write(entry))

    async def _async_write(self, entry: DecisionLogEntry) -> Path:
        return self.write(entry)

    def flush(self) -> None:
        pass  # future extension


class DecisionLogReader:
    """Read and query decision log entries."""

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = _data_dir(data_dir)

    def read(self, path: Path) -> DecisionLogEntry:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return DecisionLogEntry(**data)

    def query_by_date(self, date: str) -> list[DecisionLogEntry]:
        """Return all decision log entries for a given date string (YYYY-MM-DD)."""
        entries: list[DecisionLogEntry] = []
        log_dir = self._data_dir / "decision_logs" / date
        if not log_dir.is_dir():
            return entries
        for p in log_dir.iterdir():
            if p.suffix == ".yaml":
                try:
                    entries.append(self.read(p))
                except Exception:
                    pass
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def query_by_agent(self, agent_id: str) -> list[DecisionLogEntry]:
        """Scan all date directories and return entries for the given agent_id."""
        entries: list[DecisionLogEntry] = []
        logs_root = self._data_dir / "decision_logs"
        if not logs_root.is_dir():
            return entries
        for date_dir in logs_root.iterdir():
            if not date_dir.is_dir():
                continue
            for p in date_dir.iterdir():
                if p.suffix != ".yaml":
                    continue
                if p.stem.startswith(f"{agent_id}_"):
                    try:
                        entries.append(self.read(p))
                    except Exception:
                        pass
        entries.sort(key=lambda e: e.timestamp)
        return entries