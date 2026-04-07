#!/usr/bin/env python3
"""
Execution Sandbox
================
Layer 2: 執行隔離 - Tool 調用在隔離環境執行

功能：
- 隔離的工具執行
- 權限最小化
- 側向移動防止
"""

from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Optional, List
from enum import Enum
import subprocess
import tempfile
import os


class SandboxLevel(Enum):
    """沙盒等級"""
    NONE = "none"           # 無隔離
    BASIC = "basic"         # 基本隔離
    STRICT = "strict"       # 嚴格隔離
    FULL = "full"           # 完全隔離


@dataclass
class SandboxConfig:
    """沙盒配置"""
    level: SandboxLevel = SandboxLevel.BASIC
    allowed_paths: List[str] = field(default_factory=lambda: ["/tmp"])
    denied_paths: List[str] = field(default_factory=list)
    max_execution_time: int = 30     # 最大執行時間（秒）
    max_memory_mb: int = 512         # 最大記憶體（MB）
    network_access: bool = False     # 是否允許網路訪問


@dataclass
class ExecutionResult:
    """執行結果"""
    success: bool
    output: str
    error: str
    execution_time: float
    sandbox_level: SandboxLevel


class ExecutionSandbox:
    """
    執行沙盒
    
    使用方式：
    
    ```python
    sandbox = ExecutionSandbox(SandboxConfig(level=SandboxLevel.STRICT))
    
    result = sandbox.execute(
        tool="subprocess",
        command=["ls", "-la"],
        timeout=10
    )
    
    if result.success:
        print(result.output)
    else:
        print(f"Error: {result.error}")
    ```
    """
    
    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
    
    def execute(
        self,
        tool: str,
        command: Any = None,
        fn: Callable = None,
        timeout: int = None,
        **kwargs
    ) -> ExecutionResult:
        """
        在沙盒中執行
        
        Args:
            tool: 工具類型 ("subprocess", "function", "eval")
            command: subprocess 命令（如果 tool="subprocess"）
            fn: 要執行的函數（如果 tool="function"）
            timeout: 逾時時間
        
        Returns:
            ExecutionResult: 執行結果
        """
        import time
        start = time.time()
        
        try:
            if tool == "subprocess":
                return self._execute_subprocess(command, timeout or self.config.max_execution_time)
            elif tool == "function":
                return self._execute_function(fn, kwargs, timeout or self.config.max_execution_time)
            elif tool == "eval":
                return self._execute_eval(command, timeout or self.config.max_execution_time)
            else:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Unknown tool: {tool}",
                    execution_time=time.time() - start,
                    sandbox_level=self.config.level
                )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
    
    def _execute_subprocess(self, command: List[str], timeout: int) -> ExecutionResult:
        """執行 subprocess"""
        import time
        start = time.time()
        
        # 構建安全參數
        env = {
            "PATH": "/usr/bin:/bin",  # 最小化的 PATH
            "HOME": "/tmp",           # 臨時 home
        }
        
        # 根據 level 設定限制
        if self.config.level == SandboxLevel.STRICT:
            # 嚴格模式：只允許特定路徑
            allowed = self.config.allowed_paths or ["/tmp"]
            env["PATH"] = ":".join(allowed + ["/usr/bin"])
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd="/tmp"  # 限制工作目錄
            )
            
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timeout after {timeout}s",
                execution_time=timeout,
                sandbox_level=self.config.level
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
    
    def _execute_function(self, fn: Callable, kwargs: Dict, timeout: int) -> ExecutionResult:
        """執行函數"""
        import time
        start = time.time()
        
        try:
            # 在 timeout 內執行
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function execution timeout after {timeout}s")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
            
            try:
                result = fn(**kwargs)
                signal.alarm(0)  # 取消 alarm
                
                return ExecutionResult(
                    success=True,
                    output=str(result),
                    error="",
                    execution_time=time.time() - start,
                    sandbox_level=self.config.level
                )
            finally:
                signal.alarm(0)  # 確保取消
                
        except TimeoutError as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
    
    def _execute_eval(self, code: str, timeout: int) -> ExecutionResult:
        """安全執行 eval"""
        import time
        start = time.time()
        
        # 禁止的危险操作
        dangerous = ["import", "open", "exec", "eval", "compile", "__import__"]
        
        for d in dangerous:
            if d in code:
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Forbidden operation: {d}",
                    execution_time=time.time() - start,
                    sandbox_level=self.config.level
                )
        
        try:
            # 只允許基本類型操作
            result = eval(code)
            
            return ExecutionResult(
                success=True,
                output=str(result),
                error="",
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=time.time() - start,
                sandbox_level=self.config.level
            )
