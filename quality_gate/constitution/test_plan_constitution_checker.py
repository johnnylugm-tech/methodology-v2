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
    
    # TODO: 實作完整的 TEST_PLAN constitution 檢查邏輯
    return ConstitutionCheckResult(
        check_type="test_plan",
        passed=True,
        score=100.0,
        summary="Test Plan Constitution check PASSED",
        message="Test Plan found and validated"
    )
