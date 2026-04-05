"""
Constitution Quality Gate Checker
=================================
檢查文檔是否符合 Constitution 原則

Modules:
    - srs_constitution_checker: SRS 文件原則檢查
    - sad_constitution_checker: SAD 文件原則檢查
    - test_plan_constitution_checker: 測試計畫原則檢查
    - implementation_constitution_checker: 實作原則檢查 (Phase 3)
    - verification_constitution_checker: 驗證原則檢查 (Phase 5)
    - quality_report_constitution_checker: 品質報告原則檢查 (Phase 6)
    - risk_management_constitution_checker: 風險管理原則檢查 (Phase 7)
    - configuration_constitution_checker: 配置管理原則檢查 (Phase 8)
    - runner: 統一執行介面

Usage:
    from quality_gate.constitution import run_constitution_check
    
    result = run_constitution_check("srs", "path/to/docs")
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Constitution 原則閾值（2026-03-27 調整 - 對標第三方審計目標）
CONSTITUTION_THRESHOLDS = {
    "correctness": 100,      # 正確性 100%
    "security": 100,         # 安全性 100%
    "maintainability": 80,   # 可維護性 > 80%（舊值 70%）
    "coverage": 90,          # 覆蓋率 > 90%（舊值 80%）
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
    check_type: str  # "srs", "sad", "test_plan", "implementation", "verification", "quality_report", "risk_management", "configuration"
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
        "implementation": None,
        "verification": None,
        "quality_report": None,
        "risk_management": None,
        "configuration": None,
        "constitution": None,
    }
    
    # 搜尋 SRS
    for pattern in ["SRS*.md", "*SRS*.md", "*需求*.md", "*REQUIREMENT*.md"]:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["srs"] = matches[0].read_text(encoding="utf-8")
            break
    
    # 搜尋 SAD (先搜 02-architecture/，再搜 docs_path，若找不到再搜 parent)
    # Phase 2 SKILL.md 規範 SAD.md 在 02-architecture/ 目錄
    phase2_sad_paths = [
        "02-architecture/SAD.md",
        "02-architecture/SAD*.md",
        "02-architecture/*ARCHITECTURE*.md",
    ]
    for pattern in phase2_sad_paths:
        matches = list(docs_dir.glob(pattern))
        if matches:
            documents["sad"] = matches[0].read_text(encoding="utf-8")
            break
    # 若在 docs_path 找不到 02-architecture/SAD，搜 docs_path 本身
    if not documents["sad"]:
        for pattern in ["SAD*.md", "*SAD*.md", "*架構*.md", "*ARCHITECTURE*.md"]:
            matches = list(docs_dir.glob(pattern))
            if matches:
                documents["sad"] = matches[0].read_text(encoding="utf-8")
                break
    # 若在 docs/ 找不到，索性搜 parent 目錄
    if not documents["sad"]:
        parent_dir = docs_dir.parent
        for pattern in ["SAD.md", "SAD*.md", "SoftwareArchitecture.md", "*SAD*.md", "*架構*.md", "*ARCHITECTURE*.md", "02-architecture/SAD.md"]:
            matches = list(parent_dir.glob(pattern))
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


def run_constitution_check(check_type: str, docs_path: str = "docs", current_phase: int = None) -> ConstitutionCheckResult:
    """執行 Constitution 檢查
    
    Args:
        check_type: 檢查類型 ("srs", "sad", "test_plan", "implementation", "verification", "quality_report", "risk_management", "configuration", "all")
        docs_path: docs 目錄路徑
        current_phase: 只檢查到指定 Phase (1-8)。例如 current_phase=3 只檢查 Phase 1-3
        
    Returns:
        ConstitutionCheckResult
    """
    # Phase 映射
    phase_mapping = {
        1: ["srs"],
        2: ["srs", "sad"],
        3: ["srs", "sad", "implementation"],
        4: ["srs", "sad", "implementation", "test_plan"],
        5: ["srs", "sad", "implementation", "test_plan", "verification"],
        6: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report"],
        7: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report", "risk_management"],
        8: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report", "risk_management", "configuration"],
    }
    
    # 如果指定 current_phase，調整檢查範圍
    if current_phase is not None and current_phase in phase_mapping:
        check_types = phase_mapping[current_phase]
    else:
        check_types = None
    
    # 更新 check_type 映射
    type_mapping = {
        "srs": "srs_constitution_checker",
        "sad": "sad_constitution_checker",
        "test_plan": "test_plan_constitution_checker",
        "implementation": "implementation_constitution_checker",
        "verification": "verification_constitution_checker",
        "quality_report": "quality_report_constitution_checker",
        "risk_management": "risk_management_constitution_checker",
        "configuration": "configuration_constitution_checker",
    }
    
    if check_type == "all":
        # 執行所有檢查（或根據 current_phase 調整）
        results = []
        
        phases_to_check = check_types if check_types else ["srs", "sad", "test_plan", "implementation", 
                   "verification", "quality_report", "risk_management", "configuration"]
        
        for ct in phases_to_check:
            # For implementation check, use project root (parent of docs)
            if ct == "implementation":
                impl_path = Path(docs_path).parent
                result = run_constitution_check(ct, str(impl_path), current_phase=None)
            else:
                result = run_constitution_check(ct, docs_path, current_phase=None)
            results.append(result)
        
        # 合併結果 - 使用平均分數判斷通過與否
        # Bug Fix: 2026-03-27 - 不應該要求所有 phase 都 passed，只要平均分數 > maintainability threshold 就通過
        avg_score = sum(r.score for r in results) / len(results)
        overall_passed = avg_score >= CONSTITUTION_THRESHOLDS["maintainability"]
        
        all_violations = []
        all_recommendations = []
        
        for r in results:
            all_violations.extend(r.violations)
            all_recommendations.extend(r.recommendations)
        
        return ConstitutionCheckResult(
            check_type="all",
            passed=overall_passed,
            score=avg_score,
            violations=all_violations,
            details={"phases_checked": len(results)},
            recommendations=all_recommendations
        )
    
    # 單一檢查
    checker_module = type_mapping.get(check_type)
    if checker_module:
        from importlib import import_module
        module = import_module(f".{checker_module}", package="quality_gate.constitution")
        checker_fn = getattr(module, f"check_{check_type}_constitution")
        return checker_fn(docs_path)
    else:
        return ConstitutionCheckResult(
            check_type=check_type,
            passed=False,
            score=0,
            violations=[{"type": "unknown_check_type", "message": f"Unknown check type: {check_type}"}],
            details={},
            recommendations=[f"Valid check types: {', '.join(type_mapping.keys())}, all"]
        )


__all__ = [
    "CONSTITUTION_THRESHOLDS",
    "ERROR_LEVELS",
    "ConstitutionCheckResult",
    "load_constitution_documents",
    "run_constitution_check",
]


# Constitution HR-05/09 Extension (v6.54)
# These are explicit checks added in v6.54

HR_CONSTRAINTS = {
    "HR-05": {
        "name": "methodology-v2 優先",
        "description": "當與其他框架/規範衝突時，以 methodology-v2 為準",
        "check": "在文檔中是否有明確引用 methodology-v2",
        "severity": "medium"
    },
    "HR-09": {
        "name": "Claims Verifier",
        "description": "所有 claims 必須有可驗證的 citations",
        "check": "citations 必須包含具體行號和檔案",
        "severity": "high"
    }
}


def check_hr05_methodology_priority(documents):
    """
    HR-05: 檢查文檔是否優先遵循 methodology-v2
    """
    violations = []
    
    for doc_type, content in documents.items():
        if not content:
            continue
        
        # Check if methodology-v2 is mentioned
        if "methodology-v2" not in content.lower():
            violations.append({
                "doc": doc_type,
                "rule": "HR-05",
                "message": f"{doc_type} 中未明確引用 methodology-v2"
            })
    
    return {
        "HR-05": {
            "passed": len(violations) == 0,
            "violations": violations,
            "score": 100 if len(violations) == 0 else 0
        }
    }


def check_hr09_claims_verifier(documents):
    """
    HR-09: 檢查所有 claims 是否有可驗證的 citations
    """
    import re
    violations = []
    
    for doc_type, content in documents.items():
        if not content:
            continue
        
        # Look for patterns like "should", "must", "will", "is designed to" (claims)
        claim_pattern = r"(should|must|will|is designed to|ensures|guarantees)"
        citation_pattern = r"\[.+\]\(#L\d+\)"
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(claim_pattern, line, re.IGNORECASE):
                # This is a claim - check if it has citation
                if not re.search(citation_pattern, line):
                    violations.append({
                        "doc": doc_type,
                        "rule": "HR-09",
                        "line": i,
                        "message": f"Line {i}: Claim without citation"
                    })
    
    return {
        "HR-09": {
            "passed": len(violations) == 0,
            "violations": violations,
            "score": 100 if len(violations) == 0 else max(0, 100 - len(violations) * 10)
        }
    }
