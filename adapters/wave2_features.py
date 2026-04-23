"""
adapters/wave2_features.py — Wave 2 Features: UQLM, Gap Detector, LLM Cascade

Wave 2 — Score & Detect
  - #7 UQLM: hallucination detection (block mode)
  - #8 Gap Detector: test coverage gaps (warn→block on critical)
  - #5 LLM Cascade: simplified 2-model parallel review
"""

import sys
import time
import asyncio
import concurrent.futures
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

METHODOLOGY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(METHODOLOGY_ROOT))

logger = logging.getLogger("wave2_features")


# =============================================================================
# Wave 2: UQLM Wrapper
# =============================================================================

class UQLMWrapper:
    """
    Wave 2 Feature #7: UQLM (Uncertainty Quantification via Language Models)
    
    HR-09: Claims Verifier 需通過
    TH-07: 信心分數 ≥90 (confidence calibration)
    
    失敗策略：保守 (block)
    - UQLM 失敗 → block
    - UAF > threshold → block
    
    Threshold:
        - uaf < 0.3 → PASS
        - 0.3 ≤ uaf < 0.5 → WARN (要求補充 citations)
        - uaf ≥ 0.5 → BLOCK (疑似幻覺)
    """
    
    UAF_THRESHOLD_WARN = 0.3
    UAF_THRESHOLD_BLOCK = 0.5
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("uqlm", False)
        self._scorer = None
        
        if self.enabled:
            try:
                from detection.uqlm_ensemble import EnsembleScorer
                from detection.data_models import EnsembleConfig
                config = EnsembleConfig(
                    weights=[0.4, 0.3, 0.3],
                    scorers=["semantic_entropy", "semantic_density", "self_consistency"],
                    n_samples=5,
                )
                self._scorer = EnsembleScorer(config)
                logger.info("[UQLM] EnsembleScorer initialized")
            except ImportError as e:
                logger.warning(f"[UQLM] EnsembleScorer not available: {e}")
                self.enabled = False
    
    def compute(self, prompt: str, response: str) -> Dict[str, Any]:
        """
        Compute UAF score for a response.
        
        Returns:
            Dict with keys:
                - uaf_score: float (0.0-1.0)
                - verdict: "PASS" | "WARN" | "BLOCK"
                - blocked: bool
        """
        if not self.enabled:
            return {"uaf_score": 0.0, "verdict": "SKIPPED", "blocked": False}
        
        if not response or len(response.strip()) == 0:
            return {"uaf_score": 1.0, "verdict": "BLOCK", "blocked": True}
        
        try:
            result = self._scorer.score(prompt, response)
            uaf_score = result.uaf_score
        except Exception as e:
            logger.error(f"[UQLM] score() failed: {e}")
            # Conservative: treat failure as high uncertainty
            return {
                "uaf_score": 0.85,
                "verdict": "BLOCK",
                "blocked": True,
                "error": str(e),
            }
        
        # Determine verdict based on threshold
        if uaf_score < self.UAF_THRESHOLD_WARN:
            verdict = "PASS"
            blocked = False
        elif uaf_score < self.UAF_THRESHOLD_BLOCK:
            verdict = "WARN"
            blocked = False
        else:
            verdict = "BLOCK"
            blocked = True
        
        return {
            "uaf_score": uaf_score,
            "verdict": verdict,
            "blocked": blocked,
            "threshold_warn": self.UAF_THRESHOLD_WARN,
            "threshold_block": self.UAF_THRESHOLD_BLOCK,
        }


# =============================================================================
# Wave 2: Gap Detector Wrapper
# =============================================================================

