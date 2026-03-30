#!/usr/bin/env python3
"""
PhaseEnforcer - Phase 自動化檢查系統
====================================
在每個 Phase 結束時自動觸發檢查，確保產出符合標準。

三層檢查系統：
- L1: 結構檢查 (25%) - 使用 FolderStructureChecker
- L2: 內容檢查 (25%) - 檢查檔案內容結構
- L3: 代碼品質檢查 (50%) - 使用 Agent Quality Guard

使用方式：
    from quality_gate.phase_enforcer import PhaseEnforcer
    
    enforcer = PhaseEnforcer("/path/to/project", strict_mode=True)
    result = enforcer.enforce_phase(1)
    
    if not result.can_proceed:
        print(f"Blocked! Issues: {result.blocker_issues}")
"""

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# 匯入 Claims Verifier（2026-03-31 新增 P0 反作弊模組）
try:
    from .claims_verifier import ClaimsVerifier
    CLAIMS_VERIFIER_AVAILABLE = True
except ImportError:
    CLAIMS_VERIFIER_AVAILABLE = False

# 匯入 A/B Enforcer（2026-03-31 新增 P0 反作弊模組）
try:
    from .ab_enforcer import ABEnforcer
    AB_ENFORCER_AVAILABLE = True
except ImportError:
    AB_ENFORCER_AVAILABLE = False

# 匯入 folder_structure_checker
try:
    from .folder_structure_checker import FolderStructureChecker, FolderCheckResult
    FOLDER_STRUCTURE_CHECKER_AVAILABLE = True
except ImportError:
    FOLDER_STRUCTURE_CHECKER_AVAILABLE = False

# 匯入 unified_gate（用於整合其他檢查器）
try:
    from .unified_gate import UnifiedGate, UnifiedGateResult
    UNIFIED_GATE_AVAILABLE = True
except ImportError:
    UNIFIED_GATE_AVAILABLE = False

# 匯入 Agent Quality Guard（2026-03-29 新增 L3）
AGENT_QUALITY_GUARD_AVAILABLE = False
try:
    # 嘗試從 agent-quality-guard 匯入
    agent_guard_path = Path(__file__).parent.parent.parent / "agent-quality-guard" / "src"
    if agent_guard_path.exists():
        sys.path.insert(0, str(agent_guard_path))
        from analyzer import analyze_code, InputError, ToolError, ExecutionError, SystemError
        from scorer import score_from_code
        AGENT_QUALITY_GUARD_AVAILABLE = True
except ImportError:
    AGENT_QUALITY_GUARD_AVAILABLE = False


@dataclass
class StructureCheckResult:
    """結構檢查結果"""
    score: float
    missing: List[str]
    passed: bool


@dataclass
class ContentCheckResult:
    """內容檢查結果"""
    score: float
    missing_sections: List[str]
    passed: bool


@dataclass
class CodeQualityCheckResult:
    """代碼品質檢查結果（L3）"""
    score: float
    files_scanned: int
    issues: List[Dict]
    passed: bool
    details: Dict

    def to_dict(self) -> Dict:
        return {
            "score": self.score,
            "files_scanned": self.files_scanned,
            "issues": self.issues,
            "passed": self.passed,
            "details": self.details
        }


