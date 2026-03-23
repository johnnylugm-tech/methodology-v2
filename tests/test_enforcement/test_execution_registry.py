#!/usr/bin/env python3
"""
Execution Registry Tests
"""

import pytest
import os
import sys
import tempfile
import shutil
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

execution_registry_mod = _load_module("execution_registry", project_root / "enforcement" / "execution_registry.py")

ExecutionRegistry = execution_registry_mod.ExecutionRegistry
ExecutionRecord = execution_registry_mod.ExecutionRecord
create_minimal_registry = execution_registry_mod.create_minimal_registry


class TestExecutionRegistry:
    """Execution Registry 測試"""
    
    @pytest.fixture
    def temp_db(self):
        """建立臨時資料庫"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_registry.db")
        yield db_path
        shutil.rmtree(temp_dir)
    
    def test_init_creates_db(self, temp_db):
        """測試初始化建立資料庫"""
        registry = ExecutionRegistry(db_path=temp_db)
        assert os.path.exists(temp_db)
    
    def test_record_generates_signature(self, temp_db):
        """測試記錄生成 signature"""
        registry = ExecutionRegistry(db_path=temp_db)
        
        sig = registry.record(
            step="test-step",
            artifact={"key": "value"}
        )
        
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex length
    
    def test_prove_returns_bool(self, temp_db):
        """測試 prove 返回布林值"""
        registry = ExecutionRegistry(db_path=temp_db)
        
        # 尚未記錄
        assert registry.prove("non-existent-step") == False
        
        # 記錄後
        registry.record("test-step", {"key": "value"})
        assert registry.prove("test-step") == True
    
    def test_get_records(self, temp_db):
        """測試取得記錄"""
        registry = ExecutionRegistry(db_path=temp_db)
        
        registry.record("step-1", {"a": 1})
        registry.record("step-2", {"b": 2})
        
        records = registry.get_records()
        assert len(records) >= 2
    
    def test_verify_chain(self, temp_db):
        """測試驗證步驟鏈"""
        registry = ExecutionRegistry(db_path=temp_db)
        
        # 記錄部分步驟
        registry.record("step-1", {"a": 1})
        registry.record("step-2", {"b": 2})
        
        # 驗證
        chain = registry.verify_chain(["step-1", "step-2", "step-3"])
        
        assert chain["complete"] == False
        assert "step-3" in chain["missing"]
        assert "step-1" in chain["executed"]
        assert "step-2" in chain["executed"]
    
    def test_get_evidence_report(self, temp_db):
        """測試取得證據報告"""
        registry = ExecutionRegistry(db_path=temp_db)
        
        # 未執行
        report = registry.get_evidence_report("non-existent")
        assert report["executed"] == False
        
        # 執行後
        registry.record("test-step", {"score": 95})
        report = registry.get_evidence_report("test-step")
        
        assert report["executed"] == True
        assert report["evidence"] is not None
        assert report["evidence"]["artifact"]["score"] == 95


class TestCreateMinimalRegistry:
    """工廠函數測試"""
    
    def test_creates_registry(self):
        """測試創建最小化 registry"""
        registry = create_minimal_registry()
        assert isinstance(registry, ExecutionRegistry)
