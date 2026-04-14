#!/usr/bin/env python3
"""
CONFIGURATION MANAGEMENT Constitution Checker
=============================================
檢查配置管理文檔是否符合 Constitution 原則

Phase 8: 配置管理

原則檢查:
1. 正確性 100% - 配置記錄完整、版本正確
2. 安全性 100% - 配置變更可追溯
3. 可維護性 > 70% - 配置文檔清晰

Usage:
    from configuration_constitution_checker import check_configuration_constitution
    result = check_configuration_constitution("/path/to/docs")
"""

from pathlib import Path
from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS, check_artifact_exists
from typing import Dict, List
from dataclasses import dataclass

from . import (
    CONSTITUTION_THRESHOLDS,
    ConstitutionCheckResult
)

@dataclass
class ConfigurationChecklist:
    """Configuration Management 檢查清單"""
    config_records_exists: bool = False
    baseline_exists: bool = False
    git_tag_exists: bool = False
    release_notes_exists: bool = False


def check_configuration_constitution(path: str) -> ConstitutionCheckResult:
    """執行 Configuration Management Constitution 檢查"""
    path_obj = Path(path)

    violations = []
    recommendations = []
    checklist = ConfigurationChecklist()

    # 檢查配置記錄表
    # 使用集中化路徑搜尋 CONFIG_RECORDS（Phase 8）
    # CONFIG_RECORDS.md - Phase8_Plan WHERE: 08-config/
    config_path = path_obj.parent / "08-config/CONFIG_RECORDS.md"
    config_records = [config_path] if config_path.exists() else []
    checklist.config_records_exists = len(config_records) > 0
    if not checklist.config_records_exists:
        violations.append("CONFIG_RECORDS.md 不存在")

    # 檢查基準線文件
    # 使用集中化路徑搜尋 BASELINE（Phase 5）
    # BASELINE.md - Phase5_Plan WHERE: 05-verify/
    baseline_path = path_obj.parent / "05-verify/BASELINE.md"
    baselines = [baseline_path] if baseline_path.exists() else []
    checklist.baseline_exists = len(baselines) > 0
    if not checklist.baseline_exists:
        violations.append("BASELINE.md 不存在")

    # 檢查 Git Tag 記錄
    git_tags = list(path_obj.glob(".git_tag_record")) + list(path_obj.glob("GIT_TAG*"))
    checklist.git_tag_exists = len(git_tags) > 0

    # 檢查發布說明
    release_notes = list(path_obj.glob("RELEASE_NOTES*")) + list(path_obj.glob("CHANGELOG*"))
    checklist.release_notes_exists = len(release_notes) > 0

    # 計算分數
    total_checks = 5
    passed_checks = sum([
        checklist.config_records_exists,
        checklist.baseline_exists,
        checklist.git_tag_exists,
        checklist.release_notes_exists,
    ])
    score = passed_checks / total_checks * 100

    # 給出建議
    if not checklist.git_tag_exists:
        recommendations.append("建議記錄 Git Tag 歷史用於追溯")

    if not checklist.release_notes_exists:
        recommendations.append("建議包含 CHANGELOG.md 或 RELEASE_NOTES.md")

    if score < 100:
        violations.append(f"配置完整性 {score:.0f}% < 100%")

    return ConstitutionCheckResult(
        check_type="configuration",
        passed=score >= 60,
        score=score,
        violations=violations,
        details={"checklist": checklist.__dict__},
        recommendations=recommendations,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = check_configuration_constitution(sys.argv[1])
        print(f"Phase 8 Configuration Constitution Check")
        print(f"Score: {result.score:.0f}%")
        print(f"Violations: {result.violations}")
        print(f"Recommendations: {result.recommendations}")
