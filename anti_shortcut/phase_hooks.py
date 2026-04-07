#!/usr/bin/env python3
"""
Phase Hooks - 階段強制鉤子

目標：每個階段結束自動觸發驗證

預設鉤子：
- development: lint → test → constitution_check
- verification: quality_gate → security_scan → coverage_check
- release: approval_check → version_check → changelog_check
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

class Phase(Enum):
    """專案階段"""
    DEVELOPMENT = "development"
    VERIFICATION = "verification"
    RELEASE = "release"
    INCIDENT = "incident"
    POSTMORTEM = "postmortem"

class HookStatus(Enum):
    """鉤子狀態"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Hook:
    """單一鉤子"""
    hook_id: str
    name: str
    phase: Phase
    command: str
    timeout: int = 60  # 秒
    required: bool = True  # 是否必須通過
    status: HookStatus = HookStatus.PENDING
    output: str = ""
    error: str = ""
    executed_at: Optional[datetime] = None

@dataclass
class PhaseRecord:
    """階段記錄"""
    phase: Phase
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: HookStatus = HookStatus.PENDING
    hooks: List[Hook] = field(default_factory=list)
    blocked_reason: Optional[str] = None

class PhaseHooks:
    """
    階段強制鉤子
    
    功能：
    - 定義每個階段的鉤子
    - 自動執行驗證
    - 阻止未通過的階段繼續
    """
    
    # 預設鉤子定義
    DEFAULT_HOOKS = {
        Phase.DEVELOPMENT: [
            {"hook_id": "dev-lint", "name": "語法檢查", "command": "python3 -m py_compile", "required": True},
            {"hook_id": "dev-test", "name": "單元測試", "command": "python3 -m unittest", "required": True},
            {"hook_id": "dev-constitution", "name": "Constitution 合規", "command": "python3 cli.py constitution check", "required": True},
        ],
        Phase.VERIFICATION: [
            {"hook_id": "verify-quality", "name": "Quality Gate", "command": "python3 cli.py quality gate", "required": True},
            {"hook_id": "verify-security", "name": "安全掃描", "command": "python3 cli.py guardrails scan", "required": True},
            {"hook_id": "verify-coverage", "name": "覆蓋率檢查", "command": "python3 -m coverage report", "required": False},
        ],
        Phase.RELEASE: [
            {"hook_id": "release-approval", "name": "審批確認", "command": "python3 cli.py approval pending", "required": True},
            {"hook_id": "release-version", "name": "版本確認", "command": "echo $VERSION", "required": True},
            {"hook_id": "release-changelog", "name": "更新日誌", "command": "cat CHANGELOG.md", "required": True},
        ],
    }
    
    def __init__(self):
        self.phase_records: Dict[Phase, PhaseRecord] = {}
        self._init_phases()
    
    def _init_phases(self):
        """初始化所有階段"""
        for phase in Phase:
            hooks = [
                Hook(
                    hook_id=h["hook_id"],
                    name=h["name"],
                    phase=phase,
                    command=h["command"],
                    required=h.get("required", True),
                    timeout=h.get("timeout", 60),
                )
                for h in self.DEFAULT_HOOKS.get(phase, [])
            ]
            self.phase_records[phase] = PhaseRecord(
                phase=phase,
                started_at=datetime.now(),
                hooks=hooks
            )
    
    def execute_phase(self, phase: Phase) -> PhaseRecord:
        """
        執行一個階段的所有鉤子
        
        Args:
            phase: 階段
        
        Returns:
            PhaseRecord: 執行結果
        """
        record = self.phase_records[phase]
        record.status = HookStatus.RUNNING
        
        all_passed = True
        for hook in record.hooks:
            result = self._execute_hook(hook)
            if not result and hook.required:
                all_passed = False
                break  # 如果必須的鉤子失敗，停止執行
        
        record.status = HookStatus.PASSED if all_passed else HookStatus.FAILED
        record.completed_at = datetime.now()
        
        return record
    
    def _execute_hook(self, hook: Hook) -> bool:
        """
        執行單一鉤子
        
        Args:
            hook: 鉤子
        
        Returns:
            bool: 是否通過
        """
        import subprocess
        
        hook.status = HookStatus.RUNNING
        hook.executed_at = datetime.now()
        
        try:
            result = subprocess.run(
                hook.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=hook.timeout
            )
            
            if result.returncode == 0:
                hook.status = HookStatus.PASSED
                hook.output = result.stdout
                return True
            else:
                hook.status = HookStatus.FAILED
                hook.output = result.stdout
                hook.error = result.stderr
                return False
        
        except subprocess.TimeoutExpired:
            hook.status = HookStatus.FAILED
            hook.error = f"Timeout after {hook.timeout}s"
            return False
        
        except Exception as e:
            hook.status = HookStatus.FAILED
            hook.error = str(e)
            return False
    
    def skip_hook(self, hook_id: str, reason: str) -> bool:
        """
        跳過鉤子（需要理由）
        
        Args:
            hook_id: 鉤子 ID
            reason: 跳過原因
        
        Returns:
            bool: 是否成功
        """
        for record in self.phase_records.values():
            for hook in record.hooks:
                if hook.hook_id == hook_id:
                    hook.status = HookStatus.SKIPPED
                    hook.error = f"Skipped: {reason}"
                    return True
        return False
    
    def get_status(self, phase: Phase = None) -> dict:
        """
        取得狀態
        
        Args:
            phase: 階段（可選）
        
        Returns:
            dict: 狀態
        """
        if phase:
            record = self.phase_records.get(phase)
            if not record:
                return {}
            
            return {
                "phase": phase.value,
                "status": record.status.value,
                "started_at": record.started_at.isoformat(),
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "hooks": [
                    {
                        "id": h.hook_id,
                        "name": h.name,
                        "status": h.status.value,
                        "required": h.required,
                    }
                    for h in record.hooks
                ],
            }
        
        # 所有階段
        return {
            phase.value: self.get_status(phase)
            for phase in Phase
        }
    
    def get_failed_hooks(self, phase: Phase) -> List[Hook]:
        """取得失敗的鉤子"""
        record = self.phase_records.get(phase)
        if not record:
            return []
        return [h for h in record.hooks if h.status == HookStatus.FAILED]
    
    def can_proceed(self, from_phase: Phase, to_phase: Phase) -> tuple[bool, Optional[str]]:
        """
        檢查是否可以從一個階段進入另一個階段
        
        Args:
            from_phase: 當前階段
            to_phase: 目標階段
        
        Returns:
            (can_proceed, reason)
        """
        from_record = self.phase_records.get(from_phase)
        
        if not from_record:
            return True, None
        
        # 檢查當前階段是否通過
        if from_record.status != HookStatus.PASSED:
            return False, f"Current phase {from_phase.value} not passed"
        
        # 檢查是否有失敗的必需鉤子
        failed_required = [
            h for h in from_record.hooks
            if h.status == HookStatus.FAILED and h.required
        ]
        
        if failed_required:
            reasons = ", ".join([h.name for h in failed_required])
            return False, f"Failed required hooks: {reasons}"
        
        return True, None
