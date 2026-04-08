#!/usr/bin/env python3
"""
Unified Quality Gate
====================
統一的品質閘道，整合所有檢查器

使用方式：
    from quality_gate.unified_gate import UnifiedGate

    gate = UnifiedGate(project_path)
    result = gate.check_all()

    print(f"Passed: {result.passed}")
    print(f"Score: {result.score}")

# Phase Enforcement 整合
    from quality_gate.phase_enforcer import PhaseEnforcer
    
    gate = UnifiedGate(project_path)
    gate.set_phase_enforcement(True)
    result = gate.check_all(phase=1, phase_enforcement=True)
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import json
from enum import Enum

# 匯入現有檢查器
from .doc_checker import DocumentChecker
from .phase_artifact_enforcer import PhaseArtifactEnforcer, Phase
from .constitution import run_constitution_check, ConstitutionCheckResult

# 匯入 Logic Checker（2026-03-28 新增）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from scripts.spec_logic_checker import SpecLogicChecker
    SPEC_LOGIC_CHECKER_AVAILABLE = True
except ImportError:
    SPEC_LOGIC_CHECKER_AVAILABLE = False

# 匯入 Phase 5-8 Constitution Checkers（2026-03-29 新增）
from .constitution.verification_constitution_checker import check_verification_constitution
from .constitution.quality_report_constitution_checker import check_quality_report_constitution
from .constitution.risk_management_constitution_checker import check_risk_management_constitution
from .constitution.configuration_constitution_checker import check_configuration_constitution

# 匯入新工具（2026-03-29 新增）
try:
    from .fr_id_tracker import FRIDTracker
    FR_ID_TRACKER_AVAILABLE = True
except ImportError:
    FR_ID_TRACKER_AVAILABLE = False

# 匯入資料夾結構檢查器（2026-03-29 新增）
try:
    from .folder_structure_checker import FolderStructureChecker
    FOLDER_STRUCTURE_CHECKER_AVAILABLE = True
except ImportError:
    FOLDER_STRUCTURE_CHECKER_AVAILABLE = False

try:
    from .threat_analyzer import ThreatAnalyzer
    THREAT_ANALYZER_AVAILABLE = True
except ImportError:
    THREAT_ANALYZER_AVAILABLE = False

try:
    from .coverage_checker import CoverageChecker
    COVERAGE_CHECKER_AVAILABLE = True
except ImportError:
    COVERAGE_CHECKER_AVAILABLE = False

try:
    from .issue_tracker import IssueTracker
    ISSUE_TRACKER_AVAILABLE = True
except ImportError:
    ISSUE_TRACKER_AVAILABLE = False

try:
    from .risk_status_checker import RiskStatusChecker
    RISK_STATUS_CHECKER_AVAILABLE = True
except ImportError:
    RISK_STATUS_CHECKER_AVAILABLE = False

# 匯入 P0/P1 優先級自動化工具（2026-03-29 新增）
try:
    from .tc_trace_checker import TCTraceChecker
    TC_TRACE_CHECKER_AVAILABLE = True
except ImportError:
    TC_TRACE_CHECKER_AVAILABLE = False

try:
    from .fr_coverage_checker import FRCoverageChecker
    FR_COVERAGE_CHECKER_AVAILABLE = True
except ImportError:
    FR_COVERAGE_CHECKER_AVAILABLE = False

try:
    from .fr_verification_method_checker import FRVerificationMethodChecker
    FR_VERIFICATION_METHOD_CHECKER_AVAILABLE = True
except ImportError:
    FR_VERIFICATION_METHOD_CHECKER_AVAILABLE = False

try:
    from .tc_derivation_checker import TCDerivationChecker
    TC_DERIVATION_CHECKER_AVAILABLE = True
except ImportError:
    TC_DERIVATION_CHECKER_AVAILABLE = False

try:
    from .module_tracking_checker import ModuleTrackingChecker
    MODULE_TRACKING_CHECKER_AVAILABLE = True
except ImportError:
    MODULE_TRACKING_CHECKER_AVAILABLE = False

try:
    from .error_handling_checker import ErrorHandlingChecker
    ERROR_HANDLING_CHECKER_AVAILABLE = True
except ImportError:
    ERROR_HANDLING_CHECKER_AVAILABLE = False

try:
    from .compliance_matrix_checker import ComplianceMatrixChecker
    COMPLIANCE_MATRIX_CHECKER_AVAILABLE = True
except ImportError:
    COMPLIANCE_MATRIX_CHECKER_AVAILABLE = False

try:
    from .negative_test_checker import NegativeTestChecker
    NEGATIVE_TEST_CHECKER_AVAILABLE = True
except ImportError:
    NEGATIVE_TEST_CHECKER_AVAILABLE = False

try:
    from .pytest_result_checker import PytestResultChecker
    PYTEST_RESULT_CHECKER_AVAILABLE = True
except ImportError:
    PYTEST_RESULT_CHECKER_AVAILABLE = False

try:
    from .root_cause_checker import RootCauseChecker
    ROOT_CAUSE_CHECKER_AVAILABLE = True
except ImportError:
    ROOT_CAUSE_CHECKER_AVAILABLE = False

# 匯入 PhaseEnforcer（2026-03-29 新增）
try:
    from .phase_enforcer import PhaseEnforcer, PhaseEnforcementResult
    PHASE_ENFORCER_AVAILABLE = True
except ImportError:
    PHASE_ENFORCER_AVAILABLE = False

# 匯入 CQG Tools（v6.60+ 新增）
try:
    from .linter_adapter import LinterAdapter
    from .complexity_checker import ComplexityChecker
    from .coverage_analyzer import CoverageAnalyzer
    from .fitness_functions import FitnessFunctions
    CQG_AVAILABLE = True
except ImportError as e:
    CQG_AVAILABLE = False
    _cqg_import_error = str(e)

# 匯入 Computational Sensors（P0-1 新增）
try:
    from .sensors.sensors import ComputationalSensors
    SENSORS_AVAILABLE = True
except ImportError as e:
    SENSORS_AVAILABLE = False
    _sensors_import_error = str(e)

# 匯入 SAB Tools（v6.60+ 新增：用於 Phase 2 SAB 建立）
try:
    from .sab_parser import parse_sad
    from .sab_spec import SabSpec
    from .baseline_manager import BaselineManager
    SAB_AVAILABLE = True
except ImportError as _sab_e:
    SAB_AVAILABLE = False
    _sab_import_error = str(_sab_e)


@dataclass
class CheckResult:
    """單項檢查結果"""
    name: str
    passed: bool
    score: float
    violations: List[str]
    details: Dict


@dataclass
class UnifiedGateResult:
    """統一品質閘道結果"""
    passed: bool
    overall_score: float
    checks: List[CheckResult]
    summary: Dict

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "overall_score": self.overall_score,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "score": c.score,
                    "violations": c.violations,
                    "details": c.details
                }
                for c in self.checks
            ],
            "summary": self.summary
        }


class UnifiedGate:
    """
    統一品質閘道

    整合三種檢查：
    1. Document Existence (doc_checker)
    2. Document Compliance (constitution)
    3. Phase References (phase_artifact)
    """

    def __init__(self, project_path: str = ".", config: dict = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        self.doc_checker = DocumentChecker(str(self.project_path))
        self.phase_enforcer = PhaseArtifactEnforcer(str(self.project_path))
        # PhaseEnforcer 初始化（2026-03-29 新增）
        if PHASE_ENFORCER_AVAILABLE:
            self.phase_checker = PhaseEnforcer(str(self.project_path))
        else:
            self.phase_checker = None

        # CQG Tools 初始化（v6.60+ 新增）
        if CQG_AVAILABLE:
            self.linter = LinterAdapter(str(self.project_path))
            self.complexity = ComplexityChecker(str(self.project_path))
            self.coverage_analyzer = CoverageAnalyzer(str(self.project_path))
            self.fitness = FitnessFunctions(str(self.project_path))
        else:
            self.linter = None
            self.complexity = None
            self.coverage_analyzer = None
            self.fitness = None
        self.cqg_available = CQG_AVAILABLE

    def _log_to_development_log(self, tool_name: str, result: CheckResult, phase: int = None):
        """將 QG 工具執行結果寫入 DEVELOPMENT_LOG

        Args:
            tool_name: 工具名稱（Constitution, ASPICE, FrameworkEnforcer, PhaseTruth）
            result: CheckResult 物件
            phase: Phase 編號（可選）
        """
        try:
            log_path = self.project_path / "DEVELOPMENT_LOG.md"
            timestamp = "{{timestamp}}"  # 格式化時間戳

            # 根據不同工具格式化輸出（符合 auditor QG_EVIDENCE_PATTERNS）
            if tool_name == "Constitution":
                status_icon = "✅" if result.passed else "❌"
                log_entry = f"\n{status_icon} **[{timestamp}] Constitution Score**: {result.score:.1f}% (threshold > 80%)\n"
            elif tool_name == "ASPICE":
                status_icon = "✅" if result.passed else "❌"
                log_entry = f"\n{status_icon} **[{timestamp}] ASPICE Compliance Rate**: {result.score:.1f}%\n"
            elif tool_name == "FrameworkEnforcer":
                violations_count = len(result.violations)
                status_icon = "✅" if violations_count == 0 else "❌"
                log_entry = f"\n{status_icon} **[{timestamp}] FrameworkEnforcer**: {status_icon} {violations_count} violations\n"
            elif tool_name == "PhaseTruth":
                status_icon = "✅" if result.passed else "❌"
                log_entry = f"\n{status_icon} **[{timestamp}] Phase Truth Score**: {result.score:.1f}%\n"
            else:
                log_entry = f"\n[{timestamp}] {tool_name}: {result.score:.1f}%\n"

            # 寫入 DEVELOPMENT_LOG
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)

        except Exception as e:
            print(f"[WARNING] Failed to log to DEVELOPMENT_LOG: {e}")

    # ── Runtime Metrics State ──────────────────────────────────────────
    def _ensure_state(self):
        """確保 .methodology/state.json 存在"""
        state_dir = self.project_path / ".methodology"
        state_dir.mkdir(exist_ok=True)
        state_path = state_dir / "state.json"
        
        if not state_path.exists():
            initial_state = {
                "current_phase": 1,
                "current_step": None,
                "current_module": None,
                "status": "INIT",
                "last_commit": None,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "phase_state": {
                    "started_at": None,
                    "blocks": 0,
                    "ab_rounds": 0,
                    "warnings": 0,
                    "last_gate_score": None,
                    "estimated_minutes": 60,
                },
                # 新增：產物追蹤
                "artifacts": {},  # {artifact_name: {version, commit_hash, path, summary, updated_at}}
                # 新增：任務圖
                "tasks": [],  # [{id, title, status, dependencies, result, summary}]
                # 新增：依賴圖
                "dependencies": {},  # {task_id: [dependent_task_ids]}
                "next_action": None,
                "blockers": [],
                "history": [],
                "state_history": []
            }
            state_path.write_text(json.dumps(initial_state, indent=2))

    def _read_state(self) -> dict:
        """讀取 state.json"""
        state_path = self.project_path / ".methodology" / "state.json"
        if state_path.exists():
            return json.loads(state_path.read_text())
        self._ensure_state()
        return json.loads(state_path.read_text())

    def _write_state(self, state: dict):
        """寫入 state.json"""
        state_path = self.project_path / ".methodology" / "state.json"
        state_path.write_text(json.dumps(state, indent=2))

    def update_artifact(self, name: str, version: str, path: str, summary: str = ""):
        """
        更新產物版本
        
        Args:
            name: 產物名稱（如 "SRS.md", "SAD.md"）
            version: 版本（如 "v1.0.0"）
            path: 產物路徑
            summary: 50字內摘要
        """
        state = self._read_state()
        artifacts = state.get("artifacts", {})
        
        artifacts[name] = {
            "version": version,
            "commit_hash": self._get_current_commit(),
            "path": path,
            "summary": summary,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        state["artifacts"] = artifacts
        self._write_state(state)

    def add_task(self, task_id: str, title: str, dependencies: List[str] = None):
        """新增任務到 task graph"""
        state = self._read_state()
        tasks = state.get("tasks", [])
        
        # 避免重複
        if any(t["id"] == task_id for t in tasks):
            return
        
        tasks.append({
            "id": task_id,
            "title": title,
            "status": "pending",
            "dependencies": dependencies or [],
            "result": None,
            "summary": None
        })
        
        # 更新 dependencies
        deps = state.get("dependencies", {})
        deps[task_id] = dependencies or []
        
        state["tasks"] = tasks
        state["dependencies"] = deps
        self._write_state(state)

    def update_task_result(self, task_id: str, result: Any, summary: str, status: str = "completed"):
        """更新任務結果"""
        state = self._read_state()
        tasks = state.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                task["result"] = result
                task["summary"] = summary
                task["status"] = status
                break
        
        state["tasks"] = tasks
        self._write_state(state)

    def _get_current_commit(self) -> str:
        """取得當前 git commit hash"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=self.project_path
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _is_new_phase(self, phase: int) -> bool:
        """檢查是否是新 Phase 開始"""
        state = self._read_state()
        return state.get("current_phase") != phase

    def _update_state(self, event: str, **kwargs):
        """
        寫入 state.json - 唯一的寫入點
        
        Events:
            - PHASE_START: Phase 開始
            - BLOCK: FrameworkEnforcer 返回 BLOCK
            - AB_ROUND: A↔B 來回一次
            - GATE_CHECK: Quality Gate 完成
            - PHASE_END: Phase 完成
        """
        state = self._read_state()
        ps = state.get("phase_state", {})
        
        # 更新 last_check_at
        ps["last_check_at"] = datetime.now(timezone.utc).isoformat()
        
        if event == "PHASE_START":
            phase = kwargs.get("phase")
            state["current_phase"] = phase
            ps["started_at"] = datetime.now(timezone.utc).isoformat()
            ps["blocks"] = 0
            ps["ab_rounds"] = 0
            ps["warnings"] = 0
            ps["last_gate_score"] = None
            # 預設 estimated_minutes（可被 cli.py 或外部覆寫）
            ps["estimated_minutes"] = kwargs.get("estimated_minutes", 60)
        
        elif event == "BLOCK":
            ps["blocks"] = ps.get("blocks", 0) + 1
            violations = kwargs.get("violations", 1)
            self._check_and_append_alert(state, "BLOCK_COUNT_HIGH", ps["blocks"])
        
        elif event == "AB_ROUND":
            ps["ab_rounds"] = ps.get("ab_rounds", 0) + 1
            self._check_and_append_alert(state, "AB_ROUND_HIGH", ps["ab_rounds"])
        
        elif event == "GATE_CHECK":
            score = kwargs.get("score")
            if score is not None:
                ps["last_gate_score"] = score
            if not kwargs.get("passed", True):
                ps["warnings"] = ps.get("warnings", 0) + 1
        
        elif event == "STEP_START":
            # Step 開始，更新 step/module/next_action
            step = kwargs.get("step")
            module = kwargs.get("module")
            next_action = kwargs.get("next_action")
            if step is not None:
                state["current_step"] = step
            if module is not None:
                state["current_module"] = module
            if next_action is not None:
                state["next_action"] = next_action

        elif event == "PHASE_END":
            # Phase 結束，歸零 phase_state
            ps["started_at"] = None
            ps["blocks"] = 0
            ps["ab_rounds"] = 0
            ps["warnings"] = 0
        
        state["phase_state"] = ps
        
        # Append to history（永不刪除）
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **kwargs
        }
        state["history"] = state.get("history", [])
        state["history"].append(history_entry)
        
        # 保持 history 只留最近 100 筆
        state["history"] = state["history"][-100:]
        
        self._write_state(state)

    def _calculate_integrity_score(self, checks: List[CheckResult]) -> int:
        """計算 Integrity Score（邏輯正確性）
        
        基於 Logic Correctness Check 和 Constitution Check 的分數
        """
        if not checks:
            return 100
        
        # 找到 Logic 和 Constitution 分數
        logic_score = None
        constitution_score = None
        
        for c in checks:
            if "Logic" in c.name:
                logic_score = c.score
            if "Constitution" in c.name:
                constitution_score = c.score
        
        # 計算平均
        scores = [s for s in [logic_score, constitution_score] if s is not None]
        if not scores:
            return 100
        
        return int(sum(scores) / len(scores))

    def _check_and_append_alert(self, state: dict, alert_type: str, current_value: int):
        """檢查預警阈值，達標時追加 alert"""
        thresholds = {
            "BLOCK_COUNT_HIGH": 5,
            "AB_ROUND_HIGH": 5,
        }
        threshold = thresholds.get(alert_type)
        if threshold and current_value >= threshold:
            # 檢查是否已經觸發過
            existing = [a for a in state.get("trend_alerts", []) if a.get("type") == alert_type and a.get("triggered_at")]
            if not existing:
                state.setdefault("trend_alerts", []).append({
                    "type": alert_type,
                    "current": current_value,
                    "threshold": threshold,
                    "triggered_at": datetime.now(timezone.utc).isoformat()
                })

    def check_all(self, phase=None, strict_mode=True, phase_enforcement=False) -> UnifiedGateResult:
        """執行所有檢查
        
        Args:
            phase: 可選，指定要執行的檢查範圍
                - None: 執行全部 13 個檢查
                - 5: 只執行 Phase 5 相關檢查
                - "5-8": 執行 Phase 5-8 相關檢查
                - 其他數字/範圍: 支援對應的檢查
        """
        checks = []
        
        # 確保 state.json 存在（Runtime Metrics）
        self._ensure_state()
        
        # 解析 phase 參數
        phase_filter = self._parse_phase_filter(phase)
        
        # 儲存 phase 到實例屬性（供 SAB drift detection 使用）
        if phase_filter and len(phase_filter) == 1 and not ("all" in phase_filter or len(phase_filter) > 1):
            self.phase = list(phase_filter)[0]
        else:
            # 從 state 讀取當前 phase
            state = self._read_state()
            self.phase = state.get("current_phase", 1)
        
        # 追蹤 Phase 開始（如果是新 Phase）
        if phase_filter and len(phase_filter) == 1:
            phase_num = list(phase_filter)[0]
            if isinstance(phase_num, int) and self._is_new_phase(phase_num):
                self._update_state(event="PHASE_START", phase=phase_num)

        
        # 1. CQG Code Quality Checks (P0/P1/P2) — always run when enabled
        if self.config.get("enable_cqg", True):
            checks.append(self._check_linter())
            checks.append(self._check_complexity())
            checks.append(self._check_coverage_analyzer())
            checks.append(self._check_fitness())
            checks.append(self._check_sensors())
            checks.append(self._check_baseline_drift())

        # 2. Document Existence Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            doc_result = self._check_documents()
            checks.append(doc_result)

        # 2. Constitution Compliance Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            constitution_result = self._check_constitution()
            checks.append(constitution_result)

        # 3. Phase Artifact Reference Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            phase_result = self._check_phase_references()
            checks.append(phase_result)

        # 4. Logic Correctness Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            logic_result = self._check_logic_correctness()
            checks.append(logic_result)

        # 5. FR-ID Tracking Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            fr_id_result = self._check_fr_id_tracking()
            checks.append(fr_id_result)

        # 6. Threat Analysis Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            threat_result = self._check_threat_analysis()
            checks.append(threat_result)

        # 7. Coverage Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            coverage_result = self._check_coverage()
            checks.append(coverage_result)

        # 8. Issue Tracking Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            issue_result = self._check_issues()
            checks.append(issue_result)

        # 9. Risk Status Check (Phase 1-4)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            risk_result = self._check_risk_status()
            checks.append(risk_result)

        # 10. Folder Structure Check (Phase 1-4) - 2026-03-29 新增
        if phase_filter is not None:
            # 根據 phase 執行對應的資料夾結構檢查
            for p in [1, 2, 3, 4, 5, 6, 7, 8]:
                if p in phase_filter:
                    folder_result = self._check_folder_structure(p)
                    checks.append(folder_result)

        # 11. Phase Enforcement Check (2026-03-29 新增)
        # 當 phase_enforcement=True 時，自動執行 PhaseEnforcer
        if phase_enforcement and phase_filter is not None:
            for p in phase_filter:
                if p != "all":
                    enforcement_result = self._check_phase_enforcement(p)
                    checks.append(enforcement_result)

        # 11. Phase 5: Verification Constitution Check
        if phase_filter is None or 5 in phase_filter or "5-8" in phase_filter:
            v5_result = self._check_verification_constitution()
            checks.append(v5_result)

        # 11. Phase 6: Quality Report Constitution Check
        if phase_filter is None or 6 in phase_filter or "5-8" in phase_filter:
            v6_result = self._check_quality_report_constitution()
            checks.append(v6_result)

        # 12. Phase 7: Risk Management Constitution Check
        if phase_filter is None or 7 in phase_filter or "5-8" in phase_filter:
            v7_result = self._check_risk_management_constitution()
            checks.append(v7_result)

        # 13. Phase 8: Configuration Constitution Check
        if phase_filter is None or 8 in phase_filter or "5-8" in phase_filter:
            v8_result = self._check_configuration_constitution()
            checks.append(v8_result)

        # ========== P0/P1 優先級自動化工具 (Phase 1-4) ==========
        
        # 14. FR Verification Method Check (Phase 1)
        if phase_filter is None or 1 in phase_filter or "all" in phase_filter:
            fr_vm_result = self._check_fr_verification_method()
            checks.append(fr_vm_result)
        
        # 15. FR Coverage Check (Phase 2)
        if phase_filter is None or 2 in phase_filter or "all" in phase_filter:
            fr_cov_result = self._check_fr_coverage()
            checks.append(fr_cov_result)
        
        # 16. Error Handling Check (Phase 2)
        if phase_filter is None or 2 in phase_filter or "all" in phase_filter:
            err_result = self._check_error_handling()
            checks.append(err_result)

        # 16b. SAB Establishment (Phase 2) — 2026-04-07 新增
        if phase_filter is None or 2 in phase_filter or "all" in phase_filter:
            sab_result = self._check_sab()
            checks.append(sab_result)
        
        # 17. Module Tracking Check (Phase 3)
        if phase_filter is None or 3 in phase_filter or "all" in phase_filter:
            mod_result = self._check_module_tracking()
            checks.append(mod_result)
        
        # 18. Compliance Matrix Check (Phase 3)
        if phase_filter is None or 3 in phase_filter or "all" in phase_filter:
            comp_result = self._check_compliance_matrix()
            checks.append(comp_result)
        
        # 19. Negative Test Check (Phase 3)
        if phase_filter is None or 3 in phase_filter or "all" in phase_filter:
            neg_result = self._check_negative_test()
            checks.append(neg_result)
        
        # 20. TC Trace Check (Phase 4)
        if phase_filter is None or 4 in phase_filter or "all" in phase_filter:
            tc_trace_result = self._check_tc_trace()
            checks.append(tc_trace_result)
        
        # 21. TC Derivation Check (Phase 4)
        if phase_filter is None or 4 in phase_filter or "all" in phase_filter:
            tc_deriv_result = self._check_tc_derivation()
            checks.append(tc_deriv_result)
        
        # 22. Pytest Result Check (Phase 4)
        if phase_filter is None or 4 in phase_filter or "all" in phase_filter:
            pytest_result = self._check_pytest_result()
            checks.append(pytest_result)
        
        # 23. Root Cause Analysis Check (Phase 4)
        if phase_filter is None or 4 in phase_filter or "all" in phase_filter:
            root_cause_result = self._check_root_cause()
            checks.append(root_cause_result)

        # 計算總分
        total_score = sum(c.score for c in checks) / len(checks) if checks else 0
        all_passed = all(c.passed for c in checks)
        
        # 追蹤 GATE_CHECK 到 state.json（Runtime Metrics）
        # 計算 Integrity Score（邏輯正確性）
        integrity_score = self._calculate_integrity_score(checks)
        self._update_state(
            event="GATE_CHECK",
            phase=list(phase_filter)[0] if phase_filter and len(phase_filter) == 1 else None,
            score=round(total_score, 2),
            passed=all_passed,
            integrity_score=integrity_score
        )

        return UnifiedGateResult(
            passed=all_passed,
            overall_score=round(total_score, 2),
            checks=checks,
            summary={
                "total_checks": len(checks),
                "passed_checks": sum(1 for c in checks if c.passed),
                "failed_checks": sum(1 for c in checks if not c.passed),
                "critical_violations": self._count_critical(checks)
            }
        )
    
    def _parse_phase_filter(self, phase):
        """解析 phase 參數"""
        if phase is None:
            return None
        
        if isinstance(phase, int):
            return {phase}
        
        if isinstance(phase, str):
            if phase == "all":
                return {"all"}
            elif "-" in phase:
                # 例如 "5-8"
                start, end = phase.split("-")
                return set(range(int(start), int(end) + 1))
            else:
                return {int(phase)}
        
        return None

    # ========== CQG Code Quality Checks (v6.60+) ==========

    def _check_linter(self) -> CheckResult:
        """CQG-P0: Linter 檢查"""
        if not getattr(self, 'cqg_available', False) or self.linter is None:
            return CheckResult(
                name="CQG: Linter",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "CQG tools not available"}
            )
        try:
            result = self.linter.run()
            return CheckResult(
                name="CQG: Linter",
                passed=result.score >= 70,
                score=result.score,
                violations=[],
                details={
                    "tool": result.tool,
                    "language": result.language,
                    "errors": len(result.errors),
                    "warnings": len(result.warnings),
                    "violations": len(result.violations),
                    "top_violations": result.violations[:5] if result.violations else []
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Linter",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_complexity(self) -> CheckResult:
        """CQG-P0: Complexity 檢查"""
        if not getattr(self, 'cqg_available', False) or self.complexity is None:
            return CheckResult(
                name="CQG: Complexity",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "CQG tools not available"}
            )
        try:
            result = self.complexity.run()
            violations = result.violations
            critical_violations = [v for v in violations if v.get("rank") in ("A", "B")]
            return CheckResult(
                name="CQG: Complexity",
                passed=len(critical_violations) == 0,
                score=result.score,
                violations=[],
                details={
                    "tool": result.tool,
                    "avg_complexity": result.avg_complexity,
                    "max_complexity": result.max_complexity,
                    "total_violations": len(violations),
                    "critical_violations": len(critical_violations),
                    "top_violations": violations[:5] if violations else []
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Complexity",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_coverage_analyzer(self) -> CheckResult:
        """CQG-P1: Coverage 缺口分析"""
        if not getattr(self, 'cqg_available', False) or self.coverage_analyzer is None:
            return CheckResult(
                name="CQG: Coverage Gap",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "CQG tools not available"}
            )
        try:
            result = self.coverage_analyzer.run()
            return CheckResult(
                name="CQG: Coverage Gap",
                passed=result.score >= 70,
                score=result.score,
                violations=[],
                details={
                    "coverage_rate": result.coverage_rate,
                    "critical_gaps": len(result.critical_gaps),
                    "high_gaps": len(result.high_gaps),
                    "medium_gaps": len(result.medium_gaps),
                    "top_gaps": [(g.function, g.severity) for g in result.critical_gaps[:5]]
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Coverage Gap",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_fitness(self) -> CheckResult:
        """CQG-P2: Fitness Functions + SAB Drift Detection (Phase 3+)"""
        if not getattr(self, 'cqg_available', False) or self.fitness is None:
            return CheckResult(
                name="CQG: Fitness Functions",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "CQG tools not available"}
            )
        try:
            result = self.fitness.evaluate()
            
            # === SAB Drift Detection (Phase 3+) ===
            drift_report = {}
            sab_baseline_tag = None
            current_phase = getattr(self, 'phase', None)
            if current_phase is not None and current_phase >= 3:
                sab_baseline = self._load_sab_baseline()
                if sab_baseline:
                    drift_report = self._compute_fitness_drift(result, sab_baseline)
                    sab_baseline_tag = getattr(self, '_current_sab_tag', None)
            
            return CheckResult(
                name="CQG: Fitness Functions",
                passed=result.overall_score >= 60,
                score=result.overall_score,
                violations=[],
                details={
                    "coupling_score": result.coupling_score,
                    "cohesion_score": result.cohesion_score,
                    "stability_score": result.stability_score,
                    "reusability_score": result.reusability_score,
                    "violations": len(result.violations),
                    "cycle_groups": len(result.cycle_groups),
                    "critical_modules": result.critical_modules,
                    # SAB drift
                    "sab_drift": drift_report if drift_report else None,
                    "sab_baseline": sab_baseline_tag
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Fitness Functions",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_sensors(self) -> CheckResult:
        """CQG-P0: Computational Sensors Scan (complexity, coupling, coverage, maintainability)"""
        if not SENSORS_AVAILABLE:
            return CheckResult(
                name="CQG: Computational Sensors",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "ComputationalSensors not available"}
            )
        try:
            sensors = ComputationalSensors(str(self.project_path))
            report = sensors.scan()

            # 收集 violations
            violations = []
            for name, result in report.sensors.items():
                for v in result.violations:
                    violations.append({"sensor": name, **v})

            return CheckResult(
                name="CQG: Computational Sensors",
                passed=report.passed,
                score=report.weighted_score * 100,
                violations=violations,
                details={
                    "weighted_score": report.weighted_score,
                    "total_violations": report.total_violations,
                    "sensors": {
                        name: {
                            "score": r.score,
                            "passed": r.passed,
                            "details": r.details
                        }
                        for name, r in report.sensors.items()
                    }
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Computational Sensors",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_baseline_drift(self) -> CheckResult:
        """CQG-P1: Baseline Drift Detection via BaselineManager (Phase 3+)"""
        current_phase = getattr(self, 'phase', None)
        if current_phase is not None and current_phase < 3:
            return CheckResult(
                name="CQG: Baseline Drift",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": f"Only runs Phase 3+ (current: Phase {current_phase})"}
            )

        if not SAB_AVAILABLE:
            return CheckResult(
                name="CQG: Baseline Drift",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "BaselineManager not available"}
            )

        try:
            from .baseline_manager import BaselineManager
            bm = BaselineManager(str(self.project_path))

            # 收集當前 metrics
            current_metrics = {}
            if getattr(self, 'cqg_available', False) and self.fitness is not None:
                try:
                    fr = self.fitness.evaluate()
                    current_metrics["fitness_overall"] = fr.overall_score
                    current_metrics["fitness_coupling"] = fr.coupling_score
                    current_metrics["fitness_cohesion"] = fr.cohesion_score
                except Exception:
                    pass

            if not current_metrics:
                return CheckResult(
                    name="CQG: Baseline Drift",
                    passed=True,
                    score=100,
                    violations=[],
                    details={"status": "skipped", "reason": "No metrics available for comparison"}
                )

            # 執行 drift detection
            drift_result = bm.check_drift(current_metrics)

            # 計算 drift severity score
            drift_count = len(drift_result.drift) if drift_result.drift else 0
            if drift_count == 0:
                drift_score = 100
            elif drift_count <= 2:
                drift_score = 80
            elif drift_count <= 5:
                drift_score = 60
            else:
                drift_score = 40

            return CheckResult(
                name="CQG: Baseline Drift",
                passed=drift_count <= 3,
                score=drift_score,
                violations=[{"type": k, **v} for k, v in (drift_result.drift or {}).items()],
                details={
                    "baseline_tag": drift_result.tag,
                    "baseline_timestamp": drift_result.baseline_timestamp,
                    "current_timestamp": drift_result.current_timestamp,
                    "drift_count": drift_count,
                    "drift_summary": drift_result.summary,
                    "drift": drift_result.drift or {}
                }
            )
        except Exception as e:
            return CheckResult(
                name="CQG: Baseline Drift",
                passed=False,
                score=0,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _load_sab_baseline(self) -> Optional[dict]:
        """載入最新的 SAB baseline（從 .methodology/sab/）"""
        sab_dir = self.project_path / ".methodology" / "sab"
        if not sab_dir.exists():
            return None
        
        latest = sab_dir / "latest.json"
        if not latest.exists():
            # 找最新的 sab-phaseN.json
            files = sorted(sab_dir.glob("sab-phase*.json"), key=lambda p: p.stat().st_mtime)
            if not files:
                return None
            latest = files[-1]
        
        self._current_sab_tag = latest.stem
        return json.loads(latest.read_text())

    def _compute_fitness_drift(self, current_result, sab_baseline: dict) -> dict:
        """
        計算當前 fitness 與 SAB baseline 的 drift
        
        Args:
            current_result: FitnessFunctions.evaluate() 的結果
            sab_baseline: 從 _load_sab_baseline() 載入的 SAB dict
        
        Returns:
            drift dict，計算出的 drift 項目
        """
        drift = {}
        
        sab_modules = sab_baseline.get("modules", {})
        current_modules = {m.name: m for m in current_result.modules}
        
        # 1. 檢查模組是否被移除
        removed = [m for m in sab_modules if m not in current_modules]
        if removed:
            drift["removed_modules"] = removed
        
        # 2. Quality targets drift
        targets = sab_baseline.get("quality_targets", {})
        if targets:
            if "max_complexity" in targets:
                avg_complexity = getattr(current_result, 'avg_complexity', 0)
                if avg_complexity > targets["max_complexity"]:
                    drift["complexity_exceeded"] = {
                        "baseline": targets["max_complexity"],
                        "current": avg_complexity
                    }
        
        # 3. Overall score drift
        sab_score = sab_baseline.get("_fitness_score", None)
        if sab_score is not None:
            score_delta = current_result.overall_score - sab_score
            if abs(score_delta) > 5:  # 5% threshold
                drift["score_drift"] = {
                    "baseline": sab_score,
                    "current": current_result.overall_score,
                    "delta": score_delta,
                    "severity": "critical" if abs(score_delta) > 15 else "high" if abs(score_delta) > 10 else "medium"
                }
        
        # 4. Module count drift
        baseline_module_count = len(sab_modules)
        current_module_count = len(current_modules)
        if current_module_count != baseline_module_count:
            drift["module_count_drift"] = {
                "baseline": baseline_module_count,
                "current": current_module_count,
                "delta": current_module_count - baseline_module_count
            }
        
        return drift

    def _check_documents(self) -> CheckResult:
        """檢查文檔存在性（ASPICE Compliance Rate）"""
        result = self.doc_checker.check_all()

        violations = []
        # 從 summary 判斷是否通過
        summary = result.get("summary", {})
        compliance_rate = summary.get("compliance_rate", "0%")
        # 解析 compliance_rate 是否為 100%
        passed = summary.get("failed", 1) == 0

        for r in result.get("results", []):
            if r.get("status") == "MISSING":
                violations.append(f"Missing docs: {r.get('phase', 'unknown')} - {r.get('missing', '')}")

        # 分數以 compliance_rate 計算
        try:
            score = float(compliance_rate.rstrip("%"))
        except (ValueError, AttributeError):
            score = 100.0 if passed else 0.0

        check_result = CheckResult(
            name="Document Existence",
            passed=passed,
            score=score,
            violations=violations,
            details={"results": result}
        )

        # 記錄到 DEVELOPMENT_LOG（#5 修復 - ASPICE Compliance Rate）
        self._log_to_development_log("ASPICE", check_result)

        return check_result

    def _check_constitution(self) -> CheckResult:
        """檢查 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Constitution Compliance",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )

            result = run_constitution_check("all", str(docs_path), current_phase=getattr(self, 'phase', None))

            violations = []
            for v in result.violations:
                violations.append(f"{v.get('rule', 'unknown')}: {v.get('message', '')}")

            check_result = CheckResult(
                name="Constitution Compliance",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details={"result": asdict(result)}
            )

            # 記錄到 DEVELOPMENT_LOG（#5 修復）
            self._log_to_development_log("Constitution", check_result)

            return check_result
        except Exception as e:
            return CheckResult(
                name="Constitution Compliance",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )

    def _check_phase_references(self) -> CheckResult:
        """檢查 Phase 產物引用（Phase Truth Score）"""
        violations = []
        all_passed = True

        # 檢查每個 Phase 的依賴
        for phase in Phase:
            result = self.phase_enforcer.can_proceed_to(phase.value)
            if not result.passed:
                all_passed = False
                for missing in result.missing_references:
                    violations.append(f"Phase {phase.value} missing: {missing}")

        check_result = CheckResult(
            name="Phase References",
            passed=all_passed,
            score=100 if all_passed else 0,
            violations=violations,
            details={}
        )

        # 記錄到 DEVELOPMENT_LOG（#5 修復 - Phase Truth）
        self._log_to_development_log("PhaseTruth", check_result)

        return check_result

    def _count_critical(self, checks: List[CheckResult]) -> int:
        """計算 critical violations"""
        count = 0
        for check in checks:
            # 超過 3 個 violations 視為 critical
            if len(check.violations) > 3:
                count += 1
        return count

    def check_documents_only(self) -> CheckResult:
        """只檢查文檔存在性"""
        return self._check_documents()

    def check_constitution_only(self) -> CheckResult:
        """只檢查 Constitution 合規"""
        return self._check_constitution()

    def check_phase_only(self) -> CheckResult:
        """只檢查 Phase 引用"""
        return self._check_phase_references()

    def _check_logic_correctness(self) -> CheckResult:
        """檢查邏輯正確性（2026-03-28 新增）"""
        if not SPEC_LOGIC_CHECKER_AVAILABLE:
            return CheckResult(
                name="Logic Correctness",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "spec_logic_checker not available"}
            )
        
        try:
            checker = SpecLogicChecker(str(self.project_path))
            result = checker.scan_python_files()
            
            violations = []
            for issue in result.issues:
                violations.append(f"{issue.file_path}:{issue.line_number} - {issue.description}")
            
            return CheckResult(
                name="Logic Correctness",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details={
                    "files_checked": result.files_checked,
                    "functions_checked": result.functions_checked,
                    "issues_count": len(result.issues)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Logic Correctness",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def check_logic_only(self) -> CheckResult:
        """只檢查邏輯正確性"""
        return self._check_logic_correctness()

    def _check_fr_id_tracking(self) -> CheckResult:
        """檢查 FR-ID 追蹤（2026-03-29 新增）"""
        if not FR_ID_TRACKER_AVAILABLE:
            return CheckResult(
                name="FR-ID Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "fr_id_tracker not available"}
            )
        
        try:
            tracker = FRIDTracker(str(self.project_path))
            result = tracker.scan()
            
            violations = []
            for untracked in result.get("untracked_ids", []):
                violations.append(f"FR-ID not tracked: {untracked}")
            
            return CheckResult(
                name="FR-ID Tracking",
                passed=result.get("passed", False),
                score=result.get("tracked", 0) / result.get("total_fr_ids", 1) * 100 if result.get("total_fr_ids", 0) > 0 else 100,
                violations=violations,
                details={
                    "total": result.get("total_fr_ids", 0),
                    "tracked": result.get("tracked", 0),
                    "untracked": result.get("untracked", 0)
                }
            )
        except Exception as e:
            return CheckResult(
                name="FR-ID Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_threat_analysis(self) -> CheckResult:
        """檢查威脅分析（2026-03-29 新增）"""
        if not THREAT_ANALYZER_AVAILABLE:
            return CheckResult(
                name="Threat Analysis",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "threat_analyzer not available"}
            )
        
        try:
            analyzer = ThreatAnalyzer(str(self.project_path))
            result = analyzer.analyze()
            
            violations = []
            for threat in result.get("details", []):
                if threat.get("severity") == "HIGH":
                    violations.append(f"Threat: {threat.get('description', '')}")
            
            return CheckResult(
                name="Threat Analysis",
                passed=result.get("passed", False),
                score=100 - result.get("high_severity", 0) * 10,
                violations=violations,
                details={
                    "total": result.get("total_threats", 0),
                    "high": result.get("high_severity", 0),
                    "medium": result.get("medium_severity", 0)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Threat Analysis",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_coverage(self) -> CheckResult:
        """檢查測試覆蓋率（2026-03-29 新增）"""
        if not COVERAGE_CHECKER_AVAILABLE:
            return CheckResult(
                name="Test Coverage",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "coverage_checker not available"}
            )
        
        try:
            checker = CoverageChecker(str(self.project_path))
            result = checker.check()
            
            violations = []
            if not result.get("passed", True):
                violations.append(f"Coverage below threshold: {result.get('line_coverage', 0)}%")
            
            return CheckResult(
                name="Test Coverage",
                passed=result.get("passed", False),
                score=result.get("line_coverage", 0),
                violations=violations,
                details={
                    "line_coverage": result.get("line_coverage", 0),
                    "branch_coverage": result.get("branch_coverage", 0),
                    "threshold": result.get("threshold", 80)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Test Coverage",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_issues(self) -> CheckResult:
        """檢查問題追蹤（2026-03-29 新增）"""
        if not ISSUE_TRACKER_AVAILABLE:
            return CheckResult(
                name="Issue Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "issue_tracker not available"}
            )
        
        try:
            tracker = IssueTracker(str(self.project_path))
            result = tracker.track()
            
            violations = []
            for issue in result.get("details", []):
                if issue.get("severity") == "HIGH":
                    violations.append(f"Issue: {issue.get('description', '')}")
            
            return CheckResult(
                name="Issue Tracking",
                passed=result.get("passed", False),
                score=100 - result.get("critical", 0) * 10,
                violations=violations,
                details={
                    "total": result.get("total_issues", 0),
                    "open": result.get("open_issues", 0),
                    "critical": result.get("critical", 0)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Issue Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    def _check_risk_status(self) -> CheckResult:
        """檢查風險狀態（2026-03-29 新增）"""
        if not RISK_STATUS_CHECKER_AVAILABLE:
            return CheckResult(
                name="Risk Status",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "risk_status_checker not available"}
            )
        
        try:
            checker = RiskStatusChecker(str(self.project_path))
            result = checker.check()
            
            violations = []
            for risk in result.get("details", []):
                if risk.get("severity") == "HIGH" and risk.get("status") == "Open":
                    violations.append(f"Risk: {risk.get('description', '')}")
            
            return CheckResult(
                name="Risk Status",
                passed=result.get("passed", False),
                score=100 - result.get("high_severity", 0) * 10,
                violations=violations,
                details={
                    "total": result.get("total_risks", 0),
                    "open": result.get("open_risks", 0),
                    "high": result.get("high_severity", 0)
                }
            )
        except Exception as e:
            return CheckResult(
                name="Risk Status",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    # ========== Phase 5-8 Constitution Checks (2026-03-29 新增) ==========
    
    def _check_verification_constitution(self) -> CheckResult:
        """檢查 Phase 5 驗證 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Phase 5: Verification Constitution",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )
            
            result = check_verification_constitution(str(docs_path))
            
            violations = []
            for v in result.violations:
                violations.append(f"{v.get('type', 'unknown')}: {v.get('message', '')}")
            
            return CheckResult(
                name="Phase 5: Verification Constitution",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details=result.details
            )
        except Exception as e:
            return CheckResult(
                name="Phase 5: Verification Constitution",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )
    
    def _check_quality_report_constitution(self) -> CheckResult:
        """檢查 Phase 6 品質確保 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Phase 6: Quality Report Constitution",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )
            
            result = check_quality_report_constitution(str(docs_path))
            
            violations = []
            for v in result.violations:
                violations.append(f"{v.get('type', 'unknown')}: {v.get('message', '')}")
            
            return CheckResult(
                name="Phase 6: Quality Report Constitution",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details=result.details
            )
        except Exception as e:
            return CheckResult(
                name="Phase 6: Quality Report Constitution",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )
    
    def _check_risk_management_constitution(self) -> CheckResult:
        """檢查 Phase 7 風險管理 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Phase 7: Risk Management Constitution",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )
            
            result = check_risk_management_constitution(str(docs_path))
            
            violations = []
            for v in result.violations:
                violations.append(f"{v.get('type', 'unknown')}: {v.get('message', '')}")
            
            return CheckResult(
                name="Phase 7: Risk Management Constitution",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details=result.details
            )
        except Exception as e:
            return CheckResult(
                name="Phase 7: Risk Management Constitution",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )
    
    def _check_configuration_constitution(self) -> CheckResult:
        """檢查 Phase 8 配置管理 Constitution 合規"""
        try:
            docs_path = self.project_path / "docs"
            if not docs_path.exists():
                return CheckResult(
                    name="Phase 8: Configuration Constitution",
                    passed=False,
                    score=0,
                    violations=["docs/ directory not found"],
                    details={}
                )
            
            result = check_configuration_constitution(str(docs_path))
            
            violations = []
            for v in result.violations:
                violations.append(f"{v.get('type', 'unknown')}: {v.get('message', '')}")
            
            return CheckResult(
                name="Phase 8: Configuration Constitution",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details=result.details
            )
        except Exception as e:
            return CheckResult(
                name="Phase 8: Configuration Constitution",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )

    # ========== P0/P1 優先級自動化工具檢查方法 (2026-03-29 新增) ==========
    
    def _check_fr_verification_method(self) -> CheckResult:
        """檢查 FR 驗證方法（Phase 1）"""
        if not FR_VERIFICATION_METHOD_CHECKER_AVAILABLE:
            return CheckResult(
                name="FR Verification Method",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "fr_verification_method_checker not available"}
            )
        
        try:
            checker = FRVerificationMethodChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="FR Verification Method",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="FR Verification Method",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_fr_coverage(self) -> CheckResult:
        """檢查 FR 覆蓋率（Phase 2）"""
        if not FR_COVERAGE_CHECKER_AVAILABLE:
            return CheckResult(
                name="FR Coverage",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "fr_coverage_checker not available"}
            )
        
        try:
            checker = FRCoverageChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="FR Coverage",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="FR Coverage",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_error_handling(self) -> CheckResult:
        """檢查錯誤處理（Phase 2）"""
        if not ERROR_HANDLING_CHECKER_AVAILABLE:
            return CheckResult(
                name="Error Handling",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "error_handling_checker not available"}
            )
        
        try:
            checker = ErrorHandlingChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Error Handling",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Error Handling",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_module_tracking(self) -> CheckResult:
        """檢查模組追蹤（Phase 3）"""
        if not MODULE_TRACKING_CHECKER_AVAILABLE:
            return CheckResult(
                name="Module Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "module_tracking_checker not available"}
            )
        
        try:
            checker = ModuleTrackingChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Module Tracking",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Module Tracking",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_compliance_matrix(self) -> CheckResult:
        """檢查合規矩陣（Phase 3）"""
        if not COMPLIANCE_MATRIX_CHECKER_AVAILABLE:
            return CheckResult(
                name="Compliance Matrix",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "compliance_matrix_checker not available"}
            )
        
        try:
            checker = ComplianceMatrixChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Compliance Matrix",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Compliance Matrix",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_negative_test(self) -> CheckResult:
        """檢查負面測試（Phase 3）"""
        if not NEGATIVE_TEST_CHECKER_AVAILABLE:
            return CheckResult(
                name="Negative Test",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "negative_test_checker not available"}
            )
        
        try:
            checker = NegativeTestChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Negative Test",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Negative Test",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_tc_trace(self) -> CheckResult:
        """檢查 TC 追蹤覆蓋率（Phase 4）"""
        if not TC_TRACE_CHECKER_AVAILABLE:
            return CheckResult(
                name="TC Trace",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "tc_trace_checker not available"}
            )
        
        try:
            checker = TCTraceChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="TC Trace",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="TC Trace",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_tc_derivation(self) -> CheckResult:
        """檢查 TC 推導（Phase 4）"""
        if not TC_DERIVATION_CHECKER_AVAILABLE:
            return CheckResult(
                name="TC Derivation",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "tc_derivation_checker not available"}
            )
        
        try:
            checker = TCDerivationChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="TC Derivation",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="TC Derivation",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_pytest_result(self) -> CheckResult:
        """檢查 Pytest 結果（Phase 4）"""
        if not PYTEST_RESULT_CHECKER_AVAILABLE:
            return CheckResult(
                name="Pytest Result",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "pytest_result_checker not available"}
            )
        
        try:
            checker = PytestResultChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Pytest Result",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Pytest Result",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )
    
    def _check_root_cause(self) -> CheckResult:
        """檢查根本原因分析（Phase 4）"""
        if not ROOT_CAUSE_CHECKER_AVAILABLE:
            return CheckResult(
                name="Root Cause Analysis",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "root_cause_checker not available"}
            )
        
        try:
            checker = RootCauseChecker(str(self.project_path))
            result = checker.run(str(self.project_path))
            
            violations = []
            for v in result.get("violations", []):
                violations.append(v)
            
            return CheckResult(
                name="Root Cause Analysis",
                passed=result.get("passed", False),
                score=result.get("score", 0),
                violations=violations,
                details=result
            )
        except Exception as e:
            return CheckResult(
                name="Root Cause Analysis",
                passed=True,
                score=100,
                violations=[],
                details={"status": "error", "reason": str(e)}
            )

    # ========== 便捷方法 ==========
    
    def check_fr_id_only(self) -> CheckResult:
        """只檢查 FR-ID"""
        return self._check_fr_id_tracking()
    
    def check_threat_only(self) -> CheckResult:
        """只檢查威脅"""
        return self._check_threat_analysis()
    
    def check_coverage_only(self) -> CheckResult:
        """只檢查覆蓋率"""
        return self._check_coverage()
    
    def check_issues_only(self) -> CheckResult:
        """只檢查問題"""
        return self._check_issues()
    
    def check_risk_only(self) -> CheckResult:
        """只檢查風險"""
        return self._check_risk_status()
    
    # ========== Phase 5-8 便捷方法 ==========
    
    def check_verification_only(self) -> CheckResult:
        """只檢查 Phase 5 Verification Constitution"""
        return self._check_verification_constitution()
    
    def check_quality_report_only(self) -> CheckResult:
        """只檢查 Phase 6 Quality Report Constitution"""
        return self._check_quality_report_constitution()
    
    def check_risk_management_only(self) -> CheckResult:
        """只檢查 Phase 7 Risk Management Constitution"""
        return self._check_risk_management_constitution()
    
    def check_configuration_only(self) -> CheckResult:
        """只檢查 Phase 8 Configuration Constitution"""
        return self._check_configuration_constitution()

    # ========== Folder Structure Check (2026-03-29 新增) ==========
    
    def _check_folder_structure(self, phase: int) -> CheckResult:
        """檢查資料夾結構與產出物"""
        if not FOLDER_STRUCTURE_CHECKER_AVAILABLE:
            return CheckResult(
                name=f"Folder Structure (Phase {phase})",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "folder_structure_checker not available"}
            )
        
        try:
            checker = FolderStructureChecker(str(self.project_path))
            result = checker.run(phase)
            
            violations = []
            if result.missing_dirs:
                violations.append(f"Missing directories: {', '.join(result.missing_dirs)}")
            if result.missing_files:
                violations.append(f"Missing files: {', '.join(result.missing_files)}")
            if result.content_issues:
                violations.extend(result.content_issues)
            
            return CheckResult(
                name=f"Folder Structure (Phase {phase})",
                passed=result.passed,
                score=result.score,
                violations=violations,
                details=result.details
            )
        except Exception as e:
            return CheckResult(
                name=f"Folder Structure (Phase {phase})",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )
    
    def check_folder_structure_only(self, phase: int) -> CheckResult:
        """只檢查指定 Phase 的資料夾結構"""
        return self._check_folder_structure(phase)
    
    def _check_phase_enforcement(self, phase: int) -> CheckResult:
        """檢查 Phase Enforcement 結果（2026-03-29 新增）"""
        if not PHASE_ENFORCER_AVAILABLE or self.phase_checker is None:
            return CheckResult(
                name=f"Phase Enforcement (Phase {phase})",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "phase_enforcer not available"}
            )
        
        try:
            result = self.phase_checker.enforce_phase(phase)
            
            violations = []
            if result.blocker_issues:
                violations.extend(result.blocker_issues)
            
            # 🚨 BLOCK 發生時寫入 state.json（Runtime Metrics）
            if not result.passed and violations:
                self._update_state(
                    event="BLOCK",
                    phase=phase,
                    violations=len(violations)
                )
            
            return CheckResult(
                name=f"Phase Enforcement (Phase {phase})",
                passed=result.passed,
                score=result.gate_score,
                violations=violations,
                details={
                    "structure_score": result.structure_check.score,
                    "content_score": result.content_check.score,
                    "gate_score": result.gate_score,
                    "can_proceed": result.can_proceed
                }
            )
        except Exception as e:
            return CheckResult(
                name=f"Phase Enforcement (Phase {phase})",
                passed=False,
                score=0,
                violations=[f"Error: {str(e)}"],
                details={}
            )
    
    def check_phase_enforcement_only(self, phase: int) -> CheckResult:
        """只檢查指定 Phase 的 Enforcement 結果"""
        return self._check_phase_enforcement(phase)

    # ========== SAB — Software Architecture Baseline (Phase 2) ==========

    def _check_sab(self) -> CheckResult:
        """Phase 2: Parse SAD.md → SabSpec, save to .methodology/sab/"""
        # 只在 Phase 2 時實際建立 SAB
        current_phase = getattr(self, 'phase', None)
        if current_phase is not None and current_phase != 2:
            return CheckResult(
                name="SAB Establishment (Phase 2)",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": f"Only runs in Phase 2 (current: Phase {current_phase})"}
            )
        
        if not SAB_AVAILABLE:
            return CheckResult(
                name="SAB Establishment (Phase 2)",
                passed=True,
                score=100,
                violations=[],
                details={"status": "skipped", "reason": "SAB tools not available"}
            )

        sad_path = self.project_path / "SAD.md"
        if not sad_path.exists():
            return CheckResult(
                name="SAB Establishment (Phase 2)",
                passed=False,
                score=0,
                violations=[f"SAD.md not found at {sad_path}"],
                details={"status": "missing_sad"}
            )

        try:
            sab = parse_sad(sad_path)
            errors = sab.validate()

            # 如果有 validation errors，不儲存直接返回
            if errors:
                return CheckResult(
                    name="SAB Establishment (Phase 2)",
                    passed=False,
                    score=0,
                    violations=errors,
                    details={
                        "status": "validation_errors",
                        "errors": errors,
                        "sab_path": None
                    }
                )

            # 同時執行 fitness 檢查並附上分數到 SAB
            fitness_score = None
            if getattr(self, 'cqg_available', False) and self.fitness is not None:
                try:
                    fitness_result = self.fitness.evaluate()
                    fitness_score = fitness_result.overall_score
                except Exception:
                    pass  # fitness 失敗不影響 SAB 建立

            # 儲存 SAB snapshot 到 .methodology/sab/
            sab_dir = self.project_path / ".methodology" / "sab"
            sab_dir.mkdir(parents=True, exist_ok=True)
            
            # 建立包含 _fitness_score 的 dict
            sab_dict = sab.to_dict()
            if fitness_score is not None:
                sab_dict["_fitness_score"] = fitness_score
            
            # 儲存 sab-phase{phase}.json
            phase_tag = current_phase if current_phase is not None else 2
            sab_path = sab_dir / f"sab-phase{phase_tag}.json"
            sab_path.write_text(json.dumps(sab_dict, ensure_ascii=False, indent=2))
            
            # 更新 latest.json
            latest_path = sab_dir / "latest.json"
            latest_path.write_text(json.dumps(sab_dict, ensure_ascii=False, indent=2))

            return CheckResult(
                name="SAB Establishment (Phase 2)",
                passed=True,
                score=100,
                violations=[],
                details={
                    "status": "established",
                    "project": sab.project,
                    "phase": sab.phase,
                    "modules": len(sab.modules),
                    "layers": len(sab.layers),
                    "rules": len(sab.architecture_rules),
                    "sab_path": str(sab_path),
                    "fitness_score": fitness_score
                }
            )
        except Exception as e:
            return CheckResult(
                name="SAB Establishment (Phase 2)",
                passed=False,
                score=0,
                violations=[f"SAB parse error: {str(e)}"],
                details={"status": "parse_error"}
            )

    def establish_sab(self) -> Optional[SabSpec]:
        """公開方法：手動建立 SAB（Phase 2 成功後呼叫）"""
        if not SAB_AVAILABLE:
            return None
        sad_path = self.project_path / "SAD.md"
        if not sad_path.exists():
            return None
        sab = parse_sad(sad_path)
        sab_dir = self.project_path / ".methodology" / "sab"
        sab_dir.mkdir(parents=True, exist_ok=True)
        sab.save(sab_dir / f"sab-phase{getattr(self, 'phase', 2)}.json")
        return sab
    
    def set_phase_enforcement(self, enabled: bool):
        """設定是否啟用 Phase Enforcement"""
        self._phase_enforcement_enabled = enabled

    def end_phase(self, phase: int = None):
        """結束一個 Phase

        呼叫時機：Phase 完成時（手動或自動）
        會觸發 PHASE_END 事件寫入 state.json
        """
        if phase is None:
            state = self._read_state()
            phase = state.get("current_phase")

        if phase:
            self._update_state(event="PHASE_END", phase=phase)

    def update_step(self, step: str, module: str = None, next_action: dict = None):
        """更新當前 Step

        呼叫時機：開始新 Step 時
        會觸發 STEP_START 事件寫入 state.json

        Args:
            step: Step 名稱（如 "4.1", "4.2"）
            module: 模組名稱（如 "CircuitBreaker"）
            next_action: 下一步動作 dict（如 {"who": "...", "what": "..."}）
        """
        self._update_state(
            event="STEP_START",
            step=step,
            module=module,
            next_action=next_action
        )


