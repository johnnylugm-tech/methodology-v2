#!/usr/bin/env python3
"""
Resource Dashboard - 資源視圖

全域資源狀態：GPU/CPU/Agent/記憶體 使用情況
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResourceType(Enum):
    """資源類型"""
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    AGENT = "agent"
    API = "api"
    STORAGE = "storage"


class ResourceStatus(Enum):
    """資源狀態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


@dataclass
class ResourceUsage:
    """資源使用量"""
    used: float
    total: float
    unit: str = "%"
    
    @property
    def percentage(self) -> float:
        return (self.used / self.total * 100) if self.total > 0 else 0
    
    @property
    def available(self) -> float:
        return self.total - self.used


@dataclass
class ResourceInfo:
    """資源資訊"""
    id: str
    name: str
    type: ResourceType
    
    # 使用情況
    usage: ResourceUsage = None
    
    # 狀態
    status: ResourceStatus = ResourceStatus.HEALTHY
    
    # 配置
    max_concurrent_tasks: int = 10
    current_tasks: int = 0
    cost_per_hour: float = 0.0
    
    # 歷史
    last_updated: datetime = field(default_factory=datetime.now)
    history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if self.usage is None:
            self.usage = ResourceUsage(used=0, total=100)
    
    @property
    def utilization(self) -> float:
        """使用率"""
        return self.usage.percentage
    
    @property
    def is_available(self) -> bool:
        """是否可用"""
        return (self.status != ResourceStatus.OFFLINE and 
                self.current_tasks < self.max_concurrent_tasks)


