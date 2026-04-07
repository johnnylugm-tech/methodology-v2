#!/usr/bin/env python3
"""
Execution Logger — 從 SubagentResult 收集執行日誌
將 SubagentIsolator 的結構化輸出轉換為 BVS 可消費的格式

使用方式：
    from constitution.execution_logger import ExecutionLogger

    logger = ExecutionLogger(project_path)
    logs = logger.collect_from_sessions_spawn_log()
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

@dataclass
class ExecutionLogEntry:
    """標準化執行日誌"""
    timestamp: str
    phase: int
    role: str              # developer / reviewer / architect
    task: str              # e.g., "FR-01"
    session_id: str
    session_key: str
    status: str            # success / error / unable_to_proceed
    confidence: int        # 1-10
    citations: List[str]   # ["FR-01", "SRS.md#L23"]
    summary: str           # 50字內摘要
    duration_seconds: float
    error: Optional[str] = None
    artifacts_read: List[str] = field(default_factory=list)
    artifacts_produced: List[str] = field(default_factory=list)

class ExecutionLogger:
    """
    從各種來源收集執行日誌

    來源：
    1. .methodology/sessions_spawn.log — SubagentIsolator 的派遣日誌
    2. SubagentResult objects — 直接從 SubagentIsolator.results
    3. Phase execution records — Phase 執行的 metadata
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def collect_from_sessions_spawn_log(self) -> List[Dict[str, Any]]:
        """
        從 sessions_spawn.log 收集執行日誌
        sessions_spawn.log 格式：
        {"timestamp": "...", "role": "...", "task": "...", "session_id": "...", "status": "...", ...}
        """
        log_path = self.project_path / ".methodology" / "sessions_spawn.log"
        if not log_path.exists():
            return []

        entries = []
        for line in log_path.read_text().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                entry = json.loads(line)
                # 標準化格式
                entries.append({
                    "timestamp": entry.get("timestamp", ""),
                    "phase": self._infer_phase_from_task(entry.get("task", "")),
                    "role": entry.get("role", "unknown"),
                    "task": entry.get("task", ""),
                    "session_id": entry.get("session_id", ""),
                    "session_key": entry.get("session_key", entry.get("session_id", "")),
                    "status": entry.get("status", "unknown"),
                    "confidence": entry.get("confidence"),
                    "citations": entry.get("citations", []),
                    "summary": "",
                    "duration_seconds": entry.get("duration_seconds", 0),
                    "error": entry.get("error"),
                })
            except json.JSONDecodeError:
                continue

        return entries

    def collect_from_subagent_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        從 SubagentIsolator.results 收集（直接消費 SubagentResult）

        Args:
            results: SubagentIsolator.results (session_key -> SubagentResult)
        """
        entries = []
        for session_key, result in results.items():
            entry = {
                "timestamp": datetime.now().isoformat(),
                "phase": self._infer_phase_from_task(result.task if hasattr(result, 'task') else ""),
                "role": result.role.value if hasattr(result, 'role') else "unknown",
                "task": result.task if hasattr(result, 'task') else "",
                "session_id": session_key,
                "session_key": session_key,
                "status": result.status if hasattr(result, 'status') else "unknown",
                "confidence": result.confidence if hasattr(result, 'confidence') else 0,
                "citations": result.citations if hasattr(result, 'citations') else [],
                "summary": result.summary if hasattr(result, 'summary') else "",
                "duration_seconds": result.duration_seconds if hasattr(result, 'duration_seconds') else 0,
                "error": result.error if hasattr(result, 'error') else None,
            }
            entries.append(entry)
        return entries

    def _infer_phase_from_task(self, task: str) -> int:
        """從 task 描述推斷 Phase"""
        task_lower = task.lower()
        if "phase 1" in task_lower or "p1" in task_lower:
            return 1
        elif "phase 2" in task_lower or "p2" in task_lower:
            return 2
        elif "phase 3" in task_lower or "p3" in task_lower:
            return 3
        elif "phase 4" in task_lower or "p4" in task_lower:
            return 4
        return 1  # 預設 Phase 1

    def get_phase_context(self, phase: int) -> Dict[str, Any]:
        """取得指定 Phase 的執行上下文"""
        return {
            "phase": phase,
            "max_allowed_phase": phase,
            "parent_session_id": None,
            "review_iterations": 0,
            "estimated_duration": 3600,  # 預設 1 小時
        }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Execution Logger")
    parser.add_argument("--project-path", required=True, help="Project path")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    logger = ExecutionLogger(args.project_path)
    logs = logger.collect_from_sessions_spawn_log()

    output = {
        "total": len(logs),
        "logs": logs
    }

    if args.output:
        Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"Saved {len(logs)} entries to {args.output}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
