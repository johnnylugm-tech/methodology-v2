#!/usr/bin/env python3
"""
Tool Registry - 統一工具接入中心

参考 CrewAI 设计，提供一行代碼接入常用工具

使用範例：
    from tool_registry import ToolRegistry
    
    tools = [
        ToolRegistry.slack(channel="#team"),
        ToolRegistry.gmail(),
        ToolRegistry.github(repo="org/project")
    ]
"""

from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod


class BaseTool(ABC):
    """工具基類"""
    
    name: str
    description: str
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """執行工具"""
        pass
    
    def __repr__(self):
        return f"<Tool: {self.name}>"


class ToolRegistry:
    """
    統一工具註冊中心
    
    內建工具：
        - slack: 發送 Slack 訊息
        - gmail: 發送 Gmail
        - notion: Notion 頁面操作
        - github: GitHub 操作
        - search: 網頁搜尋
        - browser: 瀏覽器自動化
    """
    
    # 內建工具註冊表
    _tools: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, tool_class: type):
        """註冊自定義工具"""
        cls._tools[name] = tool_class
    
    @classmethod
    def slack(cls, channel: str, **kwargs) -> BaseTool:
        """Slack 工具工廠"""
        return _SlackTool(channel=channel, **kwargs)
    
    @classmethod
    def gmail(cls, **kwargs) -> BaseTool:
        """Gmail 工具工廠"""
        return _GmailTool(**kwargs)
    
    @classmethod
    def notion(cls, page_id: str, **kwargs) -> BaseTool:
        """Notion 工具工廠"""
        return _NotionTool(page_id=page_id, **kwargs)
    
    @classmethod
    def github(cls, repo: str, **kwargs) -> BaseTool:
        """GitHub 工具工廠"""
        return _GitHubTool(repo=repo, **kwargs)
    
    @classmethod
    def search(cls, **kwargs) -> BaseTool:
        """搜尋工具工廠"""
        return _SearchTool(**kwargs)
    
    @classmethod
    def browser(cls, **kwargs) -> BaseTool:
        """瀏覽器工具工廠"""
        return _BrowserTool(**kwargs)
    
    @classmethod
    def jira(cls, project: str, **kwargs) -> BaseTool:
        """Jira 工具工廠"""
        return _JiraTool(project=project, **kwargs)
    
    @classmethod
    def trello(cls, board: str, **kwargs) -> BaseTool:
        """Trello 工具工廠"""
        return _TrelloTool(board=board, **kwargs)
    
    @classmethod
    def list_available(cls) -> List[str]:
        """列出所有可用工具"""
        return list(cls._tools.keys())


# ============================================================================
# 內建工具實現
# ============================================================================

class _SlackTool(BaseTool):
    """Slack 工具"""
    name = "slack"
    description = "Send messages to Slack channels"
    
    def __init__(self, channel: str, **kwargs):
        self.channel = channel
        self.kwargs = kwargs
    
    def run(self, message: str) -> dict:
        """發送 Slack 訊息"""
        # TODO: 實現真實的 Slack API 調用
        return {
            "status": "sent",
            "channel": self.channel,
            "message": message,
            "tool": "slack"
        }


class _GmailTool(BaseTool):
    """Gmail 工具"""
    name = "gmail"
    description = "Send emails via Gmail"
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def run(self, to: str, subject: str, body: str) -> dict:
        """發送 Gmail"""
        # TODO: 實現真實的 Gmail API 調用
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
            "tool": "gmail"
        }


class _NotionTool(BaseTool):
    """Notion 工具"""
    name = "notion"
    description = "Interact with Notion pages"
    
    def __init__(self, page_id: str, **kwargs):
        self.page_id = page_id
        self.kwargs = kwargs
    
    def run(self, content: str, action: str = "create_block") -> dict:
        """操作 Notion 頁面"""
        # TODO: 實現真實的 Notion API 調用
        return {
            "status": "done",
            "page_id": self.page_id,
            "action": action,
            "tool": "notion"
        }


