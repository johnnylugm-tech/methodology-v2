#!/usr/bin/env python3
"""
Generate FR Mapping - 從專案結構生成 FR → 代碼檔案映射
====================================================

用途：為 Phase 3 快速生成 FR 映射表

使用方式：
    python scripts/generate_fr_mapping.py --project /path/to/project

產出：
    .methodology/fr_mapping.json - FR → 代碼檔案映射
"""

import argparse
import json
import re
from pathlib import Path


# FR → 關鍵字映射（用於自動偵測）
FR_KEYWORDS = {
    "FR-01": ["lexicon", "mapping", "taiwan", "台灣", "詞彙"],
    "FR-02": ["ssml", "parser", "voice"],
    "FR-03": ["chunk", "text", "split", "切分"],
    "FR-04": ["synth", "engine", "parallel", "async", "併行"],
    "FR-05": ["circuit", "breaker", "斷路"],
    "FR-06": ["redis", "cache", "快取"],
    "FR-07": ["cli", "command", "routes", "命令行"],
    "FR-08": ["ffmpeg", "audio", "format", "轉換"],
    "FR-09": ["kokoro", "proxy", "client"],
}


def scan_for_fr(project: Path, fr_id: str, keywords: list) -> list:
    """掃描 src 目錄，找出可能屬於該 FR 的檔案"""
    files = []
    src_dirs = [
        project / "03-development" / "src",
        project / "src",
        project / "lib",
    ]
    
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text(errors="ignore").lower()
            
            # 檢查關鍵字
            matches = sum(1 for kw in keywords if kw.lower() in content)
            if matches >= 2:  # 至少匹配 2 個關鍵字
                files.append(str(py_file.relative_to(project)))
    
    return list(set(files))


def main():
    parser = argparse.ArgumentParser(description="Generate FR → Code mapping")
    parser.add_argument("--project", required=True, help="專案路徑")
    parser.add_argument("--output", default=".methodology/fr_mapping.json", help="輸出路徑")
    args = parser.parse_args()
    
    project = Path(args.project)
    output_file = project / args.output
    
    print(f"\n{'='*50}")
    print(f"FR Mapping Generator")
    print(f"{'='*50}")
    print(f"Project: {project}")
    
    mapping = {}
    for fr_id, keywords in FR_KEYWORDS.items():
        files = scan_for_fr(project, fr_id, keywords)
        mapping[fr_id] = {
            "keywords": keywords,
            "files": files,
            "file_count": len(files)
        }
        print(f"{fr_id}: {len(files)} files")
    
    # 儲存
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Mapping saved to: {output_file}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
