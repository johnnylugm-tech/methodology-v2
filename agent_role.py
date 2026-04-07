#!/usr/bin/env python3
"""
Agent Role - 統一角色定義系統

對標 CrewAI 的 Role-based 概念：
- 預設角色模板
- 角色繼承
- 權限範圍
- 技能標記

AI-native 實作，零額外負擔

v5.62 (2026-03-27): 新增 Tester/Architect + 整合 ACTOR/CRITIC Prompt
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable
from datetime import datetime

class RoleType(Enum):
    """預設角色類型"""
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DEVOPS = "devops"
    SECURITY = "security"
    PM = "pm"
    ARCHITECT = "architect"
    CUSTOM = "custom"

class Permission(Enum):
    """權限枚舉"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    APPROVE = "approve"
    DELETE = "delete"
    ADMIN = "admin"

@dataclass
class Skill:
    """技能標記"""
    name: str
    level: int  # 1-5
    certifications: List[str] = field(default_factory=list)

# ============================================================================
# ACTOR_PROMPT - 執行者 System Prompt (強調嚴謹)
# ============================================================================
ACTOR_PROMPT = """你是一個極度嚴謹的執行者。
你的原則：
- 禁止省略任何步驟，必須展示完整的推理過程。
- 禁止使用「以此類推」或「略過細節」等字眼。
- 如果不確定，必須明確標註『不確定』而非編造。
- 每個結論必須有證據支持，不能憑感覺猜測。"""

# ============================================================================
# CRITIC_PROMPT - 審查者 System Prompt (專門抓偷懶)
# ============================================================================
CRITIC_PROMPT = """你是一個挑剔的審查員，專門尋找執行者輸出中的漏洞。
請檢查以下事項：
1. 他是否因為偷懶而跳過了計算或邏輯步驟？
2. 他是否在自我感覺良好地編造事實？
3. 他的語氣是否過於自信但缺乏證據？
4. 他是否有遺漏任何關鍵步驟？
5. 他的推論是否有邏輯漏洞？

如果你發現任何問題，請給予尖銳的修正建議。
如果完美，請回覆 [PASS]。"""

@dataclass
class AgentRole:
    """
    Agent 角色定義
    
    對標 CrewAI 的 role-based 概念：
    - name: 角色名稱
    - role_type: 角色類型
    - goals: 目標描述
    - backstory: 背景故事（含 System Prompt）
    - permissions: 權限列表
    - skills: 技能列表
    - system_prompt: 專屬 System Prompt（覆蓋默認）
    """
    role_id: str
    name: str
    role_type: RoleType
    goals: str
    backstory: str
    permissions: List[Permission] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    system_prompt: str = ""  # 可選的專屬 System Prompt
    parent_role: Optional[str] = None  # 角色繼承
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Permission) -> bool:
        """檢查是否有某權限"""
        return permission in self.permissions
    
    def add_skill(self, name: str, level: int = 3):
        """添加技能"""
        self.skills.append(Skill(name=name, level=level))
    
    def get_system_prompt(self) -> str:
        """取得完整的 System Prompt"""
        if self.system_prompt:
            return self.system_prompt
        # 默認行為：如果是 Developer 用 ACTOR，如果是 Reviewer 用 CRITIC
        if self.role_type == RoleType.DEVELOPER:
            return ACTOR_PROMPT
        elif self.role_type == RoleType.REVIEWER:
            return CRITIC_PROMPT
        return ""
    
    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "role_type": self.role_type.value,
            "goals": self.goals,
            "backstory": self.backstory,
            "permissions": [p.value for p in self.permissions],
            "skills": [{"name": s.name, "level": s.level} for s in self.skills],
            "system_prompt": self.get_system_prompt(),
        }

