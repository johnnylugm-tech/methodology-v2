#!/usr/bin/env python3
"""
Risk Dashboard - 風險儀表板

預測專案延期/超支風險
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import random


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """風險類別"""
    SCHEDULE = "schedule"  # 進度風險
    BUDGET = "budget"      # 預算風險
    QUALITY = "quality"     # 品質風險
    RESOURCE = "resource"   # 資源風險
    TECHNICAL = "technical" # 技術風險


@dataclass
class Risk:
    """風險"""
    id: str
    name: str
    description: str
    category: RiskCategory
    level: RiskLevel
    probability: float  # 發生機率 0-1
    impact: float       # 影響程度 0-1
    status: str = "open"  # open, mitigated, occurred, closed
    
    # 預測數據
    predicted_delay_days: float = 0.0  # 預測延遲天數
    predicted_cost_overrun: float = 0.0  # 預測超支金額
    
    # 應對策略
    mitigation: str = ""
    contingency: str = ""
    
    # 追蹤
    identified_at: datetime = field(default_factory=datetime.now)
    occurred_at: datetime = None
    resolved_at: datetime = None
    
    @property
    def expected_impact(self) -> float:
        """預期影響 (概率 × 影響)"""
        return self.probability * self.impact


@dataclass
class ProjectMetrics:
    """專案指標"""
    project_id: str
    name: str
    
    # 進度
    planned_progress: float = 0.0  # 0-100%
    actual_progress: float = 0.0
    planned_velocity: float = 0.0    # 預期速度
    actual_velocity: float = 0.0     # 實際速度
    
    # 預算
    planned_budget: float = 0.0
    actual_spend: float = 0.0
    burn_rate: float = 0.0          # 支出速率
    
    # 資源
    resource_utilization: float = 0.0  # 資源利用率
    available_capacity: float = 100.0
    
    # 品質
    defect_rate: float = 0.0
    rework_rate: float = 0.0
    
    # 時間
    days_elapsed: int = 0
    days_remaining: int = 0
    end_date: datetime = None
    
    @property
    def schedule_variance(self) -> float:
        """進度差異 (正=落後，負=超前)"""
        return self.planned_progress - self.actual_progress
    
    @property
    def schedule_performance_index(self) -> float:
        """進度績效指標 (SPI)"""
        if self.planned_velocity == 0:
            return 1.0
        return self.actual_velocity / self.planned_velocity
    
    @property
    def cost_variance(self) -> float:
        """成本差異"""
        return self.planned_budget - self.actual_spend
    
    @property
    def cost_performance_index(self) -> float:
        """成本績效指標 (CPI)"""
        if self.actual_spend == 0:
            return 1.0
        return self.planned_budget / self.actual_spend
    
    @property
    def predicted_completion_date(self) -> datetime:
        """預測完成日期"""
        if self.schedule_performance_index <= 0:
            return self.end_date + timedelta(days=30)  # 預設延遲
        
        remaining = (100 - self.actual_progress) / self.actual_velocity if self.actual_velocity > 0 else 0
        return datetime.now() + timedelta(days=remaining)
    
    @property
    def predicted_total_cost(self) -> float:
        """預測總成本"""
        if self.cost_performance_index <= 0:
            return self.planned_budget * 1.5  # 預設超支 50%
        return self.actual_spend / (self.actual_progress / 100) if self.actual_progress > 0 else self.planned_budget
    
    @property
    def schedule_risk(self) -> RiskLevel:
        """進度風險"""
        spi = self.schedule_performance_index
        if spi < 0.8:
            return RiskLevel.CRITICAL
        elif spi < 0.9:
            return RiskLevel.HIGH
        elif spi < 0.95:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    @property
    def budget_risk(self) -> RiskLevel:
        """預算風險"""
        cpi = self.cost_performance_index
        if cpi < 0.8:
            return RiskLevel.CRITICAL
        elif cpi < 0.9:
            return RiskLevel.HIGH
        elif cpi < 0.95:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


class RiskDashboard:
    """風險儀表板"""
    
    def __init__(self):
        self.risks: Dict[str, Risk] = {}
        self.metrics: Dict[str, ProjectMetrics] = {}
        self.history: List[Dict] = []
    
    def add_risk(self, name: str, description: str,
                category: RiskCategory, probability: float,
                impact: float, mitigation: str = "",
                contingency: str = "") -> str:
        """新增風險"""
        risk_id = f"risk-{len(self.risks) + 1}"
        
        # 計算風險等級
        expected = probability * impact
        if expected > 0.7 or impact > 0.9:
            level = RiskLevel.CRITICAL
        elif expected > 0.4 or impact > 0.7:
            level = RiskLevel.HIGH
        elif expected > 0.2 or impact > 0.4:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        risk = Risk(
            id=risk_id,
            name=name,
            description=description,
            category=category,
            level=level,
            probability=probability,
            impact=impact,
            mitigation=mitigation,
            contingency=contingency,
        )
        
        self.risks[risk_id] = risk
        self._record_history("risk_added", risk_id)
        
        return risk_id
    
    def update_metrics(self, project_id: str, **kwargs):
        """更新專案指標"""
        if project_id not in self.metrics:
            self.metrics[project_id] = ProjectMetrics(project_id=project_id, name=kwargs.get("name", project_id))
        
        metrics = self.metrics[project_id]
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
        
        # 重新評估風險
        self._reevaluate_risks(project_id)
    
    def _reevaluate_risks(self, project_id: str):
        """重新評估風險"""
        if project_id not in self.metrics:
            return
        
        metrics = self.metrics[project_id]
        
        # 進度風險
        if metrics.schedule_risk != RiskLevel.LOW:
            self.add_risk(
                name=f"專案進度落後 ({metrics.schedule_risk.value})",
                description=f"SPI: {metrics.schedule_performance_index:.2f}",
                category=RiskCategory.SCHEDULE,
                probability=1 - metrics.schedule_performance_index,
                impact=min(1.0, metrics.schedule_variance / 100),
                mitigation="增加資源或調整範圍",
            )
        
        # 預算風險
        if metrics.budget_risk != RiskLevel.LOW:
            self.add_risk(
                name=f"專案預算超支 ({metrics.budget_risk.value})",
                description=f"CPI: {metrics.cost_performance_index:.2f}",
                category=RiskCategory.BUDGET,
                probability=1 - metrics.cost_performance_index,
                impact=min(1.0, abs(metrics.cost_variance) / metrics.planned_budget if metrics.planned_budget else 0),
                mitigation="砍功能或追加預算",
            )
    
    def _record_history(self, action: str, risk_id: str):
        """記錄歷史"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "risk_id": risk_id,
        })
    
    def get_risk_matrix(self) -> Dict:
        """取得風險矩陣"""
        # 按等級分組
        by_level = defaultdict(list)
        for risk in self.risks.values():
            if risk.status == "open":
                by_level[risk.level.value].append({
                    "id": risk.id,
                    "name": risk.name,
                    "category": risk.category.value,
                    "probability": risk.probability,
                    "impact": risk.impact,
                    "expected_impact": risk.expected_impact,
                })
        
        return {
            "critical": by_level["critical"],
            "high": by_level["high"],
            "medium": by_level["medium"],
            "low": by_level["low"],
            "total_open": sum(len(v) for v in by_level.values()),
        }
    
    def get_top_risks(self, limit: int = 5) -> List[Dict]:
        """取得最高風險"""
        open_risks = [r for r in self.risks.values() if r.status == "open"]
        sorted_risks = sorted(open_risks, key=lambda r: -r.expected_impact)
        
        return [
            {
                "id": r.id,
                "name": r.name,
                "level": r.level.value,
                "expected_impact": r.expected_impact,
                "mitigation": r.mitigation,
            }
            for r in sorted_risks[:limit]
        ]
    
    def get_project_health(self, project_id: str) -> Dict:
        """取得專案健康狀態"""
        if project_id not in self.metrics:
            return {"status": "unknown"}
        
        metrics = self.metrics[project_id]
        
        # 計算總風險分數
        project_risks = [r for r in self.risks.values() 
                       if r.category.value in ["schedule", "budget"]]
        total_risk = sum(r.expected_impact for r in project_risks)
        
        # 健康狀態
        if total_risk < 0.2 and metrics.schedule_risk == RiskLevel.LOW and metrics.budget_risk == RiskLevel.LOW:
            status = "healthy"
        elif total_risk < 0.5:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "project_id": project_id,
            "name": metrics.name,
            "status": status,
            "schedule_risk": metrics.schedule_risk.value,
            "budget_risk": metrics.budget_risk.value,
            "predicted_completion": metrics.predicted_completion_date.isoformat(),
            "predicted_cost": metrics.predicted_total_cost,
            "total_risk_score": total_risk,
        }
    
    def get_predictions(self) -> Dict:
        """取得預測"""
        predictions = {}
        
        for project_id, metrics in self.metrics.items():
            delay = (metrics.predicted_completion_date - metrics.end_date).days if metrics.end_date else 0
            overrun = metrics.predicted_total_cost - metrics.planned_budget
            
            predictions[project_id] = {
                "name": metrics.name,
                "delay_days": max(0, delay),
                "cost_overrun": max(0, overrun),
                "confidence": 0.7,  # 簡化
            }
        
        return predictions
    
    def generate_report(self) -> str:
        """生成報告"""
        matrix = self.get_risk_matrix()
        predictions = self.get_predictions()
        
        report = f"""
# 🚨 風險報告

## 風險概覽

| 等級 | 數量 |
|------|------|
| 🔴 Critical | {len(matrix['critical'])} |
| 🟠 High | {len(matrix['high'])} |
| 🟡 Medium | {len(matrix['medium'])} |
| 🟢 Low | {len(matrix['low'])} |

---

## 最高風險

"""
        
        for i, risk in enumerate(self.get_top_risks(), 1):
            report += f"{i}. {risk['name']} ({risk['level'].upper()})\n"
            report += f"   預期影響: {risk['expected_impact']:.2%}\n"
            report += f"   緩解: {risk['mitigation']}\n\n"
        
        if predictions:
            report += f"""

## 預測

"""
            for project_id, pred in predictions.items():
                if pred['delay_days'] > 0:
                    report += f"- **{pred['name']}**: 預測延遲 {pred['delay_days']:.0f} 天\n"
                if pred['cost_overrun'] > 0:
                    report += f"- **{pred['name']}**: 預測超支 ${pred['cost_overrun']:.2f}\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    dashboard = RiskDashboard()
    
    # 更新專案指標
    dashboard.update_metrics(
        "project-ai",
        name="AI 系統開發",
        planned_progress=50.0,
        actual_progress=35.0,
        planned_velocity=10.0,
        actual_velocity=7.0,
        planned_budget=100000,
        actual_spend=45000,
        days_elapsed=14,
        days_remaining=14,
        end_date=datetime.now() + timedelta(days=14),
    )
    
    # 手動新增風險
    dashboard.add_risk(
        name="第三方 API 依賴",
        description="依賴外部 API 可能不穩定",
        category=RiskCategory.TECHNICAL,
        probability=0.3,
        impact=0.6,
        mitigation="建立備用方案",
    )
    
    # 風險矩陣
    print("=== Risk Matrix ===")
    matrix = dashboard.get_risk_matrix()
    print(f"Total open risks: {matrix['total_open']}")
    
    # 專案健康
    print("\n=== Project Health ===")
    health = dashboard.get_project_health("project-ai")
    print(f"Status: {health['status']}")
    print(f"Schedule risk: {health['schedule_risk']}")
    print(f"Budget risk: {health['budget_risk']}")
    
    # 預測
    print("\n=== Predictions ===")
    predictions = dashboard.get_predictions()
    for pid, pred in predictions.items():
        print(f"{pred['name']}: Delay {pred['delay_days']:.0f} days, Overrun ${pred['cost_overrun']:.2f}")
    
    # 報告
    print("\n=== Report ===")
    print(dashboard.generate_report())
