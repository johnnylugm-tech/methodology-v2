"""
UnifiedAlert — 統一的 Quality Signal Alert 格式。

所有 quality signal（Constitution Violation, Drift, BVS, Linter, Test Failure）
都使用這個格式進入 Feedback Loop。
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid


@dataclass
class UnifiedAlert:
    """
    所有 quality signal 的統一 Alert 格式。

    使用方式：
        alert = UnifiedAlert(
            source="constitution",
            source_detail="HR-01",
            severity="critical",
            title="Phase gate violated",
            message="Phase 2 executed before Phase 1",
        )

        # 送進 Feedback Loop
        fb = alert.to_feedback()
        store.add(fb)

        # 或直接送進 Self-Correction
        alert.trigger_self_correction()
    """

    # ----------------------------------------------------------------------
    # 分類（required; must precede fields with defaults in Python dataclass）
    # ----------------------------------------------------------------------
    source: str  # constitution / quality_gate / bvs / drift / linter / test_failure
    source_detail: str  # HR-01 / linter/error / complexity/cc_high / ...

    # ----------------------------------------------------------------------
    # 內容（all have defaults — placed here to satisfy dataclass ordering rules）
    # ----------------------------------------------------------------------
    category: str = "quality"  # quality / security / performance / usability
    severity: str = "medium"  # critical / high / medium / low
    title: str = ""
    message: str = ""
    context: dict = field(default_factory=dict)  # 詳細上下文

    # ----------------------------------------------------------------------
    # 處置
    # ----------------------------------------------------------------------
    recommended_action: str = ""
    auto_fixable: bool = False
    sla_hours: int = 24  # 預設 24 小時

    # ----------------------------------------------------------------------
    # 身份（auto-generated; factory must be callable with parens in field def）
    # ----------------------------------------------------------------------
    alert_id: str = field(default_factory=lambda: f"alert-{uuid.uuid4().hex[:8]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sla_deadline: str = ""  # auto-computed in __post_init__

    def __post_init__(self) -> None:
        if not self.sla_deadline:
            ts = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
            self.sla_deadline = (ts + timedelta(hours=self.sla_hours)).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_feedback(self) -> dict:
        """
        轉換為 StandardFeedback 格式，進入 Feedback Loop。
        """
        # 從 severity str 反推 impact/urgency 用於 routing
        severity_map = {
            "critical": (1.0, 1.0),
            "high": (0.8, 0.6),
            "medium": (0.5, 0.5),
            "low": (0.3, 0.2),
        }
        impact, urgency = severity_map.get(self.severity, (0.5, 0.5))

        # SLA deadline 從 sla_hours 計算
        ts = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        sla_deadline = (ts + timedelta(hours=self.sla_hours)).isoformat()

        return {
            "id": self.alert_id,
            "source": self.source,
            "source_detail": self.source_detail,
            "type": "alert",
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.message,
            "context": {
                "recommended_action": self.recommended_action,
                "auto_fixable": self.auto_fixable,
                **self.context,
            },
            "timestamp": self.timestamp,
            "sla_deadline": sla_deadline,
            "status": "pending",
            "assignee": None,
            "resolution": None,
            "verified_at": None,
            "related_feedbacks": [],
            "recurrence_count": 0,
            "confidence": 0.95 if self.auto_fixable else 0.8,
            "tags": [self.source, self.category, self.severity, "unified_alert"],
        }

    @classmethod
    def from_drift_alert(cls, drift_alert: "DriftAlert") -> "UnifiedAlert":
        """工廠方法：從 DriftAlert 轉換為 UnifiedAlert。"""
        return cls(
            source=drift_alert.source,
            source_detail="architecture_drift",
            category="architecture",
            severity=drift_alert.severity,
            title=f"Drift Alert: {drift_alert.severity}",
            message=drift_alert.message,
            context={"drift_score": drift_alert.drift_score},
            recommended_action=drift_alert.recommended_action,
            auto_fixable=False,
            sla_hours={"critical": 4, "high": 24, "medium": 72, "low": 168}[
                drift_alert.severity
            ],
        )


# ----------------------------------------------------------------------
# 支援型別（尚未存在的 DriftAlert, 僅作為工廠方法的介面），
# 正式引入時由實際模組提供。
# ----------------------------------------------------------------------
class DriftAlert:
    """
    Stub for type-checking `from_drift_alert()` factory.
    生產環境中替換為真實的架構 drift 模組。
    """

    source: str
    severity: str
    message: str
    drift_score: float
    recommended_action: str

    def __init__(
        self,
        source: str,
        severity: str,
        message: str,
        drift_score: float,
        recommended_action: str,
    ) -> None:
        self.source = source
        self.severity = severity
        self.message = message
        self.drift_score = drift_score
        self.recommended_action = recommended_action
