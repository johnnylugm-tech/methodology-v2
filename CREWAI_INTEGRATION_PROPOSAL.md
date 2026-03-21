# CrewAI 設計優點整合提案

> 目標：將 CrewAI 的設計優點吸收到 methodology-v2，無需引入 CrewAI 依賴

## 概述

| 項目 | 內容 |
|------|------|
| **提案日期** | 2026-03-22 |
| **改動風險** | 低（向後相容） |
| **影響範圍** | 局部增量新增 |
| **實現版本** | v5.8.0 |

---

## Point 1: Agent 定義方式 (role/goal/backstory)

### 現況 (agent_spawner.py)

```python
@dataclass
class SpawnRequest:
    role: str
    task_id: str
    task_description: str
    # 缺乏 goal、backstory
```

### 改進方案

**在 agent_spawner.py 新增：**

```python
@dataclass
class AgentPersona:
    """
    CrewAI 風格的 Agent 人格定義
    賦予 Agent 更豐富的角色內涵
    """
    role: str           # "Researcher", "Writer", "Developer"
    goal: str           # "Find latest AI trends"
    backstory: str      # "You are a senior research analyst..."
    
    def to_prompt(self) -> str:
        """轉換為 LLM prompt"""
        return f"You are a {self.role}. Your goal is: {self.goal}. {self.backstory}"
```

**更新 SpawnRequest：**

```python
@dataclass
class SpawnRequest:
    # ... 現有欄位保持不變 ...
    persona: Optional[AgentPersona] = None  # 新增：可選的人格
    tools: List[Any] = field(default_factory=list)  # 新增：工具列表
```

---

## Point 2: Tool 接入模式

### 現況

每個 Tool 需手寫 50+ 行 adapter，無統一標準。

### 改進方案

**新增檔案：tool_registry.py**

```python
class BaseTool(ABC):
    """工具基類"""
    name: str
    description: str
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass


class ToolRegistry:
    """
    統一工具註冊中心
    
    使用範例：
        tools = [ToolRegistry.slack(channel="#team"), ToolRegistry.gmail()]
    """
    
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
```

### 內建工具

| 工具 | 方法 | 用途 |
|------|------|------|
| slack | `ToolRegistry.slack(channel="#team")` | 發送 Slack 訊息 |
| gmail | `ToolRegistry.gmail()` | 發送 Gmail |
| notion | `ToolRegistry.notion(page_id="xxx")` | Notion 頁面操作 |
| github | `ToolRegistry.github(repo="org/proj")` | GitHub 操作 |
| search | `ToolRegistry.search()` | 網頁搜尋 |
| browser | `ToolRegistry.browser()` | 瀏覽器自動化 |
| jira | `ToolRegistry.jira(project="PROJ")` | Jira 操作 |
| trello | `ToolRegistry.trello(board="Board")` | Trello 操作 |

---

## Point 3: 更新 Agent 類別

### 修改 agent_team.py

```python
from agent_spawner import AgentPersona  # 新增導入

@dataclass
class AgentInstance:
    # ... 現有欄位 ...
    
    # === 新增欄位 ===
    persona: Optional[AgentPersona] = None  # Agent 人格
    tools: List[Any] = field(default_factory=list)  # 工具列表
    
    def get_system_prompt(self) -> str:
        """取得系統 prompt"""
        base = self.role.value + " Agent - " + self.name
        if self.persona:
            return self.persona.to_prompt()
        return base
```

---

## 實作計劃

### Phase 1: AgentPersona (30 分鐘)

| 檔案 | 改動 |
|------|------|
| `agent_spawner.py` | +30 行 (新增 AgentPersona class) |

### Phase 2: ToolRegistry (60 分鐘)

| 檔案 | 改動 |
|------|------|
| `tool_registry.py` | 新增檔案 (~150 行) |

### Phase 3: Agent 更新 (20 分鐘)

| 檔案 | 改動 |
|------|------|
| `agent_team.py` | +20 行 (新增 persona/tools 欄位) |

---

## 向後相容性

**確保現有代碼不受影響：**

```python
# 舊寫法 - 完全相容
SpawnRequest(role="dev", task_id="123")

# 新寫法 - 可選增強
SpawnRequest(
    role="dev", 
    task_id="123",
    persona=AgentPersona(
        role="Developer",
        goal="Write clean code",
        backstory="Senior dev with 10 years..."
    ),
    tools=[ToolRegistry.github(repo="org/project")]
)
```

---

## 預期效益

| 維度 | 改善前 | 改善後 |
|------|--------|--------|
| Agent 定義 | role + description | role + goal + backstory |
| 工具接入 | 50+ 行手寫 | 1 行呼叫 |
| 向後相容 | - | 100% 相容 |
| 代碼量新增 | - | ~200 行 |

---

## 測試驗證

```python
# Test 1: AgentPersona
persona = AgentPersona(
    role="Researcher",
    goal="Find AI trends",
    backstory="Expert in ML"
)
assert persona.to_prompt() == "You are a Researcher. Your goal is: Find AI trends. Expert in ML"

# Test 2: ToolRegistry
slack = ToolRegistry.slack(channel="#team")
assert slack.name == "slack"
assert slack.channel == "#team"

# Test 3: 向後相容
req = SpawnRequest(role="dev", task_id="123")
assert req.persona is None
assert req.tools == []
```

---

## 結論

- **改動範圍**：局部增量，不大幅修改現有邏輯
- **風險**：低（向後 100% 相容）
- **價值**：吸收 CrewAI 設計優點，提升易用性
- **實現狀態**：✅ 已實現 (v5.8.0)
