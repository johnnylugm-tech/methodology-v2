#!/usr/bin/env python3
"""
HITL Controller - 人類介入控制中心

職責：
- 管理 Agent 負責人 (Owner)
- 追蹤產出生命週期
- 處理審批/修訂/升級
- 支援企業表單系統整合

使用方法：
    from hitl_controller import HITLController, AgentOwner, OutputStatus
    
    controller = HITLController()
    
    # 註冊負責人
    owner = AgentOwner(
        owner_id="owner-1",
        name="John",
        email="john@example.com",
        role="Manager"
    )
    controller.register_owner(owner)
    
    # 建立產出
    output_id = controller.create_output("agent-1", "task-1", {"result": "data"})
    controller.submit_for_review(output_id)
    
    # 批准
    controller.approve_output(output_id, "owner-1")
"""

from abc import ABC, abstractmethod

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import json


# ============================================================================
# 企業表單系統整合介面
# ============================================================================

class FormSystemAdapter(ABC):
    """
    企業表單系統介面卡
    
    用途：
    - 整合 Jira、ServiceNow、SAP、Monday.com 等企業表單系統
    - 將 HITL 審批流程無縫嵌入企業既有工作流
    
    使用方式：
        # 自定義 Jira 整合
        class JiraFormAdapter(FormSystemAdapter):
            def create_ticket(self, output):
                return jira_client.create_issue(...)
            
            def notify_approval(self, owner_id, output):
                jira_client.add_comment(...)
        
        # 使用
        controller = HITLController()
        controller.set_form_adapter(JiraFormAdapter())
    """
    
    @abstractmethod
    def create_ticket(self, output: "Output", owner: "AgentOwner") -> str:
        """
        在表單系統中建立審批工單
        
        Args:
            output: 產出物件
            owner: 負責人
        
        Returns:
            str: 工單 ID
        """
        pass
    
    @abstractmethod
    def notify_approval(self, owner_id: str, output: "Output", action: str):
        """
        通知負責人有新審批任務
        
        Args:
            owner_id: 負責人 ID
            output: 產出物件
            action: 操作類型 (approve/reject/escalate)
        """
        pass
    
    @abstractmethod
    def get_approval_status(self, ticket_id: str) -> str:
        """
        查詢表單系統中的審批狀態
        
        Args:
            ticket_id: 工單 ID
        
        Returns:
            str: 狀態 (approved/rejected/pending)
        """
        pass
    
    @abstractmethod
    def update_ticket(self, ticket_id: str, status: str, feedback: str = None):
        """
        更新表單系統中的工單狀態
        
        Args:
            ticket_id: 工單 ID
            status: 新狀態
            feedback: 審批意見
        """
        pass


class DefaultFormAdapter(FormSystemAdapter):
    """
    預設表單適配器（僅本地儲存）
    
    適用場景：
    - POC / 快速驗證
    - 無企業表單系統需求
    """
    
    def __init__(self):
        self.tickets: Dict[str, dict] = {}
    
    def create_ticket(self, output: "Output", owner: "AgentOwner") -> str:
        ticket_id = f"TICKET-{output.id}"
        self.tickets[ticket_id] = {
            "output_id": output.id,
            "owner_id": owner.owner_id,
            "status": "pending"
        }
        return ticket_id
    
    def notify_approval(self, owner_id: str, output: "Output", action: str):
        # 預設實現：僅打印日誌
        print(f"[DefaultFormAdapter] Notify {owner_id}: {action} for output {output.id}")
    
    def get_approval_status(self, ticket_id: str) -> str:
        ticket = self.tickets.get(ticket_id, {})
        return ticket.get("status", "pending")
    
    def update_ticket(self, ticket_id: str, status: str, feedback: str = None):
        if ticket_id in self.tickets:
            self.tickets[ticket_id]["status"] = status
            if feedback:
                self.tickets[ticket_id]["feedback"] = feedback


