"""
adapters/phase_hooks_adapter.py — PhaseHooks + 13 Features Integration

整合架構：
- 包裝現有的 PhaseHooks，在 7 個鉤子點順帶呼叫對應的 Feature
- 每個 Feature 可獨立啟用/停用（feature_flags）
- Wave 1 (#11 Langfuse, #13 DecisionLog, #2 Shields, #4 KillSwitch)
- Wave 2 (#7 UQLM, #8 GapDetector, #5 LLMCascade)

Wave 1: Defend & Log
  - #11 Langfuse: 全程可觀測性（每個鉤子點加 span）
  - #13 Decision Log: 決策審計軌跡
  - #2 Prompt Shields: injection scan (warn only)
  - #4 Kill-Switch: HR-12/HR-13 熔斷

Wave 2: Score & Detect
  - #7 UQLM: hallucination detection (block mode)
  - #8 Gap Detector: test coverage gaps (warn→block on critical)
  - #5 LLM Cascade: simplified 2-model parallel review

Wave 3: Govern & Hunt
  - #1 SAIF: identity propagation (scope validation)
  - #6 Hunter: integrity validation (tampering detection)
  - #3 Governance: tier classification (HOTL/HITL/HOOTL)
"""

import sys
import time
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from functools import wraps

# Add methodology-v2 root to path for imports
METHODOLOGY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(METHODOLOGY_ROOT))

# Feature #10 LangGraph path
LANGGRAPH_ROOT = METHODOLOGY_ROOT / "implement" / "feature-10-langgraph" / "03-implement"
sys.path.insert(0, str(LANGGRAPH_ROOT))

# Import existing PhaseHooks
from phase_hooks import PhaseHooks

logger = logging.getLogger("phase_hooks_adapter")


# =============================================================================
# Exceptions
# =============================================================================

class PhaseHookError(Exception):
    """Base exception for PhaseHooks adapter errors."""
    pass


class PHASE_HOOK_FAILED(PhaseHookError):
    """Raised when a feature check fails and should block execution."""
    pass


class KillSwitchError(PhaseHookError):
    """Raised when Kill-Switch has been triggered and blocks all further hooks."""
    pass


class POSTFLIGHT_FAILED(PhaseHookError):
    """Raised when postflight check fails."""
    pass


# =============================================================================
# Feature Flags (Wave 1: all enabled by default)
# =============================================================================

DEFAULT_FEATURE_FLAGS = {
    # Wave 1: Defend & Log
    "langfuse": True,       # #11 Langfuse tracing
    "decision_log": True,    # #13 Decision Log
    "effort": True,          # #13 Effort Metrics
    "shields": True,         # #2 Prompt Shields (warn mode)
    "kill_switch": True,     # #4 Kill-Switch
    # Wave 2: Score & Detect (Wave 2: all enabled)
    "uqlm": True,           # #7 UQLM (block on high uncertainty)
    "gap_detector": True,    # #8 Gap Detector (warn→block on critical)
    "llm_cascade": True,    # #5 LLM Cascade (simplified 2-model)
    # Wave 3: Govern & Hunt (Wave 3: all enabled)
    "saif": True,            # #1 SAIF (identity propagation)
    "hunter": True,          # #6 Hunter (integrity validation)
    "governance": True,       # #3 Governance (tier classification)
    # Wave 4: Assess & Comply (Wave 4: all enabled)
    "risk": True,           # #9 Risk (warn ≥7, freeze ≥9)
    "compliance": True,     # #12 Compliance (ASPICE >80%)
    # Feature #10 LangGraph (selective extraction)
    "checkpoint": False,     # CheckpointManager for HITL resume
    "parallel": False,       # Parallel executor for Cascade
    "routing": False,        # Router for conditional routing
}


# =============================================================================
# Wave 1: Langfuse Tracing
# =============================================================================

class LangfuseTracer:
    """
    Wave 1 Feature #11: Langfuse 可觀測性
    
    在每個 PhaseHooks 鉤子點加 trace span，記錄完整決策路徑。
    失敗策略：warn (Langfuse 斷線不影響主流程)
    
    必要欄位（每個 span 必須含）:
        - trace_id: 同一 Phase 所有 spans 共用
        - agent_id: developer / reviewer / governance / ...
        - fr_id: 功能需求編號
        - hook_name: 鉤子名稱
        - start_time, end_time, latency_ms
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("langfuse", True)
        self._trace_id: Optional[str] = None
        self._span_id: int = 0
        self._spans: List[Dict] = []  # In-memory span storage (for testing)
        
        # Try to import Langfuse decorators
        self._decorators_available = False
        try:
            from ml_langfuse.decorators import observe_span, observe_decision_point
            self._observe_span = observe_span
            self._observe_decision_point = observe_decision_point
            self._decorators_available = True
        except ImportError as e:
            logger.warning(f"[Langfuse] Decorators not available: {e}")
    
    def _get_trace_id(self) -> str:
        """Get or create trace_id for this Phase."""
        if self._trace_id is None:
            self._trace_id = str(uuid.uuid4())
        return self._trace_id
    
    def _next_span_id(self) -> str:
        """Generate next span_id."""
        self._span_id += 1
        return f"span_{self._span_id:04d}"
    
    def start_span(
        self,
        hook_name: str,
        agent_id: Optional[str] = None,
        fr_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Start a new span for a hook.
        
        Returns span context dict with required fields.
        """
        if not self.enabled:
            return {"enabled": False}
        
        trace_id = self._get_trace_id()
        span_id = self._next_span_id()
        start_time = time.time()
        
        span = {
            "trace_id": trace_id,
            "span_id": span_id,
            "hook_name": hook_name,
            "agent_id": agent_id,
            "fr_id": fr_id,
            "start_time": start_time,
            "end_time": None,
            "latency_ms": None,
            "metadata": metadata or {},
            "status": "active",
        }
        
        self._spans.append(span)
        return span
    
    def end_span(
        self,
        span: Dict,
        metadata: Optional[Dict] = None,
        status: str = "ok",
    ) -> None:
        """End a span and record latency."""
        if not self.enabled or not span.get("enabled", True):
            return
        
        end_time = time.time()
        span["end_time"] = end_time
        span["latency_ms"] = (end_time - span["start_time"]) * 1000
        span["status"] = status
        
        if metadata:
            span["metadata"].update(metadata)
        
        # In production, this would flush to Langfuse
        # For now, spans are stored in-memory for testing
        logger.debug(
            f"[Langfuse] span ended: {span['hook_name']} "
            f"({span['latency_ms']:.2f}ms)"
        )
    
    def flush(self) -> List[Dict]:
        """Flush all spans and return them (for testing/debugging)."""
        return self._spans.copy()
    
    def reset(self) -> None:
        """Reset trace_id and spans (for new Phase)."""
        self._trace_id = None
        self._span_id = 0
        self._spans = []


