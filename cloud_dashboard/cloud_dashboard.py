"""
Cloud Dashboard for methodology-v2 - SaaS-ready monitoring dashboard
"""

import time
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Metrics:
    agents: int = 0
    tasks_completed: int = 0
    avg_latency: float = 0.0
    error_rate: float = 0.0
    cost_today: float = 0.0


class CloudDashboard:
    """Cloud Dashboard for methodology-v2"""
    
    def __init__(self, api_key: str = "", project: str = "default"):
        self.api_key = api_key
        self.project = project
        self.metrics_history: List[Metrics] = []
        self.alerts: List[Dict] = []
        self.team: List[Dict] = []
        self.budget_limit: float = None
    
    def get_metrics(self, current: Dict = None) -> Metrics:
        if current:
            m = Metrics(
                agents=current.get("agents", 0),
                tasks_completed=current.get("tasks_completed", 0),
                avg_latency=current.get("avg_latency", 0.0),
                error_rate=current.get("error_rate", 0.0),
                cost_today=current.get("cost_today", 0.0)
            )
            self.metrics_history.append(m)
            return m
        return Metrics()
    
    def create_alert(self, name: str, condition: str, channels: List[str] = None):
        alert = {"name": name, "condition": condition, "channels": channels or ["email"]}
        self.alerts.append(alert)
        return alert
    
    def invite_member(self, email: str, role: str = "viewer"):
        member = {"email": email, "role": role}
        self.team.append(member)
        return member
    
    def set_budget(self, monthly_limit: float):
        self.budget_limit = monthly_limit
    
    def get_budget_status(self) -> Dict:
        current = self.get_metrics()
        if not self.budget_limit:
            return {"configured": False}
        return {
            "configured": True,
            "used": current.cost_today,
            "limit": self.budget_limit,
            "percentage": current.cost_today / self.budget_limit
        }


if __name__ == "__main__":
    # Demo
    dashboard = CloudDashboard(api_key="demo", project="test")
    dashboard.set_budget(500)
    dashboard.get_metrics({"agents": 5, "tasks_completed": 100, "cost_today": 25.50})
    dashboard.create_alert("High Cost", "cost > 100", ["slack"])
    dashboard.invite_member("john@example.com", "developer")
    print("Cloud Dashboard initialized!")
