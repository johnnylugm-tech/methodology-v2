"""
risk.py - Risk Data Model
[FR-01, FR-02, FR-03, FR-04] Core risk data structure

Provides the core data models for risk assessment:
- MitigationPlan: Structured mitigation action plan
- Risk: Individual risk record with scoring
- RiskAssessmentResult: Aggregation of assessment results

Usage:
    >>> from models import Risk, RiskAssessmentResult
    >>> risk = Risk(title="Test", description="Test risk", dimension=RiskDimension.TECHNICAL)
    >>> print(f"Risk score: {risk.score}")
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any

from .enums import RiskDimension, RiskLevel, RiskStatus, StrategyType


@dataclass
class MitigationPlan:
    """緩解措施計劃"""
    immediate: List[str] = field(default_factory=list)
    short_term: List[str] = field(default_factory=list)
    long_term: List[str] = field(default_factory=list)
    fallback: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert mitigation plan to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MitigationPlan":
        """Create MitigationPlan from dictionary."""
        return cls(
            immediate=data.get("immediate", []),
            short_term=data.get("short_term", []),
            long_term=data.get("long_term", []),
            fallback=data.get("fallback", [])
        )


@dataclass
class Risk:
    """
    風險記錄 dataclass

    [FR-01] Risk identification - id, title, description, dimension
    [FR-02] Risk evaluation - probability, impact, score
    [FR-03] Risk response strategy - strategy, mitigation
    [FR-04] Risk tracking - status, timestamps, history
    """
    title: str
    description: str
    dimension: RiskDimension

    # Evaluation
    probability: float = 0.5
    impact: int = 3
    detectability_factor: float = 1.0

    # Metadata
    id: str = field(default_factory=lambda: f"R-{uuid.uuid4().hex[:8].upper()}")
    level: RiskLevel = field(default=RiskLevel.MEDIUM)
    status: RiskStatus = field(default=RiskStatus.OPEN)
    owner: str = ""
    strategy: StrategyType = field(default=StrategyType.ACCEPT)
    mitigation: str = ""
    mitigation_plan: MitigationPlan = field(default_factory=MitigationPlan)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

    # Evidence
    evidence: List[str] = field(default_factory=list)

    # Computed
    def __post_init__(self):
        self._score = self.calculate_score()
        if self.level == RiskLevel.MEDIUM and self._score > 0:
            self.level = RiskLevel.from_score(self._score)

    def calculate_score(self) -> float:
        """[FR-02] Calculate risk score: P × I × Detectability_Factor"""
        try:
            prob = max(0.0, min(1.0, self.probability))
            imp = max(1, min(5, self.impact))
            det = max(0.5, min(1.0, self.detectability_factor))
            return round(prob * imp * det / 5, 3)  # Normalized to 0-1
        except (TypeError, ValueError):
            return 0.3  # Default to MEDIUM

    @property
    def score(self) -> float:
        """Risk score (read-only, computed from probability, impact, detectability)."""
        return self._score

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dimension": self.dimension.value if isinstance(self.dimension, RiskDimension) else self.dimension,
            "level": self.level.value if isinstance(self.level, RiskLevel) else self.level,
            "status": self.status.value if isinstance(self.status, RiskStatus) else self.status,
            "probability": self.probability,
            "impact": self.impact,
            "detectability_factor": self.detectability_factor,
            "score": self.score,
            "owner": self.owner,
            "strategy": self.strategy.value if isinstance(self.strategy, StrategyType) else self.strategy,
            "mitigation": self.mitigation,
            "mitigation_plan": self.mitigation_plan.to_dict() if isinstance(self.mitigation_plan, MitigationPlan) else self.mitigation_plan,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "closed_at": self.closed_at.isoformat() if isinstance(self.closed_at, datetime) else self.closed_at,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Risk":
        """從字典還原"""
        # Parse enums
        dimension = RiskDimension(data.get("dimension", "technical"))
        level = RiskLevel(data.get("level", "medium"))
        status = RiskStatus(data.get("status", "open"))
        strategy = StrategyType(data.get("strategy", "accept"))

        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()

        closed_at = data.get("closed_at")
        if isinstance(closed_at, str):
            closed_at = datetime.fromisoformat(closed_at)

        # Parse mitigation plan
        mitigation_plan_data = data.get("mitigation_plan", {})
        if isinstance(mitigation_plan_data, dict):
            mitigation_plan = MitigationPlan.from_dict(mitigation_plan_data)
        else:
            mitigation_plan = MitigationPlan()

        return cls(
            id=data.get("id", f"R-{uuid.uuid4().hex[:8].upper()}"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            dimension=dimension,
            level=level,
            status=status,
            probability=data.get("probability", 0.5),
            impact=data.get("impact", 3),
            detectability_factor=data.get("detectability_factor", 1.0),
            owner=data.get("owner", ""),
            strategy=strategy,
            mitigation=data.get("mitigation", ""),
            mitigation_plan=mitigation_plan,
            created_at=created_at,
            updated_at=updated_at,
            closed_at=closed_at,
            evidence=data.get("evidence", []),
        )

    def update_status(self, new_status: RiskStatus) -> bool:
        """[FR-04] 更新風險狀態"""
        if not self.status.can_transition_to(new_status):
            return False

        self.status = new_status
        self.updated_at = datetime.now()

        if new_status == RiskStatus.CLOSED:
            self.closed_at = datetime.now()

        return True


@dataclass
class RiskAssessmentResult:
    """風險評估結果"""
    project_name: str
    phase: int
    total_risks: int
    risks: List[Risk]
    average_score: float
    constitution_compliant: bool = False
    generated_at: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "project_name": self.project_name,
            "phase": self.phase,
            "total_risks": self.total_risks,
            "risks": [r.to_dict() for r in self.risks],
            "average_score": self.average_score,
            "constitution_compliant": self.constitution_compliant,
            "generated_at": self.generated_at.isoformat() if isinstance(self.generated_at, datetime) else self.generated_at,
            "recommendations": self.recommendations,
        }

    @property
    def critical_count(self) -> int:
        """Number of critical-level risks."""
        return len([r for r in self.risks if r.level == RiskLevel.CRITICAL])

    @property
    def high_count(self) -> int:
        """Number of high-level risks."""
        return len([r for r in self.risks if r.level == RiskLevel.HIGH])

    @property
    def medium_count(self) -> int:
        """Number of medium-level risks."""
        return len([r for r in self.risks if r.level == RiskLevel.MEDIUM])

    @property
    def low_count(self) -> int:
        """Number of low-level risks."""
        return len([r for r in self.risks if r.level == RiskLevel.LOW])

    @property
    def open_count(self) -> int:
        """Number of open (unresolved) risks."""
        return len([r for r in self.risks if r.status == RiskStatus.OPEN])

    @property
    def closed_count(self) -> int:
        """Number of closed risks."""
        return len([r for r in self.risks if r.status == RiskStatus.CLOSED])
