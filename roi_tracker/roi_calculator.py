#!/usr/bin/env python3
"""
ROI Calculator
=============
計算投資回報率

ROI = (Value - Cost) / Cost * 100%
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
from .cost_tracker import CostTracker
from .value_tracker import ValueTracker

@dataclass
class ROIReport:
    """ROI 報告"""
    period: str
    total_cost: float
    total_value: float
    roi_percentage: float
    net_value: float
    recommendation: str
    generated_at: datetime

class ROICalculator:
    """
    ROI 計算器
    
    使用方式：
    
    ```python
    calculator = ROICalculator()
    
    report = calculator.calculate(period="month")
    
    print(f"ROI: {report.roi_percentage}%")
    print(f"Net Value: ${report.net_value}")
    print(f"Recommendation: {report.recommendation}")
    ```
    """
    
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.value_tracker = ValueTracker()
    
    def calculate(self, period: str = "month") -> ROIReport:
        """計算 ROI"""
        cost_summary = self.cost_tracker.get_summary(period)
        value_summary = self.value_tracker.get_summary(period)
        
        total_cost = cost_summary["total"]
        total_value_units = value_summary["total_units"]
        
        # 將價值單位轉換為貨幣（這裡需要一個轉換率）
        # 假設：1 task 完成 = $100, 1 小時節省 = $50
        value_to_currency = self._convert_value_to_currency(value_summary)
        
        net_value = value_to_currency - total_cost
        roi_percentage = ((value_to_currency - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        recommendation = self._generate_recommendation(roi_percentage, total_cost, value_to_currency)
        
        return ROIReport(
            period=period,
            total_cost=total_cost,
            total_value=value_to_currency,
            roi_percentage=round(roi_percentage, 2),
            net_value=round(net_value, 2),
            recommendation=recommendation,
            generated_at=datetime.now()
        )
    
    def _convert_value_to_currency(self, value_summary: Dict) -> float:
        """將價值單位轉換為貨幣"""
        # 轉換率（可配置）
        rates = {
            "task_completed": 100,  # $100 per task
            "efficiency_gain": 50,   # $50 per hour saved
            "bugs_prevented": 200,  # $200 per bug prevented
            "quality_improvement": 25,  # $25 per point
            "time_saved": 50         # $50 per hour saved
        }
        
        total = 0
        for value_type, data in value_summary.get("by_type", {}).items():
            rate = rates.get(value_type, 10)  # 預設 $10
            total += data["amount"] * rate
        
        return total
    
    def _generate_recommendation(self, roi: float, cost: float, value: float) -> str:
        """生成建議"""
        if cost == 0 and value > 0:
            return "Infinite ROI! No costs recorded but value delivered."
        elif roi > 200:
            return "Excellent ROI! Consider scaling up investment."
        elif roi > 100:
            return "Good ROI. Current investment is paying off."
        elif roi > 0:
            return "Positive but marginal ROI. Look for optimization opportunities."
        elif roi == 0:
            return "Zero ROI. No net gain or loss."
        elif roi > -50:
            return "Negative ROI. Investigate cost drivers and value delivery."
        else:
            return "Critical: ROI is significantly negative. Major changes needed."
    
    def get_dashboard_data(self) -> Dict:
        """取得儀表板資料"""
        return {
            "monthly": self.calculate("month"),
            "weekly": self.calculate("week"),
            "daily": self.calculate("day")
        }
