"""
MAP Protocol - Methodology Agent Protocol

Standardized inter-agent communication protocol.
"""

import uuid
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
import threading


class MessageType(Enum):
    TASK_START = "task_start"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    REQUEST_HELP = "request_help"
    PROVIDE_HELP = "provide_help"
    HANDOFF = "handoff"
    HEARTBEAT = "heartbeat"


class Priority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentInfo:
    """Agent information"""
    agent_id: str
    role: str = ""
    status: str = "online"


@dataclass
class AgentMessage:
    """MAP Protocol message"""
    protocol: str = "map-v1"
    message_id: str = field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    from_agent: str = ""
    from_role: str = ""
    to_agent: str = ""
    to_role: str = ""
    type: MessageType = MessageType.TASK_START
    priority: Priority = Priority.NORMAL
    payload: Dict = field(default_factory=dict)
    correlation_id: str = ""
    reply_to: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "protocol": self.protocol,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "from": {
                "agent_id": self.from_agent,
                "role": self.from_role
            },
            "to": {
                "agent_id": self.to_agent,
                "role": self.to_role
            },
            "type": self.type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentMessage":
        """Create from dictionary"""
        msg = cls()
        msg.protocol = data.get("protocol", "map-v1")
        msg.message_id = data.get("message_id", f"msg_{uuid.uuid4().hex[:12]}")
        msg.timestamp = data.get("timestamp", time.time())
        
        from_info = data.get("from", {})
        msg.from_agent = from_info.get("agent_id", "")
        msg.from_role = from_info.get("role", "")
        
        to_info = data.get("to", {})
        msg.to_agent = to_info.get("agent_id", "")
        msg.to_role = to_info.get("role", "")
        
        msg.type = MessageType(data.get("type", "task_start"))
        msg.priority = Priority(data.get("priority", "normal"))
        msg.payload = data.get("payload", {})
        msg.correlation_id = data.get("correlation_id", "")
        msg.reply_to = data.get("reply_to", "")
        
        return msg


