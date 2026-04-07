#!/usr/bin/env python3
"""A/B Enforcer Tests"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Resolve paths relative to this file's location
_TEST_DIR = Path(__file__).parent.resolve()
_ROOT_DIR = _TEST_DIR.parent  # skills/methodology-v2
_quality_gate_dir = _ROOT_DIR / "quality_gate"

# Insert root at front so quality_gate is found directly
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

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
        self.assertIn("has_dialogue", result)
    
    def test_qa_not_developer(self):
        """測試 QA ≠ Developer 驗證"""
        result = self.enforcer.verify_qa_not_developer()
        self.assertIsInstance(result, dict)
        self.assertIn("separated", result)

if __name__ == "__main__":
    unittest.main()
