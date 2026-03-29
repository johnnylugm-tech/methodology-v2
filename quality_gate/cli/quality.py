#!/usr/bin/env python3
"""
Quality CLI - 命令列介面
=======================
提供 Phase 檢查的 CLI 介面。

使用方式：
    python -m quality_gate.cli quality check-phase 1
    python -m quality_gate.cli quality check-phase 2 --strict
    python -m quality_gate.cli quality check-all
    python -m quality_gate.cli quality check-phase 3 --block
"""

import sys
import json
import argparse
from pathlib import Path

# 將專案根目錄加入路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 匯入檢查器
try:
    from quality_gate.phase_enforcer import PhaseEnforcer, enforce_phase
    from quality_gate.unified_gate import UnifiedGate
except ImportError as e:
    print(f"Error: Cannot import quality_gate modules: {e}")
    sys.exit(1)


class QualityCLI:
    """Quality CLI 主類別"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
    
    def check_phase(
        self, 
        phase: int, 
        strict: bool = False, 
        block: bool = False,
        use_unified: bool = False
    ) -> int:
        """
        檢查指定 Phase
        
        Args:
            phase: Phase 編號 (1-8)
            strict: 是否啟用嚴格模式
            block: 失敗時是否阻擋
            use_unified: 是否使用 unified_gate
            
        Returns:
            int: 退出碼（0=成功，1=失敗）
        """
        print(f"\n🔍 Checking Phase {phase}...")
        print(f"   Strict Mode: {strict}")
        print(f"   Block on Failure: {block}")
        print(f"   Use Unified Gate: {use_unified}")
        print()
        
        if use_unified:
            result = self._check_with_unified(phase, strict)
        else:
            result = self._check_with_enforcer(phase, strict)
        
        # 輸出結果
        self._print_result(result)
        
        # 如果是 block 模式且失敗，退出
        if block and not result["passed"]:
            print("\n🚫 BLOCKED: Phase enforcement failed!")
            return 1
        
        return 0 if result["passed"] else 1
    
    def _check_with_enforcer(self, phase: int, strict: bool) -> dict:
        """使用 PhaseEnforcer 檢查"""
        enforcer = PhaseEnforcer(
            str(self.project_root),
            strict_mode=strict
        )
        result = enforcer.enforce_phase(phase)
        return result.to_dict()
    
    def _check_with_unified(self, phase: int, strict: bool) -> dict:
        """使用 UnifiedGate 檢查"""
        gate = UnifiedGate(str(self.project_root))
        result = gate.check_all(phase=phase, strict_mode=strict, phase_enforcement=True)
        return result.to_dict()
    
    def check_all(self, strict: bool = False) -> int:
        """
        檢查所有 Phase
        
        Returns:
            int: 退出碼（0=成功，1=失敗）
        """
        print("\n🔍 Checking All Phases...")
        print(f"   Strict Mode: {strict}")
        print()
        
        enforcer = PhaseEnforcer(str(self.project_root), strict_mode=strict)
        report = enforcer.generate_report()
        
        # 輸出報告
        self._print_full_report(report)
        
        # 返回結果
        passed_phases = report["summary"]["passed_phases"]
        failed_phases = report["summary"]["failed_phases"]
        
        print(f"\n📊 Summary:")
        print(f"   Passed: {passed_phases}/8")
        print(f"   Failed: {failed_phases}/8")
        print(f"   Overall Score: {report['summary']['overall_score']:.2f}%")
        
        return 0 if failed_phases == 0 else 1
    
    def _print_result(self, result: dict):
        """輸出檢查結果"""
        phase = result["phase"]
        passed = result["passed"]
        gate_score = result["gate_score"]
        can_proceed = result["can_proceed"]
        blockers = result.get("blocker_issues", [])
        
        # 狀態emoji
        status = "✅ PASS" if passed else "❌ FAIL"
        proceed = "🚀 Can Proceed" if can_proceed else "🚫 BLOCKED"
        
        print(f"{'='*60}")
        print(f"Phase {phase} Enforcement Result")
        print(f"{'='*60}")
        print(f"Status:      {status}")
        print(f"Gate Score:  {gate_score:.2f}%")
        print(f"Proceed:     {proceed}")
        print()
        
        # Structure Check
        sc = result.get("structure_check", {})
        print(f"Structure Check:")
        print(f"  Score:   {sc.get('score', 0):.2f}%")
        missing_dirs = [m for m in sc.get('missing', []) if m.startswith('dir:')]
        missing_files = [m for m in sc.get('missing', []) if m.startswith('file:')]
        if missing_dirs:
            print(f"  Missing Dirs: {len(missing_dirs)}")
            for m in missing_dirs[:3]:
                print(f"    - {m}")
        if missing_files:
            print(f"  Missing Files: {len(missing_files)}")
            for m in missing_files[:3]:
                print(f"    - {m}")
        print()
        
        # Content Check
        cc = result.get("content_check", {})
        print(f"Content Check:")
        print(f"  Score:           {cc.get('score', 0):.2f}%")
        missing_sections = cc.get('missing_sections', [])
        if missing_sections:
            print(f"  Missing Sections: {len(missing_sections)}")
            for ms in missing_sections[:5]:
                print(f"    - {ms}")
        print()
        
        # Blocker Issues
        if blockers:
            print(f"Blocker Issues ({len(blockers)}):")
            for issue in blockers[:10]:
                print(f"  🚫 {issue}")
            print()
        
        print(f"{'='*60}")
    
    def _print_full_report(self, report: dict):
        """輸出完整報告"""
        phases = report.get("phases", {})
        
        print(f"{'='*60}")
        print("Phase Enforcement Full Report")
        print(f"{'='*60}")
        print()
        
        for phase_num in range(1, 9):
            if phase_num in phases:
                p = phases[phase_num]
                passed = p["passed"]
                score = p["gate_score"]
                status = "✅" if passed else "❌"
                
                print(f"Phase {phase_num}: {status} ({score:.2f}%)")
        
        print()
        print(f"{'='*60}")


def main():
    """主程式入口"""
    # 預處理：處理 "quality" 作為第一個子命令的情況
    # 例如：python -m quality_gate.cli quality check-phase 1
    if len(sys.argv) > 1 and sys.argv[1] == "quality":
        sys.argv.pop(1)  # 移除 "quality"
    
    parser = argparse.ArgumentParser(
        description="Quality Gate CLI - Phase Enforcement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check specific phase
  python -m quality_gate.cli quality check-phase 1
  python -m quality_gate.cli check-phase 1
  
  # Strict mode check
  python -m quality_gate.cli quality check-phase 2 --strict
  python -m quality_gate.cli check-phase 2 --strict
  
  # Check all phases
  python -m quality_gate.cli quality check-all
  python -m quality_gate.cli check-all
  
  # Block mode (exit on failure)
  python -m quality_gate.cli quality check-phase 3 --block
  
  # Use unified gate
  python -m quality_gate.cli quality check-phase 4 --unified
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # quality check-phase
    check_phase_parser = subparsers.add_parser("check-phase", help="Check specific phase")
    check_phase_parser.add_argument("phase", type=int, help="Phase number (1-8)")
    check_phase_parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    check_phase_parser.add_argument("--block", action="store_true", help="Exit on failure")
    check_phase_parser.add_argument("--unified", action="store_true", help="Use unified gate")
    
    # quality check-all
    check_all_parser = subparsers.add_parser("check-all", help="Check all phases")
    check_all_parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    
    # quality check (alternative to check-phase)
    check_parser = subparsers.add_parser("check", help="Check specific phase (alias)")
    check_parser.add_argument("phase", type=int, help="Phase number (1-8)")
    check_parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    check_parser.add_argument("--block", action="store_true", help="Exit on failure")
    check_parser.add_argument("--unified", action="store_true", help="Use unified gate")
    
    # Parse arguments
    args = parser.parse_args()
    
    # 預設專案根目錄（從 CLI 位置推斷）
    cli_dir = Path(__file__).parent
    project_root = cli_dir.parent.parent
    
    # 建立 CLI
    cli = QualityCLI(str(project_root))
    
    # 執行命令
    if args.command == "check-phase" or args.command == "check":
        return cli.check_phase(
            phase=args.phase,
            strict=args.strict,
            block=args.block,
            use_unified=args.unified
        )
    elif args.command == "check-all":
        return cli.check_all(strict=args.strict)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())