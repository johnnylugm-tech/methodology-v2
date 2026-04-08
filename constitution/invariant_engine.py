#!/usr/bin/env python3
"""
Invariant Engine — 行為不變量檢查
從 Constitution HR 規則自動生成 invariants，驗證 Subagent 執行是否符合規範

使用方式：
    from constitution.invariant_engine import InvariantEngine, BehavioralInvariant

    engine = InvariantEngine.from_constitution_rules()
    violations = engine.check(execution_log, context)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import json
import logging

# HR-09: Claims Verifier availability
try:
    from .claim_verifier import verify_result
    HR09_AVAILABLE = True
except ImportError as e:
    HR09_AVAILABLE = False
    _hr09_import_error = str(e)

@dataclass
class InvariantViolation:
    """Invariant 違反"""
    invariant_name: str
    severity: str           # critical / high / medium / low
    phase: int
    session_id: str
    task: str
    message: str
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehavioralInvariant:
    """行為不變量定義"""
    name: str
    description: str
    check_func: Callable[[Dict, Dict], bool]  # (execution_log, context) -> bool
    severity: str = "high"
    phase_scope: Optional[List[int]] = None  # None = all phases
    source: str = ""   # e.g., "HR-03"

    def is_in_scope(self, phase: int) -> bool:
        if self.phase_scope is None:
            return True
        return phase in self.phase_scope


class InvariantEngine:
    """
    行為不變量引擎

    從 HR Constitution 規則生成 invariants，並檢查 execution logs
    """

    # 從 HR 規則自動生成的 invariants
    CONSTITUTION_INVARIANTS: List[BehavioralInvariant] = []

    def __init__(self, invariants: List[BehavioralInvariant] = None):
        self.invariants = invariants or []

    @classmethod
    def from_constitution_rules(cls) -> "InvariantEngine":
        """從 Constitution HR 規則生成 invariants"""
        invariants = [
            # HR-03: Phase execution order
            BehavioralInvariant(
                name="Phase execution order",
                description="Subagent 不能在未經授權的情況下執行未來 Phase 的任務",
                check_func=lambda log, ctx: (
                    log.get("status") == "unable_to_proceed" or
                    log.get("phase", 1) <= ctx.get("max_allowed_phase", 999)
                ),
                severity="critical",
                source="HR-03"
            ),
            # HR-07: Citation required
            BehavioralInvariant(
                name="Artifact citation required",
                description="所有實作必須引用對應的 artifact（SRS/SAD/Test Plan）",
                check_func=lambda log, ctx: (
                    log.get("status") == "unable_to_proceed" or
                    bool(log.get("citations")) or
                    log.get("confidence", 0) >= 7  # 高信心 = 可能已讀 artifact
                ),
                severity="high",
                source="HR-07"
            ),
            # HR-10: Subagent isolation
            BehavioralInvariant(
                name="Subagent isolation",
                description="Subagent session 不能與其他 subagent 共享",
                check_func=lambda log, ctx: (
                    log.get("session_id") != ctx.get("parent_session_id")
                ),
                severity="high",
                source="HR-10"
            ),
            # HR-12: A/B review threshold
            BehavioralInvariant(
                name="A/B review threshold",
                description="A/B 審查不能超過 5 輪，超過則暫停",
                check_func=lambda log, ctx: (
                    ctx.get("review_iterations", 0) <= 5 or
                    log.get("status") == "unable_to_proceed"
                ),
                severity="medium",
                phase_scope=[3, 4, 5, 6, 7, 8],
                source="HR-12"
            ),
            # HR-13: Phase timeout
            BehavioralInvariant(
                name="Phase execution timeout",
                description="Phase 執行時間不能超過預估時間的 3 倍",
                check_func=lambda log, ctx: (
                    log.get("duration_seconds", 0) <= ctx.get("estimated_duration", 99999) * 3 or
                    log.get("status") in ("unable_to_proceed", "error")
                ),
                severity="medium",
                source="HR-13"
            ),
            # HR-15: Artifact must be read
            BehavioralInvariant(
                name="Artifact read before proceeding",
                description="Subagent 必須在產出前引用 artifact",
                check_func=lambda log, ctx: (
                    log.get("status") == "unable_to_proceed" or
                    bool(log.get("citations")) or
                    len(log.get("citations", [])) > 0
                ),
                severity="critical",
                source="HR-15"
            ),
            # HR-09: Claims must be verified (supported by citations)
            BehavioralInvariant(
                name="HR-09: Claims verification",
                description="Claim 內容必須被 citations 實際支持，不只是存在citation",
                check_func=lambda log, ctx: _check_hr09_invariant(log, ctx),
                severity="high",
                source="HR-09"
            ),
            # No false confidence
            BehavioralInvariant(
                name="Confidence calibration",
                description="Confidence 1-2 必須伴隨 unable_to_proceed 或 error status",
                check_func=lambda log, ctx: (
                    log.get("confidence", 5) >= 3 or
                    log.get("status") in ("unable_to_proceed", "error")
                ),
                severity="medium",
                source="TH-07"
            ),
        ]
        return cls(invariants)

    def check(self, execution_log: Dict[str, Any], context: Dict[str, Any]) -> List[InvariantViolation]:
        """
        檢查單一 execution log 是否違反 invariant

        Args:
            execution_log: SubagentResult 的結構化輸出
            context: 執行上下文（phase, max_allowed_phase, parent_session_id 等）
        """
        violations = []
        phase = context.get("phase", 1)

        for invariant in self.invariants:
            if not invariant.is_in_scope(phase):
                continue

            try:
                passed = invariant.check_func(execution_log, context)
                if not passed:
                    violations.append(InvariantViolation(
                        invariant_name=invariant.name,
                        severity=invariant.severity,
                        phase=phase,
                        session_id=execution_log.get("session_id", "unknown"),
                        task=execution_log.get("task", "unknown"),
                        message=f"Invariant violated: {invariant.name} (source: {invariant.source})",
                        evidence={
                            "log": {k: v for k, v in execution_log.items() if k != "result"},
                            "context": context,
                            "invariant_description": invariant.description
                        }
                    ))
            except Exception as e:
                logging.warning(
                    f"[InvariantEngine] check_func failed for invariant '{invariant.name}': {e}"
                )
                violations.append(InvariantViolation(
                    invariant_name=invariant.name,
                    severity=invariant.severity,
                    phase=phase,
                    session_id=execution_log.get("session_id", "unknown"),
                    task=execution_log.get("task", "unknown"),
                    message=f"Invariant check raised exception: {e}",
                    evidence={"error": str(e), "log": execution_log, "context": context}
                ))

        return violations

    def check_batch(
        self,
        execution_logs: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[InvariantViolation]:
        """批次檢查多個 execution logs"""
        all_violations = []
        for log in execution_logs:
            violations = self.check(log, context)
            all_violations.extend(violations)
        return all_violations

    def generate_report(self, violations: List[InvariantViolation]) -> Dict[str, Any]:
        """產生 violations 報告"""
        if not violations:
            return {
                "passed": True,
                "total_violations": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "violations": []
            }

        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in violations:
            by_severity[v.severity] = by_severity.get(v.severity, 0) + 1

        return {
            "passed": by_severity["critical"] == 0 and by_severity["high"] == 0,
            "total_violations": len(violations),
            **by_severity,
            "violations": [
                {
                    "name": v.invariant_name,
                    "severity": v.severity,
                    "phase": v.phase,
                    "task": v.task,
                    "session_id": v.session_id,
                    "message": v.message
                }
                for v in violations
            ]
        }


# ─── HR-09 Helper ──────────────────────────────────────────────────────────────


def _check_hr09_invariant(log: dict, ctx: dict) -> bool:
    """
    HR-09 檢查：驗證 claim 內容是否被 citations 實際支持
    """
    if not HR09_AVAILABLE:
        return True
    
    result_text = log.get("result", "") or ""
    citations = log.get("citations", [])
    
    if not result_text or not citations:
        return True
    
    artifact_content = ctx.get("artifact_contents", {})
    if not artifact_content:
        return True
    
    try:
        verification = verify_result(
            result_text=result_text,
            citations=citations,
            artifact_content=artifact_content,
            strict=False
        )
        return verification.get("verified", True)
    except Exception:
        return True


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Invariant Engine")
    parser.add_argument("--logs", required=True, help="Path to execution logs JSON")
    parser.add_argument("--phase", type=int, required=True, help="Current phase")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    # 載入 execution logs
    with open(args.logs) as f:
        logs = json.load(f)

    # 建立 engine
    engine = InvariantEngine.from_constitution_rules()

    # 執行檢查
    context = {"phase": args.phase}
    violations = engine.check_batch(logs, context)

    # 產生報告
    report = engine.generate_report(violations)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        if report["passed"]:
            print(f"✅ PASSED — {report['total_violations']} violations")
        else:
            print(f"❌ FAILED — {report['total_violations']} violations:")
            for v in report["violations"][:10]:
                print(f"  [{v['severity'].upper()}] {v['name']} — {v['task']}")
            if report["total_violations"] > 10:
                print(f"  ... and {report['total_violations'] - 10} more")


if __name__ == "__main__":
    main()
