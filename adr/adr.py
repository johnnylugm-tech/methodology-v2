#!/usr/bin/env python3
"""
ADR - Architecture Decision Record
=================================
單一 ADR 的資料結構
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class ADR:
    """
    Architecture Decision Record
    
    Attributes:
        title: 決策標題
        status: accepted/rejected/proposed/superseded
        context: 決策的背景和問題
        decision: 決定的內容
        consequences: 決定的後果（正面和負面）
        alternatives: 被拒絕的替代方案
        related_decisions: 相關的 ADR ID
        created_by: 決策者
        created_at: 創建時間
    """
    title: str
    status: str = "proposed"
    context: str = ""
    decision: str = ""
    consequences: str = ""
    alternatives: List[str] = field(default_factory=list)
    related_decisions: List[str] = field(default_factory=list)
    created_by: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    adr_id: Optional[str] = None

@dataclass 
class ADRRecord:
    """ADR 記錄（包含 ID）"""
    id: str
    title: str
    status: str
    context: str
    decision: str
    consequences: str
    alternatives: List[str]
    related_decisions: List[str]
    created_by: str
    created_at: str
    
    def to_markdown(self) -> str:
        """轉換為 Markdown 格式"""
        md = f"# ADR-{self.id}: {self.title}\n\n"
        md += f"**Status**: {self.status}\n\n"
        md += f"**Date**: {self.created_at}\n\n"
        md += f"**Author**: {self.created_by}\n\n"
        
        md += "## Context\n\n"
        md += f"{self.context}\n\n"
        
        md += "## Decision\n\n"
        md += f"{self.decision}\n\n"
        
        md += "## Consequences\n\n"
        md += f"{self.consequences}\n\n"
        
        if self.alternatives:
            md += "## Alternatives Considered\n\n"
            for alt in self.alternatives:
                md += f"- {alt}\n"
            md += "\n"
        
        if self.related_decisions:
            md += "## Related Decisions\n\n"
            for rel in self.related_decisions:
                md += f"- ADR-{rel}\n"
            md += "\n"
        
        return md