class GapDetectorWrapper:
    """
    Wave 2 Feature #8: Gap Detector
    
    TH-11/12: 測試覆蓋率 ≥70/80%
    TH-13: SRS FR 覆蓋 = 100%
    
    兩層架構：
    - Basic scan (monitoring_before_rev): 快速，5 秒內，warn only
    - Full scan (postflight_all): 完整報告，block on critical gap
    
    失敗策略：
    - Basic: warn (不中斷流程)
    - Full: block on critical gap
    """
    
    def __init__(self, feature_flags: Dict[str, bool], project_path: str):
        self.enabled = feature_flags.get("gap_detector", False)
        self.project_path = Path(project_path)
        self._spec_parser = None
        self._code_scanner = None
        self._detector = None
        
        if self.enabled:
            try:
                from gap_detector import SpecParser, CodeScanner, GapDetector
                self._spec_parser = SpecParser()
                self._code_scanner = CodeScanner()
                self._detector_class = GapDetector
                logger.info("[GapDetector] Initialized")
            except ImportError as e:
                logger.warning(f"[GapDetector] not available: {e}")
                self.enabled = False
    
    def basic_scan(self, fr_id: str) -> Dict[str, Any]:
        """
        Quick gap scan before review (≤5 seconds).
        
        Returns:
            Dict with keys:
                - gap_count: int
                - critical_gaps: list
                - warn: bool
        """
        if not self.enabled:
            return {"gap_count": 0, "critical_gaps": [], "warn": False}
        
        try:
            # Parse SPEC.md
            spec_path = self.project_path / "docs" / "SPEC.md"
            if not spec_path.exists():
                return {"gap_count": 0, "critical_gaps": [], "warn": False, "error": "SPEC.md not found"}
            
            spec = self._spec_parser.parse(str(spec_path))
            
            # Scan code
            src_path = self.project_path / "src"
            if not src_path.exists():
                src_path = self.project_path
            
            code = self._code_scanner.scan(str(src_path))
            
            # Detect gaps
            detector = self._detector_class(spec, code)
            gaps = detector.detect()
            summary = detector.get_summary()
            
            # Filter critical gaps
            critical = [g for g in gaps if g.severity == "critical"]
            
            if critical:
                logger.warning(f"[GapDetector] FR-{fr_id}: {len(critical)} critical gaps")
                return {
                    "gap_count": summary.total_gaps,
                    "critical_gaps": critical,
                    "warn": True,
                }
            
            return {
                "gap_count": summary.total_gaps,
                "critical_gaps": [],
                "warn": False,
            }
            
        except Exception as e:
            logger.warning(f"[GapDetector] basic_scan failed: {e}")
            return {"gap_count": 0, "critical_gaps": [], "warn": False, "error": str(e)}
    
    def full_scan(self) -> Dict[str, Any]:
        """
        Full gap scan at postflight (produces GAP_REPORT.md).
        
        Returns:
            Dict with keys:
                - gaps: list
                - summary: dict
                - report_path: str
                - blocked: bool
        """
        if not self.enabled:
            return {"gaps": [], "summary": {}, "report_path": None, "blocked": False}
        
        try:
            from gap_detector import GapReporter, ReportPaths
            
            # Parse SPEC.md
            spec_path = self.project_path / "docs" / "SPEC.md"
            if not spec_path.exists():
                return {"gaps": [], "summary": {}, "report_path": None, "blocked": False}
            
            spec = self._spec_parser.parse(str(spec_path))
            
            # Scan code
            src_path = self.project_path / "src"
            if not src_path.exists():
                src_path = self.project_path
            
            code = self._code_scanner.scan(str(src_path))
            
            # Detect gaps
            detector = self._detector_class(spec, code)
            gaps = detector.detect()
            summary = detector.get_summary()
            
            # Generate report
            report_paths = ReportPaths(
                report_dir=str(self.project_path / "docs"),
                data_dir=str(self.project_path / "data"),
            )
            reporter = GapReporter(detector, report_paths)
            reporter.generate_report()
            
            # Check for critical gaps (block on critical)
            critical = [g for g in gaps if g.severity == "critical"]
            
            return {
                "gaps": gaps,
                "summary": {
                    "total_gaps": summary.total_gaps,
                    "missing_count": summary.missing_count,
                    "incomplete_count": summary.incomplete_count,
                    "orphaned_count": summary.orphaned_count,
                },
                "report_path": report_paths.report_path,
                "critical_gaps": critical,
                "blocked": len(critical) > 0,
            }
            
        except Exception as e:
            logger.warning(f"[GapDetector] full_scan failed: {e}")
            return {"gaps": [], "summary": {}, "report_path": None, "blocked": False, "error": str(e)}


# =============================================================================
# Wave 2: LLM Cascade Wrapper (Simplified)
# =============================================================================

