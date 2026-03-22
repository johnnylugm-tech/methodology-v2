# P2P Orchestrator - 點對點代理協調器

> 讓主代理可以平等協作的 P2P 架構

## 概述

P2P Orchestrator 實現了去中心化的代理協調模式，每個代理都是對等節點，可以：
- 直接通訊
- 廣播訊息
- 請求-回應模式
- 擁有獨立記憶空間

## 核心概念

### PeerAgent - 對等代理

每個代理是一個完整的自治實例：

```python
@dataclass
class PeerAgent:
    agent_id: str           # 唯一標識
    name: str               # 顯示名稱
    capabilities: List[str] # 能力列表
    tools: List[str]        # 可用工具
    state: str              # idle/running/busy/offline
    memory: AgentMemory     # 獨立記憶
    workspace: Dict          # 工作空間
```

### 訊息類型

| 類型 | 說明 |
|------|------|
| `message` | 一般訊息 |
| `request` | 請求（需要回應） |
| `response` | 回應 |
| `broadcast` | 廣播 |
| `error` | 錯誤 |

## API 參考

### 初始化

```python
from p2p_orchestrator import P2POrchestrator

orchestrator = P2POrchestrator(
    message_bus=None,        # 可選外部 message_bus
    enable_memory=True,      # 啟用記憶管理
    enable_spawner=True,     # 啟用子代理 spawn
    default_timeout=30.0,     # 預設超時
    max_peers=100,           # 最大代理數
)
```

### 註冊代理

```python
orchestrator.register_peer("agent-1", {
    "name": "Researcher",
    "capabilities": ["web_search", "data_analysis"],
    "tools": ["browser", "web_search"],
    "metadata": {"specialty": "AI trends"}
})
```

### 發送訊息

```python
# 直接發送
orchestrator.send_to_peer(
    from_id="agent-1",
    to_id="agent-2",
    payload={"task": "analyze this"},
    message_type="message"
)
```

### 廣播

```python
# 廣播到所有在線代理（排除自己）
count = orchestrator.broadcast(
    from_id="agent-1",
    message={"announcement": "任務完成"},
    exclude=["agent-3"]  # 可選排除列表
)
print(f"送達 {count} 個代理")
```

### 請求-回應（異步）

```python
import asyncio

async def query_peer():
    response = await orchestrator.request_response(
        from_id="agent-1",
        to_id="agent-2",
        request_payload={"query": "最新消息？"},
        timeout=10.0
    )
    
    if response:
        print(f"收到回應: {response}")
    else:
        print("請求超時")

asyncio.run(query_peer())
```

### 取得代理狀態

```python
status = orchestrator.get_peer_status("agent-1")

if status:
    print(f"狀態: {status['state']}")
    print(f"在線: {status['online']}")
    print(f"最後活動: {status['last_seen']}")
```

### 列出所有代理

```python
# 所有代理
all_peers = orchestrator.list_peers()

# 僅在線代理
online_peers = orchestrator.list_peers(online_only=True)
```

### 訊息處理器

```python
def handle_message(msg: P2PMessage):
    print(f"收到訊息: {msg.payload}")

# 設定特定類型處理器
orchestrator.set_message_handler("agent-2", "message", handle_message)

# 設定廣播處理器
orchestrator.set_broadcast_handler(lambda msg, peer: print(f"廣播到 {peer.name}"))
```

### 記憶管理

```python
# 存儲到代理記憶
orchestrator.store_in_peer_memory(
    peer_id="agent-1",
    key="context",
    value={"task": "research", "status": "in_progress"},
    memory_type="short_term"
)

# 檢索記憶
context = orchestrator.retrieve_from_peer_memory(
    peer_id="agent-1",
    key="context",
    memory_type="short_term"
)
```

### 根據能力查找

```python
# 找出会 web_search 的代理
researchers = orchestrator.find_peer_by_capability("web_search")

# 找所有空閒代理
idle_peers = orchestrator.find_peers_by_state("idle")
```

