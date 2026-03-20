#!/usr/bin/env python3
"""
Agent Team - Sub-agent 定義與團隊管理

定義 Agent 角色、權限、能力
"""

import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentRole(Enum):
    """Agent 角色"""
    ARCHITECT = "architect"      # 架構師：定義系統結構
    DEVELOPER = "developer"      # 開發者：寫代碼
    TESTER = "tester"           # 測試員：測試
    REVIEWER = "reviewer"       # 評審：品質把關
    PM = "pm"                   # 專案經理：協調
    RESEARCHER = "researcher"   # 研究員：研究
    DEVOPS = "devops"          # 運維：部署
    SECURITY = "security"       # 安全：審計


class AgentCapability(Enum):
    """Agent 能力"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    DEPLOYMENT = "deployment"
    SECURITY_AUDIT = "security_audit"
    COST_OPTIMIZATION = "cost_optimization"
    PERFORMANCE_ANALYSIS = "performance_analysis"


class AgentPermission(Enum):
    """Agent 權限"""
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"
    CODE_READ = "code:read"
    CODE_WRITE = "code:write"
    CODE_DELETE = "code:delete"
    DEPLOY = "deploy"
    VIEW_SECRETS = "secrets:read"
    MANAGE_USERS = "users:manage"


@dataclass
class AgentTool:
    """工具定義"""
    id: str
    name: str
    description: str
    input_schema: Dict = field(default_factory=dict)
    output_schema: Dict = field(default_factory=dict)


@dataclass
class AgentDefinition:
    """Agent 定義"""
    id: str
    name: str
    role: AgentRole
    description: str
    
    # 能力
    capabilities: Set[AgentCapability] = field(default_factory=set)
    
    # 權限
    permissions: Set[AgentPermission] = field(default_factory=set)
    
    # 系統提示詞
    system_prompt: str = ""
    
    # 可用工具
    tools: List[AgentTool] = field(default_factory=list)
    
    # 配置
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 限制
    max_concurrent_tasks: int = 3
    timeout_seconds: int = 300
    
    # 元數據
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    
    def has_capability(self, capability: AgentCapability) -> bool:
        return capability in self.capabilities
    
    def has_permission(self, permission: AgentPermission) -> bool:
        return permission in self.permissions


@dataclass
class AgentInstance:
    """Agent 實例"""
    definition_id: str
    instance_id: str
    name: str
    role: AgentRole
    
    # 狀態
    is_busy: bool = False
    current_task_id: str = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    
    # 統計
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
    # 上下文
    memory: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "instance_id": self.instance_id,
            "name": self.name,
            "role": self.role.value,
            "is_busy": self.is_busy,
            "current_task": self.current_task_id,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_active": self.last_active.isoformat(),
        }


class AgentTeam:
    """Agent 團隊管理器"""
    
    def __init__(self, team_id: str = None, name: str = "Default Team"):
        self.team_id = team_id or f"team-{datetime.now().timestamp()}"
        self.name = name
        
        # Agent 定義庫
        self.definitions: Dict[str, AgentDefinition] = {}
        
        # Agent 實例
        self.instances: Dict[str, AgentInstance] = {}
        
        # 預設模板
        self._load_default_definitions()
    
    def _load_default_definitions(self):
        """載入預設 Agent 定義"""
        
        # 架構師
        self.define_agent(
            name="Architect",
            role=AgentRole.ARCHITECT,
            description="系統架構師，負責定義系統結構和技術決策",
            capabilities={
                AgentCapability.ARCHITECTURE,
                AgentCapability.CODE_REVIEW,
            },
            permissions={
                AgentPermission.TASK_READ,
                AgentPermission.TASK_CREATE,
                AgentPermission.CODE_READ,
            },
            system_prompt="你是一位資深系統架構師，擅長設計可擴展、高性能的系統架構。"
        )
        
        # 開發者
        self.define_agent(
            name="Developer",
            role=AgentRole.DEVELOPER,
            description="全端開發者，負責實現功能",
            capabilities={
                AgentCapability.CODE_GENERATION,
                AgentCapability.CODE_REVIEW,
                AgentCapability.DOCUMENTATION,
            },
            permissions={
                AgentPermission.TASK_READ,
                AgentPermission.TASK_UPDATE,
                AgentPermission.CODE_READ,
                AgentPermission.CODE_WRITE,
            },
            system_prompt="你是一位全端開發者，擅長寫高質量、可維護的代碼。",
            max_concurrent_tasks=2
        )
        
        # 測試員
        self.define_agent(
            name="Tester",
            role=AgentRole.TESTER,
            description="QA 工程師，負責測試和品質把關",
            capabilities={
                AgentCapability.TESTING,
                AgentCapability.CODE_REVIEW,
            },
            permissions={
                AgentPermission.TASK_READ,
                AgentPermission.CODE_READ,
            },
            system_prompt="你是一位資深 QA 工程師，擅長設計全面的測試案例。"
        )
        
        # 評審
        self.define_agent(
            name="Reviewer",
            role=AgentRole.REVIEWER,
            description="代碼評審，負責審查代碼品質",
            capabilities={
                AgentCapability.CODE_REVIEW,
                AgentCapability.SECURITY_AUDIT,
            },
            permissions={
                AgentPermission.TASK_READ,
                AgentPermission.CODE_READ,
            },
            system_prompt="你是一位資深代碼評審，嚴格把關代碼品質和安全。"
        )
        
        # PM
        self.define_agent(
            name="PM",
            role=AgentRole.PM,
            description="專案經理，負責協調和管理",
            capabilities={
                AgentCapability.ARCHITECTURE,
                AgentCapability.CODE_REVIEW,
                AgentCapability.COST_OPTIMIZATION,
            },
            permissions={
                AgentPermission.TASK_CREATE,
                AgentPermission.TASK_READ,
                AgentPermission.TASK_UPDATE,
                AgentPermission.TASK_DELETE,
                AgentPermission.TASK_ASSIGN,
            },
            system_prompt="你是一位高效的專案經理，善於協調團隊和追蹤進度。"
        )
    
    def define_agent(self, name: str, role: AgentRole,
                    description: str = "",
                    capabilities: Set[AgentCapability] = None,
                    permissions: Set[AgentPermission] = None,
                    system_prompt: str = "",
                    model: str = "gpt-4o",
                    **kwargs) -> str:
        """定義新的 Agent"""
        definition_id = f"{role.value}-{name.lower().replace(' ', '-')}"
        
        definition = AgentDefinition(
            id=definition_id,
            name=name,
            role=role,
            description=description,
            capabilities=capabilities or set(),
            permissions=permissions or set(),
            system_prompt=system_prompt,
            model=model,
            **kwargs
        )
        
        self.definitions[definition_id] = definition
        return definition_id
    
    def create_instance(self, definition_id: str, name: str = None) -> AgentInstance:
        """創建 Agent 實例"""
        definition = self.definitions.get(definition_id)
        if not definition:
            raise ValueError(f"Definition {definition_id} not found")
        
        instance_id = f"{definition_id}-{len(self.instances) + 1}"
        
        instance = AgentInstance(
            definition_id=definition_id,
            instance_id=instance_id,
            name=name or definition.name,
            role=definition.role,
        )
        
        self.instances[instance_id] = instance
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[AgentInstance]:
        """取得 Agent 實例"""
        return self.instances.get(instance_id)
    
    def get_instances_by_role(self, role: AgentRole) -> List[AgentInstance]:
        """取得特定角色的所有實例"""
        return [i for i in self.instances.values() if i.role == role]
    
    def get_available_agent(self, role: AgentRole) -> Optional[AgentInstance]:
        """取得空閒的 Agent"""
        instances = self.get_instances_by_role(role)
        
        for instance in instances:
            if not instance.is_busy:
                return instance
        
        return None
    
    def assign_task(self, instance_id: str, task_id: str) -> bool:
        """指派任務給 Agent"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        definition = self.definitions.get(instance.definition_id)
        if not definition:
            return False
        
        # 檢查是否超過並發限制
        if instance.is_busy and instance.current_task_id:
            definition = self.definitions.get(instance.definition_id)
            if definition and instance.current_task_id:
                return False
        
        instance.is_busy = True
        instance.current_task_id = task_id
        instance.last_active = datetime.now()
        
        return True
    
    def complete_task(self, instance_id: str, success: bool = True):
        """完成任務"""
        instance = self.instances.get(instance_id)
        if not instance:
            return
        
        instance.is_busy = False
        instance.current_task_id = None
        instance.last_active = datetime.now()
        
        if success:
            instance.tasks_completed += 1
        else:
            instance.tasks_failed += 1
    
    def get_team_summary(self) -> Dict:
        """取得團隊摘要"""
        by_role = {}
        for role in AgentRole:
            instances = self.get_instances_by_role(role)
            if instances:
                by_role[role.value] = {
                    "count": len(instances),
                    "busy": sum(1 for i in instances if i.is_busy),
                    "available": sum(1 for i in instances if not i.is_busy),
                }
        
        total_completed = sum(i.tasks_completed for i in self.instances.values())
        total_failed = sum(i.tasks_failed for i in self.instances.values())
        
        return {
            "team_id": self.team_id,
            "name": self.name,
            "total_agents": len(self.instances),
            "by_role": by_role,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
        }
    
    def generate_report(self) -> str:
        """生成團隊報告"""
        summary = self.get_team_summary()
        
        report = f"""
# 🤖 Agent 團隊報告

## {self.name}

| 指標 | 數值 |
|------|------|
| 總 Agent 數 | {summary['total_agents']} |
| 總完成任務 | {summary['total_tasks_completed']} |
| 失敗任務 | {summary['total_tasks_failed']} |

---

## 按角色

| 角色 | 總數 | 空閒 | 工作中 |
|------|------|------|--------|
"""
        
        for role, data in summary['by_role'].items():
            report += f"| {role} | {data['count']} | {data['available']} | {data['busy']} |\n"
        
        report += f"""

## Agent 實例

| 名稱 | 角色 | 狀態 | 已完成 | 失敗 |
|------|------|------|--------|------|
"""
        
        for instance in self.instances.values():
            status = "🔄 工作中" if instance.is_busy else "✅ 空閒"
            report += f"| {instance.name} | {instance.role.value} | {status} | {instance.tasks_completed} | {instance.tasks_failed} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    team = AgentTeam(name="AI 開發團隊")
    
    print("=== Default Definitions ===")
    for def_id, definition in team.definitions.items():
        print(f"{def_id}: {definition.name} ({definition.role.value})")
    
    print("\n=== Creating Instances ===")
    
    # 創建各角色實例
    architect = team.create_instance("architect-architect", "小架")
    dev1 = team.create_instance("developer-developer", "大明")
    dev2 = team.create_instance("developer-developer", "小明")
    tester = team.create_instance("tester-tester", "小測")
    reviewer = team.create_instance("reviewer-reviewer", "小評")
    
    print(f"Created: {architect.name}, {dev1.name}, {dev2.name}, {tester.name}, {reviewer.name}")
    
    # 指派任務
    print("\n=== Assigning Tasks ===")
    team.assign_task(architect.instance_id, "task-1")
    team.assign_task(dev1.instance_id, "task-2")
    
    # 團隊摘要
    print("\n=== Team Summary ===")
    summary = team.get_team_summary()
    print(f"Total agents: {summary['total_agents']}")
    print(f"By role: {summary['by_role']}")
    
    # 完成任務
    team.complete_task(architect.instance_id, success=True)
    team.complete_task(dev1.instance_id, success=True)
    
    # 報告
    print("\n=== Report ===")
    print(team.generate_report())
