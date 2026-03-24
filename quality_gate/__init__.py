"""
Quality Gate - 品質閘道模組

包含：
- DocumentChecker: 文檔完整性檢查
- PhaseArtifactEnforcer: Phase 產物強制執行
"""

from .doc_checker import DocumentChecker, DocumentRequirement
from .phase_artifact_enforcer import PhaseArtifactEnforcer, PhaseDependency

__all__ = ["DocumentChecker", "DocumentRequirement", "PhaseArtifactEnforcer", "PhaseDependency"]
