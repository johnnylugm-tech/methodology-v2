#!/usr/bin/env python3
"""
Check FR Full - 每個 FR 完成後的完整檢查
==========================================

用途：每個 FR Reviewer APPROVE 後，執行完整檢查

使用方式：
    # 完整檢查（推薦）
    python scripts/check_fr_full.py --fr FR-01

    # 迭代檢查
    python scripts/check_fr_full.py --fr FR-01 --loop

檢查內容（三層）：
    1. 輕量：Syntax + Import（~30秒）
    2. Constitution：BVS + HR-09（~1分鐘）
    3. CQG：Linter + Complexity（~1分鐘）

Pass 條件：
    - 輕量：無 Error
    - Constitution：無 BLOCK（Warning 可接受）
    - CQG：無 Error（Warning 可接受）
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_check(name: str, cmd: list, project: str) -> tuple:
    """執行檢查命令"""
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分鐘超時
            cwd=project
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        
        if passed:
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
            print(output[-500:] if len(output) > 500 else output)  # 最後 500 字
        
        return passed, output
    except subprocess.TimeoutExpired:
        print(f"❌ {name}: TIMEOUT (>5min)")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="每個 FR 的完整品質檢查")
    parser.add_argument("--fr", required=True, help="FR ID (e.g., FR-01)")
    parser.add_argument("--project", default=".", help="專案路徑")
    parser.add_argument("--loop", action="store_true", help="Loop until PASS")
    parser.add_argument("--max-loops", type=int, default=10, help="Max loop count")
    parser.add_argument("--skip-constitution", action="store_true", help="Skip Constitution check")
    parser.add_argument("--skip-cqg", action="store_true", help="Skip CQG check")
    args = parser.parse_args()
    
    project = str(Path(args.project).resolve())
    fr_id = args.fr
    
    loop_count = 0
    while True:
        loop_count += 1
        print(f"\n{'#'*60}")
        print(f"# FR Full Check: {fr_id} (loop {loop_count}/{args.max_loops})")
        print(f"{'#'*60}")
        
        all_passed = True
        
        # Layer 1: 輕量檢查（必須）
        passed, _ = run_check(
            "Layer 1: Syntax + Import",
            ["python3", "scripts/check_fr_quality.py", "--fr", fr_id, "--project", project],
            project
        )
        if not passed:
            all_passed = False
        
        # Layer 2: Constitution（可選）
        if not args.skip_constitution:
            passed, _ = run_check(
                "Layer 2: Constitution (BVS + HR-09)",
                ["python3", "-m", "quality_gate.constitution.runner", "--type", "implementation"],
                project
            )
            if not passed:
                all_passed = False
        
        # Layer 3: CQG（可選）
        if not args.skip_cqg:
            passed, _ = run_check(
                "Layer 3: CQG (Linter + Complexity)",
                ["python3", "-m", "cli", "quality-gate", "--phase", "3"],
                project
            )
            if not passed:
                all_passed = False
        
        # 結果
        print(f"\n{'='*60}")
        if all_passed:
            print(f"✅ ALL CHECKS PASSED for {fr_id}")
            return 0
        else:
            print(f"❌ SOME CHECKS FAILED for {fr_id}")
            
            if args.loop and loop_count < args.max_loops:
                print(f"\n🔧 修復問題後，按 Enter 繼續... (Ctrl+C 退出)")
                try:
                    input()
                except (KeyboardInterrupt, EOFError):
                    print("\n❌ 退出")
                    return 1
                continue
            return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
