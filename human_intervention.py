#!/usr/bin/env python3
"""
Human Intervention - 人類介入界面

功能：
- 狀態儀表板
- 介入請求
- 行動批准
- 狀態覆寫
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid

class InterventionType(Enum):
    """介入類型"""
    APPROVAL = "approval"           # 需要批准
    CORRECTION = "correction"       # 需要修正
    ESCALATION = "escalation"       # 需要升級
    NOTIFICATION = "notification"  # 僅通知

class InterventionStatus(Enum):
    """介入狀態"""
    PENDING = "pending"         # 等待處理
    IN_PROGRESS = "in_progress" # 處理中
    RESOLVED = "resolved"        # 已解決
    CANCELLED = "cancelled"      # 已取消

@dataclass
class StatusDashboard:
    """狀態儀表板"""
    agent_id: str
    task_id: str
    current_state: Dict[str, Any]
    last_checkpoint: Optional[Dict] = None
    active_failures: List[Dict] = field(default_factory=list)
    pending_interventions: List[Dict] = field(default_factory=list)
    recent_history: List[Dict] = field(default_factory=list)
    generated_at: datetime = field(default=datetime.now)

@dataclass
class InterventionRequest:
    """介入請求"""
    request_id: str
    agent_id: str
    task_id: str
    intervention_type: InterventionType
    reason: str
    current_state: Dict[str, Any]
    suggested_actions: List[str] = field(default_factory=list)
    priority: int = 1  # 1-5, 5 是最高
    status: InterventionStatus = InterventionStatus.PENDING
    created_at: datetime = field(default=datetime.now)
    requested_by: str = "system"  # system, human
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "intervention_type": self.intervention_type.value,
            "reason": self.reason,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "requested_by": self.requested_by,
            "suggested_actions": self.suggested_actions,
        }

class HumanIntervention:
    """
    人類介入界面
    
    功能：
    - 顯示當前狀態
    - 請求介入
    - 批准/拒絕行動
    - 覆寫狀態
    """
    
    def __init__(self, notification_handler: Callable = None):
        self.pending_requests: Dict[str, InterventionRequest] = {}
        self.resolved_requests: Dict[str, InterventionRequest] = {}
        self.notification_handler = notification_handler
        self.intervention_history: List[InterventionRequest] = []
    
    def show_status(self, agent_id: str, task_id: str = None,
                    checkpoint_manager=None, recovery_controller=None) -> StatusDashboard:
        """
        顯示狀態儀表板
        
        Args:
            agent_id: Agent ID
            task_id: 任務 ID（可選）
            checkpoint_manager: CheckpointManager 實例
            recovery_controller: RecoveryController 實例
        
        Returns:
            StatusDashboard: 狀態儀表板
        """
        dashboard = StatusDashboard(
            agent_id=agent_id,
            task_id=task_id or "all",
            current_state={},
        )
        
        # 獲取最後快照
        if checkpoint_manager:
            latest = checkpoint_manager.get_latest(agent_id)
            if latest:
                dashboard.last_checkpoint = {
                    "checkpoint_id": latest.checkpoint_id,
                    "created_at": latest.created_at.isoformat(),
                    "task_id": latest.task_id,
                }
                dashboard.current_state = latest.state
        
        # 獲取活躍失敗
        if recovery_controller:
            active = recovery_controller.get_active_failures()
            dashboard.active_failures = [
                {
                    "failure_id": f.failure_id,
                    "type": f.failure_type.value,
                    "severity": f.severity.value,
                    "message": f.message,
                    "occurred_at": f.occurred_at.isoformat(),
                }
                for f in active if f.agent_id == agent_id
            ]
        
        # 獲取待處理介入
        dashboard.pending_interventions = [
            req.to_dict()
            for req in self.pending_requests.values()
            if req.agent_id == agent_id
        ]
        
        return dashboard
    
    def request_intervention(self, agent_id: str, task_id: str,
                            intervention_type: InterventionType,
                            reason: str,
                            current_state: Dict = None,
                            suggested_actions: List[str] = None,
                            priority: int = 1) -> str:
        """
        請求介入
        
        Args:
            agent_id: Agent ID
            task_id: 任務 ID
            intervention_type: 介入類型
            reason: 原因
            current_state: 當前狀態
            suggested_actions: 建議行動
            priority: 優先級 1-5
        
        Returns:
            request_id: 請求 ID
        """
        request_id = f"intv-{uuid.uuid4().hex[:12]}"
        
        request = InterventionRequest(
            request_id=request_id,
            agent_id=agent_id,
            task_id=task_id,
            intervention_type=intervention_type,
            reason=reason,
            current_state=current_state or {},
            suggested_actions=suggested_actions or [],
            priority=priority,
        )
        
        self.pending_requests[request_id] = request
        self.intervention_history.append(request)
        
        # 通知
        if self.notification_handler:
            self.notification_handler({
                "type": "intervention_request",
                "request": request.to_dict(),
            })
        
        return request_id
    
    def approve_action(self, request_id: str, approver: str,
                      comments: str = None) -> bool:
        """
        批准行動
        
        Args:
            request_id: 請求 ID
            approver: 批准者
            comments: 評論
        
        Returns:
            bool: 是否成功
        """
        request = self.pending_requests.get(request_id)
        if not request:
            return False
        
        request.status = InterventionStatus.RESOLVED
        request.resolved_at = datetime.now()
        request.resolution = "approved"
        request.resolved_by = approver
        
        # 移動到已解決
        self.resolved_requests[request_id] = request
        del self.pending_requests[request_id]
        
        # 通知
        if self.notification_handler:
            self.notification_handler({
                "type": "intervention_approved",
                "request": request.to_dict(),
                "approver": approver,
                "comments": comments,
            })
        
        return True
    
    def reject_action(self, request_id: str, rejector: str,
                     reason: str = None) -> bool:
        """
        拒絕行動
        
        Args:
            request_id: 請求 ID
            rejector: 拒絕者
            reason: 原因
        
        Returns:
            bool: 是否成功
        """
        request = self.pending_requests.get(request_id)
        if not request:
            return False
        
        request.status = InterventionStatus.CANCELLED
        request.resolved_at = datetime.now()
        request.resolution = f"rejected: {reason}" if reason else "rejected"
        request.resolved_by = rejector
        
        # 移動到已解決
        self.resolved_requests[request_id] = request
        del self.pending_requests[request_id]
        
        # 通知
        if self.notification_handler:
            self.notification_handler({
                "type": "intervention_rejected",
                "request": request.to_dict(),
                "rejector": rejector,
                "reason": reason,
            })
        
        return True
    
    def override_state(self, agent_id: str, new_state: Dict[str, Any],
                      override_by: str, reason: str = None) -> bool:
        """
        覆寫狀態
        
        Args:
            agent_id: Agent ID
            new_state: 新狀態
            override_by: 覆寫者
            reason: 原因
        
        Returns:
            bool: 是否成功
        """
        # 這只是一個標記操作，實際狀態更新需要由調用者處理
        if self.notification_handler:
            self.notification_handler({
                "type": "state_override",
                "agent_id": agent_id,
                "new_state": new_state,
                "override_by": override_by,
                "reason": reason,
                "timestamp": datetime.now().isoformat(),
            })
        
        return True
    
    def resolve_and_continue(self, request_id: str, resolution: str,
                            continuator: str) -> bool:
        """
        解決並繼續執行
        
        Args:
            request_id: 請求 ID
            resolution: 解決方案描述
            continuator: 處理者
        
        Returns:
            bool: 是否成功
        """
        request = self.pending_requests.get(request_id)
        if not request:
            return False
        
        request.status = InterventionStatus.RESOLVED
        request.resolved_at = datetime.now()
        request.resolution = resolution
        request.resolved_by = continuator
        
        self.resolved_requests[request_id] = request
        del self.pending_requests[request_id]
        
        # 通知繼續執行
        if self.notification_handler:
            self.notification_handler({
                "type": "continue_execution",
                "request": request.to_dict(),
                "resolution": resolution,
            })
        
        return True
    
    def get_pending_requests(self, agent_id: str = None,
                            priority: int = None) -> List[InterventionRequest]:
        """取得待處理請求"""
        requests = list(self.pending_requests.values())
        
        if agent_id:
            requests = [r for r in requests if r.agent_id == agent_id]
        
        if priority:
            requests = [r for r in requests if r.priority >= priority]
        
        # 按優先級和時間排序
        requests.sort(key=lambda x: (-x.priority, x.created_at))
        
        return requests
    
    def get_intervention_history(self, agent_id: str = None,
                                  limit: int = 100) -> List[InterventionRequest]:
        """取得介入歷史"""
        history = self.intervention_history
        
        if agent_id:
            history = [r for r in history if r.agent_id == agent_id]
        
        return history[-limit:]
    
    def get_intervention_summary(self) -> dict:
        """取得介入摘要"""
        pending = list(self.pending_requests.values())
        
        return {
            "total_pending": len(pending),
            "by_type": {
                it.value: sum(1 for r in pending if r.intervention_type == it)
                for it in InterventionType
            },
            "by_priority": {
                f"p{p}": sum(1 for r in pending if r.priority == p)
                for p in range(1, 6)
            },
            "avg_resolution_time": self._calculate_avg_resolution_time(),
        }
    
    def _calculate_avg_resolution_time(self) -> Optional[float]:
        """計算平均解決時間（分鐘）"""
        resolved = [r for r in self.resolved_requests.values() if r.resolved_at]
        if not resolved:
            return None
        
        total_minutes = 0
        for r in resolved:
            delta = r.resolved_at - r.created_at
            total_minutes += delta.total_seconds() / 60
        
        return round(total_minutes / len(resolved), 2)
    
    def export_dashboard_text(self, dashboard: StatusDashboard) -> str:
        """導出儀表板為文字格式"""
        lines = [
            "=" * 60,
            f"Agent Status Dashboard",
            "=" * 60,
            f"Agent ID: {dashboard.agent_id}",
            f"Task ID: {dashboard.task_id}",
            f"Generated: {dashboard.generated_at.isoformat()}",
            "",
        ]
        
        if dashboard.last_checkpoint:
            lines.append("Last Checkpoint:")
            lines.append(f"  ID: {dashboard.last_checkpoint['checkpoint_id']}")
            lines.append(f"  Created: {dashboard.last_checkpoint['created_at']}")
            lines.append("")
        
        if dashboard.active_failures:
            lines.append(f"Active Failures ({len(dashboard.active_failures)}):")
            for f in dashboard.active_failures:
                lines.append(f"  - [{f['severity']}] {f['type']}: {f['message']}")
            lines.append("")
        
        if dashboard.pending_interventions:
            lines.append(f"Pending Interventions ({len(dashboard.pending_interventions)}):")
            for i in dashboard.pending_interventions:
                lines.append(f"  - [{i['priority']}] {i['intervention_type']}: {i['reason']}")
            lines.append("")
        
        return "\n".join(lines)