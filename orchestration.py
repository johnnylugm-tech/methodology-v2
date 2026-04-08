"""
Orchestration — 統一初始化反饋迴路系統

提供工廠函數，確保所有模組正確串聯：
- Constitution → Feedback Loop
- Quality Gate → Feedback Loop
- BVS → Feedback Loop
- Closure → Self-Correction Engine

Usage:
    from orchestration import (
        create_integrated_gate,
        create_bvs_runner,
        create_self_correcting_closure,
        create_full_pipeline,
    )

    # 完整 pipeline
    pipeline = create_full_pipeline()
    gate = pipeline["gate"]
    bvs = pipeline["bvs"]
    closure = pipeline["closure"]
    store = pipeline["store"]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING

# Ensure both project root AND core/ are in sys.path.
# This is needed because:
# - `quality_gate.constitution` lives at project_root/quality_gate/constitution/__init__.py
# - `core.feedback` lives at project_root/core/feedback/__init__.py
# Both need to be findable.
_project_root = str(Path(__file__).parent)
_core_dir = str(Path(__file__).parent / "core")

# Add project root first (for quality_gate.X imports)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
# Then add core/ (for core.feedback.X imports)
# IMPORTANT: append to end to avoid shadowing project-root quality_gate
if _core_dir not in sys.path:
    sys.path.append(_core_dir)

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Factory Functions
# ---------------------------------------------------------------------------

def create_feedback_store() -> "FeedbackStore":
    """建立 FeedbackStore."""
    from feedback import FeedbackStore
    return FeedbackStore()


def create_self_correction_engine(
    feedback_store: "FeedbackStore | None" = None,
) -> "SelfCorrectionEngine":
    """建立 Self-Correction Engine."""
    from self_correction import SelfCorrectionEngine

    # Use explicit None check — FeedbackStore is falsy when empty (len=0),
    # so `or` would incorrectly create a new instance.
    if feedback_store is None:
        feedback_store = create_feedback_store()
    return SelfCorrectionEngine(feedback_store)


def create_integrated_gate(
    feedback_store: "FeedbackStore | None" = None,
) -> "AutoQualityGate":
    """
    建立已整合 Feedback Loop 的 Quality Gate.

    AutoQualityGate 在每次 check() 後自動將 violations 提交到 FeedbackStore.
    """
    from core.quality_gate import AutoQualityGate

    # Use explicit None check — FeedbackStore is falsy when empty (len=0),
    # so `or` would incorrectly create a new instance.
    if feedback_store is None:
        feedback_store = create_feedback_store()
    return AutoQualityGate(feedback_store=feedback_store)


def create_bvs_runner(
    project_path: str,
    phase: int = 3,
    feedback_store: "FeedbackStore | None" = None,
) -> "BVSRunner":
    """
    建立已整合 Feedback Loop 的 BVS Runner.

    BVSRunner 在每次 run() 後自動將 invariant violations 提交到 FeedbackStore.
    """
    # Import locally to avoid circular import at module level
    from constitution.bvs_runner import BVSRunner

    # Use explicit None check — FeedbackStore is falsy when empty (len=0),
    # so `or` would incorrectly create a new instance.
    if feedback_store is None:
        feedback_store = create_feedback_store()
    return BVSRunner(project_path=project_path, phase=phase, feedback_store=feedback_store)


def create_self_correcting_closure(
    feedback_store: "FeedbackStore | None" = None,
    self_correction_engine: "SelfCorrectionEngine | None" = None,
) -> "ClosureWithSelfCorrection":
    """
    建立帶 Self-Correction 的 Closure 流程.

    verify_and_close() 在 verification 失敗時自動觸發 Self-Correction Engine.
    """
    from self_correction import ClosureWithSelfCorrection, SelfCorrectionEngine
    from self_correction.correction_library import CorrectionLibrary

    # Use explicit None check — FeedbackStore is falsy when empty (len=0)
    if feedback_store is None:
        feedback_store = create_feedback_store()
    if self_correction_engine is None:
        self_correction_engine = create_self_correction_engine(feedback_store)

    correction_library = CorrectionLibrary()
    return ClosureWithSelfCorrection(
        feedback_store,
        self_correction_engine,
        correction_library=correction_library,
    )


def _create_bvs_runner_if_possible(
    project_path: str | None,
    phase: int,
    store: "FeedbackStore",
) -> "BVSRunner | None":
    """Helper: create BVSRunner only if project_path is provided."""
    if project_path is None:
        return None
    from constitution.bvs_runner import BVSRunner
    return BVSRunner(project_path=project_path, phase=phase, feedback_store=store)


def create_full_pipeline(
    project_path: str | None = None,
    phase: int = 3,
) -> dict[str, Any]:
    """
    建立完整的 Feedback Loop pipeline.

    返回 dict 包含：
    - store: FeedbackStore
    - gate: AutoQualityGate (with feedback integration)
    - bvs: BVSRunner (with feedback integration, if project_path provided)
    - closure: ClosureWithSelfCorrection
    - engine: SelfCorrectionEngine
    - run_bvs(phase): Method to run BVS and auto-submit violations to store
    - close_phase(phase): Convenience method to run closure for all feedback + BVS

    Args:
        project_path: 如果提供，會建立整合過的 BVSRunner
        phase: 預設 Phase (用於 BVS)

    Usage:
        pipeline = create_full_pipeline("/path/to/project", phase=3)
        store = pipeline["store"]
        gate = pipeline["gate"]
        bvs = pipeline["bvs"]
        closure = pipeline["closure"]

        # Quality Gate → violations auto-submitted to store
        gate_result = gate.check(phase=2, artifacts={...})

        # BVS → violations auto-submitted to store (manual trigger)
        bvs_report = pipeline["run_bvs"](phase=2)

        # Constitution check → violations auto-submitted to store
        from quality_gate.constitution import run_constitution_check
        result = run_constitution_check("srs", "docs", phase=3, feedback_store=store)

        # Closure with auto self-correction (per feedback item)
        closure_result = closure.close_with_correction(feedback_id)

        # OR: Convenience method to close ALL feedback for a phase + run BVS
        phase_result = pipeline["close_phase"](phase=3)

        # Dashboard
        from feedback.dashboard import print_dashboard
        print_dashboard(store)
    """
    from self_correction import ClosureWithSelfCorrection, SelfCorrectionEngine

    store = create_feedback_store()
    engine = SelfCorrectionEngine(store)
    closure = ClosureWithSelfCorrection(store, engine)
    gate = create_integrated_gate(store)
    bvs_runner = _create_bvs_runner_if_possible(project_path, phase, store)

    # ── BVS Auto-Trigger Methods ──────────────────────────────────────

    def run_bvs(phase: int) -> dict[str, Any]:
        """
        Run BVS for the specified phase and auto-submit violations to FeedbackStore.

        This is the key integration point: BVS violations are automatically
        captured and submitted to the feedback loop, ensuring invariant
        violations are tracked alongside quality gate and constitution violations.

        Args:
            phase: Phase number to run BVS against

        Returns:
            BVS report dict with passed/total_violations/violations/etc.
        """
        if bvs_runner is None:
            return {
                "passed": True,
                "total_violations": 0,
                "status": "no_bvs_configured",
                "message": "BVS not configured (no project_path provided)",
            }

        # Update phase and run
        bvs_runner.phase = phase
        return bvs_runner.run()

    def close_phase(phase: int) -> dict[str, Any]:
        """
        Convenience method: Close ALL feedback for a phase + run BVS.

        Flow:
        1. Get all open feedback items for the phase
        2. Attempt closure with self-correction for each
        3. Run BVS to capture invariant violations

        This ensures BVS is automatically triggered at phase boundaries
        without manual intervention.

        Args:
            phase: Phase number to close

        Returns:
            dict with closure_results and bvs_report
        """
        # Get all feedback for this phase
        all_feedback = store.list()
        phase_feedback = [
            fb for fb in all_feedback
            if fb.get("context", {}).get("phase") == phase
            and fb.get("status") not in ("closed", "resolved")
        ]

        closure_results = []
        for fb in phase_feedback:
            feedback_id = fb.get("id") or fb.get("feedback_id")
            if feedback_id:
                result = closure.close_with_correction(feedback_id)
                closure_results.append(result)

        # Run BVS to capture invariant violations for this phase
        bvs_report = run_bvs(phase)

        return {
            "phase": phase,
            "feedback_closed": len(closure_results),
            "closure_results": closure_results,
            "bvs_report": bvs_report,
        }

    result: dict[str, Any] = {
        "store": store,
        "gate": gate,
        "closure": closure,
        "engine": engine,
        "bvs": bvs_runner,
        "run_bvs": run_bvs,
        "close_phase": close_phase,
    }

    return result


# ---------------------------------------------------------------------------
# Convenience aliases for run_constitution_check with feedback integration
# ---------------------------------------------------------------------------

def run_constitution_check_with_feedback(
    check_type: str,
    docs_path: str = "docs",
    current_phase: int = None,
    feedback_store: "FeedbackStore | None" = None,
):
    """
    執行 Constitution check 並自動提交 violations 到 FeedbackStore.

    這是 run_constitution_check 的 wrapper，自動處理 feedback_store 參數。
    """
    from quality_gate.constitution import run_constitution_check as _run

    # Use explicit None check
    if feedback_store is None:
        feedback_store = create_feedback_store()
    return _run(
        check_type=check_type,
        docs_path=docs_path,
        current_phase=current_phase,
        feedback_store=feedback_store,
    )


__all__ = [
    "create_feedback_store",
    "create_self_correction_engine",
    "create_integrated_gate",
    "create_bvs_runner",
    "create_self_correcting_closure",
    "create_full_pipeline",
    "run_constitution_check_with_feedback",
]
