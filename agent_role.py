#!/usr/bin/env python3
"""
Agent Role - 統一角色定義系統

對標 CrewAI 的 Role-based 概念：
- 預設角色模板
- 角色繼承
- 權限範圍
- 技能標記

AI-native 實作，零額外負擔
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

@dataclass
class AgentRole:
    """
    Agent 角色定義
    
    對標 CrewAI 的 role-based 概念：
    - name: 角色名稱
    - role_type: 角色類型
    - goals: 目標描述
    - backstory: 背景故事
    - permissions: 權限列表
    - skills: 技能列表
    """
    role_id: str
    name: str
    role_type: RoleType
    goals: str
    backstory: str
    permissions: List[Permission] = field(default_factory=list)
    skills: List[Skill] = field(default_factory=list)
    parent_role: Optional[str] = None  # 角色繼承
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Permission) -> bool:
        """檢查是否有某權限"""
        return permission in self.permissions
    
    def add_skill(self, name: str, level: int = 3):
        """添加技能"""
        self.skills.append(Skill(name=name, level=level))
    
    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "role_type": self.role_type.value,
            "goals": self.goals,
            "backstory": self.backstory,
            "permissions": [p.value for p in self.permissions],
            "skills": [{"name": s.name, "level": s.level} for s in self.skills],
        }

class RoleRegistry:
    """角色註冊表"""
    
    # 預設角色工廠
    DEFAULT_ROLES = {
        "developer": AgentRole(
            role_id="role-dev",
            name="Developer",
            role_type=RoleType.DEVELOPER,
            goals="Write high-quality code",
            backstory="Experienced software engineer",
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
            skills=[Skill("coding", 5), Skill("debugging", 4)]
        ),
        "reviewer": AgentRole(
            role_id="role-review",
            name="Code Reviewer",
            role_type=RoleType.REVIEWER,
            goals="Ensure code quality and security",
            backstory="Senior engineer with security expertise",
            permissions=[Permission.READ, Permission.APPROVE],
            skills=[Skill("code-review", 5), Skill("security", 4)]
        ),
        "pm": AgentRole(
            role_id="role-pm",
            name="Project Manager",
            role_type=RoleType.PM,
            goals="Deliver projects on time and within budget",
            backstory="10 years project management experience",
            permissions=[Permission.READ, Permission.WRITE, Permission.APPROVE, Permission.DELETE],
            skills=[Skill("planning", 5), Skill("communication", 5)]
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
