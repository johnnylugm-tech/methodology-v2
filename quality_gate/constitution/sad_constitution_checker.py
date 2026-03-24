#!/usr/bin/env python3
"""
SAD Constitution Checker
==========================
檢查 SAD (Software Architecture Description) 是否符合 Constitution 原則

原則檢查:
1. 正確性 100% - 模組劃分合理、依賴關係清晰
2. 安全性 100% - 安全性設計到位
3. 可維護性 > 70% - 錯誤處理機制完善、模組化設計

Usage:
    from sad_constitution_checker import check_sad_constitution
    result = check_sad_constitution("/path/to/docs")
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from . import (
    CONSTITUTION_THRESHOLDS,
    ERROR_LEVELS,
    ConstitutionCheckResult,
    load_constitution_documents
)


@dataclass
class SADChecklist:
    """SAD 檢查清單"""
    # 正確性檢查
    module_definition: bool = False
    clear_dependencies: bool = False
    interface_definitions: bool = False
    data_flow_defined: bool = False
    
    # 安全性檢查
    security_design: bool = False
    authentication_design: bool = False
    authorization_design: bool = False
    data_protection_design: bool = False
    
    # 可維護性檢查
    error_handling: bool = False
    error_levels_defined: bool = False
    circuit_breaker_defined: bool = False
    modular_design: bool = False
    
    # 其他
    technology_stack: bool = False
    version_info: bool = False


def _count_modules(content: str) -> int:
    """統計模組數量"""
    module_patterns = [
        r'(?:module|Module|模組|元件|component|Component)[\s:.-]*\w+',
        r'^##\s+\w+\s+(?:Module|Component|模組)',
        r'class\s+\w+',
    ]
    
    count = 0
    for pattern in module_patterns:
        count += len(re.findall(pattern, content, re.MULTILINE))
    
    return count


def _check_error_handling(content: str) -> Dict[str, bool]:
    """檢查錯誤處理"""
    content_lower = content.lower()
    
    # 錯誤等級檢查
    error_levels_found = all(
        f"l{i}" in content_lower or f"level {i}" in content_lower
        for i in range(1, 5)
    )
    
    # 熔斷機制
    circuit_breaker = any(kw in content_lower for kw in [
        "circuit breaker", "熔斷", "circuit_breaker", "failover"
    ])
    
    # 錯誤處理策略
    error_handling = any(kw in content_lower for kw in [
        "error handling", "exception", "錯誤處理", "異常處理"
    ])
    
    # 重試機制
    retry = any(kw in content_lower for kw in [
        "retry", "重試", "retry policy"
    ])
    
    return {
        "error_levels": error_levels_found,
        "circuit_breaker": circuit_breaker,
        "error_handling": error_handling,
        "retry": retry
    }


def _check_security_design(content: str) -> Dict[str, bool]:
    """檢查安全性設計"""
    content_lower = content.lower()
    
    security_keywords = {
        "authentication": ["authentication", "auth", "登入", "login"],
        "authorization": ["authorization", "authorization", "權限", "permission", "rbac"],
        "encryption": ["encryption", "encrypt", "加密", "ssl", "tls", "https"],
        "security_architecture": ["security architecture", "安全架構", "零信任"],
    }
    
    found = {}
    for key, keywords in security_keywords.items():
        found[key] = any(kw in content_lower for kw in keywords)
    
    return found


def _check_modular_design(content: str) -> Dict[str, bool]:
    """檢查模組化設計"""
    content_lower = content.lower()
    
    # 單一職責
    single_responsibility = any(kw in content_lower for kw in [
        "single responsibility", "單一職責", "srp"
    ])
    
    # 依賴注入
    dependency_injection = any(kw in content_lower for kw in [
        "dependency injection", "依賴注入", "di"
    ])
    
    # 接口隔離
    interface_segregation = any(kw in content_lower for kw in [
        "interface segregation", "接口隔離"
    ])
    
    return {
        "single_responsibility": single_responsibility,
        "dependency_injection": dependency_injection,
        "interface_segregation": interface_segregation
    }


def check_sad_constitution(docs_path: str) -> ConstitutionCheckResult:
    """檢查 SAD 是否符合 Constitution 原則
    
    Args:
        docs_path: docs 目錄路徑
        
    Returns:
        ConstitutionCheckResult
    """
    docs = load_constitution_documents(docs_path)
    sad_content = docs.get("sad")
    
    if not sad_content:
        return ConstitutionCheckResult(
            check_type="sad",
            passed=False,
            score=0,
            violations=[
                {
                    "principle": "correctness",
                    "type": "missing_document",
                    "message": "SAD document not found",
                    "severity": "CRITICAL"
                }
            ],
            details={"checklist": {}},
            recommendations=[
                "Create SAD.md in docs/ directory",
                "Follow ASPICE SWE.5 template"
            ]
        )
    
    # 執行檢查
    violations = []
    recommendations = []
    checklist = SADChecklist()
    
    # 1. 正確性檢查
    module_count = _count_modules(sad_content)
    
    if module_count >= 3:
        checklist.module_definition = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "insufficient_modules",
            "message": f"Only {module_count} modules found, expected >= 3",
            "severity": "HIGH"
        })
        recommendations.append("Define at least 3 main modules in architecture")
    
    # 依賴關係
    if any(kw in sad_content.lower() for kw in ["depends", "依賴", "dependency", "→"]):
        checklist.clear_dependencies = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "missing_dependencies",
            "message": "No clear dependency relationships found",
            "severity": "HIGH"
        })
    
    # 介面定義
    if any(kw in sad_content.lower() for kw in ["interface", "api", "介面", "contract"]):
        checklist.interface_definitions = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "missing_interfaces",
            "message": "No interface definitions found",
            "severity": "HIGH"
        })
    
    # 資料流
    if any(kw in sad_content.lower() for kw in ["data flow", "資料流", "dataflow", "流程"]):
        checklist.data_flow_defined = True
    
    # 2. 安全性檢查
    security = _check_security_design(sad_content)
    
    checklist.security_design = security.get("security_architecture", False)
    checklist.authentication_design = security.get("authentication", False)
    checklist.authorization_design = security.get("authorization", False)
    checklist.data_protection_design = security.get("encryption", False)
    
    security_passed = sum([
        checklist.security_design,
        checklist.authentication_design,
        checklist.authorization_design,
        checklist.data_protection_design
    ])
    
    if security_passed < 3:
        violations.append({
            "principle": "security",
            "type": "insufficient_security",
            "message": f"Only {security_passed}/4 security design aspects found",
            "severity": "HIGH"
        })
        recommendations.append("Add comprehensive security design (authentication, authorization, encryption)")
    
    # 3. 可維護性檢查 - 錯誤處理
    error_handling = _check_error_handling(sad_content)
    
    checklist.error_handling = error_handling["error_handling"]
    checklist.error_levels_defined = error_handling["error_levels"]
    checklist.circuit_breaker_defined = error_handling["circuit_breaker"]
    
    error_handling_passed = sum([
        checklist.error_handling,
        checklist.error_levels_defined,
        checklist.circuit_breaker_defined
    ])
    
    if error_handling_passed < 2:
        violations.append({
            "principle": "maintainability",
            "type": "poor_error_handling",
            "message": f"Only {error_handling_passed}/3 error handling aspects found",
            "severity": "HIGH"
        })
        recommendations.append("Define error levels (L1-L4) and circuit breaker mechanism")
    
    # 模組化設計
    modular = _check_modular_design(sad_content)
    checklist.modular_design = modular["single_responsibility"]
    
    # 技術堆疊
    if any(kw in sad_content.lower() for kw in ["technology", "技術", "stack", "堆疊"]):
        checklist.technology_stack = True
    
    # 版本資訊
    if re.search(r'version|版本|v\d+', sad_content, re.IGNORECASE):
        checklist.version_info = True
    
    # 計算分數
    total_checks = 14
    passed_checks = sum([
        checklist.module_definition,
        checklist.clear_dependencies,
        checklist.interface_definitions,
        checklist.data_flow_defined,
        checklist.security_design,
        checklist.authentication_design,
        checklist.authorization_design,
        checklist.data_protection_design,
        checklist.error_handling,
        checklist.error_levels_defined,
        checklist.circuit_breaker_defined,
        checklist.modular_design,
        checklist.technology_stack,
        checklist.version_info,
    ])
    
    score = (passed_checks / total_checks) * 100
    
    # 根據 Constitution 閾值判斷
    passed = (
        len([v for v in violations if v["severity"] == "CRITICAL"]) == 0 and
        score >= CONSTITUTION_THRESHOLDS["maintainability"]
    )
    
    return ConstitutionCheckResult(
        check_type="sad",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "checklist": {
                "module_count": module_count,
                "security_aspects": security_passed,
                "error_handling_aspects": error_handling_passed,
            }
        },
        recommendations=recommendations
    )


if __name__ == "__main__":
    import json
    result = check_sad_constitution(".")
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