# =============================================================================
# Wave 1: Decision Log + Effort
# =============================================================================

class DecisionLogWriter:
    """
    Wave 1 Feature #13: Decision Log
    
    強制寫入每個鉤子點的決策軌跡。
    HR-07: DEVELOPMENT_LOG session_id 記錄
    HR-15: citations 可追溯
    
    失敗策略：warn (log 寫入失敗不影響主流程)
    """
    
    def __init__(self, feature_flags: Dict[str, bool], data_dir: Optional[str] = None):
        self.enabled = feature_flags.get("decision_log", True)
        self._data_dir = Path(data_dir) if data_dir else METHODOLOGY_ROOT / "data"
        self._log_dir = self._data_dir / "decision_logs"
        self._entries: List[Dict] = []  # In-memory for testing
    
    def write(
        self,
        agent_id: str,
        fr_id: str,
        event: str,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Write a decision log entry.
        
        Args:
            agent_id: developer / reviewer / governance / shield / kill_switch
            fr_id: Functional Requirement ID (e.g., "FR-01")
            event: Event type (FR_START, DEV_DONE, REV_START, REV_DONE, etc.)
            trace_id: Langfuse trace_id for correlation
            metadata: Additional event-specific data
        """
        if not self.enabled:
            return {"enabled": False}
        
        import yaml
        
        timestamp = datetime.now().isoformat()
        
        entry = {
            "trace_id": trace_id or "",
            "span_id": "",
            "agent_id": agent_id,
            "timestamp": timestamp,
            "decision": event,
            "reasoning": metadata.get("reasoning", "") if metadata else "",
            "options_considered": metadata.get("options_considered", []) if metadata else [],
            "chosen_action": metadata.get("chosen_action", event) if metadata else event,
            "uaf_score": metadata.get("uaf_score", 0.0) if metadata else 0.0,
            "risk_score": metadata.get("risk_score", 0.0) if metadata else 0.0,
            "hitl_gate": metadata.get("hitl_gate", "") if metadata else "",
            "metadata": metadata or {},
        }
        
        # Write to YAML file (date-based)
        date_str = timestamp[:10]  # "YYYY-MM-DD"
        log_file = self._log_dir / date_str / f"{agent_id}_{int(time.time()*1000)}.yaml"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(log_file, "w") as f:
                yaml.dump(entry, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            logger.warning(f"[DecisionLog] Failed to write {log_file}: {e}")
        
        # Also keep in-memory for testing
        self._entries.append(entry)
        
        return entry
    
    def get_entries(self) -> List[Dict]:
        """Get all in-memory entries (for testing)."""
        return self._entries.copy()
    
    def clear(self) -> None:
        """Clear in-memory entries (for new Phase)."""
        self._entries = []


class EffortTracker:
    """
    Wave 1 Feature #13: Effort Metrics
    
    記錄每個 FR 的 tokens 和時間消耗。
    HR-07: session_id + effort 記錄
    
    失敗策略：warn (effort 記錄失敗不影響主流程)
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("effort", True)
        self._records: Dict[str, Dict] = {}  # fr_id -> effort record
    
    def record(
        self,
        fr_id: str,
        agent: str,
        tokens: int = 0,
        time_ms: float = 0.0,
    ) -> Dict:
        """Record effort for a specific FR and agent."""
        if not self.enabled:
            return {"enabled": False}
        
        if fr_id not in self._records:
            self._records[fr_id] = {
                "fr_id": fr_id,
                "developer_tokens": 0,
                "developer_time_ms": 0.0,
                "reviewer_tokens": 0,
                "reviewer_time_ms": 0.0,
                "total_tokens": 0,
                "total_time_ms": 0.0,
            }
        
        record = self._records[fr_id]
        if agent == "developer":
            record["developer_tokens"] += tokens
            record["developer_time_ms"] += time_ms
        elif agent == "reviewer":
            record["reviewer_tokens"] += tokens
            record["reviewer_time_ms"] += time_ms
        
        record["total_tokens"] = record["developer_tokens"] + record["reviewer_tokens"]
        record["total_time_ms"] = record["developer_time_ms"] + record["reviewer_time_ms"]
        
        logger.debug(
            f"[Effort] {fr_id}/{agent}: tokens={tokens}, time_ms={time_ms:.2f}"
        )
        
        return record
    
    def get_summary(self) -> Dict:
        """Get effort summary for all FRs."""
        return {
            "frs": self._records,
            "total_tokens": sum(r["total_tokens"] for r in self._records.values()),
            "total_time_ms": sum(r["total_time_ms"] for r in self._records.values()),
        }
    
    def clear(self) -> None:
        """Clear all records (for new Phase)."""
        self._records = {}


# =============================================================================
# Wave 1: Prompt Shields
# =============================================================================

class PromptShieldWrapper:
    """
    Wave 1 Feature #2: Prompt Shields (warn mode)
    
    在 monitoring_after_dev() 掃描 developer 輸出。
    HR-09: Claims Verifier 需通過
    
    Wave 1 策略：warn only (記錄但不打斷流程)
    Wave 3 升級：block (發現 injection 直接拋異常)
    
    失敗策略：warn (shield 失敗也繼續流程)
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("shields", True)
        self._shield = None
        self._verdict = None
        
        if self.enabled:
            try:
                from implement.security import PromptShield
                self._shield = PromptShield()
            except ImportError as e:
                logger.warning(f"[Shield] PromptShield not available: {e}")
                self.enabled = False
    
    def check(self, content: str) -> Dict:
        """
        Scan content for injection patterns.
        
        Returns:
            Dict with keys: passed, blocked, verdict, reason
        """
        if not self.enabled or self._shield is None:
            return {"passed": True, "blocked": False, "verdict": "SKIPPED"}
        
        try:
            result = self._shield.check(content)
            verdict = result.verdict.name if hasattr(result, 'verdict') else "UNKNOWN"
            
            # Wave 1: warn only, don't block
            is_blocked = verdict == "BLOCK"
            
            if is_blocked:
                logger.warning(
                    f"[Shield] ⚠️ INJECTION_DETECTED: {result.matched_patterns if hasattr(result, 'matched_patterns') else 'unknown'}"
                )
            
            return {
                "passed": not is_blocked,
                "blocked": is_blocked,
                "verdict": verdict,
                "reason": str(result.matched_patterns) if hasattr(result, 'matched_patterns') else "",
            }
        except Exception as e:
            logger.warning(f"[Shield] Check failed: {e}")
            return {"passed": True, "blocked": False, "verdict": "ERROR", "reason": str(e)}


# =============================================================================
# Wave 1: Kill-Switch
# =============================================================================

class KillSwitchWrapper:
    """
    Wave 1 Feature #4: Kill-Switch
    
    HR-12: A/B > 5 輪 → PAUSE
    HR-13: Phase > 3× 預估 → PAUSE
    
    失敗策略：block (Kill-Switch 觸發後阻擋所有後續操作)
    """
    
    def __init__(self, feature_flags: Dict[str, bool], project_path: str):
        self.enabled = feature_flags.get("kill_switch", True)
        self._triggered = False
        self._trigger_reason: Optional[str] = None
        self._kill_switch = None
        self._interrupt_engine = None
        
        if self.enabled:
            try:
                from implement.kill_switch import KillSwitch, InterruptEngine, StateManager
                state_manager = StateManager()
                self._kill_switch = KillSwitch(state_manager=state_manager)
                self._interrupt_engine = InterruptEngine(state_manager=state_manager)
            except ImportError as e:
                logger.warning(f"[KillSwitch] KillSwitch not available: {e}")
                self._kill_switch = None
                self._interrupt_engine = None
    
    def trigger(self, fr_id: str, reason: str) -> None:
        """Trigger kill-switch for a specific FR."""
        if self._triggered:
            return  # Already triggered, no-op
        
        self._triggered = True
        self._trigger_reason = reason
        
        # Call actual KillSwitch interrupt engine if available
        if self._interrupt_engine:
            try:
                from implement.kill_switch.enums import KillReason
                self._interrupt_engine.trigger_interrupt(
                    agent_id=fr_id,
                    reason=reason,
                    triggered_by="PhaseHooksAdapter",
                    reason_type=KillReason.MANUAL_TRIGGER,
                )
            except Exception as e:
                logger.error(f"[KillSwitch] trigger_interrupt failed: {e}")
        
        logger.warning(
            f"[KillSwitch] 🚨 TRIGGERED: fr_id={fr_id}, reason={reason}"
        )
    
    def is_triggered(self) -> bool:
        """Check if kill-switch has been triggered."""
        return self._triggered
    
    def get_reason(self) -> Optional[str]:
        """Get the reason for kill-switch trigger."""
        return self._trigger_reason
    
    def reset(self) -> None:
        """Reset kill-switch state (for new Phase)."""
        self._triggered = False
        self._trigger_reason = None


# =============================================================================
# PhaseHooksAdapter (Wave 1: #11 Langfuse + #13 + #2 + #4)
# =============================================================================

class PhaseHooksAdapter:
    """
    PhaseHooks 的 Feature 整合適配器
    
    包裝現有的 PhaseHooks，在每個鉤子點順帶呼叫對應的 Feature 程式碼。
    每個 Feature 可透過 feature_flags 獨立啟用/停用。
    
    使用方式：
        adapter = PhaseHooksAdapter("/path/to/project", phase=3)
        
        adapter.preflight_all()
        adapter.monitoring_before_dev("FR-01")
        adapter.monitoring_after_dev("FR-01", dev_result)
        ...
    
    Wave 1 Features:
        - #11 Langfuse: tracing (observe_span on every hook)
        - #13 Decision Log: decision audit trail
        - #13 Effort: tokens/time tracking
        - #2 Prompt Shields: injection scan (warn mode)
        - #4 Kill-Switch: HR-12/HR-13 circuit breaker
    
    Wave 2 Features:
        - #7 UQLM: hallucination detection (block mode)
        - #8 Gap Detector: test coverage gaps (warn→block on critical)
        - #5 LLM Cascade: simplified 2-model parallel review
    """
    
    def __init__(
        self,
        project_path: str,
        phase: int = None,
        feature_flags: Optional[Dict[str, bool]] = None,
    ):
        # PhaseHooks instance (wrapped)
        self.phase_hooks = PhaseHooks(project_path, phase)
        
        # Feature flags (merged with defaults)
        self.feature_flags = {**DEFAULT_FEATURE_FLAGS, **(feature_flags or {})}
        
        # Project info
        self.project_path = Path(project_path)
        self.phase = phase
        self.phase_start_time = time.time()
        self.estimated_time: Optional[float] = None  # Set by caller if known
        
        # Wave 1 Features
        self.langfuse = LangfuseTracer(self.feature_flags)
        self.decision_log = DecisionLogWriter(self.feature_flags)
        self.effort = EffortTracker(self.feature_flags)
        self.shield = PromptShieldWrapper(self.feature_flags)
        self.kill_switch = KillSwitchWrapper(self.feature_flags, project_path)
        
        # Wave 2 Features (lazy init)
        self.uqlm = None
        self.gap_detector = None
        self.llm_cascade = None
        
        # Feature #10 (selective extraction): checkpoint + parallel + routing
        self.checkpoint_mgr = None  # CheckpointManager for HITL resume
        self.graph_runner = None     # GraphRunner for parallel execution
        self.router = None          # Router for conditional routing
        
        # Wave 3 Features (lazy init)
        self.saif = None
        self.hunter = None
        self.governance = None
        
        # Wave 4 Features (lazy init)
        self.risk = None       # RiskAssessor for 8-dimension assessment
        self.compliance = None # ComplianceReporter for ASPICE tracking
        
        # Runtime state
        self._uaf_scores: Dict[str, float] = {}  # fr_id -> uaf_score (for Wave 3)
        self._current_fr_id: Optional[str] = None
        self._cascade_consensus = False  # Track consensus for cascade skip logic
        self._governance_tier: Optional[str] = None  # Track current tier for governance
        self._risk_profile: Optional[Dict[str, Any]] = None  # Last risk profile (Wave 4)
    
    def _init_wave2(self) -> None:
        """Lazy initialization of Wave 2 features."""
        if self.uqlm is None and self.feature_flags.get("uqlm", False):
            try:
                from adapters.wave2_features import UQLMWrapper
                self.uqlm = UQLMWrapper(self.feature_flags)
                logger.info("[Wave2] UQLM initialized")
            except Exception as e:
                logger.warning(f"[Wave2] UQLM init failed: {e}")
        
        if self.gap_detector is None and self.feature_flags.get("gap_detector", False):
            try:
                from adapters.wave2_features import GapDetectorWrapper
                self.gap_detector = GapDetectorWrapper(self.feature_flags, str(self.project_path))
                logger.info("[Wave2] GapDetector initialized")
            except Exception as e:
                logger.warning(f"[Wave2] GapDetector init failed: {e}")
        
        if self.llm_cascade is None and self.feature_flags.get("llm_cascade", False):
            try:
                from adapters.wave2_features import LLMCascadeWrapper
                self.llm_cascade = LLMCascadeWrapper(self.feature_flags)
                logger.info("[Wave2] LLMCascade initialized")
            except Exception as e:
                logger.warning(f"[Wave2] LLMCascade init failed: {e}")
    
    def _init_feature_10(self) -> None:
        """Lazy initialization of Feature #10 (LangGraph selective extraction)."""
        if self.checkpoint_mgr is None and self.feature_flags.get("checkpoint", False):
            try:
                from ml_langgraph.checkpoint import CheckpointManager, MemoryCheckpointBackend
                backend = MemoryCheckpointBackend()
                self.checkpoint_mgr = CheckpointManager(backend)
                logger.info("[Feature#10] CheckpointManager initialized")
            except ImportError as e:
                logger.warning(f"[Feature#10] CheckpointManager not available: {e}")
        
        if self.graph_runner is None and self.feature_flags.get("parallel", False):
            try:
                from ml_langgraph.executor import GraphRunner
                from ml_langgraph.state import AgentState
                # GraphRunner needs a compiled graph, so we create a simple one
                from ml_langgraph.builder import GraphBuilder
                state_schema = AgentState
                builder = GraphBuilder(state_schema=state_schema)
                self.graph_runner = GraphRunner(builder)
                logger.info("[Feature#10] GraphRunner initialized")
            except ImportError as e:
                logger.warning(f"[Feature#10] GraphRunner not available: {e}")
        
        if self.router is None and self.feature_flags.get("routing", False):
            try:
                from ml_langgraph.routing import Router, RouteResult
                # Default routes (can be customized via config)
                self.router = Router({
                    "dev": ["developer_node"],
                    "rev": ["reviewer_node"],
                    "gov": ["governance_node"],
                })
                # Set default routing function that routes based on 'step' key
                def default_route_fn(state):
                    return state.get("step", "dev")
                self.router._routing_fn = default_route_fn
                logger.info("[Feature#10] Router initialized")
            except ImportError as e:
                logger.warning(f"[Feature#10] Router not available: {e}")
    
    def _init_wave3(self) -> None:
        """Lazy initialization of Wave 3 features."""
        if self.saif is None and self.feature_flags.get("saif", False):
            try:
                from adapters.wave3_features import SAIFWrapper
                self.saif = SAIFWrapper(self.feature_flags, str(self.project_path))
                logger.info("[Wave3] SAIF initialized")
            except Exception as e:
                logger.warning(f"[Wave3] SAIF init failed: {e}")
        
        if self.hunter is None and self.feature_flags.get("hunter", False):
            try:
                from adapters.wave3_features import HunterWrapper
                self.hunter = HunterWrapper(self.feature_flags)
                logger.info("[Wave3] Hunter initialized")
            except Exception as e:
                logger.warning(f"[Wave3] Hunter init failed: {e}")
        
        if self.governance is None and self.feature_flags.get("governance", False):
            try:
                from adapters.wave3_features import GovernanceWrapper
                self.governance = GovernanceWrapper(self.feature_flags)
                logger.info("[Wave3] Governance initialized")
            except Exception as e:
                logger.warning(f"[Wave3] Governance init failed: {e}")
    
    def _init_wave4(self) -> None:
        """Lazy initialization of Wave 4 features."""
        if self.risk is None and self.feature_flags.get("risk", False):
            try:
                from adapters.wave4_features import RiskAssessmentWrapper
                self.risk = RiskAssessmentWrapper(self.feature_flags, str(self.project_path))
                logger.info("[Wave4] RiskAssessment initialized")
            except Exception as e:
                logger.warning(f"[Wave4] Risk init failed: {e}")
        
        if self.compliance is None and self.feature_flags.get("compliance", False):
            try:
                from adapters.wave4_features import ComplianceWrapper
                self.compliance = ComplianceWrapper(self.feature_flags, str(self.project_path))
                logger.info("[Wave4] Compliance initialized")
            except Exception as e:
                logger.warning(f"[Wave4] Compliance init failed: {e}")
    
    # =========================================================================
    # PRE-FLIGHT HOOKS
    # =========================================================================
    
    def preflight_all(self) -> Dict[str, Any]:
        """
        PRE-FLIGHT: 執行所有預檢查 + Feature 整合
        
        Wave 1 Features:
            - #11 Langfuse: 啟動 trace session
        """
        trace_id = self.langfuse._get_trace_id()
        span = self.langfuse.start_span(
            hook_name="preflight_all",
            agent_id="system",
            fr_id=None,
            metadata={"phase": self.phase},
        )
        
        try:
            # Call original PhaseHooks preflight
            result = self.phase_hooks.preflight_all()
            
            # Langfuse: end span with result
            self.langfuse.end_span(
                span,
                metadata={
                    "phase": self.phase,
                    "passed": result.get("all_passed", False),
                },
                status="ok" if result.get("all_passed") else "error",
            )
            
            return result
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    # =========================================================================
    # MONITORING HOOKS
    # =========================================================================
    
    def monitoring_before_dev(self, fr_id: str) -> None:
        """
        MONITORING: Developer 執行前的鉤子
        
        Wave 1 Features:
            - #11 Langfuse: trace span
            - #13 Decision Log: FR_START event
        """
        self._current_fr_id = fr_id
        
        span = self.langfuse.start_span(
            hook_name="monitoring_before_dev",
            agent_id="developer",
            fr_id=fr_id,
        )
        
        try:
            # Original behavior
            self.phase_hooks.monitoring_before_dev(fr_id)
            
            # Decision Log: FR_START
            trace_id = self.langfuse._get_trace_id()
            self.decision_log.write(
                agent_id="developer",
                fr_id=fr_id,
                event="FR_START",
                trace_id=trace_id,
            )
            
            self.langfuse.end_span(span, metadata={"fr_id": fr_id})
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    def monitoring_after_dev(self, fr_id: str, result: Any = None) -> Dict[str, Any]:
        """
        MONITORING: Developer 執行完成後的鉤子
        
        Wave 1 Features:
            - #11 Langfuse: trace span
            - #13 Decision Log: DEV_DONE event + shield_result
            - #2 Prompt Shields: injection scan (warn mode)
            - #13 Effort: record developer tokens/time
        
        Args:
            fr_id: Functional Requirement ID
            result: Developer execution result (with .content, .tokens, .time_ms)
        
        Returns:
            Dict with keys: passed, shield_result, error
        """
        span = self.langfuse.start_span(
            hook_name="monitoring_after_dev",
            agent_id="developer",
            fr_id=fr_id,
        )
        
        return_val = {"passed": True, "shield_result": None, "error": None}
        
        try:
            # Original behavior
            self.phase_hooks.monitoring_after_dev(fr_id, result)
            
            # Feature #2: Prompt Shields (warn mode - Wave 1)
            content = getattr(result, 'content', '') if result else ''
            shield_result = self.shield.check(content)
            return_val["shield_result"] = shield_result
            
            # Log shield result if blocked (warn only in Wave 1)
            trace_id = self.langfuse._get_trace_id()
            metadata = {
                "shield_verdict": shield_result.get("verdict", "UNKNOWN"),
                "shield_blocked": shield_result.get("blocked", False),
            }
            self.decision_log.write(
                agent_id="shield",
                fr_id=fr_id,
                event="DEV_DONE",
                trace_id=trace_id,
                metadata=metadata,
            )
            
            # Feature #13: Effort record
            tokens = getattr(result, 'tokens', 0) if result else 0
            time_ms = getattr(result, 'time_ms', 0.0) if result else 0.0
            self.effort.record(fr_id=fr_id, agent="developer", tokens=tokens, time_ms=time_ms)
            
        # Feature #13: Decision Log - DEV_DONE
            self.decision_log.write(
                agent_id="developer",
                fr_id=fr_id,
                event="DEV_DONE",
                trace_id=trace_id,
                metadata={
                    "tokens": tokens,
                    "time_ms": time_ms,
                    "shield_result": shield_result,
                },
            )
            
            # Wave 2: Lazy init
            self._init_wave2()
            
            # Feature #7: UQLM hallucination check
            uqlm_result = None
            if self.uqlm and content:
                uqlm_result = self.uqlm.compute(
                    prompt=getattr(result, 'prompt', '') if result else '',
                    response=content,
                )
                self._uaf_scores[fr_id] = uqlm_result.get("uaf_score", 0.0)
                return_val["uqlm_result"] = uqlm_result
                
                # UQLM block on high uncertainty
                if uqlm_result.get("blocked"):
                    logger.warning(f"[UQLM] 🚫 BLOCKING FR-{fr_id}: uaf={uqlm_result.get('uaf_score')}")
                    return_val["passed"] = False
                    return_val["uqlm_blocked"] = True
            
            # Wave 3: Lazy init
            self._init_wave3()
            
            # Feature #6: Hunter integrity validation
            hunter_result = None
            if self.hunter and content:
                hunter_result = self.hunter.validate_content(content, context=f"FR-{fr_id}")
                return_val["hunter_result"] = hunter_result
                
                if hunter_result.get("blocked"):
                    logger.warning(f"[Hunter] 🚫 BLOCKING FR-{fr_id}: severity={hunter_result.get('severity')}")
                    return_val["passed"] = False
                    return_val["hunter_blocked"] = True
            
            # Feature #3: Governance tier classification
            governance_tier = None
            if self.governance:
                governance_tier = self.governance.classify_operation(
                    operation_type="code_generation",
                    risk_level="routine",
                    scope="single_agent",
                )
                self._governance_tier = governance_tier.get("tier")
                return_val["governance_tier"] = governance_tier
            
            self.langfuse.end_span(
                span,
                metadata={
                    "fr_id": fr_id,
                    "shield_result": shield_result.get("verdict"),
                    "tokens": tokens,
                    "uaf_score": uqlm_result.get("uaf_score") if uqlm_result else None,
                    "hunter_severity": hunter_result.get("severity") if hunter_result else None,
                    "governance_tier": governance_tier.get("tier") if governance_tier else None,
                },
            )
            
        except Exception as e:
            return_val["passed"] = False
            return_val["error"] = str(e)
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
        
        return return_val
    
    def monitoring_before_rev(self, fr_id: str) -> None:
        """
        MONITORING: Reviewer 執行前的鉤子
        
        Wave 1 Features:
            - #11 Langfuse: trace span
            - #13 Decision Log: REV_START event
        
        Wave 2 Features:
            - #8 Gap Detector: quick scan (warn only, ≤5s)
        """
        span = self.langfuse.start_span(
            hook_name="monitoring_before_rev",
            agent_id="reviewer",
            fr_id=fr_id,
        )
        
        try:
            # Wave 2: Lazy init
            self._init_wave2()
            
            # Original behavior
            self.phase_hooks.monitoring_before_rev(fr_id)
            
            # Decision Log: REV_START
            trace_id = self.langfuse._get_trace_id()
            self.decision_log.write(
                agent_id="reviewer",
                fr_id=fr_id,
                event="REV_START",
                trace_id=trace_id,
            )
            
            # Feature #8: Gap Detector quick scan (warn only)
            gap_warn = None
            if self.gap_detector:
                gap_result = self.gap_detector.basic_scan(fr_id)
                if gap_result.get("warn"):
                    critical = gap_result.get("critical_gaps", [])
                    logger.warning(f"[GapDetector] ⚠️ FR-{fr_id}: {len(critical)} critical gaps")
                    gap_warn = {
                        "gap_count": gap_result.get("gap_count", 0),
                        "critical_count": len(critical),
                        "critical_gaps": [str(g) for g in critical[:3]],  # Log first 3
                    }
            
            self.langfuse.end_span(
                span,
                metadata={
                    "fr_id": fr_id,
                    "gap_warn": gap_warn,
                },
            )
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    def monitoring_after_rev(self, fr_id: str, result: Any = None) -> None:
        """
        MONITORING: Reviewer 執行完成後的鉤子
        
        Wave 1 Features:
            - #11 Langfuse: trace span
            - #13 Decision Log: REV_DONE event
            - #13 Effort: record reviewer tokens/time
        
        Args:
            fr_id: Functional Requirement ID
            result: Reviewer execution result
        """
        span = self.langfuse.start_span(
            hook_name="monitoring_after_rev",
            agent_id="reviewer",
            fr_id=fr_id,
        )
        
        try:
            # Original behavior
            self.phase_hooks.monitoring_after_rev(fr_id, result)
            
            # Decision Log: REV_DONE
            trace_id = self.langfuse._get_trace_id()
            review_status = getattr(result, 'review_status', None) if result else None
            tokens = getattr(result, 'tokens', 0) if result else 0
            time_ms = getattr(result, 'time_ms', 0.0) if result else 0.0
            
            self.decision_log.write(
                agent_id="reviewer",
                fr_id=fr_id,
                event="REV_DONE",
                trace_id=trace_id,
                metadata={
                    "review_status": review_status,
                    "tokens": tokens,
                    "time_ms": time_ms,
                },
            )
            
            # Feature #13: Effort record
            self.effort.record(fr_id=fr_id, agent="reviewer", tokens=tokens, time_ms=time_ms)
            
            # Wave 2: LLM Cascade parallel review
            cascade_result = None
            if self.llm_cascade:
                uaf = self._uaf_scores.get(fr_id, 0.0)
                if self.llm_cascade.should_skip(uaf):
                    logger.info(f"[LLMCascade] Skipping FR-{fr_id}: uaf={uaf:.2f} < 0.2 and previous consensus")
                else:
                    # Run parallel review
                    prompt = getattr(result, 'prompt', '') if result else ''
                    cascade_result = self.llm_cascade.review_parallel(
                        fr_id=fr_id,
                        prompt=f"Review FR-{fr_id}: {prompt}",
                    )
                    self._cascade_consensus = cascade_result.get("consensus", False)
                    self.llm_cascade.set_previous_consensus(self._cascade_consensus)
                    
                    # Log cascade result
                    if not cascade_result.get("skipped"):
                        logger.info(
                            f"[LLMCascade] FR-{fr_id}: consensus={cascade_result.get('consensus')}, "
                            f"model_a={cascade_result.get('model_a_approve')}, "
                            f"model_b={cascade_result.get('model_b_approve')}"
                        )
            
            self.langfuse.end_span(
                span,
                metadata={
                    "fr_id": fr_id,
                    "review_status": review_status,
                    "tokens": tokens,
                    "cascade_consensus": cascade_result.get("consensus") if cascade_result else None,
                },
            )
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    def monitoring_hr12_check(self, fr_id: str, iteration: int) -> bool:
        """
        MONITORING: HR-12 檢查
        
        HR-12: A/B > 5 輪 → Kill-Switch 觸發
        HR-13: Phase > 3× 預估時間 → Kill-Switch 觸發
        
        Wave 1 Features:
            - #11 Langfuse: trace span
            - #4 Kill-Switch: 熔斷觸發
            - #13 Decision Log: HR12_CHECK event
        
        Returns:
            True if can proceed, False if HR-12 triggered
        """
        span = self.langfuse.start_span(
            hook_name="monitoring_hr12_check",
            agent_id="kill_switch",
            fr_id=fr_id,
            metadata={"iteration": iteration},
        )
        
        try:
            # Call original PhaseHooks HR-12 check
            result = self.phase_hooks.monitoring_hr12_check(fr_id, iteration, max_iterations=5)
            
            triggered = not result
            
            # Decision Log: HR12_CHECK
            trace_id = self.langfuse._get_trace_id()
            self.decision_log.write(
                agent_id="kill_switch",
                fr_id=fr_id,
                event="HR12_CHECK",
                trace_id=trace_id,
                metadata={
                    "iteration": iteration,
                    "triggered": triggered,
                    "reason": "hr12" if triggered else None,
                },
            )
            
            # Feature #4: Kill-Switch trigger
            if triggered:
                self.kill_switch.trigger(fr_id=fr_id, reason="hr12")
                
                # Feature #12: Compliance - record HR12 trigger event
                if self.compliance:
                    self.compliance.record_hr12_trigger(fr_id=fr_id, iteration=iteration)
            
            # Feature #4: HR-13 timeout check
            if self.estimated_time and self.phase_start_time:
                elapsed = time.time() - self.phase_start_time
                timeout_threshold = self.estimated_time * 3
                if elapsed > timeout_threshold:
                    self.kill_switch.trigger(fr_id=fr_id, reason="hr13_timeout")
                    triggered = True
                    self.decision_log.write(
                        agent_id="kill_switch",
                        fr_id=fr_id,
                        event="HR13_TIMEOUT",
                        trace_id=trace_id,
                        metadata={
                            "elapsed_ms": elapsed * 1000,
                            "estimated_ms": self.estimated_time * 1000,
                            "threshold_ms": timeout_threshold * 1000,
                        },
                    )
            
            self.langfuse.end_span(
                span,
                metadata={
                    "fr_id": fr_id,
                    "iteration": iteration,
                    "triggered": triggered,
                },
            )
            
            # If kill-switch is triggered, raise exception to block further execution
            if self.kill_switch.is_triggered():
                raise KillSwitchError(
                    f"Kill-Switch triggered for {fr_id}: {self.kill_switch.get_reason()}"
                )
            
            return result
            
        except KillSwitchError:
            self.langfuse.end_span(span, status="error")
            raise
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    # =========================================================================
    # POST-FLIGHT HOOKS
    # =========================================================================
    
    def postflight_all(self) -> Dict[str, Any]:
        """
        POST-FLIGHT: Phase 結束後的所有檢查
        
        Wave 1 Features:
            - #11 Langfuse: flush all spans
            - #13 Effort: effort summary
            - #13 Decision Log: PHASE_DONE event
        """
        span = self.langfuse.start_span(
            hook_name="postflight_all",
            agent_id="system",
            fr_id=None,
        )
        
        try:
            # Call original PhaseHooks postflight
            result = self.phase_hooks.postflight_all()
            
            # Feature #13: Effort summary
            effort_summary = self.effort.get_summary()
            
            # Feature #13: Decision Log - PHASE_DONE
            trace_id = self.langfuse._get_trace_id()
            self.decision_log.write(
                agent_id="system",
                fr_id=None,
                event="PHASE_DONE",
                trace_id=trace_id,
                metadata={
                    "phase": self.phase,
                    "effort_summary": effort_summary,
                },
            )
            
            # Feature #11: Flush Langfuse spans
            all_spans = self.langfuse.flush()
            
            # Feature #9: Risk Assessment (after gap_detector, before final result)
            risk_result = None
            if self.risk:
                self._init_wave4()
                risk_profile = self.risk.assess(phase=self.phase)
                self._risk_profile = risk_profile
                risk_result = risk_profile
                
                # Log risk level
                risk_level = risk_profile.get("level", "OK")
                risk_aggregate = risk_profile.get("aggregate", 0.0)
                
                if risk_level == "WARN":
                    self.decision_log.write(
                        agent_id="risk",
                        fr_id=None,
                        event="RISK_HIGH",
                        trace_id=trace_id,
                        metadata={"aggregate": risk_aggregate, "level": risk_level},
                    )
                    logger.warning(f"[Risk] ⚠️ RISK_HIGH: aggregate={risk_aggregate:.2f}")
                elif risk_level == "FREEZE":
                    self.decision_log.write(
                        agent_id="risk",
                        fr_id=None,
                        event="RISK_FREEZE",
                        trace_id=trace_id,
                        metadata={"aggregate": risk_aggregate, "level": risk_level},
                    )
                    logger.error(f"[Risk] 🚫 RISK_FREEZE: aggregate={risk_aggregate:.2f}")
                
                # Generate RISK_REGISTER.md for all levels (OK/WARN/FREEZE)
                if self.risk:
                    register = self.risk.generate_register()
                    if register.get("blocked"):
                        raise POSTFLIGHT_FAILED(f"RISK_CRITICAL: aggregate={risk_aggregate:.2f} >= 9.0")
            
            # Feature #12: Compliance - generate phase report
            compliance_result = None
            if self.compliance:
                self._init_wave4()
                compliance_result = self.compliance.generate_phase_report(phase=self.phase)
                
                # Log compliance warning if ASPICE rate below threshold
                if compliance_result.get("warn"):
                    aspice_rate = compliance_result.get("aspice_rate", 0) * 100
                    self.decision_log.write(
                        agent_id="compliance",
                        fr_id=None,
                        event="COMPLIANCE_WARN",
                        trace_id=trace_id,
                        metadata={"aspice_rate": aspice_rate},
                    )
                    logger.warning(f"[Compliance] ⚠️ ASPICE rate {aspice_rate:.1f}% below 80% threshold")
            
            self.langfuse.end_span(
                span,
                metadata={
                    "phase": self.phase,
                    "effort_summary": effort_summary,
                    "span_count": len(all_spans),
                    "risk_aggregate": risk_result.get("aggregate") if risk_result else None,
                    "risk_level": risk_result.get("level") if risk_result else None,
                    "aspice_rate": compliance_result.get("aspice_rate") if compliance_result else None,
                },
            )
            
            # Reset for next Phase
            self.langfuse.reset()
            self.effort.clear()
            self.decision_log.clear()
            self.kill_switch.reset()
            if self.compliance:
                self.compliance.reset_events()
            
            return {
                **result,
                "effort_summary": effort_summary,
                "span_count": len(all_spans),
                "risk_profile": risk_result,
                "compliance_report": compliance_result,
            }
            
        except Exception as e:
            self.langfuse.end_span(span, metadata={"error": str(e)}, status="error")
            raise
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def check_kill_switch(self) -> None:
        """
        Check if kill-switch is triggered and raise exception if so.
        Call this before any critical operation.
        """
        if self.kill_switch.is_triggered():
            raise KillSwitchError(
                f"Kill-Switch already triggered: {self.kill_switch.get_reason()}"
            )
    
    def set_estimated_time(self, estimated_time: float) -> None:
        """
        Set the estimated phase duration for HR-13 timeout calculation.
        
        Args:
            estimated_time: Estimated time in seconds
        """
        self.estimated_time = estimated_time
    
    def get_uaf_score(self, fr_id: str) -> Optional[float]:
        """Get UAF score for a specific FR (set by Wave 2 UQLM)."""
        return self._uaf_scores.get(fr_id)
    
    def set_uaf_score(self, fr_id: str, score: float) -> None:
        """Set UAF score for a specific FR."""
        self._uaf_scores[fr_id] = score
    
    def get_feature_status(self) -> Dict[str, bool]:
        """Get status of all features (enabled/disabled)."""
        return {
            "langfuse": self.feature_flags.get("langfuse", True),
            "decision_log": self.feature_flags.get("decision_log", True),
            "effort": self.feature_flags.get("effort", True),
            "shields": self.feature_flags.get("shields", True),
            "kill_switch": self.feature_flags.get("kill_switch", True),
        }


# =============================================================================
# CLI Entry Point (for testing)
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PhaseHooksAdapter CLI")
    parser.add_argument("--project", "-p", required=True, help="Project path")
    parser.add_argument("--phase", type=int, required=True, help="Phase number")
    parser.add_argument("--hook", required=True, help="Hook to test")
    parser.add_argument("--fr-id", default="FR-01", help="FR ID")
    parser.add_argument(
        "--feature-flags",
        default="",
        help="Comma-separated feature flags (e.g., langfuse=1,shields=0)",
    )
    
    args = parser.parse_args()
    
    # Parse feature flags
    feature_flags = {}
    for flag in args.feature_flags.split(","):
        if "=" in flag:
            key, val = flag.split("=")
            feature_flags[key.strip()] = val.strip() == "1" or val.lower() == "true"
    
    # Create adapter
    adapter = PhaseHooksAdapter(args.project, args.phase, feature_flags)
    
    print(f"Feature flags: {adapter.get_feature_status()}")
    print(f"PhaseHooks version: {adapter.phase_hooks.__class__.__name__}")
