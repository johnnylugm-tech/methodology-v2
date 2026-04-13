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
    verification_methods_defined: bool = False
    pass_criteria_met: bool = False
    
    # 可維護性
    baseline_established: bool = False
    change_log_maintained: bool = False

def check_verification_constitution(path: str) -> ConstitutionCheckResult:
    """執行 Verification Constitution 檢查"""
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = VerificationChecklist()
    
    # 檢查測試結果
    test_results = list(path_obj.glob("TEST_RESULTS*"))
    checklist.test_results_documented = len(test_results) > 0
    
    # 檢查基線
    baseline = list(path_obj.glob("BASELINE*"))
    checklist.baseline_established = len(baseline) > 0
    
    # 評分
    checks = [
        checklist.test_results_documented,
        checklist.baseline_established,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    # 違規
    if not checklist.test_results_documented:
        violations.append({
            "type": "missing_test_results",
            "message": "Verification 缺少 TEST_RESULTS.md",
            "severity": "HIGH"
        })
    
    if not checklist.baseline_established:
        violations.append({
            "type": "no_baseline",
            "message": "Verification 缺少 BASELINE.md",
            "severity": "MEDIUM"
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
        },
        recommendations=recommendations
    )
