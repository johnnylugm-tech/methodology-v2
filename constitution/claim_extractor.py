#!/usr/bin/env python3
"""
Claim Extractor — 從 Subagent result text 提取可驗證的 claims

HR-09 Claims Verifier 系統的一部分

使用方式：
    from constitution.claim_extractor import extract_claims

    claims = extract_claims(
        "Implement LRU cache strategy based on SRS.md §4.2, using asyncio for performance."
    )
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Claim:
    """可驗證的聲稱"""
    id: str
    text: str
    keywords: List[str] = field(default_factory=list)
    pattern_matched: str = ""
    claim_type: str = "unknown"  # design_decision / implementation / reasoning / assumption

# Claim 提取 patterns
CLAIM_PATTERNS = [
    # 設計決策
    (r'使用(\w+[演算法|策略|模式|機制])', 'design_decision'),
    (r'基於(\w+)', 'design_decision'),
    (r'遵循(\w+[設計|規格|標準])', 'design_decision'),
    (r'採用(\w+)', 'design_decision'),

    # 實作選擇
    (r'透過(\w+)', 'implementation'),
    (r'使用(\w+)來', 'implementation'),
    (r'以(\w+)實現', 'implementation'),
    (r'用(\w+)處理', 'implementation'),

    # 推理
    (r'由於(\w+)', 'reasoning'),
    (r'因為(\w+)', 'reasoning'),
    (r'根據(\w+)', 'reasoning'),
    (r'依據(\w+)', 'reasoning'),

    # 假設
    (r'假設(\w+)', 'assumption'),
    (r'假設(\w+)成立', 'assumption'),
]

# 停用詞（提取關鍵字時跳過）
STOP_WORDS = {'的', '了', '是', '在', '和', '與', '或', '但', '因為', '所以', '如果'}


def extract_claims(text: str) -> List[Claim]:
    """
    從文字中提取可驗證的 claims

    Args:
        text: Subagent result 文字

    Returns:
        List of Claim objects
    """
    if not text:
        return []

    claims = []
    sentences = re.split(r'[.。]\s+', text)

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence or len(sentence) < 10:
            continue

        # 嘗試每個 pattern
        for pattern, claim_type in CLAIM_PATTERNS:
            match = re.search(pattern, sentence)
            if match:
                # 提取關鍵字
                keywords = _extract_keywords(sentence, stop_words=STOP_WORDS)

                claims.append(Claim(
                    id=f"claim_{i}",
                    text=sentence,
                    keywords=keywords,
                    pattern_matched=pattern,
                    claim_type=claim_type
                ))
                break

    return claims


def _extract_keywords(text: str, stop_words: set = None) -> List[str]:
    """從文字中提取關鍵字"""
    if stop_words is None:
        stop_words = STOP_WORDS

    # 簡單分詞
    words = re.findall(r'[\w]+', text.lower())

    # 過濾停用詞和太短的詞
    keywords = [w for w in words if w not in stop_words and len(w) >= 2]

    # 取最重要的 5 個
    return list(set(keywords))[:5]


def claims_to_dict(claims: List[Claim]) -> List[Dict[str, Any]]:
    """將 Claim 列表轉為 dict（用於 JSON 序列化）"""
    return [
        {
            "id": c.id,
            "text": c.text,
            "keywords": c.keywords,
            "pattern_matched": c.pattern_matched,
            "claim_type": c.claim_type
        }
        for c in claims
    ]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claim Extractor - 從文字中提取可驗證的 claims")
        print("用法: python claim_extractor.py")
        print("或:   from constitution.claim_extractor import extract_claims")
    else:
        # Demo
        demo_text = "Implement LRU cache strategy based on SRS.md §4.2, using asyncio for performance. The system shall use this approach to handle concurrent requests."
        claims = extract_claims(demo_text)
        print(f"Extracted {len(claims)} claims:")
        for c in claims:
            print(f"  [{c.claim_type}] {c.text}")
            print(f"    keywords: {c.keywords}")