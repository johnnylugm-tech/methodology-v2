#!/usr/bin/env python3
"""
Constitution as Code - 規範即代碼
====================================
解決方案：框架不是文件，是可執行的規則

核心概念：
- 不是「建議閱讀 Constitution」
- 是「違反 Constitution 就阻擋」
- 規則是代碼，可以執行和測試
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Callable, Any, Optional
import re

class RuleSeverity(Enum):
    """規則嚴重性"""
    CRITICAL = "critical"  # 立即阻擋
    HIGH = "high"          # 警告並阻擋
    MEDIUM = "medium"      # 警告
    LOW = "low"            # 僅記錄

@dataclass
class Rule:
    """規則定義"""
    id: str
    description: str
    check_fn: Callable[[Any], bool]
    severity: RuleSeverity
    error_message: str
    enabled: bool = True

class ConstitutionAsCode:
    """
    Constitution as Code
    
    將 Constitution 文件轉為可執行的規則：
    
    ```python
    # 不是：
    # "建議 commit message 包含 task_id"
    # 
    # 而是：
    
    rules = ConstitutionAsCode()
    
    rules.add_rule(Rule(
        id="R001",
        description="所有 commit 必須有 task_id",
        check_fn=lambda msg: bool(re.search(r'\[[A-Z]+-\d+\]', msg)),
        severity=RuleSeverity.CRITICAL,
        error_message="Commit 沒有 task_id！格式：[TASK-123] message"
    ))
    
    # 執行檢查
    violations = rules.check_commit_message("[DEV-456] Add feature")
    
    if violations:
        for v in violations:
            print(f"❌ {v.error_message}")
        raise BlockedException("Constitution violation")
    ```
    """
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """設定預設規則（從 CONSTITUTION.md 而來）"""
        
        # R001: Commit Message Format
        self.add_rule(Rule(
            id="R001",
            description="所有 commit 必須有 task_id",
            check_fn=lambda msg: bool(re.search(r'\[[A-Z]+-\d+\]', msg or "")),
            severity=RuleSeverity.CRITICAL,
            error_message="Commit message 必須包含 task_id，格式：[TASK-123]"
        ))
        
        # R002: No Bypass Keywords
        self.add_rule(Rule(
            id="R002",
            description="不允許使用 bypass/skip/--no-verify",
            check_fn=lambda cmd: not any(kw in (cmd or "").lower() for kw in ['--bypass', '--skip', '--no-verify']),
            severity=RuleSeverity.CRITICAL,
            error_message="不允许使用 bypass/skip/--no-verify 命令"
        ))
        
        # R003: Quality Gate Threshold
        self.add_rule(Rule(
            id="R003",
            description="Quality Gate 分數必須 >= 90",
            check_fn=lambda score: (score or 0) >= 90,
            severity=RuleSeverity.CRITICAL,
            error_message="Quality Gate 分數低於 90，不合格"
        ))
        
        # R004: Test Coverage
        self.add_rule(Rule(
            id="R004",
            description="測試覆蓋率必須 >= 80%",
            check_fn=lambda coverage: (coverage or 0) >= 80,
            severity=RuleSeverity.HIGH,
            error_message="測試覆蓋率低於 80%，不合格"
        ))
        
        # R005: Security Score
        self.add_rule(Rule(
            id="R005",
            description="安全分數必須 >= 95",
            check_fn=lambda score: (score or 0) >= 95,
            severity=RuleSeverity.HIGH,
            error_message="安全分數低於 95，不合格"
        ))
        
        # R006: No Self Approval
        self.add_rule(Rule(
            id="R006",
            description="不允许自己批准自己的操作",
            check_fn=lambda ctx: ctx.get("approver") != ctx.get("operator") if ctx else True,
            severity=RuleSeverity.CRITICAL,
            error_message="自己不能批准自己的操作"
        ))
        
        # R007: Required Test for Feature
        self.add_rule(Rule(
            id="R007",
            description="新功能必須有對應測試",
            check_fn=lambda ctx: ctx.get("has_test", False) if ctx else False,
            severity=RuleSeverity.HIGH,
            error_message="新功能沒有測試，不符合 TDD 要求"
        ))
    
    def add_rule(self, rule: Rule):
        """添加規則"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """移除規則"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def check_commit_message(self, message: str) -> List[Rule]:
        """檢查 commit message"""
        violations = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if "task_id" in rule.description.lower() or "commit" in rule.description.lower():
                if not rule.check_fn(message):
                    violations.append(rule)
        return violations
    
    def check_command(self, command: str) -> List[Rule]:
        """檢查命令"""
        violations = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if "bypass" in rule.description.lower() or "skip" in rule.description.lower():
                if not rule.check_fn(command):
                    violations.append(rule)
        return violations
    
    def check(self, context: Dict[str, Any]) -> List[Rule]:
        """通用檢查"""
        violations = []
        
        # 檢查 commit message
        if "commit_message" in context:
            violations.extend(self.check_commit_message(context["commit_message"]))
        
        # 檢查 command
        if "command" in context:
            violations.extend(self.check_command(context["command"]))
        
        # 檢查分數
        if "quality_score" in context:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                if "quality gate" in rule.description.lower():
                    if not rule.check_fn(context["quality_score"]):
                        violations.append(rule)
        
        if "coverage" in context:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                if "coverage" in rule.description.lower():
                    if not rule.check_fn(context["coverage"]):
                        violations.append(rule)
        
        if "security_score" in context:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                if "security" in rule.description.lower():
                    if not rule.check_fn(context["security_score"]):
                        violations.append(rule)
        
        if "approval_context" in context:
            for rule in self.rules:
                if not rule.enabled:
                    continue
                if "approval" in rule.description.lower() or "approve" in rule.description.lower():
                    if not rule.check_fn(context["approval_context"]):
                        violations.append(rule)
        
        return violations
    
    def enforce(self, context: Dict[str, Any]):
        """
        執行檢查並在違規時拋出異常
        
        使用方式：
        
        ```python
        constitution = ConstitutionAsCode()
        
        try:
            constitution.enforce({
                "commit_message": "[DEV-123] Add feature",
                "quality_score": 95,
                "coverage": 85,
            })
            print("✅ Constitution check passed")
        except ConstitutionViolation as e:
            print(f"❌ {e}")
            sys.exit(1)
        ```
        """
        violations = self.check(context)
        
        if violations:
            critical = [v for v in violations if v.severity == RuleSeverity.CRITICAL]
            high = [v for v in violations if v.severity == RuleSeverity.HIGH]
            
            error_msg = "Constitution Violations:\n"
            error_msg += "\n".join(f"  ❌ [{v.severity.value}] {v.error_message}" for v in violations)
            
            if critical:
                raise ConstitutionViolation(error_msg)
            elif high:
                raise ConstitutionWarning(error_msg)
    
    def get_rules_summary(self) -> Dict:
        """取得規則摘要"""
        return {
            "total": len(self.rules),
            "enabled": len([r for r in self.rules if r.enabled]),
            "by_severity": {
                "critical": len([r for r in self.rules if r.severity == RuleSeverity.CRITICAL]),
                "high": len([r for r in self.rules if r.severity == RuleSeverity.HIGH]),
                "medium": len([r for r in self.rules if r.severity == RuleSeverity.MEDIUM]),
                "low": len([r for r in self.rules if r.severity == RuleSeverity.LOW]),
            }
        }


class ConstitutionViolation(Exception):
    """Constitution 違規異常（Critical 等級）"""
    pass


class ConstitutionWarning(Exception):
    """Constitution 警告異常（High 等級）"""
    pass
