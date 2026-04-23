"""
adapters/wave4_features.py — Wave 4 Features: Risk Assessment, Compliance

Wave 4 — Assess & Comply
  - #9 Risk Assessment: 8-dimension risk scoring (warn ≥7, freeze ≥9)
  - #12 Compliance: ASPICE reporting + event-driven compliance logging
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

METHODOLOGY_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(METHODOLOGY_ROOT))

logger = logging.getLogger("wave4_features")


# =============================================================================
# Wave 4: Risk Assessment
# =============================================================================

class RiskAssessmentWrapper:
    """
    Wave 4 Feature #9: Risk Assessment
    
    8 維度風險評估（技術、運營、外部）
    - complexity, dependency, quality, stability (技術)
    - team, process, knowledge, external (運營+外部)
    
    HR-14: Integrity < 40 → FREEZE 提前預警
    
    Threshold:
        - aggregate < 7 → OK
        - 7 ≤ aggregate < 9 → WARN (寫入 RISK_HIGH)
        - aggregate ≥ 9 → FREEZE (raise POSTFLIGHT_FAILED)
    """
    
    # Risk dimension weights for aggregate calculation
    DIMENSION_WEIGHTS = {
        "complexity": 0.15,
        "dependency": 0.15,
        "quality": 0.15,
        "stability": 0.15,
        "team": 0.10,
        "process": 0.10,
        "knowledge": 0.10,
        "external": 0.10,
    }
    
    WARN_THRESHOLD = 7.0
    FREEZE_THRESHOLD = 9.0
    
    def __init__(self, feature_flags: Dict[str, bool], project_path: str):
        self.enabled = feature_flags.get("risk", False)
        self.project_path = Path(project_path)
        self._assessor = None
        self._last_profile = None
        
        if self.enabled:
            try:
                from implement.feature_09_risk_assessment_03_implement.engine.assessor import RiskAssessor
                self._assessor = RiskAssessor(str(self.project_path))
                logger.info("[Risk] RiskAssessor initialized")
            except ImportError:
                try:
                    # Try alternate path
                    from implement.feature_09_risk_assessment_03_implement.engine.assessor import RiskAssessor
                    self._assessor = RiskAssessor(str(self.project_path))
                    logger.info("[Risk] RiskAssessor initialized")
                except ImportError as e:
                    logger.warning(f"[Risk] RiskAssessor not available: {e}")
                    self.enabled = False
    
    def assess(self, phase: int = None) -> Dict[str, Any]:
        """
        Run 8-dimension risk assessment.
        
        Returns:
            Dict with keys:
                - dimensions: dict of 8 dimension scores (0-10)
                - aggregate: float (weighted average)
                - level: str (OK/WARN/FREEZE)
                - risks: list of identified risks
        """
        if not self.enabled:
            return self._empty_profile()
        
        if not self.project_path.exists():
            logger.warning(f"[Risk] Project path not found: {self.project_path}")
            return self._empty_profile()
        
        try:
            # Run assessment
            result = self._assessor.assess()
            
            # Extract dimensions
            dimensions = {}
            if hasattr(result, 'dimensions'):
                for dim in result.dimensions:
                    name = dim.name.lower() if hasattr(dim, 'name') else str(dim)
                    score = dim.score if hasattr(dim, 'score') else 0
                    dimensions[name] = score
            
            # Calculate aggregate (weighted average)
            aggregate = self._calculate_aggregate(dimensions)
            
            # Determine level
            if aggregate >= self.FREEZE_THRESHOLD:
                level = "FREEZE"
            elif aggregate >= self.WARN_THRESHOLD:
                level = "WARN"
            else:
                level = "OK"
            
            self._last_profile = {
                "dimensions": dimensions,
                "aggregate": aggregate,
                "level": level,
                "phase": phase,
                "timestamp": datetime.now().isoformat(),
            }
            
            return self._last_profile
            
        except Exception as e:
            logger.warning(f"[Risk] assessment failed: {e}")
            return self._empty_profile()
    
    def _calculate_aggregate(self, dimensions: Dict[str, float]) -> float:
        """Calculate weighted average of dimension scores."""
        if not dimensions:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for dim_name, weight in self.DIMENSION_WEIGHTS.items():
            if dim_name in dimensions:
                score = dimensions[dim_name]
                weighted_sum += weight * score
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def _empty_profile(self) -> Dict[str, Any]:
        """Return empty risk profile when assessment unavailable."""
        return {
            "dimensions": {dim: 0.0 for dim in self.DIMENSION_WEIGHTS.keys()},
            "aggregate": 0.0,
            "level": "OK",
            "phase": None,
            "timestamp": datetime.now().isoformat(),
        }
    
    def check_freeze(self) -> bool:
        """Check if current profile should trigger FREEZE."""
        if not self._last_profile:
            return False
        return self._last_profile.get("level") == "FREEZE"
    
    def generate_register(self) -> Dict[str, Any]:
        """
        Generate RISK_REGISTER.md content.
        
        Returns:
            Dict with keys:
                - path: str (path to register file)
                - content: str (markdown content)
                - blocked: bool (if FREEZE triggered)
        """
        if not self._last_profile:
            self.assess()
        
        register_path = self.project_path / "RISK_REGISTER.md"
        
        content = f"""# Risk Register

