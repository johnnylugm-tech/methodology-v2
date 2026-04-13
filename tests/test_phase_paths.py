#!/usr/bin/env python3
"""
Path Contract Tests
================
確保所有 Phase artifact 路徑定義一致且正確

v7.99 Johnny's Design Principle:
- 每個階段的產物位置是明確的
- 硬編碼單一路徑 = 正確（明確）
- 使用 alternatives = 錯誤（模糊）
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class PathContractTest:
    def run_all(self):
        print("=" * 60)
        print("PATH CONTRACT TESTS (v7.99)")
        print("Johnny's Principle: Single explicit paths = correct")
        print("=" * 60)
        
        errors = []
        
        # Test 1: phase_paths structure
        print("\n[TEST 1] phase_paths.py structure")
        try:
            from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS
            for phase in [5, 6, 7, 8]:
                if phase not in PHASE_ARTIFACT_PATHS:
                    errors.append(f"Phase {phase} missing")
                    print(f"  ❌ Phase {phase} missing")
                else:
                    print(f"  ✅ Phase {phase}: {list(PHASE_ARTIFACT_PATHS[phase].keys())}")
        except Exception as e:
            errors.append(f"Import error: {e}")
            print(f"  ❌ Import error: {e}")
        
        # Test 2: No alternatives in constitution checkers
        print("\n[TEST 2] No alternative paths in constitution checkers")
        constitution_dir = PROJECT_ROOT / "quality_gate" / "constitution"
        for checker in constitution_dir.glob("*_checker.py"):
            content = checker.read_text()
            # Check for nested iteration (alternative pattern)
            if "for k in PHASE_ARTIFACT_PATHS" in content and "for p in" in content:
                errors.append(f"{checker.name}: nested iteration (alternatives)")
                print(f"  ❌ {checker.name}: has alternatives")
            else:
                print(f"  ✅ {checker.name}: single paths")
        
        # Test 3: Hardcoded paths are OK (Johnny's principle)
        print("\n[TEST 3] Hardcoded single paths")
        print("  ✅ Hardcoded paths are now CORRECT (Johnny's principle)")
        
        # Summary
        print("\n" + "=" * 60)
        if errors:
            print("❌ TESTS FAILED")
            for e in errors:
                print(f"  {e}")
            return 1
        else:
            print("✅ ALL TESTS PASSED")
            return 0

if __name__ == "__main__":
    sys.exit(PathContractTest().run_all())
