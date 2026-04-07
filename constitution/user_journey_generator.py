#!/usr/bin/env python3
"""
User Journey Generator — 從 HR rules 和 execution logs 自動生成 user journey 測試

使用方式：
    from constitution.user_journey_generator import UserJourneyGenerator, UserJourneyTest

    generator = UserJourneyGenerator()
    journeys = generator.generate(phase=3, execution_log=logs)
    for j in journeys:
        print(f"{j.name}: {j.description}")
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .invariant_engine import InvariantEngine


@dataclass
class UserJourneyTest:
    """User journey 測試案例"""
    name: str
    description: str
    phase: int
    steps: List[str]
    expected_outcome: str
    is_edge_case: bool = False
    hr_rules_applied: List[str] = field(default_factory=list)


class UserJourneyGenerator:
    """
    從 HR rules 和 execution logs 自動生成 user journey 測試。
    """

    def __init__(self):
        self.invariant_engine = InvariantEngine.from_constitution_rules()
        self.edge_case_templates = self._load_edge_case_templates()

    def generate(self, phase: int, execution_log: Optional[List[Dict[str, Any]]] = None) -> List[UserJourneyTest]:
        """
        生成 user journey 測試案例。

        Args:
            phase: Phase number (1-8)
            execution_log: 實際執行的路徑日誌（用於基於實際路徑生成）
        """
        journeys = []

        # 1. 從 HR rules 生成標準 journey
        hr_journeys = self._generate_hr_journeys(phase)
        journeys.extend(hr_journeys)

        # 2. 從 execution log 生成路徑 journey（如果有的話）
        if execution_log:
            path_journeys = self._generate_from_paths(phase, execution_log)
            journeys.extend(path_journeys)

        # 3. 生成 edge cases
        edge_cases = self._generate_edge_cases(phase)
        journeys.extend(edge_cases)

        return journeys

    def _generate_hr_journeys(self, phase: int) -> List[UserJourneyTest]:
        """從 HR rules 生成標準 journey。"""
        journeys = []
        invariants = self.invariant_engine.invariants

        for inv in invariants:
            # Check if invariant applies to this phase via phase_scope
            if not inv.is_in_scope(phase):
                continue

            journey = UserJourneyTest(
                name=f"hr_{inv.source}_{inv.name.replace(' ', '_').lower()}",
                description=f"Validates {inv.source}: {inv.description}",
                phase=phase,
                steps=[
                    f"Execute Phase {phase}",
                    f"Verify {inv.name}",
                    f"Check {inv.description}",
                ],
                expected_outcome=f"{inv.source} constraint satisfied",
                is_edge_case=False,
                hr_rules_applied=[inv.source],
            )
            journeys.append(journey)

        return journeys

    def _generate_from_paths(self, phase: int, execution_log: List[Dict[str, Any]]) -> List[UserJourneyTest]:
        """從 execution log 提取路徑並生成測試。"""
        journeys = []

        # 提取 phase 相關的執行步驟
        phase_steps = [e for e in execution_log if e.get("phase") == phase]

        if phase_steps:
            journey = UserJourneyTest(
                name=f"path_phase_{phase}",
                description=f"Actual execution path for Phase {phase}",
                phase=phase,
                steps=[s.get("action", "") for s in phase_steps],
                expected_outcome="All steps executed successfully",
                is_edge_case=False,
                hr_rules_applied=[],
            )
            journeys.append(journey)

        return journeys

    def _generate_edge_cases(self, phase: int) -> List[UserJourneyTest]:
        """自動化生成 edge cases。"""
        edge_cases = []

        # Edge case templates 基於 HR rules
        templates = self.edge_case_templates.get(phase, [])

        for template in templates:
            journey = UserJourneyTest(
                name=template["name"],
                description=template["description"],
                phase=phase,
                steps=template["steps"],
                expected_outcome=template["expected"],
                is_edge_case=True,
                hr_rules_applied=template.get("hr_rules", []),
            )
            edge_cases.append(journey)

        # 通用 edge cases（所有 Phase）
        universal = self._get_universal_edge_cases(phase)
        edge_cases.extend(universal)

        return edge_cases

    def _load_edge_case_templates(self) -> Dict[int, List[Dict[str, Any]]]:
        """載入 edge case 模板。"""
        return {
            1: [
                {
                    "name": "phase_skip_attempt",
                    "description": "嘗試跳過 Phase 1 直接進入 Phase 2",
                    "steps": [
                        "Attempt to set FSM state to ACTIVE for Phase 2",
                        "Verify FSM rejects (Phase 1 not completed)",
                    ],
                    "expected": "FSM blocks transition — HR-03",
                    "hr_rules": ["HR-03", "HR-04"],
                },
            ],
            2: [
                {
                    "name": "missing_srs_citation",
                    "description": "Claims 沒有 citation",
                    "steps": [
                        "Generate claims from SRS",
                        "Attempt verification without citations",
                    ],
                    "expected": "HR-07 violation raised",
                    "hr_rules": ["HR-07"],
                },
            ],
            3: [
                {
                    "name": "self_review_attempt",
                    "description": "嘗試自己寫自己審（同一 Agent）",
                    "steps": [
                        "Set HybridWorkflow mode=OFF",
                        "Run Phase 3 with single agent",
                    ],
                    "expected": "HR-01 violation — self-review not allowed",
                    "hr_rules": ["HR-01"],
                },
            ],
            4: [
                {
                    "name": "fr_test_coverage_mismatch",
                    "description": "FR 覆蓋率 < 90%",
                    "steps": [
                        "Run test generation",
                        "Check FR coverage",
                        "If FR coverage < 90%: trigger TH-17 violation",
                    ],
                    "expected": "TH-17: FR↔test ≥ 90%",
                    "hr_rules": ["TH-17", "HR-11"],
                },
                {
                    "name": "test_environment_mismatch",
                    "description": "Test 在 dev 環境通過但 staging 失敗",
                    "steps": [
                        "Run tests in staging environment",
                        "Compare results with dev",
                    ],
                    "expected": "HR-15: artifact 追蹤完整性問題",
                    "hr_rules": ["HR-15"],
                },
            ],
            5: [
                {
                    "name": "verification_method_invalid",
                    "description": "驗證方法不是 specification 中的方法",
                    "steps": [
                        "Check TEST_RESULTS against TEST_PLAN",
                        "Compare verification methods",
                    ],
                    "expected": "HR-09: claims not verified by correct method",
                    "hr_rules": ["HR-09", "TH-02"],
                },
                {
                    "name": "test_evidence_insufficient",
                    "description": "Evidence 不夠嚴謹（截圖未標記時間戳）",
                    "steps": [
                        "Review evidence in TEST_RESULTS",
                        "Check timestamp and traceability",
                    ],
                    "expected": "Constitution verification fails",
                    "hr_rules": ["TH-02", "HR-04"],
                },
            ],
            6: [
                {
                    "name": "quality_metrics_below_threshold",
                    "description": "Maintainability < 70% or Security < 100%",
                    "steps": [
                        "Run quality_report generation",
                        "Check metrics against thresholds",
                    ],
                    "expected": "TH-02: Constitution ≥ 80% fails",
                    "hr_rules": ["TH-02", "HR-04"],
                },
            ],
            7: [
                {
                    "name": "risk_not_mitigated",
                    "description": "Risk register 有項目狀態仍為 Open",
                    "steps": [
                        "Review RISK_REGISTER",
                        "Check all risks have mitigation",
                    ],
                    "expected": "HR-15: artifact completeness issue",
                    "hr_rules": ["HR-15", "HR-05"],
                },
                {
                    "name": "risk_threshold_breached",
                    "description": "Risk impact > threshold 但未更新狀態",
                    "steps": [
                        "Compare risk impact vs threshold",
                        "Check status update timestamp",
                    ],
                    "expected": "HR-13: Phase timeout risk",
                    "hr_rules": ["HR-13", "HR-05"],
                },
            ],
            8: [
                {
                    "name": "config_drift",
                    "description": "配置文件與 SPEC.md 不一致",
                    "steps": [
                        "Compare CONFIG_RECORDS with SPEC.md",
                        "Check version alignment",
                    ],
                    "expected": "HR-16: config vs implementation mismatch",
                    "hr_rules": ["HR-16", "HR-15"],
                },
                {
                    "name": "deployment_procedure_unverified",
                    "description": "部署步驟未經實際驗證",
                    "steps": [
                        "Check deployment documentation",
                        "Verify against CONFIG_RECORDS",
                    ],
                    "expected": "TH-08: deployment procedure incomplete",
                    "hr_rules": ["TH-08", "HR-08"],
                },
            ],
        }

    def _get_universal_edge_cases(self, phase: int) -> List[UserJourneyTest]:
        """所有 Phase 都適用的通用 edge cases。"""
        return [
            UserJourneyTest(
                name="iteration_overflow",
                description="超過 5 輪迭代",
                phase=phase,
                steps=[
                    f"Run Phase {phase}",
                    "Iterate 6 times without convergence",
                ],
                expected_outcome="HR-12 triggers PAUSE state",
                is_edge_case=True,
                hr_rules_applied=["HR-12"],
            ),
            UserJourneyTest(
                name="timeout_exceeded",
                description="Phase 執行時間超過 3x 預估",
                phase=phase,
                steps=[
                    f"Run Phase {phase}",
                    "Simulate timeout",
                ],
                expected_outcome="HR-13 triggers PAUSE state",
                is_edge_case=True,
                hr_rules_applied=["HR-13"],
            ),
        ]


# ─── CLI ────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="User Journey Generator")
    parser.add_argument("--phase", type=int, required=True, help="Phase number (1-8)")
    parser.add_argument("--log", help="Path to execution log JSON (optional)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    # 載入 execution log（如果有的話）
    execution_log = None
    if args.log:
        with open(args.log) as f:
            execution_log = json.load(f)

    # 生成 journeys
    generator = UserJourneyGenerator()
    journeys = generator.generate(phase=args.phase, execution_log=execution_log)

    if args.json:
        output = [
            {
                "name": j.name,
                "description": j.description,
                "phase": j.phase,
                "steps": j.steps,
                "expected_outcome": j.expected_outcome,
                "is_edge_case": j.is_edge_case,
                "hr_rules_applied": j.hr_rules_applied,
            }
            for j in journeys
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"=== Phase {args.phase} User Journeys ===\n")
        for j in journeys:
            ec = "[EDGE CASE]" if j.is_edge_case else "[STANDARD]"
            print(f"{ec} {j.name}")
            print(f"  Description: {j.description}")
            print(f"  Steps:")
            for step in j.steps:
                print(f"    - {step}")
            print(f"  Expected: {j.expected_outcome}")
            print(f"  HR Rules: {j.hr_rules_applied}")
            print()


if __name__ == "__main__":
    main()
