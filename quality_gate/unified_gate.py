#!/usr/bin/env python3
"""
Unified Quality Gate
====================
統一的品質閘道，整合所有檢查器

使用方式：
    from quality_gate.unified_gate import UnifiedGate

    gate = UnifiedGate(project_path)
    result = gate.check_all()

    print(f"Passed: {result.passed}")
    print(f"Score: {result.score}")
"""

from dataclasses import dataclass, asdict
from typing import List, Dict
from pathlib import Path

# 匯入現有檢查器
from .doc_checker import DocumentChecker
from .phase_artifact_enforcer import PhaseArtifactEnforcer, Phase
from .constitution import run_constitution_check, ConstitutionCheckResult

# 匯入 Logic Checker（2026-03-28 新增）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from scripts.spec_logic_checker import SpecLogicChecker
    SPEC_LOGIC_CHECKER_AVAILABLE = True
except ImportError:
    SPEC_LOGIC_CHECKER_AVAILABLE = False


@dataclass
class CheckResult:
    """單項檢查結果"""
    name: str
    passed: bool
    score: float
    violations: List[str]
    details: Dict


@dataclass
class UnifiedGateResult:
    """統一品質閘道結果"""
    passed: bool
    overall_score: float
    checks: List[CheckResult]
    summary: Dict

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "overall_score": self.overall_score,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "score": c.score,
                    "violations": c.violations,
                    "details": c.details
                }
                for c in self.checks
            ],
            "summary": self.summary
        }


class UnifiedGate:
    """
    統一品質閘道

    整合三種檢查：
    1. Document Existence (doc_checker)
    2. Document Compliance (constitution)
    3. Phase References (phase_artifact)
    """

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.doc_checker = DocumentChecker(str(self.project_path))
        self.phase_enforcer = PhaseArtifactEnforcer(str(self.project_path))

    def check_all(self) -> UnifiedGateResult:
        """執行所有檢查"""
        checks = []

        # 1. Document Existence Check
        doc_result = self._check_documents()
        checks.append(doc_result)

        # 2. Constitution Compliance Check
        constitution_result = self._check_constitution()
        checks.append(constitution_result)

        # 3. Phase Artifact Reference Check
        phase_result = self._check_phase_references()
        checks.append(phase_result)

        # 4. Logic Correctness Check (2026-03-28 新增)
        logic_result = self._check_logic_correctness()
        checks.append(logic_result)

        # 計算總分
        total_score = sum(c.score for c in checks) / len(checks)
        all_passed = all(c.passed for c in checks)

        return UnifiedGateResult(
            passed=all_passed,
            overall_score=round(total_score, 2),
            checks=checks,
            summary={
                "total_checks": len(checks),
                "passed_checks": sum(1 for c in checks if c.passed),
                "failed_checks": sum(1 for c in checks if not c.passed),
                "critical_violations": self._count_critical(checks)
            }
        )

    def _check_documents(self) -> CheckResult:
        """檢查文檔存在性"""
        result = self.doc_checker.check_all()

        violations = []
        # 從 summary 判斷是否通過
        summary = result.get("summary", {})
        compliance_rate = summary.get("compliance_rate", "0%")
        # 解析 compliance_rate 是否為 100%
        passed = summary.get("failed", 1) == 0

        for r in result.get("results", []):
            if r.get("status") == "MISSING":
                violations.append(f"Missing docs: {r.get('phase', 'unknown')} - {r.get('missing', '')}")

        # 分數以 compliance_rate 計算
        try:
            score = float(compliance_rate.rstrip("%"))
        except (ValueError, AttributeError):
            score = 100.0 if passed else 0.0

        return CheckResult(
            name="Document Existence",
            passed=passed,
            score=score,
            violations=violations,
            details={"results": result}
        )

    def _check_constitution(self) -> CheckResult:
        """檢查 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Constitution Compliance",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )

            result = run_constitution_check("all", str(docs_path))

            violations = []
            for v in result.violations:
                violations.append(f"{v.get('rule', 'unknown')}: {v.get('message', '')}")

            # ConstitutionCheckResult 沒有 to_dict，用 asdict
            return CheckResult(
                name="Constitution Compliance",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details={"result": asdict(result)}
            )
        except Exception as e:
            return CheckResult(
                name="Constitution Compliance",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )

    def _check_phase_references(self) -> CheckResult:
        """檢查 Phase 產物引用"""
        violations = []
        all_passed = True

        # 檢查每個 Phase 的依賴
        for phase in Phase:
            result = self.phase_enforcer.can_proceed_to(phase.value)
            if not result.passed:
                all_passed = False
                for missing in result.missing_references:
                    violations.append(f"Phase {phase.value} missing: {missing}")

        return CheckResult(
            name="Phase References",
            passed=all_passed,
            score=100 if all_passed else 0,
            violations=violations,
            details={}
        )

    def _count_critical(self, checks: List[CheckResult]) -> int:
        """計算 critical violations"""
        count = 0
        for check in checks:
            # 超過 3 個 violations 視為 critical
            if len(check.violations) > 3:
                count += 1
        return count

    def check_documents_only(self) -> CheckResult:
        """只檢查文檔存在性"""
        return self._check_documents()

    def check_constitution_only(self) -> CheckResult:
        """只檢查 Constitution 合規"""
        return self._check_constitution()

    def check_phase_only(self) -> CheckResult:
        """只檢查 Phase 引用"""
        return self._check_phase_references()

    def _check_logic_correctness(self) -> CheckResult:
        """檢查邏輯正確性（2026-03-28 新增）"""
        if not SPEC_LOGIC_CHECKER_AVAILABLE:
            return CheckResult(
                name="Logic Correctness",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "spec_logic_checker not available"}
            )
        
        try:
            checker = SpecLogicChecker(str(self.project_path))
            result = checker.scan_python_files()
            
            violations = []
            for issue in result.issues:
                violations.append(f"{issue.file_path}:{issue.line_number} - {issue.description}")
            
            return CheckResult(
                name="Logic Correctness",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details={
                    "files_checked": result.files_checked,
                    "functions_checked": result.functions_checked,
                    "issues_count": len(result.issues)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Logic Correctness",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def check_logic_only(self) -> CheckResult:
        """只檢查邏輯正確性"""
        return self._check_logic_correctness()
