#!/usr/bin/env python3
"""
VERIFICATION Constitution Checker
================================
檢查 Verification 文檔是否符合 Constitution 原則

Phase 5: 驗證與交付

原則檢查:
1. 正確性 100% - 驗證方法合適、結果可靠
2. 安全性 100% - 驗證環境安全
3. 可維護性 > 70% - 驗證記錄完整

Usage:
    from verification_constitution_checker import check_verification_constitution
    result = check_verification_constitution("/path/to/docs")
"""

import os
from pathlib import Path
from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS, check_artifact_exists
from typing import Dict, List, Optional
from dataclasses import dataclass

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class VerificationChecklist:
    """Verification 檢查清單"""
    # 正確性
    test_results_documented: bool = False
    baseline_established: bool = False
    
    # 安全性（v7.97）
    security_verification: bool = False

def check_verification_constitution(path: str) -> ConstitutionCheckResult:
    """
    Phase 5 (Verification) Constitution Checker
    Phase5_Plan WHERE: 05-verify/
    
    Phase 5 artifacts:
    - BASELINE.md (Phase5_Plan WHERE)
    - VERIFICATION_REPORT.md (Phase5_Plan WHERE)
    - Note: TEST_RESULTS.md and TEST_PLAN.md are Phase 4 artifacts (04-testing/)
    
    Phase 6 Prerequisites:
    - BASELINE.md from Phase 5
    """
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = VerificationChecklist()
    
    # Phase 5 artifacts - only check Phase5_Plan WHERE locations
    project_root = path_obj.parent  # path is typically docs/, go up to project root
    
    # BASELINE.md - Phase5_Plan WHERE: 05-verify/
    baseline_path = project_root / "05-verify/BASELINE.md"
    checklist.baseline_established = baseline_path.exists()
    
    # TEST_RESULTS.md - Phase4_Plan WHERE: 04-testing/ (Phase 4 artifact, checked as prereq)
    test_results_path = project_root / "04-testing/TEST_RESULTS.md"
    checklist.test_results_documented = test_results_path.exists()
    
    # Security 驗證覆蓋檢查（v7.97）
    verification_content = ""
    
    # VERIFICATION_REPORT.md - Phase5_Plan WHERE: 05-verify/
    verification_path = project_root / "05-verify/VERIFICATION_REPORT.md"
    if verification_path.exists():
        verification_content = verification_path.read_text(encoding="utf-8")
    
    # If no VERIFICATION_REPORT, check TEST_RESULTS
    elif test_results_path.exists():
        verification_content = test_results_path.read_text(encoding="utf-8")
    
    # Security verification keywords
    security_keywords = [
        "安全測試", "security test", "滲透測試", "penetration test",
        "漏洞掃描", "vulnerability scan", "安全掃描",
        "認證驗證", "authentication verification", "auth verification",
    ]
    
    checklist.security_verification = any(
        kw.lower() in verification_content.lower()
        for kw in security_keywords
    )
    
    # 評分
    checks = [
        checklist.test_results_documented,
        checklist.baseline_established,
        checklist.security_verification,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    # 違規
    if not checklist.baseline_established:
        violations.append({
            "type": "no_baseline",
            "message": "Verification 缺少 BASELINE.md（應在 05-verify/）",
            "severity": "MEDIUM"
        })
    
    if not checklist.security_verification:
        violations.append({
            "type": "missing_security_verification",
            "message": "Verification 缺少安全驗證結果",
            "severity": "HIGH"
        })
    
    passed = score >= CONSTITUTION_THRESHOLDS["maintainability"]
    
    return ConstitutionCheckResult(
        check_type="verification",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "has_test_results": checklist.test_results_documented,
            "has_baseline": checklist.baseline_established,
            "has_security_verification": checklist.security_verification,
        },
        recommendations=recommendations
    )

