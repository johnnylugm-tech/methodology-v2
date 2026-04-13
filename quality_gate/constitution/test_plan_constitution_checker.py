#!/usr/bin/env python3
"""
Test Plan Constitution Checker
=============================
Phase-Aware Constitution Check

Phase-Aware Logic:
- Phase 0-3: TEST_PLAN 不是前置，不需要檢查 → PASS (skipped)
- Phase 4 preflight: TEST_PLAN 不存在是預期的 → PASS (skipped)
- Phase 4 postflight: TEST_PLAN 應該存在 → Check
- Phase 5+: TEST_PLAN 應該存在 → Check
"""

from typing import Dict
from . import ConstitutionCheckResult, load_constitution_documents


def check_test_plan_constitution(docs_path: str, phase: int = 0) -> ConstitutionCheckResult:
    """檢查 Test Plan 是否符合 Constitution 原則
    
    Args:
        docs_path: docs 目錄路徑
        phase: 當前 Phase (用於 Phase-Aware 檢查)
        
    Returns:
        ConstitutionCheckResult
    """
    # Phase-Aware: Phase 1-4 preflight 不需要 TEST_PLAN
    if phase < 4:
        result = ConstitutionCheckResult(
            check_type="test_plan",
            passed=True,
            score=100.0,
            violations=[],
            details={},
            recommendations=[f"TEST_PLAN will be produced by Phase 4"]
        )
        result.message = f"TEST_PLAN is produced by Phase 4, not required as prerequisite for Phase {phase}"
        return result
    
    # Phase 4+ postflight: TEST_PLAN 應該存在
    docs = load_constitution_documents(docs_path)
    test_plan_content = docs.get("test_plan")
    
    if not test_plan_content:
        result = ConstitutionCheckResult(
            check_type="test_plan",
            passed=False,
            score=0,
            violations=[
                {
                    "principle": "testing",
                    "type": "missing_document",
                    "message": "Test Plan document not found",
                    "severity": "CRITICAL"
                }
            ],
            details={"checklist": {}},
            recommendations=["Create TEST_PLAN.md before Phase 4 postflight check"]
        )
        result.message = "Test Plan document not found"
        return result
    
    # 完整的 TEST_PLAN constitution 檢查邏輯（v7.97）
    
    # Security 測試覆蓋檢查
    security_test_keywords = {
        "auth_test": ["認證測試", "authentication test", "login test", "登入測試", "auth_test"],
        "authorization_test": ["授權測試", "authorization test", "permission test", "權限測試"],
        "input_validation_test": ["輸入驗證測試", "validation test", "sanitization test"],
        "security_test": ["安全測試", "security test", "penetration test", "滲透測試"],
        "encryption_test": ["加密測試", "encryption test", "TLS", "SSL", "cipher test"],
    }
    
    # 檢查各項安全測試是否存在於 TEST_PLAN
    security_tests_found = {}
    for test_type, keywords in security_test_keywords.items():
        if any(kw.lower() in test_plan_content.lower() for kw in keywords):
            security_tests_found[test_type] = True
    
    # 評分：基礎檢查 + 安全測試覆蓋
    base_checks = [test_plan_content is not None]  # TEST_PLAN 存在
    security_checks = list(security_tests_found.values())
    all_checks = base_checks + security_checks
    
    score = (sum(all_checks) / len(all_checks)) * 100 if all_checks else 0
    passed = score >= 80  # Threshold
    
    # 違規
    if not security_tests_found.get("auth_test"):
        violations.append({
            "principle": "security",
            "type": "missing_auth_test",
            "message": "TEST_PLAN 缺少認證測試",
            "severity": "HIGH"
        })
        recommendations.append("Add authentication test cases")
    
    if not security_tests_found.get("security_test"):
        violations.append({
            "principle": "security",
            "type": "missing_security_test",
            "message": "TEST_PLAN 缺少安全測試",
            "severity": "HIGH"
        })
        recommendations.append("Add security test cases (penetration testing, etc.)")
    
    return ConstitutionCheckResult(
        check_type="test_plan",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "security_tests_found": security_tests_found,
            "has_test_plan": test_plan_content is not None,
        },
        recommendations=recommendations
    )
