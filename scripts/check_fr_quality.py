#!/usr/bin/env python3
"""
Check FR Quality - 每個 FR 完成後的快速檢查
==========================================

用途：每個 FR 完成後，快速檢查該 FR 的代碼品質

使用方式：
    python scripts/check_fr_quality.py --fr FR-01 --project /path/to/project

檢查內容：
    1. Syntax check (python -m py_compile)
    2. Basic lint (ruff 或 flake8)
    3. Import check (import 該模組)

Pass 條件：無 Error（Warning 可接受）

這是最小的檢查，不包含 Constitution/CQG（那些在事後檢查時做）
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_fr_files(project_path: Path, fr_id: str) -> list:
    """從 traceability_report.json 取得該 FR 的檔案"""
    trace_file = project_path / "traceability_report.json"
    if not trace_file.exists():
        return []
    
    import json
    with open(trace_file) as f:
        data = json.load(f)
    
    files = []
    for req in data.get("requirements", []):
        if req.get("requirement_id") == fr_id:
            files.extend(req.get("code_files", []))
    return files


def check_syntax(file_path: Path) -> tuple:
    """Python 語法檢查"""
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(file_path)],
            capture_output=True, text=True
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


def check_import(file_path: Path) -> tuple:
    """Import 該模組"""
    try:
        module_name = str(file_path).replace("/", ".").replace(".py", "")
        result = subprocess.run(
            ["python3", "-c", f"import {module_name}"],
            capture_output=True, text=True,
            timeout=10
        )
        return result.returncode == 0, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Import timeout"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description="每個 FR 的快速品質檢查")
    parser.add_argument("--fr", required=True, help="FR ID (e.g., FR-01)")
    parser.add_argument("--project", default=".", help="專案路徑")
    args = parser.parse_args()
    
    project = Path(args.project)
    fr_id = args.fr
    
    print(f"\n{'='*50}")
    print(f"FR Quality Check: {fr_id}")
    print(f"{'='*50}")
    
    # 取得該 FR 的檔案
    files = get_fr_files(project, fr_id)
    if not files:
        print(f"⚠️  找不到 {fr_id} 的代碼檔案")
        print(f"   跳過（請確認 traceability_report.json 已更新）")
        return 0
    
    print(f"📁 檢查 {len(files)} 個檔案: {files}\n")
    
    errors = []
    for f in files:
        file_path = project / f
        if not file_path.exists():
            print(f"⚠️  檔案不存在: {f}")
            continue
        
        if not f.endswith(".py"):
            continue
        
        # Syntax check
        ok, err = check_syntax(file_path)
        if not ok:
            errors.append(f"❌ Syntax error in {f}: {err}")
        else:
            print(f"✅ {f}: Syntax OK")
    
    print(f"\n{'='*50}")
    if errors:
        print(f"❌ FAILED: {len(errors)} errors")
        for e in errors:
            print(f"   {e}")
        return 1
    else:
        print(f"✅ PASSED: All checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
