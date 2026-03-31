#!/usr/bin/env python3
"""Claims Verifier Tests"""
import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_gate.claims_verifier import ClaimsVerifier

class TestClaimsVerifier(unittest.TestCase):
    def setUp(self):
        """Create temp project directory"""
        self.temp_dir = tempfile.mkdtemp()
        # Create minimal DEVELOPMENT_LOG.md
        with open(os.path.join(self.temp_dir, "DEVELOPMENT_LOG.md"), "w") as f:
            f.write("# Development Log\n")
        self.verifier = ClaimsVerifier(self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_subagent_usage_verification(self):
        """測試 sub-agent 使用驗證"""
        result = self.verifier.verify_subagent_usage()
        self.assertIsInstance(result, dict)
        self.assertIn("match", result)
        self.assertIn("claimed", result)
        self.assertIn("actual", result)
    
    def test_code_lines_verification(self):
        """測試代碼行數驗證"""
        result = self.verifier.verify_code_lines()
        self.assertIsInstance(result, dict)
        self.assertIn("match", result)
        self.assertIn("claimed", result)
        self.assertIn("actual", result)
    
    def test_quality_gate_execution_verification(self):
        """測試 Quality Gate 執行驗證"""
        result = self.verifier.verify_quality_gate_executed()
        self.assertIsInstance(result, dict)
        self.assertIn("executed", result)

if __name__ == "__main__":
    unittest.main()
