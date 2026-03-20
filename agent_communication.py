#!/usr/bin/env python3
"""
Agent Communication - Agent 溝通與轉交機制

支援 Agent 之間的訊息傳遞、轉交、衝突處理
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import uuid


class MessageType(Enum):
    """訊息類型"""
    REQUEST = "request"           # 請求
    RESPONSE = "response"       # 回應
    HANDOFF = "handoff"          # 轉交
    ESCALATION = "escalation"    # 升級
    BROADCAST = "broadcast"      # 廣播
    CONSENSUS = "consensus"      # 共識請求


class HandoffTrigger(Enum):
    """轉交觸發條件"""
    TASK_COMPLETE = "task_complete"
    NEEDS_REVIEW = "needs_review"
    NEEDS_TEST = "needs_test"
    NEEDS_ARCHITECT = "needs_architect"
    ESCALATE = "escalate"
    TIMEOUT = "timeout"
    ERROR = "error"
    MANUAL = "manual"


@dataclass
class AgentMessage:
    """Agent 訊息"""
    id: str
    from_agent: str
    to_agent: str  # 或 "broadcast"
    content: str
    type: MessageType
    
    # 上下文
    task_id: str = None
    context: Dict = field(default_factory=dict)
    
    # 附件
    attachments: List[Dict] = field(default_factory=list)
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    
    # 狀態
    read: bool = False
    replied: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "type": self.type.value,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
        }


@dataclass
class HandoffRule:
    """轉交規則"""
    id: str
    from_role: str
    to_role: str
    trigger: HandoffTrigger
    
    # 條件
    condition: Callable = None  # 可選的條件函數
    
    # 需要審批
    required_approval: bool = False
    approver_role: str = None
    
    # 描述
    description: str = ""
    
    # 優先級
    priority: int = 0


@dataclass
class Conversation:
    """對話 thread"""
    id: str
    participants: List[str] = field(default_factory=list)
    messages: List[AgentMessage] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, message: AgentMessage):
        self.messages.append(message)
        self.last_activity = datetime.now()


@dataclass
class ConflictRecord:
    """衝突記錄"""
    id: str
    task_id: str
    agents: List[str]
    type: str  # "decision", "resource", "priority"
    description: str
    status: str = "open"  # open, resolved, escalated
    resolution: str = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: datetime = None


class AgentCommunication:
    """Agent 溝通管理器"""
    
    def __init__(self):
        # 訊息佇列
        self.inbox: Dict[str, List[AgentMessage]] = defaultdict(list)  # agent_id -> messages
        self.outbox: Dict[str, List[AgentMessage]] = defaultdict(list)
        self.all_messages: List[AgentMessage] = []
        
        # 轉交規則
        self.handoff_rules: List[HandoffRule] = []
        
        # 對話 threads
        self.conversations: Dict[str, Conversation] = {}
        
        # 衝突記錄
        self.conflicts: Dict[str, ConflictRecord] = {}
        
        # 監聽器
        self.listeners: Dict[str, Callable] = {}
        
        # 訊息歷史
        self.message_history_limit = 1000
        
        # 載入預設規則
        self._load_default_rules()
    
    def _load_default_rules(self):
        """載入預設轉交規則"""
        # 開發者完成 -> 測試
        self.add_handoff_rule(
            from_role="developer",
            to_role="tester",
            trigger=HandoffTrigger.TASK_COMPLETE,
            description="開發完成，轉交測試"
        )
        
        # 測試完成 -> 評審
        self.add_handoff_rule(
            from_role="tester",
            to_role="reviewer",
            trigger=HandoffTrigger.TASK_COMPLETE,
            description="測試完成，轉交評審"
        )
        
        # 需要架構决策 -> 架構師
        self.add_handoff_rule(
            from_role="developer",
            to_role="architect",
            trigger=HandoffTrigger.NEEDS_ARCHITECT,
            description="需要架構决策"
        )
        
        # 評審不通過 -> 回開發者
        self.add_handoff_rule(
            from_role="reviewer",
            to_role="developer",
            trigger=HandoffTrigger.NEEDS_REVIEW,
            description="評審不通過"
        )
        
        # 任何錯誤 -> PM 升級
        self.add_handoff_rule(
            from_role="developer",
            to_role="pm",
            trigger=HandoffTrigger.ERROR,
            required_approval=True,
            description="錯誤需要 PM 介入"
        )
    
    def add_handoff_rule(self, from_role: str, to_role: str,
                        trigger: HandoffTrigger,
                        condition: Callable = None,
                        required_approval: bool = False,
                        approver_role: str = None,
                        description: str = "") -> str:
        """新增轉交規則"""
        rule_id = f"rule-{len(self.handoff_rules) + 1}"
        
        rule = HandoffRule(
            id=rule_id,
            from_role=from_role,
            to_role=to_role,
            trigger=trigger,
            condition=condition,
            required_approval=required_approval,
            approver_role=approver_role,
            description=description,
        )
        
        self.handoff_rules.append(rule)
        return rule_id
    
    def send_message(self, from_agent: str, to_agent: str,
                    content: str, message_type: MessageType = MessageType.REQUEST,
                    task_id: str = None, context: Dict = None,
                    attachments: List[Dict] = None) -> str:
        """發送訊息"""
        message_id = f"msg-{uuid.uuid4().hex[:12]}"
        
        message = AgentMessage(
            id=message_id,
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            type=message_type,
            task_id=task_id,
            context=context or {},
            attachments=attachments or [],
        )
        
        # 加入收件匣
        self.inbox[to_agent].append(message)
        
        # 加入發件匣
        self.outbox[from_agent].append(message)
        
        # 加入歷史
        self.all_messages.append(message)
        
        # 觸發監聽器
        self._notify_listeners(to_agent, message)
        
        # 限制歷史大小
        if len(self.all_messages) > self.message_history_limit:
            self.all_messages = self.all_messages[-self.message_history_limit:]
        
        return message_id
    
    def broadcast(self, from_agent: str, content: str,
                 message_type: MessageType = MessageType.BROADCAST,
                 task_id: str = None, context: Dict = None) -> List[str]:
        """廣播訊息"""
        message_ids = []
        
        for agent_id in self.inbox.keys():
            if agent_id != from_agent:
                msg_id = self.send_message(
                    from_agent=from_agent,
                    to_agent=agent_id,
                    content=content,
                    message_type=message_type,
                    task_id=task_id,
                    context=context
                )
                message_ids.append(msg_id)
        
        return message_ids
    
    def reply_to(self, from_agent: str, original_message_id: str,
                content: str, context: Dict = None) -> str:
        """回覆訊息"""
        original = self.get_message(original_message_id)
        if not original:
            raise ValueError(f"Message {original_message_id} not found")
        
        message_id = self.send_message(
            from_agent=from_agent,
            to_agent=original.from_agent,
            content=content,
            message_type=MessageType.RESPONSE,
            task_id=original.task_id,
            context=context
        )
        
        # 標記原訊息為已回覆
        original.replied = True
        
        return message_id
    
    def get_messages(self, agent_id: str, unread_only: bool = False) -> List[Dict]:
        """取得 Agent 的訊息"""
        messages = self.inbox.get(agent_id, [])
        
        if unread_only:
            messages = [m for m in messages if not m.read]
        
        return [m.to_dict() for m in messages]
    
    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """取得特定訊息"""
        for msg in self.all_messages:
            if msg.id == message_id:
                return msg
        return None
    
    def mark_read(self, agent_id: str, message_id: str):
        """標記已讀"""
        for msg in self.inbox.get(agent_id, []):
            if msg.id == message_id:
                msg.read = True
                break
    
    def trigger_handoff(self, from_agent: str, from_role: str,
                       trigger: HandoffTrigger, task_id: str = None,
                       context: Dict = None) -> Optional[str]:
        """觸發轉交"""
        # 找符合的規則
        matching_rules = [
            r for r in self.handoff_rules
            if r.from_role == from_role and r.trigger == trigger
        ]
        
        if not matching_rules:
            return None
        
        rule = matching_rules[0]  # 選擇第一個
        
        # 檢查條件
        if rule.condition and not rule.condition(context or {}):
            return None
        
        # 如果需要審批
        if rule.required_approval:
            # 發送審批請求
            approver_msg = self.send_message(
                from_agent=from_agent,
                to_agent=rule.approver_role or "pm",
                content=f"轉交請求需要審批：{rule.description}",
                message_type=MessageType.CONSENSUS,
                task_id=task_id,
                context={"rule_id": rule.id, "action": "handoff"}
            )
            return approver_msg
        
        # 直接轉交
        return self._execute_handoff(from_agent, rule.to_role, task_id, context)
    
    def _execute_handoff(self, from_agent: str, to_role: str,
                        task_id: str = None, context: Dict = None) -> str:
        """執行轉交"""
        return self.send_message(
            from_agent=from_agent,
            to_agent=f"role:{to_role}",  # 標記為角色
            content=f"任務轉交給 {to_role}",
            message_type=MessageType.HANDOFF,
            task_id=task_id,
            context=context
        )
    
    def create_conversation(self, participants: List[str],
                          context: Dict = None) -> str:
        """建立對話 thread"""
        conv_id = f"conv-{uuid.uuid4().hex[:12]}"
        
        conversation = Conversation(
            id=conv_id,
            participants=participants,
            context=context or {},
        )
        
        self.conversations[conv_id] = conversation
        return conv_id
    
    def add_to_conversation(self, conv_id: str, agent_id: str):
        """加入對話"""
        conv = self.conversations.get(conv_id)
        if conv and agent_id not in conv.participants:
            conv.participants.append(agent_id)
    
    def send_in_conversation(self, conv_id: str, from_agent: str,
                           content: str, message_type: MessageType = MessageType.REQUEST) -> str:
        """在對話中發送訊息"""
        conv = self.conversations.get(conv_id)
        if not conv:
            raise ValueError(f"Conversation {conv_id} not found")
        
        # 發送給所有參與者
        message_ids = []
        for participant in conv.participants:
            if participant != from_agent:
                msg_id = self.send_message(
                    from_agent=from_agent,
                    to_agent=participant,
                    content=content,
                    message_type=message_type,
                    context={"conversation_id": conv_id}
                )
                message_ids.append(msg_id)
        
        # 加入 thread
        last_msg = self.all_messages[-1] if self.all_messages else None
        if last_msg:
            conv.add_message(last_msg)
        
        return message_ids[0] if message_ids else None
    
    def report_conflict(self, task_id: str, agents: List[str],
                       conflict_type: str, description: str) -> str:
        """報告衝突"""
        conflict_id = f"conflict-{uuid.uuid4().hex[:12]}"
        
        conflict = ConflictRecord(
            id=conflict_id,
            task_id=task_id,
            agents=agents,
            type=conflict_type,
            description=description,
        )
        
        self.conflicts[conflict_id] = conflict
        
        # 通知 PM
        self.send_message(
            from_agent="system",
            to_agent="pm",
            content=f"衝突報告：{description}",
            message_type=MessageType.ESCALATION,
            task_id=task_id,
            context={"conflict_id": conflict_id}
        )
        
        return conflict_id
    
    def resolve_conflict(self, conflict_id: str, resolution: str):
        """解決衝突"""
        conflict = self.conflicts.get(conflict_id)
        if not conflict:
            return
        
        conflict.status = "resolved"
        conflict.resolution = resolution
        conflict.resolved_at = datetime.now()
    
    def register_listener(self, agent_id: str, callback: Callable):
        """註冊監聽器"""
        self.listeners[agent_id] = callback
    
    def _notify_listeners(self, agent_id: str, message: AgentMessage):
        """通知監聽器"""
        if agent_id in self.listeners:
            try:
                self.listeners[agent_id](message)
            except Exception:
                pass
    
    def get_pending_approvals(self, agent_id: str) -> List[Dict]:
        """取得待審批"""
        pending = []
        
        for msg in self.inbox.get(agent_id, []):
            if msg.type == MessageType.CONSENSUS and not msg.read:
                pending.append({
                    "message_id": msg.id,
                    "from": msg.from_agent,
                    "content": msg.content,
                    "task_id": msg.task_id,
                    "context": msg.context,
                })
        
        return pending
    
    def approve(self, agent_id: str, message_id: str, approved: bool = True) -> str:
        """審批"""
        message = self.get_message(message_id)
        if not message:
            return None
        
        context = message.context or {}
        rule_id = context.get("rule_id")
        
        if approved and rule_id:
            # 執行審批後的轉交
            for rule in self.handoff_rules:
                if rule.id == rule_id:
                    return self._execute_handoff(
                        message.from_agent,
                        rule.to_role,
                        message.task_id,
                        message.context
                    )
        
        # 拒絕
        self.send_message(
            from_agent=agent_id,
            to_agent=message.from_agent,
            content="請求被拒絕" if not approved else "審批完成",
            message_type=MessageType.RESPONSE,
            task_id=message.task_id
        )
        
        self.mark_read(agent_id, message_id)
        return None
    
    def get_statistics(self) -> Dict:
        """取得統計"""
        total_messages = len(self.all_messages)
        unread = sum(1 for msgs in self.inbox.values() for m in msgs if not m.read)
        
        by_type = {}
        for msg in self.all_messages:
            type_key = msg.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        
        open_conflicts = sum(1 for c in self.conflicts.values() if c.status == "open")
        
        return {
            "total_messages": total_messages,
            "unread_messages": unread,
            "by_type": by_type,
            "open_conflicts": open_conflicts,
            "handoff_rules": len(self.handoff_rules),
            "active_conversations": len(self.conversations),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        stats = self.get_statistics()
        
        report = f"""
