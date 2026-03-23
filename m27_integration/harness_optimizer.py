#!/usr/bin/env python3
"""
Harness Optimizer
================
M2.7 的 Agent Harness 自動優化

功能：
- 自動優化採樣設置
- 自動優化工作流規則
- 減少人工維護負擔

使用方式：

```python
optimizer = HarnessOptimizer()

result = optimizer.optimize(
    current_config,
    evaluation_results
)

print(f"New config: {result.optimized_config}")
print(f"Improvement: {result.improvement}%")
```
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from datetime import datetime

@dataclass
class OptimizationResult:
    """優化結果"""
    optimized_config: Dict[str, Any]
    improvement: float  # 百分比
    changes: List[str]
    iterations_needed: int

class HarnessOptimizer:
    """
    Harness 優化器
    
    自動優化 Agent Harness 的配置參數
    """
    
    def __init__(self):
        self.default_configs = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 4096,
            "timeout": 30,
            "max_retries": 3
        }
    
    def optimize(
        self,
        current_config: Dict[str, Any],
        evaluation_results: List[Dict]
    ) -> OptimizationResult:
        """
        優化配置
        
        Args:
            current_config: 當前配置
            evaluation_results: 評估結果列表
        
        Returns:
            OptimizationResult: 優化結果
        """
        import copy
        
        optimized = copy.deepcopy(current_config)
        changes = []
        
        # 分析評估結果
        avg_score = sum(r.get("score", 0) for r in evaluation_results) / len(evaluation_results) if evaluation_results else 0
        
        # 根據評估結果調整參數
        if avg_score < 0.7:
            # 分數太低，降低 temperature
            optimized["temperature"] = max(0.1, optimized.get("temperature", 0.7) - 0.1)
            changes.append(f"temperature: {optimized['temperature']}")
        
        if any(r.get("timeout_issue", False) for r in evaluation_results):
            # 有逾時問題，增加 timeout
            optimized["timeout"] = optimized.get("timeout", 30) * 1.5
            changes.append(f"timeout: {optimized['timeout']}")
        
        if any(r.get("memory_issue", False) for r in evaluation_results):
            # 有記憶體問題，減少 max_tokens
            optimized["max_tokens"] = int(optimized.get("max_tokens", 4096) * 0.8)
            changes.append(f"max_tokens: {optimized['max_tokens']}")
        
        improvement = (0.8 - avg_score) * 100 if avg_score < 0.8 else 5
        
        return OptimizationResult(
            optimized_config=optimized,
            improvement=improvement,
            changes=changes,
            iterations_needed=len(evaluation_results)
        )
