#!/usr/bin/env python3
"""
Fault Tolerant - 容錯系統

提供 AI Agent 的錯誤處理機制：
- Retry: 指數退避重試
- Circuit Breaker: 熔斷機制
- Fallback: 備援方案
- Timeout: 逾時保護
- Output Validator: 輸出驗證（針對 LLM hallucination）

Reference:
- Resilience Circuit Breakers for Agentic AI
- Preventing Cascading Failures in AI Agents
"""
import asyncio
import time
import functools
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
from collections import deque


class CircuitState(Enum):
    """熔斷器狀態"""
    CLOSED = "closed"      # 正常
    OPEN = "open"         # 開啟（熔斷）
    HALF_OPEN = "half_open"  # 半開（測試）


@dataclass
class RetryConfig:
    """重試配置"""
    max_attempts: int = 3
    base_delay: float = 0.1  # 秒
    max_delay: float = 10.0   # 秒
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """熔斷器配置"""
    failure_threshold: int = 5      # 失敗次數閾值
    success_threshold: int = 2      # 成功次數閾值（半開→關閉）
    timeout: float = 30.0           # 秒（自動嘗試恢復）
    half_open_max_calls: int = 3    # 半開狀態最大調用數


@dataclass
class ValidationRule:
    """輸出驗證規則"""
    name: str
    check: Callable[[Any], bool]
    error_message: str


@dataclass
class ExecutionResult:
    """執行結果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    validation_passed: bool = True


class OutputValidator:
    """輸出驗證器 - 檢測 LLM hallucination"""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
        self.validation_log: List[Dict] = []
    
    def add_rule(self, name: str, check: Callable[[Any], bool], error_message: str):
        """添加驗證規則"""
        self.rules.append(ValidationRule(name, check, error_message))
    
    def add_keyword_rule(self, keywords: List[str]):
        """添加關鍵字規則 - 檢測是否包含敏感詞"""
        self.add_rule(
            name="keyword_check",
            check=lambda x: not any(k in str(x).lower() for k in keywords),
            error_message=f"Output contains sensitive keywords"
        )
    
    def add_json_structure_rule(self, required_fields: List[str]):
        """添加 JSON 結構規則"""
        def check_json(x):
            if isinstance(x, dict):
                return all(f in x for f in required_fields)
            if isinstance(x, str):
                import json
                try:
                    data = json.loads(x)
                    return all(f in data for f in required_fields)
                except:
                    return False
            return False
        
        self.add_rule(
            name="json_structure",
            check=check_json,
            error_message=f"Missing required fields: {required_fields}"
        )
    
    def validate(self, output: Any) -> tuple[bool, List[str]]:
        """驗證輸出"""
        errors = []
        for rule in self.rules:
            try:
                if not rule.check(output):
                    errors.append(f"{rule.name}: {rule.error_message}")
            except Exception as e:
                errors.append(f"{rule.name}: validation error - {e}")
        
        self.validation_log.append({
            "timestamp": datetime.now().isoformat(),
            "output_type": type(output).__name__,
            "passed": len(errors) == 0,
            "errors": errors
        })
        
        return len(errors) == 0, errors


class CircuitBreaker:
    """熔斷器 - 防止級聯故障"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.call_history: deque = deque(maxlen=100)
    
    def can_execute(self) -> bool:
        """檢查是否可以執行"""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # 檢查是否過了 timeout
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed > self.config.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
            return False
        
        # HALF_OPEN 狀態
        return True
    
    def record_success(self):
        """記錄成功"""
        self.success_count += 1
        self.call_history.append({"success": True, "time": datetime.now()})
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                print(f"🔄 Circuit {self.name}: CLOSED")
    
    def record_failure(self):
        """記錄失敗"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.call_history.append({"success": False, "time": datetime.now()})
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            print(f"⚠️ Circuit {self.name}: OPEN (half_open failed)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"⚠️ Circuit {self.name}: OPEN (threshold reached)")
    
    def get_state(self) -> Dict:
        """取得狀態"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "successes": self.success_count
        }