class LLMCascadeWrapper:
    """
    Wave 2 Feature #5: LLM Cascade (Simplified: 2-model parallel)
    
    HR-01: 強制多模型驗證，防 Reviewer 偷懶
    
    簡化設計：
    - 2 個不同 model family 同時執行 (e.g., Claude + GPT)
    - Parallel execution via ThreadPoolExecutor
    - Consensus: 兩個都 APPROVE 才通過
    
    失敗策略：warn (Cascade 失敗回退到單一 Reviewer)
    
    Skip 條件：
    - uaf_score < 0.2 AND 前次 consensus → skip (省 token)
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("llm_cascade", False)
        self._previous_consensus = False
        
        if self.enabled:
            logger.info("[LLMCascade] Initialized (simplified 2-model)")
    
    def set_previous_consensus(self, had_consensus: bool) -> None:
        """Set whether previous cascade had consensus."""
        self._previous_consensus = had_consensus
    
    def should_skip(self, uaf_score: float) -> bool:
        """
        Determine if cascade should be skipped (for efficiency).
        
        Skip if: uaf < 0.2 AND previous had consensus
        """
        if not self.enabled:
            return True
        return uaf_score < 0.2 and self._previous_consensus
    
    def review_parallel(
        self,
        fr_id: str,
        prompt: str,
        model_a: str = "claude-sonnet",
        model_b: str = "gpt-4o",
    ) -> Dict[str, Any]:
        """
        Run parallel 2-model review.
        
        Args:
            fr_id: FR ID
            prompt: Review prompt
            model_a: First model (e.g., claude-sonnet)
            model_b: Second model (e.g., gpt-4o)
        
        Returns:
            Dict with keys:
                - consensus: bool
                - model_a_result: str
                - model_b_result: str
                - skipped: bool
                - reason: str
        """
        if not self.enabled:
            return {
                "consensus": None,
                "model_a_result": None,
                "model_b_result": None,
                "skipped": True,
                "reason": "cascade_disabled",
            }
        
        try:
            # Run both models in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(self._call_model, model_a, prompt)
                future_b = executor.submit(self._call_model, model_b, prompt)
                
                model_a_result = future_a.result(timeout=60)
                model_b_result = future_b.result(timeout=60)
            
            # Determine consensus
            model_a_approve = "APPROVE" in str(model_a_result).upper()
            model_b_approve = "APPROVE" in str(model_b_result).upper()
            consensus = model_a_approve and model_b_approve
            
            self._previous_consensus = consensus
            
            return {
                "consensus": consensus,
                "model_a_result": model_a_result,
                "model_a_approve": model_a_approve,
                "model_b_result": model_b_result,
                "model_b_approve": model_b_approve,
                "skipped": False,
                "reason": None,
            }
            
        except Exception as e:
            logger.warning(f"[LLMCascade] parallel review failed: {e}")
            # Fall back to single model on error
            return {
                "consensus": None,
                "model_a_result": None,
                "model_b_result": None,
                "skipped": False,
                "reason": f"cascade_error: {str(e)}",
            }
    
    def _call_model(self, model: str, prompt: str) -> str:
        """
        Call a single model (placeholder - integrate with actual LLM API).
        
        In production, this would call the actual LLM API.
        """
        # Placeholder: simulate LLM call
        logger.info(f"[LLMCascade] Calling model: {model}")
        
        # In real implementation, this would be:
        # from implement.llm_cascade import LLMCascade
        # cascade = LLMCascade()
        # result = await cascade.route(prompt, config=...)
        
        # For now, return a mock result based on prompt length
        # (replace with actual LLM call in production)
        return "APPROVE" if len(prompt) > 50 else "REJECT"


# =============================================================================
# Parallel Executor Bridge (Feature #10 selective extraction)
# =============================================================================

class ParallelExecutorBridge:
    """
    Feature #10 (Selective): Parallel Executor for Cascade
    
    Wraps simple parallel execution patterns used by LLM Cascade.
    Only ~50 LOC, reuses concepts from ml_langgraph/executor.py
    
    Not integrating full LangGraph executor to avoid complexity.
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("parallel", False)
    
    def fan_out(
        self,
        task: Callable,
        inputs: List[Any],
        max_workers: int = 2,
    ) -> List[Any]:
        """
        Execute task in parallel for multiple inputs.
        
        Args:
            task: Callable to execute
            inputs: List of inputs
            max_workers: Max parallel workers
        
        Returns:
            List of results in same order as inputs
        """
        if not self.enabled:
            # Fall back to sequential
            return [task(inp) for inp in inputs]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(task, inp) for inp in inputs]
            results = [f.result() for f in futures]
        return results
    
    def fan_in(
        self,
        futures: List[concurrent.futures.Future],
        wait_all: bool = True,
    ) -> List[Any]:
        """
        Collect results from parallel executions.
        
        Args:
            futures: List of Future objects
            wait_all: If True, wait for all futures
        
        Returns:
            List of results
        """
        if wait_all:
            return [f.result() for f in futures]
        else:
            # Return completed only
            return [f.result() for f in futures if f.done()]
