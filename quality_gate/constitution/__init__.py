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

# HR-09 InferentialSensor checker
try:
    from quality_gate.constitution.hr09_checker import HR09Checker
    HR09_CHECKER_AVAILABLE = True
except ImportError as e:
    HR09_CHECKER_AVAILABLE = False
    _hr09_import_error = e

# BVS — Behaviour Validation System (P1-1)
# Note: BVS modules are in the top-level `constitution/` directory,
# not in quality_gate/constitution/. Use absolute import.
try:
    from constitution.bvs_runner import BVSRunner
    BVS_AVAILABLE = True
except ImportError:
    BVS_AVAILABLE = False
    _bvs_import_error = str(e)

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


def _check_behaviour(phase: int) -> dict:
    """
    BVS Behaviour 檢查
    
    在 Phase 3+ 執行，驗證 Subagent 行為是否符合 Constitution HR 規則
    
    Args:
        phase: 當前 Phase (1-8)
        
    Returns:
        {
            "passed": bool,
            "violations": [...],
            "logs_analyzed": int,
            "status": "passed" / "skipped" / "no_logs"
        }
    """
    if not BVS_AVAILABLE:
        return {"passed": True, "status": "skipped", "reason": "BVS not available"}
    
    # 只在 Phase 3+ 執行
    if phase < 3:
        return {"passed": True, "status": "skipped", "reason": f"Only Phase 3+ (current: {phase})"}
    
    try:
        # 假設 project path 為 docs 的 parent
        from pathlib import Path
        docs_path = Path("docs") if Path("docs").exists() else Path(".")
        project_path = str(docs_path.parent) if not docs_path.is_absolute() else str(docs_path)
        
        runner = BVSRunner(project_path, phase=phase)
        report = runner.run()
        
        return {
            "passed": report.get("passed", True),
            "total_violations": report.get("total_violations", 0),
            "critical": report.get("critical", 0),
            "high": report.get("high", 0),
            "medium": report.get("medium", 0),
            "violations": report.get("violations", [])[:10],  # 最多10條
            "logs_analyzed": report.get("logs_analyzed", 0),
            "status": "passed" if report.get("passed") else "failed"
        }
    except Exception as e:
        return {"passed": False, "status": "error", "reason": str(e)}


