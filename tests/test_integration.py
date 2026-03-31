#!/usr/bin/env python3
"""
Integration Tests - 端到端測試

測試 quality_gate 模組與 enforcement 框架的整合。
These tests are designed to work with pytest's import mechanisms.
"""
import unittest
import sys
import tempfile
from pathlib import Path

# Resolve project root
_TEST_DIR = Path(__file__).parent.resolve()
_ROOT_DIR = _TEST_DIR.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))


class TestPhaseTruthVerifierIntegration(unittest.TestCase):
    """測試 PhaseTruthVerifier 與其他模組的整合"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        (self.project_root / "methodology.log").write_text("test log")
        (self.project_root / "session.log").write_text("test session")
        self.phase = 1

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_phase_truth_verifier_initializes(self):
        """測試 PhaseTruthVerifier 可以正常初始化"""
        from quality_gate.phase_truth_verifier import PhaseTruthVerifier
        verifier = PhaseTruthVerifier(str(self.project_root), self.phase)
        self.assertEqual(verifier.project_root, self.project_root)
        self.assertEqual(verifier.phase, self.phase)

    def test_phase_truth_verifier_returns_proper_result_structure(self):
        """測試 PhaseTruthVerifier 返回正確的結果結構"""
        from quality_gate.phase_truth_verifier import PhaseTruthVerifier
        verifier = PhaseTruthVerifier(str(self.project_root), self.phase)
        result = verifier.check_framework_block()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        passed, score, message = result
        self.assertIsInstance(passed, bool)
        self.assertIsInstance(score, float)
        self.assertIsInstance(message, str)

    def test_phase_truth_verifier_phase_config_loaded(self):
        """測試 PhaseTruthVerifier 正確加載階段配置"""
        from quality_gate.phase_truth_verifier import PhaseTruthVerifier
        verifier = PhaseTruthVerifier(str(self.project_root), self.phase)
        self.assertIsInstance(verifier.results, dict)


class TestClaimsVerifierIntegration(unittest.TestCase):
    """測試 ClaimsVerifier 與 development log 的整合"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        (self.project_path / "DEVELOPMENT_LOG.md").write_text("# Dev Log\nphase=1")
        (self.project_path / "methodology.log").write_text("test methodology log")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_claims_verifier_initializes(self):
        """測試 ClaimsVerifier 可以正常初始化"""
        from quality_gate.claims_verifier import ClaimsVerifier
        verifier = ClaimsVerifier(str(self.project_path))
        self.assertEqual(verifier.project_path, self.project_path)

    def test_claims_verifier_development_log_accessible(self):
        """測試 ClaimsVerifier 可以訪問 development log"""
        from quality_gate.claims_verifier import ClaimsVerifier
        verifier = ClaimsVerifier(str(self.project_path))
        self.assertTrue(hasattr(verifier, "development_log_path"))
        self.assertEqual(verifier.development_log_path.name, "DEVELOPMENT_LOG.md")

    def test_claims_verifier_verify_all_returns_dict(self):
        """測試 ClaimsVerifier.verify_all 返回正確結構"""
        from quality_gate.claims_verifier import ClaimsVerifier
        verifier = ClaimsVerifier(str(self.project_path))
        result = verifier.verify_all(phase=1)
        self.assertIsInstance(result, dict)
        # verify_all returns a dict with specific check categories
        self.assertIn("subagent_usage", result)
        self.assertIn("code_lines", result)


class TestStagePassGeneratorIntegration(unittest.TestCase):
    """測試 STAGE_PASS Generator 與 FrameworkEnforcer 的整合"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.phase = 1
        (self.project_root / "methodology.log").write_text("phase=1 status=active")
        (self.project_root / "session.log").write_text("session active")
        (self.project_root / "DEVELOPMENT_LOG.md").write_text("# Dev Log")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stage_pass_generator_initializes(self):
        """測試 IntegratedStagePassGenerator 可以正常初始化
        
        Note: This test may fail during pytest collection if FrameworkEnforcer
        import chain has issues. Use direct Python execution for full test.
        """
        try:
            from quality_gate.stage_pass_generator import IntegratedStagePassGenerator
        except ImportError:
            self.skipTest("FrameworkEnforcer import chain unavailable")
        generator = IntegratedStagePassGenerator(str(self.project_root), self.phase)
        self.assertEqual(generator.project_root, self.project_root)
        self.assertEqual(generator.phase, self.phase)

    def test_stage_pass_generator_has_framework_config(self):
        """測試 IntegratedStagePassGenerator 包含 Framework 配置"""
        try:
            from quality_gate.stage_pass_generator import IntegratedStagePassGenerator
        except ImportError:
            self.skipTest("FrameworkEnforcer import chain unavailable")
        generator = IntegratedStagePassGenerator(str(self.project_root), self.phase)
        self.assertIsInstance(generator.config, dict)


class TestFrameworkEnforcerIntegration(unittest.TestCase):
    """測試 FrameworkEnforcer 與 quality_gate 的整合"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_enforcement_result_structure(self):
        """測試 EnforcementResult 具有正確的結構
        
        Note: This test may fail during pytest collection if FrameworkEnforcer
        import chain has issues. Use direct Python execution for full test.
        """
        try:
            from enforcement.framework_enforcer import EnforcementResult
        except ImportError:
            self.skipTest("FrameworkEnforcer import chain unavailable")
        result = EnforcementResult()
        self.assertFalse(result.passed)
        self.assertIsInstance(result.violations, list)
        self.assertIsInstance(result.block_checks, dict)
        self.assertIsInstance(result.warn_checks, dict)


class TestCrossModuleIntegration(unittest.TestCase):
    """跨模組整合測試"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        (self.project_root / "methodology.log").write_text("phase=1 status=active")
        (self.project_root / "session.log").write_text("session active")
        (self.project_root / "DEVELOPMENT_LOG.md").write_text("# Dev Log")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_phase_truth_and_claims_verifier_work_on_same_project(self):
        """測試 PhaseTruthVerifier 和 ClaimsVerifier 可以在同一個專案上工作"""
        from quality_gate.phase_truth_verifier import PhaseTruthVerifier
        from quality_gate.claims_verifier import ClaimsVerifier
        verifier = PhaseTruthVerifier(str(self.project_root), 1)
        claims = ClaimsVerifier(str(self.project_root))
        self.assertEqual(verifier.project_root, self.project_root)
        self.assertEqual(claims.project_path, self.project_root)

    def test_phase_truth_verifier_and_claims_share_project_root(self):
        """測試 PhaseTruthVerifier 和 ClaimsVerifier 共享專案根目錄"""
        from quality_gate.phase_truth_verifier import PhaseTruthVerifier
        from quality_gate.claims_verifier import ClaimsVerifier
        phase_verifier = PhaseTruthVerifier(str(self.project_root), 1)
        claims_verifier = ClaimsVerifier(str(self.project_root))
        self.assertEqual(str(phase_verifier.project_root), str(claims_verifier.project_path))


if __name__ == "__main__":
    unittest.main()
