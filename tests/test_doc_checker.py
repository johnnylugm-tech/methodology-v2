#!/usr/bin/env python3
"""
Quality Gate Document Checker Tests
===================================
測試 doc_checker.py 的功能
"""

import unittest
import tempfile
import os
import json
from pathlib import Path

# 假設 doc_checker.py 在 quality_gate/ 目錄下
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_gate.doc_checker import DocumentChecker, DocumentRequirement


class TestDocumentChecker(unittest.TestCase):
    """DocumentChecker 測試"""
    
    def setUp(self):
        """建立測試用臨時目錄"""
        self.test_dir = tempfile.mkdtemp()
        self.checker = DocumentChecker(self.test_dir)
    
    def tearDown(self):
        """清理測試目錄"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_check_with_no_docs(self):
        """沒有文檔時應該失敗"""
        result = self.checker.check_all()
        self.assertFalse(result["passed"])
        self.assertIn("missing", result["summary"])
    
    def test_check_with_srs(self):
        """有 SRS 文檔時應該通過"""
        # 建立 SRS.md
        Path(self.test_dir, "SRS.md").touch()
        
        result = self.checker.check_all()
        # Phase 1 應該通過
        phase1 = result["results"]["phase_1"]
        self.assertTrue(phase1["passed"])
    
    def test_check_with_sad(self):
        """有 SAD 文檔時應該通過"""
        Path(self.test_dir, "SAD.md").touch()
        
        result = self.checker.check_all()
        phase2 = result["results"]["phase_2"]
        self.assertTrue(phase2["passed"])
    
    def test_json_output(self):
        """JSON 輸出格式正確"""
        result = self.checker.check_all()
        json_str = json.dumps(result)
        
        # 應該是有效 JSON
        parsed = json.loads(json_str)
        self.assertIn("passed", parsed)
        self.assertIn("results", parsed)
    
    def test_check_with_test_plan(self):
        """有 Test Plan 時 Phase 4 通過"""
        Path(self.test_dir, "TEST_PLAN.md").touch()
        
        result = self.checker.check_all()
        phase4 = result["results"]["phase_4"]
        self.assertTrue(phase4["passed"])


class TestDocumentPatterns(unittest.TestCase):
    """文檔模式匹配測試"""
    
    def test_pattern_matching(self):
        """測試文檔模式匹配"""
        checker = DocumentChecker()
        
        # 測試 SRS 模式
        self.assertTrue(checker._matches_pattern("SRS.md", [r"SRS.*\.md"]))
        self.assertTrue(checker._matches_pattern("Software_Requirements.md", checker.SRS_PATTERNS))
        
        # 測試 SAD 模式
        self.assertTrue(checker._matches_pattern("SAD.md", [r"SAD.*\.md"]))
        self.assertTrue(checker._matches_pattern("Architecture_Design.md", checker.SAD_PATTERNS))


if __name__ == "__main__":
    unittest.main()