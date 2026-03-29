#!/usr/bin/env python3
"""
UnifiedGate Test Coverage Matrix
=================================
驗證 UnifiedGate 中所有 13+ 檢查工具的測試覆蓋。

使用方式：
    from tests.test_unified_gate_coverage import run_coverage_matrix
    
    result = run_coverage_matrix("/path/to/project")
    print(result.coverage_percentage)
    
    # 或使用命令列
    # python -m tests.test_unified_gate_coverage /path/to/project
"""

import sys
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# 添加專案根目錄到 Python 路徑
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# 嘗試匯入 UnifiedGate
try:
    from quality_gate.unified_gate import UnifiedGate, UnifiedGateResult
    UNIFIED_GATE_AVAILABLE = True
except ImportError:
    UNIFIED_GATE_AVAILABLE = False


# UnifiedGate 中的檢查工具列表（根據 unified_gate.py 分析）
CHECKER_DEFINITIONS = {
    # 核心檢查器（舊版）
    "document_checker": {
        "name": "Document Checker",
        "description": "檢查文件是否存在和基本格式",
        "method": "_check_documents",
        "required": True,
    },
    "constitution_checker": {
        "name": "Constitution Checker",
        "description": "檢查 Constitution 合規性",
        "method": "_check_constitution",
        "required": True,
    },
    "phase_reference_checker": {
        "name": "Phase Reference Checker",
        "description": "檢查 Phase 參照完整性",
        "method": "_check_phase_references",
        "required": True,
    },
    
    # 新增檢查器（2026-03-28/29）
    "spec_logic_checker": {
        "name": "Spec Logic Checker",
        "description": "檢查規格邏輯正確性",
        "method": "_check_logic_correctness",
        "required": False,
    },
    "fr_id_tracker": {
        "name": "FR ID Tracker",
        "description": "追蹤功能需求 ID",
        "method": "_check_fr_id_tracking",
        "required": False,
    },
    "threat_analyzer": {
        "name": "Threat Analyzer",
        "description": "分析安全威脅",
        "method": "_check_threat_analysis",
        "required": False,
    },
    "coverage_checker": {
        "name": "Coverage Checker",
        "description": "檢查測試覆蓋率",
        "method": "_check_coverage",
        "required": False,
    },
    "issue_tracker": {
        "name": "Issue Tracker",
        "description": "追蹤問題單",
        "method": "_check_issues",
        "required": False,
    },
    "risk_status_checker": {
        "name": "Risk Status Checker",
        "description": "檢查風險狀態",
        "method": "_check_risk_status",
        "required": False,
    },
    "verification_constitution": {
        "name": "Verification Constitution",
        "description": "驗證 Constitution",
        "method": "_check_verification_constitution",
        "required": False,
    },
    "quality_report_constitution": {
        "name": "Quality Report Constitution",
        "description": "品質報告 Constitution",
        "method": "_check_quality_report_constitution",
        "required": False,
    },
    "risk_management_constitution": {
        "name": "Risk Management Constitution",
        "description": "風險管理 Constitution",
        "method": "_check_risk_management_constitution",
        "required": False,
    },
    "configuration_constitution": {
        "name": "Configuration Constitution",
        "description": "配置管理 Constitution",
        "method": "_check_configuration_constitution",
        "required": False,
    },
    "fr_verification_method": {
        "name": "FR Verification Method",
        "description": "功能需求驗證方法",
        "method": "_check_fr_verification_method",
        "required": False,
    },
    "fr_coverage_checker": {
        "name": "FR Coverage Checker",
        "description": "功能需求覆蓋率",
        "method": "_check_fr_coverage",
        "required": False,
    },
    "error_handling_checker": {
        "name": "Error Handling Checker",
        "description": "錯誤處理檢查",
        "method": "_check_error_handling",
        "required": False,
    },
    "module_tracking_checker": {
        "name": "Module Tracking Checker",
        "description": "模組追蹤檢查",
        "method": "_check_module_tracking",
        "required": False,
    },
    "compliance_matrix_checker": {
        "name": "Compliance Matrix Checker",
        "description": "合規矩陣檢查",
        "method": "_check_compliance_matrix",
        "required": False,
    },
    "negative_test_checker": {
        "name": "Negative Test Checker",
        "description": "負面測試檢查",
        "method": "_check_negative_test",
        "required": False,
    },
    "tc_trace_checker": {
        "name": "TC Trace Checker",
        "description": "測試用例追蹤檢查",
        "method": "_check_tc_trace",
        "required": False,
    },
    "tc_derivation_checker": {
        "name": "TC Derivation Checker",
        "description": "測試用例衍生檢查",
        "method": "_check_tc_derivation",
        "required": False,
    },
    "pytest_result_checker": {
        "name": "Pytest Result Checker",
        "description": "Pytest 結果檢查",
        "method": "_check_pytest_result",
        "required": False,
    },
    "root_cause_checker": {
        "name": "Root Cause Checker",
        "description": "根本原因分析檢查",
        "method": "_check_root_cause",
        "required": False,
    },
    
    # Phase 相關檢查器
    "folder_structure_checker": {
        "name": "Folder Structure Checker",
        "description": "資料夾結構檢查",
        "method": "_check_folder_structure",
        "required": False,
    },
    "phase_enforcer": {
        "name": "Phase Enforcer",
        "description": "Phase 強制執行",
        "method": "_check_phase_enforcement",
        "required": False,
    },
}


