"""
M2.7 Self-Evolving Integration
==============================
支援 MiniMax M2.7 的自我演化能力

M2.7 特性：
- Hybrid Attention (Lightning + Softmax)
- 100+ 自我迭代循環
- 失敗路徑自動分析
- 自動優化 Agent Harness
"""

from .hybrid_attention import HybridAttention, AttentionConfig
from .self_iteration import SelfIteration, IterationResult
from .failure_analyzer import FailureAnalyzer, FailurePath
from .harness_optimizer import HarnessOptimizer, OptimizationResult

__all__ = [
    'HybridAttention',
    'AttentionConfig',
    'SelfIteration',
    'IterationResult',
    'FailureAnalyzer',
    'FailurePath',
    'HarnessOptimizer',
    'OptimizationResult',
]
