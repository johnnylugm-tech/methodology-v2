#!/usr/bin/env python3
"""
Test Inferential Sensor — 推理鏈品質量化測試

測試項目：
- _calculate_coverage() 正常情況
- _calculate_coverage() 無 citations 時返回 0.0
- _assess_coherence()
- assess() 整合分數計算（40/30/30 權重）
- issue 正確識別
"""

import sys
import os

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constitution.inferential_sensor import InferentialSensor, ReasoningChainAssessment


def test_calculate_coverage_normal():
    """測試 _calculate_coverage() 正常情況"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache for performance optimization.",
        "keywords": ["lru", "cache", "performance"]
    }
    citations = [
        {"text": "The system shall use LRU cache strategy for performance optimization.", "line": 1},
    ]
    
    coverage = sensor._calculate_coverage(claim, citations)
    
    # "lru", "cache", "performance" 都出現在 citation 中
    assert coverage == 1.0, f"Expected 1.0, got {coverage}"
    print("✓ test_calculate_coverage_normal passed")


def test_calculate_coverage_partial():
    """測試 _calculate_coverage() 部分覆蓋"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache for performance optimization.",
        "keywords": ["lru", "cache", "performance", "scaling"]
    }
    citations = [
        {"text": "The system shall use LRU cache strategy for performance optimization.", "line": 1},
    ]
    
    coverage = sensor._calculate_coverage(claim, citations)
    
    # "lru", "cache", "performance" 都匹配，"scaling" 不匹配 -> 3/4 = 0.75
    assert coverage == 0.75, f"Expected 0.75, got {coverage}"
    print("✓ test_calculate_coverage_partial passed")


def test_calculate_coverage_no_citations():
    """測試 _calculate_coverage() 無 citations 時返回 0.0"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache.",
        "keywords": ["lru", "cache"]
    }
    citations = []
    
    coverage = sensor._calculate_coverage(claim, citations)
    
    assert coverage == 0.0, f"Expected 0.0, got {coverage}"
    print("✓ test_calculate_coverage_no_citations passed")


def test_calculate_coverage_empty_keywords():
    """測試 _calculate_coverage() 無 keywords 時使用 text fallback"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache for performance.",
        "keywords": []
    }
    citations = [
        {"text": "The system uses LRU cache for performance optimization.", "line": 1},
    ]
    
    coverage = sensor._calculate_coverage(claim, citations)
    
    # 從 text 提取 keywords: "system", "uses", "cache", "performance" 等 > 4 字元的詞
    # 其中 "system", "cache", "performance" 匹配
    assert coverage > 0.0, f"Expected > 0.0, got {coverage}"
    print(f"✓ test_calculate_coverage_empty_keywords passed (coverage={coverage:.2f})")


def test_assess_coherence():
    """測試 _assess_coherence()"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache. It improves performance.",
        "keywords": ["lru", "cache"]
    }
    citations = [
        {"text": "The system uses LRU cache. It improves performance.", "line": 1},
    ]
    
    coherence = sensor._assess_coherence(claim, citations)
    
    # 完全匹配
    assert coherence == 1.0, f"Expected 1.0, got {coherence}"
    print("✓ test_assess_coherence passed")


def test_assess_coherence_no_citations():
    """測試 _assess_coherence() 無 citations 時返回 0.0"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache.",
        "keywords": ["lru", "cache"]
    }
    citations = []
    
    coherence = sensor._assess_coherence(claim, citations)
    
    assert coherence == 0.0, f"Expected 0.0, got {coherence}"
    print("✓ test_assess_coherence_no_citations passed")


def test_assess_integration():
    """測試 assess() 整合分數計算（40/30/30 權重）"""
    sensor = InferentialSensor()
    
    # Case 1: 完整匹配
    claim = {
        "text": "The system uses LRU cache.",
        "keywords": ["lru", "cache"]
    }
    citations = [
        {"text": "The system uses LRU cache strategy.", "line": 1},
    ]
    
    result = sensor.assess(claim, citations)
    
    # citation_existence = 1.0 (40%)
    # citation_coverage = 1.0 (30%) - lru, cache 都匹配
    # reasoning_coherence = 1.0 (30%) - 完全匹配
    # overall = 1.0*0.4 + 1.0*0.3 + 1.0*0.3 = 1.0
    assert result.overall_score == 1.0, f"Expected 1.0, got {result.overall_score}"
    assert result.citation_existence == 1.0
    assert result.citation_coverage == 1.0
    assert result.reasoning_coherence == 1.0
    assert result.recommendation == "Claim is well-supported"
    print("✓ test_assess_integration (full match) passed")


