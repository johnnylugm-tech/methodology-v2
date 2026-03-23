#!/usr/bin/env python3
"""
Policy Engine Tests
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from enforcement.policy_engine import (
    PolicyEngine,
    Policy,
    PolicyResult,
    EnforcementLevel,
    PolicyViolationException,
    create_hard_block_engine
)


class TestPolicyEngine:
    """Policy Engine 測試"""
    
    def test_default_policies_exist(self):
        """測試預設政策存在"""
        engine = PolicyEngine()
        assert len(engine.policies) > 0
    
    def test_add_policy(self):
        """測試添加政策"""
        engine = PolicyEngine()
        initial_count = len(engine.policies)
        
        engine.add_policy(Policy(
            id="test-policy",
            description="Test policy",
            check_fn=lambda: True,
            enforcement=EnforcementLevel.BLOCK,
            severity="medium"
        ))
        
        assert len(engine.policies) == initial_count + 1
    
    def test_enable_disable_policy(self):
        """測試啟用/停用政策"""
        engine = PolicyEngine()
        
        # 停用
        engine.disable("commit-has-task-id")
        policy = next(p for p in engine.policies if p.id == "commit-has-task-id")
        assert policy.enabled == False
        
        # 啟用
        engine.enable("commit-has-task-id")
        assert policy.enabled == True
    
    def test_check_returns_result(self):
        """測試 check 返回結果"""
        engine = PolicyEngine()
        result = engine.check("commit-has-task-id")
        
        assert isinstance(result, PolicyResult)
        assert result.policy_id == "commit-has-task-id"
    
    def test_enforce_all_passes_with_no_blocking(self):
        """測試所有政策都通過"""
        engine = PolicyEngine()
        engine.policies = []  # 清空
        
        # 添加一個永遠通過的政策
        engine.add_policy(Policy(
            id="always-pass",
            description="Always pass",
            check_fn=lambda: True,
            enforcement=EnforcementLevel.BLOCK
        ))
        
        results = engine.enforce_all()
        assert len(results) == 1
        assert results[0].passed == True
    
    def test_enforce_all_blocks_on_failure(self):
        """測試失敗時 block"""
        engine = PolicyEngine()
        engine.policies = []  # 清空
        
        # 添加一個永遠失敗的政策
        engine.add_policy(Policy(
            id="always-fail",
            description="Always fail",
            check_fn=lambda: False,
            enforcement=EnforcementLevel.BLOCK
        ))
        
        with pytest.raises(PolicyViolationException):
            engine.enforce_all()
    
    def test_get_summary(self):
        """測試取得摘要"""
        engine = PolicyEngine()
        engine.policies = []
        
        engine.add_policy(Policy(
            id="pass1",
            description="Pass 1",
            check_fn=lambda: True,
            enforcement=EnforcementLevel.LOG
        ))
        
        engine.add_policy(Policy(
            id="pass2",
            description="Pass 2",
            check_fn=lambda: True,
            enforcement=EnforcementLevel.LOG
        ))
        
        results = engine.enforce_all()
        summary = engine.get_summary()
        
        assert summary['total'] == 2
        assert summary['passed'] == 2
        assert summary['all_passed'] == True


class TestPolicyViolationException:
    """PolicyViolationException 測試"""
    
    def test_exception_message(self):
        """測試異常訊息"""
        exc = PolicyViolationException("Test violation")
        assert str(exc) == "Test violation"


class TestCreateHardBlockEngine:
    """工廠函數測試"""
    
    def test_creates_engine_with_block(self):
        """測試創建硬 block engine"""
        engine = create_hard_block_engine()
        
        assert isinstance(engine, PolicyEngine)
        assert len(engine.policies) > 0
        
        # 所有政策應該是 BLOCK
        for policy in engine.policies:
            assert policy.enforcement == EnforcementLevel.BLOCK