class FaultTolerantExecutor:
    """容錯執行器"""
    
    def __init__(
        self,
        name: str = "default",
        retry_config: RetryConfig = None,
        circuit_config: CircuitBreakerConfig = None,
        timeout: float = 30.0,
        fallback: Callable = None,
        validator: OutputValidator = None
    ):
        self.name = name
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        self.timeout = timeout
        self.fallback = fallback
        self.validator = validator or OutputValidator()
        self.execution_log: List[Dict] = []
    
    async def execute(self, func: Callable, *args, **kwargs) -> ExecutionResult:
        """執行函數（帶容錯）"""
        # 1. 檢查熔斷器
        if not self.circuit_breaker.can_execute():
            return await self._handle_circuit_open()
        
        # 2. 執行並重試
        for attempt in range(self.retry_config.max_attempts + 1):
            try:
                # 執行函數
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.timeout
                    )
                else:
                    result = await asyncio.wait_for(
                        asyncio.to_thread(func, *args, **kwargs),
                        timeout=self.timeout
                    )
                
                # 3. 驗證輸出
                validation_passed, errors = self.validator.validate(result)
                
                if validation_passed:
                    self.circuit_breaker.record_success()
                    self._log_execution(attempt + 1, True, result)
                    return ExecutionResult(
                        success=True,
                        result=result,
                        attempts=attempt + 1,
                        circuit_state=self.circuit_breaker.state,
                        validation_passed=True
                    )
                else:
                    # 驗證失敗，重試
                    print(f"⚠️ Validation failed: {errors}")
                    if attempt < self.retry_config.max_attempts:
                        await self._wait_before_retry(attempt)
                    else:
                        return ExecutionResult(
                            success=False,
                            error=f"Validation failed: {errors}",
                            attempts=attempt + 1,
                            circuit_state=self.circuit_breaker.state,
                            validation_passed=False
                        )
            
            except asyncio.TimeoutError:
                error = f"Timeout after {self.timeout}s"
                print(f"⏱️ {error}")
                self.circuit_breaker.record_failure()
                if attempt < self.retry_config.max_attempts:
                    await self._wait_before_retry(attempt)
                else:
                    return await self._handle_failure(error, attempt + 1)
            
            except Exception as e:
                error = str(e)
                print(f"❌ Error: {error}")
                self.circuit_breaker.record_failure()
                if attempt < self.retry_config.max_attempts:
                    await self._wait_before_retry(attempt)
                else:
                    return await self._handle_failure(error, attempt + 1)
        
        return await self._handle_failure("Max attempts reached", self.retry_config.max_attempts)
    
    async def _wait_before_retry(self, attempt: int):
        """等待後重試（指數退避）"""
        delay = min(
            self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random())
        await asyncio.sleep(delay)
    
    async def _handle_failure(self, error: str, attempts: int) -> ExecutionResult:
        """處理失敗"""
        if self.fallback:
            try:
                if asyncio.iscoroutinefunction(self.fallback):
                    fallback_result = await self.fallback()
                else:
                    fallback_result = self.fallback()
                return ExecutionResult(
                    success=True,
                    result=fallback_result,
                    error=f"Fallback used: {error}",
                    attempts=attempts,
                    circuit_state=self.circuit_breaker.state
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    error=f"Fallback also failed: {e}",
                    attempts=attempts,
                    circuit_state=self.circuit_breaker.state
                )
        
        return ExecutionResult(
            success=False,
            error=error,
            attempts=attempts,
            circuit_state=self.circuit_breaker.state
        )
    
    async def _handle_circuit_open(self) -> ExecutionResult:
        """處理熔斷狀態"""
        if self.fallback:
            try:
                return ExecutionResult(
                    success=True,
                    result=await self.fallback() if asyncio.iscoroutinefunction(self.fallback) else self.fallback(),
                    error="Circuit open - fallback used",
                    circuit_state=self.circuit_breaker.state
                )
            except:
                pass
        
        return ExecutionResult(
            success=False,
            error="Circuit breaker is open",
            circuit_state=self.circuit_breaker.state
        )
    
    def _log_execution(self, attempts: int, success: bool, result: Any):
        """記錄執行"""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "function": self.name,
            "attempts": attempts,
            "success": success,
            "circuit_state": self.circuit_breaker.state.value
        })
    
    def get_report(self) -> Dict:
        """取得報告"""
        return {
            "name": self.name,
            "circuit_breaker": self.circuit_breaker.get_state(),
            "retry_config": {
                "max_attempts": self.retry_config.max_attempts,
                "base_delay": self.retry_config.base_delay
            },
            "total_executions": len(self.execution_log),
            "validation_rules": len(self.validator.rules)
        }


# 便捷裝飾器
def with_fault_tolerance(
    retry_config: RetryConfig = None,
    circuit_config: CircuitBreakerConfig = None,
    timeout: float = 30.0,
    fallback: Callable = None
):
    """Fault Tolerant 裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            executor = FaultTolerantExecutor(
                name=func.__name__,
                retry_config=retry_config,
                circuit_config=circuit_config,
                timeout=timeout,
                fallback=fallback
            )
            return await executor.execute(func, *args, **kwargs)
        return wrapper
    return decorator


# 測試
if __name__ == "__main__":
    async def test():
        # 測試熔斷器
        print("=== Test Circuit Breaker ===")
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        
        for i in range(5):
            print(f"Call {i+1}: can_execute={cb.can_execute()}")
            cb.record_failure()
        
        print(f"Final state: {cb.state}")
        
        # 測試執行器
        print("\n=== Test Executor ===")
        call_count = 0
        
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "Success!"
        
        executor = FaultTolerantExecutor(
            name="test_func",
            retry_config=RetryConfig(max_attempts=3, base_delay=0.1)
        )
        
        result = await executor.execute(failing_func)
        print(f"Result: success={result.success}, attempts={result.attempts}, error={result.error}")
        
        # 測試驗證器
        print("\n=== Test Validator ===")
        validator = OutputValidator()
        validator.add_keyword_rule(["forbidden", "banned"])
        validator.add_json_structure_rule(["status", "data"])
        
        passed, errors = validator.validate({"status": "ok", "data": "test"})
        print(f"Validation: passed={passed}, errors={errors}")
    
    asyncio.run(test())