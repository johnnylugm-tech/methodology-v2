#!/usr/bin/env python3
"""
SabParser - 從 SAD.md 提取 SAB Block
====================================
從 SAD.md 的 <!-- SAB:START --> 和 <!-- SAB:END --> 之間提取 JSON

這是簡單的 JSON extraction，不是 semantic parsing
"""

import re
import json
from pathlib import Path
from typing import Optional, Dict, Any


class SabParser:
    """
    從 SAD.md 提取 SAB Block
    
    使用方式：
        parser = SabParser(sad_path=Path("SAD.md"))
        sab_spec = parser.parse()
    """
    
    def __init__(self, sad_path: Path):
        self.sad_path = sad_path
        self.content = ""
        if sad_path.exists():
            self.content = sad_path.read_text(encoding="utf-8")
    
    def parse(self) -> Optional[Dict[str, Any]]:
        """
        從 SAD.md 提取 SAB JSON
        
        Returns:
            SAB dict 或 None（如果提取失敗）
        """
        # 提取 <!-- SAB:START --> 和 <!-- SAB:END --> 之間的內容
        pattern = r'<!--\s*SAB:START\s*-->\s*(.*?)\s*<!--\s*SAB:END\s*-->'
        match = re.search(pattern, self.content, re.DOTALL)
        
        if not match:
            return None
        
        json_str = match.group(1).strip()
        
        # 移除 markdown code block 標記（如果有的話）
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'^```\s*', '', json_str)
        json_str = re.sub(r'```\s*$', '', json_str)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"❌ SAB JSON parse error: {e}")
            return None


def extract_sab_from_sad(sad_path: Path) -> Optional[Dict[str, Any]]:
    """便捷函數：從 SAD.md 提取 SAB"""
    parser = SabParser(sad_path)
    return parser.parse()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract SAB from SAD.md")
    parser.add_argument("sad_file", type=Path, help="SAD.md path")
    args = parser.parse_args()
    
    sab = extract_sab_from_sad(args.sad_file)
    if sab:
        print(json.dumps(sab, indent=2, ensure_ascii=False))
    else:
        print("❌ No SAB block found or parse error")
