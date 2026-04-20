#!/usr/bin/env python3
"""
engine.py - Risk Assessment Engine (Main Entry Point)
[FR-01, FR-02, FR-03, FR-04] Unified Risk Assessment Engine

整合 assessor, strategist, tracker 為單一引擎介面。
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from .assessor import RiskAssessor, RiskScorer
from .strategist import RiskStrategist
from .tracker import RiskTracker
from ..models.risk import Risk, RiskAssessmentResult
from ..models.enums import RiskStatus, RiskLevel


@dataclass
class DecisionGateResult:
    """Phase 7 Decision Gate 結果"""
    can_proceed: bool
    conditions: List[str]
    blockers: List[str]
    recommendations: List[str]
    assessed_at: datetime = field(default_factory=datetime.now)

    @property
    def status(self) -> str:
        if self.can_proceed and not self.blockers:
            return "PASS"
        elif self.conditions:
            return "CONDITIONAL_PASS"
        else:
            return "BLOCKED"


class RiskAssessmentEngine:
    """
    [FR-01, FR-02, FR-03, FR-04] 統一風險評估引擎

    提供單一介面給 Phase 6/7 使用。
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)

        # Initialize components
        self.assessor = RiskAssessor(str(project_root))
        self.scorer = RiskScorer()
        self.strategist = RiskStrategist()
        self.tracker = RiskTracker(str(project_root))

    def assess(self) -> RiskAssessmentResult:
        """
        [FR-01, FR-02] 執行完整風險評估

        1. 識別風險
        2. 評估風險
        3. 生成策略
        4. 保存到資料庫

        Returns:
            RiskAssessmentResult with all assessed risks
        """
        # 1. Identify and assess risks
        result = self.assessor.assess()

        # 2. Generate strategies for all risks
        result.risks = self.strategist.generate_all_plans(result.risks)

        # 3. Save to tracker
        for risk in result.risks:
            self.tracker.save_risk(risk)

        # 4. Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        # 5. Check constitution compliance
        result.constitution_compliant = self._check_constitution_compliance()

        return result

    def generate_strategies(self, risk_id: str) -> Optional[Risk]:
        """
        [FR-03] 為單一風險生成應對策略

        Args:
            risk_id: 風險 ID

        Returns:
            Updated risk with strategy, or None if not found
        """
        risk = self.tracker.load_risk(risk_id)
        if not risk:
            return None

        # Generate strategy
        risk.strategy = self.strategist.generate(risk)
        risk.mitigation_plan = self.strategist.generate_mitigation_plan(risk)
        risk.mitigation = self.strategist._summarize_plan(risk.mitigation_plan)

        # Save
        self.tracker.save_risk(risk)

        return risk

    def update_status(
        self,
        risk_id: str,
        new_status: RiskStatus,
        changed_by: str = "System",
        note: str = ""
    ) -> tuple:
        """
        [FR-04] 更新風險狀態

        Args:
            risk_id: 風險 ID
            new_status: 新狀態
            changed_by: 變更人
            note: 備註

        Returns:
            (success, message)
        """
        return self.tracker.update_status(risk_id, new_status, changed_by, note)

    def evaluate_gates(self) -> DecisionGateResult:
        """
        [FR-04] Phase 7 決策門評估

        評估是否可以進入下一個 Phase。

        Returns:
            DecisionGateResult with gate evaluation
        """
        risks = self.tracker.load_all_risks()

        blockers = []
        conditions = []
        recommendations = []

        # Check for critical/open risks
        critical_open = [r for r in risks if r.level == RiskLevel.CRITICAL and r.status == RiskStatus.OPEN]
        if critical_open:
            blockers.append(
                f"{len(critical_open)} CRITICAL risks remain OPEN: "
                f"{', '.join([r.id for r in critical_open])}"
            )

        # Check for high risks without mitigation
        high_unmitigated = [
            r for r in risks
            if r.level == RiskLevel.HIGH
            and r.status == RiskStatus.OPEN
            and not r.mitigation_plan.short_term
        ]
        if high_unmitigated:
            conditions.append(
                f"{len(high_unmitigated)} HIGH risks need mitigation plans"
            )

        # Check for stale risks (>30 days without update)
        stale_threshold = datetime.now().timestamp() - (30 * 24 * 60 * 60)
        stale_risks = [
            r for r in risks
            if r.status == RiskStatus.OPEN
            and r.updated_at.timestamp() < stale_threshold
        ]
        if stale_risks:
            recommendations.append(
                f"{len(stale_risks)} OPEN risks haven't been updated in 30+ days"
            )

        # Calculate overall health
        if risks:
            open_count = len([r for r in risks if r.status == RiskStatus.OPEN])
            closed_count = len([r for r in risks if r.status == RiskStatus.CLOSED])
            total = len(risks)

            resolution_rate = closed_count / total if total > 0 else 0

            if resolution_rate < 0.5 and open_count > 5:
                conditions.append(
                    f"Risk resolution rate is low ({resolution_rate:.0%}), "
                    f"consider dedicating resources to risk management"
                )

        # Can proceed if no blockers
        can_proceed = len(blockers) == 0

        return DecisionGateResult(
            can_proceed=can_proceed,
            conditions=conditions,
            blockers=blockers,
            recommendations=recommendations,
        )

    def get_risk_summary(self) -> Dict[str, Any]:
        """[FR-04] 獲取風險摘要"""
        risks = self.tracker.load_all_risks()

        return {
            "total": len(risks),
            "open": len([r for r in risks if r.status == RiskStatus.OPEN]),
            "mitigated": len([r for r in risks if r.status == RiskStatus.MITIGATED]),
            "accepted": len([r for r in risks if r.status == RiskStatus.ACCEPTED]),
            "closed": len([r for r in risks if r.status == RiskStatus.CLOSED]),
            "by_level": {
                "critical": len([r for r in risks if r.level == RiskLevel.CRITICAL]),
                "high": len([r for r in risks if r.level == RiskLevel.HIGH]),
                "medium": len([r for r in risks if r.level == RiskLevel.MEDIUM]),
                "low": len([r for r in risks if r.level == RiskLevel.LOW]),
            },
            "average_score": sum(r.score for r in risks) / len(risks) if risks else 0,
            "constitution_compliant": self._check_constitution_compliance(),
        }

    def _generate_recommendations(self, result: RiskAssessmentResult) -> List[str]:
        """根據評估結果生成建議"""
        recommendations = []

        if result.critical_count > 0:
            recommendations.append(
                f"CRITICAL attention needed: {result.critical_count} critical risks identified"
            )

        if result.average_score > 0.5:
            recommendations.append(
                f"Average risk score ({result.average_score:.2f}) is elevated, "
                f"consider additional mitigation efforts"
            )

        if result.open_count > 10:
            recommendations.append(
                f"High number of open risks ({result.open_count}), "
                f"prioritize resolution or escalation"
            )

        # Dimension-specific recommendations
        by_dimension = {}
        for risk in result.risks:
            dim = risk.dimension.value if hasattr(risk.dimension, 'value') else risk.dimension
            by_dimension[dim] = by_dimension.get(dim, 0) + 1

        for dim, count in by_dimension.items():
            if count > 5:
                recommendations.append(
                    f"Many {dim.upper()} risks ({count}), "
                    f"review processes for this dimension"
                )

        return recommendations

    def _check_constitution_compliance(self) -> bool:
        """檢查 Constitution 合規"""
        # Check required files exist
        required_files = [
            "RISK_ASSESSMENT.md",
            "RISK_REGISTER.md",
        ]

        for filename in required_files:
            if not (self.project_root / filename).exists():
                # Also check in docs/
                if not (self.project_root / "docs" / filename).exists():
                    return False

        # Check risk register has content
        register_path = self.project_root / "RISK_REGISTER.md"
        if register_path.exists():
            content = register_path.read_text()
            if "R-" not in content:
                return False  # No risk IDs found

        return True