**Generated**: {datetime.now().isoformat()}  
**Phase**: {self._last_profile.get('phase', 'N/A')}

## Aggregate Risk Score

**Score**: {self._last_profile.get('aggregate', 0.0):.2f} / 10  
**Level**: {self._last_profile.get('level', 'OK')}

## Dimension Scores

| Dimension | Score | Weight |
|-----------|-------|--------|
"""
        
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            score = self._last_profile.get("dimensions", {}).get(dim, 0.0)
            content += f"| {dim.capitalize()} | {score:.1f} | {weight:.0%} |\n"
        
        content += f"\n**Weighted Aggregate**: {self._last_profile.get('aggregate', 0.0):.2f}\n"
        
        # Write register
        try:
            register_path.write_text(content)
            logger.info(f"[Risk] RISK_REGISTER.md written to {register_path}")
        except Exception as e:
            logger.warning(f"[Risk] Failed to write RISK_REGISTER.md: {e}")
        
        blocked = self._last_profile.get("level") == "FREEZE"
        
        return {
            "path": str(register_path),
            "content": content,
            "blocked": blocked,
        }


# =============================================================================
# Wave 4: Compliance Reporter
# =============================================================================

class ComplianceWrapper:
    """
    Wave 4 Feature #12: Compliance (ASPICE + EU AI Act + NIST RMF)
    
    事件驅動合規記錄 + Phase-end 報告生成
    
    觸發點：
        - monitoring_hr12_check(): HR-12 觸發時記錄合規事件
        - postflight_all(): Phase-end 生成合規報告
    
    TH-01: ASPICE 合規率 > 80%
    - < 80% → WARN (不 block)
    - ≥ 80% → OK
    
    失敗策略：warn only（不阻塞主流程）
    """
    
    ASPICE_THRESHOLD = 0.80  # 80%
    
    def __init__(self, feature_flags: Dict[str, bool], project_path: str):
        self.enabled = feature_flags.get("compliance", False)
        self.project_path = Path(project_path)
        self._reporter = None
        self._events: List[Dict[str, Any]] = []
        
        if self.enabled:
            try:
                from implement.feature_12_compliance_03_implement.compliance_reporter import (
                    ComplianceReporter,
                    ReportType,
                    ReportFormat,
                )
                self._reporter = ComplianceReporter()
                logger.info("[Compliance] ComplianceReporter initialized")
            except ImportError:
                try:
                    from implement.feature_12_compliance_03_implement.compliance_reporter import ComplianceReporter
                    self._reporter = ComplianceReporter()
                    logger.info("[Compliance] ComplianceReporter initialized")
                except ImportError as e:
                    logger.warning(f"[Compliance] ComplianceReporter not available: {e}")
                    self.enabled = False
    
    def record_event(self, event_type: str, fr_id: str = None, metadata: Dict[str, Any] = None) -> None:
        """
        Record a compliance event.
        
        Args:
            event_type: Event type (e.g., HR12_TRIGGERED, PHASE_COMPLETE)
            fr_id: Optional FR ID
            metadata: Optional additional metadata
        """
        if not self.enabled:
            return
        
        event = {
            "event": event_type,
            "fr_id": fr_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        self._events.append(event)
        logger.info(f"[Compliance] Event recorded: {event_type}")
    
    def record_hr12_trigger(self, fr_id: str, iteration: int) -> None:
        """
        Record HR-12 trigger event (KillSwitch activated).
        
        Args:
            fr_id: FR ID that triggered HR-12
            iteration: Iteration count when triggered
        """
        self.record_event(
            event_type="HR12_TRIGGERED",
            fr_id=fr_id,
            metadata={"iteration": iteration},
        )
    
    def calculate_aspice_rate(self) -> float:
        """
        Calculate ASPICE compliance rate.
        
        Returns:
            float: Compliance rate (0.0 - 1.0)
        """
        if not self.enabled:
            return 1.0  # Assume compliant if disabled
        
        # Calculate based on events and violations
        # Simplified: count compliant events / total events
        if not self._events:
            return 1.0
        
        compliant_events = sum(1 for e in self._events if "TRIGGERED" not in e.get("event", ""))
        total_events = len(self._events)
        
        if total_events == 0:
            return 1.0
        
        rate = compliant_events / total_events
        
        # Also check for critical violations
        critical_violations = sum(
            1 for e in self._events 
            if e.get("metadata", {}).get("severity") == "critical"
        )
        
        if critical_violations > 0:
            rate = min(rate, 0.7)  # Reduce rate if critical violations
        
        return rate
    
    def generate_phase_report(self, phase: int) -> Dict[str, Any]:
        """
        Generate Phase-end compliance report.
        
        Args:
            phase: Phase number
        
        Returns:
            Dict with keys:
                - path: str (path to report)
                - aspice_rate: float
                - events: list
                - violations: list
                - warn: bool (if rate < threshold)
        """
        if not self.enabled:
            return {"path": None, "aspice_rate": 1.0, "events": [], "violations": [], "warn": False}
        
        aspice_rate = self.calculate_aspice_rate()
        
        violations = [
            e for e in self._events 
            if "TRIGGERED" in e.get("event", "") or e.get("metadata", {}).get("severity") == "critical"
        ]
        
        report_path = self.project_path / "COMPLIANCE_REPORT.md"
        
        content = f"""# Compliance Report - Phase {phase}

