#!/usr/bin/env python3
"""
Generate FR Mapping - 從專案結構生成 FR → 代碼檔案映射
====================================================

用途：為 Phase 3 快速生成 FR 映射表

使用方式：
    python scripts/generate_fr_mapping.py --project /path/to/project

產出：
    .methodology/fr_mapping.json - FR → 代碼檔案映射

掃描策略（按優先順序）：
    1. FR Tag 解析：掃描 docstring 裡的 [FR-XX] 或 FR-XX: pattern
    2. Keyword 匹配：Fallback 關鍵字掃描（至少 2 個關鍵字）
"""

import argparse
import json
import re
from pathlib import Path
from collections import defaultdict


# FR → 關鍵字映射（用於 Keyword 匹配 fallback）
FR_KEYWORDS = {
    "FR-01": ["lexicon", "mapping", "taiwan", "台灣", "詞彙"],
    "FR-02": ["ssml", "parser", "voice"],
    "FR-03": ["chunk", "text", "split", "切分"],
    "FR-04": ["synth", "engine", "parallel", "async", "併行"],
    "FR-05": ["circuit", "breaker", "斷路"],
    "FR-06": ["redis", "cache", "快取"],
    "FR-07": ["cli", "command", "routes", "tts-v610"],
    "FR-08": ["ffmpeg", "audio", "format", "轉換", "converter"],
    "FR-09": ["kokoro", "proxy", "client"],
}


def extract_fr_tags(content: str) -> list:
    """從 docstring 或程式碼內容解析 [FR-XX] 或 FR-XX: pattern"""
    fr_ids = []
    
    # 匹配 [FR-01] 或 FR-01: 或 FR-01 - 或 FR-01.
    patterns = [
        r'\[FR-(\d+)\]',           # [FR-01]
        r'FR-(\d+):',              # FR-01:
        r'FR-(\d+)\s*-',           # FR-01 -
        r'FR-(\d+)\.',             # FR-01.
        r'FR-(\d+)\s',             # FR-01 (followed by space)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        fr_ids.extend([f"FR-{m}" for m in matches])
    
    return list(set(fr_ids))


def scan_for_fr_tags(project: Path) -> dict:
    """掃描所有 Python 檔案，解析 docstring 裡的 FR tags"""
    fr_files = defaultdict(list)
    
    src_dirs = [
        project / "03-development" / "src",
        project / "03-development" / "tests",
        project / "src",
        project / "tests",
        project / "lib",
    ]
    
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        
        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(errors="ignore")
                fr_ids = extract_fr_tags(content)
                
                rel_path = str(py_file.relative_to(project))
                for fr_id in fr_ids:
                    if rel_path not in fr_files[fr_id]:  # 避免重複
                        fr_files[fr_id].append(rel_path)
            except Exception:
                continue
    
    return dict(fr_files)


def scan_for_keywords(project: Path, fr_id: str, keywords: list) -> list:
    """關鍵字匹配 fallback"""
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
            try:
                content = py_file.read_text(errors="ignore").lower()
                
                # 檢查關鍵字
                matches = sum(1 for kw in keywords if kw.lower() in content)
                if matches >= 2:  # 至少匹配 2 個關鍵字
                    files.append(str(py_file.relative_to(project)))
            except Exception:
                continue
    
    return list(set(files))


def main():
    parser = argparse.ArgumentParser(description="Generate FR → Code mapping")
    parser.add_argument("--project", required=True, help="專案路徑")
    parser.add_argument("--output", default=".methodology/fr_mapping.json", help="輸出路徑")
    parser.add_argument("--force-keyword", action="store_true", help="強制使用關鍵字匹配（忽略 FR tags）")
    args = parser.parse_args()
    
    project = Path(args.project)
    output_file = project / args.output
    
    print(f"\n{'='*50}")
    print(f"FR Mapping Generator")
    print(f"{'='*50}")
    print(f"Project: {project}")
    
    # Step 1: FR Tag 解析（主要方法）
    print(f"\n[Step 1] Scanning FR tags from docstrings...")
    fr_tag_mapping = scan_for_fr_tags(project)
    
    for fr_id, files in sorted(fr_tag_mapping.items()):
        print(f"  {fr_id}: {len(files)} files (FR tag)")
    
    # Step 2: Keyword 匹配（Fallback）
    print(f"\n[Step 2] Keyword matching (fallback)...")
    fr_keyword_mapping = {}
    for fr_id, keywords in FR_KEYWORDS.items():
        files = scan_for_keywords(project, fr_id, keywords)
        fr_keyword_mapping[fr_id] = files
        if fr_id not in fr_tag_mapping:
            print(f"  {fr_id}: {len(files)} files (keyword fallback)")
    
    # Step 3: 合併結果（Tag 優先）
    print(f"\n[Step 3] Merging results...")
    mapping = {}
    all_fr_ids = set(list(fr_tag_mapping.keys()) + list(fr_keyword_mapping.keys()))
    
    for fr_id in sorted(all_fr_ids):
        # Tag 匹配的檔案
        tag_files = fr_tag_mapping.get(fr_id, [])
        # Keyword 匹配的檔案
        keyword_files = fr_keyword_mapping.get(fr_id, [])
        
        # 合併：Tag 優先，Keyword 作為補充
        all_files = list(set(tag_files + keyword_files))
        
        # 標記來源
        source = []
        if tag_files:
            source.append("fr_tag")
        if keyword_files and fr_id not in fr_tag_mapping:
            source.append("keyword_fallback")
        elif keyword_files:
            source.append("keyword_supplement")
        
        mapping[fr_id] = {
            "files": all_files,
            "file_count": len(all_files),
            "source": source,
            "keywords": FR_KEYWORDS.get(fr_id, []),
            "fr_tag_files": tag_files,
            "keyword_files": [f for f in keyword_files if f not in tag_files],
        }
        
        source_str = ", ".join(source)
        print(f"  {fr_id}: {len(all_files)} files ({source_str})")
    
    # 儲存
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Mapping saved to: {output_file}")
    
    # 總結
    total_files = sum(m["file_count"] for m in mapping.values())
    frs_with_tags = sum(1 for m in mapping.values() if "fr_tag" in m["source"])
    print(f"\n--- Summary ---")
    print(f"Total FRs: {len(mapping)}")
    print(f"FRs with docstring tags: {frs_with_tags}")
    print(f"Total file mappings: {total_files}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
