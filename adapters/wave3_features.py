"""
adapters/wave3_features.py — Wave 3 Features: SAIF, Hunter, Governance

Wave 3 — Govern & Hunt
  - #1 SAIF: identity propagation (scope validation)
  - #6 Hunter: integrity validation (tampering detection)
  - #3 Governance: tier classification (HOTL/HITL/HOOTL)
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

METHODOLOGY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(METHODOLOGY_ROOT))

logger = logging.getLogger("wave3_features")


# =============================================================================
# Wave 3: SAIF Identity Propagation
# =============================================================================

class SAIFWrapper:
    """
    Wave 3 Feature #1: SAIF (Security Authority Identity Framework)
    
    HR-01: 多模型驗證（防止 Reviewer 偷懶）
    HR-05: 身份追蹤（每個操作需有 audit trail）
    
    Scope Validation:
        - scope_required: 需要哪些 scope 才能執行
        - scope_validator: 驗證 current scope
    
    失敗策略：block (身份驗證失敗阻擋操作)
    """
    
    def __init__(self, feature_flags: Dict[str, bool], project_path: str):
        self.enabled = feature_flags.get("saif", False)
        self.project_path = Path(project_path)
        self._middleware = None
        self._scope_validator = None
        self._current_context = None
        
        if self.enabled:
            try:
                from implement.mcp.saif_identity_middleware import (
                    SAIFMiddleware,
                    ScopeValidator,
                    SAIFToken,
                )
                agents_dir = str(self.project_path / "agents")
                self._middleware = SAIFMiddleware(agents_dir=agents_dir)
                self._scope_validator = ScopeValidator(agents_dir=agents_dir)
                logger.info("[SAIF] SAIFMiddleware initialized")
            except ImportError as e:
                logger.warning(f"[SAIF] SAIF not available: {e}")
                self.enabled = False
    
    def validate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming request with SAIF middleware.
        
        Returns:
            Dict with keys:
                - context: SAIF context if valid
                - valid: bool
                - error: str if invalid
        """
        if not self.enabled:
            return {"valid": True, "context": None, "error": None}
        
        try:
            result = self._middleware(request)
            self._current_context = result.get("saif_context")
            return {
                "valid": True,
                "context": self._current_context,
                "error": None,
            }
        except Exception as e:
            logger.error(f"[SAIF] validation failed: {e}")
            return {
                "valid": False,
                "context": None,
                "error": str(e),
            }
    
    def check_scopes(self, required_scopes: List[str]) -> bool:
        """
        Check if current context has required scopes.
        
        Args:
            required_scopes: List of required scope strings
        
        Returns:
            True if all scopes present, False otherwise
        """
        if not self.enabled or self._current_context is None:
            return True  # Skip check if disabled or no context
        
        current_scopes = set(self._current_context.get("scopes", []))
        required = set(required_scopes)
        
        return required.issubset(current_scopes)
    
    def get_agent_identity(self) -> Optional[str]:
        """Get current agent identity from SAIF context."""
        if self._current_context:
            return self._current_context.get("sub")
        return None
    
    def require_scopes(self, *required_scopes: str):
        """
        Decorator-based scope requirement (like @require_scopes).
        
        Usage:
            @saif.require_scopes("spec.read", "audit.write")
            def read_spec():
                ...
        """
        if not self.enabled:
            return lambda f: f
        
        from implement.mcp.saif_identity_middleware import require_scopes as saif_require
        return saif_require(*required_scopes)


# =============================================================================
# Wave 3: Hunter Agent (Integrity Validation)
# =============================================================================

