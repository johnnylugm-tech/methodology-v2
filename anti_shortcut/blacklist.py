#!/usr/bin/env python3
"""
Blacklisted Commands - 危險操作黑名單

目標：防止 AI Agent 執行危險操作

危險操作黑名單：
- guardrails --bypass
- quality --skip
- eval --modify-after-run
- approval --self-approve
- merge --no-review
- git push --force
- rm -rf (不經確認的刪除)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable
import re

class ViolationSeverity(Enum):
    """違規嚴重程度"""
    BLOCKED = "blocked"      # 直接阻止
    WARN = "warn"            # 警告後允許
    APPROVAL_REQUIRED = "approval_required"  # 需要審批

@dataclass
class BlacklistedCommand:
    """黑名單命令"""
    pattern: str              # 正規表達式模式
    severity: ViolationSeverity
    description: str           # 說明
    alternative: str = ""    # 替代方案
    requires_approver: bool = False  # 是否需要審批者確認

class CommandBlacklist:
    """
    危險操作黑名單
    
    功能：
    - 檢查命令是否危險
    - 提供替代方案
    - 記錄違規
    """
    
    # 黑名單定義
    BLACKLISTED_COMMANDS = [
        BlacklistedCommand(
            pattern=r"guardrails?\s+--\s*bypass",
            severity=ViolationSeverity.BLOCKED,
            description="停用安全檢查是非常危險的",
            alternative="使用 'guardrails --audit' 查看問題",
        ),
        BlacklistedCommand(
            pattern=r"quality\s+--\s*skip",
            severity=ViolationSeverity.BLOCKED,
            description="跳過品質檢查會影響軟體品質",
            alternative="使用 'quality --fix' 自動修復問題",
        ),
        BlacklistedCommand(
            pattern=r"eval\s+--\s*modify",
            severity=ViolationSeverity.BLOCKED,
            description="測試後修改測試是不允許的",
            alternative="先修復問題，再重新執行測試",
        ),
        BlacklistedCommand(
            pattern=r"approval\s+--\s*self-approve",
            severity=ViolationSeverity.BLOCKED,
            description="自己批准自己的操作是違規的",
            alternative="請求其他人批准",
        ),
        BlacklistedCommand(
            pattern=r"merge\s+--\s*no-review",
            severity=ViolationSeverity.BLOCKED,
            description="不經審查的合併是不允許的",
            alternative="使用標準合併流程",
        ),
        BlacklistedCommand(
            pattern=r"git\s+push\s+--\s*force",
            severity=ViolationSeverity.APPROVAL_REQUIRED,
            description="強制推送會覆寫歷史",
            alternative="使用 'git push --force-with-lease'",
            requires_approver=True,
        ),
        BlacklistedCommand(
            pattern=r"rm\s+-rf\s+/\s*\*",
            severity=ViolationSeverity.BLOCKED,
            description="危險的刪除操作",
            alternative="使用 'trash' 而非 'rm'",
        ),
        BlacklistedCommand(
            pattern=r"constitution\s+--\s*bypass",
            severity=ViolationSeverity.BLOCKED,
            description="繞過 Constitution 是不允許的",
            alternative="使用 'constitution edit' 正式修改",
        ),
    ]
    
    def __init__(self):
        self.violations: List[dict] = []
        self._patterns = [
            (re.compile(cmd.pattern, re.IGNORECASE), cmd)
            for cmd in self.BLACKLISTED_COMMANDS
        ]
    
    def check(self, command: str) -> Optional[BlacklistedCommand]:
        """
        檢查命令是否在黑名單
        
        Args:
            command: 要檢查的命令
        
        Returns:
            BlacklistedCommand 如果在黑名單，否則 None
        """
        for pattern, bl_cmd in self._patterns:
            if pattern.search(command):
                self._record_violation(bl_cmd, command)
                return bl_cmd
        return None
    
    def _record_violation(self, cmd: BlacklistedCommand, original: str):
        """記錄違規"""
        from datetime import datetime
        self.violations.append({
            "command": original,
            "pattern": cmd.pattern,
            "severity": cmd.severity.value,
            "description": cmd.description,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_violations(self) -> List[dict]:
        """取得所有違規記錄"""
        return self.violations
    
    def get_violation_report(self) -> dict:
        """取得違規報告"""
        blocked = sum(1 for v in self.violations if v["severity"] == "blocked")
        warnings = sum(1 for v in self.violations if v["severity"] == "warn")
        approval_req = sum(1 for v in self.violations if v["severity"] == "approval_required")
        
        return {
            "total": len(self.violations),
            "blocked": blocked,
            "warnings": warnings,
            "approval_required": approval_req,
            "violations": self.violations[-10:],  # 最近10條
        }
    
    def explain(self, command: BlacklistedCommand) -> str:
        """解釋為什麼命令被阻止"""
        lines = [
            f"⚠️ 命令被阻止: {command.description}",
            f"原始命令可能包含: {command.pattern}",
        ]
        if command.alternative:
            lines.append(f"替代方案: {command.alternative}")
        if command.requires_approver:
            lines.append(f"此操作需要額外審批")
        return "\n".join(lines)
