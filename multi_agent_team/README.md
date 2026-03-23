# Multi-Agent Team Module

## 功能
- 4 Agent 協作開發
- DevBot: 開發
- ReviewBot: 審查
- TestBot: 測試
- DocBot: 文件

## 使用方法

```python
from multi_agent_team import MultiAgentTeam, AgentRole

team = MultiAgentTeam()
result = team.run_workflow('src')
print(f"Steps: {result['steps']}")
```

## Agent Roles

| Role | Name | 職責 |
|------|------|------|
| DEVELOPER | DevBot | 開發功能 |
| REVIEWER | ReviewBot | Code Review |
| TESTER | TestBot | 測試驗證 |
| DOCUMENTER | DocBot | 文件撰寫 |

## Workflow

1. DevBot 開發
2. ReviewBot 審查
3. TestBot 測試
4. DocBot 文件

## Quality Gate

- 4 steps completed → 通過