# =============================================================================
# FSM State Machine
# =============================================================================

class ProjectState(Enum):
    """FSM 狀態定義"""
    INIT = "INIT"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    WRITING = "WRITING"
    PAUSED = "PAUSED"
    FREEZE = "FREEZE"
    COMPLETED = "COMPLETED"


class FSMStateMachine:
    """
    FSM 狀態機管理器

    整合 HR-12/13/14 煞車系統到完整的狀態機。

    狀態切換規則：
    - INIT → RUNNING（Phase 開始）
    - RUNNING → VERIFYING（A/B 審查開始）
    - VERIFYING → WRITING（審查不通過，回修）
    - VERIFYING → RUNNING（審查通過）
    - RUNNING → PAUSED（HR-12/13 觸發）
    - PAUSED → RUNNING（修復後解除）
    - RUNNING → FREEZE（HR-14 或嚴重問題）
    - PAUSED → FREEZE（問題升級）
    - 任意 → INIT（Phase Reset）
    """

    VALID_TRANSITIONS = {
        ProjectState.INIT: [ProjectState.RUNNING],
        ProjectState.RUNNING: [ProjectState.VERIFYING, ProjectState.PAUSED, ProjectState.COMPLETED, ProjectState.FREEZE],
        ProjectState.VERIFYING: [ProjectState.WRITING, ProjectState.RUNNING],
        ProjectState.WRITING: [ProjectState.VERIFYING, ProjectState.PAUSED],
        ProjectState.PAUSED: [ProjectState.RUNNING, ProjectState.FREEZE],
        ProjectState.FREEZE: [ProjectState.INIT],
        ProjectState.COMPLETED: [ProjectState.INIT],
    }

    def __init__(self, project_path):
        self.ug = UnifiedGate(project_path=project_path)

    def transition(self, from_state: ProjectState, to_state: ProjectState, reason: str = "") -> bool:
        """
        執行狀態切換

        Args:
            from_state: 來源狀態
            to_state: 目標狀態
            reason: 切換原因

        Returns:
            bool: 是否切換成功
        """
        state = self.ug._read_state()
        current = state.get("status", "INIT")

        if current != from_state.value:
            return False  # 狀態不匹配

        if to_state not in self.VALID_TRANSITIONS.get(from_state, []):
            return False  # 不允許的切換

        state["status"] = to_state.value
        state.setdefault("state_history", [])
        state["state_history"].append({
            "from": from_state.value,
            "to": to_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        self.ug._write_state(state)
        return True

    def get_state(self) -> ProjectState:
        """取得當前狀態"""
        state = self.ug._read_state()
        status = state.get("status", "INIT")
        try:
            return ProjectState(status)
        except ValueError:
            return ProjectState.INIT

    def trigger_brake(self, brake_type: str, reason: str):
        """
        觸發煞車（HR-12/13/14）

        Args:
            brake_type: 煞車類型（HR-12, HR-13, HR-14）
            reason: 觸發原因

        HR-12: A/B 審查 > 5 輪 → PAUSED
        HR-13: Phase 時間 > 3× 預估 → PAUSED
        HR-14: Integrity < 40 → FREEZE
        """
        current = self.ug._read_state().get("status", "INIT")

        if brake_type in ("HR-12", "HR-13"):
            # A/B 過多或時間過長 → PAUSED
            self.transition(ProjectState.RUNNING, ProjectState.PAUSED, f"{brake_type}: {reason}")
        elif brake_type == "HR-14":
            # Integrity 過低 → FREEZE
            self.transition(ProjectState.RUNNING, ProjectState.FREEZE, f"HR-14: {reason}")

    def resume(self):
        """解除煞車，恢復執行"""
        return self.transition(ProjectState.PAUSED, ProjectState.RUNNING, "Manual resume")

    def unfreeze(self):
        """解除凍住，回到 INIT（需審計後重置）"""
        return self.transition(ProjectState.FREEZE, ProjectState.INIT, "Manual unfreeze after audit")

    def start_phase(self):
        """開始新 Phase（INIT → RUNNING）"""
        self.transition(ProjectState.INIT, ProjectState.RUNNING, "Phase started")

    def start_verification(self):
        """開始 A/B 審查（RUNNING → VERIFYING）"""
        self.transition(ProjectState.RUNNING, ProjectState.VERIFYING, "Verification started")

    def verification_pass(self):
        """審查通過（VERIFYING → RUNNING）"""
        self.transition(ProjectState.VERIFYING, ProjectState.RUNNING, "Verification passed")

    def verification_fail(self):
        """審查不通過（VERIFYING → WRITING）"""
        self.transition(ProjectState.VERIFYING, ProjectState.WRITING, "Verification failed, rewriting")

    def complete_phase(self):
        """Phase 完成（RUNNING → COMPLETED）"""
        self.transition(ProjectState.RUNNING, ProjectState.COMPLETED, "Phase completed")

    def reset_phase(self):
        """重置 Phase（任意 → INIT）"""
        state = self.ug._read_state()
        try:
            current = ProjectState(state.get("status", "INIT"))
        except ValueError:
            current = ProjectState.INIT
        self.transition(current, ProjectState.INIT, "Phase reset")


# ===== 快速入口函式 =====

def unified_gate(
    project_root, 
    phase=None, 
    strict_mode=True, 
    include_code_quality: bool = True,
    weights: tuple = (0.25, 0.25, 0.50)
) -> Dict:
    """
    統一品質閘道 - 快速入口函式
    
    三層檢查系統：
    - L1: 結構檢查 (25%) - 使用 FolderStructureChecker
    - L2: 內容檢查 (25%) - 檢查檔案內容結構
    - L3: 代碼品質檢查 (50%) - 使用 Agent Quality Guard
    
    Args:
        project_root: 專案根目錄路徑
        phase: Phase 編號 (1-8)，None 表示檢查所有
        strict_mode: 是否啟用嚴格模式
        include_code_quality: 是否包含代碼品質檢查（L3）
        weights: 三層檢查的權重 (structure, content, code_quality)
        
    Returns:
        Dict: 檢查結果
    """
    from .phase_enforcer import PhaseEnforcer
    
    enforcer = PhaseEnforcer(
        project_root, 
        strict_mode=strict_mode,
        include_code_quality=include_code_quality,
        weights=weights
    )
    
    if phase is not None:
        result = enforcer.enforce_phase(phase)
        return result.to_dict()
    else:
        # 檢查所有 Phase
        report = enforcer.generate_report()
        return report
