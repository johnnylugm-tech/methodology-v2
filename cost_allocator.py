#!/usr/bin/env python3
"""
Cost Allocator - 成本分攤系統

按人/按專案/按團隊分攤成本
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum


class CostType(Enum):
    """成本類型"""
    API_CALL = "api_call"
    COMPUTE = "compute"
    STORAGE = "storage"
    TRANSFER = "transfer"
    OTHER = "other"


@dataclass
class CostEntry:
    """成本項目"""
    id: str
    project_id: str
    user_id: str
    team_id: str
    cost_type: CostType
    amount: float  # 金額
    currency: str = "USD"
    model: str = None  # 使用的模型
    tokens_used: int = 0
    description: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Budget:
    """預算"""
    id: str
    name: str
    total_amount: float
    spent: float = 0.0
    period: str = "monthly"  # daily, weekly, monthly, project
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = None
    alert_threshold: float = 0.8  # 80% 警報
    
    @property
    def remaining(self) -> float:
        return self.total_amount - self.spent
    
    @property
    def utilization(self) -> float:
        return (self.spent / self.total_amount * 100) if self.total_amount > 0 else 0
    
    @property
    def is_exceeded(self) -> bool:
        return self.spent > self.total_amount
    
    @property
    def is_alert(self) -> bool:
        return self.utilization >= (self.alert_threshold * 100)


@dataclass
class Allocation:
    """分攤配置"""
    entity_type: str  # "user", "team", "project"
    entity_id: str
    share: float  # 分攤比例 (0-1)
    budget_id: str = None


class CostAllocator:
    """成本分攤系統"""
    
    def __init__(self):
        self.entries: List[CostEntry] = []
        self.budgets: Dict[str, Budget] = {}
        self.allocations: List[Allocation] = []
        self.rate_table: Dict[str, float] = {
            # 預設費率 (USD per 1K tokens)
            "gpt-4o": 0.005,
            "gpt-4o-mini": 0.00015,
            "claude-4-sonnet": 0.003,
            "claude-4-opus": 0.015,
            "gemini-2.0-flash": 0.0,
            "minimax-m2.7": 0.0003,
        }
    
    def set_rate(self, model: str, cost_per_1k: float):
        """設定費率"""
        self.rate_table[model] = cost_per_1k
    
    def add_entry(self, project_id: str, user_id: str,
                 cost_type: CostType, amount: float,
                 team_id: str = None, model: str = None,
                 tokens_used: int = 0, description: str = "") -> str:
        """新增成本項目"""
        entry_id = f"cost-{len(self.entries) + 1}"
        
        entry = CostEntry(
            id=entry_id,
            project_id=project_id,
            user_id=user_id,
            team_id=team_id,
            cost_type=cost_type,
            amount=amount,
            model=model,
            tokens_used=tokens_used,
            description=description,
        )
        
        self.entries.append(entry)
        
        # 更新預算
        self._update_budget_spent(project_id, user_id, amount)
        
        return entry_id
    
    def add_api_cost(self, project_id: str, user_id: str,
                    model: str, input_tokens: int, output_tokens: int,
                    team_id: str = None) -> str:
        """新增 API 成本"""
        rate = self.rate_table.get(model, 0)
        
        input_cost = (input_tokens / 1000) * rate
        output_cost = (output_tokens / 1000) * rate * 3  # output 通常更貴
        total = input_cost + output_cost
        
        return self.add_entry(
            project_id=project_id,
            user_id=user_id,
            team_id=team_id,
            cost_type=CostType.API_CALL,
            amount=total,
            model=model,
            tokens_used=input_tokens + output_tokens,
            description=f"{model}: {input_tokens} in + {output_tokens} out"
        )
    
    def create_budget(self, name: str, total_amount: float,
                     period: str = "monthly",
                     start_date: datetime = None,
                     end_date: datetime = None) -> str:
        """建立預算"""
        budget_id = f"budget-{len(self.budgets) + 1}"
        
        budget = Budget(
            id=budget_id,
            name=name,
            total_amount=total_amount,
            period=period,
            start_date=start_date or datetime.now(),
            end_date=end_date,
        )
        
        self.budgets[budget_id] = budget
        return budget_id
    
    def set_budget_allocation(self, entity_type: str, entity_id: str,
                             share: float, budget_id: str = None):
        """設定分攤配置"""
        allocation = Allocation(
            entity_type=entity_type,
            entity_id=entity_id,
            share=share,
            budget_id=budget_id,
        )
        self.allocations.append(allocation)
    
    def _update_budget_spent(self, project_id: str = None, user_id: str = None, amount: float = 0):
        """更新預算支出"""
        for budget in self.budgets.values():
            should_update = False
            
            if budget.period == "project":
                # 專案預算只更新匹配的
                should_update = (budget.name == project_id)
            else:
                # 非專案預算（daily/weekly/monthly）根據 entity 判斷
                # 這裡簡化為更新所有，實際應該根據 user_id/project_id 匹配
                should_update = True
            
            if should_update:
                budget.spent += amount
    
    def get_user_costs(self, user_id: str, 
                      start_date: datetime = None,
                      end_date: datetime = None) -> Dict:
        """取得用戶成本"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        user_entries = [e for e in filtered if e.user_id == user_id]
        
        total = sum(e.amount for e in user_entries)
        by_type = defaultdict(float)
        for e in user_entries:
            by_type[e.cost_type.value] += e.amount
        
        return {
            "user_id": user_id,
            "total": total,
            "by_type": dict(by_type),
            "entries_count": len(user_entries),
        }
    
    def get_project_costs(self, project_id: str,
                          start_date: datetime = None,
                          end_date: datetime = None) -> Dict:
        """取得專案成本"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        project_entries = [e for e in filtered if e.project_id == project_id]
        
        total = sum(e.amount for e in project_entries)
        by_user = defaultdict(float)
        by_team = defaultdict(float)
        by_model = defaultdict(float)
        
        for e in project_entries:
            by_user[e.user_id] += e.amount
            if e.team_id:
                by_team[e.team_id] += e.amount
            if e.model:
                by_model[e.model] += e.amount
        
        return {
            "project_id": project_id,
            "total": total,
            "by_user": dict(by_user),
            "by_team": dict(by_team),
            "by_model": dict(by_model),
            "entries_count": len(project_entries),
        }
    
    def get_team_costs(self, team_id: str,
                       start_date: datetime = None,
                       end_date: datetime = None) -> Dict:
        """取得團隊成本"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        team_entries = [e for e in filtered if e.team_id == team_id]
        
        total = sum(e.amount for e in team_entries)
        by_member = defaultdict(float)
        
        for e in team_entries:
            by_member[e.user_id] += e.amount
        
        return {
            "team_id": team_id,
            "total": total,
            "by_member": dict(by_member),
            "entries_count": len(team_entries),
        }
    
    def get_budget_status(self, budget_id: str = None) -> List[Dict]:
        """取得預算狀態"""
        budgets = [self.budgets[budget_id]] if budget_id else self.budgets.values()
        
        return [
            {
                "id": b.id,
                "name": b.name,
                "total": b.total_amount,
                "spent": b.spent,
                "remaining": b.remaining,
                "utilization": b.utilization,
                "is_exceeded": b.is_exceeded,
                "is_alert": b.is_alert,
                "period": b.period,
            }
            for b in budgets
        ]
    
    def get_cost_breakdown(self, start_date: datetime = None,
                          end_date: datetime = None) -> Dict:
        """取得成本分析"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        total = sum(e.amount for e in filtered)
        
        by_type = defaultdict(float)
        by_project = defaultdict(float)
        by_user = defaultdict(float)
        by_model = defaultdict(float)
        
        for e in filtered:
            by_type[e.cost_type.value] += e.amount
            by_project[e.project_id] += e.amount
            by_user[e.user_id] += e.amount
            if e.model:
                by_model[e.model] += e.amount
        
        return {
            "total": total,
            "by_type": dict(by_type),
            "by_project": dict(by_project),
            "by_user": dict(by_user),
            "by_model": dict(by_model),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            }
        }
    
    def generate_report(self) -> str:
        """生成成本報告"""
        breakdown = self.get_cost_breakdown()
        budget_status = self.get_budget_status()
        
        # 找出超支的預算
        exceeded = [b for b in budget_status if b["is_exceeded"]]
        alerts = [b for b in budget_status if b["is_alert"]]
        
        report = f"""
