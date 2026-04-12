#!/usr/bin/env python3
"""
Phase Prerequisite Checker
==========================
每個 Phase 往前檢查，確保前一階段的產出已 Ready

Logic:
- Phase N Constitution 檢查 Phase (N-1) 的產出
- 不是檢查 Phase N 自己的產出
"""

from pathlib import Path
from typing import Dict, List

# Phase N 需要的前置產出（ASPICE 目錄結構）
PHASE_PREREQUISITES = {
    1: [],  # 基本前提（由 FSM 檢查）
    2: ["SRS.md", "01-requirements/SRS.md"],
    3: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json"],
    4: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json", ".methodology/SAB.json"],
    5: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json", "04-testing/TEST_PLAN.md"],
    6: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", "04-testing/TEST_PLAN.md", "05-baseline/BASELINE.md"],
    7: ["06-reports/QUALITY_REPORT.md"],
    8: ["07-deployment/CONFIG_RECORDS.md", "07-deployment/requirements.lock"],
}

def check_phase_prerequisites(phase: int, project_path: Path) -> tuple:
    """
    檢查 Phase N 的前置產出是否 Ready
    
    Returns: (passed: bool, missing: list, ready: list)
    """
    prereqs = PHASE_PREREQUISITES.get(phase, [])
    missing = []
    ready = []
    
    for item in prereqs:
        path = project_path / item
        if item.endswith("/"):
            # 目錄檢查
            if path.exists() and any(path.iterdir()):
                ready.append(item)
            else:
                missing.append(item)
        else:
            # 檔案檢查
            if path.exists():
                ready.append(item)
            else:
                missing.append(item)
    
    return len(missing) == 0, missing, ready


def format_prerequisite_error(phase: int, missing: list, ready: list) -> str:
    """格式化前置條件檢查失敗的錯誤訊息"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"❌ Phase {phase} 前置條件檢查失敗")
    lines.append("=" * 70)
    
    if ready:
        lines.append(f"\n✅ 已就緒 ({len(ready)}):")
        for item in ready:
            lines.append(f"   ✓ {item}")
    
    if missing:
        lines.append(f"\n❌ 缺失 ({len(missing)}):")
        for item in missing:
            lines.append(f"   ✗ {item}")
    
    lines.append(f"\n💡 提示: 這些檔案應該由 Phase {phase-1} 或更早的階段產生")
    lines.append("=" * 70)
    
    return "\n".join(lines)