class _GitHubTool(BaseTool):
    """GitHub 工具"""
    name = "github"
    description = "Interact with GitHub repositories"
    
    def __init__(self, repo: str, **kwargs):
        self.repo = repo
        self.kwargs = kwargs
    
    def run(self, action: str, **params) -> dict:
        """執行 GitHub 操作"""
        # TODO: 實現真實的 GitHub API 調用
        return {
            "status": "done",
            "action": action,
            "repo": self.repo,
            "tool": "github"
        }


class _SearchTool(BaseTool):
    """搜尋工具"""
    name = "search"
    description = "Web search tool"
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def run(self, query: str, max_results: int = 5) -> dict:
        """執行網頁搜尋"""
        # TODO: 實現真實的搜尋 API 調用
        return {
            "results": [],
            "query": query,
            "max_results": max_results,
            "tool": "search"
        }


class _BrowserTool(BaseTool):
    """瀏覽器工具"""
    name = "browser"
    description = "Browser automation tool"
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def run(self, url: str, action: str = "goto") -> dict:
        """執行瀏覽器操作"""
        # TODO: 實現真實的瀏覽器自動化
        return {
            "status": action,
            "url": url,
            "tool": "browser"
        }


class _JiraTool(BaseTool):
    """Jira 工具"""
    name = "jira"
    description = "Interact with Jira issues"
    
    def __init__(self, project: str, **kwargs):
        self.project = project
        self.kwargs = kwargs
    
    def run(self, action: str, issue_key: str = None, **params) -> dict:
        """執行 Jira 操作"""
        # TODO: 實現真實的 Jira API 調用
        return {
            "status": "done",
            "action": action,
            "project": self.project,
            "tool": "jira"
        }


class _TrelloTool(BaseTool):
    """Trello 工具"""
    name = "trello"
    description = "Interact with Trello boards"
    
    def __init__(self, board: str, **kwargs):
        self.board = board
        self.kwargs = kwargs
    
    def run(self, action: str, **params) -> dict:
        """執行 Trello 操作"""
        # TODO: 實現真實的 Trello API 調用
        return {
            "status": "done",
            "action": action,
            "board": self.board,
            "tool": "trello"
        }


# 註冊預設工具
ToolRegistry._tools = {
    "slack": _SlackTool,
    "gmail": _GmailTool,
    "notion": _NotionTool,
    "github": _GitHubTool,
    "search": _SearchTool,
    "browser": _BrowserTool,
    "jira": _JiraTool,
    "trello": _TrelloTool,
}


# ============================================================================
# Main - 測試
# ============================================================================

if __name__ == "__main__":
    print("=== Tool Registry Demo ===\n")
    
    # 列出可用工具
    print("Available tools:", ToolRegistry.list_available())
    print()
    
    # 使用 Slack
    slack = ToolRegistry.slack(channel="#team")
    print(f"Slack tool: {slack}")
    result = slack.run("Hello from ToolRegistry!")
    print(f"Result: {result}\n")
    
    # 使用 GitHub
    github = ToolRegistry.github(repo="org/project")
    print(f"GitHub tool: {github}")
    result = github.run(action="create_issue", title="Bug report")
    print(f"Result: {result}\n")
    
    # 使用 Search
    search = ToolRegistry.search()
    print(f"Search tool: {search}")
    result = search.run("AI agents 2026")
    print(f"Result: {result}\n")
    
    # 測試 AgentPersona
    print("=== AgentPersona Demo ===\n")
    from agent_spawner import AgentPersona
    
    persona = AgentPersona(
        role="Researcher",
        goal="Find latest AI trends",
        backstory="Expert in ML with 10 years experience"
    )
    print(f"Persona: {persona}")
    print(f"Prompt: {persona.to_prompt()}\n")
