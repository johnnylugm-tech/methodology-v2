#!/usr/bin/env python3
"""
Phase-Aware Constitution System
================================
Phase N 的 Constitution 分為 Pre-flight 和 Post-flight

| 時機 | 檢查什麼 | 目的 |
|------|----------|------|
| Pre-flight | Phase (N-1) 的產出是否 Ready | 確保可以開始 Phase N |
| Post-flight | Phase N 的產出是否完成 | 確保 Phase N 完成 |
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# Phase N 的前置產出（Pre-flight 檢查）
PHASE_PREREQUISITES = {
    1: [],  # 基本環境
    2: ["SRS.md", "01-requirements/SRS.md"],
    3: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json"],
    4: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/fr_mapping.json", ".methodology/SAB.json"],
    5: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/SAB.json", "04-testing/TEST_PLAN.md", "05-verify/BASELINE.md", "05-verify/TEST_RESULTS.md"],
    6: ["SRS.md", "01-requirements/SRS.md", "02-architecture/SAD.md", ".methodology/SAB.json", "04-testing/TEST_PLAN.md", "05-baseline/BASELINE.md"],
    7: ["06-reports/QUALITY_REPORT.md"],
    8: ["07-deployment/CONFIG_RECORDS.md", "07-deployment/requirements.lock"],
}

# Phase N 的 Essential Deliverables（Post-flight 檢查）
# 不包含 Audit Documents（sessions_spawn.log, state.json, SPEC_TRACKING.md）
PHASE_OUTPUTS = {
    1: ["SRS.md", "01-requirements/SRS.md"],  # 需求規格
    2: ["SAD.md", "02-architecture/SAD.md"],  # 架構設計
    3: [".methodology/fr_mapping.json"],      # FR→Code 映射
    4: ["04-testing/TEST_PLAN.md"],           # 測試計畫（主要產物）
    5: ["05-verify/BASELINE.md"],          # 基準線
    6: ["05-verify/QUALITY_REPORT.md"],      # 品質報告
    7: ["07-deployment/CONFIG_RECORDS.md", "07-deployment/requirements.lock"],  # 配置記錄
    8: [],  # Phase 8 是最後階段
}


@dataclass
class PhaseConstitutionResult:
    """Phase Constitution 檢查結果"""
    phase: int
    mode: str  # "preflight" or "postflight"
    passed: bool
    score: float
    ready: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    produced: List[str] = field(default_factory=list)
    missing_outputs: List[str] = field(default_factory=list)
    violations: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"Phase {self.phase} [{self.mode}]: {status} ({self.score:.0f}%)"


def check_phase_prerequisites(phase: int, project_path: Path) -> Tuple[bool, List[str], List[str]]:
    """Pre-flight: 檢查 Phase N 的前置產出是否 Ready"""
    prereqs = PHASE_PREREQUISITES.get(phase, [])
    ready = []
    missing = []
    
    for item in prereqs:
        path = project_path / item
        if path.exists():
            ready.append(item)
        else:
            missing.append(item)
    
    return len(missing) == 0, ready, missing


def check_phase_outputs(phase: int, project_path: Path) -> Tuple[bool, List[str], List[str]]:
    """Post-flight: 檢查 Phase N 的產出是否完成"""
    outputs = PHASE_OUTPUTS.get(phase, [])
    produced = []
    missing = []
    
    for item in outputs:
        path = project_path / item
        if path.exists():
            produced.append(item)
        else:
            missing.append(item)
    
    return len(missing) == 0, produced, missing


def run_phase_constitution(phase: int, mode: str, project_path: Path) -> PhaseConstitutionResult:
    """
    執行 Phase Constitution 檢查
    
    Args:
        phase: Phase 編號 (1-8)
        mode: "preflight" | "postflight" | "full"
        project_path: 專案根目錄
    
    Returns:
        PhaseConstitutionResult
    """
    if mode == "preflight":
        # Pre-flight: 只檢查前置產出
        passed, ready, missing = check_phase_prerequisites(phase, project_path)
        score = (len(ready) / (len(ready) + len(missing) + 1)) * 100 if missing else 100
        
        violations = []
        if missing:
            violations.append({
                "principle": "prerequisite",
                "type": "missing_artifacts",
                "message": f"Phase {phase} prerequisite check failed",
                "severity": "CRITICAL",
                "details": missing
            })
        
        return PhaseConstitutionResult(
            phase=phase,
            mode=mode,
            passed=passed,
            score=score,
            ready=ready,
            missing=missing,
            violations=violations,
            recommendations=[
                f"Complete Phase {phase - 1} before starting Phase {phase}"
            ] if missing else []
        )
    
    elif mode == "postflight":
        # Post-flight: 只檢查產出
        passed, produced, missing = check_phase_outputs(phase, project_path)
        score = (len(produced) / (len(produced) + len(missing) + 1)) * 100 if missing else 100
        
        violations = []
        if missing:
            violations.append({
                "principle": "output",
                "type": "missing_outputs",
                "message": f"Phase {phase} output check failed",
                "severity": "CRITICAL",
                "details": missing
            })
        
        return PhaseConstitutionResult(
            phase=phase,
            mode=mode,
            passed=passed,
            score=score,
            produced=produced,
            missing_outputs=missing,
            violations=violations,
            recommendations=[
                f"Complete Phase {phase} before proceeding"
            ] if missing else []
        )
    
    else:  # "full"
        # Full: Pre-flight + Post-flight
        pre_result = run_phase_constitution(phase, "preflight", project_path)
        post_result = run_phase_constitution(phase, "postflight", project_path)
        
        # 加權分數: Pre-flight 30%, Post-flight 70%
        combined_score = pre_result.score * 0.3 + post_result.score * 0.7
        all_violations = pre_result.violations + post_result.violations
        all_recommendations = pre_result.recommendations + post_result.recommendations
        
        return PhaseConstitutionResult(
            phase=phase,
            mode=mode,
            passed=pre_result.passed and post_result.passed,
            score=combined_score,
            ready=pre_result.ready,
            missing=pre_result.missing,
            produced=post_result.produced,
            missing_outputs=post_result.missing_outputs,
            violations=all_violations,
            recommendations=all_recommendations
        )


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 4:
        print("Usage: phase_aware_constitution.py <phase> <mode> <project_path>")
        print("  mode: preflight | postflight | full")
        sys.exit(1)
    
    phase = int(sys.argv[1])
    mode = sys.argv[2]
    project_path = Path(sys.argv[3])
    
    result = run_phase_constitution(phase, mode, project_path)
    print(json.dumps({
        "phase": result.phase,
        "mode": result.mode,
        "passed": result.passed,
        "score": result.score,
        "ready": result.ready,
        "missing": result.missing,
        "produced": result.produced,
        "missing_outputs": result.missing_outputs,
        "violations": result.violations,
        "summary": result.summary()
    }, indent=2, ensure_ascii=False))
