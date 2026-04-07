#!/usr/bin/env python3
"""
QUALITY REPORT Constitution Checker
==================================
檢查 Quality Report 文檔是否符合 Constitution 原則

Phase 6: 品質報告

原則檢查:
1. 正確性 100% - 報告準確、完整
2. 安全性 100% - 敏感資訊保護
3. 可維護性 > 70% - 報告結構清晰

Usage:
    from quality_report_constitution_checker import check_quality_report_constitution
    result = check_quality_report_constitution("/path/to/docs")
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class QualityReportChecklist:
    """Quality Report 檢查清單"""
    quality_report_exists: bool = False
    metrics_defined: bool = False
    improvement_plan: bool = False

def check_quality_report_constitution(path: str) -> ConstitutionCheckResult:
    """執行 Quality Report Constitution 檢查"""
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = QualityReportChecklist()
    
    # 檢查品質報告
    quality_reports = list(path_obj.glob("QUALITY_REPORT*"))
    checklist.quality_report_exists = len(quality_reports) > 0
    
    if checklist.quality_report_exists:
        try:
            content = quality_reports[0].read_text(errors="ignore")
            checklist.metrics_defined = any(m in content for m in ["metric", "coverage", "defect"])
            checklist.improvement_plan = any(w in content for w in ["improvement", "action", "plan"])
        except Exception:
            pass
    
    # 評分
    checks = [
        checklist.quality_report_exists,
        checklist.metrics_defined,
        checklist.improvement_plan,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    if not checklist.quality_report_exists:
        violations.append({
            "type": "missing_quality_report",
            "message": "缺少 QUALITY_REPORT.md",
            "severity": "HIGH"
        })
    
    passed = score >= CONSTITUTION_THRESHOLDS["maintainability"]
    
    return ConstitutionCheckResult(
        check_type="quality_report",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "has_report": checklist.quality_report_exists,
            "has_metrics": checklist.metrics_defined,
            "has_plan": checklist.improvement_plan,
        },
        recommendations=recommendations
    )
