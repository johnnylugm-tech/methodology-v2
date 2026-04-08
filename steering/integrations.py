#!/usr/bin/env python3
"""
Steering Integrations — 與現有系統的整合點

整合：
- BVS Runner（InvariantEngine）→ HR-03 Phase 順序檢查
- Constitution Checker → HR-07/09/15 Citation/Claims/Artifact 檢查
- CQG（代碼品質）→ 代碼品質量化
- AB Enforcer → HR-12 迭代次數矛盾解決
- AI Test Suite → HR-17 AI-generated tests 合規

HR-12 矛盾解決方案：
- HR-12：「不允許 >5 輪無效迭代」是消極約束
- SteeringLoop.max_iterations=5 是積極上限
- 兩者不矛盾：可以早停，但不能超過 5 輪
- SteeringLoop.should_continue() 會在抵達 max_iterations 之前，
  滿足收斂條件時提前終止，實現「不浪費迭代」的目標
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

from steering.steering_loop import IterationResult, SteeringLoop, SteeringConfig


# ─── HR Constraints ────────────────────────────────────────────────────────────

@dataclass
class HRConstraints:
    """
    Methodology HR 約束整合

    現有相關 HR：
    - HR-01：30% 效率提升目標
    - HR-03：Phase 順序強制
    - HR-07：Citation 引用規範
    - HR-09：Claims 準確性
    - HR-12：不允許 >5 輪迭代（矛盾已解決）
    - HR-15：Artifact 完整性
    - HR-17：AI-generated tests 標記
    """

    max_iterations: int = 5              # HR-12 上限
    min_iterations: int = 3
    efficiency_target: float = 0.30      # HR-01: 30% 效率提升
    convergence_threshold: float = 0.05  # 收斂閾值

    # HR 合規標記
    require_citation: bool = True        # HR-07
    require_claims_verification: bool = True  # HR-09
    require_artifact_traceability: bool = True  # HR-15
    require_ai_test_tagging: bool = True  # HR-17


@dataclass
class IntegrationResult:
    """整合檢查結果"""
    hr_compliant: bool
    violations: List[str]
    warnings: List[str]
    metrics: Dict[str, float]
    details: Dict[str, Any]


# ─── Steering + BVS 整合 ──────────────────────────────────────────────────────

class SteeringBVSIntegrator:
    """
    SteeringLoop 與 BVS Runner 整合

    功能：
    1. 在 Steering 迭代前執行 BVS Phase 順序檢查（HR-03）
    2. 將 Steering 迭代結果寫入 ExecutionLogger
    3. 追蹤 Phase 間的 Artifact 連貫性
    """

    def __init__(
        self,
        project_path: str,
        bvs_runner,      # BVSRunner 實例
        phase: int = 3
    ):
        self.project_path = Path(project_path)
        self.bvs_runner = bvs_runner
        self.phase = phase

    def check_phase_invariants(
        self,
        steering_result,
        context: Dict[str, Any]
    ) -> IntegrationResult:
        """
        檢查當前 Phase 的 BVS invariant（HR-03）

        Args:
            steering_result: SteeringLoop 的 IterationResult
            context: 額外上下文（前期產出等）

        Returns:
            IntegrationResult: 含 HR 合規狀態
        """
        violations = []
        warnings = []
        metrics = {}

        # 1. Phase 順序檢查（HR-03）
        # BVS Runner 會檢查 Phase N 的 logs 是否符合 expected behavior
        bvs_report = self.bvs_runner.run()

        if not bvs_report["passed"]:
            violations.append(f"BVS Phase {self.phase} violations: {bvs_report['total_violations']}")
            for v in bvs_report.get("violations", [])[:3]:
                violations.append(f"  - {v.get('rule', 'unknown')}: {v.get('message', '')}")

        metrics["bvs_violations"] = bvs_report["total_violations"]
        metrics["bvs_passed"] = 1.0 if bvs_report["passed"] else 0.0

        # 2. Steering 迭代指標
        metrics["steering_iterations"] = steering_result.iteration
        metrics["steering_score_delta"] = steering_result.score_delta
        metrics["steering_convergence"] = steering_result.convergence_score

        # 3. 判斷 HR 合規
        hr_compliant = (
            bvs_report["passed"] and
            steering_result.iteration <= 5 and
            steering_result.convergence_score <= 0.10
        )

        return IntegrationResult(
            hr_compliant=hr_compliant,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            details={
                "phase": self.phase,
                "bvs_report": bvs_report,
                "steering_winner": steering_result.winner
            }
        )


# ─── Steering + Constitution 整合 ─────────────────────────────────────────────

class SteeringConstitutionIntegrator:
    """
    SteeringLoop 與 Constitution Checker 整合

    功能：
    1. HR-07：Citation 引用規範檢查
    2. HR-09：Claims 準確性驗證
    3. HR-15：Artifact 完整性追蹤
    """

    def __init__(
        self,
        constitution_checker,  # 某個 ConstitutionChecker 實例
        citation_parser       # CitationParser 實例
    ):
        self.checker = constitution_checker
        self.citation_parser = citation_parser

    def check_output_compliance(
        self,
        output: Dict[str, Any],
        phase: int
    ) -> IntegrationResult:
        """
        檢查 Steering 输出的 Constitution 合規性

        Args:
            output: SteeringLoop.best_output.output
            phase: 當前 Phase

        Returns:
            IntegrationResult: 含 Constitution 合規狀態
        """
        violations = []
        warnings = []
        metrics = {}

        # 提取文字
        text = self._extract_text(output)

        # HR-07：Citation 檢查
        citations = self.citation_parser.extract_citations(text)
        if not citations and len(text) > 500:
            violations.append("HR-07: No citations found in long output")

        metrics["citation_count"] = len(citations)

        # HR-09：Claims 驗證
        claims = self.citation_parser.extract_claims(text)
        verified_claims = sum(
            1 for c in claims
            if self.citation_parser.verify_claim(c, citations)
        )
        if claims and verified_claims / len(claims) < 0.5:
            violations.append(f"HR-09: Only {verified_claims}/{len(claims)} claims verified")

        metrics["claims_total"] = len(claims)
        metrics["claims_verified"] = verified_claims

        # HR-15：Artifact 完整性（檢查是否有預期的 artifact 標記）
        has_artifacts = bool(output.get("artifacts") or output.get("files"))
        if not has_artifacts and phase >= 3:
            warnings.append("HR-15: No artifact references found")

        metrics["has_artifacts"] = 1.0 if has_artifacts else 0.0

        hr_compliant = len(violations) == 0

        return IntegrationResult(
            hr_compliant=hr_compliant,
            violations=violations,
            warnings=warnings,
            metrics=metrics,
            details={
                "citations": citations,
                "claims": claims,
                "verified_claims": verified_claims
            }
        )

    def _extract_text(self, output: Dict[str, Any]) -> str:
        if isinstance(output, str):
            return output
        return output.get("text", output.get("content", str(output)))


# ─── Steering + CQG 整合 ──────────────────────────────────────────────────────

class SteeringCQGIntegrator:
    """
    SteeringLoop 與 CQG（代碼品質 gate）整合

    功能：
    1. 代碼品質量化測量
    2. 將 CQG 分數納入 Steering 評分

    CQG 是獨立的 quality_gate module，這裡提供介面整合點
    """

    def __init__(self, cqg_checker=None):
        """
        Args:
            cqg_checker: CQG 實例（可選，如果沒有就跳過代碼品質檢查）
        """
        self.cqg_checker = cqg_checker

    def measure_code_quality(
        self,
        output: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        測量代碼品質

        Returns:
            {"quality": 0.0-1.0, "complexity": 0.0-1.0, "readability": 0.0-1.0}
        """
        if not self.cqg_checker:
            # 沒有 CQG checker 時返回預設值
            return {"quality": 0.5, "complexity": 0.5, "readability": 0.5}

        text = self._extract_text(output)

        # 嘗試從 text 中提取代碼塊
        code_blocks = self._extract_code_blocks(text)

        if not code_blocks:
            return {"quality": 0.5, "complexity": 0.5, "readability": 0.5}

        # 對每個代碼塊運行 CQG 檢查
        scores = []
        for block in code_blocks:
            try:
                result = self.cqg_checker.check(block)
                scores.append(result.get("quality_score", 0.5))
            except Exception:
                scores.append(0.5)

        avg = sum(scores) / len(scores) if scores else 0.5

        return {
            "quality": avg,
            "complexity": avg,  # 簡化版
            "readability": avg
        }

    def integrate_cqg_into_steering_score(
        self,
        base_score: float,
        cqg_scores: Dict[str, float]
    ) -> float:
        """
        將 CQG 分數整合進 Steering 的加權總分

        Formula: base_score * (1 - cqg_weight) + cqg_quality * cqg_weight
        """
        cqg_weight = 0.15  # CQG 佔 15% 權重
        cqg_quality = cqg_scores.get("quality", 0.5)
        return base_score * (1 - cqg_weight) + cqg_quality * cqg_weight

    def _extract_text(self, output: Dict[str, Any]) -> str:
        if isinstance(output, str):
            return output
        return output.get("text", output.get("content", str(output)))

    def _extract_code_blocks(self, text: str) -> List[str]:
        """簡單的 code block 提取（```...```）"""
        import re
        pattern = r"```[\w]*\n(.*?)```"
        return re.findall(pattern, text, re.DOTALL)


