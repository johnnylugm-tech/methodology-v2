"""
Deep Security Defense Architecture
=================================
解決 LPCI 攻擊、Confused Deputy 問題

Layer 1: Input Validation（輸入驗證）
Layer 2: Execution Sandbox（執行隔離）
Layer 3: Output Filter（輸出過濾）
Layer 4: Human-in-the-Loop（人類審批）
"""

from .input_validator import InputValidator, ValidationResult, ThreatType
from .execution_sandbox import ExecutionSandbox, SandboxConfig, SandboxLevel, ExecutionResult as SandboxExecutionResult
from .output_filter import OutputFilter, SensitivePattern
from .human_in_loop import HumanInTheLoop, ApprovalRequest, ApprovalLevel

__all__ = [
    # Input Validator
    'InputValidator',
    'ValidationResult',
    'ThreatType',
    # Execution Sandbox
    'ExecutionSandbox',
    'SandboxConfig',
    'SandboxLevel',
    'SandboxExecutionResult',
    # Output Filter
    'OutputFilter',
    'SensitivePattern',
    # Human-in-the-Loop
    'HumanInTheLoop',
    'ApprovalRequest',
    'ApprovalLevel',
]
