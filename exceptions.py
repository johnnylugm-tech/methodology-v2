"""
Enhanced Exceptions for Methodology v2

Provides structured exception hierarchy with context tracking and fix suggestions.
"""

from __future__ import annotations


class MethodologyError(Exception):
    """基礎異常 — 所有 Methodology 相關異常的頂層類別。"""

    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context: dict = context or {}

    def suggest_fix(self) -> str:
        """預設修復建議（子類應覆寫）。"""
        return f"請檢查 context: {self.context}"

    def __repr__(self) -> str:
        ctx = f", context={self.context!r}" if self.context else ""
        return f"{self.__class__.__name__}({self.message!r}{ctx})"

    @property
    def message(self) -> str:
        """相容性存取：self.args[0] 視為 message。"""
        return self.args[0] if self.args else ""


# ─── Phase ───────────────────────────────────────────────────────────────────


class PhaseTransitionError(MethodologyError):
    """Phase 轉換失敗。"""

    def suggest_fix(self) -> str:
        current = self.context.get("current_phase", "?")
        target = self.context.get("target_phase", "?")
        return (
            f"Phase {current} → {target} 轉換失敗。"
            " 請檢查是否滿足進入條件。"
        )


# ─── Tool ─────────────────────────────────────────────────────────────────────


class ToolExecutionError(MethodologyError):
    """工具執行失敗。"""

    def suggest_fix(self) -> str:
        tool = self.context.get("tool", "?")
        return f"工具 {tool} 執行失敗。請檢查參數或嘗試使用替代工具。"


# ─── Constitution ──────────────────────────────────────────────────────────────


class ConstitutionViolationError(MethodologyError):
    """Constitution 品質標準違規。"""

    def suggest_fix(self) -> str:
        violations = self.context.get("violations", [])
        top = violations[:3]
        suffix = " ..." if len(violations) > 3 else ""
        return f"Constitution 違規 {len(violations)} 項：{top}{suffix}"


# ─── Integrity ────────────────────────────────────────────────────────────────


class IntegrityError(MethodologyError):
    """Integrity 分數過低。"""

    def suggest_fix(self) -> str:
        score = self.context.get("integrity_score", 0)
        if score < 40:
            return (
                f"Integrity {score}% < 40%，已觸發 HR-14，"
                " 請執行全面審計"
            )
        return f"Integrity {score}% 低於標準，請檢查產出品質"


# ─── Validation ───────────────────────────────────────────────────────────────


class ValidationError(MethodologyError):
    """驗證失敗。"""

    pass


# ─── Agent ────────────────────────────────────────────────────────────────────


class AgentSpawnError(MethodologyError):
    """Subagent 派遣失敗。"""

    def suggest_fix(self) -> str:
        role = self.context.get("role", "?")
        return f"派遣 {role} 失敗。請檢查 session 狀態或嘗試重試。"


# ─── Artifact ─────────────────────────────────────────────────────────────────


class ArtifactMissingError(MethodologyError):
    """Artifact 缺失錯誤。"""

    def suggest_fix(self) -> str:
        artifacts = [a['artifact'] for a in self.context.get('artifacts', [])]
        return f"請確認以下 artifact 存在：{artifacts}"