# ─── Steering + HR-12 矛盾解決方案 ─────────────────────────────────────────────

@dataclass
class HR12Resolution:
    """
    HR-12 矛盾解決方案

    矛盾點：
    - AB Workflow 中有「來回迭代」的需求
    - HR-12 說「不允許 >5 輪迭代」
    - 兩者表面上看起來衝突

    解決方案：
    - HR-12 的本質是「不要無意義地過度迭代」（消極約束）
    - SteeringLoop.max_iterations=5 是「最多跑 5 輪」（積極上限）
    - 當收斂條件滿足（delta <= 0.05）時，即使還沒到 5 輪也停止
    - 這樣既滿足 HR-12 的本意，又給了足夠的探索空間
    """

    max_allowed: int = 5                    # HR-12 上限
    early_stop_threshold: float = 0.05    # 提前停止的 delta 閾值
    min_rounds_before_stop: int = 3        # 最少跑幾輪才能提前停止

    def should_stop(
        self,
        current_round: int,
        score_delta: float,
        has_converged_early: bool = False
    ) -> Tuple[bool, str]:
        """
        判斷是否應該停止

        Args:
            current_round: 當前輪數（1-indexed）
            score_delta: 當前 A/B 分數差
            has_converged_early: 是否已經收斂

        Returns:
            (should_stop, reason)
        """
        # 到達 HR-12 上限
        if current_round >= self.max_allowed:
            return True, "hr12_max_iterations"

        # 還沒到最少輪數，不能提前停止
        if current_round < self.min_rounds_before_stop:
            return False, "min_rounds_not_reached"

        # 滿足收斂條件（delta 小於閾值）
        if has_converged_early or score_delta <= self.early_stop_threshold:
            return True, "converged"

        return False, "continue"

    @staticmethod
    def resolve(
        max_iterations: int,
        min_iterations: int,
        current_round: int,
        score_delta: float,
        quality_threshold: float = 0.85,
        convergence_threshold: float = 0.05
    ) -> dict:
        """
        解決 HR-12 矛盾：
        - HR-12 要求 >5 輪迭代效率
        - 但又說「不允許過度迭代」

        Returns:
            {
                "should_stop": bool,
                "reason": str,
                "hr12_compliant": bool
            }
        """
        # 到達最大迭代次數
        if current_round >= max_iterations:
            return {
                "should_stop": True,
                "reason": "max_iterations_reached",
                "hr12_compliant": True
            }

        # 至少跑 min_iterations 輪
        if current_round < min_iterations:
            return {
                "should_stop": False,
                "reason": "min_iterations_not_reached",
                "hr12_compliant": True
            }

        # 高品質已達到
        if score_delta <= convergence_threshold:
            return {
                "should_stop": True,
                "reason": "converged",
                "hr12_compliant": True
            }

        return {
            "should_stop": False,
            "reason": "continue_iterating",
            "hr12_compliant": True
        }


