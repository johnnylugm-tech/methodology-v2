#!/usr/bin/env python3
"""
P2P Orchestrator - 點對點代理協調器

讓主代理可以平等協作的 P2P 架構，每個代理都是對等節點，
可以直接通信、廣播訊息、請求回應。

整合：
- message_bus.py（底層訊息傳遞）
- agent_memory（每個 peer 的獨立記憶）
- agent_spawner（Sub Agent 能力）
"""

import json
import uuid
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

# Import existing modules
try:
    from message_bus import MessageBus, Envelope, MessageType, MessagePriority
    from agent_memory.agent_memory import AgentMemory, ShortTermMemory, LongTermMemory, MemoryType
    from agent_spawner import AgentPersona, AgentState, SpawnPolicy
    _INTEGRATION_OK = True
except ImportError as e:
    _INTEGRATION_OK = False
    _integration_error = str(e)


# ============================================================================
# 錯誤類型
# ============================================================================

class P2PError(Enum):
    """P2P 錯誤類型"""
    PEER_NOT_FOUND = "peer_not_found"
    PEER_OFFLINE = "peer_offline"
    MESSAGE_TIMEOUT = "message_timeout"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MEMORY_ERROR = "memory_error"
    REGISTRATION_FAILED = "registration_failed"


# ============================================================================
# PeerAgent - 對等代理
# ============================================================================

@dataclass
class PeerAgent:
    """
    對等代理 - 獨立身份、記憶、工作空間
    
    每個 PeerAgent 是一個完整的自治代理實例，
    擁有自己的人格、記憶、工具和通訊能力。
    """
    agent_id: str                                    # 唯一標識
    name: str                                        # 顯示名稱
    persona: Any = None                              # AgentPersona（可選）
    
    # 能力
    capabilities: List[str] = field(default_factory=list)  # 能力列表
    tools: List[str] = field(default_factory=list)        # 可用工具
    
    # 狀態
    state: str = "idle"                              # idle/running/busy/offline
    last_seen: datetime = field(default_factory=datetime.now)
    
    # 記憶（每個 peer 獨立）
    memory: Any = None                               # AgentMemory 實例
    
    # 工作空間
    workspace: Dict[str, Any] = field(default_factory=dict)
    
    # 配置
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 連接資訊
    connected_at: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    
    def is_online(self) -> bool:
        """檢查是否在線（5分鐘內有活動）"""
        return (datetime.now() - self.last_seen).total_seconds() < 300
    
    def touch(self):
        """更新最後活動時間"""
        self.last_seen = datetime.now()
    
    def to_dict(self) -> Dict:
        """序列化為字典"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "state": self.state,
            "last_seen": self.last_seen.isoformat(),
            "connected_at": self.connected_at.isoformat(),
            "message_count": self.message_count,
            "metadata": self.metadata,
        }


# ============================================================================
# 通訊協定
# ============================================================================

@dataclass
class P2PMessage:
    """P2P 訊息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_peer: str = None
    to_peer: str = None                              # None = 廣播
    payload: Any = None
    message_type: str = "message"                    # message/request/response/error/broadcast
    correlation_id: str = None                       # 用於請求-回應配對
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: datetime = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    def reply(self, payload: Any) -> "P2PMessage":
        """創建回應訊息"""
        return P2PMessage(
            from_peer=self.to_peer,
            to_peer=self.from_peer,
            payload=payload,
            message_type="response",
            correlation_id=self.id,
        )
    
    def is_request(self) -> bool:
        return self.message_type == "request"
    
    def is_response(self) -> bool:
        return self.message_type == "response"
    
    def is_broadcast(self) -> bool:
        return self.to_peer is None


@dataclass 
class PendingRequest:
    """待處理的請求"""
    request: P2PMessage
    future: asyncio.Future
    created_at: datetime = field(default_factory=datetime.now)
    timeout: float = 30.0
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.created_at).total_seconds() > self.timeout


