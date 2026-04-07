#!/usr/bin/env python3
"""
Risk Registry - 系統化風險追蹤登記表

提供風險的 CRUD 操作、狀態管理與報告生成
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_string(cls, value: str) -> "RiskLevel":
        """從字串解析風險等級"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MEDIUM

    @property
    def priority(self) -> int:
        """優先級數值（越高越嚴重）"""
        return {
            RiskLevel.LOW: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }[self]


class RiskStatus(Enum):
    """風險狀態"""
    OPEN = "open"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"

    @classmethod
    def from_string(cls, value: str) -> "RiskStatus":
        """從字串解析風險狀態"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.OPEN


@dataclass
class Risk:
    """風險記錄"""
    id: str
    title: str
    description: str
    level: RiskLevel
    status: RiskStatus
    owner: str
    created_at: datetime
    mitigated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    tags: List[str] = None
    impact: str = ""  # 影響描述
    probability: float = 0.5  # 發生機率 0-1
    mitigation: str = ""  # 緩解措施

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        d = asdict(self)
        d['level'] = self.level.value
        d['status'] = self.status.value
        d['created_at'] = self.created_at.isoformat()
        if self.mitigated_at:
            d['mitigated_at'] = self.mitigated_at.isoformat()
        if self.closed_at:
            d['closed_at'] = self.closed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Risk":
        """從字典建立風險"""
        d = d.copy()
        d['level'] = RiskLevel.from_string(d['level'])
        d['status'] = RiskStatus.from_string(d['status'])
        if isinstance(d['created_at'], str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
        if d.get('mitigated_at') and isinstance(d['mitigated_at'], str):
            d['mitigated_at'] = datetime.fromisoformat(d['mitigated_at'])
        if d.get('closed_at') and isinstance(d['closed_at'], str):
            d['closed_at'] = datetime.fromisoformat(d['closed_at'])
        return cls(**d)


class RiskRegistry:
    """風險登記表管理器"""

    def __init__(self, storage_path: str = ".methodology/risks.json"):
        self.storage_path = storage_path
        self.risks: List[Risk] = []
        self._load()

    def _load(self):
        """從檔案載入風險記錄"""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.risks = [Risk.from_dict(r) for r in data]
        except (FileNotFoundError, json.JSONDecodeError):
            self.risks = []

    def _save(self):
        """儲存風險記錄到檔案"""
        import os
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in self.risks], f, ensure_ascii=False, indent=2)

    def add_risk(
        self,
        title: str,
        description: str,
        level: RiskLevel,
        owner: str,
        impact: str = "",
        probability: float = 0.5,
        mitigation: str = "",
        tags: List[str] = None
    ) -> Risk:
        """新增風險"""
        risk = Risk(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            level=level,
            status=RiskStatus.OPEN,
            owner=owner,
            created_at=datetime.now(),
            impact=impact,
            probability=probability,
            mitigation=mitigation,
            tags=tags or []
        )
        self.risks.append(risk)
        self._save()
        return risk

    def get_risk(self, risk_id: str) -> Optional[Risk]:
        """取得單一風險"""
        for r in self.risks:
            if r.id == risk_id:
                return r
        return None

    def get_risks_by_level(self, level: RiskLevel) -> List[Risk]:
        """依等級篩選風險"""
        return [r for r in self.risks if r.level == level]

    def get_risks_by_status(self, status: RiskStatus) -> List[Risk]:
        """依狀態篩選風險"""
        return [r for r in self.risks if r.status == status]

    def get_risks_by_owner(self, owner: str) -> List[Risk]:
        """依負責人篩選風險"""
        return [r for r in self.risks if r.owner == owner]

    def get_all_risks(self) -> List[Risk]:
        """取得所有風險"""
        return self.risks

    def update_risk_status(self, risk_id: str, status: RiskStatus) -> bool:
        """更新風險狀態"""
        risk = self.get_risk(risk_id)
        if not risk:
            return False
        risk.status = status
        if status == RiskStatus.MITIGATED:
            risk.mitigated_at = datetime.now()
        elif status == RiskStatus.CLOSED:
            risk.closed_at = datetime.now()
        self._save()
        return True

    def close_risk(self, risk_id: str) -> bool:
        """關閉風險"""
        return self.update_risk_status(risk_id, RiskStatus.CLOSED)

    def delete_risk(self, risk_id: str) -> bool:
        """刪除風險"""
        for i, r in enumerate(self.risks):
            if r.id == risk_id:
                self.risks.pop(i)
                self._save()
                return True
        return False

    def generate_report(self) -> str:
        """生成風險報告"""
        total = len(self.risks)
        open_risks = [r for r in self.risks if r.status == RiskStatus.OPEN]
        mitigated = [r for r in self.risks if r.status == RiskStatus.MITIGATED]
        accepted = [r for r in self.risks if r.status == RiskStatus.ACCEPTED]
        closed = [r for r in self.risks if r.status == RiskStatus.CLOSED]

        by_level = {
            'critical': len([r for r in self.risks if r.level == RiskLevel.CRITICAL]),
            'high': len([r for r in self.risks if r.level == RiskLevel.HIGH]),
            'medium': len([r for r in self.risks if r.level == RiskLevel.MEDIUM]),
            'low': len([r for r in self.risks if r.level == RiskLevel.LOW]),
        }

        lines = [
            "=" * 60,
            "🔴 風險報告",
            "=" * 60,
            f"生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"📊 總風險數: {total}",
            f"   ▪ 開放中: {len(open_risks)}",
            f"   ▪ 已緩解: {len(mitigated)}",
            f"   ▪ 已接受: {len(accepted)}",
            f"   ▪ 已關閉: {len(closed)}",
            "",
            "📈 風險等級分佈:",
            f"   ▪ Critical: {by_level['critical']}",
            f"   ▪ High: {by_level['high']}",
            f"   ▪ Medium: {by_level['medium']}",
            f"   ▪ Low: {by_level['low']}",
            "",
        ]

        # 開放的 Critical/High 風險
        critical_high = [r for r in open_risks if r.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
        if critical_high:
            lines.append("⚠️  需要關注的高風險 (開放中):")
            for r in sorted(critical_high, key=lambda x: x.level.priority, reverse=True):
                lines.append(f"   [{r.level.value.upper()}] {r.title}")
                lines.append(f"      ID: {r.id} | 負責人: {r.owner}")
                lines.append(f"      機率: {r.probability:.0%} | 影響: {r.impact}")
                lines.append("")
        else:
            lines.append("✅ 目前無開放的高風險項目")

        lines.append("=" * 60)
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        """取得風險摘要"""
        return {
            "total": len(self.risks),
            "by_status": {
                "open": len(self.get_risks_by_status(RiskStatus.OPEN)),
                "mitigated": len(self.get_risks_by_status(RiskStatus.MITIGATED)),
                "accepted": len(self.get_risks_by_status(RiskStatus.ACCEPTED)),
                "closed": len(self.get_risks_by_status(RiskStatus.CLOSED)),
            },
            "by_level": {
                "critical": len(self.get_risks_by_level(RiskLevel.CRITICAL)),
                "high": len(self.get_risks_by_level(RiskLevel.HIGH)),
                "medium": len(self.get_risks_by_level(RiskLevel.MEDIUM)),
                "low": len(self.get_risks_by_level(RiskLevel.LOW)),
            }
        }