class RoleRegistry:
    """角色註冊表"""
    
    # ==========================================================================
    # 預設角色工廠（完整人格設定）
    # ==========================================================================
    DEFAULT_ROLES = {
        "developer": AgentRole(
            role_id="role-dev",
            name="Developer",
            role_type=RoleType.DEVELOPER,
            goals="Write high-quality code following strict methodology",
            backstory="""你是一個極度嚴謹的軟體工程師。
你的工作原則：
- 遵循 methodology-v2 的完整開發流程
- 每個 Phase 都要通過 Quality Gate
- 記錄所有「自主決定」的決策
- 禁止跳過任何步驟

你使用 ACTOR_PROMPT 作為行為準則。""",
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
            skills=[Skill("coding", 5), Skill("debugging", 4), Skill("methodology", 5)],
            system_prompt=ACTOR_PROMPT  # 強制執行者嚴謹模式
        ),
        "reviewer": AgentRole(
            role_id="role-review",
            name="Code Reviewer",
            role_type=RoleType.REVIEWER,
            goals="Ensure code quality, security, and methodology compliance",
            backstory="""你是一個挑剔的高級工程師，專門尋找開發者輸出中的漏洞。
你的工作原則：
- 檢查是否有偷懶或遺漏
- 驗證是否遵循 methodology-v2
- 確保每個 Phase 都有 Quality Gate 記錄
- 找出邏輯漏洞和安全問題

你使用 CRITIC_PROMPT 作為審查準則。""",
            permissions=[Permission.READ, Permission.APPROVE],
            skills=[Skill("code-review", 5), Skill("security", 4), Skill("methodology", 5)],
            system_prompt=CRITIC_PROMPT  # 強制審查者挑剔模式
        ),
        "tester": AgentRole(
            role_id="role-test",
            name="QA Engineer",
            role_type=RoleType.TESTER,
            goals="Verify functionality, catch bugs, ensure quality",
            backstory="""你是一個細心的 QA 工程師，專門找出系統中的缺陷。
你的工作原則：
- 執行完整的測試覆蓋（單元/整合/系統測試）
- 不放過任何可能的邊界條件
- 記錄所有失敗的測試案例
- 驗證開發者的修復是否完整

你需要同時具備執行者的嚴謹（ACTOR）和審查者的挑剔（CRITIC）。""",
            permissions=[Permission.READ, Permission.EXECUTE],
            skills=[Skill("testing", 5), Skill("automation", 4), Skill("debugging", 4)],
            system_prompt=ACTOR_PROMPT  # 測試需要嚴謹
        ),
        "architect": AgentRole(
            role_id="role-arch",
            name="System Architect",
            role_type=RoleType.ARCHITECT,
            goals="Design scalable, maintainable systems",
            backstory="""你是一個資深的系統架構師，專門設計可擴展和可維護的系統。
你的工作原則：
- 確保架構符合未來擴展需求
- 平衡技術實現和商業價值
- 識別潛在的技術風險
- 驗證設計是否符合最佳實踐

你需要用 CRITIC_PROMPT 審查自己的設計，確保沒有缺陷。""",
            permissions=[Permission.READ, Permission.WRITE, Permission.APPROVE],
            skills=[Skill("architecture", 5), Skill("performance", 4), Skill("scalability", 5)],
            system_prompt=CRITIC_PROMPT  # 架構需要審查
        ),
        "pm": AgentRole(
            role_id="role-pm",
            name="Project Manager",
            role_type=RoleType.PM,
            goals="Deliver projects on time and within budget",
            backstory="10 years project management experience. Expert in agile methodologies and stakeholder communication.",
            permissions=[Permission.READ, Permission.WRITE, Permission.APPROVE, Permission.DELETE],
            skills=[Skill("planning", 5), Skill("communication", 5), Skill("risk-management", 4)],
        ),
    }
    
    def __init__(self):
        self.roles: Dict[str, AgentRole] = {}
        for name, role in self.DEFAULT_ROLES.items():
            self.roles[name] = role
    
    def register(self, role: AgentRole):
        """註冊角色"""
        self.roles[role.role_id] = role
    
    def get(self, role_id: str) -> Optional[AgentRole]:
        """取得角色"""
        return self.roles.get(role_id)
    
    def list_by_type(self, role_type: RoleType) -> List[AgentRole]:
        """按類型列出角色"""
        return [r for r in self.roles.values() if r.role_type == role_type]
    
    def list_all(self) -> Dict[str, AgentRole]:
        """列出所有角色"""
        return self.roles.copy()


# ============================================================================
# 便捷函數
# ============================================================================

def get_role(role_id: str) -> Optional[AgentRole]:
    """取得角色（便捷函數）"""
    registry = RoleRegistry()
    return registry.get(role_id)

def get_developer() -> AgentRole:
    """取得 Developer 角色（含 ACTOR_PROMPT）"""
    return get_role("developer")

def get_reviewer() -> AgentRole:
    """取得 Reviewer 角色（含 CRITIC_PROMPT）"""
    return get_role("reviewer")

def get_tester() -> AgentRole:
    """取得 Tester 角色"""
    return get_role("tester")

def get_architect() -> AgentRole:
    """取得 Architect 角色"""
    return get_role("architect")

def create_team(role_ids: List[str]) -> List[AgentRole]:
    """建立團隊（多個角色）"""
    registry = RoleRegistry()
    return [registry.get(rid) for rid in role_ids if registry.get(rid)]