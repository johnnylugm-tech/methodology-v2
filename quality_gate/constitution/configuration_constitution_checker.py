#!/usr/bin/env python3
"""
CONFIGURATION Constitution Checker
=================================
檢查配置管理文檔是否符合 Constitution 原則

Phase 8: 配置管理

原則檢查:
1. 正確性 100% - 配置記錄完整、版本清楚
2. 安全性 100% - 配置變更受控
3. 可維護性 > 70% - 配置可追溯

Usage:
    from configuration_constitution_checker import check_configuration_constitution
    result = check_configuration_constitution("/path/to/docs")
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class ConfigurationChecklist:
    """Configuration 檢查清單"""
    config_records_exists: bool = False
    version_info: bool = False
    change_history: bool = False

def check_configuration_constitution(path: str) -> ConstitutionCheckResult:
    """執行 Configuration Constitution 檢查"""
    path_obj = Path(path)
    
    violations = []
    recommendations = []
    checklist = ConfigurationChecklist()
    
    # 檢查配置記錄
    config_records = list(path_obj.glob("CONFIG_RECORDS*"))
    checklist.config_records_exists = len(config_records) > 0
    
    if checklist.config_records_exists:
        try:
            content = config_records[0].read_text(errors="ignore")
            checklist.version_info = any(v in content for v in ["version", "Version", "v1", "v2"])
            checklist.change_history = any(c in content for c in ["change", "Change", "history", "History"])
        except Exception:
            pass
    
    # 評分
    checks = [
        checklist.config_records_exists,
        checklist.version_info,
        checklist.change_history,
    ]
    score = (sum(checks) / len(checks)) * 100 if checks else 0
    
    if not checklist.config_records_exists:
        violations.append({
            "type": "missing_config_records",
            "message": "缺少 CONFIG_RECORDS.md",
            "severity": "HIGH"
        })
    
    passed = score >= CONSTITUTION_THRESHOLDS["maintainability"]
    
    return ConstitutionCheckResult(
        check_type="configuration",
        passed=passed,
        score=score,
        violations=violations,
        details={
            "has_records": checklist.config_records_exists,
            "has_version": checklist.version_info,
            "has_history": checklist.change_history,
        },
        recommendations=recommendations
    )
