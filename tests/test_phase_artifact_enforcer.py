#!/usr/bin/env python3
"""
Phase Artifact Enforcer Tests
=============================
測試 phase_artifact_enforcer.py 的功能
"""

import unittest
import tempfile
import os
import json
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_gate.phase_artifact_enforcer import PhaseArtifactEnforcer, PhaseDependency


class TestPhaseArtifactEnforcer(unittest.TestCase):
    """PhaseArtifactEnforcer 測試"""
    
    def setUp(self):
        """建立測試用臨時目錄"""
        self.test_dir = tempfile.mkdtemp()
        self.enforcer = PhaseArtifactEnforcer(self.test_dir)
    
    def tearDown(self):
        """清理測試目錄"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_empty_project_fails(self):
        """空專案應該失敗"""
        result = self.enforcer.enforce_all()
        self.assertFalse(result["passed"])
    
    def test_phase1_without_phase0_fails(self):
        """Phase 1 沒有 Phase 0 產物應該失敗"""
        # 建立 Phase 1 產物但沒有 Phase 0
        Path(self.test_dir, "01-specify").mkdir()
        Path(self.test_dir, "01-specify/requirements.md").write_text("# Reqs")
        
        result = self.enforcer.enforce_all()
        self.assertFalse(result["passed"])
    
    def test_valid_phase_chain(self):
        """完整的 Phase 鏈應該通過"""
        # 建立 Phase 0
        Path(self.test_dir, "00-constitution").mkdir()
        Path(self.test_dir, "00-constitution/CONSTITUTION.md").write_text("# Constitution")
        
        # 建立 Phase 1
        Path(self.test_dir, "01-specify").mkdir()
        Path(self.test_dir, "01-specify/requirements.md").write_text("# Reqs")
        
        result = self.enforcer.enforce_all()
        # 應該至少 Phase 1 通過
        self.assertTrue(result["results"]["phase_1"]["passed"])
    
    def test_missing_intermediate_phase(self):
        """缺少中間 Phase 應該失敗"""
        # Phase 0 -> Phase 2（跳過 Phase 1）
        Path(self.test_dir, "00-constitution").mkdir()
        Path(self.test_dir, "00-constitution/CONSTITUTION.md").write_text("# Constitution")
        
        Path(self.test_dir, "02-plan").mkdir()
        Path(self.test_dir, "02-plan/architecture.md").write_text("# Arch")
        
        result = self.enforcer.enforce_all()
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()