class ResourceDashboard:
    """
    資源儀表板
    
    使用方式：
    
    ```python
    from methodology import ResourceDashboard, ResourceType, ResourceStatus
    
    dashboard = ResourceDashboard()
    
    # 新增資源
    dashboard.add_resource("gpu-1", "NVIDIA A100", ResourceType.GPU,
                          capacity=100)
    
    dashboard.add_resource("agent-pool", "Developer Agents", ResourceType.AGENT,
                          capacity=10)
    
    # 更新使用量
    dashboard.update_usage("gpu-1", used=75)
    
    # 獲取狀態
    status = dashboard.get_all_status()
    print(status)
    
    # 生成報告
    print(dashboard.generate_report())
    ```
    """
    
    def __init__(self):
        self.resources: Dict[str, ResourceInfo] = {}
        self.alerts: List[Dict] = []
    
    def add_resource(self, resource_id: str, name: str, 
                   resource_type: ResourceType,
                   capacity: float = 100,
                   max_concurrent_tasks: int = 10,
                   cost_per_hour: float = 0.0) -> ResourceInfo:
        """
        新增資源
        
        Args:
            resource_id: 資源 ID
            name: 資源名稱
            resource_type: 資源類型
            capacity: 容量
            max_concurrent_tasks: 最大並發任務數
            cost_per_hour: 每小時成本
            
        Returns:
            ResourceInfo 實例
        """
        info = ResourceInfo(
            id=resource_id,
            name=name,
            type=resource_type,
            usage=ResourceUsage(used=0, total=capacity),
            max_concurrent_tasks=max_concurrent_tasks,
            cost_per_hour=cost_per_hour
        )
        
        self.resources[resource_id] = info
        return info
    
    def update_usage(self, resource_id: str, used: float = None,
                    percentage: float = None, tasks: int = None):
        """
        更新資源使用量
        
        Args:
            resource_id: 資源 ID
            used: 已使用量
            percentage: 使用百分比 (優先於 used)
            tasks: 當前任務數
        """
        if resource_id not in self.resources:
            return
        
        resource = self.resources[resource_id]
        
        if percentage is not None:
            resource.usage.used = resource.usage.total * (percentage / 100)
        elif used is not None:
            resource.usage.used = used
        
        if tasks is not None:
            resource.current_tasks = tasks
        
        # 更新狀態
        self._update_status(resource)
        
        # 記錄歷史
        self._record_history(resource)
        
        # 檢查警報
        self._check_alerts(resource)
        
        resource.last_updated = datetime.now()
    
    def _update_status(self, resource: ResourceInfo):
        """根據使用量更新狀態"""
        util = resource.utilization
        
        if resource.type == ResourceType.AGENT:
            # Agent 根據任務數判斷
            if resource.current_tasks >= resource.max_concurrent_tasks:
                resource.status = ResourceStatus.CRITICAL
            elif resource.current_tasks >= resource.max_concurrent_tasks * 0.8:
                resource.status = ResourceStatus.WARNING
            else:
                resource.status = ResourceStatus.HEALTHY
        else:
            # 其他資源根據使用率
            if util >= 90:
                resource.status = ResourceStatus.CRITICAL
            elif util >= 75:
                resource.status = ResourceStatus.WARNING
            else:
                resource.status = ResourceStatus.HEALTHY
    
    def _record_history(self, resource: ResourceInfo):
        """記錄使用歷史"""
        resource.history.append({
            "timestamp": datetime.now(),
            "used": resource.usage.used,
            "percentage": resource.utilization,
            "tasks": resource.current_tasks
        })
        
        # 只保留最近 100 條
        if len(resource.history) > 100:
            resource.history = resource.history[-100:]
    
    def _check_alerts(self, resource: ResourceInfo):
        """檢查是否需要警報"""
        if resource.status == ResourceStatus.CRITICAL:
            self.alerts.append({
                "timestamp": datetime.now(),
                "resource_id": resource.id,
                "resource_name": resource.name,
                "level": "critical",
                "message": f"{resource.name} 使用率達 {resource.utilization:.0f}%"
            })
        elif resource.status == ResourceStatus.WARNING:
            self.alerts.append({
                "timestamp": datetime.now(),
                "resource_id": resource.id,
                "resource_name": resource.name,
                "level": "warning",
                "message": f"{resource.name} 使用率達 {resource.utilization:.0f}%"
            })
    
    def get_resource(self, resource_id: str) -> Optional[ResourceInfo]:
        """取得資源資訊"""
        return self.resources.get(resource_id)
    
    def get_all_status(self) -> Dict:
        """
        取得所有資源狀態
        
        Returns:
            資源狀態概覽
        """
        by_type = {}
        for resource in self.resources.values():
            if resource.type.value not in by_type:
                by_type[resource.type.value] = []
            
            by_type[resource.type.value].append({
                "id": resource.id,
                "name": resource.name,
                "status": resource.status.value,
                "utilization": resource.utilization,
                "used": resource.usage.used,
                "total": resource.usage.total,
                "available": resource.usage.available,
                "current_tasks": resource.current_tasks,
                "max_tasks": resource.max_concurrent_tasks
            })
        
        return {
            "total_resources": len(self.resources),
            "by_type": by_type,
            "summary": {
                "healthy": sum(1 for r in self.resources.values() if r.status == ResourceStatus.HEALTHY),
                "warning": sum(1 for r in self.resources.values() if r.status == ResourceStatus.WARNING),
                "critical": sum(1 for r in self.resources.values() if r.status == ResourceStatus.CRITICAL),
                "offline": sum(1 for r in self.resources.values() if r.status == ResourceStatus.OFFLINE)
            }
        }
    
    def get_available_resources(self, resource_type: ResourceType = None) -> List[ResourceInfo]:
        """
        取得可用資源
        
        Args:
            resource_type: 篩選特定類型
            
        Returns:
            可用資源列表
        """
        available = []
        
        for resource in self.resources.values():
            if resource_type and resource.type != resource_type:
                continue
            
            if resource.is_available:
                available.append(resource)
        
        return available
    
    def generate_report(self) -> str:
        """
        生成資源報告
        
        Returns:
            格式化報告
        """
        status = self.get_all_status()
        
        lines = [
            "=" * 60,
            "RESOURCE DASHBOARD REPORT",
            "=" * 60,
            "",
            f"總資源數: {status['total_resources']}",
            "",
            "狀態摘要:",
            f"  ✅ Healthy: {status['summary']['healthy']}",
            f"  ⚠️  Warning: {status['summary']['warning']}",
            f"  🔴 Critical: {status['summary']['critical']}",
            f"  ⬛ Offline: {status['summary']['offline']}",
            "",
        ]
        
        # 按類型顯示
        for type_name, resources in status['by_type'].items():
            lines.append(f"\n{type_name.upper()}:")
            lines.append("-" * 40)
            
            for r in resources:
                status_icon = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "critical": "🔴",
                    "offline": "⬛"
                }.get(r['status'], "?")
                
                lines.append(f"  {status_icon} {r['name']}")
                lines.append(f"      使用率: {r['utilization']:.1f}% ({r['used']:.1f}/{r['total']})")
                
                if r.get('current_tasks') is not None:
                    lines.append(f"      任務: {r['current_tasks']}/{r['max_tasks']}")
        
        # 最近的警報
        if self.alerts:
            lines.append("\n" + "=" * 60)
            lines.append("RECENT ALERTS")
            lines.append("=" * 60)
            
            for alert in self.alerts[-5:]:
                icon = "🔴" if alert['level'] == 'critical' else "⚠️"
                lines.append(f"\n{icon} {alert['timestamp'].strftime('%H:%M:%S')}")
                lines.append(f"   {alert['message']}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """生成 JSON"""
        import json
        return json.dumps(self.get_all_status(), indent=2, default=str)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    dashboard = ResourceDashboard()
    
    # 新增資源
    dashboard.add_resource("gpu-1", "NVIDIA A100", ResourceType.GPU, capacity=100, cost_per_hour=2.50)
    dashboard.add_resource("gpu-2", "NVIDIA A100", ResourceType.GPU, capacity=100, cost_per_hour=2.50)
    dashboard.add_resource("cpu-1", "Xeon Processor", ResourceType.CPU, capacity=64, cost_per_hour=0.50)
    dashboard.add_resource("agent-pool", "Developer Pool", ResourceType.AGENT, capacity=20, max_concurrent_tasks=20)
    dashboard.add_resource("memory-1", "128GB RAM", ResourceType.MEMORY, capacity=128, cost_per_hour=0.30)
    
    # 更新使用量
    dashboard.update_usage("gpu-1", percentage=75)
    dashboard.update_usage("gpu-2", percentage=45)
    dashboard.update_usage("cpu-1", used=32)
    dashboard.update_usage("agent-pool", tasks=15)
    dashboard.update_usage("memory-1", percentage=85)
    
    # 顯示報告
    print(dashboard.generate_report())
    
    print("\n" + "=" * 60)
    print("JSON Output:")
    print("=" * 60)
    print(dashboard.to_json())
