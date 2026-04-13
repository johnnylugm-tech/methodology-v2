#!/usr/bin/env python3
"""
Phase Prerequisite Checker
==========================
每個 Phase 往前檢查，確保前一階段的產出已 Ready

Logic:
- Phase N Constitution 檢查 Phase (N-1) 的產出
- 不是檢查 Phase N 自己的產出

IMPORTANT: Phase 5 artifacts are in 05-verify/ (Phase5_Plan WHERE)
           Phase 6 needs to check both 05-baseline/ and 05-verify/
"""

from pathlib import Path
from typing import Dict, List, Tuple, Union
from quality_gate.phase_paths import PHASE_ARTIFACT_PATHS
from typing import Dict, List, Tuple

# Phase N 需要的前置產出（ASPICE 目錄結構）
# Phase 6 includes Phase 5 outputs at both 05-baseline/ (old) and 05-verify/ (Phase5_Plan)
PHASE_PREREQUISITES = {
    1: [],  # 基本前提（由 FSM 檢查）
    2: ["SRS.md", "01-requirements/SRS.md"],
    3: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json"],
    4: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json", ".methodology/SAB.json"],
    5: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json", ".methodology/SAB.json", "04-testing/TEST_PLAN.md"],
    6: [
        # Phase 6 needs Phase 5 outputs
        # Check both old location (05-baseline/) and Phase5_Plan location (05-verify/)
        "SRS.md",
        "01-requirements/SRS.md",
        "02-architecture/SAD.md",
        ".methodology/SAB.json",
        # Phase 5 outputs - check both locations
        ("05-verify/BASELINE.md", "05-verify/BASELINE.md"),  # BASELINE.md alternate paths
        ("04-testing/TEST_RESULTS.md", "05-verify/TEST_RESULTS.md"),  # TEST_RESULTS alternate paths
    ],
    7: ["06-quality/QUALITY_REPORT.md"],
    8: ["08-config/CONFIG_RECORDS.md", "08-config/requirements.lock"],
}


def check_phase_prerequisites(phase: int, project_path: Path) -> Tuple[bool, List, List]:
    """
    檢查 Phase N 的前置產出是否 Ready
    
    Supports alternate paths for Phase 5 artifacts:
    - BASELINE.md: 05-baseline/ OR 05-verify/
    - TEST_RESULTS.md: 04-testing/ OR 05-verify/
    
    Returns: (passed: bool, missing: list, ready: list)
    """
    prereqs = PHASE_PREREQUISITES.get(phase, [])
    missing = []
    ready = []
    
    for item in prereqs:
        if isinstance(item, tuple):
            # Alternate paths - check any one exists
            found = False
            found_path = None
            for alt_path in item:
                path = project_path / alt_path
                if path.exists():
                    found = True
                    found_path = alt_path
                    break
            
            if found:
                ready.append(found_path)  # Record the actual path found
            else:
                missing.append(item[0])  # Record the primary path as missing
        elif item.endswith("/"):
            # 目錄檢查
            path = project_path / item
            if path.exists() and any(path.iterdir()):
                ready.append(item)
            else:
                missing.append(item)
        else:
            # 檔案檢查
            path = project_path / item
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


# Direct export for convenience
check_prerequisites = check_phase_prerequisites