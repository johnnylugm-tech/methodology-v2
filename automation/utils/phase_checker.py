#!/usr/bin/env python3
"""
Phase 1 完成檢查模組
功能：Phase 2 執行前檢查 Phase 1 是否已完成
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class PhaseCompletionChecker:
    """Phase 完成檢查器"""
    
    def __init__(self, project_path: str = "/workspace"):
        self.project_path = Path(project_path)
        self.methodology_path = self.project_path / "methodology-v2"
        
    def check_phase1_completion(self) -> Dict[str, Any]:
        """
        檢查 Phase 1 是否已完成
        
        Returns:
            {"completed": True/False, "checks": [...], "details": {...}}
        """
        result = {
            "phase": 1,
            "checked_at": datetime.now().isoformat(),
            "completed": False,
            "checks": [],
            "details": {}
        }
        
        checks = [
            {
                "name": "STAGE_PASS_P1.md",
                "path": self.methodology_path / "STAGE_PASS_P1.md",
                "required": True
            },
            {
                "name": "01-requirements 目錄",
                "path": self.methodology_path / "01-requirements",
                "required": True
            },
            {
                "name": "SRS.md",
                "path": self.methodology_path / "01-requirements" / "SRS.md",
                "required": True
            },
            {
                "name": "DEVELOPMENT_LOG.md",
                "path": self.methodology_path / "DEVELOPMENT_LOG.md",
                "required": True
            }
        ]
        
        all_passed = True
        
        for check in checks:
            path = check["path"]
            exists = path.exists() if isinstance(path, Path) else os.path.exists(str(path))
            
            check_result = {
                "name": check["name"],
                "exists": exists,
                "required": check["required"],
                "passed": exists if not check["required"] else exists
            }
            
            if check["required"] and not exists:
                all_passed = False
                
            result["checks"].append(check_result)
            result["details"][check["name"]] = exists
        
        result["completed"] = all_passed
        return result
    
    def check_phase_completion(self, phase_num: int) -> Dict[str, Any]:
        """
        檢查任意 Phase 是否已完成
        
        Args:
            phase_num: Phase 編號 (1-8)
            
        Returns:
            檢查結果
        """
        if phase_num < 1 or phase_num > 8:
            return {"error": "Phase 編號必須在 1-8 之間"}
        
        result = {
            "phase": phase_num,
            "checked_at": datetime.now().isoformat(),
            "completed": False,
            "checks": [],
            "details": {}
        }
        
        # Phase 目錄對應
        phase_dirs = {
            1: "01-requirements",
            2: "02-architecture",
            3: "03-implementation",
            4: "04-testing",
            5: "05-verify",
            6: "06-quality",
            7: "07-risk",
            8: "08-config"
        }
        
        # 檢查 STAGE_PASS
        stage_pass = self.methodology_path / f"STAGE_PASS_P{phase_num}.md"
        result["checks"].append({
            "name": f"STAGE_PASS_P{phase_num}.md",
            "exists": stage_pass.exists(),
            "required": True
        })
        
        # 檢查 Phase 目錄
        phase_dir = self.methodology_path / phase_dirs[phase_num]
        result["checks"].append({
            "name": phase_dirs[phase_num],
            "exists": phase_dir.exists(),
            "required": True
        })
        
        result["completed"] = all(c["passed"] for c in result["checks"])
        result["details"] = {
            "stage_pass": stage_pass.exists(),
            "phase_dir": phase_dir.exists()
        }
        
        return result
    
    def get_phase_sequence_status(self) -> Dict[str, Any]:
        """
        取得所有 Phase 的完成狀態
        
        Returns:
            {1: {"completed": True}, 2: {"completed": False}, ...}
        """
        status = {}
        
        for phase in range(1, 9):
            result = self.check_phase_completion(phase)
            status[phase] = {
                "completed": result.get("completed", False),
                "checked_at": result.get("checked_at")
            }
        
        return status
    
    def can_proceed_to_phase(self, phase_num: int) -> Dict[str, Any]:
        """
        判斷是否可以進入指定 Phase
        
        Args:
            phase_num: 目標 Phase 編號
            
        Returns:
            {"allowed": True/False, "reason": "...", "previous_phase": {...}}
        """
        if phase_num == 1:
            return {"allowed": True, "reason": "Phase 1 是起始 Phase"}
        
        # 檢查上一個 Phase 是否完成
        previous_phase = phase_num - 1
        prev_result = self.check_phase_completion(previous_phase)
        
        if not prev_result["completed"]:
            return {
                "allowed": False,
                "reason": f"Phase {previous_phase} 尚未完成",
                "previous_phase": prev_result
            }
        
        return {
            "allowed": True,
            "reason": f"Phase {previous_phase} 已完成，可以進入 Phase {phase_num}",
            "previous_phase": prev_result
        }


# 全域實例
checker = PhaseCompletionChecker()


# 便捷函數
def check_phase1() -> Dict[str, Any]:
    """快速檢查 Phase 1"""
    return checker.check_phase1_completion()


def can_proceed(phase_num: int) -> Dict[str, Any]:
    """快速判斷是否可以進入指定 Phase"""
    return checker.can_proceed_to_phase(phase_num)


# 測試
if __name__ == "__main__":
    print("=== PhaseCompletionChecker 測試 ===")
    
    # 測試 Phase 1 檢查
    result = check_phase1()
    print(f"\nPhase 1 檢查結果:")
    print(f"   完成: {result['completed']}")
    print(f"   檢查項目: {len(result['checks'])}")
    
    # 測試權限判斷
    can_go = can_proceed(2)
    print(f"\n是否可以進入 Phase 2: {can_go['allowed']}")
    print(f"   原因: {can_go['reason']}")
    
    print("\n✅ PhaseCompletionChecker 測試完成")