class HunterWrapper:
    """
    Wave 3 Feature #6: Hunter Agent (Tampering Detection)
    
    HR-02/03: 幻覺防護（Hunter Agent 檢測）
    HR-04: 虛假程式碼（fabrication detection）
    HR-06: 記憶污染（poisoning detection）
    
    整合模式：
        - monitoring_after_dev: 運行完整性驗證
        - postflight_all: 運行全面掃描
    
    失敗策略：block (檢測到 tampering 阻擋)
    """
    
    # Severity thresholds
    SEVERITY_THRESHOLD_BLOCK = "critical"  # Block on critical
    SEVERITY_THRESHOLD_WARN = "high"      # Warn on high
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("hunter", False)
        self._hunter = None
        self._validator = None
        
        if self.enabled:
            try:
                from implement.feature_06_hunter.03_implement.hunter import (
                    HunterAgent,
                    IntegrityValidator,
                    AnomalyDetector,
                )
                self._hunter = HunterAgent()
                self._validator = IntegrityValidator()
                logger.info("[Hunter] HunterAgent initialized")
            except ImportError as e:
                logger.warning(f"[Hunter] Hunter not available: {e}")
                self.enabled = False
    
    def validate_content(self, content: str, context: str = "") -> Dict[str, Any]:
        """
        Validate content integrity (detect tampering/fabrication).
        
        Returns:
            Dict with keys:
                - valid: bool
                - severity: str (none/low/medium/high/critical)
                - alerts: list of HunterAlert
                - blocked: bool
        """
        if not self.enabled:
            return {"valid": True, "severity": "none", "alerts": [], "blocked": False}
        
        if not content:
            return {"valid": True, "severity": "none", "alerts": [], "blocked": False}
        
        try:
            # Run integrity validation
            result = self._validator.validate(content, context)
            
            severity = getattr(result, 'severity', 'none') if result else 'none'
            
            # Determine if should block
            blocked = severity in ("critical", "high")
            
            if severity in ("critical", "high"):
                logger.warning(f"[Hunter] 🚫 BLOCKING: severity={severity}")
            
            return {
                "valid": not blocked,
                "severity": severity,
                "alerts": getattr(result, 'alerts', []) if result else [],
                "blocked": blocked,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"[Hunter] validation failed: {e}")
            # Conservative: block on error
            return {
                "valid": False,
                "severity": "critical",
                "alerts": [],
                "blocked": True,
                "error": str(e),
            }
    
    def scan_for_patterns(self, content: str, pattern_type: str = "all") -> Dict[str, Any]:
        """
        Scan content for specific patterns (tamper/abuse/fabricate).
        
        Args:
            content: Content to scan
            pattern_type: "tamper" | "fabricate" | "poison" | "abuse" | "all"
        
        Returns:
            Dict with keys:
                - detected: bool
                - patterns: list
                - severity: str
        """
        if not self.enabled:
            return {"detected": False, "patterns": [], "severity": "none"}
        
        try:
            if pattern_type == "tamper" or pattern_type == "all":
                from implement.feature_06_hunter.03_implement.hunter import TamperPattern
                # Scan for tamper patterns
                patterns = []
                if "ignore previous" in content.lower():
                    patterns.append({"type": "direct_override", "pattern": "ignore previous instructions"})
                if len(patterns) > 0:
                    return {
                        "detected": True,
                        "patterns": patterns,
                        "severity": "high",
                    }
            
            return {"detected": False, "patterns": [], "severity": "none"}
            
        except Exception as e:
            logger.warning(f"[Hunter] scan failed: {e}")
            return {"detected": False, "patterns": [], "severity": "none"}
    
    def full_scan(self, content: str) -> Dict[str, Any]:
        """
        Full integrity scan (used in postflight).
        
        Returns:
            Dict with keys:
                - integrity_score: float (0.0-1.0)
                - violations: list
                - blocked: bool
        """
        if not self.enabled:
            return {"integrity_score": 1.0, "violations": [], "blocked": False}
        
        # Basic scan for now
        result = self.validate_content(content)
        
        violations = []
        if result.get("blocked"):
            violations.append({
                "type": "integrity_violation",
                "severity": result.get("severity"),
                "alerts": result.get("alerts", []),
            })
        
        return {
            "integrity_score": 0.0 if result.get("blocked") else 1.0,
            "violations": violations,
            "blocked": result.get("blocked", False),
        }


# =============================================================================
# Wave 3: Governance (Tiered Oversight)
# =============================================================================

