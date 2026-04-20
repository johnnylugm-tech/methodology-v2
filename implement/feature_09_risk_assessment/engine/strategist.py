#!/usr/bin/env python3
"""
strategist.py - Risk Response Strategy Generator
[FR-03] Generate risk mitigation strategies
"""

from typing import List, Optional
from datetime import datetime

from ..models.risk import Risk, MitigationPlan
from ..models.enums import StrategyType, RiskLevel


class RiskStrategist:
    """
    [FR-03] Risk response strategy generator

    Generates mitigation plans based on risk score and dimension.
    """

    STRATEGY_THRESHOLDS = {
        StrategyType.AVOID: 0.6,   # Score > 0.6 → Avoid
        StrategyType.MITIGATE: 0.3,  # Score 0.3-0.6 → Mitigate
        StrategyType.TRANSFER: 0.3,  # Score 0.3-0.6 → Transfer (alternative)
        StrategyType.ACCEPT: 0.0,   # Score < 0.3 → Accept
    }

    def generate(self, risk: Risk) -> StrategyType:
        """[FR-03] 根據分數選擇策略"""
        if risk.score > self.STRATEGY_THRESHOLDS[StrategyType.AVOID]:
            return StrategyType.AVOID
        elif risk.score >= self.STRATEGY_THRESHOLDS[StrategyType.MITIGATE]:
            # For MITIGATE vs TRANSFER, prefer MITIGATE for internal risks
            if risk.dimension.value in ["technical", "operational"]:
                return StrategyType.MITIGATE
            else:
                return StrategyType.TRANSFER
        else:
            return StrategyType.ACCEPT

    def generate_mitigation_plan(
        self,
        risk: Risk,
        context: Optional[str] = None
    ) -> MitigationPlan:
        """
        [FR-03] 生成完整的緩解措施計劃

        Generates:
        - Immediate actions (within 24h)
        - Short-term actions (within 1 week)
        - Long-term actions (within 1 month)
        - Fallback plan
        """
        plan = MitigationPlan()

        # Build context-aware actions
        dim_context = self._get_dimension_context(risk)
        level_context = self._get_level_context(risk)

        # Immediate actions (24h)
        plan.immediate = [
            f"Document risk in RISK_REGISTER: {risk.id}",
            f"Notify {risk.owner or 'project owner'} of {risk.title}",
            f"Assess current exposure and immediate blast radius",
        ]

        if risk.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            plan.immediate.append("Activate incident response if applicable")
            plan.immediate.append("Prepare communication to stakeholders")

        # Short-term actions (1 week)
        plan.short_term = [
            f"Conduct detailed analysis of {dim_context}",
            f"Develop remediation plan for {risk.title}",
            f"Identify resources needed for mitigation",
        ]

        if risk.strategy == StrategyType.AVOID:
            plan.short_term.append(f"Eliminate root cause: {risk.description}")
            plan.short_term.append("Validate risk is no longer applicable")
        elif risk.strategy == StrategyType.MITIGATE:
            plan.short_term.append(f"Implement control measures for {dim_context}")
            plan.short_term.append("Monitor effectiveness of controls")

        # Long-term actions (1 month)
        plan.long_term = [
            f"Integrate {risk.title} into ongoing monitoring",
            f"Update risk register with lessons learned",
            f"Review and update related processes/procedures",
        ]

        if risk.dimension.value == "technical":
            plan.long_term.append("Review architecture for similar risks")
            plan.long_term.append("Add automated detection for this risk type")
        elif risk.dimension.value == "operational":
            plan.long_term.append("Conduct team training on this risk type")
            plan.long_term.append("Update runbook with new procedures")

        # Fallback plan
        plan.fallback = [
            "Escalate to project sponsor if mitigation fails",
            "Prepare contingency budget/resource plan",
            "Document decision rationale for acceptance",
        ]

        if risk.strategy == StrategyType.AVOID:
            plan.fallback.append("Rollback changes if elimination causes issues")
        elif risk.strategy == StrategyType.TRANSFER:
            plan.fallback.append("Exercise contractual fallback clauses")

        return plan

    def _get_dimension_context(self, risk: Risk) -> str:
        """獲取維度相關的上下文描述"""
        contexts = {
            "technical": "system architecture and code quality",
            "operational": "team processes and procedures",
            "external": "market conditions and third-party dependencies",
        }
        return contexts.get(risk.dimension.value, "general operations")

    def _get_level_context(self, risk: Risk) -> str:
        """獲取等級相關的上下文描述"""
        contexts = {
            RiskLevel.CRITICAL: "immediate attention and executive involvement",
            RiskLevel.HIGH: "dedicated resources and regular status updates",
            RiskLevel.MEDIUM: "scheduled remediation within sprint",
            RiskLevel.LOW: "track in backlog for eventual resolution",
        }
        return contexts.get(risk.level, "standard monitoring")

    def generate_all_plans(self, risks: List[Risk]) -> List[Risk]:
        """
        [FR-03] 為所有風險生成策略和計劃

        Args:
            risks: List of identified risks

        Returns:
            Risks with strategy and mitigation_plan populated
        """
        for risk in risks:
            # Determine strategy
            risk.strategy = self.generate(risk)

            # Generate mitigation plan
            risk.mitigation_plan = self.generate_mitigation_plan(risk)
            risk.mitigation = self._summarize_plan(risk.mitigation_plan)

            # Set owner if not set
            if not risk.owner:
                risk.owner = self._default_owner(risk)

            # Update timestamp
            risk.updated_at = datetime.now()

        return risks

    def _summarize_plan(self, plan: MitigationPlan) -> str:
        """將緩解計劃總結為一行描述"""
        summary_parts = []

        if plan.immediate:
            summary_parts.append(f"Immediate: {plan.immediate[0]}")
        if plan.short_term:
            summary_parts.append(f"Short-term: {plan.short_term[0]}")
        if plan.long_term:
            summary_parts.append(f"Long-term: {plan.long_term[0]}")

        return "; ".join(summary_parts) if summary_parts else "Monitoring only"

    def _default_owner(self, risk: Risk) -> str:
        """根據風險維度返回默認負責人"""
        owners = {
            "technical": "Tech Lead",
            "operational": "Project Manager",
            "external": "Product Owner",
        }
        return owners.get(risk.dimension.value, "Project Owner")

    def evaluate_strategy_effectiveness(
        self,
        risk: Risk,
        actual_outcome: float
    ) -> dict:
        """
        [FR-03] 評估策略有效性

        Args:
            risk: The risk with its planned strategy
            actual_outcome: Actual result (0-1, lower is better)

        Returns:
            Effectiveness assessment dict
        """
        expected_score = risk.score
        improvement = expected_score - actual_outcome

        effectiveness = "unknown"
        if actual_outcome < expected_score:
            if improvement > 0.5:
                effectiveness = "highly_effective"
            elif improvement > 0.2:
                effectiveness = "effective"
            else:
                effectiveness = "marginally_effective"
        elif actual_outcome >= expected_score:
            effectiveness = "ineffective"

        return {
            "risk_id": risk.id,
            "strategy_used": risk.strategy.value,
            "expected_score": expected_score,
            "actual_outcome": actual_outcome,
            "improvement": improvement,
            "effectiveness": effectiveness,
            "recommendation": self._effectiveness_recommendation(effectiveness),
        }

    def _effectiveness_recommendation(self, effectiveness: str) -> str:
        """根據有效性給出建議"""
        recommendations = {
            "highly_effective": "Continue using this strategy for similar risks",
            "effective": "Strategy is working, monitor for minor adjustments",
            "marginally_effective": "Consider enhancing controls or adjusting threshold",
            "ineffective": "Reconsider strategy type, escalate if necessary",
            "unknown": "Collect more data before making strategy changes",
        }
        return recommendations.get(effectiveness, "Review risk assessment")
