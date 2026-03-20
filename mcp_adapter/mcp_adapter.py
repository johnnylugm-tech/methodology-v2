"""
MCP Protocol Adapter for methodology-v2

Provides MCP client/server implementation, service discovery,
and unified tool interface for enterprise integration.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPConfig:
    """MCP Adapter Configuration"""
    timeout: int = 30
    retry: int = 3
    cache: bool = True
    cache_ttl: int = 3600
    auto_reconnect: bool = True


@dataclass
class ServiceConnection:
    """Service connection state"""
    name: str
    status: ServiceStatus = ServiceStatus.DISCONNECTED
    credentials: Dict[str, str] = field(default_factory=dict)
    tools: List[Dict[str, Any]] = field(default_factory=list)
    last_used: Optional[float] = None


class MCPClient:
    """MCP Protocol Client"""
    
    def __init__(self, config: MCPConfig = None):
        self.config = config or MCPConfig()
        self.connections: Dict[str, ServiceConnection] = {}
    
    async def connect(self, service: str, **credentials) -> bool:
        """Connect to MCP server"""
        logger.info(f"Connecting to {service}...")
        
        conn = ServiceConnection(
            name=service,
            status=ServiceStatus.CONNECTING,
            credentials=credentials
        )
        
        try:
            # Simulate connection (real implementation would use actual MCP)
            await asyncio.sleep(0.1)
            
            conn.status = ServiceStatus.CONNECTED
            conn.tools = self._discover_tools(service)
            self.connections[service] = conn
            
            logger.info(f"Connected to {service} with {len(conn.tools)} tools")
            return True
            
        except Exception as e:
            conn.status = ServiceStatus.ERROR
            logger.error(f"Failed to connect to {service}: {e}")
            return False
    
    def _discover_tools(self, service: str) -> List[Dict[str, Any]]:
        """Discover available tools for service"""
        tools_map = {
            "slack": [
                {"name": "send_message", "params": ["channel", "text"]},
                {"name": "list_channels", "params": []},
                {"name": "get_thread", "params": ["channel", "thread_ts"]},
            ],
            "notion": [
                {"name": "create_database", "params": ["title", "properties"]},
                {"name": "create_page", "params": ["parent_id", "content"]},
                {"name": "query_database", "params": ["database_id"]},
            ],
            "github": [
                {"name": "create_issue", "params": ["repo", "title", "body"]},
                {"name": "list_issues", "params": ["repo"]},
                {"name": "create_pr", "params": ["repo", "title", "base", "head"]},
            ],
            "gmail": [
                {"name": "send_email", "params": ["to", "subject", "body"]},
                {"name": "search_emails", "params": ["query"]},
                {"name": "read_email", "params": ["message_id"]},
            ],
        }
        return tools_map.get(service, [])
    
    async def call_tool(self, service: str, tool: str, params: Dict) -> Any:
        """Call MCP tool"""
        if service not in self.connections:
            raise ValueError(f"Not connected to {service}")
        
        conn = self.connections[service]
        if conn.status != ServiceStatus.CONNECTED:
            raise RuntimeError(f"Service {service} not ready")
        
        logger.info(f"Calling {service}.{tool} with params {params}")
        
        # Simulate tool execution
        await asyncio.sleep(0.1)
        
        return {"status": "success", "service": service, "tool": tool}
    
    async def disconnect(self, service: str):
        """Disconnect from service"""
        if service in self.connections:
            self.connections[service].status = ServiceStatus.DISCONNECTED
            logger.info(f"Disconnected from {service}")


class RequestRouter:
    """Routes requests to appropriate MCP service"""
    
    def __init__(self, client: MCPClient):
        self.client = client
        self.service_keywords = {
            "slack": ["slack", "channel", "message", "chat"],
            "notion": ["notion", "database", "page", "workspace"],
            "github": ["github", "issue", "pr", "pull request", "repo"],
            "gmail": ["email", "gmail", "mail", "send"],
        }
    
    def route(self, prompt: str) -> tuple[str, str, Dict]:
        """Route prompt to appropriate service and tool"""
        prompt_lower = prompt.lower()
        
        for service, keywords in self.service_keywords.items():
            for keyword in keywords:
                if keyword in prompt_lower:
                    # Find first available tool
                    if service in self.client.connections:
                        tools = self.client.connections[service].tools
                        if tools:
                            return service, tools[0]["name"], {}
        
        raise ValueError(f"Could not route prompt: {prompt}")


class MCPAdapter:
    """
    Main MCP Adapter class for methodology-v2 integration.
    
    Usage:
        adapter = MCPAdapter()
        adapter.connect("slack", token="xxx")
        result = adapter.execute("在 Slack 發送訊息")
    """
    
    def __init__(self, config: MCPConfig = None):
        self.config = config or MCPConfig()
        self.client = MCPClient(self.config)
        self.router = RequestRouter(self.client)
    
    def connect(self, service: str, **credentials) -> bool:
        """Connect to a service"""
        return asyncio.run(self.client.connect(service, **credentials))
    
    def disconnect(self, service: str):
        """Disconnect from a service"""
        asyncio.run(self.client.disconnect(service))
    
    def execute(self, prompt: str, **params) -> Dict:
        """Execute prompt by routing to appropriate service"""
        service, tool, default_params = self.router.route(prompt)
        params = {**default_params, **params}
        
        return asyncio.run(self.client.call_tool(service, tool, params))
    
    def list_services(self) -> List[str]:
        """List connected services"""
        return list(self.client.connections.keys())
    
    def list_tools(self, service: str) -> List[Dict]:
        """List available tools for service"""
        if service in self.client.connections:
            return self.client.connections[service].tools
        return []


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Protocol Adapter")
    parser.add_argument("command", choices=["list", "connect", "test", "server"])
    parser.add_argument("--service", help="Service name")
    parser.add_argument("--token", help="Auth token")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    
    args = parser.parse_args()
    
    adapter = MCPAdapter()
    
    if args.command == "list":
        services = adapter.list_services()
        print(f"Connected services: {services}")
    
    elif args.command == "connect":
        if args.service and args.token:
            success = adapter.connect(args.service, token=args.token)
            print(f"Connected: {success}")
        else:
            print("Error: --service and --token required")
    
    elif args.command == "test":
        if args.service:
            tools = adapter.list_tools(args.service)
            print(f"Tools for {args.service}: {json.dumps(tools, indent=2)}")
        else:
            print("Error: --service required")
    
    elif args.command == "server":
        print(f"Starting MCP server on port {args.port}...")
        # Server mode would run async server here
