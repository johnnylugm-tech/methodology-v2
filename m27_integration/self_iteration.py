#!/usr/bin/env python3
"""
Self Iteration
=============
M2.7 的自我迭代優化

100+ 次迭代循環：
1. 分析失敗路徑
2. 修改自身代碼架構
3. 重新運行評估
4. 如果變好則保留

使用方式：

```python
iteration = SelfIteration(max_iterations=100)

for i, result in iteration.run():
    if result.improved:
        print(f"Iteration {i}: improved by {result.improvement}%")
    else:
        print(f"Iteration {i}: no improvement, stopping")
```
"""

from dataclasses import dataclass
from typing import List, Callable, Optional
from datetime import datetime
import json

@dataclass
class IterationResult:
    """迭代結果"""
    iteration: int
    score: float
    previous_score: float
    improvement: float
    improved: bool
    changes_made: List[str]
    timestamp: datetime

class SelfIteration:
    """
    自我迭代器
    
    M2.7 的核心能力：
    - 超過 100 次的自我迭代循環
    - 每次迭代分析失敗並改進
    - 內部測試中實現 30% 性能提升
    """
    
    def __init__(
        self,
        max_iterations: int = 100,
        improvement_threshold: float = 0.01  # 1% 改進閾值
    ):
        self.max_iterations = max_iterations
        self.improvement_threshold = improvement_threshold
        self.results: List[IterationResult] = []
        self.current_score = 0.0
    
    def run(
        self,
        evaluate_fn: Callable[[], float],
        improve_fn: Callable[[float], List[str]]
    ):
        """
        運行自我迭代
        
        Args:
            evaluate_fn: 評估函數，返回當前分數
            improve_fn: 改進函數，接收當前分數，返回改變列表
        
        Yields:
            IterationResult: 每次迭代的結果
        """
        self.current_score = evaluate_fn()
        
        for i in range(self.max_iterations):
            previous_score = self.current_score
            
            # 分析失敗並改進
            changes = improve_fn(self.current_score)
            
            # 重新評估
            self.current_score = evaluate_fn()
            
            # 計算改進
            improvement = (self.current_score - previous_score) / previous_score if previous_score > 0 else 0
            improved = improvement > self.improvement_threshold
            
            # 記錄結果
            result = IterationResult(
                iteration=i + 1,
                score=self.current_score,
                previous_score=previous_score,
                improvement=improvement,
                improved=improved,
                changes_made=changes,
                timestamp=datetime.now()
            )
            self.results.append(result)
            
            yield result
            
            # 如果沒有改進，可以提前停止
            if not improved and i > 10:  # 至少嘗試 10 次
                # 繼續迭代但不停止，讓模型繼續探索
                pass
    
    def get_best_result(self) -> Optional[IterationResult]:
        """取得最佳結果"""
        if not self.results:
            return None
        return max(self.results, key=lambda r: r.score)
    
    def get_summary(self) -> dict:
        """取得迭代摘要"""
        return {
            "total_iterations": len(self.results),
            "improved_count": sum(1 for r in self.results if r.improved),
            "best_score": self.get_best_result().score if self.results else 0,
            "total_improvement": sum(r.improvement for r in self.results)
        }
