#!/usr/bin/env python3
"""
Test Plan Constitution Checker
===============================
檢查 Test Plan 是否符合 Constitution 原則

原則檢查:
1. 測試金字塔 - Unit 70%, Integration 20%, E2E 10%
2. 覆蓋率 > 80%
3. 關鍵路徑覆蓋

Usage:
    from test_plan_constitution_checker import check_test_plan_constitution
    result = check_test_plan_constitution("/path/to/docs")
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult,
    load_constitution_documents
)


@dataclass
class TestPlanChecklist:
    """Test Plan 檢查清單"""
    # 測試金字塔
    unit_tests_defined: bool = False
    integration_tests_defined: bool = False
    e2e_tests_defined: bool = False
    
    # 覆蓋率
    coverage_threshold_defined: bool = False
    coverage_target_met: bool = False
    branch_coverage_defined: bool = False
    
    # 測試策略
    test_strategy_defined: bool = False
    test_scope_defined: bool = False
    test_environments_defined: bool = False
    
    # 關鍵路徑
    critical_path_coverage: bool = False
    regression_tests_defined: bool = False
    smoke_tests_defined: bool = False
    
    # 其他
    test_prioritization: bool = False
    version_info: bool = False


# 測試金字塔理想比例
TEST_PYRAMID = {
    "unit": 70,
    "integration": 20,
    "e2e": 10
}


def _analyze_test_pyramid(content: str) -> Dict[str, bool]:
    """分析測試金字塔"""
    content_lower = content.lower()
    
    # 查找測試類型
    unit_keywords = ["unit test", "單元測試", "component test"]
    integration_keywords = ["integration test", "整合測試", "integration test"]
    e2e_keywords = ["e2e test", "end-to-end", "端到端", "e2e"]
    
    unit_found = any(kw in content_lower for kw in unit_keywords)
    integration_found = any(kw in content_lower for kw in integration_keywords)
    e2e_found = any(kw in content_lower for kw in e2e_keywords)
    
    # 檢查比例描述
    pyramid_described = any(kw in content_lower for kw in [
        "test pyramid", "測試金字塔", "70%", "20%", "10%"
    ])
    
    return {
        "unit": unit_found,
        "integration": integration_found,
        "e2e": e2e_found,
        "pyramid_described": pyramid_described
    }


def _check_coverage_requirements(content: str) -> Dict[str, bool]:
    """檢查覆蓋率要求"""
    content_lower = content.lower()
    
    # 覆蓋率閾值
    coverage_threshold = any(kw in content_lower for kw in [
        "coverage", "覆蓋率", "80%"
    ])
    
    # 目標覆蓋率
    coverage_target = re.search(r'(\d+)%', content)
    coverage_target_met = False
    if coverage_target:
        coverage_value = int(coverage_target.group(1))
        coverage_target_met = coverage_value >= 80
    
    # 分支覆蓋率
    branch_coverage = any(kw in content_lower for kw in [
        "branch coverage", "分支覆蓋", "decision coverage"
    ])
    
    # 路徑覆蓋
    path_coverage = any(kw in content_lower for kw in [
        "path coverage", "路徑覆蓋"
    ])
    
    return {
        "coverage_threshold": coverage_threshold,
        "coverage_target_met": coverage_target_met,
        "branch_coverage": branch_coverage,
        "path_coverage": path_coverage
    }


def _check_test_strategy(content: str) -> Dict[str, bool]:
    """檢查測試策略"""
    content_lower = content.lower()
    
    # 測試策略
    strategy = any(kw in content_lower for kw in [
        "test strategy", "測試策略", "testing strategy"
    ])
    
    # 測試範圍
    scope = any(kw in content_lower for kw in [
        "test scope", "測試範圍", "scope"
    ])
    
    # 測試環境
    environment = any(kw in content_lower for kw in [
        "test environment", "測試環境", "staging", "qa"
    ])
    
    # 測試資料
    test_data = any(kw in content_lower for kw in [
        "test data", "測試資料", "fixture", "mock"
    ])
    
    return {
        "strategy": strategy,
        "scope": scope,
        "environment": environment,
        "test_data": test_data
    }


def _check_critical_path(content: str) -> Dict[str, bool]:
    """檢查關鍵路徑"""
    content_lower = content.lower()
    
    # 關鍵路徑覆蓋
    critical_path = any(kw in content_lower for kw in [
        "critical path", "關鍵路徑", "核心功能", "key functionality"
    ])
    
    # 回歸測試
    regression = any(kw in content_lower for kw in [
        "regression", "回歸測試"
    ])
    
    # 冒煙測試
    smoke = any(kw in content_lower for kw in [
        "smoke test", "冒煙測試", "sanity test"
    ])
    
    # 效能測試
    performance = any(kw in content_lower for kw in [
        "performance test", "效能測試", "load test", "壓測"
    ])
    
    # 安全測試
    security = any(kw in content_lower for kw in [
        "security test", "安全測試", "penetration"
    ])
    
    return {
        "critical_path": critical_path,
        "regression": regression,
        "smoke": smoke,
        "performance": performance,
        "security": security
    }


def check_test_plan_constitution(docs_path: str) -> ConstitutionCheckResult:
    """檢查 Test Plan 是否符合 Constitution 原則
    
    Args:
        docs_path: docs 目錄路徑
        
    Returns:
        ConstitutionCheckResult
    """
    docs = load_constitution_documents(docs_path)
    test_plan_content = docs.get("test_plan")
    
    if not test_plan_content:
        return ConstitutionCheckResult(
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
            recommendations=[
                "Create TEST_PLAN.md in docs/ directory",
                "Follow ASPICE SWE.7 template",
                "Define test pyramid strategy"
            ]
        )
    
    # 執行檢查
    violations = []
    recommendations = []
    checklist = TestPlanChecklist()
    
    # 1. 測試金字塔
    pyramid = _analyze_test_pyramid(test_plan_content)
    
    checklist.unit_tests_defined = pyramid["unit"]
    checklist.integration_tests_defined = pyramid["integration"]
    checklist.e2e_tests_defined = pyramid["e2e"]
    
    pyramid_passed = sum([
        checklist.unit_tests_defined,
        checklist.integration_tests_defined,
        checklist.e2e_tests_defined
    ])
    
    if pyramid_passed < 2:
        violations.append({
            "principle": "testing",
            "type": "incomplete_pyramid",
            "message": f"Only {pyramid_passed}/3 test types defined",
            "severity": "HIGH"
        })
        recommendations.append("Define all three test levels: Unit, Integration, E2E")
    
    if not pyramid["pyramid_described"]:
        violations.append({
            "principle": "testing",
            "type": "missing_pyramid_description",
            "message": "Test pyramid ratios not described",
            "severity": "MEDIUM"
        })
    
    # 2. 覆蓋率
    coverage = _check_coverage_requirements(test_plan_content)
    
    checklist.coverage_threshold_defined = coverage["coverage_threshold"]
    checklist.coverage_target_met = coverage["coverage_target_met"]
    checklist.branch_coverage_defined = coverage["branch_coverage"]
    
    coverage_passed = sum([
        checklist.coverage_threshold_defined,
        checklist.branch_coverage_defined
    ])
    
    if coverage_passed < 1:
        violations.append({
            "principle": "coverage",
            "type": "missing_coverage_threshold",
            "message": "No coverage threshold defined",
            "severity": "HIGH"
        })
        recommendations.append("Define coverage threshold >= 80%")
    
    if not coverage["coverage_target_met"]:
        violations.append({
            "principle": "coverage",
            "type": "coverage_below_threshold",
            "message": "Coverage target not meeting 80% threshold",
            "severity": "HIGH"
        })
    
    # 3. 測試策略
    strategy = _check_test_strategy(test_plan_content)
    
    checklist.test_strategy_defined = strategy["strategy"]
    checklist.test_scope_defined = strategy["scope"]
    checklist.test_environments_defined = strategy["environment"]
    
    # 4. 關鍵路徑
    critical = _check_critical_path(test_plan_content)
    
    checklist.critical_path_coverage = critical["critical_path"]
    checklist.regression_tests_defined = critical["regression"]
    checklist.smoke_tests_defined = critical["smoke"]
    
    critical_passed = sum([
        checklist.critical_path_coverage,
        checklist.regression_tests_defined,
        checklist.smoke_tests_defined
    ])
    
    if critical_passed < 2:
        violations.append({
            "principle": "testing",
            "type": "insufficient_critical_path",
            "message": f"Only {critical_passed}/3 critical path aspects defined",
            "severity": "MEDIUM"
        })
        recommendations.append("Define critical path coverage, regression tests, and smoke tests")
    
    # 測試優先順序
    if any(kw in test_plan_content.lower() for kw in [
        "priority", "優先順序", "prioritization", "test case priority"
    ]):
        checklist.test_prioritization = True
    
    # 版本資訊
    if re.search(r'version|版本|v\d+', test_plan_content, re.IGNORECASE):
        checklist.version_info = True
    
    # 計算分數
    total_checks = 14
    passed_checks = sum([
        checklist.unit_tests_defined,
        checklist.integration_tests_defined,
        checklist.e2e_tests_defined,
        checklist.coverage_threshold_defined,
        checklist.coverage_target_met,
        checklist.branch_coverage_defined,
        checklist.test_strategy_defined,
        checklist.test_scope_defined,
        checklist.test_environments_defined,
        checklist.critical_path_coverage,
        checklist.regression_tests_defined,
        checklist.smoke_tests_defined,
        checklist.test_prioritization,
        checklist.version_info,
    ])
    
    score = (passed_checks / total_checks) * 100
    
    # 根據 Constitution 閾值判斷 (覆蓋率 > 80%)
    passed = (
        len([v for v in violations if v["severity"] == "CRITICAL"]) == 0 and
        score >= CONSTITUTION_THRESHOLDS["coverage"]
    )
    
    return ConstitutionCheckResult(
        check_type="test_plan",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "checklist": {
                "pyramid_levels": pyramid_passed,
                "coverage_defined": coverage_passed,
                "critical_path_aspects": critical_passed,
            }
        },
        recommendations=recommendations
    )


if __name__ == "__main__":
    import json
    result = check_test_plan_constitution(".")
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