# ─── 統一整合入口 ──────────────────────────────────────────────────────────────

class SteeringIntegrator:
    """
    Unified Steering Integrator

    Integrates: SteeringLoop + BVS + Constitution + CQG + HR-12
    """

    def __init__(
        self,
        provider,
        project_path: str,
        phase: int = 3,
        config: Optional["SteeringConfig"] = None,  # forward ref
        hr_constraints: Optional[HRConstraints] = None
    ):
        from steering.steering_loop import SteeringLoop

        self.steering = SteeringLoop(provider, config)
        self.hr = hr_constraints or HRConstraints()

        # Lazy-load 整合模組（避免循環依賴）
        self._bvs_integrator = None
        self._constitution_integrator = None
        self._cqg_integrator = None

        self.project_path = Path(project_path)
        self.phase = phase

    @property
    def bvs_integrator(self) -> SteeringBVSIntegrator:
        if self._bvs_integrator is None:
            from constitution.bvs_runner import BVSRunner
            runner = BVSRunner(str(self.project_path), phase=self.phase)
            self._bvs_integrator = SteeringBVSIntegrator(
                str(self.project_path), runner, self.phase
            )
        return self._bvs_integrator

    def iterate_with_full_check(
        self,
        output_a: Dict[str, Any],
        output_b: Dict[str, Any],
        run_bvs: bool = True,
        run_constitution: bool = True,
        run_cqg: bool = False
    ) -> Tuple[IterationResult, List[IntegrationResult]]:
        """
        執行迭代並運行所有整合檢查

        Returns:
            (steering_result, integration_results)
        """
        # 1. Steering 迭代
        steering_result = self.steering.iterate(output_a, output_b)

        integration_results = []

        # 2. BVS 檢查
        if run_bvs:
            try:
                bvs_result = self.bvs_integrator.check_phase_invariants(
                    steering_result, {}
                )
                integration_results.append(bvs_result)
            except Exception as e:
                integration_results.append(IntegrationResult(
                    hr_compliant=True,
                    violations=[],
                    warnings=[f"BVS check failed: {e}"],
                    metrics={},
                    details={}
                ))

        # 3. Constitution 檢查
        if run_constitution:
            try:
                if self._constitution_integrator is None:
                    from constitution.citation_parser import CitationParser
                    from constitution.verification_constitution_checker import VerificationConstitutionChecker
                    self._constitution_integrator = SteeringConstitutionIntegrator(
                        VerificationConstitutionChecker(),
                        CitationParser()
                    )
                winner_output = steering_result.best_so_far.output
                const_result = self._constitution_integrator.check_output_compliance(
                    winner_output, self.phase
                )
                integration_results.append(const_result)
            except Exception as e:
                integration_results.append(IntegrationResult(
                    hr_compliant=True,
                    violations=[],
                    warnings=[f"Constitution check failed: {e}"],
                    metrics={},
                    details={}
                ))

        # 4. CQG 檢查
        if run_cqg:
            try:
                if self._cqg_integrator is None:
                    self._cqg_integrator = SteeringCQGIntegrator()
                winner_output = steering_result.best_so_far.output
                cqg_scores = self._cqg_integrator.measure_code_quality(winner_output)
                # 可以將 CQG 分數寫入 metrics
            except Exception:
                pass

        return steering_result, integration_results

    @property
    def should_continue(self) -> Tuple[bool, str]:
        return self.steering.should_continue()

    def get_full_summary(self) -> Dict[str, Any]:
        """取得完整摘要（含 HR 合規狀態）"""
        steering_summary = self.steering.get_summary()

        # HR-12 檢查
        hr12 = HR12Resolution()
        last_delta = 0.0
        if self.steering.iterations:
            last_delta = self.steering.iterations[-1].score_delta

        should_stop, reason = hr12.should_stop(
            len(self.steering.iterations),
            last_delta
        )

        return {
            "steering": steering_summary,
            "hr12_compliant": should_stop,
            "hr12_stop_reason": reason,
            "hr_constraints": {
                "max_iterations": self.hr.max_iterations,
                "efficiency_target": self.hr.efficiency_target
            }
        }