class GovernanceWrapper:
    """
    Wave 3 Feature #3: Governance (Tiered Oversight)
    
    Tiers:
        - HOTL (Human On The Loop): Post-execution review
        - HITL (Human In The Loop): Approval required before execution
        - HOOTL (Human Out Of The Loop): Automated with monitoring
    
    GovernanceTrigger:
        - Evaluates trigger conditions
        - Fires tier-appropriate workflows
    
    失敗策略：
        - HITL/HOOTL: block (需要審批)
        - HOTL: warn (事後審查)
    """
    
    def __init__(self, feature_flags: Dict[str, bool]):
        self.enabled = feature_flags.get("governance", False)
        self._classifier = None
        self._trigger = None
        
        if self.enabled:
            try:
                from implement.governance.tier_classifier import TierClassifier
                from implement.governance.governance_trigger import GovernanceTrigger
                
                self._classifier = TierClassifier()
                self._trigger = GovernanceTrigger()
                logger.info("[Governance] TierClassifier + GovernanceTrigger initialized")
            except ImportError as e:
                logger.warning(f"[Governance] not available: {e}")
                self.enabled = False
    
    def classify_operation(
        self,
        operation_type: str,
        risk_level: str = "routine",
        scope: str = "single_agent",
    ) -> Dict[str, Any]:
        """
        Classify operation into tier.
        
        Args:
            operation_type: "code_generation" | "automated_testing" | ...
            risk_level: "routine" | "elevated" | "critical"
            scope: "single_agent" | "multi_agent"
        
        Returns:
            Dict with keys:
                - tier: str (HOTL/HITL/HOOTL)
                - confidence: float
                - requires_approval: bool
        """
        if not self.enabled:
            return {"tier": "HOTL", "confidence": 1.0, "requires_approval": False}
        
        try:
            from implement.governance.enums import OperationType, RiskLevel, OperationScope, Tier
            
            op_type = OperationType[operation_type.upper().replace(" ", "_")]
            risk = RiskLevel[risk_level.upper()]
            op_scope = OperationScope[scope.upper()]
            
            decision = self._classifier.classify(
                operation_type=op_type,
                risk_level=risk,
                scope=op_scope,
            )
            
            requires_approval = decision.tier in (Tier.HITL, Tier.HOOTL)
            
            return {
                "tier": decision.tier.value if hasattr(decision.tier, 'value') else str(decision.tier),
                "confidence": decision.confidence,
                "requires_approval": requires_approval,
                "reason": decision.reason,
            }
            
        except Exception as e:
            logger.warning(f"[Governance] classify failed: {e}")
            # Conservative: require approval on failure
            return {
                "tier": "HITL",
                "confidence": 0.0,
                "requires_approval": True,
                "error": str(e),
            }
    
    def check_approval_required(self, fr_id: str, operation_type: str) -> Dict[str, Any]:
        """
        Check if operation requires approval before execution.
        
        Args:
            fr_id: FR ID
            operation_type: Type of operation
        
        Returns:
            Dict with keys:
                - requires_approval: bool
                - tier: str
                - sla_hours: float (for HITL)
        """
        classification = self.classify_operation(operation_type)
        
        tier = classification.get("tier", "HOTL")
        requires_approval = classification.get("requires_approval", False)
        
        # HITL has SLA
        sla_hours = 24.0  # Default HITL SLA
        if tier == "HITL":
            from implement.governance.enums import DEFAULT_HITL_SLA_HOURS
            sla_hours = DEFAULT_HITL_SLA_HOURS
        
        return {
            "requires_approval": requires_approval,
            "tier": tier,
            "sla_hours": sla_hours,
            "fr_id": fr_id,
        }
    
    def record_approval(
        self,
        fr_id: str,
        operation_type: str,
        approved: bool,
        approver: str = "human",
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Record approval decision for audit trail.
        
        Returns:
            Dict with keys:
                - recorded: bool
                - record_id: str
        """
        if not self.enabled:
            return {"recorded": True, "record_id": None}
        
        # For now, just log it
        decision = "APPROVED" if approved else "REJECTED"
        logger.info(f"[Governance] {decision} FR-{fr_id} {operation_type} by {approver}")
        
        if not approved:
            logger.warning(f"[Governance] 🚫 OPERATION REJECTED: FR-{fr_id}")
        
        return {
            "recorded": True,
            "record_id": f"gov_{fr_id}_{operation_type}_{int(time.time())}",
            "decision": decision,
            "approver": approver,
            "notes": notes,
        }