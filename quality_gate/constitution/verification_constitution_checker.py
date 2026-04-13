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
    """執行 Verification Constitution 檢查"""
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = VerificationChecklist()
    
    # 使用集中化路徑搜尋 Phase 5 產出
    project_root = path_obj.parent  # path is typically docs/, go up to project root
    
    # 檢查 TEST_RESULTS.md（Phase 5）- 使用 PHASE_ARTIFACT_PATHS
    test_results_found = False
    for artifact_path in PHASE_ARTIFACT_PATHS.get(5, {}).get("TEST_RESULTS.md", []):
        if (project_root / artifact_path).exists():
            test_results_found = True
            break
    checklist.test_results_documented = test_results_found

    # 檢查 BASELINE.md（Phase 5）- 使用 PHASE_ARTIFACT_PATHS
    baseline_found = False
    for artifact_path in PHASE_ARTIFACT_PATHS.get(5, {}).get("BASELINE.md", []):
        if (project_root / artifact_path).exists():
            baseline_found = True
            break
    checklist.baseline_established = baseline_found
    
    # Security 驗證覆蓋檢查（v7.97: Phase 5 verification security）
    # 檢查 VERIFICATION_REPORT 或 TEST_RESULTS 是否包含安全驗證
    verification_content = ""
    for artifact_path in PHASE_ARTIFACT_PATHS.get(5, {}).get("VERIFICATION_REPORT.md", []):
        vp = project_root / artifact_path
        if vp.exists():
            verification_content = vp.read_text(encoding="utf-8")
            break
    
    test_results_path = None
    for artifact_path in PHASE_ARTIFACT_PATHS.get(5, {}).get("TEST_RESULTS.md", []):
        trp = project_root / artifact_path
        if trp.exists():
            test_results_path = trp
            break
    
    if test_results_path and not verification_content:
        verification_content = test_results_path.read_text(encoding="utf-8")
    
    security_verification_keywords = [
        "安全測試", "security test", "滲透測試", "penetration test",
        "漏洞掃描", "vulnerability scan", "安全掃描",
        "認證驗證", "authentication verification", "auth verification",
        "授權驗證", "authorization verification",
        "加密驗證", "encryption verification", "TLS", "SSL",
    ]
    
    checklist.security_verification = any(
        kw.lower() in verification_content.lower() 
        for kw in security_verification_keywords
    )
    
    # 評分（v7.97: 新增 Security 檢查）
    checks = [
        checklist.test_results_documented,
        checklist.baseline_established,
        checklist.security_verification,  # 新增
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
    
    if not checklist.security_verification:
        violations.append({
            "type": "missing_security_verification",
            "message": "Verification 缺少安全驗證結果（安全測試/漏洞掃描/認證驗證）",
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
