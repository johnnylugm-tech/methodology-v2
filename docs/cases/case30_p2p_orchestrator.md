# Case 30: P2P Orchestrator - 多代理點對點協作

## 場景

一個 AI 客服系統需要三種專門的代理：
- **Analyzer**：分析客戶問題類型
- **Resolver**：解決技術問題
- **Escalator**：處理需要升級的複雜問題

傳統的星型架構（hub-spoke）會讓所有流量經過協調者，成為瓶頸。

使用 P2P Orchestrator 實現真正的對等協作。

## 架構

```
┌─────────────────────────────────────────────────────────┐
│                    P2POrchestrator                      │
│                                                          │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐           │
│  │ Analyzer│◄────│ Resolver│────►│Escalator│           │
│  └─────────┘     └─────────┘     └─────────┘           │
│       │               │               │                │
│       └───────────────┼───────────────┘                │
│                       │  (所有代理直接溝通)              │
└─────────────────────────────────────────────────────────┘
```

## 實現

```python
import asyncio
from p2p_orchestrator import P2POrchestrator

# 初始化協調器
orchestrator = P2POrchestrator(
    enable_memory=True,
    default_timeout=15.0
)

# 註冊三個專業代理
orchestrator.register_peer("analyzer", {
    "name": "Issue Analyzer",
    "capabilities": ["intent_detection", "sentiment_analysis", "classification"],
    "tools": ["nlp_parser", "keyword_extractor"]
})

orchestrator.register_peer("resolver", {
    "name": "Technical Resolver",
    "capabilities": ["troubleshooting", "code_search", "solution_delivery"],
    "tools": ["knowledge_base", "diagnostic_scripts"]
})

orchestrator.register_peer("escalator", {
    "name": "Human Escalation Handler",
    "capabilities": ["priority_routing", "summary_generation", "handover"],
    "tools": ["ticket_system", "notification_service"]
})

# 設定訊息處理
def handle_analysis_result(msg):
    if msg.payload.get("needs_escalation"):
        orchestrator.send_to_peer(
            from_id="analyzer",
            to_id="escalator",
            payload={
                "issue": msg.payload["issue"],
                "priority": "high",
                "reason": msg.payload["escalation_reason"]
            }
        )
    else:
        orchestrator.send_to_peer(
            from_id="analyzer", 
            to_id="resolver",
            payload={"task": msg.payload["resolved_issue"]}
        )

orchestrator.set_message_handler("analyzer", "response", handle_analysis_result)
```

## 協作流程

### 1. 客戶問題輸入

```python
# 協調者廣播新問題
orchestrator.broadcast(
    from_id="coordinator",
    message={
        "type": "new_ticket",
        "customer_id": "CUST-12345",
        "issue": "系統登入失敗，已持續 30 分鐘"
    }
)
```

### 2. Analyzer 分析問題

```python
# Analyzer 處理並回應
async def analyzer_task():
    # Analyzer 收到問題，進行分析
    analysis = {
        "issue_type": "authentication_error",
        "sentiment": "frustrated",
        "needs_escalation": True,
        "escalation_reason": "VIP 客戶 + 持續時間 > 15分鐘",
        "resolved_issue": None
    }
    
    # 發送分析結果（觸發 handler）
    orchestrator.send_to_peer(
        from_id="analyzer",
        to_id="analyzer",  # 發送給自己觸發 handler
        payload=analysis
    )
```

### 3. P2P 直接協商

```python
# Resolver 和 Analyzer 直接溝通
async def resolver_negotiation():
    # Resolver 請求 Analyzer 提供更多上下文
    context = await orchestrator.request_response(
        from_id="resolver",
        to_id="analyzer",
        request_payload={"query": "客戶最近的活動記錄"}
    )
    
    if context:
        # Resolver 使用上下文解決問題
        solution = await orchestrator.request_response(
            from_id="resolver",
            to_id="resolver",
            request_payload={"action": "diagnose", "context": context}
        )
```

### 4. 升級處理

```python
# Escalator 處理升級
async def escalation_flow():
    # 收到升級請求
    escalation_data = await orchestrator.request_response(
        from_id="escalator",
        to_id="escalator",
        request_payload={
            "action": "prepare_handover",
            "customer": "CUST-12345",
            "summary": "VIP 客戶登入問題，已影響工作 30 分鐘"
        }
    )
    
    # 通知人類支援
    orchestrator.send_to_peer(
        from_id="escalator",
        to_id="human_support",
        payload={
            "ticket_id": "TICKET-789",
            "priority": "P1",
            "summary": escalation_data
        }
    )
```

## 完整工作流程

```python
async def customer_support_workflow(ticket: dict):
    """
    完整客服工作流程
    """
    # 步驟 1: Analyzer 分類問題
    classification = await orchestrator.request_response(
        from_id="analyzer",
        to_id="analyzer",
        request_payload={
            "issue": ticket["issue"],
            "customer_tier": ticket["customer_tier"]
        }
    )
    
    if classification.get("can_self_resolve"):
        # 步驟 2a: Resolver 自動解決
        solution = await orchestrator.request_response(
            from_id="resolver",
            to_id="resolver",
            request_payload={"issue": classification["resolved_issue"]}
        )
        return {"status": "resolved", "solution": solution}
    
    else:
        # 步驟 2b: 升級到人類支援
        await orchestrator.request_response(
            from_id="escalator",
            to_id="escalator",
            request_payload={
                "issue": ticket["issue"],
                "classification": classification,
                "customer": ticket["customer"]
            }
        )
        return {"status": "escalated", "ticket_id": f"TICKET-{ticket['id']}"}


# 執行流程
async def main():
    result = await customer_support_workflow({
        "id": "12345",
        "customer": "ACME Corp",
        "customer_tier": "enterprise",
        "issue": "無法訪問管理後台"
    })
    print(f"處理結果: {result}")

asyncio.run(main())
```

## 記憶共享

```python
# Analyzer 將分析結果存入共享記憶
orchestrator.store_in_peer_memory(
    peer_id="analyzer",
    key="ticket_analysis",
    value={
        "ticket_id": "12345",
        "issue_type": "authentication",
        "confidence": 0.92
    },
    memory_type="long_term"
)

# Resolver 可以檢索這個記憶
context = orchestrator.retrieve_from_peer_memory(
    peer_id="analyzer",
    key="ticket_analysis"
)
```

## 監控和統計

```python
# 查看系統狀態
stats = orchestrator.get_stats()

print(f"訊息發送: {stats['messages_sent']}")
print(f"訊息接收: {stats['messages_received']}")
print(f"廣播次數: {stats['broadcasts']}")
print(f"總代理數: {stats['total_peers']}")
print(f"在線代理: {stats['online_peers']}")

# 查看特定代理狀態
for peer in orchestrator.list_peers():
    print(f"{peer['name']}: {peer['state']} ({peer['message_count']} 訊息)")
```

## 關鍵優勢

| 特性 | 星型架構 | P2P Orchestrator |
|------|---------|------------------|
| 訊息延遲 | O(n) 經過 hub | O(1) 直接傳遞 |
| 擴展性 | 受限於 hub | 線性擴展 |
| 容錯性 | hub 是瓶頸 | 無單點故障 |
| 代理自主性 | 低 | 高 |
| 複雜度 | 低 | 中 |

## 總結

P2P Orchestrator 實現了真正的對等代理協作：
- 每個代理可以自由直接通訊
- 支援一對一和一對多通訊
- 請求-回應模式確保同步協作
- 獨立記憶保持上下文
- 可擴展的子代理 spawn 機制