# ============================================================================
# P2POrchestrator - 點對點協調器
# ============================================================================

class P2POrchestrator:
    """
    P2P 代理協調器
    
    特性：
    - 去中心化：每個代理都是對等節點
    - 直接通訊：代理之間可以直接交換訊息
    - 廣播支援：一個代理可以向所有代理廣播
    - 請求-回應：支援帶超時的請求-回應模式
    - 記憶隔離：每個代理有獨立的記憶空間
    - 動態發現：支援動態註冊和註銷代理
    
    使用範例：
    ```python
    orchestrator = P2POrchestrator()
    
    # 註冊代理
    orchestrator.register_peer("agent-1", {
        "name": "Researcher",
        "capabilities": ["web_search", "data_analysis"]
    })
    
    # 發送訊息
    orchestrator.send_to_peer("agent-1", "agent-2", {"task": "research"})
    
    # 請求回應（異步）
    response = await orchestrator.request_response(
        "agent-1", 
        {"query": "最新AI趨勢"}
    )
    ```
    """
    
    def __init__(
        self,
        message_bus: Optional[Any] = None,
        enable_memory: bool = True,
        enable_spawner: bool = True,
        default_timeout: float = 30.0,
        max_peers: int = 100,
    ):
        self.message_bus = message_bus
        self.enable_memory = enable_memory
        self.enable_spawner = enable_spawner
        self.default_timeout = default_timeout
        self.max_peers = max_peers
        
        # 對等代理註冊表
        self.peers: Dict[str, PeerAgent] = {}
        
        # 待處理的請求（用於請求-回應模式）
        self._pending_requests: Dict[str, PendingRequest] = {}
        self._lock = threading.RLock()
        
        # 訊息處理器
        self._handlers: Dict[str, Callable] = {}
        self._broadcast_handlers: List[Callable] = []
        
        # 如果沒有外部 message_bus，創建內部的
        if self.message_bus is None and _INTEGRATION_OK:
            try:
                self.message_bus = MessageBus()
            except Exception:
                self.message_bus = None
        
        # 初始化內存管理器
        self._memory_store: Dict[str, Any] = {}
        
        # 統計
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "broadcasts": 0,
            "requests": 0,
            "responses": 0,
        }
        
        # 事件回調
        self._event_callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    # ------------------------------------------------------------------------
    # 代理註冊與管理
    # ------------------------------------------------------------------------
    
    def register_peer(
        self,
        agent_id: str,
        config: Dict[str, Any],
    ) -> PeerAgent:
        """
        註冊對等代理
        
        Args:
            agent_id: 代理唯一標識
            config: 配置，包含：
                - name: 顯示名稱
                - capabilities: 能力列表
                - tools: 可用工具
                - persona: AgentPersona 實例
                - metadata: 額外元數據
        
        Returns:
            PeerAgent 實例
        """
        with self._lock:
            if len(self.peers) >= self.max_peers:
                raise RuntimeError(f"已達到最大代理數限制 ({self.max_peers})")
            
            if agent_id in self.peers:
                # 更新現有代理
                peer = self.peers[agent_id]
                peer.name = config.get("name", peer.name)
                peer.capabilities = config.get("capabilities", peer.capabilities)
                peer.tools = config.get("tools", peer.tools)
                peer.metadata.update(config.get("metadata", {}))
                peer.touch()
                self._emit_event("peer_updated", peer)
                return peer
            
            # 創建新代理
            peer = PeerAgent(
                agent_id=agent_id,
                name=config.get("name", agent_id),
                persona=config.get("persona"),
                capabilities=config.get("capabilities", []),
                tools=config.get("tools", []),
                state=config.get("state", "idle"),
                metadata=config.get("metadata", {}),
            )
            
            # 初始化記憶
            if self.enable_memory and _INTEGRATION_OK:
                try:
                    peer.memory = AgentMemory(agent_id=agent_id)
                except Exception:
                    peer.memory = None
            else:
                peer.memory = None
            
            self.peers[agent_id] = peer
            self._emit_event("peer_registered", peer)
            
            return peer
    
    def unregister_peer(self, agent_id: str) -> bool:
        """註銷對等代理"""
        with self._lock:
            if agent_id not in self.peers:
                return False
            
            peer = self.peers.pop(agent_id)
            peer.state = "offline"
            self._emit_event("peer_unregistered", peer)
            return True
    
    def get_peer_status(self, agent_id: str) -> Optional[Dict]:
        """取得代理狀態"""
        peer = self.peers.get(agent_id)
        if peer is None:
            return None
        
        return {
            "agent_id": peer.agent_id,
            "name": peer.name,
            "state": peer.state,
            "online": peer.is_online(),
            "last_seen": peer.last_seen.isoformat(),
            "capabilities": peer.capabilities,
            "message_count": peer.message_count,
        }
    
    def list_peers(self, online_only: bool = False) -> List[Dict]:
        """列出所有代理"""
        peers = self.peers.values()
        if online_only:
            peers = [p for p in peers if p.is_online()]
        return [p.to_dict() for p in peers]
    
    # ------------------------------------------------------------------------
    # 訊息傳遞
    # ------------------------------------------------------------------------
    
    def send_to_peer(
        self,
        from_id: str,
        to_id: str,
        payload: Any,
        message_type: str = "message",
        headers: Dict[str, str] = None,
    ) -> bool:
        """
        直接發送訊息到對等代理
        
        Args:
            from_id: 發送者代理 ID
            to_id: 接收者代理 ID
            payload: 訊息內容
            message_type: 訊息類型
            headers: 額外標頭
        
        Returns:
            是否成功發送
        """
        if from_id not in self.peers:
            return False
        if to_id not in self.peers:
            return False
        
        sender = self.peers[from_id]
        receiver = self.peers[to_id]
        
        message = P2PMessage(
            from_peer=from_id,
            to_peer=to_id,
            payload=payload,
            message_type=message_type,
            headers=headers or {},
        )
        
        # 更新統計
        sender.message_count += 1
        sender.touch()
        self.stats["messages_sent"] += 1
        
        # 處理訊息
        self._deliver_message(message, receiver)
        
        return True
    
    def broadcast(
        self,
        from_id: str,
        message: Any,
        exclude: List[str] = None,
    ) -> int:
        """
        廣播訊息到所有對等代理
        
        Args:
            from_id: 發送者代理 ID
            message: 廣播內容
            exclude: 要排除的代理 ID 列表
        
        Returns:
            成功接收的代理數量
        """
        if from_id not in self.peers:
            return 0
        
        sender = self.peers[from_id]
        exclude = exclude or []
        
        # 創建廣播訊息
        p2p_message = P2PMessage(
            from_peer=from_id,
            to_peer=None,  # 廣播標記
            payload=message,
            message_type="broadcast",
        )
        
        # 發送給所有在線代理（排除指定）
        delivered = 0
        for peer_id, peer in self.peers.items():
            if peer_id == from_id or peer_id in exclude:
                continue
            if not peer.is_online():
                continue
            
            p2p_message.id = str(uuid.uuid4())  # 每個接收者不同的 ID
            self._deliver_message(p2p_message, peer)
            delivered += 1
        
        sender.message_count += delivered
        sender.touch()
        self.stats["broadcasts"] += 1
        
        return delivered
    
    def _deliver_message(self, message: P2PMessage, peer: PeerAgent):
        """交付訊息到目標代理"""
        peer.touch()
        self.stats["messages_received"] += 1
        
        # 調用訊息處理器
        handler_key = f"{peer.agent_id}:{message.message_type}"
        if handler_key in self._handlers:
            try:
                self._handlers[handler_key](message)
            except Exception:
                pass
        
        # 通用處理器
        if f"{peer.agent_id}:*" in self._handlers:
            try:
                self._handlers[f"{peer.agent_id}:*"](message)
            except Exception:
                pass
        
        # 廣播處理器
        if message.is_broadcast():
            for handler in self._broadcast_handlers:
                try:
                    handler(message, peer)
                except Exception:
                    pass
    
    # ------------------------------------------------------------------------
    # 請求-回應模式
    # ------------------------------------------------------------------------
    
    async def request_response(
        self,
        from_id: str,
        to_id: str,
        request_payload: Any,
        timeout: float = None,
    ) -> Optional[Any]:
        """
        發送請求並等待回應（請求-回應模式）
        
        Args:
            from_id: 發送者代理 ID
            to_id: 目標代理 ID
            request_payload: 請求內容
            timeout: 超時時間（秒）
        
        Returns:
            回應內容，超時返回 None
        """
        timeout = timeout or self.default_timeout
        
        if from_id not in self.peers or to_id not in self.peers:
            return None
        
        # 創建請求訊息
        request = P2PMessage(
            from_peer=from_id,
            to_peer=to_id,
            payload=request_payload,
            message_type="request",
        )
        
        # 創建 Future 等待回應
        future = asyncio.Future()
        pending = PendingRequest(
            request=request,
            future=future,
            timeout=timeout,
        )
        
        with self._lock:
            self._pending_requests[request.id] = pending
        
        # 發送請求
        self.stats["requests"] += 1
        self.send_to_peer(from_id, to_id, request.payload, message_type="request")
        
        # 等待回應或超時
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            with self._lock:
                self._pending_requests.pop(request.id, None)
            return None
    
    def respond_to_request(
        self,
        responder_id: str,
        request_correlation_id: str,
        response_payload: Any,
    ) -> bool:
        """
        回應請求
        
        Args:
            responder_id: 回應者代理 ID
            request_correlation_id: 請求的 correlation_id
            response_payload: 回應內容
        
        Returns:
            是否成功發送回應
        """
        with self._lock:
            pending = self._pending_requests.get(request_correlation_id)
            if pending is None:
                return False
        
        # 創建回應訊息
        response = P2PMessage(
            from_peer=responder_id,
            to_peer=pending.request.from_peer,
            payload=response_payload,
            message_type="response",
            correlation_id=request_correlation_id,
        )
        
        # 交付回應
        try:
            pending.future.set_result(response.payload)
            self.stats["responses"] += 1
            return True
        except Exception:
            return False
    
    # ------------------------------------------------------------------------
    # 訊息處理器
    # ------------------------------------------------------------------------
    
    def set_message_handler(
        self,
        agent_id: str,
        message_type: str,
        handler: Callable[[P2PMessage], None],
    ):
        """設定訊息處理器"""
        key = f"{agent_id}:{message_type}"
        self._handlers[key] = handler
    
    def set_broadcast_handler(self, handler: Callable[[P2PMessage, PeerAgent], None]):
        """設定廣播處理器"""
        self._broadcast_handlers.append(handler)
    
    # ------------------------------------------------------------------------
    # 事件系統
    # ------------------------------------------------------------------------
    
    def on(self, event: str, callback: Callable):
        """訂閱事件"""
        self._event_callbacks[event].append(callback)
    
    def _emit_event(self, event: str, *args, **kwargs):
        """發出事件"""
        for callback in self._event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass
    
    # ------------------------------------------------------------------------
    # 記憶管理
    # ------------------------------------------------------------------------
    
    def store_in_peer_memory(
        self,
        peer_id: str,
        key: str,
        value: Any,
        memory_type: str = "short_term",
    ) -> bool:
        """存儲到對等代理的記憶"""
        if peer_id not in self.peers:
            return False
        
        peer = self.peers[peer_id]
        if peer.memory is None:
            # 使用內部記憶儲存
            if peer_id not in self._memory_store:
                self._memory_store[peer_id] = {"short_term": {}, "long_term": {}}
            self._memory_store[peer_id][memory_type][key] = value
            return True
        
        # 使用代理自己的記憶
        try:
            if memory_type == "short_term":
                peer.memory.add_short_term(value, tags=[key])
            elif memory_type == "long_term":
                peer.memory.store_long_term(key, value)
            return True
        except Exception:
            return False
    
    def retrieve_from_peer_memory(
        self,
        peer_id: str,
        key: str = None,
        memory_type: str = "short_term",
    ) -> Optional[Any]:
        """從對等代理的記憶檢索"""
        if peer_id not in self.peers:
            return None
        
        peer = self.peers[peer_id]
        if peer.memory is None:
            # 使用內部儲存
            if peer_id not in self._memory_store:
                return None
            if key:
                return self._memory_store[peer_id][memory_type].get(key)
            return self._memory_store[peer_id][memory_type]
        
        # 使用代理自己的記憶
        try:
            if memory_type == "short_term":
                items = peer.memory.get_short_term()
                return items[-1].content if items else None
            elif memory_type == "long_term":
                return peer.memory.retrieve_long_term(key)
        except Exception:
            return None
    
    # ------------------------------------------------------------------------
    # 代理 Spawn（需要 agent_spawner）
    # ------------------------------------------------------------------------
    
    def spawn_sub_agent(
        self,
        parent_peer_id: str,
        role: str,
        task: str,
        persona: Any = None,
    ) -> Optional[str]:
        """
        Spawn 子代理（需要 agent_spawner 整合）
        
        Returns:
            子代理 ID
        """
        if not self.enable_spawner or not _INTEGRATION_OK:
            return None
        
        from agent_spawner import AgentSpawner, SpawnPolicy
        
        try:
            spawner = AgentSpawner()
            request_id = spawner.create_request(
                role=role,
                task_id=str(uuid.uuid4()),
                task_description=task,
                priority=1,
                policy=SpawnPolicy.EAGER,
            )
            
            # 動態創建子代理 ID
            child_id = f"{parent_peer_id}_child_{uuid.uuid4().hex[:8]}"
            
            # 註冊子代理
            self.register_peer(child_id, {
                "name": f"{role}-{child_id[:8]}",
                "capabilities": [role],
                "metadata": {"parent": parent_peer_id, "spawned_task": task}
            })
            
            return child_id
        except Exception:
            return None
    
    # ------------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------------
    
    def get_stats(self) -> Dict:
        """取得統計資訊"""
        return {
            **self.stats,
            "total_peers": len(self.peers),
            "online_peers": len([p for p in self.peers.values() if p.is_online()]),
            "pending_requests": len(self._pending_requests),
        }
    
    def find_peer_by_capability(self, capability: str) -> List[PeerAgent]:
        """根據能力查找代理"""
        return [
            p for p in self.peers.values()
            if capability in p.capabilities and p.is_online()
        ]
    
    def find_peers_by_state(self, state: str) -> List[PeerAgent]:
        """根據狀態查找代理"""
        return [p for p in self.peers.values() if p.state == state]
    
    def cleanup_expired_requests(self):
        """清理過期的請求"""
        with self._lock:
            expired = [
                req_id for req_id, req in self._pending_requests.items()
                if req.is_expired()
            ]
            for req_id in expired:
                pending = self._pending_requests.pop(req_id)
                if not pending.future.done():
                    pending.future.set_result(None)
    
    # ------------------------------------------------------------------------
    # 上下文管理器
    # ------------------------------------------------------------------------
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False
    
    def shutdown(self):
        """優雅關閉"""
        for peer in list(self.peers.values()):
            peer.state = "offline"
        self._pending_requests.clear()


# ============================================================================
# 便捷函數
# ============================================================================

def create_p2p_orchestrator(**kwargs) -> P2POrchestrator:
    """創建 P2P Orchestrator 實例"""
    return P2POrchestrator(**kwargs)


# ============================================================================
# 向後相容性別名
# ============================================================================

Peer = PeerAgent  # 向後相容
