# P2P Team Config - SKILL.md

JSON 驅動的 P2P 團隊配置系統

## 概述

`P2PTeamConfig` 讓你用 JSON 檔案定義、管理 P2P 架構的多 Agent 團隊。所有設定集中在一個 JSON，適用於：
- 定義團隊角色與權限
- 配置 Agent 間通訊方式
- 管理子 Agent 嵌套深度

---

## 核心類別

### `P2PTeamSettings` - 團隊全域設定

```python
@dataclass
class P2PTeamSettings:
    mode: str = "peer-to-peer"        # "peer-to-peer" or "master-sub"
    max_spawn_depth: int = 2           # 子 Agent 嵌套上限 (0-5)
    allow_agent_to_agent: bool = True  # 是否允許 Agent 互相通訊
    message_queue_size: int = 100       # 訊息佇列大小
```

### `TeamMember` - 團隊成員

```python
@dataclass
class TeamMember:
    agent_id: str                      # 唯一 ID (如 "programmer-agent")
    role: str                          # 角色名 (如 "Developer")
    peer_memory_enabled: bool = True   # 是否啟用獨立記憶
    can_spawn_subagent: bool = True    # 是否可產生子 Agent
```

### `P2PTeamConfig` - 設定檔管理器

```python
class P2PTeamConfig:
    @classmethod
    def from_json(cls, path: str) -> "P2PTeamConfig"
    @classmethod
    def from_dict(cls, data: dict) -> "P2PTeamConfig"
    def to_dict(self) -> dict
    def validate(self) -> bool
    def get_member(self, agent_id: str) -> TeamMember | None
    def list_agents(self) -> List[dict]
    def summary(self) -> dict
```

---

## JSON 格式

```json
{
  "team": {
    "teamId": "research-dev-team",
    "mode": "peer-to-peer",
    "settings": {
      "maxSpawnDepth": 2,
      "allowAgentToAgent": true,
      "messageQueueSize": 100
    }
  },
  "members": [
    {
      "agentId": "programmer-agent",
      "role": "Developer",
      "canSpawnSubagent": true,
      "peerMemoryEnabled": true
    }
  ]
}
```

### 欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `team.teamId` | string | 團隊唯一識別碼 |
| `team.mode` | string | `peer-to-peer` 或 `master-sub` |
| `team.settings.maxSpawnDepth` | int | 0-5，預設 2 |
| `team.settings.allowAgentToAgent` | bool | 是否允許 Agent 直接通訊 |
| `members[].agentId` | string | 成員唯一 ID |
| `members[].role` | string | 角色描述 |
| `members[].canSpawnSubagent` | bool | 是否可產生子 Agent |
| `members[].peerMemoryEnabled` | bool | 是否啟用獨立記憶 |

---

## CLI 使用方式

```bash
# 初始化團隊（從 JSON 載入）
python cli.py p2p init team-config.json

# 查看團隊狀態
python cli.py p2p status

# 列出所有成員
python cli.py p2p list
```

---

## 使用範例

### 基本載入與驗證

```python
from p2p_team_config import P2PTeamConfig

# 從 JSON 檔案載入
config = P2PTeamConfig.from_json("team-config.json")

# 驗證設定
if not config.validate():
    raise ValueError("Invalid team config")

# 取得摘要
print(config.summary())
```

### 透過程式碼建立

```python
from p2p_team_config import P2PTeamConfig, TeamMember, P2PTeamSettings, TeamMeta

config = P2PTeamConfig(
    team_meta=TeamMeta(team_id="my-team"),
    settings=P2PTeamSettings(mode="peer-to-peer", max_spawn_depth=3),
    members=[
        TeamMember(agent_id="dev-agent", role="Developer"),
        TeamMember(agent_id="reviewer-agent", role="CodeReviewer"),
    ]
)

# 匯出為 JSON
import json
print(json.dumps(config.to_dict(), indent=2))
```

### 查詢成員

```python
# 依 ID 查詢
member = config.get_member("dev-agent")
if member:
    print(f"{member.role} can spawn: {member.can_spawn_subagent}")

# 列出所有 Agent（不含內部細節）
for agent in config.list_agents():
    print(f"{agent['agentId']} - {agent['role']}")
```

---

## 驗證規則

`validate()` 檢查：
- ✅ `teamId` 非空
- ✅ `mode` 為 `peer-to-peer` 或 `master-sub`
- ✅ `maxSpawnDepth` 在 0-5 範圍內
- ✅ 成員數 > 0
- ✅ 成員 `agentId` 不重複且非空

---

## 與 Agent Team 的差異

| 特性 | `agent_team.py` | `p2p_team_config.py` |
|------|----------------|---------------------|
| 資料格式 | Python dataclass | JSON 檔案 |
| 用途 | 執行期 Agent 管理 | 靜態團隊定義 |
| 特色 | 角色枚舉、權限系統 | 設定即代碼、易於版本控制 |
| 儲存 | 記憶體 | JSON 檔案 |
| CLI 整合 | 有 | **新增** |

兩者可以同時使用：`p2p_team_config.json` 定義團隊結構，`agent_team.py` 負責執行期的 Agent 協作。
