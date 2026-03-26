#!/usr/bin/env python3
"""
Framework Enforcement Engine
===========================
讀取 SKILL.md 的 enforcement 定義並執行

使用方法：
    from enforcement.framework_enforcer import FrameworkEnforcer
    
    enforcer = FrameworkEnforcer("/path/to/project")
    result = enforcer.run()
    
    if not result.passed:
        for msg, fix in result.violations:
            print(f"🔴 {msg}")
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Import existing enforcement components
from enforcement import PolicyEngine, ConstitutionAsCode, EnforcementLevel
from enforcement.execution_registry import ExecutionRegistry


class EnforcementResult:
    """Enforcement 結果容器"""
    
    def __init__(self):
        self.violations: List[Tuple[str, Optional[str]]] = []  # (message, fix_command)
        self.warnings: List[Tuple[str, Optional[str]]] = []
        self.passed = False
        self.block_checks: Dict[str, bool] = {}
        self.warn_checks: Dict[str, bool] = {}
    
    def add_violation(self, message: str, fix: str = None):
        """新增 BLOCK 等級違規"""
        self.violations.append((message, fix))
    
    def add_warning(self, message: str, fix: str = None):
        """新增 WARN 等級警告"""
        self.warnings.append((message, fix))
    
    def add_block_check(self, name: str, passed: bool):
        """記錄 BLOCK 檢查結果"""
        self.block_checks[name] = passed
    
    def add_warn_check(self, name: str, passed: bool):
        """記錄 WARN 檢查結果"""
        self.warn_checks[name] = passed
    
    def summary(self) -> str:
        """生成摘要文字"""
        lines = []
        lines.append(f"Passed: {self.passed}")
        lines.append(f"BLOCK Violations: {len(self.violations)}")
        lines.append(f"WARN Warnings: {len(self.warnings)}")
        return "\n".join(lines)


class FrameworkEnforcer:
    """
    Framework Enforcement 引擎
    
    根據 SKILL.md 定義的 enforcement 規則執行檢查。
    
    BLOCK 等級（必須通過，否則阻擋）：
    - SPEC_TRACKING: 規格追蹤完整性 >= 90%
    - CONSTITUTION_SCORE: Constitution Score >= 60
    
    WARN 等級（警告，不阻擋）：
    - DECISION_FRAMEWORK: Decision Framework 已建立
    - ENHANCED_CHECKLIST: 增強檢查清單已建立
    """
    
    # BLOCK 等級檢查門檻
    BLOCK_CHECKS = [
        {"name": "SPEC_TRACKING", "threshold": 90},
        {"name": "CONSTITUTION_SCORE", "threshold": 60},
    ]
    
    # WARN 等級檢查
    WARN_CHECKS = [
        {"name": "DECISION_FRAMEWORK"},
        {"name": "ENHANCED_CHECKLIST"},
    ]
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._spec_checker = None
    
    @property
    def spec_checker(self):
        """延遲載入 SpecTrackingChecker"""
        if self._spec_checker is None:
            from quality_gate.spec_tracking_checker import SpecTrackingChecker
            self._spec_checker = SpecTrackingChecker(str(self.project_root))
        return self._spec_checker
    
    def check_spec_tracking(self) -> Dict:
        """
        檢查 SPEC_TRACKING
        
        Returns:
            Dict with keys: exists, completeness, complete, missing
        """
        return self.spec_checker.run_enforcement()
    
    def check_constitution(self) -> Dict:
        """
        檢查 Constitution Score
        
        Returns:
            Dict with keys: score, passed
        """
        try:
            from quality_gate.constitution.runner import run_constitution_check
            
            docs_path = self.project_root / "docs"
            if not docs_path.exists():
                return {"score": 0, "passed": False, "error": "docs/ not found"}
            
            result = run_constitution_check("all", str(docs_path))
            return {
                "score": result.score,
                "passed": result.passed,
                "violations": len(result.violations) if hasattr(result, 'violations') else 0
            }
        except Exception as e:
            return {"score": 0, "passed": False, "error": str(e)}
    
    def check_decision_framework(self) -> Dict:
        """檢查 Decision Framework 是否存在"""
        framework_file = self.project_root / "DECISION_FRAMEWORK.md"
        return {
            "exists": framework_file.exists(),
            "path": str(framework_file)
        }
    
    def check_enhanced_checklist(self) -> Dict:
        """檢查 Enhanced Checklist 是否存在"""
        checklist_file = self.project_root / "CHECKLIST.md"
        return {
            "exists": checklist_file.exists(),
            "path": str(checklist_file)
        }
    
    def check_traceability_matrix(self) -> Dict:
        """
        檢查 TRACEABILITY_MATRIX.md 完整性
        
        Returns:
            Dict with keys: exists, complete, completeness, missing_tests, missing_constitution
        """
        from pathlib import Path
        
        trace_file = self.project_root / "TRACEABILITY_MATRIX.md"
        if not trace_file.exists():
            return {
                "exists": False, 
                "complete": False, 
                "completeness": 0,
                "missing_tests": [],
                "missing_constitution": []
            }
        
        content = trace_file.read_text()
        lines = content.split("\n")
        
        missing_tests = []
        missing_constitution = []
        completed = 0
        total = 0
        
        for line in lines:
            if "src/" in line or ".py" in line:
                total += 1
                # 檢查是否有測試
                if "test_" not in line and "| ✅ |" not in line:
                    # 實作了但狀態不是已完成
                    pass
                # 檢查 Constitution 欄位
                if "❌" in line or "⚠️" in line:
                    missing_constitution.append(line)
                if "✅" in line:
                    completed += 1
        
        completeness = (completed / total * 100) if total > 0 else 0
        complete = completeness >= 90 and len(missing_tests) == 0
        
        return {
            "exists": True,
            "complete": complete,
            "completeness": completeness,
            "total": total,
            "completed": completed,
            "missing_tests": missing_tests,
            "missing_constitution": missing_constitution
        }
    
    def check_phase_traceability(self) -> Dict:
        """
        檢查 Phase 間追溯性（ASPICE 要求）
        
        驗證：
        - Phase 2 是否有引用 Phase 1 的產物
        - Phase 3 是否有引用 Phase 2 的產物
        - ...
        
        Returns:
            Dict with keys: all_verified, verified_phases, missing_links
        """
        from quality_gate.phase_artifact_enforcer import PhaseArtifactRegistry, Phase
        
        registry = PhaseArtifactRegistry(str(self.project_root))
        
        # 驗證所有 Phase 間的引用
        verified = []
        missing = []
        
        for phase in Phase:
            config = PhaseArtifactRegistry.PHASE_ARTIFACTS.get(phase, {})
            depends_on = config.get("depends_on", [])
            
            for prev_phase in depends_on:
                # 檢查是否有引用上一個 Phase 的產物
                ref_check = registry.verify_phase_link(prev_phase, phase)
                if ref_check.passed:
                    verified.append(f"{prev_phase.value} → {phase.value}")
                else:
                    missing.append(f"{prev_phase.value} → {phase.value}")
        
        return {
            "all_verified": len(missing) == 0,
            "verified_phases": verified,
            "missing_links": missing,
            "stats": {
                "total": len(verified) + len(missing),
                "verified": len(verified),
                "missing": len(missing)
            }
        }
    
    def check_aspice_completeness(self) -> Dict:
        """
        檢查 ASPICE 8 階段文檔完整性
        
        ASPICE 要求每個 Phase 有對應文檔：
        - Phase 1: SRS.md (Software Requirements Specification)
        - Phase 2: SAD.md (Software Architecture Description)
        - Phase 3: IMPLEMENTATION.md
        - Phase 4: TEST_PLAN.md, TEST_RESULTS.md
        - Phase 5: BASELINE.md
        - Phase 6: QUALITY_REPORT.md
        - Phase 7: RISK_ASSESSMENT.md, RISK_REGISTER.md
        - Phase 8: CONFIG_RECORDS.md
        
        Returns:
            Dict with keys: complete, missing_docs, phase_coverage
        """
        docs_path = self.project_root / "docs"
        
        required_by_phase = {
            "Phase 1": ["SRS.md", "SPEC.md"],
            "Phase 2": ["SAD.md", "ARCHITECTURE.md"],
            "Phase 3": ["IMPLEMENTATION.md"],
            "Phase 4": ["TEST_PLAN.md", "TEST_RESULTS.md"],
            "Phase 5": ["BASELINE.md"],
            "Phase 6": ["QUALITY_REPORT.md"],
            "Phase 7": ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
            "Phase 8": ["CONFIG_RECORDS.md"],
        }
        
        missing = []
        found = []
        
        for phase, docs in required_by_phase.items():
            for doc in docs:
                doc_path = docs_path / doc
                if doc_path.exists():
                    found.append(f"{phase}/{doc}")
                else:
                    # 也檢查根目錄
                    root_path = self.project_root / doc
                    if root_path.exists():
                        found.append(f"{phase}/{doc} (root)")
                    else:
                        missing.append(f"{phase}/{doc}")
        
        return {
            "complete": len(missing) == 0,
            "missing_docs": missing,
            "phase_coverage": {
                "total_phases": 8,
                "phases_with_docs": 8 - len(set([m.split("/")[0] for m in missing])),
                "total_docs": sum(len(d) for d in required_by_phase.values()),
                "found": len(found)
            }
        }
    
    def generate_aspice_report(self) -> str:
        """
        生成 ASPICE 追溯報告
        
        報告內容：
        1. Phase 間追溯鏈
        2. ASPICE 文檔完整性
        3. Constitution 分數
        4. 規格追蹤狀態
        
        Returns:
            str: 格式化的報告
        """
        lines = []
        lines.append("=" * 60)
        lines.append("ASPICE TRACEABILITY REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Phase 間追溯
        trace = self.check_phase_traceability()
        lines.append("## Phase Traceability")
        lines.append(f"Total Links: {trace['stats']['total']}")
        lines.append(f"Verified: {trace['stats']['verified']}")
        lines.append(f"Missing: {trace['stats']['missing']}")
        lines.append("")
        lines.append("### Verified Links")
        for link in trace['verified_phases']:
            lines.append(f"  ✅ {link}")
        lines.append("")
        lines.append("### Missing Links")
        if trace['missing_links']:
            for link in trace['missing_links']:
                lines.append(f"  ❌ {link}")
        else:
            lines.append("  (none)")
        lines.append("")
        
        # ASPICE 文檔完整性
        aspice = self.check_aspice_completeness()
        lines.append("## ASPICE Document Completeness")
        lines.append(f"Coverage: {aspice['phase_coverage']['found']}/{aspice['phase_coverage']['total_docs']} docs")
        lines.append(f"Phases: {aspice['phase_coverage']['phases_with_docs']}/{aspice['phase_coverage']['total_phases']}")
        lines.append("")
        if aspice['missing_docs']:
            lines.append("### Missing Documents")
            for doc in aspice['missing_docs']:
                lines.append(f"  ❌ {doc}")
        lines.append("")
        
        # Constitution Score
        const = self.check_constitution()
        lines.append("## Constitution Score")
        lines.append(f"Score: {const.get('score', 0)}%")
        lines.append(f"Threshold: 60%")
        lines.append(f"Status: {'✅ PASS' if const.get('passed') else '❌ FAIL'}")
        lines.append("")
        
        # SPEC Tracking
        spec = self.check_spec_tracking()
        lines.append("## Specification Tracking")
        lines.append(f"Completeness: {spec.get('completeness', 0)}%")
        lines.append(f"Threshold: 90%")
        lines.append(f"Status: {'✅ PASS' if spec.get('complete') else '❌ FAIL'}")
        lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def run(self, level: str = "ALL") -> EnforcementResult:
        """
        執行 Enforcement
        
        Args:
            level: "BLOCK" | "WARN" | "ALL"
        
        Returns:
            EnforcementResult
        """
        result = EnforcementResult()
        
        # BLOCK 檢查
        if level in ["BLOCK", "ALL"]:
            # 1. SPEC_TRACKING
            spec = self.check_spec_tracking()
            spec_passed = (
                spec.get('exists', False) and 
                spec.get('completeness', 0) >= 90
            )
            result.add_block_check("SPEC_TRACKING", spec_passed)
            
            if not spec.get('exists', False):
                result.add_violation(
                    "SPEC_TRACKING.md 不存在",
                    "methodology spec-track init"
                )
            elif spec.get('completeness', 0) < 90:
                result.add_violation(
                    f"規格完整性 {spec['completeness']}% < 90%",
                    None
                )
            
            # 2. Constitution Score
            const = self.check_constitution()
            const_passed = const.get('score', 0) >= 60
            result.add_block_check("CONSTITUTION_SCORE", const_passed)
            
            if not const_passed:
                result.add_violation(
                    f"Constitution Score {const.get('score', 0)}% < 60%",
                    "methodology constitution check"
                )
            
            # 3. ASPICE Phase Traceability
            trace = self.check_phase_traceability()
            trace_passed = trace['all_verified']
            result.add_block_check("ASPICE_PHASE_TRACE", trace_passed)
            
            if not trace_passed:
                result.add_violation(
                    f"ASPICE Phase 追溯性未完成: {', '.join(trace['missing_links'])}",
                    "請確保每個 Phase 引用上一個 Phase 的產物"
                )
            
            # 4. ASPICE Document Completeness
            aspice = self.check_aspice_completeness()
            aspice_passed = aspice['complete']
            result.add_block_check("ASPICE_COMPLETE", aspice_passed)
            
            if not aspice_passed:
                result.add_violation(
                    f"ASPICE 文檔缺失: {', '.join(aspice['missing_docs'][:3])}",
                    "請補齊所有 Phase 的文檔"
                )
            
            # 5. TRACEABILITY Matrix
            trace = self.check_traceability_matrix()
            trace_passed = trace['complete']
            result.add_block_check("TRACEABILITY_COMPLETE", trace_passed)
            
            if not trace.get('exists', False):
                result.add_violation(
                    "TRACEABILITY_MATRIX.md 不存在",
                    "methodology trace init"
                )
            elif not trace_passed:
                missing = []
                if trace.get('missing_tests'):
                    missing.append(f"{len(trace['missing_tests'])} 項缺少測試")
                if trace.get('missing_constitution'):
                    missing.append(f"{len(trace['missing_constitution'])} 項 Constitution 未通過")
                result.add_violation(
                    f"TRACEABILITY 不完整: {', '.join(missing)}",
                    "methodology trace check"
                )
        
        # WARN 檢查
        if level in ["WARN", "ALL"]:
            # Decision Framework
            df = self.check_decision_framework()
            result.add_warn_check("DECISION_FRAMEWORK", df['exists'])
            if not df['exists']:
                result.add_warning(
                    "Decision Framework 未建立",
                    "建議建立 DECISION_FRAMEWORK.md"
                )
            
            # Enhanced Checklist
            cl = self.check_enhanced_checklist()
            result.add_warn_check("ENHANCED_CHECKLIST", cl['exists'])
            if not cl['exists']:
                result.add_warning(
                    "Enhanced Checklist 未建立",
                    "建議建立 CHECKLIST.md"
                )
        
        result.passed = len(result.violations) == 0
        return result
    
    def run_with_exit(self, level: str = "ALL") -> int:
        """
        執行 Enforcement並根據結果sys.exit
        
        Returns:
            exit code (0 = passed, 1 = failed)
        """
        result = self.run(level)
        
        print("=" * 50)
        print(f"Framework Enforcement - {level}")
        print("=" * 50)
        
        print("\n🔴 BLOCK Violations:")
        if result.violations:
            for msg, fix in result.violations:
                print(f"   🔴 {msg}")
                if fix:
                    print(f"      請執行: {fix}")
        else:
            print("   ✅ 無 BLOCK 違規")
        
        print("\n🟡 Warnings:")
        if result.warnings:
            for msg, fix in result.warnings:
                print(f"   🟡 {msg}")
                if fix:
                    print(f"      {fix}")
        else:
            print("   ✅ 無警告")
        
        if result.passed:
            print("\n✅ Framework Enforcement 通過")
        else:
            print("\n❌ Framework Enforcement 失敗")
        
        return 0 if result.passed else 1


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Framework Enforcement")
    parser.add_argument("--level", "-l", choices=["BLOCK", "WARN", "ALL"], 
                       default="ALL", help="Enforcement level")
    parser.add_argument("--project", "-p", default=".", help="Project root path")
    parser.add_argument("--exit", "-x", action="store_true", 
                       help="Exit with code based on result")
    
    args = parser.parse_args()
    
    enforcer = FrameworkEnforcer(args.project)
    
    if args.exit:
        sys.exit(enforcer.run_with_exit(args.level))
    else:
        result = enforcer.run(args.level)
        print(result.summary())
        sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    sys.exit(main())