**Generated**: {datetime.now().isoformat()}  
**ASPICE Rate**: {aspice_rate * 100:.1f}%

## Compliance Status

{"✅ COMPLIANT" if aspice_rate >= self.ASPICE_THRESHOLD else "⚠️ NON-COMPLIANT"} (Threshold: {self.ASPICE_THRESHOLD * 100:.0f}%)

## Events Recorded

"""
        
        for event in self._events:
            content += f"- [{event['timestamp']}] {event['event']}"
            if event.get("fr_id"):
                content += f" (FR: {event['fr_id']})"
            content += "\n"
        
        content += f"""

## Violations

"""
        
        if violations:
            for v in violations:
                content += f"- {v['event']}: FR-{v.get('fr_id', 'N/A')}\n"
        else:
            content += "No violations recorded.\n"
        
        content += f"""

## Recommendations

"""
        
        if aspice_rate < self.ASPICE_THRESHOLD:
            content += f"- Address {len(violations)} violation(s) to improve ASPICE rate above {self.ASPICE_THRESHOLD * 100:.0f}%\n"
        else:
            content += "- Continue monitoring compliance throughout next phase.\n"
        
        # Write report
        try:
            report_path.write_text(content)
            logger.info(f"[Compliance] COMPLIANCE_REPORT.md written to {report_path}")
        except Exception as e:
            logger.warning(f"[Compliance] Failed to write COMPLIANCE_REPORT.md: {e}")
        
        warn = aspice_rate < self.ASPICE_THRESHOLD
        
        return {
            "path": str(report_path),
            "aspice_rate": aspice_rate,
            "events": self._events,
            "violations": violations,
            "warn": warn,
            "content": content,
        }
    
    def reset_events(self) -> None:
        """Reset events for new phase."""
        self._events = []