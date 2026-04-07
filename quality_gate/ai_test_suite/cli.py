#!/usr/bin/env python3
"""CLI for AI Test Suite Generator"""

import argparse
import sys
from pathlib import Path

# 添加 skill root 到 path
skill_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(skill_root))

from quality_gate.ai_test_suite import LLMTestGenerator
from provider_abstraction import ModelRouter


def main():
    parser = argparse.ArgumentParser(description="AI Test Suite Generator")
    parser.add_argument("--target", "-t", required=True, help="Target source file or directory")
    parser.add_argument("--output", "-o", default="tests/ai_generated", help="Output directory")
    parser.add_argument("--model", "-m", default=None, help="LLM model override")
    parser.add_argument("--context", "-c", nargs="*", help="Context files (SRS.md, SAD.md)")

    args = parser.parse_args()

    # 讀取 target
    target = Path(args.target)
    if target.is_file():
        source_code = target.read_text(encoding="utf-8")
    else:
        # 讀取所有 .py 檔案
        source_code = ""
        for py_file in target.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                source_code += f"\n\n# File: {py_file}\n"
                source_code += py_file.read_text(encoding="utf-8")

    # 讀取 context artifacts
    artifacts = {}
    if args.context:
        for ctx_file in args.context:
            path = Path(ctx_file)
            if path.exists():
                artifacts[path.name] = path.read_text(encoding="utf-8")

    # 初始化 LLM Generator
    router = ModelRouter()
    provider = router.route(phase=4)  # Phase 4 = 測試
    generator = LLMTestGenerator(provider=provider, model=args.model)

    # 生成測試套件
    test_cases = generator.generate_test_suite(source_code, artifacts)

    # 輸出
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for tc in test_cases:
        output_file = output_dir / f"{tc.name}.py"
        output_file.write_text(tc.code, encoding="utf-8")
        print(f"✅ {output_file}")

    print(f"\n共生成 {len(test_cases)} 個測試案例")
    print(f"輸出目錄: {output_dir}")
    print("\n⚠️  所有測試需要人工審查後啟用 (HR-17)")


if __name__ == "__main__":
    main()
