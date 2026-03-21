"""
Auto Optimizer - 自動優化器

每小時自動分析趨勢、收集痛點、產生改進提案並實施。
"""

from .auto_optimizer import AutoOptimizer, should_run, mark_run

__all__ = ["AutoOptimizer", "should_run", "mark_run"]
