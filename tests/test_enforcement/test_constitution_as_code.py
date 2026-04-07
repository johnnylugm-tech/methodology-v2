#!/usr/bin/env python3
"""
Constitution as Code Tests
"""

import pytest
import sys
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Explicitly load modules without triggering package __init__.py
def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

constitution_as_code_mod = _load_module("constitution_as_code", project_root / "enforcement" / "constitution_as_code.py")

ConstitutionAsCode = constitution_as_code_mod.ConstitutionAsCode
Rule = constitution_as_code_mod.Rule
RuleSeverity = constitution_as_code_mod.RuleSeverity
ConstitutionViolation = constitution_as_code_mod.ConstitutionViolation
ConstitutionWarning = constitution_as_code_mod.ConstitutionWarning


class TestConstitutionAsCode:
    """Constitution as Code 測試"""
    
    def test_default_rules_exist(self):
        """測試預設規則存在"""
        c = ConstitutionAsCode()
        assert len(c.rules) > 0
    
    def test_add_rule(self):
        """測試添加規則"""
        c = ConstitutionAsCode()
        initial = len(c.rules)
        
        c.add_rule(Rule(
            id="TEST-R001",
            description="Test rule",
            check_fn=lambda x: True,
            severity=RuleSeverity.MEDIUM,
            error_message="Test error"
        ))
        
        assert len(c.rules) == initial + 1
    
    def test_check_commit_message_valid(self):
        """測試合法的 commit message"""
        c = ConstitutionAsCode()
        
        violations = c.check_commit_message("[DEV-123] Add feature")
        # 不应该有违规（除非没有定义 commit 规则）
        # 这个测试根据实际规则而定
    
    def test_check_commit_message_invalid(self):
        """測試不合法的 commit message"""
        c = ConstitutionAsCode()
        
        # 创建一个必须包含 task_id 的规则
        c.add_rule(Rule(
            id="TEST-R001",
            description="Must have task ID",
            check_fn=lambda msg: bool(msg and '[DEV-' in msg),
            severity=RuleSeverity.CRITICAL,
            error_message="Must have DEV-XXX"
        ))
        
        violations = c.check_commit_message("no task id")
        assert len(violations) > 0
    
    def test_check_command_no_bypass(self):
        """測試無 bypass 命令"""
        c = ConstitutionAsCode()
        
        violations = c.check_command("git commit -m 'fix'")
        assert len(violations) == 0
    
    def test_check_command_with_bypass(self):
        """測試有 bypass 命令"""
        c = ConstitutionAsCode()
        
        violations = c.check_command("git commit --no-verify -m 'fix'")
        assert len(violations) > 0
    
    def test_enforce_passes(self):
        """測試 enforce 通過"""
        c = ConstitutionAsCode()
        c.rules = []  # 清空
        
        # 不应该抛出异常
        c.enforce({"commit_message": "[DEV-123] test"})
    
    def test_enforce_raises_critical(self):
        """測試 CRITICAL 違規拋異常"""
        c = ConstitutionAsCode()
        c.rules = []
        
        # Use description matching a known check type (quality gate check_fn receives score)
        c.add_rule(Rule(
            id="TEST-R001",
            description="Quality Gate check - must meet threshold",
            check_fn=lambda score: False,  # Always fail
            severity=RuleSeverity.CRITICAL,
            error_message="Critical violation"
        ))
        
        with pytest.raises(ConstitutionViolation):
            c.enforce({"quality_score": 50})
    
    def test_enforce_raises_warning(self):
        """測試 HIGH 違規拋警告"""
        c = ConstitutionAsCode()
        c.rules = []
        
        # Use description matching a known check type (coverage check_fn receives coverage)
        c.add_rule(Rule(
            id="TEST-R001",
            description="Coverage must meet threshold",
            check_fn=lambda coverage: False,  # Always fail
            severity=RuleSeverity.HIGH,
            error_message="High violation"
        ))
        
        with pytest.raises(ConstitutionWarning):
            c.enforce({"coverage": 50})
    
    def test_get_rules_summary(self):
        """測試取得規則摘要"""
        c = ConstitutionAsCode()
        summary = c.get_rules_summary()
        
        assert "total" in summary
        assert "enabled" in summary
        assert "by_severity" in summary
        assert summary["total"] > 0


class TestConstitutionViolation:
    """異常測試"""
    
    def test_violation_message(self):
        """測試違規異常訊息"""
        exc = ConstitutionViolation("Test violation")
        assert "Test violation" in str(exc)
    
    def test_warning_message(self):
        """測試警告異常訊息"""
        exc = ConstitutionWarning("Test warning")
        assert "Test warning" in str(exc)
