---
name: mcp-adapter
description: MCP Protocol Adapter for methodology-v2. Use when: (1) Connecting to external services (Slack, Notion, GitHub, Gmail, etc.), (2) Building multi-tool AI agents, (3) Integrating enterprise workflows, (4) Following the methodology-v2 development framework. Provides MCP client/server implementation, service discovery, and unified tool interface.
---

# MCP Protocol Adapter

This skill provides MCP (Model Context Protocol) integration for methodology-v2, enabling AI agents to connect to enterprise services seamlessly.

## Quick Start

```python
import sys
sys.path.insert(0, '/workspace/methodology-v2')
sys.path.insert(0, '/workspace/mcp-adapter/scripts')

from mcp_adapter import MCPAdapter

# Initialize
adapter = MCPAdapter()

# Connect to services
adapter.connect("slack", token="xoxb-xxx")
adapter.connect("notion", token="secret_xxx")

# Execute task (auto-routes to appropriate tool)
result = adapter.execute("建立 Notion 資料庫追蹤專案進度")
```

## Architecture

```
MCPAdapter
├── MCPClient          # Connects to MCP servers
├── ServiceRegistry    # Manages service connections
├── RequestRouter      # Routes requests to appropriate tools
├── ResponseHandler    # Normalizes responses
└── MCPServer          # Exposes methodology-v2 as MCP provider
```

## Supported Services

| Service | Status | Description |
|---------|--------|-------------|
| Slack | ✅ | Messaging, channels, threads |
| Notion | ✅ | Databases, pages, workspace |
| GitHub | ✅ | Issues, PRs, repos |
| Gmail | ✅ | Send, read, search emails |
| Google Drive | ✅ | Files, folders, sharing |
| Stripe | ⏳ | Payments, customers |

## Configuration

```python
from mcp_adapter import MCPConfig

config = MCPConfig(
    timeout=30,
    retry=3,
    cache=True,
    cache_ttl=3600
)

adapter = MCPAdapter(config)
```

## Integration with methodology-v2

```python
from methodology import Crew, Agent
from mcp_adapter import MCPAdapter

# Create agent with MCP tools
adapter = MCPAdapter()
adapter.connect("slack")
adapter.connect("notion")

# Use in Crew workflow
crew = Crew(agents=[agent_with_mcp], process="sequential")
result = crew.kickoff()
```

## Error Handling

| Error Type | Handling |
|------------|----------|
| ConnectionError | Retry 3x, then fallback |
| AuthError | Raise immediately |
| RateLimitError | Exponential backoff |
| TimeoutError | Return partial + warning |

## CLI Usage

```bash
# List available services
python mcp_adapter.py list

# Connect a service
python mcp_adapter.py connect slack --token xoxb-xxx

# Test connection
python mcp_adapter.py test slack

# Run in server mode
python mcp_adapter.py server --port 8080
```

## See Also

- [references/mcp_protocol.md](references/mcp_protocol.md) - MCP protocol details
- [references/service_configs.md](references/service_configs.md) - Service configuration templates