### 事件監聽

```python
orchestrator.on("peer_registered", lambda peer: print(f"新代理: {peer.name}"))
orchestrator.on("peer_unregistered", lambda peer: print(f"代理離開: {peer.name}"))
orchestrator.on("peer_updated", lambda peer: print(f"代理更新: {peer.name}"))
```

## 整合現有模組

### 整合 message_bus.py

```python
from message_bus import MessageBus

# 使用外部 message_bus
bus = MessageBus()
orchestrator = P2POrchestrator(message_bus=bus)
```

### 整合 agent_memory

每個 `PeerAgent` 自動擁有獨立的 `AgentMemory` 實例：

```python
peer = orchestrator.peers["agent-1"]
if peer.memory:
    peer.memory.add_short_term({"event": "task_complete"})
```

### 整合 agent_spawner

Spawn 子代理參與協作：

```python
child_id = orchestrator.spawn_sub_agent(
    parent_peer_id="agent-1",
    role="researcher",
    task="研究競爭對手動態"
)
```

## 完整範例

```python
import asyncio
from p2p_orchestrator import P2POrchestrator

async def main():
    # 創建協調器
    orchestrator = P2POrchestrator()
    
    # 註冊三個代理
    orchestrator.register_peer("coordinator", {
        "name": "Coordinator",
        "capabilities": ["coordination", "planning"]
    })
    
    orchestrator.register_peer("researcher", {
        "name": "Researcher",
        "capabilities": ["web_search", "data_analysis"]
    })
    
    orchestrator.register_peer("executor", {
        "name": "Executor",
        "capabilities": ["code_generation", "testing"]
    })
    
    # 協調者發起任務
    orchestrator.send_to_peer(
        from_id="coordinator",
        to_id="researcher",
        payload={"task": "研究 2025 年 AI 趨勢"}
    )
    
    # 請求研究結果
    results = await orchestrator.request_response(
        from_id="coordinator",
        to_id="researcher",
        request_payload={"query": "總結要點"}
    )
    
    # 廣播最終結果
    orchestrator.broadcast(
        from_id="coordinator",
        message={"summary": results}
    )
    
    # 查看統計
    print(orchestrator.get_stats())

asyncio.run(main())
```

## 統計資訊

```python
stats = orchestrator.get_stats()
# {
#     "messages_sent": 10,
#     "messages_received": 8,
#     "broadcasts": 2,
#     "requests": 5,
#     "responses": 4,
#     "total_peers": 3,
#     "online_peers": 3,
#     "pending_requests": 0
# }
```

## 錯誤處理

```python
# 代理不存在
if not orchestrator.get_peer_status("unknown-agent"):
    print("代理不存在")

# 請求超時
response = await orchestrator.request_response(...)
if response is None:
    print("請求超時或代理離線")

# 清理過期請求
orchestrator.cleanup_expired_requests()
```

## 最佳實踐

1. **合理的超時設置**：根據任務性質調整 `default_timeout`
2. **記憶管理**：重要上下文存儲到 long_term_memory
3. **狀態維護**：及時更新代理狀態（idle/busy/offline）
4. **錯誤處理**：使用 `try/except` 包裝所有 P2P 操作
5. **資源清理**：使用上下文管理器或显式调用 `shutdown()`

## 與現有模組的關係

```
┌─────────────────────────────────────────────────────┐
│                 P2POrchestrator                      │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │message_bus  │  │ agent_memory│  │agent_spawner│  │
│  │ (transport) │  │ (per-peer   │  │(sub-agents) │  │
│  │             │  │  memory)    │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│         ▲                ▲                ▲        │
│         │                │                │        │
│    ┌────┴────────────────┴────────────────┴────┐    │
│    │              PeerAgent                    │    │
│    │  - agent_id, name                         │    │
│    │  - capabilities, tools                     │    │
│    │  - memory (AgentMemory)                   │    │
│    │  - workspace                              │    │
│    └───────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

_Last updated: 2025-03-22_
