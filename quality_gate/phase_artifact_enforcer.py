"""
Phase Artifact Enforcer - Phase 產物強制執行
=============================================

確保每個 Phase 的產物都存在且正確。
"""

import os
from typing import Dict, List


class PhaseDependency:
    """Phase 依賴關係定義"""

    def __init__(self, phase: str, requires: List[str], artifact_path: str):
        self.phase = phase
        self.requires = requires
        self.artifact_path = artifact_path


class PhaseArtifactEnforcer:
    """Phase 產物執行器"""

    # Phase 目錄及其所需的前置 Phase
    PHASE_DEFINITIONS = {
        "phase_0": {
            "dir": "00-constitution",
            "requires": [],
            "artifact": "CONSTITUTION.md",
        },
        "phase_1": {
            "dir": "01-specify",
            "requires": ["phase_0"],
            "artifact": "requirements.md",
        },
        "phase_2": {
            "dir": "02-plan",
            "requires": ["phase_1"],
            "artifact": "architecture.md",
        },
        "phase_3": {
            "dir": "03-build",
            "requires": ["phase_2"],
            "artifact": "implementation.md",
        },
        "phase_4": {
            "dir": "04-verify",
            "requires": ["phase_3"],
            "artifact": "test_results.md",
        },
    }

    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def _get_existing_phases(self) -> List[str]:
        """獲取所有已存在的 Phase"""
        existing = []
        for phase, info in self.PHASE_DEFINITIONS.items():
            phase_dir = os.path.join(self.project_root, info["dir"])
            if os.path.exists(phase_dir):
                existing.append(phase)
        return existing

    def _check_phase_prerequisites(self, phase: str, existing_phases: List[str]) -> bool:
        """檢查 Phase 的前置條件是否滿足"""
        info = self.PHASE_DEFINITIONS.get(phase, {})
        requires = info.get("requires", [])

        for req in requires:
            if req not in existing_phases:
                return False
        return True

    def enforce_phase(self, phase: str) -> Dict:
        """檢查單個 Phase 的產物"""
        info = self.PHASE_DEFINITIONS.get(phase, {})
        phase_dir = os.path.join(self.project_root, info.get("dir", ""))
        artifact = info.get("artifact", "")

        exists = os.path.exists(phase_dir)
        artifact_path = os.path.join(phase_dir, artifact) if exists else None
        artifact_exists = os.path.exists(artifact_path) if artifact_path else False

        existing_phases = self._get_existing_phases()
        prerequisites_met = self._check_phase_prerequisites(phase, existing_phases)

        passed = exists and artifact_exists and prerequisites_met

        return {
            "phase": phase,
            "dir": phase_dir,
            "exists": exists,
            "artifact_exists": artifact_exists,
            "prerequisites_met": prerequisites_met,
            "passed": passed,
        }

    def enforce_all(self) -> Dict:
        """執行所有 Phase 產物檢查"""
        results = {}

        for phase in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"]:
            result = self.enforce_phase(phase)
            results[phase] = result

        # 只有連續的 Phase 鏈才能算通過
        # 必須從 phase_0 開始，且每個 Phase 都必須有前置條件
        all_passed = all(r["passed"] for r in results.values())

        return {
            "passed": all_passed,
            "results": results,
        }