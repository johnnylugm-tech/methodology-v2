"""
Document Checker - 文檔完整性檢查
=================================

檢查所有必要文檔是否存在、格式是否正確。
支持 Phase-based 檢查模式。
"""

import os
import re
from typing import Dict, List


class DocumentRequirement:
    """文檔需求定義"""

    def __init__(self, name: str, patterns: List[str], phase: str):
        self.name = name
        self.patterns = patterns
        self.phase = phase


class DocumentChecker:
    """文檔檢查器"""

    # Phase 1: 需求文檔
    SRS_PATTERN = r"SRS.*\.md"
    # Phase 2: 架構文檔
    SAD_PATTERN = r"SAD.*\.md"
    # Phase 3: 測試相關文檔
    TEST_PLAN_PATTERN = r"TEST_PLAN.*\.md"

    # 按 Phase 分組的文檔需求
    PHASE_REQUIREMENTS = {
        "phase_1": [
            DocumentRequirement("SRS", [SRS_PATTERN], "phase_1"),
        ],
        "phase_2": [
            DocumentRequirement("SAD", [SAD_PATTERN], "phase_2"),
        ],
        "phase_3": [
            DocumentRequirement("Architecture", [SAD_PATTERN], "phase_3"),
        ],
        "phase_4": [
            DocumentRequirement("TestPlan", [TEST_PLAN_PATTERN], "phase_4"),
        ],
    }

    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def _matches_pattern(self, filename: str, patterns: List[str]) -> bool:
        """檢查文件名是否匹配任一模式"""
        for pattern in patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
        return False

    def _find_matching_docs(self, patterns: List[str]) -> List[str]:
        """找出所有匹配模式的文檔"""
        matches = []
        if not os.path.exists(self.project_root):
            return matches

        for entry in os.listdir(self.project_root):
            if os.path.isfile(entry):
                if self._matches_pattern(entry, patterns):
                    matches.append(entry)

        # 也檢查子目錄
        for root, dirs, files in os.walk(self.project_root):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.project_root)
                if self._matches_pattern(rel_path, patterns):
                    matches.append(rel_path)

        return matches

    def check_phase(self, phase: str) -> Dict:
        """檢查單個 Phase 的文檔"""
        requirements = self.PHASE_REQUIREMENTS.get(phase, [])
        missing = []
        found = []

        for req in requirements:
            docs = self._find_matching_docs(req.patterns)
            if docs:
                found.append({"requirement": req.name, "files": docs})
            else:
                missing.append(req.name)

        passed = len(missing) == 0

        return {
            "phase": phase,
            "passed": passed,
            "missing": missing,
            "found": found,
        }

    def check_all(self) -> Dict:
        """執行所有文檔檢查"""
        results = {}
        all_missing = []

        for phase in ["phase_1", "phase_2", "phase_3", "phase_4"]:
            result = self.check_phase(phase)
            results[phase] = result
            all_missing.extend(result.get("missing", []))

        all_passed = all(r["passed"] for r in results.values())

        # 構建 summary
        if all_passed:
            summary = "all_present"
        elif all_missing:
            summary = "missing:" + ",".join(all_missing)
        else:
            summary = "partial"

        return {
            "passed": all_passed,
            "results": results,
            "summary": summary,
        }