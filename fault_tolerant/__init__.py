"""
Fault Tolerant - 容錯系統

提供 AI Agent 的錯誤處理機制：
- Retry: 指數退避重試
- Circuit Breaker: 熔斷機制
- Fallback: 備援方案
- Output Validator: 輸出驗證
"""

from .fault_tolerant import (
    FaultTolerantExecutor,
    CircuitBreaker,
    CircuitState,
    OutputValidator,
    RetryConfig,
    CircuitBreakerConfig,
    ExecutionResult,
    with_fault_tolerance,
)

__all__ = [
    "FaultTolerantExecutor",
    "CircuitBreaker",
    "CircuitState",
    "OutputValidator", 
    "RetryConfig",
    "CircuitBreakerConfig",
    "ExecutionResult",
    "with_fault_tolerance",
]
