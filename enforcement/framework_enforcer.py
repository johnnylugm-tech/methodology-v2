#!/usr/bin/env python3
"""
Framework Enforcement Engine
===========================
讀取 SKILL.md 的 enforcement 定義並執行

使用方法：
    from enforcement.framework_enforcer import FrameworkEnforcer
    
    enforcer = FrameworkEnforcer("/path/to/project")
    result = enforcer.run()
    
    if not result.passed:
        for msg, fix in result.violations:
            print(f"🔴 {msg}")
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import existing enforcement components
from enforcement import PolicyEngine, ConstitutionAsCode, EnforcementLevel
from enforcement.execution_registry import ExecutionRegistry


class EnforcementResult:
    """Enforcement 結果容器"""
    
    def __init__(self):
        self.violations: List[Tuple[str, Optional[str]]] = []  # (message, fix_command)
        self.warnings: List[Tuple[str, Optional[str]]] = []
        self.passed = False
        self.block_checks: Dict[str, bool] = {}
        self.warn_checks: Dict[str, bool] = {}
    
    def add_violation(self, message: str, fix: str = None):
        """新增 BLOCK 等級違規"""
        self.violations.append((message, fix))
    
    def add_warning(self, message: str, fix: str = None):
        """新增 WARN 等級警告"""
        self.warnings.append((message, fix))
    
    def add_block_check(self, name: str, passed: bool):
        """記錄 BLOCK 檢查結果"""
        self.block_checks[name] = passed
    
    def add_warn_check(self, name: str, passed: bool):
        """記錄 WARN 檢查結果"""
        self.warn_checks[name] = passed
    
    def summary(self) -> str:
        """生成摘要文字"""
        lines = []
        lines.append(f"Passed: {self.passed}")
        lines.append(f"BLOCK Violations: {len(self.violations)}")
        lines.append(f"WARN Warnings: {len(self.warnings)}")
        return "\n".join(lines)


class FrameworkEnforcer:
    """
    Framework Enforcement 引擎
    
    根據 SKILL.md 定義的 enforcement 規則執行檢查。
    
    BLOCK 等級（必須通過，否則阻擋）：
    - SPEC_TRACKING: 規格追蹤完整性 >= 90%
    - CONSTITUTION_SCORE: Constitution Score >= 60
    
    WARN 等級（警告，不阻擋）：
    - DECISION_FRAMEWORK: Decision Framework 已建立
    - ENHANCED_CHECKLIST: 增強檢查清單已建立
    """
    
    # BLOCK 等級檢查門檻
    BLOCK_CHECKS = [
        {"name": "SPEC_TRACKING", "threshold": 90},
        {"name": "CONSTITUTION_SCORE", "threshold": 60},
    ]
    
    # WARN 等級檢查
    WARN_CHECKS = [
        {"name": "DECISION_FRAMEWORK"},
        {"name": "ENHANCED_CHECKLIST"},
    ]
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._spec_checker = None
    
    @property
    def spec_checker(self):
        """延遲載入 SpecTrackingChecker"""
        if self._spec_checker is None:
            from quality_gate.spec_tracking_checker import SpecTrackingChecker
            self._spec_checker = SpecTrackingChecker(str(self.project_root))
        return self._spec_checker
    
    def check_spec_tracking(self) -> Dict:
        """
        檢查 SPEC_TRACKING
        
        Returns:
            Dict with keys: exists, completeness, complete, missing
        """
        return self.spec_checker.run_enforcement()
    
    def check_constitution(self) -> Dict:
        """
        檢查 Constitution Score
        
        Returns:
            Dict with keys: score, passed
        """
        try:
            from quality_gate.constitution.runner import run_constitution_check
            
            docs_path = self.project_root / "docs"
            if not docs_path.exists():
                return {"score": 0, "passed": False, "error": "docs/ not found"}
            
            result = run_constitution_check("all", str(docs_path))
            return {
                "score": result.score,
                "passed": result.passed,
                "violations": len(result.violations) if hasattr(result, 'violations') else 0
            }
        except Exception as e:
            return {"score": 0, "passed": False, "error": str(e)}
    
    def check_decision_framework(self) -> Dict:
        """檢查 Decision Framework 是否存在"""
        framework_file = self.project_root / "DECISION_FRAMEWORK.md"
        return {
            "exists": framework_file.exists(),
            "path": str(framework_file)
        }
    
    def check_enhanced_checklist(self) -> Dict:
        """檢查 Enhanced Checklist 是否存在"""
        checklist_file = self.project_root / "CHECKLIST.md"
        return {
            "exists": checklist_file.exists(),
            "path": str(checklist_file)
        }
    
    def run(self, level: str = "ALL") -> EnforcementResult:
        """
        執行 Enforcement
        
        Args:
            level: "BLOCK" | "WARN" | "ALL"
        
        Returns:
            EnforcementResult
        """
        result = EnforcementResult()
        
        # BLOCK 檢查
        if level in ["BLOCK", "ALL"]:
            # 1. SPEC_TRACKING
            spec = self.check_spec_tracking()
            spec_passed = (
                spec.get('exists', False) and 
                spec.get('completeness', 0) >= 90
            )
            result.add_block_check("SPEC_TRACKING", spec_passed)
            
            if not spec.get('exists', False):
                result.add_violation(
                    "SPEC_TRACKING.md 不存在",
                    "methodology spec-track init"
                )
            elif spec.get('completeness', 0) < 90:
                result.add_violation(
                    f"規格完整性 {spec['completeness']}% < 90%",
                    None
                )
            
            # 2. Constitution Score
            const = self.check_constitution()
            const_passed = const.get('score', 0) >= 60
            result.add_block_check("CONSTITUTION_SCORE", const_passed)
            
            if not const_passed:
                result.add_violation(
                    f"Constitution Score {const.get('score', 0)}% < 60%",
                    "methodology constitution check"
                )
        
        # WARN 檢查
        if level in ["WARN", "ALL"]:
            # Decision Framework
            df = self.check_decision_framework()
            result.add_warn_check("DECISION_FRAMEWORK", df['exists'])
            if not df['exists']:
                result.add_warning(
                    "Decision Framework 未建立",
                    "建議建立 DECISION_FRAMEWORK.md"
                )
            
            # Enhanced Checklist
            cl = self.check_enhanced_checklist()
            result.add_warn_check("ENHANCED_CHECKLIST", cl['exists'])
            if not cl['exists']:
                result.add_warning(
                    "Enhanced Checklist 未建立",
                    "建議建立 CHECKLIST.md"
                )
        
        result.passed = len(result.violations) == 0
        return result
    
    def run_with_exit(self, level: str = "ALL") -> int:
        """
        執行 Enforcement並根據結果sys.exit
        
        Returns:
            exit code (0 = passed, 1 = failed)
        """
        result = self.run(level)
        
        print("=" * 50)
        print(f"Framework Enforcement - {level}")
        print("=" * 50)
        
        print("\n🔴 BLOCK Violations:")
        if result.violations:
            for msg, fix in result.violations:
                print(f"   🔴 {msg}")
                if fix:
                    print(f"      請執行: {fix}")
        else:
            print("   ✅ 無 BLOCK 違規")
        
        print("\n🟡 Warnings:")
        if result.warnings:
            for msg, fix in result.warnings:
                print(f"   🟡 {msg}")
                if fix:
                    print(f"      {fix}")
        else:
            print("   ✅ 無警告")
        
        if result.passed:
            print("\n✅ Framework Enforcement 通過")
        else:
            print("\n❌ Framework Enforcement 失敗")
        
        return 0 if result.passed else 1


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Framework Enforcement")
    parser.add_argument("--level", "-l", choices=["BLOCK", "WARN", "ALL"], 
                       default="ALL", help="Enforcement level")
    parser.add_argument("--project", "-p", default=".", help="Project root path")
    parser.add_argument("--exit", "-x", action="store_true", 
                       help="Exit with code based on result")
    
    args = parser.parse_args()
    
    enforcer = FrameworkEnforcer(args.project)
    
    if args.exit:
        sys.exit(enforcer.run_with_exit(args.level))
    else:
        result = enforcer.run(args.level)
        print(result.summary())
        sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    sys.exit(main())
