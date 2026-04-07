#!/usr/bin/env python3
"""
HITL Workflow - 與現有架構整合

整合：
- agent_team.py (Agent 管理)
- approval_flow.py (審批)
- message_bus.py (訊息傳遞)

使用方法：
    from hitl_workflow import HITLWorkflow
    from hitl_controller import HITLController
    
    controller = HITLController()
    workflow = HITLWorkflow(controller)
    
    # 當 Agent 產出生結果時
    workflow.on_agent_output("agent-1", {"data": "result"}, "task-1")
"""

from typing import Any, Optional, Dict, List
from hitl_controller import HITLController, OutputStatus, AgentOwner


class HITLWorkflow:
    """HITL 工作流整合"""
    
    def __init__(self, controller: HITLController):
        """
        初始化 HITL Workflow
        
        Args:
            controller: HITLController 實例
        """
        self.controller = controller
        self._notification_handlers: List[callable] = []
    
    def register_notification_handler(self, handler: callable):
        """
        註冊通知處理器
        
        Args:
            handler: 回調函數，簽名為 handler(output_id, owner_id, event_type)
        """
        self._notification_handlers.append(handler)
    
    def on_agent_output(self, agent_id: str, output: Any, task_id: str) -> str:
        """
        當 Agent 產出生結果時
        
        自動流程：
        1. 建立產出
        2. 自動提交審批
        3. 通知負責人
        
        Args:
            agent_id: Agent ID
            output: 產出內容
            task_id: 任務 ID
            
        Returns:
            str: 產出 ID
        """
        # 1. 自動建立產出
        output_id = self.controller.create_output(agent_id, task_id, output)
        
        # 2. 自動提交審批
        self.controller.submit_for_review(output_id)
        
        # 3. 通知負責人
        self._notify_owner(output_id, "new_output")
        
        return output_id
    
    def on_owner_approve(self, output_id: str, owner_id: str) -> bool:
        """
        當負責人批准時
        
        Args:
            output_id: 產出 ID
            owner_id: 負責人 ID
            
        Returns:
            bool: 是否成功
        """
        result = self.controller.approve_output(output_id, owner_id)
        
        if result:
            # 通知相關方
            self._notify_handlers(output_id, owner_id, "approved")
        
        return result
    
    def on_owner_revision(self, output_id: str, owner_id: str, feedback: str) -> bool:
        """
        當負責人要求修改時
        
        Args:
            output_id: 產出 ID
            owner_id: 負責人 ID
            feedback: 修訂回饋
            
        Returns:
            bool: 是否成功
        """
        result = self.controller.request_revision(output_id, owner_id, feedback)
        
        if result:
            # 通知 Agent 需要修訂
            self._notify_agent(output_id, "revision_requested", feedback)
            self._notify_handlers(output_id, owner_id, "revision_requested")
        
        return result
    
    def on_owner_escalate(self, output_id: str, reason: str) -> bool:
        """
        當負責人升級問題時
        
        Args:
            output_id: 產出 ID
            reason: 升級原因
            
        Returns:
            bool: 是否成功
        """
        result = self.controller.escalate_output(output_id, reason)
        
        if result:
            self._notify_handlers(output_id, None, "escalated")
        
        return result
    
    def _notify_owner(self, output_id: str, event_type: str):
        """通知負責人"""
        output = self.controller.get_output(output_id)
        if not output:
            return
        
        owner = self.controller.get_owner(output.owner_id)
        if not owner:
            return
        
        # 觸發通知
        for handler in self._notification_handlers:
            try:
                handler(output_id, output.owner_id, event_type)
            except Exception as e:
                print(f"Warning: Notification handler failed: {e}")
    
    def _notify_agent(self, output_id: str, event_type: str, feedback: str = None):
        """通知 Agent"""
        output = self.controller.get_output(output_id)
        if not output:
            return
        
        for handler in self._notification_handlers:
            try:
                handler(output_id, output.agent_id, event_type, feedback=feedback)
            except Exception as e:
                print(f"Warning: Notification handler failed: {e}")
    
    def _notify_handlers(self, output_id: str, owner_id: Optional[str], event_type: str, **kwargs):
        """觸發所有通知處理器"""
        for handler in self._notification_handlers:
            try:
                handler(output_id, owner_id, event_type, **kwargs)
            except Exception as e:
                print(f"Warning: Notification handler failed: {e}")
    
    def get_pending_for_owner(self, owner_id: str) -> List[Dict]:
        """
        取得負責人的待審批列表
        
        Args:
            owner_id: 負責人 ID
            
        Returns:
            List[Dict]: 待審批產出列表
        """
        pending = self.controller.get_pending_reviews(owner_id)
        return [
            {
                "output_id": o.id,
                "agent_id": o.agent_id,
                "task_id": o.task_id,
                "status": o.status.value,
                "created_at": o.created_at.isoformat(),
                "feedback": o.feedback,
                "revision_count": o.revision_count,
            }
            for o in pending
        ]
    
    def get_owner_workload(self, owner_id: str) -> Dict:
        """
        取得負責人的工作負載統計
        
        Args:
            owner_id: 負責人 ID
            
        Returns:
            Dict: 負載統計
        """
        outputs = self.controller.get_outputs_by_owner(owner_id)
        
        return {
            "total": len(outputs),
            "pending": sum(1 for o in outputs if o.status == OutputStatus.PENDING_REVIEW),
            "approved": sum(1 for o in outputs if o.status == OutputStatus.APPROVED),
            "revision_requested": sum(1 for o in outputs if o.status == OutputStatus.REVISION_REQUESTED),
            "completed": sum(1 for o in outputs if o.status == OutputStatus.COMPLETED),
            "escalated": sum(1 for o in outputs if o.status == OutputStatus.ESCALATED),
        }


