#!/usr/bin/env python3
"""
Check FR Full - 每個 FR 完成後的完整檢查
==========================================

用途：每個 FR Reviewer APPROVE 後，執行完整檢查

使用方式：
    # 完整檢查（推薦）
    python scripts/check_fr_full.py --fr FR-01 --project /path/to/project

    # 迭代檢查
    python scripts/check_fr_full.py --fr FR-01 --project /path/to/project --loop

檢查內容（三層）：
    1. 輕量：Syntax + Import（~30秒）
    2. Constitution：BVS + HR-09（~1分鐘）
    3. CQG：Linter + Complexity 只針對該 FR 的檔案（~1分鐘）

Pass 條件：
    - 輕量：無 Error
    - Constitution：無 BLOCK（Warning 可接受）
    - CQG：無 Error（Warning 可接受）
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


# 自動偵測 methodology-v2 路徑
SCRIPT_DIR = Path(__file__).resolve().parent
METHODOLOGY_V2_DIR = SCRIPT_DIR.parent
QUALITY_GATE_DIR = METHODOLOGY_V2_DIR / "quality_gate"


def get_fr_files(project_path: Path, fr_id: str) -> list:
    """從 fr_mapping.json 取得該 FR 的檔案"""
    fr_map_file = project_path / ".methodology" / "fr_mapping.json"
    if fr_map_file.exists():
        import json
        with open(fr_map_file) as f:
            data = json.load(f)
        if fr_id in data:
            return data[fr_id].get("files", [])
    return []


def run_linter(project: Path, files: list) -> tuple:
    """執行 Linter 檢查"""
    if not files:
        return True, []
    
    print(f"   Linting {len(files)} files...")
    errors = []
    
    # 只檢查 Python 檔案
    py_files = [project / f for f in files if f.endswith('.py')]
    if not py_files:
        return True, []
    
    # 使用 pylint 或 pylint3
    linter_cmd = None
    for cmd in ['pylint', 'pylint3']:
        result = subprocess.run(['which', cmd], capture_output=True)
        if result.returncode == 0:
            linter_cmd = cmd
            break
    
    if not linter_cmd:
        print("   ⚠️  pylint not found, skipping Lint")
        return True, []
    
    # 對每個檔案執行 linter
    for py_file in py_files:
        result = subprocess.run(
            [linter_cmd, '--errors-only', str(py_file)],
            capture_output=True, text=True, cwd=str(project)
        )
        if result.returncode != 0 and result.stderr:
            errors.append(f"   ❌ {py_file.name}: {result.stderr.split(chr(10))[0]}")
    
    return len(errors) == 0, errors


def run_complexity(project: Path, files: list) -> tuple:
    """執行 Complexity 檢查"""
    if not files:
        return True, []
    
    print(f"   Checking complexity for {len(files)} files...")
    errors = []
    
    py_files = [project / f for f in files if f.endswith('.py')]
    if not py_files:
        return True, []
    
    # 使用 radon 檢查複雜度
    result = subprocess.run(
        ['which', 'radon'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("   ⚠️  radon not found, skipping Complexity")
        return True, []
    
    for py_file in py_files:
        result = subprocess.run(
            ['radon', 'cc', '-a', '-m', '10', str(py_file)],
            capture_output=True, text=True, cwd=str(project)
        )
        if result.returncode != 0 and result.stdout:
            lines = result.stdout.strip().split('\n')
            if lines:
                errors.append(f"   ❌ {py_file.name}: {lines[-1]}")
    
    return len(errors) == 0, errors


def run_check(name: str, cmd: list, project: str, cwd: str = None) -> tuple:
    """執行檢查命令"""
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    
    # 設定環境：PYTHONPATH 包含 methodology-v2
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{METHODOLOGY_V2_DIR}:{current_pythonpath}"
    
    # 使用 methodology-v2 作為 cwd
    exec_cwd = cwd or str(METHODOLOGY_V2_DIR)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分鐘超時
            cwd=exec_cwd,
            env=env
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        
        if passed:
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
            print(output[-500:] if len(output) > 500 else output)
        
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
    parser.add_argument("--methodology", default=None, help="Methodology-v2 路徑（自動偵測）")
    args = parser.parse_args()
    
    project = str(Path(args.project).resolve())
    fr_id = args.fr
    
    # 如果有指定 methodology-v2 路徑，使用它
    global METHODOLOGY_V2_DIR, QUALITY_GATE_DIR, SCRIPT_DIR
    if args.methodology:
        METHODOLOGY_V2_DIR = Path(args.methodology).resolve()
        SCRIPT_DIR = METHODOLOGY_V2_DIR / "scripts"
        QUALITY_GATE_DIR = METHODOLOGY_V2_DIR / "quality_gate"
    
    print(f"Project: {project}")
    print(f"Methodology-v2: {METHODOLOGY_V2_DIR}")
    
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
            ["python3", str(SCRIPT_DIR / "check_fr_quality.py"), "--fr", fr_id, "--project", project],
            project
        )
        if not passed:
            all_passed = False
        
        # Layer 2: Constitution（可選）
        if not args.skip_constitution:
            passed, _ = run_check(
                "Layer 2: Constitution (BVS + HR-09)",
                ["python3", "-m", "quality_gate.constitution.runner", "--type", "implementation", "--project", project],
                project
            )
            if not passed:
                all_passed = False
        
        # Layer 3: CQG - 直接執行 FR-level 檢查（不呼叫 cli quality-gate）
        if not args.skip_cqg:
            print(f"\n{'='*50}")
            print(f"  Layer 3: CQG (Linter + Complexity)")
            print(f"{'='*50}")
            
            fr_files = get_fr_files(Path(project), fr_id)
            if not fr_files:
                print(f"⚠️  找不到 {fr_id} 的代碼檔案")
            else:
                print(f"📁 FR files: {fr_files}")
                
                # Linter
                lint_passed, lint_errors = run_linter(Path(project), fr_files)
                if lint_errors:
                    for err in lint_errors[:5]:
                        print(err)
                if not lint_passed:
                    all_passed = False
                
                # Complexity
                complexity_passed, complexity_errors = run_complexity(Path(project), fr_files)
                if complexity_errors:
                    for err in complexity_errors[:5]:
                        print(err)
                if not complexity_passed:
                    all_passed = False
                
                if lint_passed and complexity_passed:
                    print(f"✅ Layer 3: CQG PASSED")
                else:
                    print(f"❌ Layer 3: CQG FAILED")
        
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
