# Case 36: Quick Start - 快速啟動系統

## 目標
對標 CrewAI 的 minimal boilerplate，降低起步門檻

## 問題
現有的 Agent Team 系統功能完整，但起步需要較多配置：
- 需要了解多個模組的互動
- 需要手動建立 Agent、Team、Task
- 缺乏預設模板快速啟動

## 解決方案
實現 quick_start.py，提供三層次的極簡 API：

### Level 1: 5 行啟動一個 Agent
```python
from quick_start import create_agent

agent = create_agent(
    name="DevBot",
    role="Developer",
    goal="Write code"
)
```

### Level 2: 3 行建立團隊
```python
from quick_start import create_team, create_agent

dev_agent = create_agent("DevBot", "Developer", "Write code")
review_agent = create_agent("ReviewBot", "Reviewer", "Review code")
team = create_team("DevTeam", [dev_agent, review_agent])
```

### Level 3: 一行執行任務
```python
from quick_start import quick_start, run_task

team = quick_start("full")  # 一行建立完整團隊
result = run_task(team, "Build a login system")
```

## 預設模板

| 模板 | Agent 數量 | 用途 |
|------|-----------|------|
| `dev` | 2 | 開發團隊 (Developer + Reviewer) |
| `pm` | 1 | PM 團隊 (PM) |
| `full` | 4 | 完整團隊 (Architect + Developer + Reviewer + Tester) |

## 互動式模式

```bash
python quick_start.py interactive
```

輸出：
```
🚀 Quick Start - Agent Team Generator
========================================
Templates:
  1. dev
  2. pm
  3. full

Select template (1-3) or 'q' to quit:
```

## CLI 模式

```bash
# 查看可用模板
python quick_start.py templates

# 快速啟動完整團隊
python quick_start.py quick

# 互動式選擇
python quick_start.py interactive
```

## 設計原則

1. **零負擔** - 不需要了解底層架構
2. **AI-native** - 用自然的方式建立 Agent Team
3. **可擴展** - 從簡單模板開始，逐步客製化

## 與 CrewAI 的對標

| 功能 | CrewAI | 本系統 |
|------|--------|--------|
| 5 行啟動 Agent | `Agent(role="...")` | `create_agent()` |
| 3 行建立團隊 | `Crew(agents=[...])` | `create_team()` |
| 預設模板 | via examples | via `quick_start()` |
| 互動式引導 | 第三方 | 原生支援 |

## 擴展方向

1. **更多模板** - data_team, research_team, creative_team
2. **自定義模板** - 用戶可保存自己的模板
3. **整合執行** - 真正執行任務而不只是返回結構
