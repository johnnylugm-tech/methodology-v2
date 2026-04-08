#!/usr/bin/env python3
"""
Claim Verifier — 驗證 claims 是否被 citations 支持

HR-09 Claims Verifier 系統的核心

使用方式：
    from constitution.claim_verifier import verify_claims

    verified = verify_claims(
        claims=[{"id": "c1", "text": "使用 LRU cache", "keywords": ["lru", "cache"]}],
        citations=["SRS.md#L45"],
        artifact_content={"SRS.md": "The system shall use LRU cache strategy..."}
    )
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .claim_extractor import Claim, extract_claims, claims_to_dict
from .citation_parser import parse_citations
from .inferential_sensor import InferentialSensor

# Handle standalone execution (when running as __main__)
if __name__ == "__main__":
    import sys
    import os
    # Add parent directory to path for standalone execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class VerifiedClaim:
    """經過驗證的 claim"""
    id: str
    text: str
    claim_type: str
    keywords: List[str]
    verified: bool
    supporting_citations: List[str] = field(default_factory=list)
    supporting_count: int = 0
    reason: str = ""
    reasoning_chain_score: float = 0.0  # 推理鏈品質分數


class ClaimVerifier:
    """
    Claims 驗證器。
    
    整合 keyword-based 驗證與推理鏈品質評估。
    """
    
    def __init__(self, min_coverage_threshold: float = 0.5):
        self.inferential_sensor = InferentialSensor(
            min_coverage_threshold=min_coverage_threshold
        )
    
    def _assess_reasoning_chain(self, claim: dict, citations: list[dict]) -> float:
        """
        評估推理鏈品質。
        
        Args:
            claim: {"text": "...", "keywords": [...]}
            citations: [{"text": "...", "line": 1}, ...]
        
        Returns:
            overall_score: 0.0-1.0
        """
        result = self.inferential_sensor.assess(claim, citations)
        return result.overall_score
    
    def verify_claims(
        self,
        claims: List[Dict[str, Any]],
        citations: List[str],
        artifact_content: Dict[str, str],
        strict: bool = True
    ) -> List[VerifiedClaim]:
        """
        驗證 claims 是否被 citations 支持

        演算法：
        1. 對每個 claim，檢查其 keywords 是否出現在 cited artifact 的內容中
        2. 如果任何 keyword 匹配 → verified = True
        3. 如果 strict=True，所有 keywords 都必須匹配

        Args:
            claims: 從 claim_extractor 提取的 claims
            citations: citation 字串列表
            artifact_content: {artifact_name: content} 的字典
            strict: True = 所有 keywords 都必須匹配，False = 任一匹配即可

        Returns:
            List of VerifiedClaim objects
        """
        verified_claims = []

        # 解析 citations
        parsed_citations = parse_citations(citations)

        for claim in claims:
            claim_id = claim.get("id", "")
            claim_text = claim.get("text", "")
            claim_type = claim.get("claim_type", "unknown")
            keywords = claim.get("keywords", [])

            if not keywords:
                verified_claims.append(VerifiedClaim(
                    id=claim_id,
                    text=claim_text,
                    claim_type=claim_type,
                    keywords=keywords,
                    verified=False,
                    reason="No keywords to verify"
                ))
                continue

            # 檢查每個 keyword
            supporting = []
            missing_keywords = []

            for keyword in keywords:
                keyword_lower = keyword.lower()
                found_in = []

                # 檢查每個 cited artifact
                for parsed_cite in parsed_citations:
                    artifact_name = parsed_cite.artifact
                    content = artifact_content.get(artifact_name, "")

                    if content and keyword_lower in content.lower():
                        found_in.append(artifact_name)

                if found_in:
                    supporting.extend(found_in)
                else:
                    missing_keywords.append(keyword)

            # 去重
            supporting = list(set(supporting))

            # 判定 verified
            if strict:
                verified = len(missing_keywords) == 0
                reason = f"All keywords found in {len(supporting)} artifacts" if verified else f"Missing keywords: {missing_keywords}"
            else:
                verified = len(supporting) > 0
                reason = f"Keywords found in {len(supporting)} artifacts" if verified else f"No keywords found: {missing_keywords}"

            # 評估推理鏈品質
            reasoning_score = self._assess_reasoning_chain(
                {"text": claim_text, "keywords": keywords},
                [{"text": artifact_content.get(parsed_cite.artifact, ""), "line": 1} for parsed_cite in parsed_citations]
            )

            verified_claims.append(VerifiedClaim(
                id=claim_id,
                text=claim_text,
                claim_type=claim_type,
                keywords=keywords,
                verified=verified,
                supporting_citations=supporting,
                supporting_count=len(supporting),
                reason=reason,
                reasoning_chain_score=reasoning_score
            ))

        return verified_claims
    
    def verify_result(
        self,
        result_text: str,
        citations: List[str],
        artifact_content: Dict[str, str],
        strict: bool = True
    ) -> Dict[str, Any]:
        """
        便利函數：直接從 result text 提取並驗證 claims

        Args:
            result_text: Subagent result 文字
            citations: citation 字串列表
            artifact_content: {artifact_name: content}
            strict: 是否 strict mode

        Returns:
            {
                "total_claims": N,
                "verified_claims": N,
                "unverified_claims": N,
                "verification_rate": 0.0-1.0,
                "verified": bool,
                "claims": [...]
            }
        """
        # 提取 claims
        claims = extract_claims(result_text)
        claims_dict = claims_to_dict(claims)

        # 驗證 claims
        verified = self.verify_claims(claims_dict, citations, artifact_content, strict=strict)

        total = len(verified)
        verified_count = sum(1 for c in verified if c.verified)

        return {
            "total_claims": total,
            "verified_claims": verified_count,
            "unverified_claims": total - verified_count,
            "verification_rate": verified_count / total if total > 0 else 1.0,
            "verified": verified_count == total if strict else verified_count > 0,
            "claims": [
                {
                    "id": c.id,
                    "text": c.text,
                    "claim_type": c.claim_type,
                    "verified": c.verified,
                    "supporting_citations": c.supporting_citations,
                    "supporting_count": c.supporting_count,
                    "reason": c.reason
                }
                for c in verified
            ]
        }


# Module-level functions for backward compatibility
def verify_claims(
    claims: List[Dict[str, Any]],
    citations: List[str],
    artifact_content: Dict[str, str],
    strict: bool = True
) -> List[VerifiedClaim]:
    """
    驗證 claims 是否被 citations 支持（模組級函數，向後相容）
    """
    verifier = ClaimVerifier()
    return verifier.verify_claims(claims, citations, artifact_content, strict)


def verify_result(
    result_text: str,
    citations: List[str],
    artifact_content: Dict[str, str],
    strict: bool = True
) -> Dict[str, Any]:
    """
    便利函數：直接從 result text 提取並驗證 claims（模組級函數，向後相容）
    """
    verifier = ClaimVerifier()
    return verifier.verify_result(result_text, citations, artifact_content, strict)


def verification_to_dict(verified: List[VerifiedClaim]) -> List[Dict[str, Any]]:
    """將 VerifiedClaim 列表轉為 dict"""
    return [
        {
            "id": c.id,
            "text": c.text,
            "claim_type": c.claim_type,
            "keywords": c.keywords,
            "verified": c.verified,
            "supporting_citations": c.supporting_citations,
            "supporting_count": c.supporting_count,
            "reason": c.reason
        }
        for c in verified
    ]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Claim Verifier - 驗證 claims 是否被 citations 支持")
        print("用法: python claim_verifier.py")
        print("或:   from constitution.claim_verifier import verify_claims, verify_result")
    else:
        # Demo
        demo_text = "Implement LRU cache strategy based on SRS.md §4.2, using asyncio for performance."
        demo_citations = ["SRS.md#L45"]
        demo_artifacts = {
            "SRS.md": "The system shall use LRU cache strategy for performance optimization. Asyncio will handle concurrent requests."
        }

        result = verify_result(demo_text, demo_citations, demo_artifacts)
        print(f"Verification result:")
        print(f"  total_claims: {result['total_claims']}")
        print(f"  verified_claims: {result['verified_claims']}")
        print(f"  verification_rate: {result['verification_rate']:.2f}")
        print(f"  verified: {result['verified']}")
        for claim in result['claims']:
            print(f"  - [{claim['claim_type']}] {claim['text']}")
            print(f"      verified={claim['verified']}, reason={claim['reason']}")
