#!/usr/bin/env python3
"""
Unit Tests - UserJourneyGenerator

執行方式：
    python -m pytest constitution/test_user_journey_generator.py -v
    python -m unittest constitution/test_user_journey_generator.py -v
"""

import unittest
import sys
import os
from pathlib import Path

# Add parent directory to path
_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from constitution.user_journey_generator import (
    UserJourneyGenerator,
    UserJourneyTest,
)


class TestUserJourneyGenerator(unittest.TestCase):
    """UserJourneyGenerator 測試"""

    def setUp(self):
        """測試前準備"""
        self.generator = UserJourneyGenerator()

    def test_generate_returns_list(self):
        """測試 generate() 返回 list[UserJourneyTest]"""
        journeys = self.generator.generate(phase=3)
        self.assertIsInstance(journeys, list)
        self.assertGreater(len(journeys), 0)
        for j in journeys:
            self.assertIsInstance(j, UserJourneyTest)

    def test_generate_returns_non_empty_for_phase_1(self):
        """測試 generate() 返回 non-empty list for Phase 1"""
        journeys = self.generator.generate(phase=1)
        self.assertGreater(len(journeys), 0)

    def test_generate_returns_non_empty_for_phase_3(self):
        """測試 generate() 返回 non-empty list for Phase 3"""
        journeys = self.generator.generate(phase=3)
        self.assertGreater(len(journeys), 0)

    def test_generate_returns_non_empty_for_phase_5(self):
        """測試 generate() 返回 non-empty list for Phase 5"""
        journeys = self.generator.generate(phase=5)
        self.assertGreater(len(journeys), 0)

    def test_user_journey_test_dataclass(self):
        """測試 UserJourneyTest dataclass 屬性"""
        journey = UserJourneyTest(
            name="test_journey",
            description="A test journey",
            phase=1,
            steps=["step1", "step2"],
            expected_outcome="success",
            is_edge_case=False,
            hr_rules_applied=["HR-03"],
        )
        self.assertEqual(journey.name, "test_journey")
        self.assertEqual(journey.description, "A test journey")
        self.assertEqual(journey.phase, 1)
        self.assertEqual(journey.steps, ["step1", "step2"])
        self.assertEqual(journey.expected_outcome, "success")
        self.assertFalse(journey.is_edge_case)
        self.assertEqual(journey.hr_rules_applied, ["HR-03"])

    def test_edge_cases_have_correct_flag(self):
        """測試 edge cases 正確標記 is_edge_case=True"""
        journeys = self.generator.generate(phase=1)
        edge_cases = [j for j in journeys if j.is_edge_case]
        # Phase 1 has 1 phase-specific edge case + 2 universal = 3 total
        self.assertGreaterEqual(len(edge_cases), 3)

        # Verify all edge_cases have is_edge_case=True
        for ec in edge_cases:
            self.assertTrue(ec.is_edge_case, f"{ec.name} should be marked as edge case")

    def test_standard_journeys_have_correct_flag(self):
        """測試 standard journeys 標記 is_edge_case=False"""
        journeys = self.generator.generate(phase=3)
        standard = [j for j in journeys if not j.is_edge_case]
        self.assertGreater(len(standard), 0)

        for j in standard:
            self.assertFalse(j.is_edge_case, f"{j.name} should NOT be marked as edge case")

    def test_hr_rules_applied_populated(self):
        """測試 hr_rules_applied 正確填充"""
        journeys = self.generator.generate(phase=3)
        # Find a journey with hr_rules_applied
        journeys_with_rules = [j for j in journeys if j.hr_rules_applied]
        self.assertGreater(len(journeys_with_rules), 0)

        for j in journeys_with_rules:
            self.assertIsInstance(j.hr_rules_applied, list)
            for rule in j.hr_rules_applied:
                self.assertIsInstance(rule, str)
                # HR rules should be in format HR-XX
                if rule:  # skip empty strings
                    self.assertTrue(
                        rule.startswith("HR-") or rule.startswith("TH-"),
                        f"{rule} should be HR or TH prefixed"
                    )

    def test_generate_hr_journeys_from_invariants(self):
        """測試 _generate_hr_journeys() 從 invariants 生成"""
        hr_journeys = self.generator._generate_hr_journeys(phase=3)

        # Phase 3 invariants: HR-12 (A/B review threshold) has phase_scope=[3,4,5,6,7,8]
        # Should generate at least one journey for HR-12
        self.assertIsInstance(hr_journeys, list)

        # All generated journeys should have phase=3
        for j in hr_journeys:
            self.assertEqual(j.phase, 3)
            # expected_outcome should contain HR- or TH- prefix
            has_rule_prefix = "HR-" in j.expected_outcome or "TH-" in j.expected_outcome
            self.assertTrue(has_rule_prefix, f"{j.expected_outcome} should contain HR- or TH-")

    def test_generate_from_paths_with_execution_log(self):
        """測試 _generate_from_paths() 使用 execution log"""
        execution_log = [
            {"phase": 3, "action": "Analyze SRS"},
            {"phase": 3, "action": "Generate claims"},
            {"phase": 3, "action": "Verify claims"},
        ]
        journeys = self.generator._generate_from_paths(phase=3, execution_log=execution_log)

        self.assertEqual(len(journeys), 1)
        journey = journeys[0]
        self.assertEqual(journey.name, "path_phase_3")
        self.assertEqual(len(journey.steps), 3)

    def test_generate_from_paths_no_matching_phase(self):
        """測試 _generate_from_paths() 沒有匹配的 phase 時返回空"""
        execution_log = [
            {"phase": 1, "action": "Phase 1 action"},
            {"phase": 2, "action": "Phase 2 action"},
        ]
        journeys = self.generator._generate_from_paths(phase=3, execution_log=execution_log)
        self.assertEqual(len(journeys), 0)

    def test_universal_edge_cases_all_phases(self):
        """測試 _get_universal_edge_cases() 所有 phase 都有 HR-12/HR-13"""
        for phase in range(1, 9):
            universal = self.generator._get_universal_edge_cases(phase=phase)

            # Should have exactly 2 universal edge cases
            self.assertEqual(len(universal), 2, f"Phase {phase} should have 2 universal edge cases")

            # Check HR-12 and HR-13 are present
            hr_rules_found = set()
            for ec in universal:
                hr_rules_found.update(ec.hr_rules_applied)

            self.assertIn("HR-12", hr_rules_found, f"Phase {phase} missing HR-12")
            self.assertIn("HR-13", hr_rules_found, f"Phase {phase} missing HR-13")

    def test_phase_specific_edge_cases(self):
        """測試每個 Phase 的 phase-specific edge cases"""
        # Phase 1
        journeys_p1 = self.generator.generate(phase=1)
        p1_edge_cases = [j for j in journeys_p1 if j.is_edge_case and j.name == "phase_skip_attempt"]
        self.assertEqual(len(p1_edge_cases), 1)

        # Phase 2
        journeys_p2 = self.generator.generate(phase=2)
        p2_edge_cases = [j for j in journeys_p2 if j.name == "missing_srs_citation"]
        self.assertEqual(len(p2_edge_cases), 1)

        # Phase 3
        journeys_p3 = self.generator.generate(phase=3)
        p3_edge_cases = [j for j in journeys_p3 if j.name == "self_review_attempt"]
        self.assertEqual(len(p3_edge_cases), 1)

    def test_generate_with_execution_log_includes_path_journey(self):
        """測試 generate() 包含 execution log 時會加入 path journey"""
        execution_log = [
            {"phase": 2, "action": "Extract claims"},
            {"phase": 2, "action": "Generate SRS citation"},
        ]
        journeys = self.generator.generate(phase=2, execution_log=execution_log)

        path_journeys = [j for j in journeys if j.name == "path_phase_2"]
        self.assertEqual(len(path_journeys), 1)
        self.assertEqual(len(path_journeys[0].steps), 2)

    def test_edge_case_steps_are_strings(self):
        """測試 edge case 的 steps 都是字串"""
        journeys = self.generator.generate(phase=1)

        for j in journeys:
            for step in j.steps:
                self.assertIsInstance(step, str)
                self.assertGreater(len(step), 0)

    def test_journey_name_uniqueness(self):
        """測試同一 phase 的 journey name 不重複"""
        journeys = self.generator.generate(phase=3)
        names = [j.name for j in journeys]
        unique_names = set(names)

        # Allow duplicates only if they're actually different journeys
        # This is a soft check - we mainly want to ensure no copy-paste errors
        self.assertEqual(len(names), len(unique_names), "Journey names should be unique within a phase")


class TestUserJourneyTest(unittest.TestCase):
    """UserJourneyTest dataclass 測試"""

    def test_default_values(self):
        """測試預設值"""
        journey = UserJourneyTest(
            name="test",
            description="desc",
            phase=1,
            steps=["step"],
            expected_outcome="outcome",
        )
        self.assertFalse(journey.is_edge_case)
        self.assertEqual(journey.hr_rules_applied, [])

    def test_edge_case_true(self):
        """測試 is_edge_case=True"""
        journey = UserJourneyTest(
            name="ec_test",
            description="edge case test",
            phase=1,
            steps=["step"],
            expected_outcome="outcome",
            is_edge_case=True,
            hr_rules_applied=["HR-12", "HR-13"],
        )
        self.assertTrue(journey.is_edge_case)
        self.assertEqual(len(journey.hr_rules_applied), 2)


if __name__ == "__main__":
    unittest.main()
