# SKILL.md - Tool Registry

## Metadata

```yaml
name: tool-registry
description: 統一工具接入中心。參考 CrewAI 設計，提供一行代碼接入常用工具。
```

## When to Use

- 需要為 Agent 配備工具
- 希望用一行代碼接入 Slack/GitHub/Notion
- 需要統一的工具管理

## Quick Start

```python
from tool_registry import ToolRegistry

# Slack 工具
slack = ToolRegistry.slack(channel="#team")
slack.run("Hello!")

# GitHub 工具
github = ToolRegistry.github(repo="org/project")
github.run(action="create_issue", title="Bug")

# 搜尋工具
search = ToolRegistry.search()
search.run("AI trends 2026")
```

## 內建工具

| 工具 | 方法 | 用途 |
|------|------|------|
| slack | `ToolRegistry.slack(channel="#team")` | 發送 Slack 訊息 |
| gmail | `ToolRegistry.gmail()` | 發送 Gmail |
| notion | `ToolRegistry.notion(page_id="xxx")` | Notion 頁面操作 |
| github | `ToolRegistry.github(repo="org/proj")` | GitHub 操作 |
| search | `ToolRegistry.search()` | 網頁搜尋 |
| browser | `ToolRegistry.browser()` | 瀏览器自動化 |
| jira | `ToolRegistry.jira(project="PROJ")` | Jira 操作 |
| trello | `ToolRegistry.trello(board="Board")` | Trello 操作 |

## 與 SpawnRequest 整合

```python
from agent_spawner import SpawnRequest, AgentPersona
from tool_registry import ToolRegistry

# CrewAI 風格的 Agent 定義
persona = AgentPersona(
    role="Developer",
    goal="Write clean code",
    backstory="Senior dev with 10 years..."
)

request = SpawnRequest(
    role="developer",
    task_id="task-123",
    task_description="開發登入功能",
    persona=persona,
    tools=[
        ToolRegistry.github(repo="org/project"),
        ToolRegistry.slack(channel="#dev")
    ]
)
```

## CLI

```bash
python tool_registry.py
```

## Related

- agent_spawner.py
- agent_team.py
