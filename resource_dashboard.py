"""
Resource Dashboard - 資源清單視覺化

提供統一的資源視圖，整合：
- 團隊成員與技能
- 工具與系統
- API 與外部服務
- 基礎設施
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ResourceType(Enum):
    """資源類型"""
    TEAM_MEMBER = "team_member"
    TOOL = "tool"
    API = "api"
    INFRASTRUCTURE = "infrastructure"
    DATA_SOURCE = "data_source"
    EXTERNAL_SERVICE = "external_service"


class ResourceStatus(Enum):
    """資源狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    UNKNOWN = "unknown"


class SkillLevel(Enum):
    """技能等級"""
    EXPERT = "expert"        # 專家
    ADVANCED = "advanced"    # 進階
    INTERMEDIATE = "intermediate"  # 中級
    BEGINNER = "beginner"   # 初級
    AWARENESS = "awareness"  # 了解


@dataclass
class Resource:
    """資源"""
    id: str
    name: str
    type: ResourceType
    status: ResourceStatus = ResourceStatus.ACTIVE
    
    # 描述
    description: str = ""
    owner: str = ""
    
    # 使用資訊
    cost: float = 0.0  # 每月成本
    usage_count: int = 0  # 被使用次數
    
    # 時間戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 標籤
    tags: List[str] = field(default_factory=list)
    
    # 元資料
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def status_icon(self) -> str:
        icons = {
            ResourceStatus.ACTIVE: "🟢",
            ResourceStatus.INACTIVE: "⚪",
            ResourceStatus.MAINTENANCE: "🟡",
            ResourceStatus.DEPRECATED: "🔴",
            ResourceStatus.UNKNOWN: "❓",
        }
        return icons.get(self.status, "❓")
    
    @property
    def type_icon(self) -> str:
        icons = {
            ResourceType.TEAM_MEMBER: "👤",
            ResourceType.TOOL: "🔧",
            ResourceType.API: "🔌",
            ResourceType.INFRASTRUCTURE: "🏗️",
            ResourceType.DATA_SOURCE: "📊",
            ResourceType.EXTERNAL_SERVICE: "☁️",
        }
        return icons.get(self.type, "📦")


@dataclass
class TeamMember:
    """團隊成員"""
    resource_id: str
    name: str
    role: str
    
    # 技能
    skills: Dict[str, SkillLevel] = field(default_factory=dict)
    
    # 可用性
    availability: float = 1.0  # 0-1, 1 = 100%
    capacity: float = 40.0  # 每週小時數
    
    # 聯絡
    email: str = ""
    timezone: str = ""
    
    @property
    def skill_summary(self) -> str:
        levels = {
            SkillLevel.EXPERT: "🟢",
            SkillLevel.ADVANCED: "🔵",
            SkillLevel.INTERMEDIATE: "🟡",
            SkillLevel.BEGINNER: "⚪",
            SkillLevel.AWARENESS: "○",
        }
        return ", ".join([f"{s}:{levels.get(l, '?')[0]}" for s, l in self.skills.items()])


