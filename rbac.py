#!/usr/bin/env python3
"""
RBAC Module - 角色權限管理

多成員協作時的權限控制
"""

import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Role(Enum):
    """角色"""
    ADMIN = "admin"
    PROJECT_MANAGER = "pm"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    GUEST = "guest"


class Permission(Enum):
    """權限"""
    # 任務管理
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"
    
    # Sprint 管理
    SPRINT_CREATE = "sprint:create"
    SPRINT_MANAGE = "sprint:manage"
    SPRINT_VIEW = "sprint:view"
    
    # 預算管理
    BUDGET_VIEW = "budget:view"
    BUDGET_MANAGE = "budget:manage"
    
    # 系統管理
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"


# 角色預設權限
ROLE_PERMISSIONS = {
    Role.ADMIN: set(Permission),
    Role.PROJECT_MANAGER: {
        Permission.TASK_CREATE,
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.TASK_DELETE,
        Permission.TASK_ASSIGN,
        Permission.SPRINT_CREATE,
        Permission.SPRINT_MANAGE,
        Permission.SPRINT_VIEW,
        Permission.BUDGET_VIEW,
        Permission.BUDGET_MANAGE,
    },
    Role.DEVELOPER: {
        Permission.TASK_READ,
        Permission.TASK_UPDATE,
        Permission.SPRINT_VIEW,
        Permission.BUDGET_VIEW,
    },
    Role.VIEWER: {
        Permission.TASK_READ,
        Permission.SPRINT_VIEW,
        Permission.BUDGET_VIEW,
    },
    Role.GUEST: {
        Permission.TASK_READ,
        Permission.SPRINT_VIEW,
    },
}


@dataclass
class User:
    """用戶"""
    id: str
    name: str
    email: str
    role: Role = Role.VIEWER
    team: str = None
    permissions: Set[Permission] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    
    def has_permission(self, permission: Permission) -> bool:
        """檢查是否有權限"""
        if self.permissions:
            return permission in self.permissions
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def grant_permission(self, permission: Permission):
        """授予權限"""
        self.permissions.add(permission)
    
    def revoke_permission(self, permission: Permission):
        """撤銷權限"""
        self.permissions.discard(permission)


@dataclass
class Team:
    """團隊"""
    id: str
    name: str
    members: List[str] = field(default_factory=list)  # user IDs
    roles: Dict[str, Role] = field(default_factory=dict)  # user_id -> role


class RBAC:
    """角色權限控制系統"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.teams: Dict[str, Team] = {}
        self.sessions: Dict[str, str] = {}  # session_id -> user_id
    
    def create_user(self, name: str, email: str, 
                   role: Role = Role.VIEWER,
                   team: str = None) -> User:
        """建立用戶"""
        user_id = f"user-{len(self.users) + 1}"
        
        user = User(
            id=user_id,
            name=name,
            email=email,
            role=role,
            team=team,
        )
        
        self.users[user_id] = user
        
        if team and team in self.teams:
            self.teams[team].members.append(user_id)
            self.teams[team].roles[user_id] = role
        
        return user
    
    def create_team(self, name: str, owner_id: str = None) -> Team:
        """建立團隊"""
        team_id = f"team-{len(self.teams) + 1}"
        
        team = Team(
            id=team_id,
            name=name,
        )
        
        self.teams[team_id] = team
        
        if owner_id:
            team.members.append(owner_id)
            team.roles[owner_id] = Role.PROJECT_MANAGER
        
        return team
    
    def assign_role(self, user_id: str, role: Role, team_id: str = None):
        """指派角色"""
        user = self.users.get(user_id)
        if not user:
            return
        
        user.role = role
        
        if team_id and team_id in self.teams:
            team = self.teams[team_id]
            if user_id not in team.members:
                team.members.append(user_id)
            team.roles[user_id] = role
    
    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """檢查權限"""
        user = self.users.get(user_id)
        if not user:
            return False
        
        return user.has_permission(permission)
    
    def require_permission(self, user_id: str, permission: Permission) -> bool:
        """要求權限 (否則拋出異常)"""
        if not self.check_permission(user_id, permission):
            raise PermissionError(f"User {user_id} lacks permission: {permission.value}")
        return True
    
    def get_user_tasks(self, user_id: str) -> List[str]:
        """取得用戶可見的任務"""
        user = self.users.get(user_id)
        if not user:
            return []
        
        # Admin 和 PM 可以看到所有任務
        if user.role in [Role.ADMIN, Role.PROJECT_MANAGER]:
            return ["*"]  # 表示所有任務
        
        # Developer 只能看到自己和團隊的任務
        if user.role == Role.DEVELOPER:
            return [f"task:team:{user.team}"]
        
        # Viewer 只能讀取
        return []
    
    def get_user_budget(self, user_id: str) -> Dict:
        """取得用戶預算權限"""
        user = self.users.get(user_id)
        if not user:
            return {"view": False, "manage": False}
        
        return {
            "view": user.has_permission(Permission.BUDGET_VIEW),
            "manage": user.has_permission(Permission.BUDGET_MANAGE),
        }
    
    def create_session(self, user_id: str) -> str:
        """建立 session"""
        session_id = f"sess-{datetime.now().timestamp()}"
        self.sessions[session_id] = user_id
        return session_id
    
    def get_session_user(self, session_id: str) -> Optional[User]:
        """取得 session 對應的用戶"""
        user_id = self.sessions.get(session_id)
        return self.users.get(user_id) if user_id else None
    
    def to_dict(self) -> Dict:
        """轉換為 Dict"""
        return {
            "users": {
                uid: {
                    "id": u.id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role.value,
                    "team": u.team,
                    "permissions": [p.value for p in u.permissions],
                }
                for uid, u in self.users.items()
            },
            "teams": {
                tid: {
                    "id": t.id,
                    "name": t.name,
                    "members": t.members,
                    "roles": {uid: r.value for uid, r in t.roles.items()},
                }
                for tid, t in self.teams.items()
            },
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    rbac = RBAC()
    
    # 建立團隊
    team = rbac.create_team("AI 開發團隊")
    print(f"Created team: {team.name}")
    
    # 建立用戶
    admin = rbac.create_user("老闆", "boss@example.com", Role.ADMIN)
    pm = rbac.create_user("PM 小美", "pm@example.com", Role.PROJECT_MANAGER, team.id)
    dev = rbac.create_user("工程師大明", "dev@example.com", Role.DEVELOPER, team.id)
    viewer = rbac.create_user("訪客", "guest@example.com", Role.VIEWER)
    
    print(f"\nUsers: {[u.name for u in rbac.users.values()]}")
    
    # 權限檢查
    print("\n=== Permission Check ===")
    print(f"Admin can delete tasks: {rbac.check_permission(admin.id, Permission.TASK_DELETE)}")
    print(f"Developer can delete tasks: {rbac.check_permission(dev.id, Permission.TASK_DELETE)}")
    print(f"Viewer can read tasks: {rbac.check_permission(viewer.id, Permission.TASK_READ)}")
    
    # 預算權限
    print("\n=== Budget Permissions ===")
    print(f"Admin budget: {rbac.get_user_budget(admin.id)}")
    print(f"Developer budget: {rbac.get_user_budget(dev.id)}")
    print(f"Viewer budget: {rbac.get_user_budget(viewer.id)}")
    
    # Session
    session = rbac.create_session(dev.id)
    session_user = rbac.get_session_user(session)
    print(f"\nSession user: {session_user.name if session_user else 'None'}")
