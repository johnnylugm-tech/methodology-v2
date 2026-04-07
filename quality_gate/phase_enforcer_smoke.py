#!/usr/bin/env python3
"""
PhaseEnforcer Smoke Test (Independent)
======================================
PhaseEnforcer 的獨立 smoke test，不需要 Ralph Mode 依賴。

此模組提供快速驗證 PhaseEnforcer 基本功能的方式：
- 結構檢查 (L1)
- 內容檢查 (L2)
- 代碼品質檢查 (L3) - 可選

使用方式：
    from quality_gate.phase_enforcer_smoke import run_smoke_test
    
    result = run_smoke_test("/path/to/project")
    print(result.passed)
    
    # 或使用命令列
    # python -m quality_gate.phase_enforcer_smoke /path/to/project
"""

import sys
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, List, Any

# 添加專案根目錄到 Python 路徑
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 嘗試匯入 PhaseEnforcer
try:
    from quality_gate.phase_enforcer import (
        PhaseEnforcer, 
        PhaseEnforcementResult,
        StructureCheckResult,
        ContentCheckResult,
        CodeQualityCheckResult
    )
    PHASE_ENFORCER_AVAILABLE = True
except ImportError:
    PHASE_ENFORCER_AVAILABLE = False


@dataclass
class SmokeTestResult:
    """Smoke test 結果"""
    passed: bool
    phase_enforcer_available: bool
    tests_run: int
    tests_passed: int
    tests_failed: int
    details: Dict[str, Any]
    errors: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    def print_summary(self) -> str:
        """產出摘要報告"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        
        lines = [
            f"{'='*60}",
            f"PhaseEnforcer Smoke Test Result",
            f"{'='*60}",
            f"Status: {status}",
            f"PhaseEnforcer Available: {self.phase_enforcer_available}",
            f"Tests Run: {self.tests_run}",
            f"Tests Passed: {self.tests_passed}",
            f"Tests Failed: {self.tests_failed}",
            f"",
        ]
        
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  🚫 {error}")
            lines.append("")
        
        lines.append("Details:")
        for key, value in self.details.items():
            lines.append(f"  {key}: {value}")
        
        lines.append(f"{'='*60}")
        return "\n".join(lines)


def check_dependencies() -> Dict[str, bool]:
    """
    檢查所有依賴是否可用
    
    Returns:
        Dict[str, bool]: 各依賴的可用狀態
    """
    dependencies = {
        "phase_enforcer": PHASE_ENFORCER_AVAILABLE,
    }
    
    # 檢查 folder_structure_checker
    try:
        from quality_gate.folder_structure_checker import FolderStructureChecker
        dependencies["folder_structure_checker"] = True
    except ImportError:
        dependencies["folder_structure_checker"] = False
    
    # 檢查 unified_gate
    try:
        from quality_gate.unified_gate import UnifiedGate
        dependencies["unified_gate"] = True
    except ImportError:
        dependencies["unified_gate"] = False
    
    # 檢查 Agent Quality Guard
    agent_guard_available = False
    try:
        agent_guard_path = Path(__file__).parent.parent / "agent-quality-guard" / "src"
        if agent_guard_path.exists():
            sys.path.insert(0, str(agent_guard_path))
            from analyzer import analyze_code
            from scorer import score_from_code
            agent_guard_available = True
    except ImportError:
        pass
    dependencies["agent_quality_guard"] = agent_guard_available
    
    return dependencies


def test_initialization(project_path: str) -> bool:
    """
    測試 PhaseEnforcer 初始化
    
    Args:
        project_path: 專案根目錄路徑
        
    Returns:
        bool: 測試是否通過
    """
    if not PHASE_ENFORCER_AVAILABLE:
        return False
    
    try:
        enforcer = PhaseEnforcer(project_path, strict_mode=True)
        return enforcer is not None
    except Exception as e:
        print(f"Initialization test failed: {e}")
        return False


def test_enforce_phase_basic(project_path: str, phase: int = 1) -> bool:
    """
    測試 enforce_phase 基本功能
    
    Args:
        project_path: 專案根目錄路徑
        phase: Phase 編號
        
    Returns:
        bool: 測試是否通過
    """
    if not PHASE_ENFORCER_AVAILABLE:
        return False
    
    try:
        enforcer = PhaseEnforcer(project_path, strict_mode=False)
        result = enforcer.enforce_phase(phase)
        return result is not None and isinstance(result, PhaseEnforcementResult)
    except Exception as e:
        print(f"Enforce phase test failed: {e}")
        return False


def test_result_dataclasses() -> bool:
    """
    測試 Result dataclasses 是否正確定義
    
    Returns:
        bool: 測試是否通過
    """
    if not PHASE_ENFORCER_AVAILABLE:
        return False
    
    try:
        # 測試 StructureCheckResult
        struct_result = StructureCheckResult(
            score=100.0,
            missing=[],
            passed=True
        )
        assert struct_result.score == 100.0
        
        # 測試 ContentCheckResult
        content_result = ContentCheckResult(
            score=85.0,
            missing_sections=[],
            passed=True
        )
        assert content_result.score == 85.0
        
        # 測試 CodeQualityCheckResult
        code_result = CodeQualityCheckResult(
            score=90.0,
            files_scanned=5,
            issues=[],
            passed=True,
            details={}
        )
        assert code_result.score == 90.0
        
        # 測試 PhaseEnforcementResult
        phase_result = PhaseEnforcementResult(
            phase=1,
            passed=True,
            structure_check=struct_result,
            content_check=content_result,
            code_quality_check=code_result,
            gate_score=92.5,
            can_proceed=True,
            blocker_issues=[],
            details={}
        )
        assert phase_result.phase == 1
        assert phase_result.passed is True
        
        return True
    except Exception as e:
        print(f"Dataclass test failed: {e}")
        return False


def test_weights_configuration(project_path: str) -> bool:
    """
    測試權重配置
    
    Args:
        project_path: 專案根目錄路徑
        
    Returns:
        bool: 測試是否通過
    """
    if not PHASE_ENFORCER_AVAILABLE:
        return False
    
    try:
        # 測試預設權重
        enforcer_default = PhaseEnforcer(project_path)
        w_structure, w_content, w_code = enforcer_default.weights
        assert abs(w_structure - 0.25) < 0.01
        assert abs(w_content - 0.25) < 0.01
        assert abs(w_code - 0.50) < 0.01
        
        # 測試自定義權重
        enforcer_custom = PhaseEnforcer(
            project_path, 
            weights=(0.30, 0.30, 0.40)
        )
        w_structure, w_content, w_code = enforcer_custom.weights
        assert abs(w_structure - 0.30) < 0.01
        assert abs(w_content - 0.30) < 0.01
        assert abs(w_code - 0.40) < 0.01
        
        return True
    except Exception as e:
        print(f"Weights configuration test failed: {e}")
        return False


def test_all_phases(project_path: str) -> Dict[int, bool]:
    """
    測試所有 Phase (1-8)
    
    Args:
        project_path: 專案根目錄路徑
        
    Returns:
        Dict[int, bool]: 每個 Phase 的測試結果
    """
    if not PHASE_ENFORCER_AVAILABLE:
        return {}
    
    results = {}
    try:
        enforcer = PhaseEnforcer(project_path, strict_mode=False)
        
        for phase in range(1, 9):
            try:
                result = enforcer.enforce_phase(phase)
                results[phase] = result is not None
            except Exception as e:
                print(f"Phase {phase} test failed: {e}")
                results[phase] = False
    except Exception as e:
        print(f"All phases test failed: {e}")
    
    return results


def run_smoke_test(
    project_path: Optional[str] = None,
    verbose: bool = True
) -> SmokeTestResult:
    """
    執行 PhaseEnforcer smoke test
    
    Args:
        project_path: 專案根目錄路徑（預設為当前目录）
        verbose: 是否輸出詳細資訊
        
    Returns:
        SmokeTestResult: smoke test 結果
    """
    errors = []
    tests_run = 0
    tests_passed = 0
    tests_failed = 0
    
    # 預設路徑
    if project_path is None:
        project_path = str(Path(__file__).parent.parent)
    
    project_path = str(Path(project_path).resolve())
    
    # 檢查依賴
    dependencies = check_dependencies()
    
    if verbose:
        print(f"Project Path: {project_path}")
        print(f"Dependencies: {dependencies}")
    
    # 測試結果收集
    results = {}
    
    # Test 1: 依賴檢查
    tests_run += 1
    results["dependencies"] = dependencies
    
    if not PHASE_ENFORCER_AVAILABLE:
        errors.append("PhaseEnforcer not available")
        tests_failed += 1
    else:
        tests_passed += 1
        
        # Test 2: 初始化測試
        tests_run += 1
        if test_initialization(project_path):
            tests_passed += 1
        else:
            errors.append("Initialization test failed")
            tests_failed += 1
        
        # Test 3: enforce_phase 基本測試
        tests_run += 1
        if test_enforce_phase_basic(project_path):
            tests_passed += 1
        else:
            errors.append("Enforce phase basic test failed")
            tests_failed += 1
        
        # Test 4: Dataclass 測試
        tests_run += 1
        if test_result_dataclasses():
            tests_passed += 1
        else:
            errors.append("Dataclass test failed")
            tests_failed += 1
        
        # Test 5: 權重配置測試
        tests_run += 1
        if test_weights_configuration(project_path):
            tests_passed += 1
        else:
            errors.append("Weights configuration test failed")
            tests_failed += 1
        
        # Test 6: 所有 Phase 測試
        tests_run += 1
        all_phases_results = test_all_phases(project_path)
        results["all_phases"] = all_phases_results
        
        if all(all_phases_results.values()):
            tests_passed += 1
        else:
            errors.append("Some phases failed")
            tests_failed += 1
    
    # 計算最終結果
    passed = tests_failed == 0 and tests_run > 0
    
    # 組裝詳細資訊
    details = {
        "project_path": project_path,
        "dependencies": dependencies,
        "test_results": results
    }
    
    result = SmokeTestResult(
        passed=passed,
        phase_enforcer_available=PHASE_ENFORCER_AVAILABLE,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        details=details,
        errors=errors
    )
    
    if verbose:
        print(result.print_summary())
    
    return result


def main():
    """命令列入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="PhaseEnforcer Smoke Test (Independent)"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project root path"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (no verbose output)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    
    args = parser.parse_args()
    
    result = run_smoke_test(
        project_path=args.project_path,
        verbose=not args.quiet
    )
    
    if args.json:
        print(result.to_json())
    
    # 返回適當的 exit code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
