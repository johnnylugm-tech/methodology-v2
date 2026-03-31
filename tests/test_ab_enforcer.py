#!/usr/bin/env python3
"""A/B Enforcer Tests"""
import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_gate.ab_enforcer import ABEnforcer

class TestABEnforcer(unittest.TestCase):
    def setUp(self):
        """Create temp project directory"""
        self.temp_dir = tempfile.mkdtemp()
        # Create minimal DEVELOPMENT_LOG.md
        with open(os.path.join(self.temp_dir, "DEVELOPMENT_LOG.md"), "w") as f:
            f.write("# Development Log\n")
        self.enforcer = ABEnforcer(self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_developer_reviewer_separation(self):
        """測試 Developer/Reviewer 分離驗證"""
        result = self.enforcer.verify_developer_reviewer_separation("phase_1")
        self.assertIsInstance(result, dict)
        self.assertIn("separated", result)
        self.assertIn("developer_session", result)
        self.assertIn("reviewer_session", result)
    
    def test_ab_dialogue_exists(self):
        """測試 A/B 對話存在驗證"""
        result = self.enforcer.verify_ab_dialogue_exists("phase_1")
        self.assertIsInstance(result, dict)
        self.assertIn("exists", result)
    
    def test_qa_not_developer(self):
        """測試 QA ≠ Developer 驗證"""
        result = self.enforcer.verify_qa_not_developer()
        self.assertIsInstance(result, dict)
        self.assertIn("qa_is_not_dev", result)

if __name__ == "__main__":
    unittest.main()
