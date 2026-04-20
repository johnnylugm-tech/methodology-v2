#!/usr/bin/env python3
"""
test_strategist.py - Tests for Risk Strategist
[FR-03] Risk response strategy generation tests
"""

import pytest

from engine.strategist import RiskStrategist
from models.risk import Risk, MitigationPlan
from models.enums import RiskDimension, RiskLevel, StrategyType


class TestRiskStrategist:
    """Tests for RiskStrategist [FR-03]"""
    
    def setup_method(self):
        self.strategist = RiskStrategist()
    
    def test_generate_avoid_strategy(self):
        """[FR-03] High score -> AVOID strategy"""
        risk = Risk(
            title="High Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.9,
            impact=5,
        )
        
        strategy = self.strategist.generate(risk)
        assert strategy == StrategyType.AVOID
    
    def test_generate_mitigate_strategy(self):
        """[FR-03] Medium score -> MITIGATE strategy"""
        risk = Risk(
            title="Medium Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.5,
            impact=3,
        )
        
        strategy = self.strategist.generate(risk)
        assert strategy in [StrategyType.MITIGATE, StrategyType.TRANSFER]
    
    def test_generate_accept_strategy(self):
        """[FR-03] Low score -> ACCEPT strategy"""
        risk = Risk(
            title="Low Risk",
            description="Test",
            dimension=RiskDimension.OPERATIONAL,
            probability=0.1,
            impact=2,
        )
        
        strategy = self.strategist.generate(risk)
        assert strategy == StrategyType.ACCEPT
    
    def test_generate_mitigation_plan_basic(self):
        """[FR-03] Generate basic mitigation plan"""
        risk = Risk(
            title="Test Risk",
            description="Test description",
            dimension=RiskDimension.TECHNICAL,
            probability=0.6,
            impact=4,
            level=RiskLevel.HIGH,
            strategy=StrategyType.MITIGATE,
        )
        
        plan = self.strategist.generate_mitigation_plan(risk)
        
        assert isinstance(plan, MitigationPlan)
        assert len(plan.immediate) > 0
        assert len(plan.short_term) > 0
        assert len(plan.long_term) > 0
        assert len(plan.fallback) > 0
    
    def test_generate_mitigation_plan_critical(self):
        """[FR-03] Generate plan for CRITICAL risk"""
        risk = Risk(
            title="Critical Risk",
            description="Critical issue",
            dimension=RiskDimension.EXTERNAL,
            probability=0.9,
            impact=5,
            level=RiskLevel.CRITICAL,
            strategy=StrategyType.AVOID,
        )
        
        plan = self.strategist.generate_mitigation_plan(risk)
        
        # Critical risks should have more immediate actions
        assert len(plan.immediate) >= 3
    
    def test_generate_all_plans(self):
        """[FR-03] Generate plans for all risks"""
        risks = [
            Risk(
                title=f"Risk {i}",
                description="Test",
                dimension=RiskDimension.TECHNICAL,
                probability=0.5,
                impact=3,
            )
            for i in range(3)
        ]
        
        updated = self.strategist.generate_all_plans(risks)
        
        assert len(updated) == 3
        for risk in updated:
            assert risk.strategy is not None
            assert risk.mitigation_plan is not None
            assert risk.owner is not None  # Should auto-assign owner
    
    def test_summarize_plan(self):
        """[FR-03] Summarize plan to single line"""
        plan = MitigationPlan(
            immediate=["Do this first"],
            short_term=["Then do this"],
            long_term=["Finally this"],
        )
        
        summary = self.strategist._summarize_plan(plan)
        
        assert "Immediate" in summary or "Short-term" in summary
        assert len(summary) < 200  # Should be concise
    
    def test_evaluate_effectiveness_improved(self):
        """[FR-03] Strategy effectiveness - improved"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.7,
            impact=4,
        )
        
        result = self.strategist.evaluate_strategy_effectiveness(risk, 0.2)
        
        assert "effectiveness" in result
        assert result["improvement"] > 0
        assert result["expected_score"] > result["actual_outcome"]
    
    def test_evaluate_effectiveness_not_improved(self):
        """[FR-03] Strategy effectiveness - not improved"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.3,
            impact=2,
        )
        
        result = self.strategist.evaluate_strategy_effectiveness(risk, 0.5)
        
        assert result["effectiveness"] in ["ineffective", "unknown"]
    
    def test_default_owner_technical(self):
        """[FR-03] Default owner for technical risks"""
        owner = self.strategist._default_owner(
            Risk(
                title="Test",
                description="Test",
                dimension=RiskDimension.TECHNICAL,
            )
        )
        
        assert owner == "Tech Lead"
    
    def test_default_owner_operational(self):
        """[FR-03] Default owner for operational risks"""
        owner = self.strategist._default_owner(
            Risk(
                title="Test",
                description="Test",
                dimension=RiskDimension.OPERATIONAL,
            )
        )
        
        assert owner == "Project Manager"
    
    def test_default_owner_external(self):
        """[FR-03] Default owner for external risks"""
        owner = self.strategist._default_owner(
            Risk(
                title="Test",
                description="Test",
                dimension=RiskDimension.EXTERNAL,
            )
        )
        
        assert owner == "Product Owner"


class TestStrategyThresholds:
    """Tests for strategy threshold logic"""
    
    def setup_method(self):
        self.strategist = RiskStrategist()
    
    def test_avoid_threshold(self):
        """[FR-03] Score > 0.6 triggers AVOID"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.9,
            impact=5,
            detectability_factor=1.0,
        )
        
        # Score = 0.9 * 5 / 5 = 0.9
        assert risk.score > 0.6
        assert self.strategist.generate(risk) == StrategyType.AVOID
    
    def test_mitigate_threshold(self):
        """[FR-03] Score 0.3-0.6 triggers MITIGATE"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.5,
            impact=3,
            detectability_factor=1.0,
        )
        
        # Score = 0.5 * 3 / 5 = 0.3
        assert 0.3 <= risk.score <= 0.6
        strategy = self.strategist.generate(risk)
        assert strategy in [StrategyType.MITIGATE, StrategyType.TRANSFER]
    
    def test_accept_threshold(self):
        """[FR-03] Score < 0.3 triggers ACCEPT"""
        risk = Risk(
            title="Test",
            description="Test",
            dimension=RiskDimension.OPERATIONAL,
            probability=0.2,
            impact=2,
            detectability_factor=0.5,
        )
        
        # Score = 0.2 * 2 * 0.5 / 5 = 0.04
        assert risk.score < 0.3
        assert self.strategist.generate(risk) == StrategyType.ACCEPT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])