#!/usr/bin/env python3
"""
Dashboard Cost Trend - 成本趨勢分析

為 Dashboard 增加成本趨勢功能
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class CostSnapshot:
    """成本快照"""
    date: datetime
    total_cost: float
    by_model: Dict[str, float] = field(default_factory=dict)
    by_user: Dict[str, float] = field(default_factory=dict)
    by_project: Dict[str, float] = field(default_factory=dict)
    tokens_used: int = 0


@dataclass
class CostTrend:
    """成本趨勢"""
    date: str
    cost: float
    change_percent: float = 0.0
    cumulative: float = 0.0


@dataclass
class CostForecast:
    """成本預測"""
    date: str
    predicted_cost: float
    confidence: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0


class CostTrendAnalyzer:
    """成本趨勢分析器"""
    
    def __init__(self):
        self.snapshots: List[CostSnapshot] = []
        self.daily_costs: Dict[str, float] = defaultdict(float)
        self.model_rates: Dict[str, float] = {
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "claude-4-sonnet": 0.003,
            "claude-4-opus": 0.015,
            "gemini-2.0-flash": 0.0,
            "minimax-m2.7": 0.0003,
        }
    
    def record(self, date: datetime, cost: float,
              model: str = None, user_id: str = None,
              project_id: str = None, tokens: int = 0):
        """記錄成本"""
        # 轉換為日期字串
        date_str = date.strftime("%Y-%m-%d")
        
        snapshot = CostSnapshot(
            date=date,
            total_cost=cost,
            tokens_used=tokens,
        )
        
        if model:
            snapshot.by_model[model] = cost
        if user_id:
            snapshot.by_user[user_id] = cost
        if project_id:
            snapshot.by_project[project_id] = cost
        
        self.snapshots.append(snapshot)
        self.daily_costs[date_str] += cost
    
    def record_api_call(self, model: str, input_tokens: int,
                       output_tokens: int, user_id: str = None,
                       project_id: str = None):
        """記錄 API 呼叫"""
        rate = self.model_rates.get(model, 0.001)
        cost = (input_tokens / 1000) * rate + (output_tokens / 1000) * rate * 3
        
        self.record(
            date=datetime.now(),
            cost=cost,
            model=model,
            user_id=user_id,
            project_id=project_id,
            tokens=input_tokens + output_tokens
        )
    
    def get_trend(self, days: int = 30) -> List[CostTrend]:
        """取得成本趨勢"""
        trends = []
        cumulative = 0.0
        
        # 取得日期範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        current_date = start_date
        prev_cost = 0.0
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            cost = self.daily_costs.get(date_str, 0.0)
            
            change = ((cost - prev_cost) / prev_cost * 100) if prev_cost > 0 else 0.0
            
            cumulative += cost
            
            trends.append(CostTrend(
                date=date_str,
                cost=cost,
                change_percent=change,
                cumulative=cumulative
            ))
            
            prev_cost = cost
            current_date += timedelta(days=1)
        
        return trends
    
    def forecast(self, days: int = 7) -> List[CostForecast]:
        """預測未來成本"""
        trends = self.get_trend(days=30)
        
        if len(trends) < 7:
            return []
        
        # 簡單線性回歸
        costs = [t.cost for t in trends[-14:]]  # 用過去 14 天
        
        n = len(costs)
        x_mean = sum(range(n)) / n
        y_mean = sum(costs) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(costs))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # 計算標準差
        std_dev = (sum((v - (slope * i + intercept)) ** 2 for i, v in enumerate(costs)) / n) ** 0.5
        
        # 預測未來
        forecasts = []
        last_date = datetime.now()
        
        for i in range(1, days + 1):
            future_x = n + i
            predicted = slope * future_x + intercept
            predicted = max(0, predicted)  # 成本不能為負
            
            confidence = max(0.3, 1 - (i * 0.1))  # 越遠越不確定
            
            forecasts.append(CostForecast(
                date=(last_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                predicted_cost=predicted,
                confidence=confidence,
                lower_bound=max(0, predicted - std_dev),
                upper_bound=predicted + std_dev
            ))
        
        return forecasts
    
    def get_summary(self, days: int = 30) -> Dict:
        """取得摘要"""
        trends = self.get_trend(days)
        
        total = sum(t.cost for t in trends)
        avg_daily = total / days if days > 0 else 0
        
        # 計算趨勢
        if len(trends) >= 7:
            first_week = sum(t.cost for t in trends[:7])
            last_week = sum(t.cost for t in trends[-7:])
            week_over_week = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
        else:
            week_over_week = 0
        
        # 找出最高成本日
        max_day = max(trends, key=lambda t: t.cost) if trends else None
        
        # 預測
        forecasts = self.forecast(7)
        predicted_total = sum(f.predicted_cost for f in forecasts)
        
        return {
            "period_days": days,
            "total_cost": total,
            "avg_daily": avg_daily,
            "week_over_week_change": week_over_week,
            "max_day": {
                "date": max_day.date if max_day else None,
                "cost": max_day.cost if max_day else 0
            } if max_day else None,
            "predicted_next_7_days": predicted_total,
            "trend_direction": "up" if week_over_week > 5 else "down" if week_over_week < -5 else "stable"
        }
    
    def get_by_model(self, days: int = 30) -> Dict:
        """按模型分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        model_costs = defaultdict(float)
        model_tokens = defaultdict(int)
        
        for snapshot in self.snapshots:
            if start_date <= snapshot.date <= end_date:
                for model, cost in snapshot.by_model.items():
                    model_costs[model] += cost
        
        total = sum(model_costs.values())
        
        return {
            "total": total,
            "by_model": {
                model: {
                    "cost": cost,
                    "percent": (cost / total * 100) if total > 0 else 0
                }
                for model, cost in sorted(model_costs.items(), key=lambda x: -x[1])
            }
        }
    
    def get_by_user(self, days: int = 30) -> Dict:
        """按用戶分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        user_costs = defaultdict(float)
        
        for snapshot in self.snapshots:
            if start_date <= snapshot.date <= end_date:
                for user_id, cost in snapshot.by_user.items():
                    user_costs[user_id] += cost
        
        total = sum(user_costs.values())
        
        return {
            "total": total,
            "by_user": {
                user_id: {
                    "cost": cost,
                    "percent": (cost / total * 100) if total > 0 else 0
                }
                for user_id, cost in sorted(user_costs.items(), key=lambda x: -x[1])
            }
        }
    
    def get_by_project(self, days: int = 30) -> Dict:
        """按專案分析"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        project_costs = defaultdict(float)
        
        for snapshot in self.snapshots:
            if start_date <= snapshot.date <= end_date:
                for project_id, cost in snapshot.by_project.items():
                    project_costs[project_id] += cost
        
        total = sum(project_costs.values())
        
        return {
            "total": total,
            "by_project": {
                project_id: {
                    "cost": cost,
                    "percent": (cost / total * 100) if total > 0 else 0
                }
                for project_id, cost in sorted(project_costs.items(), key=lambda x: -x[1])
            }
        }
    
    def generate_report(self) -> str:
        """生成成本報告"""
        summary = self.get_summary(30)
        by_model = self.get_by_model(30)
        by_user = self.get_by_user(30)
        forecasts = self.forecast(7)
        
        report = f"""
# 💰 成本趨勢報告 (30天)

## 總覽

| 指標 | 數值 |
|------|------|
| 總成本 | ${summary['total_cost']:.4f} |
| 日均成本 | ${summary['avg_daily']:.4f} |
| 週變化 | {summary['week_over_week_change']:+.1f}% |
| 趨勢 | {'📈 ' + summary['trend_direction'] if summary['trend_direction'] == 'up' else '📉 ' + summary['trend_direction'] if summary['trend_direction'] == 'down' else '➡️ stable'} |

---

## 預測 (未來 7 天)

| 日期 | 預測成本 | 置信度 |
|------|----------|--------|
"""
        
        for f in forecasts:
            report += f"| {f.date} | ${f.predicted_cost:.4f} | {f.confidence:.0%} |\n"
        
        report += f"""

## 按模型

| 模型 | 成本 | 佔比 |
|------|------|------|
"""
        
        for model, data in list(by_model['by_model'].items())[:5]:
            report += f"| {model} | ${data['cost']:.4f} | {data['percent']:.1f}% |\n"
        
        report += f"""

## 按用戶

| 用戶 | 成本 | 佔比 |
|------|------|------|
"""
        
        for user_id, data in list(by_user['by_user'].items())[:5]:
            report += f"| {user_id} | ${data['cost']:.4f} | {data['percent']:.1f}% |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    analyzer = CostTrendAnalyzer()
    
    # 模擬數據
    import random
    
    print("=== Recording Costs ===")
    
    for i in range(30):
        date = datetime.now() - timedelta(days=30-i)
        
        # 每天隨機成本
        analyzer.record_api_call(
            model="gpt-4o",
            input_tokens=random.randint(1000, 5000),
            output_tokens=random.randint(500, 2000),
            user_id="user-1",
            project_id="project-ai"
        )
        
        analyzer.record_api_call(
            model="minimax-m2.7",
            input_tokens=random.randint(2000, 8000),
            output_tokens=random.randint(1000, 3000),
            user_id="user-2",
            project_id="project-ai"
        )
    
    # 趨勢
    print("\n=== Cost Trend (Last 7 days) ===")
    trends = analyzer.get_trend(7)
    for t in trends[-7:]:
        print(f"{t.date}: ${t.cost:.4f} ({t.change_percent:+.1f}%)")
    
    # 摘要
    print("\n=== Summary ===")
    summary = analyzer.get_summary(30)
    print(f"Total: ${summary['total_cost']:.4f}")
    print(f"Avg Daily: ${summary['avg_daily']:.4f}")
    print(f"Week over Week: {summary['week_over_week_change']:+.1f}%")
    print(f"Predicted Next 7 Days: ${summary['predicted_next_7_days']:.4f}")
    
    # 按模型
    print("\n=== By Model ===")
    by_model = analyzer.get_by_model(30)
    for model, data in by_model['by_model'].items():
        print(f"{model}: ${data['cost']:.4f} ({data['percent']:.1f}%)")
    
    # 報告
    print("\n=== Report ===")
    print(analyzer.generate_report())
