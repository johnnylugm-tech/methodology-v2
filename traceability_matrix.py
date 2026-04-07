#!/usr/bin/env python3
"""
Traceability Matrix - 追溯性矩陣

AI-native 實作：
- 自動記錄所有執行鏈
- 零額外負擔
- 自動生成客觀證據

ASPICE 合規：支援 SWE.3 / SYS.4 等流程的追溯性要求
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json


class TraceStatus(Enum):
    """追溯狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"


class LinkType(Enum):
    """鏈接類型"""
    TASK_TO_AGENT = "task→agent"
    AGENT_TO_OUTPUT = "agent→output"
    OUTPUT_TO_VERIFICATION = "output→verification"
    TASK_TO_OUTPUT = "task→output"
    VERIFICATION_TO_SIGNED = "verification→signed"


@dataclass
class TraceLink:
    """追溯鏈接"""
    link_id: str
    source_type: str          # "task", "agent", "output", "verification"
    source_id: str
    target_type: str
    target_id: str
    link_type: LinkType = LinkType.TASK_TO_AGENT
    created_at: datetime = field(default_factory=datetime.now)
    verified_at: Optional[datetime] = None
    status: TraceStatus = TraceStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "link_id": self.link_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "link_type": self.link_type.value if isinstance(self.link_type, Enum) else self.link_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TraceLink":
        """從字典創建"""
        link_type = data.get("link_type")
        if link_type and isinstance(link_type, str):
            try:
                link_type = LinkType(link_type)
            except ValueError:
                link_type = LinkType.TASK_TO_AGENT
        
        status = data.get("status")
        if status and isinstance(status, str):
            try:
                status = TraceStatus(status)
            except ValueError:
                status = TraceStatus.PENDING
        
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        verified_at = data.get("verified_at")
        if verified_at and isinstance(verified_at, str):
            verified_at = datetime.fromisoformat(verified_at)
        
        return cls(
            link_id=data["link_id"],
            source_type=data["source_type"],
            source_id=data["source_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            link_type=link_type or LinkType.TASK_TO_AGENT,
            created_at=created_at or datetime.now(),
            verified_at=verified_at,
            status=status or TraceStatus.PENDING,
            metadata=data.get("metadata", {})
        )


class TraceabilityMatrix:
    """
    追溯性矩陣
    
    AI-native 特點：
    - 自動記錄所有執行鏈
    - 不增加執行負擔
    - ASPICE 合規
    
    用法：
    
    ```python
    from traceability_matrix import TraceabilityMatrix, TraceStatus
    
    # 初始化
    trace = TraceabilityMatrix()
    
    # 任務建立時
    trace.add_link("task", "task-001", "agent", "architect-001")
    
    # Agent 執行時
    trace.add_link("agent", "architect-001", "output", "output-001")
    
    # 驗證完成時
    trace.mark_verified(link_id)
    
    # 查詢追溯鏈
    links = trace.get_trace("task-001")
    
    # 驗證完整性
    completeness = trace.verify_completeness()
    
    # 匯出報告
    report = trace.export_report()
    ```
    """
    
    def __init__(self, project_id: str = "default"):
        """
        初始化追溯矩陣
        
        Args:
            project_id: 專案 ID
        """
        self.project_id = project_id
        self.links: Dict[str, TraceLink] = {}
        self.task_outputs: Dict[str, List[str]] = {}  # task_id -> output_ids
        self.agent_outputs: Dict[str, List[str]] = {}  # agent_id -> output_ids
        self.verification_records: Dict[str, Dict] = {}  # link_id -> verification record
    
    def _infer_link_type(self, source_type: str, target_type: str) -> LinkType:
        """推斷鏈接類型"""
        if source_type == "task" and target_type == "agent":
            return LinkType.TASK_TO_AGENT
        elif source_type == "agent" and target_type == "output":
            return LinkType.AGENT_TO_OUTPUT
        elif source_type == "output" and target_type == "verification":
            return LinkType.OUTPUT_TO_VERIFICATION
        elif source_type == "task" and target_type == "output":
            return LinkType.TASK_TO_OUTPUT
        elif source_type == "verification" and target_type == "signed":
            return LinkType.VERIFICATION_TO_SIGNED
        return LinkType.TASK_TO_AGENT
    
    def add_link(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        自動建立追溯鏈
        
        Args:
            source_type: 來源類型 ("task", "agent", "output", "verification")
            source_id: 來源 ID
            target_type: 目標類型
            target_id: 目標 ID
            metadata: 額外元數據
            
        Returns:
            link_id: 追溯鏈接 ID
        """
        link_id = f"TRL-{uuid.uuid4().hex[:8]}"
        link_type = self._infer_link_type(source_type, target_type)
        
        link = TraceLink(
            link_id=link_id,
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            link_type=link_type,
            created_at=datetime.now(),
            status=TraceStatus.PENDING,
            metadata=metadata or {}
        )
        
        self.links[link_id] = link
        
        # 更新索引
        if source_type == "task":
            self.task_outputs.setdefault(source_id, []).append(target_id)
        if source_type == "agent":
            self.agent_outputs.setdefault(source_id, []).append(target_id)
        
        return link_id
    
    def mark_verified(self, link_id: str, verifier: str = "system") -> bool:
        """
        標記為已驗證
        
        Args:
            link_id: 鏈接 ID
            verifier: 驗證者
            
        Returns:
            是否成功
        """
        if link_id not in self.links:
            return False
        
        link = self.links[link_id]
        link.status = TraceStatus.VERIFIED
        link.verified_at = datetime.now()
        
        # 記錄驗證
        self.verification_records[link_id] = {
            "verifier": verifier,
            "verified_at": link.verified_at.isoformat()
        }
        
        return True
    
    def mark_failed(self, link_id: str, reason: str = "") -> bool:
        """標記為失敗"""
        if link_id not in self.links:
            return False
        
        link = self.links[link_id]
        link.status = TraceStatus.FAILED
        link.metadata["failure_reason"] = reason
        
        return True
    
    def get_trace(self, item_id: str, item_type: Optional[str] = None) -> List[TraceLink]:
        """
        取得某項目或任務的完整追溯鏈
        
        Args:
            item_id: 項目 ID
            item_type: 項目類型 (可選，如果不指定則匹配所有類型)
            
        Returns:
            追溯鏈接列表
        """
        if item_type:
            return [
                l for l in self.links.values()
                if (l.source_type == item_type and l.source_id == item_id) or
                   (l.target_type == item_type and l.target_id == item_id)
            ]
        else:
            return [
                l for l in self.links.values()
                if l.source_id == item_id or l.target_id == item_id
            ]
    
    def get_task_to_output_chain(self, task_id: str) -> List[TraceLink]:
        """
        取得任務到產出的完整鏈
        
        Args:
            task_id: 任務 ID
            
        Returns:
            完整追溯鏈
        """
        chain = []
        visited = set()
        
        # BFS 遍歷
        queue = [task_id]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # 找到從 current 出發的鏈接
            for link in self.links.values():
                if link.source_id == current and link.link_id not in visited:
                    chain.append(link)
                    queue.append(link.target_id)
        
        return chain
    
    def verify_completeness(self) -> dict:
        """
        驗證追溯完整性
        
        Returns:
            完整性報告
        """
        total = len(self.links)
        verified = sum(1 for l in self.links.values() if l.status == TraceStatus.VERIFIED)
        pending = sum(1 for l in self.links.values() if l.status == TraceStatus.PENDING)
        in_progress = sum(1 for l in self.links.values() if l.status == TraceStatus.IN_PROGRESS)
        failed = sum(1 for l in self.links.values() if l.status == TraceStatus.FAILED)
        
        # 計算覆蓋率
        tasks_with_agents = set()
        tasks_with_outputs = set()
        
        for link in self.links.values():
            if link.link_type == LinkType.TASK_TO_AGENT:
                tasks_with_agents.add(link.source_id)
            if link.link_type == LinkType.TASK_TO_OUTPUT or \
               link.link_type == LinkType.AGENT_TO_OUTPUT:
                tasks_with_outputs.add(link.source_id)
        
        return {
            "total_links": total,
            "verified": verified,
            "pending": pending,
            "in_progress": in_progress,
            "failed": failed,
            "complete_rate": f"{(verified/total*100):.1f}%" if total > 0 else "N/A",
            "verification_rate": f"{(verified/total*100):.1f}%" if total > 0 else "N/A",
            "tasks_with_agents": len(tasks_with_agents),
            "tasks_with_outputs": len(tasks_with_outputs)
        }
    
    def get_aspice_report(self) -> dict:
        """
        生成 ASPICE 合規報告
        
        Returns:
            ASPICE 報告
        """
        completeness = self.verify_completeness()
        
        # 按鏈接類型分類
        by_type: Dict[str, List] = {}
        for link in self.links.values():
            lt = link.link_type.value if isinstance(link.link_type, Enum) else str(link.link_type)
            by_type.setdefault(lt, []).append(link.to_dict())
        
        return {
            "project_id": self.project_id,
            "generated_at": datetime.now().isoformat(),
            "aspice_compliance": {
                "traceability_complete": completeness["complete_rate"] != "N/A",
                "verification_complete": completeness["verification_rate"] == "100.0%",
                "coverage": {
                    "tasks_with_agent_assignment": completeness["tasks_with_agents"],
                    "tasks_with_outputs": completeness["tasks_with_outputs"]
                }
            },
            "summary": completeness,
            "links_by_type": {k: len(v) for k, v in by_type.items()},
            "all_links": [l.to_dict() for l in self.links.values()]
        }
    
    def export_report(self, format: str = "dict") -> dict:
        """
        匯出追溯報告
        
        Args:
            format: 輸出格式 ("dict", "json", "aspice")
            
        Returns:
            報告字典
        """
        if format == "aspice":
            return self.get_aspice_report()
        
        return {
            "project_id": self.project_id,
            "generated_at": datetime.now().isoformat(),
            "summary": self.verify_completeness(),
            "links": [l.to_dict() for l in self.links.values()],
            "verification_records": self.verification_records
        }
    
    def save(self, filepath: str) -> bool:
        """保存到文件"""
        try:
            data = self.export_report()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    @classmethod
    def load(cls, filepath: str) -> Optional["TraceabilityMatrix"]:
        """從文件加載"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            matrix = cls(project_id=data.get("project_id", "default"))
            
            for link_data in data.get("links", []):
                link = TraceLink.from_dict(link_data)
                matrix.links[link.link_id] = link
            
            matrix.verification_records = data.get("verification_records", {})
            
            # 重建索引
            for link in matrix.links.values():
                if link.source_type == "task":
                    matrix.task_outputs.setdefault(link.source_id, []).append(link.target_id)
                if link.source_type == "agent":
                    matrix.agent_outputs.setdefault(link.source_id, []).append(link.target_id)
            
            return matrix
        except Exception:
            return None
    
    def get_downstream_links(self, item_id: str) -> List[TraceLink]:
        """獲取某項目的下游鏈接"""
        return [l for l in self.links.values() if l.source_id == item_id]
    
    def get_upstream_links(self, item_id: str) -> List[TraceLink]:
        """獲取某項目的上游鏈接"""
        return [l for l in self.links.values() if l.target_id == item_id]


# ============================================================================
# Integration Helper
# ============================================================================

class TraceabilityMixin:
    """
    追溯性混入類
    
    用於為現有類別添加追溯性支持
    
    ```python
    class MyAgent(TraceabilityMixin):
        def __init__(self):
            super().__init__()
            self.trace = get_traceability_matrix()
        
        def execute(self, task):
            link_id = self.trace.add_link("agent", self.id, "output", output_id)
            # ... execute task
            self.trace.mark_verified(link_id)
    ```
    """
    
    _traceability_matrix: Optional[TraceabilityMatrix] = None
    
    @classmethod
    def get_traceability_matrix(cls) -> TraceabilityMatrix:
        """獲取或創建追溯矩陣"""
        if cls._traceability_matrix is None:
            cls._traceability_matrix = TraceabilityMatrix()
        return cls._traceability_matrix
    
    @classmethod
    def set_traceability_matrix(cls, matrix: TraceabilityMatrix):
        """設置追溯矩陣"""
        cls._traceability_matrix = matrix


# 全局追溯矩陣實例
_global_traceability: Optional[TraceabilityMatrix] = None


def get_traceability_matrix() -> TraceabilityMatrix:
    """獲取全局追溯矩陣實例"""
    global _global_traceability
    if _global_traceability is None:
        _global_traceability = TraceabilityMatrix()
    return _global_traceability


def reset_traceability_matrix():
    """重置全局追溯矩陣"""
    global _global_traceability
    _global_traceability = None


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Demo
    print("=== Traceability Matrix Demo ===\n")
    
    trace = TraceabilityMatrix(project_id="ai-agent-v1")
    
    # 模擬 ASPICE 追溯鏈
    print("1. 建立任務到 Agent 的追溯...")
    link1 = trace.add_link("task", "task-001", "agent", "architect-001")
    print(f"   Created: {link1}")
    
    print("\n2. 建立 Agent 到 Output 的追溯...")
    link2 = trace.add_link("agent", "architect-001", "output", "output-001")
    print(f"   Created: {link2}")
    
    print("\n3. 標記為已驗證...")
    trace.mark_verified(link1)
    trace.mark_verified(link2)
    print(f"   Verified: {link1}, {link2}")
    
    print("\n4. 查詢 task-001 的完整追溯鏈...")
    chain = trace.get_trace("task-001")
    for link in chain:
        print(f"   {link.source_id} -> {link.target_id} [{link.status.value}]")
    
    print("\n5. 驗證完整性...")
    completeness = trace.verify_completeness()
    for k, v in completeness.items():
        print(f"   {k}: {v}")
    
    print("\n6. ASPICE 合規報告...")
    report = trace.get_aspice_report()
    print(f"   Traceability Complete: {report['aspice_compliance']['traceability_complete']}")
    print(f"   Verification Complete: {report['aspice_compliance']['verification_complete']}")