class OutputStatus(Enum):
    """產出狀態"""
    DRAFT = "draft"                      # 草稿
    PENDING_REVIEW = "pending_review"    # 待審批
    APPROVED = "approved"               # 已批准
    REVISION_REQUESTED = "revision_requested"  # 需要修訂
    COMPLETED = "completed"             # 完成
    ESCALATED = "escalated"             # 已升級


class EscalationLevel(Enum):
    """升級層級"""
    OWNER = "owner"           # 負責人
    MANAGER = "manager"        # 經理
    EXECUTIVE = "executive"    # 高層


@dataclass
class AgentOwner:
    """Agent 負責人"""
    owner_id: str
    name: str
    email: str
    role: str
    agents: List[str] = field(default_factory=list)
    escalation_timeout: int = 3600  # 秒
    notification_callback: Optional[Callable] = None  # 通知回調
    
    def approve_output(self, output_id: str, controller: 'HITLController') -> bool:
        """批准產出"""
        return controller.approve_output(output_id, self.owner_id)
    
    def request_revision(self, output_id: str, feedback: str, controller: 'HITLController'):
        """要求修改"""
        return controller.request_revision(output_id, self.owner_id, feedback)
    
    def escalate(self, output_id: str, reason: str, level: EscalationLevel, controller: 'HITLController'):
        """升級問題"""
        return controller.escalate_output(output_id, reason, level)


@dataclass
class Output:
    """產出"""
    id: str
    agent_id: str
    owner_id: str  # 人類負責人
    task_id: str
    status: OutputStatus
    created_at: datetime
    content: Any = None  # 產出內容
    submitted_at: datetime = None
    approved_at: datetime = None
    approved_by: str = None
    feedback: str = None
    revision_count: int = 0
    escalation_reason: str = None
    escalation_level: EscalationLevel = None
    escalated_at: datetime = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "owner_id": self.owner_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "feedback": self.feedback,
            "revision_count": self.revision_count,
            "escalation_reason": self.escalation_reason,
            "escalation_level": self.escalation_level.value if self.escalation_level else None,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
        }


