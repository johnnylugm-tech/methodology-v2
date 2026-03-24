"""
Quality Gate - 品質閘道模組

包含：
- DocumentChecker: 文檔完整性檢查
- PhaseArtifactEnforcer: Phase 產物強制執行
"""

from quality_gate.doc_checker import DocumentChecker
from quality_gate.phase_artifact_enforcer import PhaseArtifactEnforcer

__all__ = ["DocumentChecker", "PhaseArtifactEnforcer"]
