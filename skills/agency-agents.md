# SKILL.md - Agency Agents

> 下一代開源 Agent 框架 (62,549 ⭐)
> 
> **一句话**：讓 AI Agent 能自主決策、協作、執行的開源框架

---

## 一句话总结

Agency Agents 是一個讓多個 AI Agent 能夠自主協作、規劃和執行的開源框架，強調「Agent 之間的溝通和任務分配」。

---

## 核心概念

| 概念 | 說明 |
|------|------|
| **Agent** | 獨立運算的 AI 個體，有自己的目標和行為 |
| **Agency** | Agent 協作網路，Agent 之間可以溝通和協調 |
| **Supervisor** | 監督 Agent，負責任務分配 |
| **Executor** | 執行 Agent，負責具體操作 |

---

## 架構特點

```
┌─────────────────┐
│   Supervisor    │ ← 任務分配者
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│Agent 1│ │Agent 2│ ← 執行者
└───────┘ └───────┘
```

### 關鍵特性

1. **自主規劃** - Agent 自己決定下一步要做什麼
2. **協作溝通** - Agent 之間可以交換訊息
3. **任務分解** - 複雜任務自動拆分給多個 Agent
4. **容錯機制** - 單一 Agent 失敗不會影響整體

---

## 安裝方式

```bash
pip install agency-agents

# 或從源碼
git clone https://github.com/agency-agents/agency-agents
cd agency-agents
pip install -e .
```

---

## 使用範例

```python
from agency import Agent, Agency

# 定義 Agent
researcher = Agent(name="researcher", role="搜尋資訊")
writer = Agent(name="writer", role="撰寫報告")

# 建立 Agency
agency = Agency([researcher, writer])

# 執行任務
result = agency.run("研究 AI 趨勢並撰寫報告")
```

---

## 與其他框架比較

| 框架 | 特色 | 適用場景 |
|------|------|----------|
| **Agency Agents** | 多 Agent 協作、自主決策 | 複雜任務、多角色協作 |
| **LangChain** | 鏈式調用、工具整合 | 單一流程自動化 |
| **CrewAI** | 角色扮演、任務分工 | 結構化工作流程 |
| **AutoGen** | 多代理對話、可視化 | 實驗和原型 |

---

## 應用場景

1. **研究助理** - 多個 Agent 分工蒐集資訊、分析、寫作
2. **程式開發團隊** - 規劃師、開發者、測試員協作
3. **客服系統** - 分類 Agent 回覆Agent 串聯
4. **數據分析** - 收集、清洗、分析、視覺化分工

---

## 資源

- GitHub：https://github.com/agency-agents/agency-agents
- 文件：https://docs.agency-agents.io

---

*建立日期：2026-03-26*