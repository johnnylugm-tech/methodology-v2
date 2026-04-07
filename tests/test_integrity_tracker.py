#!/usr/bin/env python3
"""Integrity Tracker Tests"""
import unittest
import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quality_gate.integrity_tracker import IntegrityTracker

class TestIntegrityTracker(unittest.TestCase):
    def setUp(self):
        """Create temp project directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = IntegrityTracker(self.temp_dir)
    
    def tearDown(self):
        """Clean up temp directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initial_trust_level_full(self):
        """測試初始 FULL_TRUST 等級"""
        trust_level = self.tracker.get_trust_level()
        self.assertEqual(trust_level, "FULL_TRUST")
        self.assertEqual(self.tracker.integrity_score, 100)
    
    def test_fake_qg_penalty(self):
        """測試 fake QG 扣分 (-20)"""
        self.tracker.record_violation({
            "type": "fake_qg_result",
            "details": "虛假 Quality Gate 結果"
        })
        # Score: 100 - 20 = 80, which is still FULL_TRUST (>= 80)
        self.assertEqual(self.tracker.integrity_score, 80)
        self.assertEqual(self.tracker.get_trust_level(), "FULL_TRUST")
    
    def test_skip_phase_penalty(self):
        """測試 skip phase 扣分 (-30)"""
        self.tracker.record_violation({
            "type": "skip_phase",
            "phase": "phase_2",
            "details": "跳過 Phase"
        })
        # Score: 100 - 30 = 70, which is PARTIAL_TRUST (50-79)
        self.assertEqual(self.tracker.integrity_score, 70)
        self.assertEqual(self.tracker.get_trust_level(), "PARTIAL_TRUST")
    
    def test_combined_penalties(self):
        """測試組合扣分"""
        self.tracker.record_violation({"type": "fake_qg_result", "details": "test"})
        self.tracker.record_violation({"type": "skip_phase", "phase": "p1", "details": "test"})
        # Score: 100 - 20 - 30 = 50, which is PARTIAL_TRUST
        self.assertEqual(self.tracker.integrity_score, 50)
        self.assertEqual(self.tracker.get_trust_level(), "PARTIAL_TRUST")
    
    def test_trust_levels(self):
        """測試信任等級計算"""
        # FULL_TRUST: >= 80
        self.assertEqual(self.tracker.get_trust_level(), "FULL_TRUST")
        
        # PARTIAL_TRUST: 50-79
        self.tracker.integrity_score = 75
        self.assertEqual(self.tracker.get_trust_level(), "PARTIAL_TRUST")
        
        # LOW_TRUST: < 50
        self.tracker.integrity_score = 40
        self.assertEqual(self.tracker.get_trust_level(), "LOW_TRUST")

if __name__ == "__main__":
    unittest.main()
