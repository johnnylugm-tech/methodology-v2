"""
Base class for Dimension Assessors.

All 8 dimension assessors inherit from AbstractDimensionAssessor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class DimensionResult:
    """
    Result of a single dimension assessment.

    Attributes:
        dimension_id: The dimension identifier (e.g., "D1")
        score: Risk score in range [0.0, 1.0]
        evidence: List of evidence items that contributed to the score
        metadata: Additional metadata about the assessment
        warnings: List of warnings encountered during assessment
    """

    dimension_id: str
    score: float
    evidence: list[str] = None
    metadata: dict = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []

    @property
    def risk_level(self) -> str:
        """Return risk level based on score."""
        if self.score >= 0.8:
            return "CRITICAL"
        elif self.score >= 0.6:
            return "HIGH"
        elif self.score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"


class AbstractDimensionAssessor(ABC):
    """
    Abstract base class for all dimension assessors.

    Each assessor evaluates a specific risk dimension and returns a score
    in the range [0.0, 1.0] where:
        - 0.0 = no risk
        - 1.0 = maximum risk
    """

    @abstractmethod
    def assess(self, context: dict) -> float:
        """
        Assess the risk for this dimension.

        Args:
            context: Assessment context containing relevant data for this dimension

        Returns:
            Risk score in range [0.0, 1.0]
        """
        pass

    @abstractmethod
    def get_dimension_id(self) -> str:
        """
        Get the dimension identifier.

        Returns:
            Dimension ID (e.g., "D1", "D2", etc.)
        """
        pass

    def get_dimension_name(self) -> str:
        """Get the human-readable dimension name."""
        return self.__class__.__name__.replace("Assessor", "").replace("_", " ").title()

    def assess_with_details(self, context: dict) -> DimensionResult:
        """
        Perform assessment with full details.

        Default implementation calls assess() and wraps in DimensionResult.
        Subclasses can override for more detailed analysis.

        Args:
            context: Assessment context

        Returns:
            DimensionResult with score and evidence
        """
        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=[],
            metadata={},
            warnings=[],
        )

    def validate_context(self, context: dict, required_keys: list[str]) -> list[str]:
        """
        Validate that required keys are present in context.

        Args:
            context: Context to validate
            required_keys: List of required key names

        Returns:
            List of missing keys (empty if all present)
        """
        return [key for key in required_keys if key not in context]


# Import and re-export all dimension assessors
from .privacy import PrivacyAssessor
from .injection import InjectionAssessor
from .cost import CostAssessor
from .uaf_clap import UAFClapAssessor
from .memory_poisoning import MemoryPoisoningAssessor
from .cross_agent_leak import CrossAgentLeakAssessor
from .latency import LatencyAssessor
from .compliance import ComplianceAssessor

__all__ = [
    "AbstractDimensionAssessor",
    "DimensionResult",
    "PrivacyAssessor",
    "InjectionAssessor",
    "CostAssessor",
    "UAFClapAssessor",
    "MemoryPoisoningAssessor",
    "CrossAgentLeakAssessor",
    "LatencyAssessor",
    "ComplianceAssessor",
]