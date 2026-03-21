# Case 28: CrewAI Integration - CrewAI 設計優點整合

## 情境

methodology-v2 吸收 CrewAI 的設計優點，讓 Agent 定義更豐富、工具接入更簡單。

## 三大改進

### 1. AgentPersona - CrewAI 風格人格

```python
from agent_spawner import AgentPersona

persona = AgentPersona(
    role="Researcher",           # 角色
    goal="Find latest AI trends",  # 目標
    backstory="Expert in ML with 10 years experience..."  # 背景故事
)

# 轉換為 prompt
print(persona.to_prompt())
# You are a Researcher. Your goal is: Find latest AI trends. Expert in ML...
```

### 2. ToolRegistry - 一行接入工具

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

### 3. 整合使用

```python
from agent_spawner import SpawnRequest, AgentPersona
from tool_registry import ToolRegistry

request = SpawnRequest(
    role="developer",
    task_id="task-123",
    task_description="開發登入功能",
    persona=AgentPersona(
        role="Developer",
        goal="Write clean code",
        backstory="Senior dev with 10 years..."
    ),
    tools=[
        ToolRegistry.github(repo="org/project"),
        ToolRegistry.slack(channel="#dev")
    ]
)
```

## 內建工具列表

| 工具 | 方法 | 用途 |
|------|------|------|
| slack | `ToolRegistry.slack(channel="#team")` | Slack 訊息 |
| gmail | `ToolRegistry.gmail()` | Gmail |
| notion | `ToolRegistry.notion(page_id="xxx")` | Notion |
| github | `ToolRegistry.github(repo="org/proj")` | GitHub |
| search | `ToolRegistry.search()` | 網頁搜尋 |
| browser | `ToolRegistry.browser()` | 瀏覽器自動化 |
| jira | `ToolRegistry.jira(project="PROJ")` | Jira |
| trello | `ToolRegistry.trello(board="Board")` | Trello |

## 向後相容

```python
# 舊寫法 - 完全相容
SpawnRequest(role="dev", task_id="123")

# 新寫法 - 可選增強
SpawnRequest(
    role="dev",
    task_id="123",
    persona=AgentPersona(...),
    tools=[...]
)
```

## Related

- agent_spawner.py
- tool_registry.py
- agent_team.py
