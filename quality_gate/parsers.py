#!/usr/bin/env python3
"""
Parsers - JSON Block Extraction
==============================
從文件模板提取 JSON blocks

支援：
- SRS.md: <!-- FR:START --> ... <!-- FR:END -->
- SAD.md: <!-- SAB:START --> ... <!-- SAB:END -->
- TEST_PLAN.md: <!-- TEST:START --> ... <!-- TEST:END -->
"""

import re
import json
from pathlib import Path
from typing import Optional, Dict, Any


def extract_json_block(content: str, block_name: str) -> Optional[Dict[str, Any]]:
    """
    從內容中提取 JSON block
    
    Args:
        content: 文件內容
        block_name: block 名稱（如 "FR", "SAB", "TEST"）
    
    Returns:
        Parsed JSON dict 或 None
    """
    pattern = rf'<!--\s*{block_name}:START\s*-->\s*(.*?)\s*<!--\s*{block_name}:END\s*-->'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return None
    
    json_str = match.group(1).strip()
    
    # 移除 markdown code block 標記
    json_str = re.sub(r'^```json\s*', '', json_str)
    json_str = re.sub(r'^```\s*', '', json_str)
    json_str = re.sub(r'```\s*$', '', json_str)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ {block_name} JSON parse error: {e}")
        return None


def extract_fr_from_srs(srs_path: Path) -> Optional[Dict[str, Any]]:
    """從 SRS.md 提取 FR block"""
    if not srs_path.exists():
        return None
    content = srs_path.read_text(encoding="utf-8")
    return extract_json_block(content, "FR")


def extract_sab_from_sad(sad_path: Path) -> Optional[Dict[str, Any]]:
    """從 SAD.md 提取 SAB block"""
    if not sad_path.exists():
        return None
    content = sad_path.read_text(encoding="utf-8")
    return extract_json_block(content, "SAB")


def extract_test_from_plan(plan_path: Path) -> Optional[Dict[str, Any]]:
    """從 TEST_PLAN.md 提取 TEST block"""
    if not plan_path.exists():
        return None
    content = plan_path.read_text(encoding="utf-8")
    return extract_json_block(content, "TEST")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract JSON blocks from templates")
    parser.add_argument("file", type=Path, help="File to parse")
    parser.add_argument("block", help="Block name (FR, SAB, TEST)")
    args = parser.parse_args()
    
    result = extract_json_block(args.file.read_text(), args.block)
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ No {args.block} block found")
