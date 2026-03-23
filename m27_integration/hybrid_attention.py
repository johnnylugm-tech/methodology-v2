#!/usr/bin/env python3
"""
Hybrid Attention
===============
M2.7 的混合注意力機制

- Lightning Attention: 長程背景檢索
- Softmax Attention: 局部精密計算

使用方式：

```python
config = AttentionConfig(
    lightning_ratio=0.7,  # 70% Lightning, 30% Softmax
    context_length=100000
)
attention = HybridAttention(config)

result = attention.process(query, context)
```
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum
import numpy as np

class AttentionType(Enum):
    """注意力類型"""
    LIGHTNING = "lightning"  # 長程檢索
    SOFTMAX = "softmax"      # 局部計算
    HYBRID = "hybrid"         # 混合

@dataclass
class AttentionConfig:
    """注意力配置"""
    lightning_ratio: float = 0.7  # Lightning 比例
    context_length: int = 100000   # 上下文長度
    batch_size: int = 1

@dataclass
class AttentionResult:
    """注意力結果"""
    output: np.ndarray
    attention_type: AttentionType
    processing_time: float
    tokens_processed: int

class HybridAttention:
    """
    混合注意力
    
    M2.7 的核心創新：
    - Lightning Attention：用於長程背景檢索（O(n) 複雜度）
    - Softmax Attention：用於局部精密計算（O(n²) 複雜度）
    """
    
    def __init__(self, config: AttentionConfig = None):
        self.config = config or AttentionConfig()
    
    def process(
        self,
        query: np.ndarray,
        context: np.ndarray
    ) -> AttentionResult:
        """
        處理混合注意力
        
        Args:
            query: 查詢向量
            context: 上下文向量
        
        Returns:
            AttentionResult: 注意力結果
        """
        import time
        start = time.time()
        
        # 分割 Lightning 和 Softmax 部分
        lightning_size = int(len(context) * self.config.lightning_ratio)
        lightning_context = context[:lightning_size]
        softmax_context = context[lightning_size:]
        
        # Lightning Attention（快速長程檢索）
        lightning_output = self._lightning_attention(query, lightning_context)
        
        # Softmax Attention（局部精密計算）
        softmax_output = self._softmax_attention(query, softmax_context)
        
        # 混合輸出
        output = (
            self.config.lightning_ratio * lightning_output +
            (1 - self.config.lightning_ratio) * softmax_output
        )
        
        processing_time = time.time() - start
        
        return AttentionResult(
            output=output,
            attention_type=AttentionType.HYBRID,
            processing_time=processing_time,
            tokens_processed=len(context)
        )
    
    def _lightning_attention(self, query: np.ndarray, context: np.ndarray) -> np.ndarray:
        """Lightning Attention - O(n) 線性注意力"""
        # 簡化實現
        scores = np.dot(context, query)
        # Lightning 使用 linear attention 近似
        return np.tanh(scores) * 0.1
    
    def _softmax_attention(self, query: np.ndarray, context: np.ndarray) -> np.ndarray:
        """Softmax Attention - O(n²) 標準注意力"""
        if len(context) == 0:
            return np.zeros_like(query)
        
        scores = np.dot(context, query)
        weights = self._softmax(scores)
        return np.sum(context * weights[:, np.newaxis], axis=0)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax 函數"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)
