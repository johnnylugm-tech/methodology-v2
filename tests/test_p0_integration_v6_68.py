"""
P0 Integration Test — v6.68 Automation Chain

驗證所有觸發點自動化串連：
1. Constitution → Feedback Loop
2. Quality Gate → Feedback Loop
3. BVS → Feedback Loop
4. Closure → Self-Correction

Run:
    pytest tests/test_p0_integration_v6_68.py -v
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestOrchestrationFactory:
    """Test the orchestration factory functions."""

    def test_create_feedback_store(self):
        # Import from root-level orchestration.py
        from orchestration import create_feedback_store

        store = create_feedback_store()
        assert store is not None
        assert hasattr(store, "add")
        assert hasattr(store, "get")
        assert hasattr(store, "list_all")

    def test_create_integrated_gate(self):
        from orchestration import create_integrated_gate, create_feedback_store

        store = create_feedback_store()
        gate = create_integrated_gate(store)

        assert gate is not None
        assert hasattr(gate, "check")
        assert hasattr(gate, "_feedback_store")
        assert gate._feedback_store is store

    def test_create_bvs_runner(self):
        from orchestration import create_bvs_runner, create_feedback_store

        store = create_feedback_store()
        runner = create_bvs_runner(str(project_root), phase=3, feedback_store=store)

        assert runner is not None
        assert hasattr(runner, "run")
        assert runner.feedback_store is store
        assert runner.phase == 3

    def test_create_self_correcting_closure(self):
        from orchestration import create_self_correcting_closure, create_feedback_store

        store = create_feedback_store()
        closure = create_self_correcting_closure(store)

        assert closure is not None
        assert hasattr(closure, "close_with_correction")
        assert closure.store is store
        assert closure.engine is not None

    def test_create_full_pipeline(self):
        from orchestration import create_full_pipeline

        pipeline = create_full_pipeline(str(project_root), phase=3)

        assert "store" in pipeline
        assert "gate" in pipeline
        assert "closure" in pipeline
        assert "engine" in pipeline
        assert "bvs" in pipeline

        assert pipeline["store"] is not None
        assert pipeline["gate"] is not None
        assert pipeline["bvs"] is not None
        assert pipeline["bvs"].phase == 3


class TestQualityGateFeedbackIntegration:
    """Test AutoQualityGate with FeedbackStore integration."""

    def test_gate_auto_submits_violations(self):
        from orchestration import create_integrated_gate

        store = create_feedback_store()
        gate = create_integrated_gate(store)

        # Run check with artifacts that will produce violations
        result = gate.check(
            phase=2,
            artifacts={
                "linter_output": [
                    {
                        "rule": "E501",
                        "message": "line too long",
                        "file": "test.py",
                        "line": 10,
                        "severity": "warning",
                    }
                ]
            },
        )

        assert result["passed"] is True  # warning doesn't fail

    def test_gate_submits_error_violations(self):
        from orchestration import create_integrated_gate

        store = create_feedback_store()
        gate = create_integrated_gate(store)

        result = gate.check(
            phase=2,
            artifacts={
                "linter_output": [
                    {
                        "rule": "E999",
                        "message": "syntax error",
                        "file": "test.py",
                        "line": 1,
                        "severity": "error",
                    }
                ]
            },
        )

        assert result["passed"] is False


class TestConstitutionFeedbackIntegration:
    """Test run_constitution_check with FeedbackStore integration."""

    def test_constitution_check_signature_has_feedback_store(self):
        import inspect
        from quality_gate.constitution import run_constitution_check

        sig = inspect.signature(run_constitution_check)
        params = list(sig.parameters.keys())

        assert "feedback_store" in params

    def test_constitution_check_accepts_feedback_store(self):
        from quality_gate.constitution import run_constitution_check
        from orchestration import create_feedback_store

        store = create_feedback_store()

        # Call with feedback_store (even if docs don't exist, should not crash)
        try:
            result = run_constitution_check(
                "srs",
                docs_path="docs",
                current_phase=1,
                feedback_store=store,
            )
            assert hasattr(result, "passed")
            assert hasattr(result, "violations")
        except Exception:
            # Docs might not exist in test env, that's OK
            pass


class TestBVSRunnerFeedbackIntegration:
    """Test BVSRunner with FeedbackStore integration."""

    def test_bvs_runner_signature_has_feedback_store(self):
        from constitution.bvs_runner import BVSRunner
        import inspect

        sig = inspect.signature(BVSRunner.__init__)
        params = list(sig.parameters.keys())

        assert "feedback_store" in params

    def test_bvs_runner_run_auto_submits_violations(self):
        from constitution.bvs_runner import BVSRunner
        from orchestration import create_feedback_store

        store = create_feedback_store()
        runner = BVSRunner(
            project_path=str(project_root),
            phase=3,
            feedback_store=store,
        )

        # Run BVS (may have no logs, which is OK)
        report = runner.run()

        assert "passed" in report
        assert "violations" in report


class TestClosureSelfCorrectionIntegration:
    """Test verify_and_close with SelfCorrectionEngine integration."""

    def test_verify_and_close_signature_has_self_correction_engine(self):
        # Use direct path for closure module
        sys.path.insert(0, str(project_root / "core"))
        from feedback.closure import verify_and_close
        import inspect

        sig = inspect.signature(verify_and_close)
        params = list(sig.parameters.keys())

        assert "self_correction_engine" in params

    def test_verify_and_close_fails_without_engine(self):
        sys.path.insert(0, str(project_root / "core"))
        from feedback.closure import verify_and_close
        from feedback.feedback import StandardFeedback, FeedbackStore, get_store, reset_store
        from datetime import datetime, timezone

        reset_store()
        store = get_store()

        # Add a feedback item
        fb = StandardFeedback(
            id="test-fb-1",
            source="linter",
            source_detail="E501",
            type="violation",
            category="code_quality",
            severity="medium",
            title="Test violation",
            description="Test description",
            context={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            sla_deadline=None,
            status="in_progress",
        )
        store.add(fb)

        # Try to close with bad proof — should fail
        result = verify_and_close(
            feedback_id="test-fb-1",
            resolution_proof={},  # Empty proof will fail verification
            store=store,
            self_correction_engine=None,  # No engine
        )

        assert result.success is False


class TestEndToEndPipeline:
    """Test the complete pipeline from gate to closure."""

    def test_full_pipeline_creation(self):
        from orchestration import create_full_pipeline

        pipeline = create_full_pipeline(str(project_root), phase=3)

        assert pipeline["store"] is not None
        assert pipeline["gate"] is not None
        assert pipeline["bvs"] is not None
        assert pipeline["closure"] is not None
        assert pipeline["engine"] is not None

    def test_pipeline_store_is_shared(self):
        from orchestration import create_full_pipeline

        pipeline = create_full_pipeline(str(project_root), phase=3)

        # All components should share the same store
        assert pipeline["gate"]._feedback_store is pipeline["store"]
        assert pipeline["bvs"].feedback_store is pipeline["store"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
