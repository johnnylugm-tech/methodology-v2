#!/usr/bin/env python3
"""
Citation Parser — 解析 citation 字串

支援格式：
- "SRS.md#L45"     → artifact="SRS.md", section="L45"
- "SAD.md#§3.2"   → artifact="SAD.md", section="§3.2"
- "SRS.md"        → artifact="SRS.md", section=None
- "SRS.md#L23-L45" → artifact="SRS.md", section="L23-L45"

使用方式：
    from constitution.citation_parser import parse_citation, parse_citations

    artifact, section = parse_citation("SRS.md#L45")
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, List

@dataclass
class Citation:
    """解析後的 citation"""
    raw: str
    artifact: str      # e.g., "SRS.md"
    section: Optional[str]  # e.g., "L45" or "§3.2"
    line_range: Optional[Tuple[int, int]] = None  # (23, 45)


def parse_citation(citation: str) -> Tuple[str, Optional[str]]:
    """
    解析單一 citation 字串

    Args:
        citation: citation 字串，如 "SRS.md#L45"

    Returns:
        (artifact, section) tuple
    """
    if not citation:
        return ("", None)

    # 移除 leading #
    citation = citation.strip().lstrip('#')

    # 找 # 分隔
    if '#' in citation:
        parts = citation.split('#', 1)
        artifact = parts[0].strip()
        section = parts[1].strip() if len(parts) > 1 else None
    else:
        artifact = citation.strip()
        section = None

    return (artifact, section)


def parse_citations(citations: List[str]) -> List[Citation]:
    """解析多個 citations"""
    result = []
    for raw in citations:
        artifact, section = parse_citation(raw)
        line_range = _parse_line_range(section) if section else None
        result.append(Citation(
            raw=raw,
            artifact=artifact,
            section=section,
            line_range=line_range
        ))
    return result


def _parse_line_range(section: str) -> Optional[Tuple[int, int]]:
    """解析 line range，如 'L23-L45' → (23, 45)"""
    if not section:
        return None

    # 移除常見前綴
    section = re.sub(r'^[Ll]ine?\s*', '', section)

    # 處理範圍 L23-L45
    range_match = re.match(r'(\d+)\s*[-–]\s*(\d+)', section)
    if range_match:
        return (int(range_match.group(1)), int(range_match.group(2)))

    # 處理單一數字 L45 → (45, 45)
    num_match = re.match(r'(\d+)', section)
    if num_match:
        num = int(num_match.group(1))
        return (num, num)

    return None


def load_artifact_content(artifact_path: str, section: str = None) -> str:
    """
    讀取 artifact 內容（可選特定 section）

    Note: 實際使用时需要 project_path，這裡只定義介面
    """
    # 這裡不實際讀檔案，由 caller 提供 artifact_content dict
    raise NotImplementedError("Use load_artifact_content_from_paths() instead")


def load_artifact_content_from_paths(
    artifact_contents: dict,  # {artifact_name: content}
    citations: List[str]
) -> dict:
    """
    根據 citations 讀取對應的 artifact 內容

    Args:
        artifact_contents: {artifact_name: full_content}
        citations: list of citation strings

    Returns:
        {artifact_name: relevant_content}
    """
    result = {}
    for raw in citations:
        artifact, section = parse_citation(raw)
        if artifact in artifact_contents:
            content = artifact_contents[artifact]
            if section:
                # 這裡可以進一步過濾 section，但目前直接返回全文
                result[artifact] = content
            else:
                result[artifact] = content
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Citation Parser - 解析 citation 字串")
        print("用法: python citation_parser.py")
        print("或:   from constitution.citation_parser import parse_citation")
    else:
        # Demo
        test_citations = ["SRS.md#L45", "SAD.md#§3.2", "SRS.md#L23-L45", "README.md"]
        print("Testing citation parser:")
        for c in test_citations:
            artifact, section = parse_citation(c)
            print(f"  '{c}' → artifact='{artifact}', section='{section}'")