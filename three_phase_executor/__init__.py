"""
Three Phase Executor - 三階段並行執行器

將任務分為三個階段執行：
- Phase 1 (Sequential): 初始化、準備
- Phase 2 (Parallel): 查詢、計算
- Phase 3 (Sequential): 訂單、確認

效能提升：2.06x

Reference: 高鐵訂票實驗 (hsr_booking/approaches/phase1_3phase)
"""

from .three_phase_executor import (
    ThreePhaseExecutor,
    Task,
    TaskResult,
    Phase,
    PhaseMetrics,
    ExecutionResult,
    execute_workflow,
)

__all__ = [
    "ThreePhaseExecutor",
    "Task",
    "TaskResult", 
    "Phase",
    "PhaseMetrics",
    "ExecutionResult",
    "execute_workflow",
]