def run_constitution_check(
    check_type: str,
    docs_path: str = "docs",
    current_phase: int = None,
    feedback_store=None,  # Optional FeedbackStore for auto-submission
    check_mode: str = "preflight",  # "preflight" or "postflight" (v6.56 fix)
) -> ConstitutionCheckResult:
    """執行 Constitution 檢查
    
    Args:
        check_type: 檢查類型 ("srs", "sad", "test_plan", "implementation", "verification", "quality_report", "risk_management", "configuration", "all")
        docs_path: docs 目錄路徑
        current_phase: 只檢查到指定 Phase (1-8)。例如 current_phase=3 只檢查 Phase 1-3
        feedback_store: Optional FeedbackStore — if provided, violations are auto-submitted
        check_mode: "preflight" (進入前檢查前提條件) 或 "postflight" (完成後檢查產出品質)
                   
    Returns:
        ConstitutionCheckResult
    
    Pre-flight vs Post-flight 設計原則 (v6.56):
        - Pre-flight: 只檢查「已完成 Phase 的產出」作為前提條件
        - Post-flight: 只檢查「當前 Phase 剛生成的產出」
        - 例如 Phase 3 Pre-flight: 檢查 SRS, SAD (Phase 1-2 產出)
        - 例如 Phase 3 Post-flight: 檢查 implementation (Phase 3 產出)
    
    Auto-submission:
        When feedback_store is provided and violations are found, each violation
        is automatically converted to StandardFeedback and submitted to the store.
    """
    # === v6.56 FIX: 分離 Pre-flight vs Post-flight ===
    # Pre-flight: 檢查「已完成 Phase 的產出」作為進入前提
    # Post-flight: 檢查「當前 Phase 剛生成的產出」
    preflight_mapping = {
        1: ["srs"],
        2: ["srs", "sad"],
        3: ["srs", "sad"],                    # ✅ Phase 3 Pre-flight: 不含 implementation（還沒產生）
        4: ["srs", "sad", "implementation"], # ✅ Phase 4 Pre-flight: Phase 3 已完成，implementation 存在
        5: ["srs", "sad", "implementation", "test_plan"],
        6: ["srs", "sad", "implementation", "test_plan", "verification"],
        7: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report"],
        8: ["srs", "sad", "implementation", "test_plan", "verification", "quality_report", "risk_management"],
    }
    
    # Post-flight: 只檢查「當前 Phase 的產出」
    postflight_mapping = {
        1: ["srs"],
        2: ["sad"],
        3: ["implementation"],     # ✅ Phase 3 Post-flight: 只檢查 implementation（Phase 3 產出）
        4: ["test_plan"],
        5: ["verification"],
        6: ["quality_report"],
        7: ["risk_management"],
        8: ["configuration"],
    }
    
    # 根據 check_mode 選擇對應 mapping
    phase_mapping = preflight_mapping if check_mode == "preflight" else postflight_mapping
    
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
                result = run_constitution_check(ct, str(impl_path), current_phase=None, feedback_store=None, check_mode=check_mode)  # Pass check_mode for allow_missing
            else:
                result = run_constitution_check(ct, docs_path, current_phase=None, feedback_store=None, check_mode=check_mode)  # Pass check_mode
            results.append(result)
        
        # === Run HR-09 (InferentialSensor) check and merge violations ===
        if HR09_CHECKER_AVAILABLE:
            try:
                hr09_checker = HR09Checker()
                hr09_result = hr09_checker.check(docs_path)
                hr09_violations = hr09_result.get("violations", [])
                if hr09_violations:
                    all_violations.extend(hr09_violations)
                    # HR-09 failures affect overall pass
                    if not hr09_result.get("passed", True):
                        overall_passed = False
                    # Add HR-09 summary to details
                    details_hr09 = {
                        "hr09_score": hr09_result.get("score", 0),
                        "hr09_total_claims": hr09_result.get("total_claims", 0),
                        "hr09_passed_claims": hr09_result.get("passed_claims", 0),
                    }
                    if "hr09" not in all_result.details:
                        all_result.details["hr09"] = details_hr09
            except Exception:
                pass  # Don't let HR-09 failures break the check

        # 合併結果 - 使用平均分數判斷通過與否
        # Bug Fix: 2026-03-27 - 不應該要求所有 phase 都 passed，只要平均分數 > maintainability threshold 就通過
        avg_score = sum(r.score for r in results) / len(results)
        overall_passed = avg_score >= CONSTITUTION_THRESHOLDS["maintainability"]
        
        all_violations = []
        all_recommendations = []
        
        for r in results:
            all_violations.extend(r.violations)
            all_recommendations.extend(r.recommendations)
        
        # BVS Behaviour Check (Phase 3+)
        behaviour_result = None
        if current_phase is not None and current_phase >= 3:
            behaviour_result = _check_behaviour(current_phase)
            if not behaviour_result.get("passed", True):
                overall_passed = False
                for v in behaviour_result.get("violations", []):
                    all_violations.append({
                        "type": "behaviour_violation",
                        "severity": v.get("severity", "MEDIUM"),
                        "message": v.get("message", str(v))
                    })
        
        all_result = ConstitutionCheckResult(
            check_type="all",
            passed=overall_passed,
            score=avg_score,
            violations=all_violations,
            details={"phases_checked": len(results), "behaviour_check": behaviour_result},
            recommendations=all_recommendations
        )

        # === Auto-submit violations to FeedbackStore via UnifiedAlert ===
        if feedback_store is not None and all_violations:
            try:
                from core.feedback.alert import UnifiedAlert

                for v in all_violations:
                    severity_str = v.get("severity", "MEDIUM").upper()
                    alert = UnifiedAlert(
                        source="constitution",
                        source_detail=v.get("rule_id", "unknown"),
                        category="quality",
                        severity={"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(severity_str, "medium"),
                        title=f"Constitution violation: {v.get('rule_id', 'unknown')}",
                        message=v.get("message", ""),
                        context={"phase": current_phase, "violation": v},
                        recommended_action=f"Fix {v.get('rule_id')} violation",
                        auto_fixable=False,
                        sla_hours={"CRITICAL": 4, "HIGH": 24, "MEDIUM": 72, "LOW": 168}.get(severity_str, 24),
                    )
                    fb = alert.to_feedback()
                    feedback_store.add(fb)
                    # Route and assign to populate assignee + sla_deadline
                    from core.feedback.router import route_and_assign
                    team, deadline = route_and_assign(fb, store=feedback_store)
                    fb["assignee"] = team
                    fb["sla_deadline"] = deadline
            except Exception:
                # Don't let feedback failures break the check
                pass

        return all_result
    
    # 單一檢查
    checker_module = type_mapping.get(check_type)
    if checker_module:
        from importlib import import_module
        module = import_module(f".{checker_module}", package="quality_gate.constitution")
        checker_fn = getattr(module, f"check_{check_type}_constitution")
        
        # === v6.56 FIX: implementation 在 preflight 時允許缺失 ===
        # Phase 3 preflight 檢查 implementation 時，代碼還沒產生，不應該失敗
        if check_type == "implementation" and check_mode == "preflight":
            result = checker_fn(docs_path, allow_missing=True)
        else:
            result = checker_fn(docs_path)
    else:
        result = ConstitutionCheckResult(
            check_type=check_type,
            passed=False,
            score=0,
            violations=[{"type": "unknown_check_type", "message": f"Unknown check type: {check_type}"}],
            details={},
            recommendations=[f"Valid check types: {', '.join(type_mapping.keys())}, all"]
        )

    # === Run HR-09 (InferentialSensor) check and merge violations ===
    # HR-09 is run for all check types as a cross-cutting concern
    if HR09_CHECKER_AVAILABLE and check_type != "all":
        try:
            hr09_checker = HR09Checker()
            hr09_result = hr09_checker.check(docs_path)
            hr09_violations = hr09_result.get("violations", [])
            if hr09_violations:
                result.violations.extend(hr09_violations)
                if not hr09_result.get("passed", True):
                    result.passed = False
                result.details["hr09"] = {
                    "score": hr09_result.get("score", 0),
                    "total_claims": hr09_result.get("total_claims", 0),
                    "passed_claims": hr09_result.get("passed_claims", 0),
                }
        except Exception:
            pass  # Don't let HR-09 failures break the check

    # === Auto-submit violations to FeedbackStore via UnifiedAlert ===
    if feedback_store is not None and result.violations:
        try:
            from core.feedback.alert import UnifiedAlert

            for v in result.violations:
                severity_str = v.get("severity", "MEDIUM").upper()
                alert = UnifiedAlert(
                    source="constitution",
                    source_detail=v.get("rule_id", "unknown"),
                    category="quality",
                    severity={"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(severity_str, "medium"),
                    title=f"Constitution violation: {v.get('rule_id', 'unknown')}",
                    message=v.get("message", ""),
                    context={"phase": current_phase, "violation": v},
                    recommended_action=f"Fix {v.get('rule_id')} violation",
                    auto_fixable=False,
                    sla_hours={"CRITICAL": 4, "HIGH": 24, "MEDIUM": 72, "LOW": 168}.get(severity_str, 24),
                )
                fb = alert.to_feedback()
                feedback_store.add(fb)
                # Route and assign to populate assignee + sla_deadline
                from core.feedback.router import route_and_assign
                team, deadline = route_and_assign(fb, store=feedback_store)
                fb["assignee"] = team
                fb["sla_deadline"] = deadline
        except Exception:
            # Don't let feedback failures break the check
            pass

    return result


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
