#!/usr/bin/env python3
"""
Context Compression - 三層壓縮機制

L1: 摘要（>50 messages）
L2: 關鍵資訊提取（>100 messages）
L3: 歷史存檔（>200 messages）

用法：
    python context_compressor.py compress --input messages.json --level L1
    python context_compressor.py compress --input messages.json --level L2
    python context_compressor.py compress --input messages.json --level L3
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 預設 Threshold
THRESHOLDS = {
    "L1": 50,
    "L2": 100,
    "L3": 200,
}

def summarize(messages: List[Dict]) -> str:
    """L1: 摘要壓縮"""
    recent = messages[-50:] if len(messages) > 50 else messages
    # 簡單摘要：取前10+後10的關鍵字
    content = " ".join([m.get("content", "")[:200] for m in recent[-10:]])
    return f"[Summary of last {len(recent)} messages]: {content[:300]}..."

def extract_key_info(messages: List[Dict]) -> str:
    """L2: 關鍵資訊提取"""
    # 提取所有 tool_calls, decisions, artifacts
    tools = []
    decisions = []
    artifacts = []
    
    for m in messages:
        if m.get("role") == "assistant":
            content = m.get("content", "")
            if "tool_calls" in m:
                tools.extend([tc.get("name") for tc in m.get("tool_calls", [])])
            if content.startswith("Decision:"):
                decisions.append(content[:100])
    
    key_info = f"[Key Info] Tools used: {set(tools)}. Decisions: {decisions[-5:]}."
    return key_info

def archive_messages(messages: List[Dict], archive_dir: Path) -> List[Dict]:
    """L3: 存檔"""
    archive_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = archive_dir / f"archive_{timestamp}.json"
    
    old_messages = messages[:-100] if len(messages) > 100 else messages
    with open(archive_file, "w") as f:
        json.dump(old_messages, f, indent=2, ensure_ascii=False)
    
    return messages[-100:]

def compress(messages: List[Dict], level: str = "L1") -> List[Dict]:
    """壓縮訊息"""
    result = messages.copy()
    
    if level in ("L1", "L2", "L3"):
        threshold = THRESHOLDS[level]
    else:
        threshold = int(level)
    
    if len(result) > 200:
        result = archive_messages(result, Path(".methodology/archives"))
    
    if len(result) > 100:
        key_info = extract_key_info(result)
        result = [{"role": "system", "content": key_info}] + result[-20:]
    
    if len(result) > 50:
        summary = summarize(result)
        result = result[:10] + [{"role": "user", "content": summary}]
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Context Compression Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    compress_parser = subparsers.add_parser("compress", help="Compress messages")
    compress_parser.add_argument("--input", required=True, help="Input JSON file")
    compress_parser.add_argument("--output", help="Output JSON file")
    compress_parser.add_argument("--level", default="L1", choices=["L1", "L2", "L3", "auto"], help="Compression level")
    compress_parser.add_argument("--repo", help="Repo path for archive directory")
    
    args = parser.parse_args()
    
    if args.command == "compress":
        messages = json.loads(Path(args.input).read_text())
        original_len = len(messages)
        
        if args.level == "auto":
            if original_len > 200:
                level = "L3"
            elif original_len > 100:
                level = "L2"
            elif original_len > 50:
                level = "L1"
            else:
                level = None
        else:
            level = args.level if args.level != "auto" else None
        
        if level:
            messages = compress(messages, level)
        
        output = args.output or args.input.replace(".json", "_compressed.json")
        Path(output).write_text(json.dumps(messages, indent=2, ensure_ascii=False))
        
        print(f"Compressed: {original_len} → {len(messages)} messages (Level: {level})")
        print(f"Output: {output}")

if __name__ == "__main__":
    main()
