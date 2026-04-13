#!/usr/bin/env python3
"""
SRS Constitution Checker
========================
檢查 SRS (Software Requirements Specification) 是否符合 Constitution 原則

原則檢查:
1. 正確性 100% - 功能清單完整、非功能需求明確定義
2. 安全性 100% - 安全性需求完整
3. 可維護性 > 70% - 需求可追蹤、模組化

Usage:
    from srs_constitution_checker import check_srs_constitution
    result = check_srs_constitution("/path/to/docs")
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
class SRSChecklist:
    """SRS 檢查清單"""
    # 正確性檢查
    functional_requirements_complete: bool = False
    non_functional_requirements: bool = False
    interface_specifications: bool = False
    constraints_defined: bool = False
    
    # 安全性檢查
    security_requirements: bool = False
    authentication_defined: bool = False
    authorization_defined: bool = False
    data_protection_defined: bool = False
    
    # 可維護性檢查
    traceability_matrix: bool = False
    requirements_modular: bool = False
    clear_dependencies: bool = False
    
    # 其他
    version_info: bool = False


def _count_requirements(content: str) -> Dict[str, int]:
    """統計需求數量"""
    # 功能需求計數
    functional_matches = re.findall(
        r'(?:FR|功能需求|Functional Requirement)[\s:.-]*(\d+)',
        content, re.IGNORECASE
    )
    
    # 非功能需求計數
    nonfunctional_matches = re.findall(
        r'(?:NFR|Non-Functional Requirement|非功能需求)[\s:.-]*(\d+)',
        content, re.IGNORECASE
    )
    
    return {
        "functional": len(functional_matches) or len(re.findall(r'^\d+\.', content, re.MULTILINE)),
        "non_functional": len(nonfunctional_matches)
    }


def _check_security_requirements(content: str) -> Dict[str, bool]:
    """檢查安全性需求"""
    content_lower = content.lower()
    
    security_keywords = {
        "authentication": ["authentication", "auth", "登入", "登入", "login"],
        "authorization": ["authorization", "authorization", "權限", "permission"],
        "encryption": ["encryption", "encrypt", "加密", "ssl", "tls"],
        "data_protection": ["data protection", "data security", "資料保護", "資安"],
    }
    
    found = {}
    for key, keywords in security_keywords.items():
        found[key] = any(kw in content_lower for kw in keywords)
    
    return found


def _check_maintainability(content: str) -> Dict[str, bool]:
    """檢查可維護性"""
    content_lower = content.lower()
    
    # 可追蹤性
    traceability = any(kw in content_lower for kw in [
        "traceability", "可追溯", "需求追蹤", "requirement id"
    ])
    
    # 模組化
    modular = any(kw in content_lower for kw in [
        "module", "模組", "component", "元件", "subsystem"
    ])
    
    # 依賴關係
    dependencies = any(kw in content_lower for kw in [
        "depends", "依賴", "dependency", "requires"
    ])
    
    return {
        "traceability": traceability,
        "modular": modular,
        "dependencies": dependencies
    }


def check_srs_constitution(docs_path: str) -> ConstitutionCheckResult:
    """檢查 SRS 是否符合 Constitution 原則
    
    Args:
        docs_path: docs 目錄路徑
        
    Returns:
        ConstitutionCheckResult
    """
    docs = load_constitution_documents(docs_path)
    srs_content = docs.get("srs")
    
    if not srs_content:
        return ConstitutionCheckResult(
            check_type="srs",
            passed=False,
            score=0,
            violations=[
                {
                    "principle": "correctness",
                    "type": "missing_document",
                    "message": "SRS document not found",
                    "severity": "CRITICAL"
                }
            ],
            details={"checklist": {}},
            recommendations=[
                "Create SRS.md in docs/ directory",
                "Follow ASPICE SWE.1 template"
            ]
        )
    
    # 執行檢查
    checklist = SRSChecklist()
    violations = []
    recommendations = []
    
    # 1. 正確性檢查
    req_counts = _count_requirements(srs_content)
    
    if req_counts["functional"] >= 5:
        checklist.functional_requirements_complete = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "insufficient_requirements",
            "message": f"Only {req_counts['functional']} functional requirements found, expected >= 5",
            "severity": "HIGH"
        })
        recommendations.append("Add more functional requirements to meet Constitution threshold")
    
    if req_counts["non_functional"] >= 3:
        checklist.non_functional_requirements = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "missing_nfr",
            "message": f"Only {req_counts['non_functional']} non-functional requirements found",
            "severity": "MEDIUM"
        })
    
    # 介面規格檢查
    if any(kw in srs_content.lower() for kw in ["interface", "api", "介面", "規格"]):
        checklist.interface_specifications = True
    else:
        violations.append({
            "principle": "correctness",
            "type": "missing_interfaces",
            "message": "No interface specifications found",
            "severity": "HIGH"
        })
    
    # 約束條件
    if any(kw in srs_content.lower() for kw in ["constraint", "constraint", "約束", "限制"]):
        checklist.constraints_defined = True
    
    # 2. 安全性檢查
    security = _check_security_requirements(srs_content)
    
    checklist.security_requirements = security.get("encryption", False)
    checklist.authentication_defined = security.get("authentication", False)
    checklist.authorization_defined = security.get("authorization", False)
    checklist.data_protection_defined = security.get("data_protection", False)
    
    security_passed = sum([
        checklist.security_requirements,
        checklist.authentication_defined,
        checklist.authorization_defined,
        checklist.data_protection_defined
    ])
    
    if security_passed < 3:
        violations.append({
            "principle": "security",
            "type": "insufficient_security",
            "message": f"Only {security_passed}/4 security aspects defined",
            "severity": "HIGH"
        })
        recommendations.append("Add comprehensive security requirements (authentication, authorization, encryption, data protection)")
    
    # 3. 可維護性檢查
    maintainability = _check_maintainability(srs_content)
    
    checklist.traceability_matrix = maintainability["traceability"]
    checklist.requirements_modular = maintainability["modular"]
    checklist.clear_dependencies = maintainability["dependencies"]
    
    maintainability_passed = sum([
        checklist.traceability_matrix,
        checklist.requirements_modular,
        checklist.clear_dependencies
    ])
    
    if maintainability_passed < 2:
        violations.append({
            "principle": "maintainability",
            "type": "poor_maintainability",
            "message": f"Only {maintainability_passed}/3 maintainability aspects defined",
            "severity": "MEDIUM"
        })
        recommendations.append("Add traceability matrix and define clear module dependencies")
    
    # 版本資訊
    if re.search(r'version|版本|v\d+', srs_content, re.IGNORECASE):
        checklist.version_info = True
    
    # 計算分數
    total_checks = 14
    # Count passed checks (only defined fields)
    passed_checks = sum([
        checklist.functional_requirements_complete,
        checklist.non_functional_requirements,
        checklist.interface_specifications,
        checklist.constraints_defined,
        checklist.security_requirements,
        checklist.authentication_defined,
        checklist.authorization_defined,
        checklist.data_protection_defined,
        checklist.traceability_matrix,
        checklist.requirements_modular,
        checklist.clear_dependencies,
        checklist.version_info,
    ])
    
    score = (passed_checks / total_checks) * 100
    
    # 根據 Constitution 閾值判斷
    passed = (
        len([v for v in violations if v["severity"] == "CRITICAL"]) == 0 and
        score >= CONSTITUTION_THRESHOLDS["maintainability"]
    )
    
    return ConstitutionCheckResult(
        check_type="srs",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "checklist": {
                "functional_requirements": req_counts["functional"],
                "non_functional_requirements": req_counts["non_functional"],
                "security_aspects": security_passed,
                "maintainability_aspects": maintainability_passed,
            }
        },
        recommendations=recommendations
    )


if __name__ == "__main__":
    import json
    result = check_srs_constitution(".")
    print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
