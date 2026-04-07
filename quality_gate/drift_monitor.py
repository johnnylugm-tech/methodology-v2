"""
DriftMonitor — Architecture Drift 持續監控

提供統一的 DriftAlert 格式 + cron-friendly 的 DriftMonitor。
所有 Alert 都自動轉換為 StandardFeedback 格式，送進 Feedback Loop。
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from quality_gate.baseline_manager import BaselineManager


class DriftAlert:
    """
    統一 Alert 格式。
    所有 Alert 都用這個格式，不論來源。
    """
    def __init__(
        self,
        alert_id: str | None = None,
        severity: str = "medium",
        source: str = "drift_detector",
        message: str = "",
        drift_score: float = 0.0,
        timestamp: str | None = None,
        artifacts: list[str] | None = None,
        recommended_action: str = "",
        details: dict | None = None,
    ):
        self.id = alert_id or f"drift-{uuid.uuid4().hex[:8]}"
        self.severity = severity
        self.source = source
        self.message = message
        self.drift_score = drift_score
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.artifacts = artifacts or []
        self.recommended_action = recommended_action
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
            "drift_score": self.drift_score,
            "timestamp": self.timestamp,
            "artifacts": self.artifacts,
            "recommended_action": self.recommended_action,
            "details": self.details,
        }

    def to_feedback(self) -> dict:
        """轉換為 StandardFeedback 格式，進入 Feedback Loop。"""
        return {
            "id": self.id,
            "source": self.source,
            "source_detail": "architecture_drift",
            "type": "alert",
            "category": "architecture",
            "severity": self.severity,
            "title": f"Architecture Drift: {self.severity}",
            "description": self.message,
            "context": {
                "drift_score": self.drift_score,
                "artifacts": self.artifacts,
                "details": self.details,
                "recommended_action": self.recommended_action,
            },
            "timestamp": self.timestamp,
            "sla_deadline": None,
            "status": "pending",
            "assignee": None,
            "resolution": None,
            "verified_at": None,
            "related_feedbacks": [],
            "recurrence_count": 0,
            "confidence": 0.95,
            "tags": ["drift", "architecture", self.severity],
        }


class DriftMonitor:
    """
    持續監控架構 drift。
    支援 cron 排程，自動 Alert。
    """
    def __init__(
        self,
        project_path: str,
        feedback_store=None,
        baseline_manager: "BaselineManager | None" = None,
    ):
        self.project_path = project_path
        self.feedback_store = feedback_store
        self.baseline_manager = baseline_manager

    def run_and_alert(self) -> DriftAlert | None:
        """
        執行 drift 檢查，若有 drift 自動送 Alert。
        設計給 cron job 呼叫。
        """
        report = self._check_drift()

        if not report.get("has_drift", False):
            return None

        alert = DriftAlert(
            alert_id=f"drift-{uuid.uuid4().hex[:8]}",
            severity=self._score_to_severity(report.get("drift_score", 0.0)),
            source="drift_detector",
            message=report.get("message", "Architecture drift detected"),
            drift_score=report.get("drift_score", 0.0),
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifacts=report.get("drifted_artifacts", []),
            recommended_action=report.get("recommendation", "Review and update baseline"),
            details=report,
        )

        # 送進 Feedback Loop（如果有的話）
        if self.feedback_store is not None:
            fb = alert.to_feedback()
            self.feedback_store.add(fb)

        return alert

    def _check_drift(self) -> dict:
        """
        執行 drift 檢查。
        目前調用現有的 BaselineManager。
        返回 dict 格式供 run_and_alert 使用。
        """
        if self.baseline_manager is None:
            return {"has_drift": False}

        # BaselineManager.check_drift 需要 current_metrics
        # 我們從 baseline_manager 取得 metrics（如果有）
        # 預設用空的 metrics 觸發 structure drift 檢查
        current_metrics = getattr(self.baseline_manager, "_last_metrics", {})

        try:
            result = self.baseline_manager.check_drift(current_metrics)
        except Exception:
            return {"has_drift": False}

        # DriftResult dataclass → dict (handles both real dataclass and plain dict)
        drift_dict = self._result_to_dict(result)
        drift_data = drift_dict.get("drift", {})
        summary = drift_dict.get("summary", "")

        has_drift = len(drift_data) > 0

        # 計算 drift_score：取所有 drift 中最高的 severity 分數
        severity_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.3}
        max_score = 0.0
        for metric_info in drift_data.values():
            if isinstance(metric_info, dict):
                severity = metric_info.get("severity", "low")
                score = severity_weights.get(severity, 0.0)
                if score > max_score:
                    max_score = score
        if has_drift and max_score == 0.0:
            max_score = 0.3  # 預設 drift 存在但未量化

        # 蒐集 drifted artifacts（目錄結構變動）
        drifted_artifacts = []
        if "structure" in drift_data:
            drifted_artifacts.append("structure")
        for key in drift_data:
            if key not in ("structure",):
                drifted_artifacts.append(key)

        return {
            "has_drift": has_drift,
            "drift_score": max_score,
            "message": summary or "Architecture drift detected",
            "drifted_artifacts": drifted_artifacts,
            "recommendation": "Review drift and update baseline if intentional",
            "drift_details": drift_data,
        }

    def _result_to_dict(self, result) -> dict:
        """
        Convert BaselineManager.check_drift() result to a plain dict.
        Handles:
        - DriftResult dataclass (real instance from BaselineManager)
        - plain dict (if caller passes dict directly)
        - Mock objects in tests
        """
        # Already a dict
        if isinstance(result, dict):
            return result
        # Has dataclass fields → extract them
        if hasattr(result, "__dataclass_fields__"):
            return {
                "tag": getattr(result, "tag", ""),
                "baseline_timestamp": getattr(result, "baseline_timestamp", ""),
                "current_timestamp": getattr(result, "current_timestamp", ""),
                "drift": getattr(result, "drift", {}),
                "summary": getattr(result, "summary", ""),
            }
        # Fallback: try attribute access
        return {
            "tag": getattr(result, "tag", ""),
            "baseline_timestamp": getattr(result, "baseline_timestamp", ""),
            "current_timestamp": getattr(result, "current_timestamp", ""),
            "drift": getattr(result, "drift", {}),
            "summary": getattr(result, "summary", ""),
        }

    @staticmethod
    def _score_to_severity(score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.3:
            return "medium"
        return "low"

    def run_cron(self) -> list[DriftAlert]:
        """
        Cron-style 執行：每天都檢查，返回所有 alerts。
        """
        alert = self.run_and_alert()
        if alert is None:
            return []
        return [alert]