class ResourceDashboard:
    """資源儀表板"""
    
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.team_members: Dict[str, TeamMember] = {}
        self._setup_defaults()
    
    def _setup_defaults(self):
        """設定預設資源"""
        # 預設工具
        self.add_resource(
            id="openclaw",
            name="OpenClaw",
            type=ResourceType.TOOL,
            description="AI Agent 框架",
            owner="DevOps",
            cost=0,
            tags=["ai", "agent", "framework"]
        )
        
        self.add_resource(
            id="github",
            name="GitHub",
            type=ResourceType.TOOL,
            description="程式碼托管與協作",
            owner="DevOps",
            cost=0,
            tags=["git", "code", "ci"]
        )
        
        self.add_resource(
            id="slack",
            name="Slack",
            type=ResourceType.TOOL,
            description="團隊溝通",
            owner="IT",
            cost=15,
            tags=["communication", "chat"]
        )
        
        # 預設 API
        self.add_resource(
            id="openai",
            name="OpenAI API",
            type=ResourceType.API,
            description="GPT 模型 API",
            owner="DevOps",
            cost=0,
            tags=["ai", "llm", "gpt"]
        )
        
        self.add_resource(
            id="claude",
            name="Claude API",
            type=ResourceType.API,
            description="Claude 模型 API",
            owner="DevOps",
            cost=0,
            tags=["ai", "llm", "claude"]
        )
        
        # 預設資料源
        self.add_resource(
            id="prometheus",
            name="Prometheus",
            type=ResourceType.DATA_SOURCE,
            description="監控指標",
            owner="SRE",
            cost=0,
            tags=["monitoring", "metrics"]
        )
        
        self.add_resource(
            id="grafana",
            name="Grafana",
            type=ResourceType.DATA_SOURCE,
            description="指標視覺化",
            owner="SRE",
            cost=0,
            tags=["visualization", "dashboard"]
        )
        
        # 預設基礎設施
        self.add_resource(
            id="aws",
            name="AWS",
            type=ResourceType.INFRASTRUCTURE,
            description="雲端運算",
            owner="DevOps",
            cost=1000,
            tags=["cloud", "compute", "storage"]
        )
        
        # 預設團隊成員
        self.add_team_member(
            resource_id="member-1",
            name="Johnny Lu",
            role="PM / Developer",
            skills={"python": SkillLevel.EXPERT, "ai": SkillLevel.ADVANCED},
            email="johnny@example.com",
            timezone="Asia/Taipei"
        )
    
    def add_resource(self, id: str, name: str, type: ResourceType,
                    description: str = "", owner: str = "",
                    cost: float = 0, tags: List[str] = None) -> Resource:
        """新增資源"""
        resource = Resource(
            id=id,
            name=name,
            type=type,
            description=description,
            owner=owner,
            cost=cost,
            tags=tags or []
        )
        self.resources[id] = resource
        return resource
    
    def remove_resource(self, id: str) -> bool:
        """移除資源"""
        if id in self.resources:
            del self.resources[id]
            return True
        return False
    
    def get_resource(self, id: str) -> Optional[Resource]:
        """取得資源"""
        return self.resources.get(id)
    
    def get_resources_by_type(self, type: ResourceType) -> List[Resource]:
        """依類型取得資源"""
        return [r for r in self.resources.values() if r.type == type]
    
    def get_resources_by_status(self, status: ResourceStatus) -> List[Resource]:
        """依狀態取得資源"""
        return [r for r in self.resources.values() if r.status == status]
    
    def get_resources_by_tag(self, tag: str) -> List[Resource]:
        """依標籤取得資源"""
        return [r for r in self.resources.values() if tag in r.tags]
    
    def add_team_member(self, resource_id: str, name: str, role: str,
                       skills: Dict[str, SkillLevel] = None,
                       email: str = "", timezone: str = "",
                       availability: float = 1.0, capacity: float = 40.0) -> TeamMember:
        """新增團隊成員"""
        member = TeamMember(
            resource_id=resource_id,
            name=name,
            role=role,
            skills=skills or {},
            email=email,
            timezone=timezone,
            availability=availability,
            capacity=capacity
        )
        self.team_members[resource_id] = member
        
        # 同時作為資源
        self.add_resource(
            id=resource_id,
            name=name,
            type=ResourceType.TEAM_MEMBER,
            description=role,
            owner=name
        )
        
        return member
    
    def get_team_skills_matrix(self) -> Dict[str, List[str]]:
        """取得團隊技能矩陣"""
        matrix = {}
        for member_id, member in self.team_members.items():
            for skill, level in member.skills.items():
                if skill not in matrix:
                    matrix[skill] = []
                matrix[skill].append(f"{member.name} ({level.value})")
        return matrix
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """取得資源摘要"""
        by_type = {}
        by_status = {}
        total_cost = 0
        
        for r in self.resources.values():
            # By type
            type_name = r.type.value
            if type_name not in by_type:
                by_type[type_name] = 0
            by_type[type_name] += 1
            
            # By status
            status_name = r.status.value
            if status_name not in by_status:
                by_status[status_name] = 0
            by_status[status_name] += 1
            
            # Cost
            total_cost += r.cost
        
        return {
            "total": len(self.resources),
            "by_type": by_type,
            "by_status": by_status,
            "total_monthly_cost": total_cost,
            "team_size": len(self.team_members)
        }
    
    def to_table(self) -> str:
        """產生表格視圖"""
        lines = []
        lines.append("╔" + "═" * 90 + "╗")
        lines.append("║" + " 📦 RESOURCE INVENTORY ".center(90) + "║")
        lines.append("╚" + "═" * 90 + "╝")
        lines.append("")
        
        # Summary
        summary = self.get_resource_summary()
        lines.append(f"  Total Resources: {summary['total']} | Team: {summary['team_size']} | Monthly Cost: ${summary['total_monthly_cost']:.2f}")
        lines.append("")
        
        # Group by type
        for res_type in ResourceType:
            resources = self.get_resources_by_type(res_type)
            if not resources:
                continue
            
            lines.append(f"  {res_type.value.upper().replace('_', ' ')} ({len(resources)})")
            lines.append("  " + "─" * 86)
            
            for r in resources:
                status_icon = r.status_icon
                lines.append(
                    f"    {status_icon} {r.name:20} │ {r.description[:35]:<35} │ "
                    f"Owner: {r.owner or '-':<15} │ ${r.cost:>6.2f}"
                )
            lines.append("")
        
        return "\n".join(lines)
    
    def to_markdown(self) -> str:
        """產生 Markdown 格式"""
        lines = []
        lines.append("# Resource Dashboard\n")
        
        summary = self.get_resource_summary()
        lines.append(f"**Total Resources**: {summary['total']}")
        lines.append(f"**Team Size**: {summary['team_size']}")
        lines.append(f"**Monthly Cost**: ${summary['total_monthly_cost']:.2f}\n")
        
        lines.append("## Resources by Type\n")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for type_name, count in summary['by_type'].items():
            lines.append(f"| {type_name} | {count} |")
        
        lines.append("\n## All Resources\n")
        lines.append("| Name | Type | Status | Owner | Cost |")
        lines.append("|------|------|--------|-------|------|")
        
        for r in sorted(self.resources.values(), key=lambda x: x.type.value):
            lines.append(
                f"| {r.name} | {r.type.value} | {r.status.value} | {r.owner or '-'} | ${r.cost:.2f} |"
            )
        
        lines.append("\n## Team Skills Matrix\n")
        matrix = self.get_team_skills_matrix()
        for skill, members in sorted(matrix.items()):
            lines.append(f"### {skill}")
            for m in members:
                lines.append(f"- {m}")
        
        return "\n".join(lines)
    
    def to_json(self) -> Dict[str, Any]:
        """產生 JSON 格式"""
        return {
            "summary": self.get_resource_summary(),
            "resources": {
                k: {
                    "name": v.name,
                    "type": v.type.value,
                    "status": v.status.value,
                    "description": v.description,
                    "owner": v.owner,
                    "cost": v.cost,
                    "tags": v.tags,
                }
                for k, v in self.resources.items()
            },
            "team": {
                k: {
                    "name": v.name,
                    "role": v.role,
                    "skills": {s: l.value for s, l in v.skills.items()},
                    "availability": v.availability,
                    "capacity": v.capacity,
                    "email": v.email,
                    "timezone": v.timezone,
                }
                for k, v in self.team_members.items()
            }
        }


# ==================== Main ====================

if __name__ == "__main__":
    dashboard = ResourceDashboard()
    
    print(dashboard.to_table())
    
    print("\n" + "=" * 90)
    print("\n📊 Quick Stats:")
    summary = dashboard.get_resource_summary()
    print(f"  Total: {summary['total']}")
    print(f"  By Type: {summary['by_type']}")
    print(f"  By Status: {summary['by_status']}")
    print(f"  Monthly Cost: ${summary['total_monthly_cost']:.2f}")
    
    print("\n🔍 Search Examples:")
    print("  AI-related:", [r.name for r in dashboard.get_resources_by_tag("ai")])
    print("  Active tools:", [r.name for r in dashboard.get_resources_by_status(ResourceStatus.ACTIVE) if r.type == ResourceType.TOOL])
    
    print("\n👥 Team Skills:")
    matrix = dashboard.get_team_skills_matrix()
    for skill, members in matrix.items():
        print(f"  {skill}: {', '.join(members)}")
