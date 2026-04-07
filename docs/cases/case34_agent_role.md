# 案例 34：統一角色定義 (Agent Role)

## 情境描述

對標 CrewAI 的 Role-based Agent 概念，實現統一的 Agent 角色定義系統。包含預設角色模板、角色繼承、權限範圍和技能標記。

---

## 案例 34.1：基本角色定義

### 背景
每個 Agent 需要明確的角色定義，包括角色類型、目標、背景故事、權限和技能。

### 使用方式

```python
from agent_role import (
    AgentRole, 
    RoleType, 
    Permission, 
    Skill,
    RoleRegistry
)

# 建立 Developer 角色
dev_role = AgentRole(
    role_id="role-dev-001",
    name="Senior Developer",
    role_type=RoleType.DEVELOPER,
    goals="Write high-quality, maintainable code",
    backstory="10 years of software engineering experience",
    permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
    skills=[Skill("python", 5), Skill("system-design", 4)]
)

# 檢查權限
assert dev_role.has_permission(Permission.WRITE) == True
assert dev_role.has_permission(Permission.DELETE) == False

# 添加技能
dev_role.add_skill("go", 3)

# 轉換為字典
role_dict = dev_role.to_dict()
```

### 輸出
```json
{
  "role_id": "role-dev-001",
  "name": "Senior Developer",
  "role_type": "developer",
  "goals": "Write high-quality, maintainable code",
  "backstory": "10 years of software engineering experience",
  "permissions": ["read", "write", "execute"],
  "skills": [{"name": "python", "level": 5}, {"name": "system-design", "level": 4}, {"name": "go", "level": 3}]
}
```

---

## 案例 34.2：角色註冊表

### 背景
使用 RoleRegistry 統一管理所有角色，支援預設角色和自定義角色。

### 使用方式

```python
from agent_role import RoleRegistry, RoleType, AgentRole, Permission, Skill

# 初始化（會自動載入預設角色）
registry = RoleRegistry()

# 註冊新角色
security_role = AgentRole(
    role_id="role-sec",
    name="Security Engineer",
    role_type=RoleType.SECURITY,
    goals="Ensure system security",
    backstory="Cybersecurity expert with 5 years experience",
    permissions=[Permission.READ, Permission.APPROVE],
    skills=[Skill("security-audit", 5), Skill("penetration-testing", 4)]
)
registry.register(security_role)

# 取得角色
role = registry.get("role-sec")
print(role.name)  # Security Engineer

# 按類型列出角色
devs = registry.list_by_type(RoleType.DEVELOPER)
print(len(devs))  # 1 (預設 developer)
```

### 預設角色
| 角色 | ID | 權限 | 技能 |
|------|-----|------|------|
| Developer | role-dev | read, write, execute | coding(5), debugging(4) |
| Code Reviewer | role-review | read, approve | code-review(5), security(4) |
| Project Manager | role-pm | read, write, approve, delete | planning(5), communication(5) |

---

## 案例 34.3：角色繼承

### 背景
支援角色繼承，子角色可以擴展父角色的權限和技能。

### 使用方式

```python
from agent_role import AgentRole, RoleType, Permission, Skill

# 建立父角色
base_dev = AgentRole(
    role_id="role-base-dev",
    name="Base Developer",
    role_type=RoleType.DEVELOPER,
    goals="Write code",
    backstory="Developer",
    permissions=[Permission.READ, Permission.WRITE],
    skills=[Skill("coding", 3)]
)

# 建立子角色（繼承）
senior_dev = AgentRole(
    role_id="role-senior-dev",
    name="Senior Developer",
    role_type=RoleType.DEVELOPER,
    goals="Write high-quality code and mentor others",
    backstory="Experienced developer",
    permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
    skills=[Skill("coding", 5), Skill("mentoring", 4)],
    parent_role="role-base-dev"  # 繼承
)

# 組合權限（父 + 子）
all_permissions = set(base_dev.permissions) | set(senior_dev.permissions)
print([p.value for p in all_permissions])
# ['read', 'write', 'execute']
```

---

## 對比 CrewAI

| 概念 | CrewAI | 本系統 |
|------|--------|--------|
| 角色定義 | `Agent(role=...)` | `AgentRole` dataclass |
| 角色類型 | 自由字串 | `RoleType` 枚舉 |
| 目標 | `goal` 欄位 | `goals` 欄位 |
| 背景故事 | `backstory` 欄位 | `backstory` 欄位 |
| 權限控制 | 無內建 | `Permission` 枚舉 + `has_permission()` |
| 技能標記 | `tools` 列表 | `Skill` dataclass + 等級 |
| 角色註冊 | 無 | `RoleRegistry` 類 |
| 角色繼承 | 無 | `parent_role` 欄位 |

---

## 總結

`agent_role.py` 提供了：
- **統一角色模型**：對標 CrewAI 的 role-based 概念
- **權限控制**：細粒度的權限枚舉和檢查
- **技能標記**：帶等级的技能系統
- **角色註冊表**：集中管理所有角色
- **角色繼承**：支援父子角色擴展