class HITLController:
    """HITL 控制中心"""
    
    def __init__(self, storage_path: str = None, form_adapter: FormSystemAdapter = None):
        """
        初始化 HITL 控制中心
        
        Args:
            storage_path: 選項，持久化儲存路徑
            form_adapter: 選項，企業表單系統介面卡（預設為 DefaultFormAdapter）
        """
        self.owners: Dict[str, AgentOwner] = {}
        self.outputs: Dict[str, Output] = {}
        self.pending_reviews: List[str] = []  # 等待審批的產出 IDs
        self.agent_to_owner: Dict[str, str] = {}  # agent_id -> owner_id 映射
        self.storage_path = storage_path
        self.form_adapter = form_adapter or DefaultFormAdapter()  # 預設本地儲存
        self._load_from_storage()
    
    def set_form_adapter(self, adapter: FormSystemAdapter):
        """
        設定企業表單系統介面卡
        
        用於整合 Jira、ServiceNow、SAP、Monday.com 等
        
        Args:
            adapter: FormSystemAdapter 實作
        """
        self.form_adapter = adapter
    
    def _generate_id(self, prefix: str) -> str:
        """生成唯一 ID"""
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    
    def _save_to_storage(self):
        """保存到儲存"""
        if not self.storage_path:
            return
        
        data = {
            "owners": {
                oid: {
                    "owner_id": o.owner_id,
                    "name": o.name,
                    "email": o.email,
                    "role": o.role,
                    "agents": o.agents,
                    "escalation_timeout": o.escalation_timeout,
                }
                for oid, o in self.owners.items()
            },
            "outputs": {
                oid: o.to_dict()
                for oid, o in self.outputs.items()
            },
            "agent_to_owner": self.agent_to_owner,
        }
        
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Failed to save HITL state: {e}")
    
    def _load_from_storage(self):
        """從儲存載入"""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # 恢復 owners
            for oid, odata in data.get("owners", {}).items():
                self.owners[oid] = AgentOwner(**odata)
            
            # 恢復 outputs
            for oid, odata in data.get("outputs", {}).items():
                odata["status"] = OutputStatus(odata["status"])
                odata["created_at"] = datetime.fromisoformat(odata["created_at"])
                if odata.get("submitted_at"):
                    odata["submitted_at"] = datetime.fromisoformat(odata["submitted_at"])
                if odata.get("approved_at"):
                    odata["approved_at"] = datetime.fromisoformat(odata["approved_at"])
                if odata.get("escalated_at"):
                    odata["escalated_at"] = datetime.fromisoformat(odata["escalated_at"])
                if odata.get("escalation_level"):
                    odata["escalation_level"] = EscalationLevel(odata["escalation_level"])
                self.outputs[oid] = Output(**odata)
            
            # 恢復 pending_reviews
            self.pending_reviews = [
                oid for oid, o in self.outputs.items()
                if o.status == OutputStatus.PENDING_REVIEW
            ]
            
            # 恢復 agent_to_owner 映射
            self.agent_to_owner = data.get("agent_to_owner", {})
            
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # 首次運行或損壞的檔案
    
    # === Owner 管理 ===
    
    def register_owner(self, owner: AgentOwner) -> bool:
        """
        註冊負責人
        
        Args:
            owner: AgentOwner 實例
            
        Returns:
            bool: 是否成功
        """
        if owner.owner_id in self.owners:
            return False
        
        self.owners[owner.owner_id] = owner
        self._save_to_storage()
        return True
    
    def get_owner(self, owner_id: str) -> Optional[AgentOwner]:
        """取得負責人"""
        return self.owners.get(owner_id)
    
    def list_owners(self) -> List[AgentOwner]:
        """列出所有負責人"""
        return list(self.owners.values())
    
    def update_owner(self, owner_id: str, **kwargs) -> bool:
        """更新負責人資訊"""
        owner = self.owners.get(owner_id)
        if not owner:
            return False
        
        for key, value in kwargs.items():
            if hasattr(owner, key):
                setattr(owner, key, value)
        
        self._save_to_storage()
        return True
    
    def assign_agent_to_owner(self, agent_id: str, owner_id: str) -> bool:
        """
        指派 Agent 給負責人
        
        Args:
            agent_id: Agent ID
            owner_id: 負責人 ID
            
        Returns:
            bool: 是否成功
        """
        if owner_id not in self.owners:
            return False
        
        self.agent_to_owner[agent_id] = owner_id
        if agent_id not in self.owners[owner_id].agents:
            self.owners[owner_id].agents.append(agent_id)
        
        self._save_to_storage()
        return True
    
    def get_owner_for_agent(self, agent_id: str) -> Optional[AgentOwner]:
        """取得 Agent 的負責人"""
        owner_id = self.agent_to_owner.get(agent_id)
        if owner_id:
            return self.owners.get(owner_id)
        return None
    
    # === 產出管理 ===
    
    def create_output(self, agent_id: str, task_id: str, content: Any = None) -> str:
        """
        建立產出
        
        Args:
            agent_id: Agent ID
            task_id: 任務 ID
            content: 產出內容可選
            
        Returns:
            str: 產出 ID
        """
        # 自動取得負責人
        owner_id = self.agent_to_owner.get(agent_id)
        
        output_id = self._generate_id("output")
        output = Output(
            id=output_id,
            agent_id=agent_id,
            owner_id=owner_id or "unassigned",
            task_id=task_id,
            status=OutputStatus.DRAFT,
            created_at=datetime.now(),
            content=content,
        )
        
        self.outputs[output_id] = output
        self._save_to_storage()
        return output_id
    
    def submit_for_review(self, output_id: str) -> bool:
        """
        提交審批
        
        Args:
            output_id: 產出 ID
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        if output.status not in [OutputStatus.DRAFT, OutputStatus.REVISION_REQUESTED]:
            return False
        
        output.status = OutputStatus.PENDING_REVIEW
        output.submitted_at = datetime.now()
        
        if output_id not in self.pending_reviews:
            self.pending_reviews.append(output_id)
        
        # 透過表單系統通知負責人
        owner = self.owners.get(output.owner_id)
        if owner and self.form_adapter:
            self.form_adapter.create_ticket(output, owner)
            self.form_adapter.notify_approval(owner.owner_id, output, "review_requested")
        
        self._save_to_storage()
        return True
    
    def approve_output(self, output_id: str, owner_id: str) -> bool:
        """
        批准產出
        
        Args:
            output_id: 產出 ID
            owner_id: 批准者 ID
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        # 驗證 owner_id 匹配
        if output.owner_id != owner_id and output.owner_id != "unassigned":
            # 允許代批准，但記錄實際批准者
            pass
        
        if output.status != OutputStatus.PENDING_REVIEW:
            return False
        
        output.status = OutputStatus.APPROVED
        output.approved_at = datetime.now()
        output.approved_by = owner_id
        
        # 從 pending_reviews 移除
        if output_id in self.pending_reviews:
            self.pending_reviews.remove(output_id)
        
        # 透過表單系統更新狀態
        if self.form_adapter:
            self.form_adapter.notify_approval(owner_id, output, "approved")
        
        self._save_to_storage()
        return True
    
    def request_revision(self, output_id: str, owner_id: str, feedback: str) -> bool:
        """
        要求修改
        
        Args:
            output_id: 產出 ID
            owner_id: 要求者 ID
            feedback: 修訂回饋
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        if output.status != OutputStatus.PENDING_REVIEW:
            return False
        
        output.status = OutputStatus.REVISION_REQUESTED
        output.feedback = feedback
        output.revision_count += 1
        
        # 從 pending_reviews 移除
        if output_id in self.pending_reviews:
            self.pending_reviews.remove(output_id)
        
        self._save_to_storage()
        return True
    
    def complete_output(self, output_id: str) -> bool:
        """
        完成產出（標記為完成）
        
        Args:
            output_id: 產出 ID
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        if output.status != OutputStatus.APPROVED:
            return False
        
        output.status = OutputStatus.COMPLETED
        self._save_to_storage()
        return True
    
    def escalate_output(self, output_id: str, reason: str, level: EscalationLevel = None) -> bool:
        """
        升級產出
        
        Args:
            output_id: 產出 ID
            reason: 升級原因
            level: 升級層級（可選，預設為 OWNER）
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        output.status = OutputStatus.ESCALATED
        output.escalation_reason = reason
        output.escalation_level = level or EscalationLevel.OWNER
        output.escalated_at = datetime.now()
        
        # 從 pending_reviews 移除
        if output_id in self.pending_reviews:
            self.pending_reviews.remove(output_id)
        
        self._save_to_storage()
        return True
    
    def update_output_content(self, output_id: str, content: Any) -> bool:
        """
        更新產出內容
        
        Args:
            output_id: 產出 ID
            content: 新內容
            
        Returns:
            bool: 是否成功
        """
        output = self.outputs.get(output_id)
        if not output:
            return False
        
        output.content = content
        self._save_to_storage()
        return True
    
    # === 查詢 ===
    
    def get_output(self, output_id: str) -> Optional[Output]:
        """取得產出"""
        return self.outputs.get(output_id)
    
    def get_outputs_by_agent(self, agent_id: str) -> List[Output]:
        """取得某 Agent 的所有產出"""
        return [o for o in self.outputs.values() if o.agent_id == agent_id]
    
    def get_outputs_by_owner(self, owner_id: str) -> List[Output]:
        """取得某負責人的所有產出"""
        return [o for o in self.outputs.values() if o.owner_id == owner_id]
    
    def get_pending_reviews(self, owner_id: str = None) -> List[Output]:
        """
        取得待審批列表
        
        Args:
            owner_id: 可選，過濾特定負責人
            
        Returns:
            List[Output]: 待審批產出列表
        """
        if owner_id:
            return [
                o for o in self.outputs.values()
                if o.status == OutputStatus.PENDING_REVIEW and o.owner_id == owner_id
            ]
        return [
            o for o in self.outputs.values()
            if o.status == OutputStatus.PENDING_REVIEW
        ]
    
    def get_outputs_by_status(self, status: OutputStatus) -> List[Output]:
        """取得特定狀態的所有產出"""
        return [o for o in self.outputs.values() if o.status == status]
    
    def get_statistics(self) -> dict:
        """取得統計"""
        total = len(self.outputs)
        by_status = {}
        for status in OutputStatus:
            by_status[status.value] = sum(
                1 for o in self.outputs.values() if o.status == status
            )
        
        total_owners = len(self.owners)
        total_agents = len(self.agent_to_owner)
        
        # 計算平均修訂次數
        outputs_with_revisions = [o for o in self.outputs.values() if o.revision_count > 0]
        avg_revision = (
            sum(o.revision_count for o in outputs_with_revisions) / len(outputs_with_revisions)
            if outputs_with_revisions else 0
        )
        
        return {
            "total_outputs": total,
            "by_status": by_status,
            "total_owners": total_owners,
            "total_agents_assigned": total_agents,
            "pending_reviews": len(self.pending_reviews),
            "avg_revision_count": round(avg_revision, 2),
        }
    
    def generate_report(self) -> str:
        """生成 HITL 報告"""
        stats = self.get_statistics()
        
        report = f"""
