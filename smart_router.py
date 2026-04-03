#!/usr/bin/env python3
"""
Smart Router - 基於 Model Router 的智慧路由

根據任務自動選擇最適合的 LLM
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Multi-Provider Abstraction Layer
from provider_abstraction import ModelRouter, ProviderType


class TaskType(Enum):
    """任務類型"""
    CODING = "coding"           # 編程
    REVIEW = "review"           # 審查
    WRITING = "writing"         # 寫作
    ANALYSIS = "analysis"       # 分析
    TRANSLATION = "translation" # 翻譯
    CREATIVE = "creative"      # 創意
    GENERAL = "general"         # 一般


class BudgetLevel(Enum):
    """預算等級"""
    LOW = "low"       # 低成本
    MEDIUM = "medium"  # 中成本
    HIGH = "high"     # 高成本


@dataclass
class ModelInfo:
    """模型資訊"""
    name: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    strengths: List[str] = field(default_factory=list)
    best_for: List[TaskType] = field(default_factory=list)


@dataclass
class RoutingResult:
    """路由結果"""
    model: str
    provider: str
    estimated_cost: float
    reasoning: str
    task_type: TaskType


class SmartRouter:
    """智慧路由器 (整合 Cost Optimizer)"""
    
    # 預設配置
    DEFAULT_CONFIG = {
        "auto_route": True,       # 自動路由（預設開）
        "default_model": "gemini-pro",  # 預設模型
        "budget": "medium",       # 預算等級
        "fallback_model": "gpt-3.5-turbo",  # 備用模型
        "enable_cost_tracking": True,  # 整合 cost_optimizer
        "monthly_budget": 100.0,   # 月度預算
        "cost_alert_threshold": 0.8,  # 警報閾值
    }
    
    # Cost Optimizer 整合
    COST_TRACKING = {
        "total_spent": 0.0,
        "by_model": {},
        "by_task_type": {},
        "alerts_triggered": 0,
    }
    
    # 預設模型庫
    DEFAULT_MODELS = {
        # OpenAI
        "gpt-4": ModelInfo(
            name="gpt-4",
            provider="OpenAI",
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            strengths=["coding", "reasoning", "analysis"],
            best_for=[TaskType.CODING, TaskType.ANALYSIS]
        ),
        "gpt-4-turbo": ModelInfo(
            name="gpt-4-turbo",
            provider="OpenAI",
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            strengths=["coding", "fast"],
            best_for=[TaskType.CODING]
        ),
        "gpt-3.5-turbo": ModelInfo(
            name="gpt-3.5-turbo",
            provider="OpenAI",
            cost_per_1k_input=0.0005,
            cost_per_1k_output=0.0015,
            strengths=["speed", "cheap"],
            best_for=[TaskType.GENERAL]
        ),
        
        # Anthropic
        "claude-3-opus": ModelInfo(
            name="claude-3-opus",
            provider="Anthropic",
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            strengths=["coding", "reasoning", "writing"],
            best_for=[TaskType.CODING, TaskType.WRITING, TaskType.REVIEW]
        ),
        "claude-3-sonnet": ModelInfo(
            name="claude-3-sonnet",
            provider="Anthropic",
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            strengths=["balanced"],
            best_for=[TaskType.GENERAL]
        ),
        
        # Google
        "gemini-pro": ModelInfo(
            name="gemini-pro",
            provider="Google",
            cost_per_1k_input=0.00125,
            cost_per_1k_output=0.005,
            strengths=["multimodal", "fast"],
            best_for=[TaskType.GENERAL, TaskType.ANALYSIS]
        ),
        
        # MiniMax
        "minimax": ModelInfo(
            name="minimax",
            provider="MiniMax",
            cost_per_1k_input=0.001,
            cost_per_1k_output=0.003,
            strengths=["speed", "cheap", "chinese", "self-evolving"],
            best_for=[TaskType.TRANSLATION, TaskType.WRITING, TaskType.CODING]
        ),
        "minimax-m2.7": ModelInfo(
            name="minimax-m2.7",
            provider="MiniMax",
            cost_per_1k_input=0.0003,
            cost_per_1k_output=0.0012,
            strengths=["self-evolving", "reasoning", "coding", "agents"],
            best_for=[TaskType.CODING, TaskType.ANALYSIS, TaskType.REVIEW]
        ),
    }
    
    # 任務類型關鍵詞
    TASK_KEYWORDS = {
        TaskType.CODING: ["code", "program", "function", "class", "implement", "debug", "refactor"],
        TaskType.REVIEW: ["review", "critique", "check", "audit", "assess"],
        TaskType.WRITING: ["write", "draft", "compose", "create", "content"],
        TaskType.ANALYSIS: ["analyze", "compare", "evaluate", "study", "examine"],
        TaskType.TRANSLATION: ["translate", "convert", "transform"],
        TaskType.CREATIVE: ["idea", "brainstorm", "creative", "imagine", "design"],
        TaskType.GENERAL: ["help", "answer", "question", "what", "how"],
    }
    
    def __init__(self, budget: str = None, custom_models: Dict[str, ModelInfo] = None, 
                 auto_route: bool = None, config: Dict = None):
        """
        初始化
        
        Args:
            budget: 預算等級 (low/medium/high)，如果 auto_route=False 時忽略
            custom_models: 自定義模型
            auto_route: 自動路由開關 (None=讀取配置)
            config: 自定義配置 (會合併到預設配置)
        """
        # 載入配置
        self.config = {**self.DEFAULT_CONFIG}
        if config:
            self.config.update(config)
        
        # 處理 auto_route
        if auto_route is not None:
            self.config["auto_route"] = auto_route
        
        # 處理 budget
        actual_budget = budget if budget else self.config.get("budget", "medium")
        self.budget = BudgetLevel(actual_budget)
        
        self.models = {**self.DEFAULT_MODELS}
        if custom_models:
            self.models.update(custom_models)
        
        # 檢查環境變數中的 API Key
        self._check_api_keys()
        
        print(f"[SmartRouter] Auto-route: {'ON' if self.config['auto_route'] else 'OFF'}")
        print(f"[SmartRouter] Default model: {self.config['default_model']}")
    
    def _check_api_keys(self):
        """檢查 API Key"""
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY"),
            "minimax": os.getenv("MINIMAX_API_KEY"),
        }
    
    def route(self, task: str, force_model: str = None) -> RoutingResult:
        """
        路由任務到最適合的模型
        
        Args:
            task: 任務描述
            force_model: 強制使用某個模型
            
        Returns:
            RoutingResult
        """
        # 如果 auto_route 關閉，使用預設模型
        if not self.config["auto_route"]:
            default_model = self.config["default_model"]
            print(f"[SmartRouter] Auto-route OFF, using default: {default_model}")
            return self._route_to_model(default_model, task)
        
        # 如果指定模型
        if force_model:
            return self._route_to_model(force_model, task)
        
        # 識別任務類型
        task_type = self._classify_task(task)
        
        # 根據預算和任務類型選擇模型
        return self._select_model(task_type, task)
    
    def _classify_task(self, task: str) -> TaskType:
        """識別任務類型"""
        task_lower = task.lower()
        
        scores = {tt: 0 for tt in TaskType}
        
        for task_type, keywords in self.TASK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    scores[task_type] += 1
        
        # 返回得分最高的
        max_score = max(scores.values())
        if max_score == 0:
            return TaskType.GENERAL
        
        for tt, score in scores.items():
            if score == max_score:
                return tt
    
    def _select_model(self, task_type: TaskType, task: str) -> RoutingResult:
        """選擇模型"""
        # 根據預算過濾
        available_models = self._filter_by_budget()
        
        # 根據任務類型排序
        scored_models = []
        for name, model in available_models.items():
            score = 0
            
            # 任務類型匹配
            if task_type in model.best_for:
                score += 10
            
            # 擅長領域匹配
            for strength in model.strengths:
                if strength in task.lower():
                    score += 5
            
            # 可用 API Key 加分
            provider_key = model.provider.lower()
            if self.api_keys.get(provider_key):
                score += 20
            
            scored_models.append((name, model, score))
        
        # 按分數排序
        scored_models.sort(key=lambda x: x[2], reverse=True)
        
        if not scored_models:
            # 沒有可用模型，回退到預設
            return self._route_to_model("gpt-3.5-turbo", task)
        
        # 選擇第一個
        selected = scored_models[0]
        model_name = selected[0]
        model = selected[1]
        
        # 估算成本
        estimated_cost = self._estimate_cost(task, model)
        
        return RoutingResult(
            model=model_name,
            provider=model.provider,
            estimated_cost=estimated_cost,
            reasoning=f"任務類型: {task_type.value}, 擅長: {', '.join([t.value for t in model.best_for])}",
            task_type=task_type
        )
    
    def _filter_by_budget(self) -> Dict[str, ModelInfo]:
        """根據預算過濾模型"""
        max_cost = {
            BudgetLevel.LOW: 0.005,
            BudgetLevel.MEDIUM: 0.02,
            BudgetLevel.HIGH: 0.1,
        }[self.budget]
        
        return {
            name: model 
            for name, model in self.models.items()
            if (model.cost_per_1k_input + model.cost_per_1k_output) / 2 <= max_cost
        }
    
    def _route_to_model(self, model_name: str, task: str) -> RoutingResult:
        """路由到指定模型"""
        model = self.models.get(model_name)
        if not model:
            model = self.DEFAULT_MODELS.get(model_name)
        
        if not model:
            return RoutingResult(
                model=model_name,
                provider="Unknown",
                estimated_cost=0,
                reasoning="未知模型",
                task_type=self._classify_task(task)
            )
        
        task_type = self._classify_task(task)
        
        return RoutingResult(
            model=model_name,
            provider=model.provider,
            estimated_cost=self._estimate_cost(task, model),
            reasoning=f"強制使用 {model_name}",
            task_type=task_type
        )
    
    def _estimate_cost(self, task: str, model: ModelInfo) -> float:
        """估算成本"""
        # 假設平均輸入 500 tokens，輸出 300 tokens
        input_tokens = len(task) // 4
        output_tokens = input_tokens * 0.6
        
        return (input_tokens / 1000 * model.cost_per_1k_input + 
                output_tokens / 1000 * model.cost_per_1k_output)
    
    def list_models(self) -> List[Dict]:
        """列出可用模型"""
        return [
            {
                "name": m.name,
                "provider": m.provider,
                "cost_per_1k_input": m.cost_per_1k_input,
                "cost_per_1k_output": m.cost_per_1k_output,
                "best_for": [t.value for t in m.best_for],
                "available": bool(self.api_keys.get(m.provider.lower()))
            }
            for m in self.models.values()
        ]
    
    def calculate_savings(self, scenarios: List[Dict] = None) -> Dict:
        """
        計算並說明節省成本
        
        節省成本的三大策略：
        1. 智慧路由 - 根據任務複雜度選擇最便宜的合適模型
        2. 快取 - 重複請求直接返回快取結果
        3. 並行優化 - 批量處理比單一請求便宜
        
        情境 A: 1000 次混合請求 → 節省 90%
        情境 B: 高快取場景 (70% 命中) → 節省 70%
        情境 C: 簡單任務為主 + 快取 → 節省 99%
        """
        default_scenarios = [
            {"name": "典型混合任務", "tasks": 1000, "mix": {"simple": 0.6, "medium": 0.3, "complex": 0.1}, "cache": 0.0},
            {"name": "高快取場景", "tasks": 1000, "mix": {"simple": 0.6, "medium": 0.3, "complex": 0.1}, "cache": 0.7},
            {"name": "簡單任務為主", "tasks": 1000, "mix": {"simple": 0.9, "medium": 0.09, "complex": 0.01}, "cache": 0.9},
        ]
        
        scenarios = scenarios or default_scenarios
        results = []
        
        for s in scenarios:
            direct = s["tasks"] * 0.03
            routed = (s["tasks"] * s["mix"]["simple"] * 0.001 +
                      s["tasks"] * s["mix"]["medium"] * 0.003 +
                      s["tasks"] * s["mix"]["complex"] * 0.015)
            final = routed * (1 - s["cache"])
            savings_rate = ((direct - final) / direct * 100) if direct > 0 else 0
            
            results.append({
                "scenario": s["name"],
                "direct_cost": round(direct, 2),
                "routed_cost": round(routed, 2),
                "final_cost": round(final, 2),
                "savings_rate": round(savings_rate, 1),
            })
        
        return {"scenarios": results, "explanation": "節省取決於任務複雜度分佈和快取命中率"}


    def set_budget(self, budget: str):
        """設定預算"""
        self.budget = BudgetLevel(budget)


# ============================================================================
# Phase-based Routing
# ============================================================================

def route_by_phase(phase: int, state_path: str = None, task_hint: str = None) -> RoutingResult:
    """
    根據 Phase 自動選擇最適合的模型
    
    Args:
        phase: 當前 Phase (1-8)
        state_path: 可選，state.json 路徑，會自動讀取 current_step/current_module
        task_hint: 可選，任務提示（如 "coding", "review"）
    
    Returns:
        RoutingResult: 模型選擇結果
    """
    # 使用 Multi-Provider Abstraction Layer
    router = ModelRouter()
    info = router.route_with_info(phase, task_hint, state_path)
    
    return RoutingResult(
        model=info["model"],
        provider=info["provider"],
        estimated_cost=0.01,
        reasoning=f"Phase {phase} ({info.get('step', '?')}/{info.get('module', '?')}): {info['reasoning']}",
        task_type=TaskType.CODING
    )


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Smart Router CLI")
    parser.add_argument("--phase", type=int, help="Phase number (1-8)")
    parser.add_argument("--state-path", type=str, help="Path to state.json")
    parser.add_argument("--task", type=str, help="Task description (for regular routing)")
    args = parser.parse_args()
    
    if args.phase is not None:
        result = route_by_phase(args.phase, args.state_path)
        print(f"Model: {result.model}")
        print(f"Provider: {result.provider}")
        print(f"Estimated Cost: ${result.estimated_cost:.4f}")
        print(f"Reasoning: {result.reasoning}")
    elif args.task:
        router = SmartRouter()
        result = router.route(args.task)
        print(f"Model: {result.model}")
        print(f"Provider: {result.provider}")
        print(f"Estimated Cost: ${result.estimated_cost:.4f}")
        print(f"Reasoning: {result.reasoning}")
    else:
        parser.print_help()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    main()

    # ==================== Cost Optimizer 整合 ====================
    
    def track_usage(self, model: str, input_tokens: int, output_tokens: int,
                   task_type: str = None):
        """記錄使用量 (整合 cost_optimizer)"""
        model_info = self.models.get(model)
        if not model_info:
            return
        
        cost = (input_tokens / 1000 * model_info.cost_per_1k_input +
                output_tokens / 1000 * model_info.cost_per_1k_output)
        
        self.COST_TRACKING["total_spent"] += cost
        
        if model not in self.COST_TRACKING["by_model"]:
            self.COST_TRACKING["by_model"][model] = 0
        self.COST_TRACKING["by_model"][model] += cost
        
        if task_type:
            if task_type not in self.COST_TRACKING["by_task_type"]:
                self.COST_TRACKING["by_task_type"][task_type] = 0
            self.COST_TRACKING["by_task_type"][task_type] += cost
    
    def get_cost_summary(self) -> Dict:
        """取得成本摘要"""
        return {
            "total_spent": self.COST_TRACKING["total_spent"],
            "monthly_budget": self.DEFAULT_CONFIG["monthly_budget"],
            "remaining": self.DEFAULT_CONFIG["monthly_budget"] - self.COST_TRACKING["total_spent"],
            "utilization": (self.COST_TRACKING["total_spent"] / 
                           max(1, self.DEFAULT_CONFIG["monthly_budget"]) * 100),
            "by_model": self.COST_TRACKING["by_model"],
            "by_task_type": self.COST_TRACKING["by_task_type"],
        }
    
    def is_over_budget(self) -> bool:
        """檢查是否超出預算"""
        return (self.COST_TRACKING["total_spent"] >= 
                self.DEFAULT_CONFIG["monthly_budget"] * 
                self.DEFAULT_CONFIG["cost_alert_threshold"])
    
    def get_cost_alert(self) -> Dict:
        """取得預算警報"""
        summary = self.get_cost_summary()
        
        if self.is_over_budget():
            return {
                "level": "critical" if summary["utilization"] >= 100 else "warning",
                "message": f"已使用 {summary['utilization']:.1f}% 預算",
                "spent": summary["total_spent"],
                "remaining": summary["remaining"],
            }
        return None
    
    def select_cost_efficient_model(self, task: str, 
                                    required_quality: str = "medium") -> str:
        """選擇最便宜的合適模型"""
        quality_budget = {
            "high": 0.05,
            "medium": 0.01,
            "low": 0.002,
        }.get(required_quality, 0.01)
        
        candidates = [
            (name, model) for name, model in self.models.items()
            if (model.cost_per_1k_input + model.cost_per_1k_output) / 2 <= quality_budget
        ]
        
        if not candidates:
            return min(self.models.keys(), 
                     key=lambda n: self.models[n].cost_per_1k_input)
        
        candidates.sort(key=lambda x: x[1].cost_per_1k_input)
        return candidates[0][0]
