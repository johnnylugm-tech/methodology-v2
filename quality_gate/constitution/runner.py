#!/usr/bin/env python3
"""
Constitution Checker Runner
===========================
統一執行介面

Usage:
    python runner.py                           # 檢查當前目錄
    python runner.py --path /path/to/docs     # 檢查指定目錄
    python runner.py --type srs               # 只檢查 SRS
    python runner.py --type all               # 檢查所有
    python runner.py --format json            # JSON 輸出
    python runner.py --current-phase 3       # 只檢查到 Phase 3 (階段性檢查)
    python runner.py -cp 5                    # 只檢查到 Phase 5
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

# 確保可以匯入
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quality_gate.constitution import (
    run_constitution_check,
    ConstitutionCheckResult,
    CONSTITUTION_THRESHOLDS
)


def format_result_text(result: ConstitutionCheckResult) -> str:
    """格式化文字輸出"""
    lines = []
    
    # 標題
    check_type_names = {
        "srs": "SRS (Software Requirements Specification)",
        "sad": "SAD (Software Architecture Description)",
        "test_plan": "Test Plan",
        "all": "All Constitution Checks"
    }
    
    title = check_type_names.get(result.check_type, result.check_type)
    
    lines.append("=" * 70)
    lines.append(f"📋 Constitution Check: {title}")
    lines.append("=" * 70)
    
    # 結果摘要
    status = "✅ PASS" if result.passed else "❌ FAIL"
    lines.append(f"\n📊 Result: {status}")
    lines.append(f"   Score: {result.score:.1f}%")
    lines.append(f"   Violations: {len(result.violations)}")
    
    # 閾值
    lines.append(f"\n📏 Constitution Thresholds:")
    for key, value in CONSTITUTION_THRESHOLDS.items():
        lines.append(f"   {key}: {value}%")
    
    # 違規詳細
    if result.violations:
        lines.append(f"\n⚠️  Violations:")
        for v in result.violations:
            severity_icon = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🔵"
            }.get(v.get("severity", "LOW"), "⚪")
            
            lines.append(f"   {severity_icon} [{v.get('severity', 'UNKNOWN')}] {v.get('type', 'unknown')}")
            lines.append(f"       {v.get('message', '')}")
    
    # 建議
    if result.recommendations:
        lines.append(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            lines.append(f"   • {rec}")
    
    # 詳情
    if result.details:
        lines.append(f"\n📝 Details:")
        for key, value in result.details.items():
            lines.append(f"   {key}: {value}")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


def format_result_json(result: ConstitutionCheckResult) -> str:
    """格式化 JSON 輸出"""
    return json.dumps(asdict(result), indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Constitution Quality Gate Checker"
    )
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Base path to check (default: current directory)"
    )
    parser.add_argument(
        "--type", "-t",
        choices=["srs", "sad", "test_plan", "all"],
        default="all",
        help="Type of check to run"
    )
    parser.add_argument(
        "--current-phase", "-cp",
        type=int,
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
        default=None,
        help="只檢查到指定 Phase (1-8)。用於階段性檢查，例如：--current-phase 3 只檢查 Phase 1-3"
    )
    parser.add_argument(
        "--check-mode", "-m",
        choices=["preflight", "postflight"],
        default="preflight",
        help="檢查模式：preflight (進入前檢查前提) 或 postflight (完成後檢查產出). 預設: preflight"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # 如果是相對路徑，轉為絕對路徑
    base_path = Path(args.path)
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    
    # 嘗試找到 phase 目錄（根據 check type）
    # Phase 1 (SRS): 01-requirements 或 docs
    # Phase 2 (SAD): 02-architecture 或 docs
    # Phase 3+ (implementation): 根目錄
    check_type_to_dir = {
        "srs": ["01-requirements", "docs"],
        "sad": ["02-architecture", "docs"],
        "test_plan": ["04-testing", "docs"],
    }
    
    # 預設：docs/ (向後兼容)
    docs_path = base_path / "docs"
    
    if args.type in check_type_to_dir and not docs_path.exists():
        for alt_dir in check_type_to_dir[args.type]:
            candidate = base_path / alt_dir
            if candidate.exists():
                docs_path = candidate
                break
    
    if not docs_path.exists():
        # 嘗試在父目錄找
        for alt_dir in ["docs"] + list(check_type_to_dir.values()):
            for d in alt_dir:
                candidate = base_path.parent / d
                if candidate.exists():
                    docs_path = candidate
                    break
        if not docs_path.exists():
            print(f"Error: documentation directory not found for check type {args.type} in {base_path}")
            sys.exit(1)
    
    if args.verbose:
        print(f"Checking: {docs_path}")
        print(f"Check type: {args.type}")
    
    # 執行檢查
    result = run_constitution_check(args.type, str(docs_path), args.current_phase, check_mode=args.check_mode)
    
    # 輸出結果
    if args.format == "json":
        print(format_result_json(result))
    else:
        print(format_result_text(result))
    
    # 退出碼
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
