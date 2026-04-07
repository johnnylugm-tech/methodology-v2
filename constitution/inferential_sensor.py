"""
Inferential Sensor — 推理鏈品質量化

評估 claims 的推理過程是否合理。
這是 HR-09 Claims Verifier 的核心組成部分。

使用方式：
    from constitution.inferential_sensor import InferentialSensor

    sensor = InferentialSensor()
    result = sensor.assess(
        claim={"text": "...", "keywords": [...]},
        citations=[{"text": "...", "line": 1}, ...]
    )
"""

from dataclasses import dataclass


@dataclass
class ReasoningChainAssessment:
    """推理鏈評估結果"""
    overall_score: float       # 0.0-1.0
    citation_existence: float  # 40% 權重
    citation_coverage: float   # 30% 權重
    reasoning_coherence: float # 30% 權重
    issues: list[str]          # 發現的問題
    recommendation: str        # 建議


class InferentialSensor:
    """
    推理鏈品質量化。
    評估 claims 的推理過程是否合理。
    
    這是 HR-09 Claims Verifier 的核心組成部分。
    """
    
    def __init__(self, min_coverage_threshold: float = 0.5):
        self.min_coverage_threshold = min_coverage_threshold
    
    def assess(self, claim: dict, citations: list[dict]) -> ReasoningChainAssessment:
        """
        評估 claims 的推理鏈品質。
        
        Args:
            claim: {"text": "...", "keywords": [...]}
            citations: [{"text": "...", "line": 1}, ...]
        
        Returns:
            ReasoningChainAssessment
        """
        issues = []
        
        # 維度 1: Citation 存在性 (40%)
        citation_existence = 1.0 if citations else 0.0
        if not citations:
            issues.append("No citations provided for claim")
        
        # 維度 2: Citation 覆蓋度 (30%)
        citation_coverage = self._calculate_coverage(claim, citations)
        if citation_coverage < self.min_coverage_threshold:
            issues.append(f"Citation coverage too low: {citation_coverage:.1%}")
        
        # 維度 3: 推理邏輯連貫性 (30%)
        reasoning_coherence = self._assess_coherence(claim, citations)
        
        # 計算加權總分
        overall_score = (
            citation_existence * 0.4 +
            citation_coverage * 0.3 +
            reasoning_coherence * 0.3
        )
        
        # 建議
        if overall_score >= 0.8:
            recommendation = "Claim is well-supported"
        elif overall_score >= 0.5:
            recommendation = "Claim needs additional citations or stronger reasoning"
        else:
            recommendation = "Claim is insufficiently supported — requires major revision"
        
        return ReasoningChainAssessment(
            overall_score=overall_score,
            citation_existence=citation_existence,
            citation_coverage=citation_coverage,
            reasoning_coherence=reasoning_coherence,
            issues=issues,
            recommendation=recommendation,
        )
    
    def _calculate_coverage(self, claim: dict, citations: list[dict]) -> float:
        """
        評估 Citation 對 Claim 的覆蓋度。
        使用 keyword overlap 計算。
        """
        if not citations:
            return 0.0
        
        claim_keywords = set(
            kw.lower() for kw in claim.get("keywords", [])
        )
        if not claim_keywords:
            # Fallback: 從 claim text 提取
            claim_text = claim.get("text", "").lower()
            claim_keywords = set(w for w in claim_text.split() if len(w) > 4)
        
        # 收集 citation 中的 keywords（降低門檻以包含重要術語如 lru, api, sql）
        citation_keywords = set()
        for c in citations:
            # 提取所有單詞，但只跳過非常常見的停用詞（<= 2 chars）
            citation_keywords.update(
                w.lower() for w in c.get("text", "").split()
                if len(w) > 2 and not w.lower() in {'is', 'it', 'as', 'at', 'by', 'or', 'an', 'be', 'to', 'of', 'in', 'on', 'we', 'us', 'my', 'do', 'if', 'so'}
            )
            # 也檢查是否包含 claim keywords 中的短術語（如 lru, api）
            for kw in claim_keywords:
                if len(kw) <= 4 and kw.lower() in c.get("text", "").lower():
                    citation_keywords.add(kw.lower())
        
        if not claim_keywords:
            return 0.0
        
        overlap = len(claim_keywords & citation_keywords)
        coverage = overlap / len(claim_keywords)
        return min(coverage, 1.0)  # 不超過 100%
    
    def _assess_coherence(self, claim: dict, citations: list[dict]) -> float:
        """
        評估推理邏輯是否跳步。
        使用 claim keywords 在 citation 中的覆蓋度來評估推理連貫性。
        """
        if not citations:
            return 0.0
        
        # 收集 claim keywords
        claim_keywords = set(kw.lower() for kw in claim.get("keywords", []))
        if not claim_keywords:
            # Fallback: 從 claim text 提取 keywords
            claim_text = claim.get("text", "").lower()
            claim_keywords = set(w for w in claim_text.split() if len(w) > 2)
        
        # 收集 citation text
        citation_text = " ".join(c.get("text", "").lower() for c in citations)
        
        if not claim_keywords:
            return 0.0
        
        # 計算有多少 claim keywords 出現在 citation 中
        matched_keywords = sum(
            1 for kw in claim_keywords
            if kw.lower() in citation_text
        )
        
        coherence = matched_keywords / len(claim_keywords)
        return min(coherence, 1.0)


# Standalone demo
if __name__ == "__main__":
    sensor = InferentialSensor()
    
    # Demo case
    claim = {
        "text": "The system uses LRU cache for performance optimization.",
        "keywords": ["lru", "cache", "performance"]
    }
    citations = [
        {"text": "The system shall use LRU cache strategy for performance optimization.", "line": 1},
        {"text": "Asyncio handles concurrent requests efficiently.", "line": 2}
    ]
    
    result = sensor.assess(claim, citations)
    print(f"Overall score: {result.overall_score:.2f}")
    print(f"Citation existence: {result.citation_existence:.2f}")
    print(f"Citation coverage: {result.citation_coverage:.2f}")
    print(f"Reasoning coherence: {result.reasoning_coherence:.2f}")
    print(f"Issues: {result.issues}")
    print(f"Recommendation: {result.recommendation}")
