#!/usr/bin/env python3
"""
MessageBus - 事件驅動的消息匯流排

發布/訂閱模式的事件系統
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading
import asyncio


class MessagePriority(Enum):
    """訊息優先級"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MessageType(Enum):
    """訊息類型"""
    EVENT = "event"           # 事件
    COMMAND = "command"       # 命令
    QUERY = "query"           # 查詢
    RESPONSE = "response"     # 回應
    ERROR = "error"           # 錯誤


@dataclass
class Envelope:
    """訊息信封"""
    id: str
    topic: str
    type: MessageType
    priority: MessagePriority
    
    # 內容
    payload: Any
    headers: Dict = field(default_factory=dict)
    
    # 路由
    source: str = None
    destination: str = None
    
    # 追蹤
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = None
    expires_at: datetime = None
    
    # 狀態
    delivered: bool = False
    processed: bool = False
    error: str = None


@dataclass
class Subscription:
    """訂閱"""
    id: str
    topic: str
    callback: Callable
    filter_func: Callable = None
    priority: MessagePriority = MessagePriority.NORMAL
    
    # 配置
    ephemeral: bool = False  # 臨時訂閱
    persistent: bool = False  # 持久訂閱
    
    created_at: datetime = field(default_factory=datetime.now)


class MessageBus:
    """事件驅動消息匯流排"""
    
    def __init__(self, max_queue_size: int = 10000):
        # 主題到訂閱者的映射
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        
        # 全域訂閱（所有訊息）
        self.global_subscriptions: List[Subscription] = []
        
        # 訊息佇列
        self.queue: List[Envelope] = []
        self.max_queue_size = max_queue_size
        
        # 已處理的訊息（用於追蹤）
        self.processed: Dict[str, Envelope] = {}
        
        # 死信佇列
        self.dead_letter_queue: List[Envelope] = []
        
        # 訂閱者鎖
        self.lock = threading.RLock()
        
        # 回呼追蹤
        self.subscription_counter = 0
        
        # 統計
        self.stats = {
            "messages_sent": 0,
            "messages_processed": 0,
            "messages_failed": 0,
            "subscriptions_created": 0,
        }
    
    def publish(self, topic: str, payload: Any,
               message_type: MessageType = MessageType.EVENT,
               priority: MessagePriority = MessagePriority.NORMAL,
               headers: Dict = None,
               source: str = None,
               correlation_id: str = None,
               ttl_seconds: int = None) -> str:
        """發布訊息"""
        message_id = str(uuid.uuid4())
        
        envelope = Envelope(
            id=message_id,
            topic=topic,
            type=message_type,
            priority=priority,
            payload=payload,
            headers=headers or {},
            source=source,
            correlation_id=correlation_id,
        )
        
        # 設定過期時間
        if ttl_seconds:
            envelope.expires_at = datetime.now() + __import__('datetime').timedelta(seconds=ttl_seconds)
        
        # 加入佇列
        with self.lock:
            self.queue.append(envelope)
            self.stats["messages_sent"] += 1
            
            # 限制佇列大小
            if len(self.queue) > self.max_queue_size:
                self.queue.pop(0)  # 移除最舊的
        
        # 如果是同步模式，立即處理
        self._dispatch(envelope)
        
        return message_id
    
    def subscribe(self, topic: str, callback: Callable,
                 filter_func: Callable = None,
                 priority: MessagePriority = MessagePriority.NORMAL,
                 ephemeral: bool = False) -> str:
        """訂閱主題"""
        with self.lock:
            self.subscription_counter += 1
            subscription_id = f"sub-{self.subscription_counter}"
            
            subscription = Subscription(
                id=subscription_id,
                topic=topic,
                callback=callback,
                filter_func=filter_func,
                priority=priority,
                ephemeral=ephemeral,
            )
            
            self.subscriptions[topic].append(subscription)
            self.subscriptions[topic].sort(key=lambda x: -x.priority.value)
            
            self.stats["subscriptions_created"] += 1
        
        return subscription_id
    
    def subscribe_all(self, callback: Callable,
                     priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """訂閱所有訊息"""
        with self.lock:
            self.subscription_counter += 1
            subscription_id = f"sub-global-{self.subscription_counter}"
            
            subscription = Subscription(
                id=subscription_id,
                topic="*",
                callback=callback,
                priority=priority,
                ephemeral=True,
            )
            
            self.global_subscriptions.append(subscription)
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消訂閱"""
        with self.lock:
            # 在主題訂閱中查找
            for topic, subs in self.subscriptions.items():
                for sub in subs:
                    if sub.id == subscription_id:
                        subs.remove(sub)
                        return True
            
            # 在全域訂閱中查找
            for sub in self.global_subscriptions:
                if sub.id == subscription_id:
                    self.global_subscriptions.remove(sub)
                    return True
        
        return False
    
    def send_command(self, destination: str, command: str,
                    payload: Any = None,
                    timeout_seconds: int = 30) -> str:
        """發送命令（期待回應）"""
        correlation_id = str(uuid.uuid4())
        
        self.publish(
            topic=f"command.{destination}",
            payload={
                "command": command,
                "data": payload,
            },
            message_type=MessageType.COMMAND,
            priority=MessagePriority.HIGH,
            correlation_id=correlation_id,
        )
        
        return correlation_id
    
    def query(self, topic: str, payload: Any = None,
             timeout_seconds: int = 5) -> Optional[Any]:
        """發送查詢（期待回應）"""
        # 實現同步查詢需要更複雜的實現
        # 這裡簡化為發布查詢事件
        correlation_id = str(uuid.uuid4())
        
        self.publish(
            topic=f"query.{topic}",
            payload=payload,
            message_type=MessageType.QUERY,
            priority=MessagePriority.NORMAL,
            correlation_id=correlation_id,
        )
        
        return None  # 實際需要等待回應
    
    def _dispatch(self, envelope: Envelope):
        """派送訊息"""
        # 檢查是否過期
        if envelope.expires_at and datetime.now() > envelope.expires_at:
            self._dead_letter(envelope, "Message expired")
            return
        
        # 取得訂閱者
        with self.lock:
            topic_subs = self.subscriptions.get(envelope.topic, []).copy()
            global_subs = self.global_subscriptions.copy()
        
        delivered = False
        errors = []
        
        # 派送給主題訂閱者
        for sub in topic_subs:
            if sub.filter_func and not sub.filter_func(envelope):
                continue
            
            try:
                result = sub.callback(envelope)
                envelope.delivered = True
                delivered = True
                
                # 處理回應
                if result is not None and envelope.correlation_id:
                    self._handle_response(envelope.correlation_id, result)
                
            except Exception as e:
                errors.append(str(e))
                envelope.error = "; ".join(errors)
        
        # 派送給全域訂閱者
        for sub in global_subs:
            if sub.filter_func and not sub.filter_func(envelope):
                continue
            
            try:
                sub.callback(envelope)
                envelope.delivered = True
                delivered = True
            except Exception as e:
                errors.append(str(e))
                envelope.error = "; ".join(errors)
        
        # 標記為已處理
        envelope.processed = True
        
        # 更新統計
        if errors:
            self.stats["messages_failed"] += 1
        else:
            self.stats["messages_processed"] += 1
        
        # 如果派送失敗，加入死信佇列
        if not delivered and not topic_subs and not global_subs:
            pass  # 沒有訂閱者也視為成功
    
    def _handle_response(self, correlation_id: str, response: Any):
        """處理回應"""
        # 在實際實現中，需要維護一個等待回應的地圖
        pass
    
    def _dead_letter(self, envelope: Envelope, reason: str):
        """加入死信佇列"""
        envelope.error = reason
        self.dead_letter_queue.append(envelope)
        
        # 限制大小
        if len(self.dead_letter_queue) > 1000:
            self.dead_letter_queue.pop(0)
    
    def get_messages(self, topic: str = None, limit: int = 100) -> List[Dict]:
        """取得訊息歷史"""
        messages = [
            {
                "id": m.id,
                "topic": m.topic,
                "type": m.type.value,
                "priority": m.priority.value,
                "source": m.source,
                "timestamp": m.timestamp.isoformat(),
                "delivered": m.delivered,
                "processed": m.processed,
                "error": m.error,
            }
            for m in self.queue
            if topic is None or m.topic == topic
        ]
        
        return messages[-limit:]
    
    def get_queue_status(self) -> Dict:
        """取得佇列狀態"""
        return {
            "queue_size": len(self.queue),
            "max_queue_size": self.max_queue_size,
            "subscriptions_count": sum(len(subs) for subs in self.subscriptions.values()),
            "global_subscriptions_count": len(self.global_subscriptions),
            "dead_letter_queue_size": len(self.dead_letter_queue),
            "stats": self.stats,
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        status = self.get_queue_status()
        
        report = f"""
# 📬 MessageBus 報告

## 佇列狀態

| 指標 | 數值 |
|------|------|
| 佇列大小 | {status['queue_size']} |
| 最大佇列 | {status['max_queue_size']} |
| 主題訂閱數 | {status['subscriptions_count']} |
| 全域訂閱數 | {status['global_subscriptions_count']} |
| 死信佇列 | {status['dead_letter_queue_size']} |

---

## 統計

| 指標 | 數值 |
|------|------|
| 發送訊息 | {status['stats']['messages_sent']} |
| 處理成功 | {status['stats']['messages_processed']} |
| 處理失敗 | {status['stats']['messages_failed']} |
| 新建訂閱 | {status['stats']['subscriptions_created']} |

---

## 主題訂閱

"""
        
        for topic, subs in sorted(self.subscriptions.items()):
            report += f"| {topic} | {len(subs)} 個訂閱 |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    bus = MessageBus()
    
    print("=== Subscribing to Topics ===")
    
    # 訂閱架構師主題
    arch_sub_id = bus.subscribe(
        "architect",
        lambda msg: print(f"📋 Architect received: {msg.payload}")
    )
    
    # 訂閱所有錯誤
    error_sub_id = bus.subscribe_all(
        lambda msg: print(f"🔴 Error handler: {msg.topic} -> {msg.payload}") if msg.type.value == "error" else None,
    )
    
    # 訂閱帶過濾器
    critical_sub_id = bus.subscribe(
        "tasks",
        lambda msg: print(f"🔴 Critical task: {msg.payload}"),
        filter_func=lambda m: m.priority.value >= 2
    )
    
    print(f"Subscribed: arch_sub, error_sub, critical_sub")
    
    # 發布訊息
    print("\n=== Publishing Messages ===")
    
    bus.publish(
        topic="architect",
        payload={"action": "design_review", "project": "AI System"},
        source="pm"
    )
    
    bus.publish(
        topic="tasks",
        payload={"task": "deploy", "priority": "high"},
        priority=MessagePriority.HIGH,
        source="scheduler"
    )
    
    bus.publish(
        topic="tasks",
        payload={"task": "backup", "priority": "low"},
        priority=MessagePriority.LOW,
        source="scheduler"
    )
    
    bus.publish(
        topic="errors",
        payload={"error": "timeout", "service": "api"},
        message_type=MessageType.ERROR,
        source="system"
    )
    
    # 命令
    print("\n=== Sending Commands ===")
    
    correlation_id = bus.send_command(
        destination="dev-1",
        command="execute_task",
        payload={"task_id": "task-123"}
    )
    print(f"Command sent with correlation_id: {correlation_id}")
    
    # 佇列狀態
    print("\n=== Queue Status ===")
    status = bus.get_queue_status()
    print(f"Queue size: {status['queue_size']}")
    print(f"Messages sent: {status['stats']['messages_sent']}")
    print(f"Processed: {status['stats']['messages_processed']}")
    
    # 報告
    print("\n=== Report ===")
    print(bus.generate_report())
