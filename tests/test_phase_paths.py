#!/usr/bin/env python3
"""
Path Contract Tests
===================
確保所有 Phase artifact 路徑定義一致且正確

Test Philosophy: Test-Driven Development
- 先定義路徑合約
- 驗證所有工具都使用這些合約
- 禁止硬編碼路徑
"""

import os
import re
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS


class PathContractTest:
    """路徑合約測試"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.tools_dir = PROJECT_ROOT / "quality_gate"
        self.constitution_dir = self.tools_dir / "constitution"
    
    def run_all(self) -> bool:
        """執行所有測試"""
        print("=" * 60)
        print("PATH CONTRACT TESTS")
        print("=" * 60)
        
        tests = [
            ("test_phase_paths_structure", self.test_phase_paths_structure),
            ("test_no_hardcoded_paths_in_tools", self.test_no_hardcoded_paths_in_tools),
            ("test_all_constitution_checkers_use_phase_paths", self.test_all_constitution_checkers_use_phase_paths),
            ("test_path_consistency_with_plans", self.test_path_consistency_with_plans),
            ("test_no_glob_on_wrong_paths", self.test_no_glob_on_wrong_paths),
        ]
        
        all_passed = True
        for name, test_func in tests:
            print(f"\n[TEST] {name}")
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"  ❌ EXCEPTION: {e}")
                self.errors.append(f"{name}: {e}")
                all_passed = False
        
        return all_passed
    
    def test_phase_paths_structure(self) -> bool:
        """測試 PHASE_ARTIFACT_PATHS 結構正確"""
        print("  Checking PHASE_ARTIFACT_PATHS structure...")
        
        required_phases = [5, 6, 7, 8]
        for phase in required_phases:
            if phase not in PHASE_ARTIFACT_PATHS:
                self.errors.append(f"Phase {phase} not in PHASE_ARTIFACT_PATHS")
                print(f"  ❌ Phase {phase} missing")
                return False
        
        # Check Phase 5 is complete
        phase5_artifacts = ["BASELINE.md", "TEST_RESULTS.md", "VERIFICATION_REPORT.md"]
        for artifact in phase5_artifacts:
            if artifact not in PHASE_ARTIFACT_PATHS.get(5, {}):
                self.errors.append(f"Phase 5 artifact '{artifact}' missing")
                print(f"  ❌ Phase 5 '{artifact}' missing")
                return False
        
        print(f"  ✅ PHASE_ARTIFACT_PATHS structure is valid")
        return True
    
    def test_no_hardcoded_paths_in_tools(self) -> bool:
        """測試工具中沒有硬編碼路徑"""
        print("  Checking for hardcoded paths in tools...")
        
        # Patterns that indicate hardcoded paths (should use PHASE_ARTIFACT_PATHS instead)
        hardcoded_patterns = [
            r'"05-verify/', r'"05-baseline/', r'"06-quality/',
            r'"07-risk/', r'"08-config/', r'"04-testing/',
        ]
        
        files_to_check = list(self.tools_dir.glob("*.py"))
        files_to_check.extend(self.constitution_dir.glob("*_checker.py"))
        
        found_hardcoded = []
        for filepath in files_to_check:
            content = filepath.read_text()
            
            # Skip phase_paths.py itself
            if filepath.name == "phase_paths.py":
                continue
            
            for pattern in hardcoded_patterns:
                matches = re.findall(f'{pattern}[^"]*"', content)
                if matches:
                    # Check if it's using PHASE_ARTIFACT_PATHS
                    if "PHASE_ARTIFACT_PATHS" not in content:
                        found_hardcoded.append(f"{filepath.name}: {matches}")
        
        if found_hardcoded:
            print(f"  ⚠️  Found hardcoded paths (should use PHASE_ARTIFACT_PATHS):")
            for item in found_hardcoded[:5]:  # Show first 5
                print(f"      {item}")
            self.warnings.append(f"Hardcoded paths found: {found_hardcoded}")
            return False
        
        print(f"  ✅ No hardcoded paths found")
        return True
    
    def test_all_constitution_checkers_use_phase_paths(self) -> bool:
        """測試所有 Constitution checkers 使用 PHASE_ARTIFACT_PATHS"""
        print("  Checking Constitution checkers use phase_paths...")
        
        required_checkers = {
            "verification_constitution_checker.py": ["BASELINE.md", "TEST_RESULTS.md"],
            "quality_report_constitution_checker.py": ["QUALITY_REPORT.md"],
            "risk_management_constitution_checker.py": ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
            "configuration_constitution_checker.py": ["CONFIG_RECORDS.md"],
        }
        
        all_ok = True
        for checker, expected_artifacts in required_checkers.items():
            filepath = self.constitution_dir / checker
            if not filepath.exists():
                self.errors.append(f"{checker} not found")
                print(f"  ❌ {checker} not found")
                all_ok = False
                continue
            
            content = filepath.read_text()
            
            # Check if it imports PHASE_ARTIFACT_PATHS
            if "PHASE_ARTIFACT_PATHS" not in content:
                print(f"  ❌ {checker} doesn't import PHASE_ARTIFACT_PATHS")
                self.errors.append(f"{checker} doesn't use PHASE_ARTIFACT_PATHS")
                all_ok = False
            else:
                print(f"  ✅ {checker} uses PHASE_ARTIFACT_PATHS")
        
        return all_ok
    
    def test_path_consistency_with_plans(self) -> bool:
        """測試路徑與 Phase Plans 一致"""
        print("  Checking path consistency with Phase Plans...")
        
        plan_where = {
            5: "05-verify",
            6: "06-quality",
            7: "07-risk",
            8: "08-config",
        }
        
        all_ok = True
        for phase, expected_dir in plan_where.items():
            if phase not in PHASE_ARTIFACT_PATHS:
                continue
            
            paths = PHASE_ARTIFACT_PATHS[phase]
            for artifact, path_list in paths.items():
                # Check if any path matches the expected directory
                has_match = any(expected_dir in p for p in path_list)
                if not has_match:
                    print(f"  ⚠️  Phase {phase} {artifact}: expected '{expected_dir}' not in paths")
                    self.warnings.append(f"Phase {phase} {artifact}: {expected_dir} not in {path_list}")
                    all_ok = False
        
        if all_ok:
            print(f"  ✅ All paths consistent with Phase Plans")
        
        return all_ok
    
    def test_no_glob_on_wrong_paths(self) -> bool:
        """測試沒有在錯誤路徑使用 glob"""
        print("  Checking for glob() on wrong paths...")
        
        # Check constitution checkers for glob usage
        constitution_checkers = self.constitution_dir.glob("*_checker.py")
        
        issues = []
        for filepath in constitution_checkers:
            content = filepath.read_text()
            
            # If it has glob, it should also have PHASE_ARTIFACT_PATHS
            if "glob(" in content and "PHASE_ARTIFACT_PATHS" not in content:
                issues.append(f"{filepath.name}: uses glob() without PHASE_ARTIFACT_PATHS")
        
        if issues:
            print(f"  ⚠️  Found glob() without centralized paths:")
            for issue in issues:
                print(f"      {issue}")
            self.warnings.append(f"glob() without centralized paths: {issues}")
            return False
        
        print(f"  ✅ No improper glob() usage")
        return True


def main():
    """主函數"""
    test = PathContractTest()
    passed = test.run_all()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if test.errors:
        print(f"\n❌ ERRORS: {len(test.errors)}")
        for err in test.errors:
            print(f"    {err}")
    
    if test.warnings:
        print(f"\n⚠️  WARNINGS: {len(test.warnings)}")
        for warn in test.warnings:
            print(f"    {warn}")
    
    if passed and not test.errors and not test.warnings:
        print("\n✅ ALL TESTS PASSED")
        return 0
    elif passed:
        print("\n⚠️  TESTS PASSED WITH WARNINGS")
        return 0
    else:
        print("\n❌ TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
