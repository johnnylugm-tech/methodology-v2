#!/usr/bin/env python3
"""
HR-09 Constitution Checker
===========================
使用 InferentialSensor 評估 Claims 的推理鏈品質

HR-09: Claims must be supported by citations
所有 claims 必須有可驗證的 citations，且推理鏈必須合理。

使用 InferentialSensor 評估：
1. Citation 存在性 (40%)
2. Citation 覆蓋度 (30%)
3. 推理邏輯連貫性 (30%)

閾值: overall_score >= 0.5 通過

Usage:
    from hr09_checker import HR09Checker
    
    checker = HR09Checker()
    result = checker.check(docs_path)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

# Import InferentialSensor from the constitution package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from constitution.inferential_sensor import InferentialSensor


# Claim patterns — sentences containing these are treated as claims
CLAIM_INDICATORS = [
    r'\bshould\b', r'\bmust\b', r'\bwill\b', r'\bis designed to\b',
    r'\bensures\b', r'\bguarantees\b', r'\bprovides\b', r'\bshall\b',
    r'\bimplements\b', r'\buses\b', r'\badopts\b', r'\bfollows\b',
]

# Citation patterns — markdown links to lines/sections
CITATION_PATTERN = re.compile(r'\[([^\]]+)\]\(#L(\d+)(?:-L(\d+))?\)')
CITATION_SHORT_PATTERN = re.compile(r'\[([^\]]+)\]\([^)]+#L(\d+)(?:-L(\d+))?\)')


class HR09Checker:
    """
    HR-09 Claims Verifier.
    
    Uses InferentialSensor to assess reasoning chain quality for each claim.
    A claim passes HR-09 if its overall reasoning chain score >= 0.5.
    """
    
    def __init__(self, min_score_threshold: float = 0.5):
        self.inferential_sensor = InferentialSensor(
            min_coverage_threshold=min_score_threshold
        )
        self.min_score_threshold = min_score_threshold
    
    def check(self, docs_path: str) -> Dict:
        """
        執行 HR-09 檢查
        
        Args:
            docs_path: docs 目錄路徑
            
        Returns:
            {
                "passed": bool,
                "score": float,          # 平均推理鏈分數 (0-100)
                "violations": [...],     # 分數 < 0.5 的 claims
                "results": [...],        # 每個 claim 的詳細評估
                "total_claims": int,
                "passed_claims": int,
            }
        """
        # Load all documents
        from quality_gate.constitution import load_constitution_documents
        documents = load_constitution_documents(docs_path)
        
        results = []
        total_claims = 0
        passed_claims = 0
        
        for doc_type, content in documents.items():
            if not content:
                continue
            
            # Extract claims from this document
            claims = self._extract_claims(content, doc_type)
            
            for claim in claims:
                total_claims += 1
                
                # Extract citations for this claim
                citations = self._extract_citations_for_claim(claim, content)
                
                # Use InferentialSensor to assess reasoning chain
                assessment = self.inferential_sensor.assess(
                    claim={"text": claim["text"], "keywords": claim["keywords"]},
                    citations=citations
                )
                
                passed = assessment.overall_score >= self.min_score_threshold
                if passed:
                    passed_claims += 1
                
                results.append({
                    "doc": doc_type,
                    "claim": claim["text"],
                    "claim_line": claim["line"],
                    "keywords": claim["keywords"],
                    "citations": citations,
                    "assessment": {
                        "overall_score": assessment.overall_score,
                        "citation_existence": assessment.citation_existence,
                        "citation_coverage": assessment.citation_coverage,
                        "reasoning_coherence": assessment.reasoning_coherence,
                        "issues": assessment.issues,
                        "recommendation": assessment.recommendation,
                    },
                    "passed": passed,
                })
        
        # Compute aggregate
        if results:
            avg_score = sum(r["assessment"]["overall_score"] for r in results) / len(results)
        else:
            avg_score = 1.0  # No claims = perfect score (0.0-1.0 scale, multiplied by 100 later)
        
        # Violations are claims with score < threshold
        violations = []
        for r in results:
            if not r["passed"]:
                violations.append({
                    "rule_id": "HR-09",
                    "doc": r["doc"],
                    "line": r["claim_line"],
                    "message": f"HR-09 violation: Claim at line {r['claim_line']} has insufficient reasoning chain (score={r['assessment']['overall_score']:.2f}). {r['assessment']['issues']}",
                    "claim": r["claim"],
                    "overall_score": r["assessment"]["overall_score"],
                    "citation_coverage": r["assessment"]["citation_coverage"],
                    "reasoning_coherence": r["assessment"]["reasoning_coherence"],
                    "severity": "HIGH",
                })
        
        return {
            "passed": avg_score >= self.min_score_threshold,
            "score": avg_score * 100,  # Convert 0.0-1.0 → 0-100 scale
            "violations": violations,
            "results": results,
            "total_claims": total_claims,
            "passed_claims": passed_claims,
        }
    
    def _extract_claims(self, content: str, doc_type: str) -> List[Dict]:
        """
        從文檔中提取所有 claims。
        
        Returns:
            [{"text": "...", "keywords": [...], "line": N}, ...]
        """
        claims = []
        lines = content.split('\n')
        
        claim_pattern = re.compile(
            '|'.join(CLAIM_INDICATORS), re.IGNORECASE
        )
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Check if line contains a claim indicator
            if claim_pattern.search(line):
                # Extract keywords from the claim
                keywords = self._extract_keywords(line)
                
                claims.append({
                    "text": line,
                    "keywords": keywords,
                    "line": i,
                })
        
        return claims
    
    def _extract_keywords(self, text: str) -> List[str]:
        """從文字中提取關鍵字"""
        # Extract words >= 3 chars, excluding common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'has', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'had', 'his', 'hem', 'has', 'have', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two',
            'who', 'did', 'use', 'used', 'using', 'will', 'with',
            'this', 'that', 'from', 'they', 'been', 'were', 'said',
            'each', 'she', 'which', 'their', 'time', 'would', 'there',
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Return unique keywords, up to 8
        return list(dict.fromkeys(keywords))[:8]
    
    def _extract_citations_for_claim(self, claim: Dict, content: str) -> List[Dict]:
        """
        為 claim 提取對應的 citations。
        
        Scans the document for markdown citations [text](#Ln) or [text](#Ln-Lm)
        that appear near/after the claim line.
        
        Returns:
            [{"text": "...", "line": N}, ...]
        """
        citations = []
        
        # Find all citations in the document
        for match in CITATION_PATTERN.finditer(content):
            cited_text = match.group(1)
            start_line = int(match.group(2))
            end_line = int(match.group(3)) if match.group(3) else start_line
            
            # Include if citation is on the same line or nearby lines
            # Also include if the cited text contains any claim keywords
            line_diff = abs(start_line - claim["line"])
            if line_diff <= 50:  # Within 50 lines of the claim
                citations.append({
                    "text": cited_text,
                    "line": start_line,
                    "end_line": end_line,
                })
        
        # Also look for the claim line itself having inline citations
        claim_line_match = CITATION_PATTERN.search(content.split('\n')[claim["line"] - 1] if claim["line"] <= len(content.split('\n')) else '')
        if claim_line_match:
            cited_text = claim_line_match.group(1)
            line_num = int(claim_line_match.group(2))
            # Avoid duplicates
            if not any(c["line"] == line_num for c in citations):
                citations.append({
                    "text": cited_text,
                    "line": line_num,
                    "end_line": int(claim_line_match.group(3)) if claim_line_match.group(3) else line_num,
                })
        
        return citations


# Module-level convenience function
def check_hr09_constitution(docs_path: str) -> Dict:
    """
    執行 HR-09 Constitution 檢查（便捷函數）
    
    Returns:
        HR-09 check result dict
    """
    checker = HR09Checker()
    return checker.check(docs_path)


if __name__ == "__main__":
    import json
    import sys
    
    docs_path = sys.argv[1] if len(sys.argv) > 1 else "docs"
    result = check_hr09_constitution(docs_path)
    
    print(f"\nHR-09 Constitution Check: {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"Score: {result['score']:.1f}%")
    print(f"Claims: {result['passed_claims']}/{result['total_claims']} passed")
    print(f"Violations: {len(result['violations'])}")
    
    if result["violations"]:
        print("\nViolations:")
        for v in result["violations"]:
            print(f"  [{v['doc']}:{v['line']}] {v['message']}")
    
    if "--json" in sys.argv:
        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
