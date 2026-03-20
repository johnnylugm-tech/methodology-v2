"""
PM Mode - 產品經理日常模式

提供：
- 晨間報告 (Morning Report)
- 成本預測 (Cost Predictor)
- Sprint 健康狀況
- 風險警報
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


@dataclass
class MorningReport:
    """晨間報告"""
    date: datetime
    sprint_name: str
    sprint_progress: float  # 0-100
    
    # 產出
    completed_yesterday: List[str] = field(default_factory=list)
    planned_today: List[str] = field(default_factory=list)
    
    # 阻塞
    blockers: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # 指標
    velocity: float = 0
    burndown_rate: float = 0
    team_health: float = 0  # 0-10
    
    @property
    def status_emoji(self) -> str:
        if self.sprint_progress >= 80:
            return "🟢"
        elif self.sprint_progress >= 50:
            return "🟡"
        else:
            return "🔴"
    
    def to_markdown(self) -> str:
        lines = []
        lines.append(f"# 🌅 晨間報告 - {self.date.strftime('%Y-%m-%d')}")
        lines.append("")
        lines.append(f"**Sprint**: {self.sprint_name} | **進度**: {self.status_emoji} {self.sprint_progress:.1f}%")
        lines.append("")
        
        lines.append("## ✅ 昨日完成")
        if self.completed_yesterday:
            for item in self.completed_yesterday:
                lines.append(f"- {item}")
        else:
            lines.append("- 無")
        lines.append("")
        
        lines.append("## 📋 今日計劃")
        if self.planned_today:
            for item in self.planned_today:
                lines.append(f"- {item}")
        else:
            lines.append("- 無")
        lines.append("")
        
        if self.blockers:
            lines.append("## 🚧 阻塞問題")
            for b in self.blockers:
                lines.append(f"- 🔴 {b}")
            lines.append("")
        
        if self.risks:
            lines.append("## ⚠️ 風險")
            for r in self.risks:
                lines.append(f"- 🟡 {r}")
            lines.append("")
        
        lines.append("## 📊 指標")
        lines.append(f"- Velocity: {self.velocity:.1f} 點/sprint")
        lines.append(f"- Burndown Rate: {self.burndown_rate:.2f} 點/天")
        lines.append(f"- Team Health: {self.team_health:.1f}/10")
        lines.append("")
        
        return "\n".join(lines)


@dataclass
class CostForecast:
    """成本預測"""
    project_name: str
    current_cost: float
    budget: float
    
    # 預測
    predicted_monthly: float
    predicted_total: float
    
    # 趨勢
    daily_burn_rate: float
    days_until_budget_exhausted: Optional[float] = None
    
    # 建議
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def budget_utilization(self) -> float:
        return (self.current_cost / self.budget) * 100 if self.budget > 0 else 0
    
    @property
    def status(self) -> str:
        util = self.budget_utilization
        if util >= 90:
            return "🔴 CRITICAL"
        elif util >= 75:
            return "🟡 WARNING"
        else:
            return "🟢 NORMAL"
    
    def to_markdown(self) -> str:
        lines = []
        lines.append(f"# 💰 成本預測 - {self.project_name}")
        lines.append("")
        lines.append(f"**狀態**: {self.status}")
        lines.append("")
        
        lines.append("## 📊 當前狀態")
        lines.append(f"- 當前花費: ${self.current_cost:.2f}")
        lines.append(f"- 預算: ${self.budget:.2f}")
        lines.append(f"- 使用率: {self.budget_utilization:.1f}%")
        lines.append("")
        
        lines.append("## 📈 預測")
        lines.append(f"- 日均消耗: ${self.daily_burn_rate:.2f}")
        lines.append(f"- 預測本月: ${self.predicted_monthly:.2f}")
        lines.append(f"- 預測總計: ${self.predicted_total:.2f}")
        if self.days_until_budget_exhausted:
            lines.append(f"- 預算耗盡: 約 {self.days_until_budget_exhausted:.0f} 天後")
        lines.append("")
        
        if self.recommendations:
            lines.append("## 💡 建議")
            for r in self.recommendations:
                lines.append(f"- {r}")
            lines.append("")
        
        return "\n".join(lines)


class PMMode:
    """PM Mode 主類"""
    
    def __init__(self):
        self.reports: List[MorningReport] = []
        self.forecasts: Dict[str, CostForecast] = {}
    
    def generate_morning_report(
        self,
        sprint_name: str,
        sprint_progress: float,
        completed_yesterday: List[str] = None,
        planned_today: List[str] = None,
        blockers: List[str] = None,
        velocity: float = 0,
        team_health: float = 8.0
    ) -> MorningReport:
        """生成晨間報告"""
        report = MorningReport(
            date=datetime.now(),
            sprint_name=sprint_name,
            sprint_progress=sprint_progress,
            completed_yesterday=completed_yesterday or [],
            planned_today=planned_today or [],
            blockers=blockers or [],
            velocity=velocity,
            burndown_rate=velocity / 10,  # 估算
            team_health=team_health
        )
        self.reports.append(report)
        return report
    
    def predict_cost(
        self,
        project_name: str,
        current_cost: float,
        budget: float,
        daily_burn_rate: float,
        days_remaining: int
    ) -> CostForecast:
        """預測成本"""
        # 簡單線性預測
        predicted_total = current_cost + (daily_burn_rate * days_remaining)
        days_until_exhausted = budget / daily_burn_rate if daily_burn_rate > 0 else None
        
        recommendations = []
        
        # 根據預測生成建議
        if days_until_exhausted and days_until_exhausted < 7:
            recommendations.append("⚠️ 預算即將耗盡，建議立即審查非必要開支")
        
        if predicted_total > budget * 1.2:
            recommendations.append("📊 預測將超出預算 20% 以上，建議調整範圍")
        
        if daily_burn_rate > (budget / 30) * 1.5:
            recommendations.append("🔥 日均消耗過高，檢查是否有異常支出")
        
        # 默認建議
        if not recommendations:
            recommendations.append("✅ 成本狀況正常，持續監控")
        
        forecast = CostForecast(
            project_name=project_name,
            current_cost=current_cost,
            budget=budget,
            predicted_monthly=current_cost * 30 / max(1, 30 - days_remaining),
            predicted_total=predicted_total,
            daily_burn_rate=daily_burn_rate,
            days_until_budget_exhausted=days_until_exhausted,
            recommendations=recommendations
        )
        
        self.forecasts[project_name] = forecast
        return forecast
    
    def get_sprint_health(self, velocity: float, planned: float, completed: float) -> Dict[str, Any]:
        """計算 Sprint 健康狀況"""
        completion_rate = (completed / planned * 100) if planned > 0 else 0
        
        # 健康評估
        if completion_rate >= 90:
            health = "🟢 HEALTHY"
            health_score = 9
        elif completion_rate >= 70:
            health = "🟡 AT_RISK"
            health_score = 6
        elif completion_rate >= 50:
            health = "🟠 UNHEALTHY"
            health_score = 4
        else:
            health = "🔴 CRITICAL"
            health_score = 2
        
        # 預測
        days_elapsed = 7  # 假設一週
        days_total = 14   # 假設兩週 sprint
        required_rate = planned / days_total
        actual_rate = completed / days_elapsed if days_elapsed > 0 else 0
        
        prediction = "On Track" if actual_rate >= required_rate else "Behind"
        
        return {
            "health": health,
            "health_score": health_score,
            "completion_rate": completion_rate,
            "prediction": prediction,
            "velocity": velocity,
            "remaining": planned - completed,
            "days_remaining": days_total - days_elapsed
        }
    
    def generate_full_report(self) -> str:
        """生成完整報告"""
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " 📊 PM MODE DAILY REPORT ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        # 最近的晨間報告
        if self.reports:
            latest = self.reports[-1]
            lines.append("## 🌅 Latest Morning Report")
            lines.append(f"Sprint: {latest.sprint_name} | Progress: {latest.sprint_progress:.1f}%")
            lines.append(f"Completed Yesterday: {len(latest.completed_yesterday)} items")
            lines.append(f"Planned Today: {len(latest.planned_today)} items")
            if latest.blockers:
                lines.append(f"Blockers: {len(latest.blockers)}")
            lines.append("")
        
        # 成本預測
        if self.forecasts:
            lines.append("## 💰 Cost Forecasts")
            for name, forecast in self.forecasts.items():
                lines.append(f"**{name}**: {forecast.status} (${forecast.current_cost:.2f} / ${forecast.budget:.2f})")
            lines.append("")
        
        return "\n".join(lines)


# ==================== Main ====================

if __name__ == "__main__":
    pm = PMMode()
    
    # 生成晨間報告
    report = pm.generate_morning_report(
        sprint_name="Sprint 5",
        sprint_progress=65.0,
        completed_yesterday=["完成登入功能", "修復認證 Bug"],
        planned_today=["開發儀表板", "API 文件"],
        blockers=["等不及第三方 API 文件"],
        velocity=42.0,
        team_health=8.5
    )
    
    print(report.to_markdown())
    
    print("\n" + "=" * 50 + "\n")
    
    # 成本預測
    forecast = pm.predict_cost(
        project_name="AI Assistant",
        current_cost=500.0,
        budget=2000.0,
        daily_burn_rate=85.0,
        days_remaining=18
    )
    
    print(forecast.to_markdown())
    
    print("\n" + "=" * 50 + "\n")
    
    # Sprint 健康狀況
    health = pm.get_sprint_health(velocity=35, planned=50, completed=30)
    print("## Sprint Health")
    print(f"Status: {health['health']}")
    print(f"Score: {health['health_score']}/10")
    print(f"Completion: {health['completion_rate']:.1f}%")
    print(f"Prediction: {health['prediction']}")
