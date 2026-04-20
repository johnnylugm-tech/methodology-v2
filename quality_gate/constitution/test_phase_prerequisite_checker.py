#!/usr/bin/env python3
"""
Test Phase Prerequisite Checker
================================
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quality_gate.constitution.phase_prerequisite_checker import (
    check_phase_prerequisites,
    format_prerequisite_error,
    PHASE_PREREQUISITES
)


class TestPhasePrerequisiteChecker:
    """Phase 前置條件檢查器測試"""
    
    def setup_method(self):
        """每個測試前創建臨時目錄"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """每個測試後清理臨時目錄"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_phase1_no_prerequisites(self):
        """Phase 1 沒有前置條件"""
        passed, missing, ready = check_phase_prerequisites(1, self.project_path)
        assert passed is True
        assert missing == []
        assert ready == []
    
    def test_phase2_requires_srs(self):
        """Phase 2 需要 SRS.md"""
        passed, missing, ready = check_phase_prerequisites(2, self.project_path)
        assert passed is False
        assert missing == ["SRS.md"]
        
        # 創建 SRS.md
        (self.project_path / "SRS.md").touch()
        passed, missing, ready = check_phase_prerequisites(2, self.project_path)
        assert passed is True
        assert "SRS.md" in ready
    
    def test_phase3_requires_multiple(self):
        """Phase 3 需要 SRS.md, SAD.md, fr_mapping.json"""
        passed, missing, ready = check_phase_prerequisites(3, self.project_path)
        assert passed is False
        assert set(missing) == {"SRS.md", "SAD.md", "fr_mapping.json"}
        
        # 創建部分檔案
        (self.project_path / "SRS.md").touch()
        (self.project_path / "SAD.md").touch()
        passed, missing, ready = check_phase_prerequisites(3, self.project_path)
        assert passed is False
        assert "fr_mapping.json" in missing
        assert set(ready) == {"SRS.md", "SAD.md"}
    
    def test_phase4_requires_sab(self):
        """Phase 4 需要 SAB.json"""
        passed, missing, ready = check_phase_prerequisites(4, self.project_path)
        assert "SAB.json" in missing
        
        (self.project_path / "SAB.json").touch()
        passed, missing, ready = check_phase_prerequisites(4, self.project_path)
        assert "SAB.json" in ready
    
    def test_phase5_requires_test_plan(self):
        """Phase 5 需要 TEST_PLAN.md"""
        passed, missing, ready = check_phase_prerequisites(5, self.project_path)
        assert "TEST_PLAN.md" in missing
    
    def test_phase7_requires_quality_report(self):
        """Phase 7 需要 QUALITY_REPORT.md"""
        passed, missing, ready = check_phase_prerequisites(7, self.project_path)
        assert "QUALITY_REPORT.md" in missing
        
        (self.project_path / "QUALITY_REPORT.md").touch()
        passed, missing, ready = check_phase_prerequisites(7, self.project_path)
        assert passed is True
    
    def test_phase8_requires_config_and_lock(self):
        """Phase 8 需要 CONFIG_RECORDS.md 和 requirements.lock"""
        passed, missing, ready = check_phase_prerequisites(8, self.project_path)
        assert set(missing) == {"CONFIG_RECORDS.md", "requirements.lock"}
    
    def test_unknown_phase(self):
        """未知 Phase 返回空結果"""
        passed, missing, ready = check_phase_prerequisites(99, self.project_path)
        assert passed is True
        assert missing == []
        assert ready == []
    
    def test_format_prerequisite_error(self):
        """測試錯誤訊息格式化"""
        msg = format_prerequisite_error(
            phase=3,
            missing=["fr_mapping.json"],
            ready=["SRS.md", "SAD.md"]
        )
        assert "Phase 3" in msg
        assert "fr_mapping.json" in msg
        assert "SRS.md" in msg
    
    def test_directory_prerequisite(self):
        """測試目錄類型的前置條件"""
        # 建立一個測試案例：修改 PHASE_PREREQUISITES 包含目錄
        pass  # 現有實作不包含目錄前置條件，可擴展


class TestPhasePrerequisitesCompleteness:
    """確保所有 Phase 的前置條件映射完整"""
    
    def test_all_phases_defined(self):
        """所有 Phase 1-8 都應該有定義"""
        for phase in range(1, 9):
            assert phase in PHASE_PREREQUISITES, f"Phase {phase} should be defined"
    
    def test_prerequisites_make_sense(self):
        """前置條件應該是遞增的（後期 Phase 不能少於早期）"""
        # Phase 2+ 至少需要 SRS.md
        for phase in [2, 3, 4, 5, 6]:
            assert "SRS.md" in PHASE_PREREQUISITES[phase]
        
        # Phase 3+ 需要 SAD.md
        for phase in [3, 4, 5, 6]:
            assert "SAD.md" in PHASE_PREREQUISITES[phase]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