# 🔄 HITL (Human-in-the-Loop) 報告

## 統計概覽

| 指標 | 數值 |
|------|------|
| 總產出數 | {stats['total_outputs']} |
| 待審批 | {stats['pending_reviews']} |
| 已批准 | {stats['by_status'].get('approved', 0)} |
| 需要修訂 | {stats['by_status'].get('revision_requested', 0)} |
| 已完成 | {stats['by_status'].get('completed', 0)} |
| 已升級 | {stats['by_status'].get('escalated', 0)} |
| 負責人數 | {stats['total_owners']} |
| 已指派 Agent | {stats['total_agents_assigned']} |
| 平均修訂次數 | {stats['avg_revision_count']} |

---

## 負責人列表

| ID | 名稱 | Email | 角色 | Agent 數 |
|----|------|-------|------|----------|
"""
        
        for owner in self.owners.values():
            report += f"| {owner.owner_id} | {owner.name} | {owner.email} | {owner.role} | {len(owner.agents)} |\n"
        
        # 待審批列表
        pending = self.get_pending_reviews()
        if pending:
            report += f"""

## 待審批產出 ({len(pending)})

| ID | Agent | 任務 | 創建時間 | 負責人 |
|----|-------|------|----------|--------|
"""
            for o in pending:
                owner = self.owners.get(o.owner_id, {})
                owner_name = owner.name if owner else o.owner_id
                report += f"| {o.id} | {o.agent_id} | {o.task_id} | {o.created_at.strftime('%Y-%m-%d %H:%M')} | {owner_name} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # 演示用法
    controller = HITLController()
    
    # 註冊負責人
    owner = AgentOwner(
        owner_id="owner-1",
        name="John",
        email="john@example.com",
        role="Manager"
    )
    controller.register_owner(owner)
    
    print("=== Owner Registered ===")
    print(f"Owner: {owner.name} ({owner.email})")
    
    # 指派 Agent 給負責人
    controller.assign_agent_to_owner("agent-dev-1", "owner-1")
    controller.assign_agent_to_owner("agent-dev-2", "owner-1")
    
    print("\n=== Agent Assignment ===")
    print(f"agent-dev-1 -> owner-1: {controller.get_owner_for_agent('agent-dev-1').name}")
    print(f"agent-dev-2 -> owner-1: {controller.get_owner_for_agent('agent-dev-2').name}")
    
    # 建立產出
    output_id = controller.create_output(
        "agent-dev-1",
        "task-feature-login",
        {"result": "Login feature implemented"}
    )
    print(f"\n=== Output Created ===")
    print(f"Output ID: {output_id}")
    
    # 提交審批
    controller.submit_for_review(output_id)
    print(f"Status: {controller.get_output(output_id).status.value}")
    
    # 批准
    controller.approve_output(output_id, "owner-1")
    print(f"Approved Status: {controller.get_output(output_id).status.value}")
    
    # 統計
    print("\n=== Statistics ===")
    stats = controller.get_statistics()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    # 報告
    print("\n=== Report ===")
    print(controller.generate_report())