@dataclass
class CheckerCoverage:
    """單個檢查器的覆蓋資訊"""
    checker_id: str
    name: str
    description: str
    method: str
    implemented: bool
    tested: bool
    test_file: Optional[str] = None
    test_count: int = 0
    notes: str = ""


@dataclass
class CoverageMatrixResult:
    """覆蓋矩陣結果"""
    total_checkers: int
    implemented_checkers: int
    tested_checkers: int
    required_checkers: int
    required_tested: int
    coverage_percentage: float
    required_coverage_percentage: float
    checkers: List[CheckerCoverage]
    missing_tests: List[str]
    untested_required: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    def print_summary(self) -> str:
        """產出摘要報告"""
        lines = [
            f"{'='*70}",
            f"UnifiedGate Test Coverage Matrix",
            f"{'='*70}",
            f"Total Checkers: {self.total_checkers}",
            f"Implemented: {self.implemented_checkers}",
            f"Tested: {self.tested_checkers}",
            f"Coverage: {self.coverage_percentage:.1f}%",
            f"",
            f"Required Checkers: {self.required_checkers}",
            f"Required Tested: {self.required_tested}",
            f"Required Coverage: {self.required_coverage_percentage:.1f}%",
            f"",
        ]
        
        if self.missing_tests:
            lines.append("Checkers WITHOUT tests:")
            for checker in self.missing_tests:
                lines.append(f"  - {checker}")
            lines.append("")
        
        if self.untested_required:
            lines.append("⚠️  Required checkers WITHOUT tests:")
            for checker in self.untested_required:
                lines.append(f"  - {checker}")
            lines.append("")
        
        lines.append(f"{'='*70}")
        return "\n".join(lines)


def get_unified_gate_methods() -> Set[str]:
    """
    取得 UnifiedGate 實例的所有檢查方法
    
    Returns:
        Set[str]: 方法名稱集合
    """
    if not UNIFIED_GATE_AVAILABLE:
        return set()
    
    try:
        # 建立一個空的 UnifiedGate 實例
        project_path = str(Path(__file__).parent.parent)
        gate = UnifiedGate(project_path)
        
        # 取得所有方法
        methods = set()
        for attr_name in dir(gate):
            if attr_name.startswith("_check_") and callable(getattr(gate, attr_name)):
                methods.add(attr_name)
        
        return methods
    except Exception as e:
        print(f"Error getting UnifiedGate methods: {e}")
        return set()


def get_tested_checkers() -> Set[str]:
    """
    從測試檔案取得已測試的檢查器
    
    Returns:
        Set[str]: 已測試的檢查器 ID 集合
    """
    tested = set()
    
    # 讀取 test_unified_gate.py
    test_file = Path(__file__).parent / "test_unified_gate.py"
    if test_file.exists():
        try:
            content = test_file.read_text()
            
            # 分析測試檔案，找出測試的檢查器
            # 這裡簡單地根據方法名稱識別
            for method_name in content.split("def test_"):
                # 檢查是否呼叫了對應的 _check_* 方法
                for checker_id, definition in CHECKER_DEFINITIONS.items():
                    if definition["method"].replace("_check_", "") in method_name:
                        tested.add(checker_id)
        except Exception as e:
            print(f"Error reading test file: {e}")
    
    return tested


