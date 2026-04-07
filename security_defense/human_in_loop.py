#!/usr/bin/env python3
"""
Human-in-the-Loop
==================
Layer 4: 人類審批 - 敏感操作需要人類確認

功能：
- 審批請求佇列
- 自動升級
- 審批追蹤
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid


class ApprovalLevel(Enum):
    """審批等級"""
    INFO = "info"           # 僅通知
    REVIEW = "review"       # 需要審查
    APPROVAL = "approval"   # 需要批准
    BLOCK = "block"         # 阻擋


@dataclass
class ApprovalRequest:
    """審批請求"""
    request_id: str
    agent_id: str
    action: str
    description: str
    level: ApprovalLevel
    created_at: datetime
    status: str  # pending, approved, rejected, expired
    approver: str = ""
    response_at: Optional[datetime] = None
    notes: str = ""


class HumanInTheLoop:
    """
    人類在環
    
    使用方式：
    
    ```python
    hitl = HumanInTheLoop()
    
    # 請求審批
    request = hitl.request_approval(
        agent_id="agent-1",
        action="send_email",
        description="Send password reset email to user@example.com",
        level=ApprovalLevel.APPROVAL
    )
    
    # 等待批准
    if hitl.wait_for_approval(request.request_id, timeout=300):
        print("Approved!")
    else:
        print("Rejected or timeout")
    ```
    """
    
    def __init__(self, escalation_levels: List[str] = None):
        """
        初始化
        
        Args:
            escalation_levels: 升級順序 ["owner", "manager", "executive"]
        """
        self.escalation_levels = escalation_levels or ["owner", "manager", "executive"]
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approved_requests: set = set()
        self.rejected_requests: set = set()
    
    def request_approval(
        self,
        agent_id: str,
        action: str,
        description: str,
        level: ApprovalLevel = ApprovalLevel.REVIEW,
        context: dict = None
    ) -> ApprovalRequest:
        """請求審批"""
        request = ApprovalRequest(
            request_id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            action=action,
            description=description,
            level=level,
            created_at=datetime.now(),
            status="pending"
        )
        
        self.pending_requests[request.request_id] = request
        
        return request
    
    def approve(self, request_id: str, approver: str, notes: str = "") -> bool:
        """批准請求"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        request.status = "approved"
        request.approver = approver
        request.response_at = datetime.now()
        request.notes = notes
        
        self.approved_requests.add(request_id)
        
        return True
    
    def reject(self, request_id: str, approver: str, notes: str = "") -> bool:
        """拒絕請求"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        request.status = "rejected"
        request.approver = approver
        request.response_at = datetime.now()
        request.notes = notes
        
        self.rejected_requests.add(request_id)
        
        return True
    
    def wait_for_approval(self, request_id: str, timeout: int = 300) -> bool:
        """
        等待批准（同步等待）
        
        現實中應該是非同步的，這裡只是簡化實現
        """
        request = self.pending_requests.get(request_id)
        if not request:
            return False
        
        # 檢查是否已批准
        if request_id in self.approved_requests:
            return True
        
        # 檢查是否已拒絕
        if request_id in self.rejected_requests:
            return False
        
        # 檢查是否過期
        max_wait = timedelta(seconds=timeout)
        if datetime.now() - request.created_at > max_wait:
            request.status = "expired"
            return False
        
        # 返回狀態（實際應用中這裡會是事件驅動）
        return request.status == "approved"
    
    def should_escalate(self, request: ApprovalRequest) -> bool:
        """檢查是否需要升級"""
        if request.level in [ApprovalLevel.INFO, ApprovalLevel.REVIEW]:
            return False
        
        # 等待超過 5 分鐘自動升級
        return datetime.now() - request.created_at > timedelta(minutes=5)
    
    def get_pending(self) -> List[ApprovalRequest]:
        """取得待審批請求"""
        return [
            r for r in self.pending_requests.values()
            if r.status == "pending"
        ]
