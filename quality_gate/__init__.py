"""
Quality Gate Module
==================

提供統一的品質閘道功能。

Modules:
    - doc_checker: 文檔存在性檢查
    - phase_artifact_enforcer: Phase 產物引用檢查
    - constitution: Constitution 原則檢查
    - unified_gate: 統一品質閘道（整合以上三者）

Usage:
    from quality_gate import UnifiedGate

    gate = UnifiedGate("/path/to/project")
    result = gate.check_all()
"""

from .unified_gate import UnifiedGate, UnifiedGateResult, CheckResult
from .doc_checker import DocumentChecker
from .phase_artifact_enforcer import PhaseArtifactEnforcer
from .constitution import run_constitution_check, ConstitutionCheckResult

__all__ = [
    'UnifiedGate',
    'UnifiedGateResult',
    'CheckResult',
    'DocumentChecker',
    'PhaseArtifactEnforcer',
    'run_constitution_check',
    'ConstitutionCheckResult',
]