def build_coverage_matrix(
    project_path: Optional[str] = None
) -> CoverageMatrixResult:
    """
    建立覆蓋矩陣
    
    Args:
        project_path: 專案根目錄路徑
        
    Returns:
        CoverageMatrixResult: 覆蓋矩陣結果
    """
    # 取得 UnifiedGate 的實際方法
    implemented_methods = get_unified_gate_methods()
    
    # 取得已測試的檢查器
    tested_checkers = get_tested_checkers()
    
    # 建立每個檢查器的覆蓋資訊
    checkers = []
    implemented_count = 0
    tested_count = 0
    required_count = 0
    required_tested_count = 0
    missing_tests = []
    untested_required = []
    
    for checker_id, definition in CHECKER_DEFINITIONS.items():
        # 檢查是否已實現
        method_name = definition["method"]
        is_implemented = method_name in implemented_methods
        
        # 檢查是否已測試
        is_tested = checker_id in tested_checkers
        
        # 檢查測試數量（如果已測試）
        test_count = 1 if is_tested else 0
        
        # 收集測試檔案路徑
        test_file = None
        if is_tested:
            test_file = str(Path(__file__).parent / "test_unified_gate.py")
        
        # 產生 notes
        notes = ""
        if not is_implemented:
            notes = "NOT IMPLEMENTED"
        elif not is_tested:
            notes = "NO TEST COVERAGE"
        
        # 計算計數
        if is_implemented:
            implemented_count += 1
        
        if is_tested:
            tested_count += 1
        
        if definition["required"]:
            required_count += 1
            if is_tested:
                required_tested_count += 1
            else:
                untested_required.append(definition["name"])
        
        if is_implemented and not is_tested:
            missing_tests.append(definition["name"])
        
        checker_coverage = CheckerCoverage(
            checker_id=checker_id,
            name=definition["name"],
            description=definition["description"],
            method=method_name,
            implemented=is_implemented,
            tested=is_tested,
            test_file=test_file,
            test_count=test_count,
            notes=notes
        )
        
        checkers.append(checker_coverage)
    
    # 計算覆蓋率
    total = len(CHECKER_DEFINITIONS)
    coverage_percentage = (tested_count / total * 100) if total > 0 else 0
    
    required_coverage = (
        required_tested_count / required_count * 100 
        if required_count > 0 else 100
    )
    
    return CoverageMatrixResult(
        total_checkers=total,
        implemented_checkers=implemented_count,
        tested_checkers=tested_count,
        required_checkers=required_count,
        required_tested=required_tested_count,
        coverage_percentage=coverage_percentage,
        required_coverage_percentage=required_coverage,
        checkers=checkers,
        missing_tests=missing_tests,
        untested_required=untested_required
    )


def run_coverage_matrix(
    project_path: Optional[str] = None,
    verbose: bool = True
) -> CoverageMatrixResult:
    """
    執行覆蓋矩陣測試
    
    Args:
        project_path: 專案根目錄路徑
        verbose: 是否輸出詳細資訊
        
    Returns:
        CoverageMatrixResult: 覆蓋矩陣結果
    """
    if project_path is None:
        project_path = str(Path(__file__).parent.parent)
    
    result = build_coverage_matrix(project_path)
    
    if verbose:
        print(result.print_summary())
    
    return result


def main():
    """命令列入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="UnifiedGate Test Coverage Matrix"
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
    parser.add_argument(
        "--detail", "-d",
        action="store_true",
        help="Show detailed checker information"
    )
    
    args = parser.parse_args()
    
    result = run_coverage_matrix(
        project_path=args.project_path,
        verbose=not args.quiet
    )
    
    if args.json:
        print(result.to_json())
    
    if args.detail:
        print("\nDetailed Checker Coverage:")
        print("-" * 70)
        for checker in result.checkers:
            status = "✅" if checker.tested else "❌"
            impl = "✅" if checker.implemented else "❌"
            print(f"{status} {impl} {checker.name}")
            print(f"   Method: {checker.method}")
            print(f"   Notes: {checker.notes}")
            print()
    
    # 返回適當的 exit code
    passed = result.required_coverage_percentage >= 80
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
