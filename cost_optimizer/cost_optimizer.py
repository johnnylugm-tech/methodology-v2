"""
Cost Optimization Suite for methodology-v2

Provides token tracking, model routing, budget alerts, and usage analytics
for building cost-effective AI agents.
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Model pricing (per 1M tokens)
MODEL_PRICING = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    
    # Anthropic
    "claude-3.5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    
    # Google
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-pro": {"input": 0.50, "output": 1.50},
    
    # Meta
    "llama-3.1-70b": {"input": 0.90, "output": 0.90},
    "llama-3.1-8b": {"input": 0.20, "output": 0.20},
}

# Task to model mapping (quality -> best cost model)
TASK_MODEL_MAP = {
    # High quality tasks
    "high": {
        "coding": "claude-3.5-sonnet",
        "analysis": "gpt-4o",
        "writing": "claude-3.5-sonnet",
        "creative": "gpt-4o",
        "research": "gemini-1.5-pro",
        "default": "claude-3.5-sonnet",
    },
    # Medium quality - balance cost/quality
    "medium": {
        "coding": "gpt-4o-mini",
        "analysis": "gpt-4o-mini",
        "writing": "gemini-1.5-flash",
        "creative": "gpt-4o-mini",
        "research": "gemini-1.5-flash",
        "default": "gpt-4o-mini",
    },
    # Low quality - cheapest option
    "low": {
        "coding": "gpt-4o-mini",
        "analysis": "gemini-1.5-flash",
        "writing": "gemini-1.5-flash",
        "creative": "gemini-1.5-flash",
        "research": "gemini-1.5-flash",
        "default": "gemini-1.5-flash",
    },
}


@dataclass
class CostRecord:
    """Single cost record"""
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost: float


class CostOptimizer:
    """
    Cost Optimization Suite for methodology-v2.
    
    Usage:
        optimizer = CostOptimizer(monthly_budget=100)
        optimizer.track(model="gpt-4", prompt_tokens=1000, completion_tokens=500)
        best_model = optimizer.select_model(task="summarize", required_quality="medium")
    """
    
    def __init__(
        self,
        monthly_budget: float = 100,
        alert_threshold: float = 0.8,
        currency: str = "USD"
    ):
        self.monthly_budget = monthly_budget
        self.alert_threshold = alert_threshold
        self.currency = currency
        self.records: List[CostRecord] = []
        self._usage_by_model = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost": 0})
    
    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int = 0,
        timestamp: datetime = None
    ) -> float:
        """
        Track a single LLM call and return cost.
        
        Args:
            model: Model name (e.g., "gpt-4", "claude-3-haiku")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency_ms: Response latency (optional)
            timestamp: Call timestamp (default: now)
        
        Returns:
            Cost in USD
        """
        # Calculate cost
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        # Create record
        record = CostRecord(
            timestamp=timestamp or datetime.now(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost=cost
        )
        
        self.records.append(record)
        
        # Update aggregates
        self._usage_by_model[model]["calls"] += 1
        self._usage_by_model[model]["tokens"] += prompt_tokens + completion_tokens
        self._usage_by_model[model]["cost"] += cost
        
        logger.info(f"Tracked {model}: ${cost:.4f} ({prompt_tokens + completion_tokens} tokens)")
        
        return cost
    
    def _calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a call"""
        pricing = MODEL_PRICING.get(model, {"input": 1.0, "output": 3.0})
        
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def get_current_spend(self) -> float:
        """Get current month spending"""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return sum(
            r.cost for r in self.records
            if r.timestamp >= start_of_month
        )
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget for current month"""
        return self.monthly_budget - self.get_current_spend()
    
    def is_over_budget(self, threshold: float = None) -> bool:
        """Check if over budget"""
        threshold = threshold or self.alert_threshold
        return self.get_current_spend() >= (self.monthly_budget * threshold)
    
    def select_model(
        self,
        task: str,
        required_quality: str = "medium"
    ) -> str:
        """
        Select most cost-effective model for task.
        
        Args:
            task: Task description (e.g., "summarize", "code", "analyze")
            required_quality: "high", "medium", or "low"
        
        Returns:
            Recommended model name
        """
        task_lower = task.lower()
        
        # Detect task type
        task_type = "default"
        for kw, ttype in [
            ("code", "coding"),
            ("program", "coding"),
            ("debug", "coding"),
            ("analyze", "analysis"),
            ("compare", "analysis"),
            ("write", "writing"),
            ("draft", "writing"),
            ("creative", "creative"),
            ("idea", "creative"),
            ("research", "research"),
            ("search", "research"),
        ]:
            if kw in task_lower:
                task_type = ttype
                break
        
        # Get model for quality level
        quality_map = TASK_MODEL_MAP.get(required_quality, TASK_MODEL_MAP["medium"])
        model = quality_map.get(task_type, quality_map["default"])
        
        logger.info(f"Selected {model} for {task_type} (quality: {required_quality})")
        
        return model
    
    def estimate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Estimate cost without tracking"""
        return self._calculate_cost(model, prompt_tokens, completion_tokens)
    
    def predict_next_month(self) -> float:
        """Predict next month's cost based on current usage"""
        if not self.records:
            return 0.0
        
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Days in current month
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        
        days_this_month = (now - start_of_month).days + 1
        days_next_month = (next_month - now).days
        
        current_spend = sum(
            r.cost for r in self.records
            if r.timestamp >= start_of_month
        )
        
        # Daily average
        daily_avg = current_spend / days_this_month if days_this_month > 0 else 0
        
        # Predict
        predicted = daily_avg * days_next_month
        
        logger.info(f"Predicted next month: ${predicted:.2f} (daily avg: ${daily_avg:.2f})")
        
        return predicted
    
    def get_usage_report(self) -> Dict:
        """Get detailed usage report"""
        current_spend = self.get_current_spend()
        
        return {
            "current_spend": current_spend,
            "monthly_budget": self.monthly_budget,
            "remaining": self.get_remaining_budget(),
            "utilization": current_spend / self.monthly_budget if self.monthly_budget > 0 else 0,
            "by_model": dict(self._usage_by_model),
            "total_calls": len(self.records),
            "predicted_next_month": self.predict_next_month(),
        }
    
    def alert(self) -> None:
        """Send budget alert"""
        spend = self.get_current_spend()
        pct = (spend / self.monthly_budget) * 100
        
        logger.warning(
            f"🚨 BUDGET ALERT: ${spend:.2f} / ${self.monthly_budget} ({pct:.1f}%)"
        )


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cost Optimization Suite")
    parser.add_argument("command", choices=["status", "budget", "report"])
    parser.add_argument("--monthly", type=float, help="Monthly budget")
    parser.add_argument("--weekly", action="store_true", help="Weekly report")
    
    args = parser.parse_args()
    
    optimizer = CostOptimizer()
    
    if args.command == "status":
        report = optimizer.get_usage_report()
        print(json.dumps(report, indent=2, default=str))
    
    elif args.command == "budget":
        if args.monthly:
            optimizer.monthly_budget = args.monthly
            print(f"Budget set to ${args.monthly}")
        else:
            print(f"Current budget: ${optimizer.monthly_budget}")
    
    elif args.command == "report":
        report = optimizer.get_usage_report()
        print(json.dumps(report, indent=2, default=str))