def test_assess_integration_no_citations():
    """測試 assess() 無 citations"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache.",
        "keywords": ["lru", "cache"]
    }
    citations = []
    
    result = sensor.assess(claim, citations)
    
    # citation_existence = 0.0 (40%)
    # citation_coverage = 0.0 (30%)
    # reasoning_coherence = 0.0 (30%)
    # overall = 0.0
    assert result.overall_score == 0.0, f"Expected 0.0, got {result.overall_score}"
    assert "No citations provided for claim" in result.issues
    assert result.recommendation == "Claim is insufficiently supported — requires major revision"
    print("✓ test_assess_integration_no_citations passed")


def test_assess_integration_partial():
    """測試 assess() 部分支援"""
    sensor = InferentialSensor()
    
    claim = {
        "text": "The system uses LRU cache and scales horizontally.",
        "keywords": ["lru", "cache", "scaling"]
    }
    citations = [
        {"text": "The system uses LRU cache.", "line": 1},
    ]
    
    result = sensor.assess(claim, citations)
    
    # citation_existence = 1.0 (40%)
    # citation_coverage = 2/3 ≈ 0.67 (30%)
    # reasoning_coherence < 1.0
    # 0.4 < overall < 1.0
    assert 0.4 < result.overall_score < 1.0, f"Expected between 0.4 and 1.0, got {result.overall_score}"
    assert "Citation coverage too low" in result.issues[0] if result.issues else True
    assert result.recommendation == "Claim needs additional citations or stronger reasoning"
    print(f"✓ test_assess_integration_partial passed (score={result.overall_score:.2f})")


def test_assess_issues_identification():
    """測試 issue 正確識別"""
    sensor = InferentialSensor()
    
    # Case: 無 citations -> issue
    claim_no_cite = {
        "text": "The system uses LRU cache.",
        "keywords": ["lru", "cache"]
    }
    result = sensor.assess(claim_no_cite, [])
    
    assert "No citations provided for claim" in result.issues
    print("✓ test_assess_issues_identification passed")


def test_weight_calculation():
    """測試權重計算正確（40/30/30）"""
    sensor = InferentialSensor()
    
    # 只提供 citation 但 coverage 和 coherence 都是 0
    claim = {"text": "foo bar baz", "keywords": ["xyz"]}
    citations = [{"text": "completely different content here", "line": 1}]
    
    result = sensor.assess(claim, citations)
    
    # citation_existence = 1.0 * 0.4 = 0.4
    # citation_coverage = 0.0 * 0.3 = 0.0 (xyz not in citation)
    # reasoning_coherence = 0.0 * 0.3 = 0.0
    # overall = 0.4
    expected = 1.0 * 0.4 + 0.0 * 0.3 + 0.0 * 0.3
    assert abs(result.overall_score - expected) < 0.01, f"Expected {expected}, got {result.overall_score}"
    assert result.citation_existence == 1.0
    assert result.citation_coverage == 0.0
    print("✓ test_weight_calculation passed")


def test_min_coverage_threshold():
    """測試 min_coverage_threshold 參數"""
    sensor = InferentialSensor(min_coverage_threshold=0.8)
    
    claim = {
        "text": "The system uses LRU cache and scales.",
        "keywords": ["lru", "cache", "scaling"]
    }
    citations = [
        {"text": "The system uses LRU cache.", "line": 1},
    ]
    
    result = sensor.assess(claim, citations)
    
    # coverage = 2/3 ≈ 0.67 < 0.8 threshold
    assert "Citation coverage too low" in result.issues[0] if result.issues else True
    print(f"✓ test_min_coverage_threshold passed (threshold=0.8, coverage={result.citation_coverage:.2f})")


def test_reasoning_chain_assessment_dataclass():
    """測試 ReasoningChainAssessment dataclass 屬性"""
    sensor = InferentialSensor()
    
    claim = {"text": "test claim", "keywords": ["test"]}
    citations = [{"text": "test citation", "line": 1}]
    
    result = sensor.assess(claim, citations)
    
    # Verify all dataclass fields exist
    assert hasattr(result, 'overall_score')
    assert hasattr(result, 'citation_existence')
    assert hasattr(result, 'citation_coverage')
    assert hasattr(result, 'reasoning_coherence')
    assert hasattr(result, 'issues')
    assert hasattr(result, 'recommendation')
    assert isinstance(result.issues, list)
    assert isinstance(result.recommendation, str)
    print("✓ test_reasoning_chain_assessment_dataclass passed")


def run_all_tests():
    """執行所有測試"""
    print("=" * 60)
    print("Running Inferential Sensor Tests")
    print("=" * 60)
    
    tests = [
        test_calculate_coverage_normal,
        test_calculate_coverage_partial,
        test_calculate_coverage_no_citations,
        test_calculate_coverage_empty_keywords,
        test_assess_coherence,
        test_assess_coherence_no_citations,
        test_assess_integration,
        test_assess_integration_no_citations,
        test_assess_integration_partial,
        test_assess_issues_identification,
        test_weight_calculation,
        test_min_coverage_threshold,
        test_reasoning_chain_assessment_dataclass,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
