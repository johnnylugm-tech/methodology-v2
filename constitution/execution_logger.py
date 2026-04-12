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
        {"timestamp": "...", "role": "qa|architect|reviewer", "task": "...", "session_id": "...", ...}
        
        HR-10 規定：role 欄位必須是 qa / architect / review，禁止 developer / manager
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
        context = {
            "phase": phase,
            "max_allowed_phase": phase,
            "parent_session_id": None,
            "review_iterations": 0,
            "estimated_duration": 3600,  # 預設 1 小時
        }
        # 載入 artifact_contents（用於 HR-09 Claims 驗證）
        context["artifact_contents"] = self._load_artifacts_for_phase(phase)
        return context

    def _load_artifacts_for_phase(self, phase: int) -> Dict[str, str]:
        """
        根據 Phase 載入對應的 artifact 內容

        Phase 1: SRS.md
        Phase 2: SAD.md
        Phase 3-8: SRS.md + SAD.md + TEST_PLAN.md
        """
        artifacts = {}

        # 根據 Phase 決定要載入哪些 artifacts
        artifact_map = {
            1: ["01-requirements/SRS.md", "SRS.md"],
            2: ["02-architecture/SAD.md", "SAD.md"],
        }

        # Phase 3+ 載入更多 artifacts
        phase_artifacts = artifact_map.get(phase, [])
        if phase >= 3:
            phase_artifacts = [
                "01-requirements/SRS.md",
                "SRS.md",
                "02-architecture/SAD.md",
                "SAD.md",
                "03-test/TEST_PLAN.md",
                "TEST_PLAN.md",
            ]

        for artifact_path in phase_artifacts:
            full_path = self.project_path / artifact_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8")
                    artifacts[artifact_path] = content[:100000]  # 限制大小避免記憶體問題
                except Exception:
                    continue

        return artifacts


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
