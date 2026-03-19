# 🎯 Methodology v2 Skill

> Multi-Agent Collaboration Development Methodology v2.1

## 安裝

```bash
cd skills/methodology-v2
pip install -e .
```

## 使用

```python
from methodology import ErrorClassifier, Crew, Monitor

# 錯誤分類
classifier = ErrorClassifier()
level = classifier.classify(error)

# Agent 協作
crew = Crew(agents, process="sequential")
result = crew.kickoff()

# 監控
monitor = Monitor()
monitor.register_agent(agent)
health = monitor.get_health_score(agent_id)
```

## 核心類別

| 類別 | 功能 |
|------|------|
| ErrorClassifier | L1-L4 錯誤分類 |
| ErrorHandler | 錯誤處理 |
| TaskLifecycle | 任務生命週期 |
| QualityGate | 品質把關 |
| Crew | Agent 團隊協作 |
| Monitor | 健康監控 |

## 版本

v2.1.0