class MessageQueue:
    """Message queue for agents"""
    
    def __init__(self):
        self.queues: Dict[str, Queue] = {}
        self.lock = threading.Lock()
    
    def enqueue(self, agent_id: str, message: AgentMessage):
        """Add message to queue"""
        with self.lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = Queue()
            self.queues[agent_id].put(message)
    
    def dequeue(self, agent_id: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        """Get message from queue"""
        with self.lock:
            if agent_id not in self.queues:
                return None
        
        try:
            return self.queues[agent_id].get(timeout=timeout)
        except Empty:
            return None
    
    def size(self, agent_id: str) -> int:
        """Get queue size"""
        with self.lock:
            if agent_id not in self.queues:
                return 0
            return self.queues[agent_id].qsize()


class MAPProtocol:
    """
    Methodology Agent Protocol implementation.
    
    Usage:
        protocol = MAPProtocol()
        protocol.send(message)
        received = protocol.receive("my_agent")
    """
    
    def __init__(self):
        self.message_queue = MessageQueue()
        self.subscriptions: Dict[MessageType, List[Callable]] = {}
        self.handlers: Dict[str, Callable] = {}
        self.sent_messages: List[AgentMessage] = []
        self.lock = threading.Lock()
    
    def send(self, message: AgentMessage) -> bool:
        """Send message to agent"""
        with self.lock:
            # Validate message
            if not message.to_agent:
                return False
            
            # Enqueue for recipient
            self.message_queue.enqueue(message.to_agent, message)
            
            # Store in sent history
            self.sent_messages.append(message)
            
            # Trigger subscriptions
            self._trigger_subscriptions(message)
            
            return True
    
    def receive(self, agent_id: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        """Receive message for agent"""
        return self.message_queue.dequeue(agent_id, timeout)
    
    def publish(self, message: AgentMessage):
        """Publish to all subscribers"""
        message.to_agent = "*"
        self.send(message)
    
    def subscribe(self, message_type: MessageType, callback: Callable):
        """Subscribe to message type"""
        if message_type not in self.subscriptions:
            self.subscriptions[message_type] = []
        self.subscriptions[message_type].append(callback)
    
    def _trigger_subscriptions(self, message: AgentMessage):
        """Trigger subscribed callbacks"""
        if message.type in self.subscriptions:
            for callback in self.subscriptions[message.type]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def request_response(
        self, 
        message: AgentMessage, 
        timeout: float = 30.0
    ) -> Optional[AgentMessage]:
        """Send request and wait for response"""
        # Set correlation ID
        message.correlation_id = message.message_id
        message.reply_to = message.from_agent
        
        # Send request
        self.send(message)
        
        # Wait for response
        start = time.time()
        while time.time() - start < timeout:
            response = self.receive(message.from_agent, timeout=1.0)
            if response and response.correlation_id == message.message_id:
                return response
        
        return None
    
    def get_queue_size(self, agent_id: str) -> int:
        """Get message queue size"""
        return self.message_queue.size(agent_id)
    
    def get_sent_messages(self, agent_id: str = None) -> List[AgentMessage]:
        """Get sent messages"""
        with self.lock:
            if agent_id:
                return [m for m in self.sent_messages if m.from_agent == agent_id]
            return self.sent_messages.copy()


class ProtocolHandler:
    """
    Protocol handler for processing messages.
    
    Usage:
        handler = ProtocolHandler(agent_id="my_agent")
        handler.start()
    """
    
    def __init__(self, agent_id: str, protocol: MAPProtocol = None):
        self.agent_id = agent_id
        self.protocol = protocol or MAPProtocol()
        self.handlers: Dict[MessageType, Callable] = {}
        self.running = False
        self.thread = None
    
    def on(self, message_type: MessageType):
        """Decorator to register handler"""
        def decorator(func: Callable):
            self.handlers[message_type] = func
            return func
        return decorator
    
    def start(self):
        """Start handling messages"""
        self.running = True
        self.thread = threading.Thread(target=self._process_messages)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop handling messages"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _process_messages(self):
        """Process incoming messages"""
        while self.running:
            message = self.protocol.receive(self.agent_id, timeout=1.0)
            
            if message:
                # Find handler
                handler = self.handlers.get(message.type)
                
                if handler:
                    try:
                        response = handler(message)
                        
                        # Send response if returned
                        if response:
                            response.to_agent = message.from_agent
                            self.protocol.send(response)
                    except Exception as e:
                        print(f"Handler error: {e}")
                        
                        # Send error response
                        error_msg = AgentMessage(
                            from_agent=self.agent_id,
                            to_agent=message.from_agent,
                            type=MessageType.TASK_FAILED,
                            payload={"error": str(e)}
                        )
                        self.protocol.send(error_msg)


class MessageRouter:
    """Route messages between agents"""
    
    def __init__(self):
        self.routes: Dict[str, List[str]] = {}
        self.broadcast_routes: List[str] = []
    
    def add_route(self, from_agent: str, to_agent: str, direct: bool = True):
        """Add route"""
        if direct:
            if from_agent not in self.routes:
                self.routes[from_agent] = []
            self.routes[from_agent].append(to_agent)
    
    def add_broadcast(self, agent_id: str):
        """Add broadcast route"""
        if agent_id not in self.broadcast_routes:
            self.broadcast_routes.append(agent_id)
    
    def route(self, message: AgentMessage) -> List[str]:
        """Get next hop(s) for message"""
        recipients = []
        
        # Direct route
        if message.to_agent in self.routes.get(message.from_agent, []):
            recipients.append(message.to_agent)
        
        # Broadcast routes
        if message.to_agent == "*":
            recipients.extend(self.broadcast_routes)
        
        return recipients


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MAP Protocol CLI")
    parser.add_argument("command", choices=["send", "receive", "queue"])
    parser.add_argument("--from", dest="from_agent")
    parser.add_argument("--to", dest="to_agent")
    parser.add_argument("--type", default="task_start")
    
    args = parser.parse_args()
    
    protocol = MAPProtocol()
    
    if args.command == "send":
        msg = AgentMessage(
            from_agent=args.from_agent or "agent_a",
            to_agent=args.to_agent or "agent_b",
            type=MessageType(args.type)
        )
        protocol.send(msg)
        print(f"Sent: {msg.message_id}")
    
    elif args.command == "receive":
        msg = protocol.receive(args.from_agent or "agent_a", timeout=5.0)
        if msg:
            print(f"Received: {msg.to_dict()}")
    
    elif args.command == "queue":
        size = protocol.get_queue_size(args.from_agent or "agent_a")
        print(f"Queue size: {size}")