# 💰 成本報告

## 總覽

| 指標 | 數值 |
|------|------|
| 總成本 | ${breakdown['total']:.4f} |
| 成本項目 | {len(self.entries)} |
| 活跃預算 | {len(self.budgets)} |

---

## 按類型

| 類型 | 金額 |
|------|------|
"""
        
        for cost_type, amount in breakdown['by_type'].items():
            report += f"| {cost_type} | ${amount:.4f} |\n"
        
        report += f"""

## 按專案

| 專案 | 金額 |
|------|------|
"""
        
        for project, amount in breakdown['by_project'].items():
            report += f"| {project} | ${amount:.4f} |\n"
        
        if alerts:
            report += f"""

## ⚠️ 預算警報

"""
            for b in alerts:
                report += f"- {b['name']}: {b['utilization']:.1f}% 已使用\n"
        
        if exceeded:
            report += f"""

## 🔴 超支預算

"""
            for b in exceeded:
                report += f"- {b['name']}: 超支 ${b['spent'] - b['total']:.4f}\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    allocator = CostAllocator()
    
    # 建立預算
    pm_budget = allocator.create_budget("PM 團隊月度預算", 1000.0, "monthly")
    dev_budget = allocator.create_budget("開發團隊月度預算", 2000.0, "monthly")
    
    # 記錄成本
    print("=== Recording Costs ===")
    
    allocator.add_api_cost(
        project_id="project-ai",
        user_id="user-1",
        model="gpt-4o",
        input_tokens=1000,
        output_tokens=500,
        team_id="team-pm"
    )
    
    allocator.add_api_cost(
        project_id="project-ai",
        user_id="user-2",
        model="claude-4-sonnet",
        input_tokens=2000,
        output_tokens=1000,
        team_id="team-dev"
    )
    
    allocator.add_api_cost(
        project_id="project-ai",
        user_id="user-1",
        model="minimax-m2.7",
        input_tokens=5000,
        output_tokens=2000,
        team_id="team-pm"
    )
    
    # 用戶成本
    print("\n=== User Costs ===")
    user1_costs = allocator.get_user_costs("user-1")
    print(f"User 1: ${user1_costs['total']:.4f}")
    print(f"  By type: {user1_costs['by_type']}")
    
    # 專案成本
    print("\n=== Project Costs ===")
    project_costs = allocator.get_project_costs("project-ai")
    print(f"Total: ${project_costs['total']:.4f}")
    print(f"  By user: {project_costs['by_user']}")
    print(f"  By model: {project_costs['by_model']}")
    
    # 團隊成本
    print("\n=== Team Costs ===")
    team_costs = allocator.get_team_costs("team-pm")
    print(f"PM Team: ${team_costs['total']:.4f}")
    
    # 預算狀態
    print("\n=== Budget Status ===")
    for status in allocator.get_budget_status():
        print(f"{status['name']}: {status['utilization']:.1f}% used")
    
    # 報告
    print("\n=== Report ===")
    print(allocator.generate_report())
