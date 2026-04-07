---
name: map-protocol
description: Methodology Agent Protocol (MAP) for standardizing inter-agent communication. Use when: (1) Multiple agents need to communicate, (2) Building agent workflows, (3) Integrating with external frameworks. Provides standardized message format and protocol handler.
---

# MAP Protocol

Methodology Agent Protocol - Standardized inter-agent communication.

## Quick Start

```python
from map_protocol import MAPProtocol, AgentMessage

# Create message
msg = AgentMessage(
    from_agent="coder",
    to_agent="reviewer",
    type="task_complete",
    payload={"result": "code_review_done"}
)

# Send via protocol
protocol = MAPProtocol()
protocol.send(msg)
```

## Message Types

| Type | Description | Payload |
|------|-------------|---------|
| `task_start` | Agent started task | `{task_id, description}` |
| `task_progress` | Task progress update | `{progress, status}` |
| `task_complete` | Task completed | `{result, artifacts}` |
| `task_failed` | Task failed | `{error, retry}` |
| `request_help` | Request assistance | `{question, context}` |
| `provide_help` | Provide assistance | `{answer, suggestions}` |
| `handoff` | Transfer task | `{task_id, reason, priority}` |
| `heartbeat` | Agent alive | `{status, load}` |

## Message Format

```json
{
    "protocol": "map-v1",
    "message_id": "msg_123456",
    "timestamp": 1700000000.123,
    "from": {
        "agent_id": "coder",
        "role": "developer"
    },
    "to": {
        "agent_id": "reviewer",
        "role": "qa"
    },
    "type": "task_complete",
    "priority": "normal",
    "payload": {
        "task_id": "task_789",
        "result": "success",
        "artifacts": ["file.py"]
    }
}
```

## Usage

### Basic Communication

```python
from map_protocol import MAPProtocol, AgentMessage

protocol = MAPProtocol()

# Agent A sends to Agent B
msg = AgentMessage(
    from_agent="agent_a",
    to_agent="agent_b",
    type="task_complete",
    payload={"result": "done"}
)

protocol.send(msg)

# Agent B receives
received = protocol.receive("agent_b")
```

### Pub/Sub Pattern

```python
# Subscribe to message types
protocol.subscribe("task_failed", callback=handle_failure)

# Publish message
protocol.publish(AgentMessage(
    from_agent="agent_a",
    to_agent="*",  # Broadcast
    type="task_failed",
    payload={"error": "timeout"}
))
```

### Request/Response Pattern

```python
# Send request
request = AgentMessage(
    from_agent="agent_a",
    to_agent="agent_b",
    type="request_help",
    payload={"question": "How do I fix this bug?"}
)

response = protocol.request_response(request, timeout=30)
```

## Protocol Handler

### Create Handler

```python
from map_protocol import ProtocolHandler

handler = ProtocolHandler(agent_id="my_agent")

@handler.on("task_complete")
def handle_task_complete(msg):
    print(f"Task completed: {msg.payload}")

@handler.on("handoff")
def handle_handoff(msg):
    print(f"Received handoff from {msg.from_agent}")
    return {"status": "accepted"}

handler.start()
```

### Message Routing

```python
router = MessageRouter()

# Add routes
router.add_route("coder", "reviewer", direct=True)
router.add_route("reviewer", "qa", direct=True)
router.add_route("*", "logger", broadcast=True)

# Route message
next_hop = router.route(message)
```

## Integration

### LangChain Integration

```python
from map_protocol import MAPAdapter

# Convert LangChain messages to MAP
adapter = MAPAdapter()

map_msg = adapter.from_langchain(langchain_msg)
map_msg.to_langchain()
```

### MCP Integration

```python
from map_protocol import MCPBridge

bridge = MCPBridge()

# Forward MAP messages to MCP tools
bridge.forward_to_mcp(message)
```

## Error Handling

| Error | Handling |
|-------|----------|
| Agent not found | Queue message, retry |
| Timeout | Return error, log |
| Invalid format | Reject with error |

## CLI Usage

```bash
# Start protocol server
python map_protocol.py server --port 8080

# Send message
python map_protocol.py send --from agent_a --to agent_b --type task_complete

# View queue
python map_protocol.py queue --agent agent_a
```

## Best Practices

1. **Use standard types** - Don't create custom message types
2. **Include context** - Always provide enough payload context
3. **Handle timeouts** - Set reasonable timeout values
4. **Log everything** - Use logging for debugging

## See Also

- [message_bus.py](message_bus.py) - Message bus implementation
- [agent_communication.py](agent_communication.py) - Agent communication