@dataclass
class PhaseEnforcementResult:
    """Phase 執行結果"""
    phase: int
    passed: bool
    structure_check: StructureCheckResult
    content_check: ContentCheckResult
    code_quality_check: CodeQualityCheckResult  # 新增 L3
    gate_score: float
    can_proceed: bool
    blocker_issues: List[str]
    details: Dict

    def to_dict(self) -> Dict:
        return {
            "phase": self.phase,
            "passed": self.passed,
            "structure_check": asdict(self.structure_check),
            "content_check": asdict(self.content_check),
            "code_quality_check": asdict(self.code_quality_check),
            "gate_score": self.gate_score,
            "can_proceed": self.can_proceed,
            "blocker_issues": self.blocker_issues,
            "details": self.details
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def print_summary(self) -> str:
        """產出摘要報告"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        proceed = "🚀 Can Proceed" if self.can_proceed else "🚫 BLOCKED"
        
        lines = [
            f"{'='*50}",
            f"Phase {self.phase} Enforcement Result",
            f"{'='*50}",
            f"Status: {status}",
            f"Gate Score: {self.gate_score:.2f}%",
            f"Proceed: {proceed}",
            f"",
            f"Structure Check (L1):",
            f"  Score: {self.structure_check.score:.2f}%",
            f"  Missing: {len(self.structure_check.missing)} items",
            f"",
            f"Content Check (L2):",
            f"  Score: {self.content_check.score:.2f}%",
            f"  Missing Sections: {len(self.content_check.missing_sections)} items",
            f"",
            f"Code Quality Check (L3):",
            f"  Score: {self.code_quality_check.score:.2f}%",
            f"  Files Scanned: {self.code_quality_check.files_scanned}",
            f"  Issues Found: {len(self.code_quality_check.issues)}",
            f"",
        ]
        
        if self.blocker_issues:
            lines.append("Blocker Issues:")
            for issue in self.blocker_issues:
                lines.append(f"  🚫 {issue}")
            lines.append("")
        
        lines.append(f"{'='*50}")
        return "\n".join(lines)


class PhaseEnforcer:
    """
    Phase 自動化檢查系統
    
    在每個 Phase 結束時自動觸發檢查，確保產出符合標準。
    整合三層檢查：
    - L1: folder_structure_checker (結構)
    - L2: folder_structure_checker (內容)
    - L3: Agent Quality Guard (代碼品質)
    
    Attributes:
        project_root: 專案根目錄路徑
        strict_mode: 是否啟用嚴格模式（預設 True）
        gate_threshold: 通過閾值（預設 80）
        include_code_quality: 是否包含代碼品質檢查（預設 True）
        weights: 三層檢查的權重 (structure, content, code_quality)，預設 (0.25, 0.25, 0.50)
    """
    
    def __init__(
        self, 
        project_root: str, 
        strict_mode: bool = True,
        gate_threshold: float = 80.0,
        include_code_quality: bool = True,
        weights: Tuple[float, float, float] = (0.25, 0.25, 0.50)
    ):
        self.project_root = Path(project_root)
        self.strict_mode = strict_mode
        self.gate_threshold = gate_threshold
        self.include_code_quality = include_code_quality
        self.weights = weights
        
        # 初始化 folder_structure_checker
        if FOLDER_STRUCTURE_CHECKER_AVAILABLE:
            self.structure_checker = FolderStructureChecker(
                str(self.project_root),
                strict_mode=strict_mode
            )
        else:
            self.structure_checker = None
        
        # 初始化 unified_gate（可選）
        if UNIFIED_GATE_AVAILABLE:
            self.unified_gate = UnifiedGate(str(self.project_root))
        else:
            self.unified_gate = None
    
    def enforce_phase(self, phase: int) -> PhaseEnforcementResult:
        """
        執行 Phase N 的完整檢查
        
        Args:
            phase: Phase 編號 (1-8)
            
        Returns:
            PhaseEnforcementResult: 檢查結果
        """
        # L1: 執行 folder_structure_check (結構)
        structure_result = self._check_structure(phase)
        
        # L2: 執行 content_check (內容)
        content_result = self._check_content(phase)
        
        # L3: 執行代碼品質檢查 (可選)
        if self.include_code_quality:
            code_quality_result = self._check_code_quality(phase)
        else:
            code_quality_result = CodeQualityCheckResult(
                score=100.0,
                files_scanned=0,
                issues=[],
                passed=True,
                details={"skipped": True}
            )
        
        # 計算综合 gate_score
        w_structure, w_content, w_code = self.weights
        gate_score = (
            structure_result.score * w_structure +
            content_result.score * w_content +
            code_quality_result.score * w_code
        )
        
        # 判斷是否通過
        passed = gate_score >= self.gate_threshold
        
        # 判斷是否可以進入下一個 Phase
        can_proceed = passed and len(structure_result.missing) == 0
        
        # 收集 blocker_issues（原有三層檢查）
        blocker_issues = self._collect_blocker_issues(
            structure_result, 
            content_result,
            code_quality_result,
            gate_score
        )
        
        # ===== 2026-03-31 新增：Claims Verification Hook =====
        # 這是 P0 反作弊模組的核心：驗證聲稱 vs 實際
        if CLAIMS_VERIFIER_AVAILABLE:
            try:
                claims_verifier = ClaimsVerifier(str(self.project_root))
                
                # 1. 檢查代碼行數 claim vs actual
                code_check = claims_verifier.verify_code_lines()
                if code_check["claimed"] > 0:
                    if not code_check["match"] and code_check["diff_percent"] > 5:
                        blocker_issues.append(
                            f"CODE LINES mismatch: claimed {code_check['claimed']}, "
                            f"actual {code_check['actual']} ({code_check['diff_percent']:.1f}%)"
                        )
                
                # 2. 檢查 Quality Gate 執行
                qg_check = claims_verifier.verify_quality_gate_executed()
                if not qg_check["executed"]:
                    blocker_issues.append(
                        f"QUALITY GATE not executed"
                    )
                
                # 3. 檢查 STAGE_PASS 存在
                stage_pass = claims_verifier.verify_stage_pass_exists(phase)
                if not stage_pass["exists"]:
                    blocker_issues.append(
                        f"STAGE_PASS not found for Phase {phase}"
                    )
                    
            except Exception as e:
                # 如果 Claims Verifier 出錯，記錄但不阻止流程
                blocker_issues.append(f"Claims verification error: {str(e)}")
        
        # ===== 2026-03-31 新增：A/B Enforcer Hook =====
        # 這是 P0 反作弊模組的核心：驗證 A/B 協作
        if AB_ENFORCER_AVAILABLE:
            try:
                ab_enforcer = ABEnforcer(str(self.project_path))
                phase_str = f"phase_{phase}"
                
                # 3. 檢查 Developer ≠ Reviewer
                separation = ab_enforcer.verify_developer_reviewer_separation(phase_str)
                if not separation["separated"]:
                    blocker_issues.append(
                        f"A/B SEPARATION violation: Developer same as Reviewer"
                    )
                
                # 4. 檢查 A/B 對話存在
                dialogue = ab_enforcer.verify_ab_dialogue_exists(phase_str)
                if not dialogue["has_dialogue"]:
                    blocker_issues.append(
                        f"A/B DIALOGUE missing: no real A/B conversation found"
                    )
                
                # 5. Phase 4 特殊檢查：QA ≠ Developer
                if phase == 4:
                    qa_sep = ab_enforcer.verify_qa_not_developer()
                    if not qa_sep["separated"]:
                        blocker_issues.append(
                            f"QA/DEVELOPER SEPARATION violation: Tester same as Developer"
                        )
                        
            except Exception as e:
                # 如果 A/B Enforcer 出錯，記錄但不阻止流程
                blocker_issues.append(f"A/B enforcement error: {str(e)}")
        
        # 產生結果
        result = PhaseEnforcementResult(
            phase=phase,
            passed=passed,
            structure_check=structure_result,
            content_check=content_result,
            code_quality_check=code_quality_result,
            gate_score=gate_score,
            can_proceed=can_proceed,
            blocker_issues=blocker_issues,
            details={
                "strict_mode": self.strict_mode,
                "gate_threshold": self.gate_threshold,
                "include_code_quality": self.include_code_quality,
                "weights": {
                    "structure": w_structure,
                    "content": w_content,
                    "code_quality": w_code
                },
                "project_root": str(self.project_root)
            }
        )
        
        return result
    
    def can_proceed_to_next_phase(self, current_phase: int) -> bool:
        """
        檢查是否可以進入下一個 Phase
        
        Args:
            current_phase: 當前 Phase 編號
            
        Returns:
            bool: 是否可以進入下一個 Phase
        """
        if current_phase >= 8:
            return True  # 最後一個 Phase
        
        result = self.enforce_phase(current_phase)
        return result.can_proceed
    
    def generate_report(self) -> Dict:
        """
        生成 Phase 執行報告
        
        Returns:
            Dict: 包含所有 Phase 檢查結果的報告
        """
        report = {
            "project_root": str(self.project_root),
            "strict_mode": self.strict_mode,
            "gate_threshold": self.gate_threshold,
            "phases": {},
            "summary": {
                "total_phases": 8,
                "passed_phases": 0,
                "failed_phases": 0,
                "overall_score": 0.0
            }
        }
        
        total_score = 0.0
        passed_count = 0
        
        for phase in range(1, 9):
            result = self.enforce_phase(phase)
            report["phases"][phase] = result.to_dict()
            total_score += result.gate_score
            
            if result.passed:
                passed_count += 1
        
        report["summary"]["passed_phases"] = passed_count
        report["summary"]["failed_phases"] = 8 - passed_count
        report["summary"]["overall_score"] = total_score / 8
        
        return report
    
    def _check_structure(self, phase: int) -> StructureCheckResult:
        """執行結構檢查"""
        if self.structure_checker is None:
            return StructureCheckResult(
                score=100.0,
                missing=[],
                passed=True
            )
        
        result = self.structure_checker.run(phase)
        
        # 收集缺失的目錄和檔案
        missing = []
        if result.missing_dirs:
            missing.extend([f"dir: {d}" for d in result.missing_dirs])
        if result.missing_files:
            missing.extend([f"file: {f}" for f in result.missing_files])
        
        return StructureCheckResult(
            score=result.score,
            missing=missing,
            passed=result.passed
        )
    
    def _check_content(self, phase: int) -> ContentCheckResult:
        """執行內容檢查（strict_mode）"""
        if not self.strict_mode or self.structure_checker is None:
            return ContentCheckResult(
                score=100.0,
                missing_sections=[],
                passed=True
            )
        
        result = self.structure_checker.run(phase)
        
        # 收集缺失的章節
        missing_sections = []
        for cc in result.content_check:
            if not cc.get("passed", True):
                missing_sections.extend(cc.get("missing_sections", []))
        
        # 計算內容分數
        if result.content_check:
            passed_count = sum(1 for cc in result.content_check if cc.get("passed", True))
            total_count = len(result.content_check)
            score = (passed_count / total_count) * 100
        else:
            score = 100.0
        
        passed = len(missing_sections) == 0
        
        return ContentCheckResult(
            score=score,
            missing_sections=missing_sections,
            passed=passed
        )
    
    def _check_code_quality(self, phase: int) -> CodeQualityCheckResult:
        """執行代碼品質檢查（L3）"""
        if not AGENT_QUALITY_GUARD_AVAILABLE:
            # Fallback: 本地基本代碼品質檢查（不依賴外部套件）
            scan_dir = self.project_root / "src"
            if not scan_dir.exists():
                scan_dir = self.project_root / "03-development"
            if not scan_dir.exists():
                return CodeQualityCheckResult(
                    score=100.0,
                    files_scanned=0,
                    issues=[],
                    passed=True,
                    details={"status": "skipped", "reason": "No source directory found"}
                )
            py_files = list(scan_dir.rglob("*.py"))
            py_files = [f for f in py_files if "__pycache__" not in str(f)]
            if not py_files:
                return CodeQualityCheckResult(
                    score=100.0,
                    files_scanned=0,
                    issues=[],
                    passed=True,
                    details={"status": "skipped", "reason": "No Python files found"}
                )
            all_issues = []
            total_score = 0.0
            for py_file in py_files:
                try:
                    content = py_file.read_text(errors="ignore")
                    file_issues = []
                    # 1. 檢查 docstring
                    if '"""' not in content and "'''" not in content:
                        file_issues.append({
                            "type": "missing_docstring",
                            "severity": "low",
                            "file": str(py_file.relative_to(scan_dir)),
                            "message": "Module missing docstring"
                        })
                    # 2. 檢查 type hints
                    if "def " in content:
                        func_defs = len([l for l in content.split('\n') if 'def ' in l])
                        type_hints = len([l for l in content.split('\n') if ': ' in l and ('str' in l or 'int' in l or 'bool' in l or 'List' in l)])
                        if func_defs > 0 and type_hints == 0:
                            file_issues.append({
                                "type": "no_type_hints",
                                "severity": "low",
                                "file": str(py_file.relative_to(scan_dir)),
                                "message": "No type hints found"
                            })
                    # 3. 檢查錯誤處理
                    if 'try:' in content and 'except' not in content:
                        file_issues.append({
                            "type": "missing_error_handling",
                            "severity": "medium",
                            "file": str(py_file.relative_to(scan_dir)),
                            "message": "try block without except"
                        })
                    # 4. 檢查過長函數（>100行）
                    lines = content.split('\n')
                    in_func = False
                    func_line_count = 0
                    for line in lines:
                        if 'def ' in line:
                            in_func = True
                            func_line_count = 0
                        elif in_func:
                            func_line_count += 1
                            if func_line_count > 100:
                                file_issues.append({
                                    "type": "function_too_long",
                                    "severity": "medium",
                                    "file": str(py_file.relative_to(scan_dir)),
                                    "message": f"Function > 100 lines ({func_line_count} lines)"
                                })
                                break
                    # 5. 檢查 TODO/FIXME
                    if 'TODO' in content or 'FIXME' in content:
                        file_issues.append({
                            "type": "has_todo",
                            "severity": "info",
                            "file": str(py_file.relative_to(scan_dir)),
                            "message": "Contains TODO or FIXME"
                        })
                    # 計算檔案分數
                    if file_issues:
                        severity_weights = {"high": 10, "medium": 5, "low": 2, "info": 0}
                        deductions = sum(severity_weights.get(i["severity"], 0) for i in file_issues)
                        file_score = max(0, 100 - deductions)
                    else:
                        file_score = 100
                    total_score += file_score
                    all_issues.extend(file_issues)
                except Exception:
                    pass
            avg_score = total_score / len(py_files) if py_files else 100
            passed = avg_score >= 90
            return CodeQualityCheckResult(
                score=avg_score,
                files_scanned=len(py_files),
                issues=all_issues,
                passed=passed,
                details={
                    "status": "local_check",
                    "agent_guard_used": AGENT_QUALITY_GUARD_AVAILABLE
                }
            )
        
        # 根據 Phase 決定要掃描的目錄
        # Phase 1-3: 03-development/ 目錄有代碼
        # Phase 4-8: 可能需要掃描更多目錄
        scan_dir = self.project_root / "03-development"
        
        if not scan_dir.exists():
            return CodeQualityCheckResult(
                score=100.0,
                files_scanned=0,
                issues=[],
                passed=True,
                details={"status": "skipped", "reason": "03-development directory not found"}
            )
        
        # 掃描所有 Python 檔案
        py_files = list(scan_dir.rglob("*.py"))
        
        if not py_files:
            return CodeQualityCheckResult(
                score=100.0,
                files_scanned=0,
                issues=[],
                passed=True,
                details={"status": "skipped", "reason": "No Python files found"}
            )
        
        all_issues = []
        total_score = 0.0
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                if not code.strip():
                    continue
                
                # 使用 Agent Quality Guard 分析
                result = score_from_code(code)
                
                # 收集 issues
                for issue in result.get("issues", []):
                    all_issues.append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "line": issue.get("line"),
                        "issue": issue.get("type"),
                        "severity": issue.get("severity"),
                        "message": issue.get("message")
                    })
                
                total_score += result.get("score", 100)
                
            except Exception as e:
                # 如果分析失敗，給予該檔案 100 分
                total_score += 100
        
        # 計算平均分數
        files_scanned = len(py_files)
        avg_score = total_score / files_scanned if files_scanned > 0 else 100.0
        
        # 判斷是否通過（高嚴重性問題少於 5 個）
        high_issues = [i for i in all_issues if i.get("severity") == "high"]
        passed = len(high_issues) < 5
        
        return CodeQualityCheckResult(
            score=avg_score,
            files_scanned=files_scanned,
            issues=all_issues,
            passed=passed,
            details={
                "high_issues_count": len(high_issues),
                "medium_issues_count": len([i for i in all_issues if i.get("severity") == "medium"]),
                "low_issues_count": len([i for i in all_issues if i.get("severity") == "low"]),
                "scan_directory": str(scan_dir.relative_to(self.project_root))
            }
        )
    
    def _collect_blocker_issues(
        self, 
        structure: StructureCheckResult,
        content: ContentCheckResult,
        code_quality: CodeQualityCheckResult,
        gate_score: float
    ) -> List[str]:
        """收集 blocker 問題"""
        issues = []
        
        # 結構問題
        if structure.missing:
            for m in structure.missing[:5]:  # 最多顯示 5 個
                issues.append(f"Missing: {m}")
        
        # 內容問題
        if content.missing_sections:
            for ms in content.missing_sections[:5]:
                issues.append(f"Missing section: {ms}")
        
        # 代碼品質問題
        if code_quality.details.get("high_issues_count", 0) >= 5:
            issues.append(f"Too many high severity code issues: {code_quality.details.get('high_issues_count')}")
        
        # 分數不足
        if gate_score < self.gate_threshold:
            issues.append(f"Gate score {gate_score:.2f}% < threshold {self.gate_threshold}%")
        
        return issues
    
    def enforce_with_unified_gate(self, phase: int) -> Dict:
        """
        執行 Phase 檢查（整合 unified_gate）
        
        Args:
            phase: Phase 編號 (1-8)
            
        Returns:
            Dict: 整合檢查結果
        """
        # 1. 執行 PhaseEnforcer 檢查
        enforcement_result = self.enforce_phase(phase)
        
        # 2. 執行 unified_gate 檢查（可選）
        unified_result = None
        if self.unified_gate is not None:
            try:
                unified_result = self.unified_gate.check_all(phase=phase)
            except Exception as e:
                unified_result = None
        
        # 3. 整合結果
        combined_result = {
            "phase": phase,
            "enforcement": enforcement_result.to_dict(),
            "unified_gate": unified_result.to_dict() if unified_result else None,
            "combined_passed": enforcement_result.passed and (
                unified_result.passed if unified_result else True
            ),
            "combined_score": (
                (enforcement_result.gate_score + unified_result.overall_score) / 2
                if unified_result else enforcement_result.gate_score
            )
        }
        
        return combined_result


