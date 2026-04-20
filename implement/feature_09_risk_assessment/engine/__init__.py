"""engine/__init__.py
[FR-01, FR-02, FR-03, FR-04] Risk Assessment Engine

Provides the core risk assessment components:
- RiskAssessor: Identifies and evaluates project risks
- RiskScorer: Calculates risk scores based on probability and impact
- RiskStrategist: Generates mitigation strategies and plans
- RiskTracker: Manages risk lifecycle with SQLite persistence
- RiskAssessmentEngine: Unified facade combining all components

Usage:
    >>> from engine import RiskAssessmentEngine
    >>> engine = RiskAssessmentEngine("/path/to/project")
    >>> result = engine.assess()

    >>> # Or use components individually
    >>> from engine import RiskAssessor, RiskStrategist
    >>> assessor = RiskAssessor("/path/to/project")
    >>> result = assessor.assess()
    >>> risks = RiskStrategist().generate_all_plans(result.risks)
"""

from .assessor import RiskAssessor, RiskScorer
from .strategist import RiskStrategist
from .tracker import RiskTracker
from .engine import RiskAssessmentEngine

__all__ = [
    "RiskAssessor",
    "RiskScorer",
    "RiskStrategist",
    "RiskTracker",
    "RiskAssessmentEngine",
]
