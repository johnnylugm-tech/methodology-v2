"""
Constitution Quality Gate Checker
=================================
檢查文檔是否符合 Constitution 原則

Modules:
    - srs_constitution_checker: SRS 文件原則檢查
    - sad_constitution_checker: SAD 文件原則檢查
    - test_plan_constitution_checker: 測試計畫原則檢查
    - runner: 統一執行介面

Usage:
    from quality_gate.constitution import run_constitution_check
    
    result = run_constitution_check("srs", "path/to/docs")
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Constitution 原則閾值
CONSTITUTION_THRESHOLDS = {
    "correctness": 100,      # 正確性 100%
    "security": 100,         # 安全性 100%
    "maintainability": 70,   # 可維護性 > 70%
    "coverage": 80,          # 覆蓋率 > 80%
}

# 錯誤等級定義
ERROR_LEVELS = {
    "L1": {"name": "配置錯誤", "recoverable": False, "circuit_breaker": True},
    "L2": {"name": "API 錯誤", "recoverable": True, "circuit_breaker": True},
    "L3": {"name": "業務錯誤", "recoverable": True, "circuit_breaker": True},
    "L4": {"name": "預期異常", "recoverable": True, "circuit_breaker": False},
}


@dataclass
class ConstitutionCheckResult:
    """Constitution 檢查結果"""
    check_type: str  # "srs", "sad", "test_plan"
    passed: bool
    score: float
    violations: List[Dict]
    details: Dict
    recommendations: List[str]


def load_constitution_documents(docs_path: str) -> Dict[str, Optional[str]]:
    """載入所有 Constitution 相關文檔
    
    Args:
        docs_path: docs 目錄路徑
        
    Returns:
        Dict[doc_type, content]
    """
    docs_dir = Path(docs_path)
    
    documents = {
        "srs": None,
        "sad": None,
        "test_plan": None,
        "constitution": None,
    }
    
    # 搜尋 SRS
    for pattern in ["SRS*.md", "*SRS*.md", "*需求*.md", "*REQUIREMENT*.md"]:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["srs"] = matches[0].read_text(encoding="utf-8")
            break
    
    # 搜尋 SAD
    for pattern in ["SAD*.md", "*SAD*.md", "*架構*.md", "*ARCHITECTURE*.md"]:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["sad"] = matches[0].read_text(encoding="utf-8")
            break
    
    # 搜尋 Test Plan
    for pattern in ["TEST*.md", "*測試*.md", "*TEST_PLAN*.md"]:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["test_plan"] = matches[0].read_text(encoding="utf-8")
            break
    
    # 搜尋 Constitution
    const_patterns = ["CONSTITUTION*.md", "*品質監控*.md"]
    for pattern in const_patterns:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["constitution"] = matches[0].read_text(encoding="utf-8")
            break
    
    return documents


def run_constitution_check(check_type: str, docs_path: str) -> ConstitutionCheckResult:
    """執行 Constitution 檢查
    
    Args:
        check_type: 檢查類型 ("srs", "sad", "test_plan", "all")
        docs_path: docs 目錄路徑
        
    Returns:
        ConstitutionCheckResult
    """
    if check_type == "all":
        # 執行所有檢查
        results = []
        for ct in ["srs", "sad", "test_plan"]:
            result = run_constitution_check(ct, docs_path)
            results.append(result)
        
        # 合併結果
        all_passed = all(r.passed for r in results)
        avg_score = sum(r.score for r in results) / len(results)
        all_violations = []
        all_recommendations = []
        
        for r in results:
            all_violations.extend(r.violations)
            all_recommendations.extend(r.recommendations)
        
        return ConstitutionCheckResult(
            check_type="all",
            passed=all_passed,
            score=avg_score,
            violations=all_violations,
            details={},
            recommendations=all_recommendations
        )
    
    # 單一檢查
    if check_type == "srs":
        from .srs_constitution_checker import check_srs_constitution
        return check_srs_constitution(docs_path)
    elif check_type == "sad":
        from .sad_constitution_checker import check_sad_constitution
        return check_sad_constitution(docs_path)
    elif check_type == "test_plan":
        from .test_plan_constitution_checker import check_test_plan_constitution
        return check_test_plan_constitution(docs_path)
    else:
        return ConstitutionCheckResult(
            check_type=check_type,
            passed=False,
            score=0,
            violations=[{"type": "unknown_check_type", "message": f"Unknown check type: {check_type}"}],
            details={},
            recommendations=[f"Valid check types: srs, sad, test_plan, all"]
        )


__all__ = [
    "CONSTITUTION_THRESHOLDS",
    "ERROR_LEVELS",
    "ConstitutionCheckResult",
    "load_constitution_documents",
    "run_constitution_check",
]