# ============================================================================
# 整合適配器
# ============================================================================

class AgentTeamHITLAdapter:
    """AgentTeam 整合適配器
    
    將 HITL Workflow 整合到 AgentTeam 系統
    """
    
    def __init__(self, team, hitl_controller: HITLController):
        """
        初始化適配器
        
        Args:
            team: AgentTeam 實例
            hitl_controller: HITLController 實例
        """
        self.team = team
        self.controller = hitl_controller
        self.workflow = HITLWorkflow(hitl_controller)
    
    def assign_owner_to_agent_instance(self, instance_id: str, owner_id: str) -> bool:
        """
        為 Agent 實例指派負責人
        
        Args:
            instance_id: Agent 實例 ID
            owner_id: 負責人 ID
            
        Returns:
            bool: 是否成功
        """
        instance = self.team.get_instance(instance_id)
        if not instance:
            return False
        
        # 更新 AgentInstance 的 owner_id
        instance.owner_id = owner_id
        
        # 更新 HITL controller 的映射
        return self.controller.assign_agent_to_owner(instance_id, owner_id)
    
    def on_task_completed(self, instance_id: str, task_id: str, result: Any) -> str:
        """
        當任務完成時觸發 HITL 流程
        
        Args:
            instance_id: Agent 實例 ID
            task_id: 任務 ID
            result: 任務結果
            
        Returns:
            str: 產出 ID
        """
        return self.workflow.on_agent_output(instance_id, result, task_id)


class MessageBusHITLAdapter:
    """MessageBus 整合適配器
    
    將 HITL 事件發送到訊息匯流排
    """
    
    def __init__(self, message_bus, hitl_controller: HITLController):
        """
        初始化適配器
        
        Args:
            message_bus: MessageBus 實例
            hitl_controller: HITLController 實例
        """
        self.bus = message_bus
        self.controller = hitl_controller
        self.workflow = HITLWorkflow(hitl_controller)
        
        # 註冊通知處理器
        self.workflow.register_notification_handler(self._on_hitl_event)
    
    def _on_hitl_event(self, output_id: str, target_id: str, event_type: str, **kwargs):
        """處理 HITL 事件並發送到匯流排"""
        output = self.controller.get_output(output_id)
        if not output:
            return
        
        message = {
            "type": "hitl_event",
            "event": event_type,
            "output_id": output_id,
            "agent_id": output.agent_id,
            "owner_id": output.owner_id,
            "task_id": output.task_id,
            "status": output.status.value,
            "feedback": kwargs.get("feedback"),
        }
        
        # 發送到匯流排
        topic = f"hitl.{event_type}"
        self.bus.publish(topic, message)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # 演示用法
    from hitl_controller import HITLController, AgentOwner
    
    controller = HITLController()
    workflow = HITLWorkflow(controller)
    
    # 註冊負責人
    owner = AgentOwner(
        owner_id="owner-1",
        name="John",
        email="john@example.com",
        role="Manager"
    )
    controller.register_owner(owner)
    controller.assign_agent_to_owner("agent-dev-1", "owner-1")
    
    print("=== HITL Workflow Demo ===")
    
    # 模擬 Agent 產出
    output_id = workflow.on_agent_output(
        "agent-dev-1",
        {"feature": "login", "status": "completed"},
        "task-123"
    )
    print(f"Created output: {output_id}")
    print(f"Status: {controller.get_output(output_id).status.value}")
    
    # 模擬批准
    workflow.on_owner_approve(output_id, "owner-1")
    print(f"After approve: {controller.get_output(output_id).status.value}")
    
    # 統計
    print("\n=== Owner Workload ===")
    workload = workflow.get_owner_workload("owner-1")
    for k, v in workload.items():
        print(f"  {k}: {v}")
