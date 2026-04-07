"""
Self-Correction Engine — Main Correction Orchestrator.

Routes feedback violations to appropriate correction strategies and
manages the correction lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from .correction_library import CorrectionLibrary
from .ai_corrector import AICorrectorProtocol, MockAICorrector
from .strategies import (
    PatchSyntaxStrategy,
    IsortAutofixStrategy,
    RemoveUnusedStrategy,
    RuffFormatStrategy,
    ExtractFunctionStrategy,
    AddTestStubStrategy,
    BaseStrategy,
    PatchResult,
)

if TYPE_CHECKING:
    from projects.methodology_v2.core.feedback.feedback import StandardFeedback, FeedbackStore


@dataclass
class CorrectionResult:
    """
    Result of a self-correction attempt.

    Attributes:
        feedback_id: ID of the feedback being corrected.
        error_id: Internal error identifier.
        auto_fixable: Whether this was an auto-fixable correction.
        strategy: Name of the strategy that was applied (if any).
        confidence: Confidence score 0.0-1.0 in the correction.
        patched_code: The patched source code (or None if not applicable).
        verification_status: One of "success", "failed", "pending_review", "manual_required".
        correction_log: Chronological log of correction steps.
    """

    feedback_id: str
    error_id: str
    auto_fixable: bool
    strategy: str | None
    confidence: float
    patched_code: str | None
    verification_status: str
    correction_log: list[dict] = field(default_factory=list)


class SelfCorrectionEngine:
    """
    Orchestrates automatic correction of feedback violations.

    The engine classifies incoming feedback into three categories:
    - auto_fixable: Can be fixed by rule-based strategies
    - ai_assisted: Needs AI assistance for complex fixes
    - manual_required: Must be routed to a human

    It maintains a correction history and uses the CorrectionLibrary
    to learn from past experiences.
    """

    # Map of (source, category) → (strategy_name, confidence)
    AUTO_FIX_RULES: ClassVar[dict[tuple[str, str], tuple[str, float]]] = {
        ("linter", "syntax"):          ("patch_syntax", 0.95),
        ("linter", "unused-import"):   ("isort_autofix", 0.90),
        ("linter", "unused-variable"): ("remove_unused", 0.90),
        ("linter", "format"):          ("ruff_format", 0.95),
        ("linter", "pep8"):            ("ruff_format", 0.90),
        ("complexity", "cc_high"):     ("extract_function", 0.80),
        ("coverage", "gap"):           ("add_test_stub", 0.70),
        ("test_failure", "import"):   ("regenerate_import", 0.75),
    }

    AI_ASSISTED_RULES: ClassVar[dict[tuple[str, str], tuple[str, float]]] = {
        ("linter", "logic"):       ("ai_fix_logic", 0.70),
        ("quality_gate", "drift"):  ("ai_fix_architecture", 0.60),
        ("constitution", "HR-07"): ("ai_suggest_citation", 0.75),
        ("constitution", "HR-09"): ("ai_validate_claim", 0.70),
    }

    MANUAL_REQUIRED: ClassVar[frozenset[tuple[str, str]]] = frozenset([
        ("security", "cve"),
        ("drift_detector", "critical"),
        ("constitution", "HR-01"),
    ])

    def __init__(
        self,
        feedback_store: "FeedbackStore",
        ai_corrector: AICorrectorProtocol | None = None,
    ) -> None:
        """
        Initialize the self-correction engine.

        Args:
            feedback_store: The FeedbackStore to read/write feedback.
            ai_corrector: Optional AI corrector. If None, uses MockAICorrector.
        """
        self.store = feedback_store
        self.ai_corrector = ai_corrector or MockAICorrector()
        self.correction_history: list[CorrectionResult] = []

        # Initialize strategy registry
        self._strategies: dict[str, BaseStrategy] = {
            "patch_syntax":       PatchSyntaxStrategy(),
            "isort_autofix":      IsortAutofixStrategy(),
            "remove_unused":      RemoveUnusedStrategy(),
            "ruff_format":        RuffFormatStrategy(),
            "extract_function":   ExtractFunctionStrategy(),
            "add_test_stub":      AddTestStubStrategy(),
        }

        # Initialize correction library
        self.library = CorrectionLibrary()

    def correct(self, feedback_id: str) -> CorrectionResult:
        """
        Attempt to correct a feedback item.

        This is the main entry point. It:
        1. Retrieves the feedback from the store
        2. Classifies it into auto_fixable / ai_assisted / manual_required
        3. Applies the appropriate correction strategy
        4. Records the result in history and library

        Args:
            feedback_id: ID of the feedback to correct.

        Returns:
            CorrectionResult with the outcome.
        """
        feedback = self.store.get(feedback_id)
        if feedback is None:
            return CorrectionResult(
                feedback_id=feedback_id,
                error_id="not_found",
                auto_fixable=False,
                strategy=None,
                confidence=0.0,
                patched_code=None,
                verification_status="failed",
                correction_log=[{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "step": "lookup",
                    "result": "feedback_not_found",
                }],
            )

        error_id = f"{feedback.source}|{feedback.source_detail}"
        log: list[dict] = [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "lookup",
            "result": "found",
            "feedback_id": feedback_id,
        }]

        # Step 1: Classify the feedback
        classification = self._classify(feedback)
        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "classify",
            "result": classification,
        })

        # Step 2: Route to appropriate handler
        if classification == "auto_fixable":
            result = self._auto_fix(feedback, log)
        elif classification == "ai_assisted":
            result = self._ai_assisted_fix(feedback, log)
        else:
            result = self._manual_required(feedback, log)

        # Step 3: Attempt verification if we have a patch
        if result.patched_code and result.verification_status not in ("failed", "manual_required"):
            verified = self._verify(feedback, result.patched_code)
            log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": "verify",
                "result": "passed" if verified else "failed",
            })
            if not verified:
                result.verification_status = "failed"
                result.confidence *= 0.5  # Reduce confidence on failed verification
        else:
            log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": "verify",
                "result": "skipped",
                "reason": result.verification_status,
            })

        # Step 4: Record result
        result.correction_log = log
        self._record_result(result)

        return result

    def _classify(self, feedback: StandardFeedback) -> str:
        """
        Classify a feedback item into correction category.

        Args:
            feedback: The feedback item to classify.


        Returns:
            One of "auto_fixable", "ai_assisted", "manual_required".
        """
        key = (feedback.source, feedback.source_detail)

        # 1. Check MANUAL_REQUIRED (exact match)
        if key in self.MANUAL_REQUIRED:
            return "manual_required"

        # 2. Check AUTO_FIX_RULES (exact match on source_detail)
        if key in self.AUTO_FIX_RULES:
            return "auto_fixable"

        # 3. Check if source matches any AUTO_FIX source with "__any__" detail
        # (如果某些 source 有通用的 auto-fix)
        for (src, detail), (strategy, conf) in self.AUTO_FIX_RULES.items():
            if src == feedback.source and detail == "__any__":
                return "auto_fixable"

        # 4. Check AI_ASSISTED_RULES (exact match)
        if key in self.AI_ASSISTED_RULES:
            return "ai_assisted"

        # 5. Fallback: check correction library for similar successful corrections
        if self._has_successful_history(feedback):
            return "ai_assisted"

        return "manual_required"

    def _has_successful_history(self, feedback: StandardFeedback) -> bool:
        """Check if similar feedback was successfully corrected before."""
        for result in self.correction_history:
            if result.feedback_id == feedback.id and result.verification_status == "success":
                return True
        return False

    def _auto_fix(self, feedback: StandardFeedback, log: list[dict]) -> CorrectionResult:
        """
        Apply an automatic fix using rule-based strategies.

        Args:
            feedback: The feedback to fix.
            log: Correction log to append to.

        Returns:
            CorrectionResult with the patch.
        """
        key = (feedback.source, feedback.source_detail)
        strategy_info = self.AUTO_FIX_RULES.get(key)
        if strategy_info is None:
            return CorrectionResult(
                feedback_id=feedback.id,
                error_id=f"{feedback.source}|{feedback.source_detail}",
                auto_fixable=False,
                strategy=None,
                confidence=0.0,
                patched_code=None,
                verification_status="failed",
                correction_log=log,
            )

        strategy_name, base_confidence = strategy_info
        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "auto_fix",
            "strategy": strategy_name,
            "confidence": base_confidence,
        })

        strategy = self._strategies.get(strategy_name)
        if strategy is None:
            return CorrectionResult(
                feedback_id=feedback.id,
                error_id=f"{feedback.source}|{feedback.source_detail}",
                auto_fixable=False,
                strategy=None,
                confidence=0.0,
                patched_code=None,
                verification_status="failed",
                correction_log=log,
            )

        # Build context from feedback
        context = dict(feedback.context)
        if "file_path" not in context:
            context["file_path"] = feedback.source_detail

        patch_result = strategy.apply(feedback, context)

        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "apply",
            "success": patch_result.success,
            "message": patch_result.message,
        })

        return CorrectionResult(
            feedback_id=feedback.id,
            error_id=f"{feedback.source}|{feedback.source_detail}",
            auto_fixable=True,
            strategy=strategy_name,
            confidence=patch_result.confidence * base_confidence,
            patched_code=patch_result.patched_code,
            verification_status="success" if patch_result.success else "failed",
            correction_log=log,
        )

    def _ai_assisted_fix(
        self,
        feedback: StandardFeedback,
        log: list[dict],
    ) -> CorrectionResult:
        """
        Apply an AI-assisted correction.

        Args:
            feedback: The feedback to fix.
            log: Correction log to append to.

        Returns:
            CorrectionResult with the AI-generated patch.
        """
        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "ai_assisted",
            "source": feedback.source,
            "category": feedback.category,
        })

        # Retrieve similar past corrections for context
        similar = self.library.retrieve(
            source=feedback.source,
            source_detail=feedback.source_detail,
            category=feedback.category,
            limit=5,
        )

        if similar:
            log.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "step": "library_retrieval",
                "count": len(similar),
                "top_confidence": similar[0].confidence if similar else 0.0,
            })

        # Build AI correction prompt
        from .ai_corrector import build_ai_correction_prompt

        prompt = build_ai_correction_prompt(feedback, similar)
        ai_result = self.ai_corrector.correct(prompt)

        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "ai_correct",
            "confidence": ai_result.confidence,
            "has_patch": bool(ai_result.patched_code),
        })

        return CorrectionResult(
            feedback_id=feedback.id,
            error_id=f"{feedback.source}|{feedback.source_detail}",
            auto_fixable=False,
            strategy="ai_assisted",
            confidence=ai_result.confidence,
            patched_code=ai_result.patched_code if ai_result.patched_code else None,
            verification_status="pending_review",
            correction_log=log,
        )

    def _manual_required(
        self,
        feedback: StandardFeedback,
        log: list[dict],
    ) -> CorrectionResult:
        """
        Mark a feedback as requiring manual intervention.

        Args:
            feedback: The feedback item.
            log: Correction log to append to.

        Returns:
            CorrectionResult with manual_required status.
        """
        log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": "manual_required",
            "reason": f"({feedback.source}, {feedback.category}) marked as manual-only",
        })

        return CorrectionResult(
            feedback_id=feedback.id,
            error_id=f"{feedback.source}|{feedback.source_detail}",
            auto_fixable=False,
            strategy=None,
            confidence=0.0,
            patched_code=None,
            verification_status="manual_required",
            correction_log=log,
        )

    def _verify(self, feedback: StandardFeedback, patched_code: str) -> bool:
        """
        Verify that a patched code actually fixes the feedback.

        This is a lightweight verification — for full verification,
        use ClosureWithSelfCorrection which runs the full closure pipeline.

        Args:
            feedback: The original feedback.
            patched_code: The patched code to verify.

        Returns:
            True if the patch appears to fix the issue.
        """
        # Lightweight verification: check if the patch is non-empty and different
        # For more thorough verification, the ClosureWithSelfCorrection class
        # runs the actual linter/test suite
        if not patched_code or patched_code.strip() == "":
            return False

        # For syntax errors, try parsing the patched code
        if feedback.category == "syntax":
            try:
                import ast
                ast.parse(patched_code)
                return True
            except SyntaxError:
                return False

        # For other categories, accept the patch if it's non-empty
        return True

    def _record_result(self, result: CorrectionResult) -> None:
        """
        Record a correction result in history and library.

        Args:
            result: The correction result to record.
        """
        self.correction_history.append(result)

        # Store in library if we have a feedback item
        if result.feedback_id != "not_found":
            feedback = self.store.get(result.feedback_id)
            if feedback:
                self.library.store(feedback, result)



