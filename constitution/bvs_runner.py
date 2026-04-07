#!/usr/bin/env python3
"""
BVS Runner — Behaviour Validation System 整合器
整合 InvariantEngine + ExecutionLogger + Constitution Runner

使用方式：
    from constitution.bvs_runner import BVSRunner

    runner = BVSRunner(project_path, phase=3)
    report = runner.run()
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import sys

# Handle relative imports when run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from constitution.invariant_engine import InvariantEngine, InvariantViolation
    from constitution.execution_logger import ExecutionLogger
else:
    from .invariant_engine import InvariantEngine, InvariantViolation
    from .execution_logger import ExecutionLogger

class BVSRunner:
    """
    Behaviour Validation System 整合器

    流程：
    1. 收集 execution logs（從 sessions_spawn.log）
    2. 執行 invariant 檢查
    3. 整合進 Constitution runner
    """

    def __init__(
        self,
        project_path: str,
        phase: int = 3,
        feedback_store: Any = None,  # Optional FeedbackStore for auto-submission
    ):
        self.project_path = Path(project_path)
        self.phase = phase
        self.logger = ExecutionLogger(project_path)
        self.engine = InvariantEngine.from_constitution_rules()
        self.feedback_store = feedback_store

    def _invariant_severity_to_feedback_severity(self, severity: str) -> str:
        """Map invariant severity to FeedbackSeverity string."""
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        return mapping.get(severity.lower(), "medium")

    def run(self) -> Dict[str, Any]:
        """
        執行完整的 BVS 檢查

        Returns:
            BVSReport {
                "passed": bool,
                "total_violations": int,
                "critical": int,
                "high": int,
                "medium": int,
                "violations": [...],
                "logs_analyzed": int
            }
        """
        # 1. 收集 logs
        logs = self.logger.collect_from_sessions_spawn_log()

        # 過濾出當前 Phase 的 logs
        phase_logs = [log for log in logs if log.get("phase") == self.phase]

        if not phase_logs:
            return {
                "passed": True,
                "total_violations": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "violations": [],
                "logs_analyzed": 0,
                "status": "no_logs_for_phase"
            }

        # 2. 取得上下文
        context = self.logger.get_phase_context(self.phase)

        # 3. 執行 invariant 檢查
        violations = self.engine.check_batch(phase_logs, context)

        # 4. 產生報告
        report = self.engine.generate_report(violations)
        report["logs_analyzed"] = len(phase_logs)
        report["phase"] = self.phase

        # === Auto-submit violations to FeedbackStore ===
        if self.feedback_store and report.get("violations"):
            try:
                from core.feedback import StandardFeedback, route_and_assign
                from datetime import datetime, timezone
                import uuid

                for v in report["violations"]:
                    fb = StandardFeedback(
                        id=f"bvs-{uuid.uuid4().hex[:12]}",
                        source="bvs",
                        source_detail=v.get("name", "unknown"),
                        type="violation",
                        category="quality",
                        severity=self._invariant_severity_to_feedback_severity(v.get("severity", "MEDIUM")),
                        title=f"BVS Violation: {v.get('name', 'unknown')}",
                        description=v.get("message", ""),
                        context={"phase": self.phase, "invariant": v},
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        sla_deadline=None,
                        status="pending",
                        assignee=None,
                        resolution=None,
                        verified_at=None,
                        related_feedbacks=[],
                        recurrence_count=0,
                        confidence=0.95,
                        tags=["bvs", "invariant", v.get("name", "unknown")],
                    )
                    self.feedback_store.add(fb)
                    team, deadline = route_and_assign(fb, store=self.feedback_store)
                    fb.assignee = team
                    fb.sla_deadline = deadline
            except Exception:
                # Don't let feedback failures break the BVS run
                pass

        return report

    def run_all_phases(self) -> Dict[str, Any]:
        """執行所有 Phase 的 BVS 檢查"""
        results = {}
        for phase in range(1, 9):
            runner = BVSRunner(str(self.project_path), phase=phase)
            results[f"phase_{phase}"] = runner.run()

        # 彙總
        total_violations = sum(r.get("total_violations", 0) for r in results.values())
        total_critical = sum(r.get("critical", 0) for r in results.values())

        return {
            "passed": total_critical == 0,
            "total_violations": total_violations,
            "phase_results": results
        }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="BVS Runner")
    parser.add_argument("--project-path", required=True, help="Project path")
    parser.add_argument("--phase", type=int, required=True, help="Phase to check")
    parser.add_argument("--all", action="store_true", help="Check all phases")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.all:
        runner = BVSRunner(args.project_path)
        report = runner.run_all_phases()
    else:
        runner = BVSRunner(args.project_path, phase=args.phase)
        report = runner.run()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["passed"]:
            print(f"✅ BVS PASSED — {report.get('total_violations', 0)} violations")
        else:
            print(f"❌ BVS FAILED — {report.get('total_violations', 0)} violations:")
            for phase_key, result in report.get("phase_results", {}).items():
                if result.get("total_violations", 0) > 0:
                    print(f"  {phase_key}: {result['total_violations']} violations")


if __name__ == "__main__":
    main()