# 💬 Agent 溝通報告

## 統計

| 指標 | 數值 |
|------|------|
| 總訊息數 | {stats['total_messages']} |
| 未讀訊息 | {stats['unread_messages']} |
| 開放衝突 | {stats['open_conflicts']} |
| 轉交規則 | {stats['handoff_rules']} |
| 對話 threads | {stats['active_conversations']} |

---

## 訊息類型分佈

| 類型 | 數量 |
|------|------|
"""
        
        for msg_type, count in stats['by_type'].items():
            report += f"| {msg_type} | {count} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    comm = AgentCommunication()
    
    print("=== Sending Messages ===")
    
    # 開發者 -> 測試
    msg1 = comm.send_message(
        from_agent="dev-1",
        to_agent="tester-1",
        content="登入功能開發完成，請測試",
        message_type=MessageType.REQUEST,
        task_id="task-123"
    )
    print(f"Sent: {msg1}")
    
    # 測試 -> 開發者 (回覆)
    msg2 = comm.reply_to(
        from_agent="tester-1",
        original_message_id=msg1,
        content="發現 2 個 bug，請修復"
    )
    print(f"Reply: {msg2}")
    
    # 觸發轉交
    print("\n=== Handoff ===")
    handoff_msg = comm.trigger_handoff(
        from_agent="dev-1",
        from_role="developer",
        trigger=HandoffTrigger.TASK_COMPLETE,
        task_id="task-123"
    )
    print(f"Handoff triggered: {handoff_msg}")
    
    # 衝突報告
    print("\n=== Conflict ===")
    conflict_id = comm.report_conflict(
        task_id="task-456",
        agents=["dev-1", "dev-2"],
        conflict_type="resource",
        description="兩個開發者同時想要修改同一個檔案"
    )
    print(f"Conflict reported: {conflict_id}")
    
    # 統計
    print("\n=== Statistics ===")
    stats = comm.get_statistics()
    print(f"Total messages: {stats['total_messages']}")
    print(f"Unread: {stats['unread_messages']}")
    
    # tester 的收件匣
    print("\n=== Tester Inbox ===")
    messages = comm.get_messages("tester-1")
    for msg in messages:
        print(f"  {msg['from']}: {msg['content'][:50]}...")
    
    print("\n=== Report ===")
    print(comm.generate_report())
