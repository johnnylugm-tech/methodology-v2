#!/usr/bin/env python3
"""
RISK MANAGEMENT Constitution Checker
===================================
檢查風險管理文檔是否符合 Constitution 原則

Phase 7: 風險管理

原則檢查:
1. 正確性 100% - 風險識別完整、評估合理
2. 安全性 100% - 風險應對措施到位
3. 可維護性 > 70% - 風險記錄追蹤

Usage:
    from risk_management_constitution_checker import check_risk_management_constitution
    result = check_risk_management_constitution("/path/to/docs")
"""

from pathlib import Path
from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS
from typing import Dict, List
from dataclasses import dataclass

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class RiskManagementChecklist:
    """Risk Management 檢查清單"""
    risk_assessment_exists: bool = False
    risk_register_exists: bool = False
    mitigation_plans: bool = False

def check_risk_management_constitution(path: str) -> ConstitutionCheckResult:
    """執行 Risk Management Constitution 檢查"""
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = RiskManagementChecklist()
    
    # 檢查風險評估
    # 使用集中化路徑搜尋 RISK_ASSESSMENT（Phase 7）
    risk_assessments = []
    for artifact_path in PHASE_ARTIFACT_PATHS.get(7, {}).get("RISK_ASSESSMENT.md", []):
        full_path = path_obj.parent / artifact_path
        if full_path.exists():
            risk_assessments.append(full_path)
    checklist.risk_assessment_exists = len(risk_assessments) > 0
    
    # 檢查風險登記表
    # 使用集中化路徑搜尋 RISK_REGISTER（Phase 7）
    risk_registers = []
    for artifact_path in PHASE_ARTIFACT_PATHS.get(7, {}).get("RISK_REGISTER.md", []):
        full_path = path_obj.parent / artifact_path
        if full_path.exists():
            risk_registers.append(full_path)
    checklist.risk_register_exists = len(risk_registers) > 0
    
    # 檢查緩解計劃
    if checklist.risk_assessment_exists:
        try:
            content = risk_assessments[0].read_text(errors="ignore")
            checklist.mitigation_plans = any(m in content for m in ["mitigation", "response", "action"])
        except Exception:
            pass
    
    # 評分
    checks = [
        checklist.risk_assessment_exists,
        checklist.risk_register_exists,
        checklist.mitigation_plans,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    if not checklist.risk_assessment_exists:
        violations.append({
            "type": "missing_risk_assessment",
            "message": "缺少 RISK_ASSESSMENT.md",
            "severity": "HIGH"
        })
    
    if not checklist.risk_register_exists:
        violations.append({
            "type": "missing_risk_register",
            "message": "缺少 RISK_REGISTER.md",
            "severity": "HIGH"
        })
    
    passed = score >= CONSTITUTION_THRESHOLDS["maintainability"]
    
    return ConstitutionCheckResult(
        check_type="risk_management",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "has_assessment": checklist.risk_assessment_exists,
            "has_register": checklist.risk_register_exists,
            "has_mitigation": checklist.mitigation_plans,
        },
        recommendations=recommendations
    )