# ===== 快速函式入口 =====

def enforce_phase(project_root: str, phase: int, strict_mode: bool = True) -> PhaseEnforcementResult:
    """
    快速執行 Phase 檢查
    
    Args:
        project_root: 專案根目錄路徑
        phase: Phase 編號 (1-8)
        strict_mode: 是否啟用嚴格模式
        
    Returns:
        PhaseEnforcementResult: 檢查結果
    """
    enforcer = PhaseEnforcer(project_root, strict_mode=strict_mode)
    return enforcer.enforce_phase(phase)


def check_can_proceed(project_root: str, current_phase: int) -> bool:
    """
    快速檢查是否可以進入下一個 Phase
    
    Args:
        project_root: 專案根目錄路徑
        current_phase: 當前 Phase 編號
        
    Returns:
        bool: 是否可以進入下一個 Phase
    """
    enforcer = PhaseEnforcer(project_root)
    return enforcer.can_proceed_to_next_phase(current_phase)


def generate_full_report(project_root: str) -> Dict:
    """
    生成完整 Phase 報告
    
    Args:
        project_root: 專案根目錄路徑
        
    Returns:
        Dict: 完整報告
    """
    enforcer = PhaseEnforcer(project_root)
    return enforcer.generate_report()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python phase_enforcer.py <project_root> <phase> [--strict]")
        sys.exit(1)
    
    project_root = sys.argv[1]
    phase = int(sys.argv[2])
    strict_mode = "--strict" in sys.argv
    
    result = enforce_phase(project_root, phase, strict_mode=strict_mode)
    print(result.print_summary())
    
    # 如果有 blocker_issues，退出碼為 1
    if result.blocker_issues:
        sys.exit(1)