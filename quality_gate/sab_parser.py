#!/usr/bin/env python3
"""
SabParser - 從 SAD.md 提取 SAB Block
====================================
使用 shared parsers.py 的 extract_json_block

注意：舊版 semantic parsing 已廢棄，使用 JSON extraction 代替
"""

from quality_gate.parsers import extract_sab_from_sad

# 便捷函數
def extract_sab_from_sad(sad_path):
    """從 SAD.md 提取 SAB（使用 parsers.py）"""
    from pathlib import Path
    return extract_json_block(Path(sad_path).read_text(), "SAB")

# 為了向後兼容，保留 SabParser 類
class SabParser:
    def __init__(self, sad_path):
        from pathlib import Path
        self.sad_path = Path(sad_path)
        self.content = ""
        if self.sad_path.exists():
            self.content = self.sad_path.read_text(encoding="utf-8")
    
    def parse(self):
        import json
        from quality_gate.parsers import extract_json_block
        return extract_json_block(self.content, "SAB")
