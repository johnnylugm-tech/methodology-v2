#!/usr/bin/env python3
"""
Agent Registry - 統一代理注册中心

Agent 的注册、發現、生命周期管理
"""

import json
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent 狀態"""
    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"
    ERROR = "error"
    DECOMMISSIONED = "decommissioned"


class AgentType(Enum):
    """Agent 類型"""
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    PM = "pm"
    RESEARCHER = "researcher"
    DEVOPS = "devops"
    SECURITY = "security"
    CUSTOM = "custom"


@dataclass
class AgentMetadata:
    """Agent 元數據"""
    version: str = "1.0.0"
    author: str = "system"
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)


@dataclass
class AgentRegistration:
    """Agent 注册資訊"""
    agent_id: str
    name: str
    agent_type: AgentType
    status: AgentStatus
    
    # 連接
    endpoint: str = None
    api_key: str = None
    
    # 能力
    capabilities: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    
    # 配置
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    config: Dict = field(default_factory=dict)
    
    # 資源
    max_concurrent_tasks: int = 3
    timeout_seconds: int = 300
    
    # 統計
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    
    # 生命周期
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    last_task_at: datetime = None
    
    # 健康
    error_count: int = 0
    avg_task_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "type": self.agent_type.value,
            "status": self.status.value,
            "capabilities": list(self.capabilities),
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


class AgentRegistry:
    """統一代理注册中心"""
    
    def __init__(self):
        # 注册表
        self.agents: Dict[str, AgentRegistration] = {}
        
        # 按類型索引
        self.by_type: Dict[AgentType, List[str]] = {}
        
        # 按狀態索引
        self.by_status: Dict[AgentStatus, List[str]] = {}
        
        # 訂閱者
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # 鎖
        self.lock = threading.RLock()
        
        # 默認超時
        self.heartbeat_timeout = 60  # 秒
    
    def register(self, agent_id: str, name: str,
                agent_type: AgentType,
                capabilities: List[str] = None,
                endpoint: str = None,
                metadata: AgentMetadata = None,
                **config) -> AgentRegistration:
        """注册 Agent"""
        with self.lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already registered")
            
            registration = AgentRegistration(
                agent_id=agent_id,
                name=name,
                agent_type=agent_type,
                status=AgentStatus.REGISTERED,
                capabilities=set(capabilities or []),
                endpoint=endpoint,
                metadata=metadata or AgentMetadata(),
                config=config,
            )
            
            self.agents[agent_id] = registration
            
            # 更新索引
            self._update_indices(registration)
            
            # 通知訂閱者
            self._notify("agent_registered", registration)
            
            return registration
    
    def unregister(self, agent_id: str):
        """取消注册"""
        with self.lock:
            if agent_id not in self.agents:
                return False
            
            registration = self.agents[agent_id]
            registration.status = AgentStatus.DECOMMISSIONED
            
            # 從索引移除
            self._remove_from_indices(registration)
            
            # 通知
            self._notify("agent_unregistered", registration)
            
            return True
    
    def update_status(self, agent_id: str, status: AgentStatus):
        """更新狀態"""
        with self.lock:
            registration = self.agents.get(agent_id)
            if not registration:
                return False
            
            old_status = registration.status
            registration.status = status
            
            # 更新索引
            if old_status in self.by_status:
                self.by_status[old_status].remove(agent_id)
            if status not in self.by_status:
                self.by_status[status] = []
            self.by_status[status].append(agent_id)
            
            # 通知
            self._notify("agent_status_changed", {
                "agent_id": agent_id,
                "old_status": old_status.value,
                "new_status": status.value,
            })
            
            return True
    
    def heartbeat(self, agent_id: str) -> bool:
        """心跳"""
        with self.lock:
            registration = self.agents.get(agent_id)
            if not registration:
                return False
            
            registration.last_heartbeat = datetime.now()
            
            # 如果之前是 OFFLINE，變成 READY
            if registration.status == AgentStatus.OFFLINE:
                registration.status = AgentStatus.READY
            
            return True
    
    def get(self, agent_id: str) -> Optional[AgentRegistration]:
        """取得 Agent"""
        return self.agents.get(agent_id)
    
    def find_by_type(self, agent_type: AgentType) -> List[AgentRegistration]:
        """按類型查找"""
        return [self.agents[aid] for aid in self.by_type.get(agent_type, [])
                if aid in self.agents]
    
    def find_by_status(self, status: AgentStatus) -> List[AgentRegistration]:
        """按狀態查找"""
        return [self.agents[aid] for aid in self.by_status.get(status, [])
                if aid in self.agents]
    
    def find_by_capability(self, capability: str) -> List[AgentRegistration]:
        """按能力查找"""
        return [
            reg for reg in self.agents.values()
            if capability in reg.capabilities and reg.status in [
                AgentStatus.READY, AgentStatus.IDLE
            ]
        ]
    
    def find_available(self, required_capabilities: List[str] = None,
                      agent_type: AgentType = None) -> Optional[AgentRegistration]:
        """查找可用的 Agent"""
        candidates = []
        
        if agent_type:
            candidates = self.find_by_type(agent_type)
        else:
            candidates = self.find_by_status(AgentStatus.READY) + \
                        self.find_by_status(AgentStatus.IDLE)
        
        # 過濾能力
        if required_capabilities:
            candidates = [
                c for c in candidates
                if all(cap in c.capabilities for cap in required_capabilities)
            ]
        
        # 按負載排序（任務最少的最先）
        candidates.sort(key=lambda x: x.tasks_completed)
        
        return candidates[0] if candidates else None
    
    def record_task_start(self, agent_id: str):
        """記錄任務開始"""
        with self.lock:
            registration = self.agents.get(agent_id)
            if not registration:
                return
            
            registration.status = AgentStatus.BUSY
            registration.last_task_at = datetime.now()
    
    def record_task_complete(self, agent_id: str, success: bool = True,
                           tokens_used: int = 0, cost: float = 0.0,
                           duration_ms: float = 0.0):
        """記錄任務完成"""
        with self.lock:
            registration = self.agents.get(agent_id)
            if not registration:
                return
            
            if success:
                registration.tasks_completed += 1
            else:
                registration.tasks_failed += 1
            
            registration.total_tokens += tokens_used
            registration.total_cost += cost
            
            # 更新平均任務時間
            if registration.tasks_completed > 0:
                prev_total = registration.avg_task_duration_ms * (registration.tasks_completed - 1)
                registration.avg_task_duration_ms = (prev_total + duration_ms) / registration.tasks_completed
            
            # 變回 READY 或 IDLE
            registration.status = AgentStatus.READY
    
    def record_error(self, agent_id: str, error: str):
        """記錄錯誤"""
        with self.lock:
            registration = self.agents.get(agent_id)
            if not registration:
                return
            
            registration.error_count += 1
            registration.last_heartbeat = datetime.now()
            
            # 錯誤太多變 ERROR
            if registration.error_count >= 3:
                registration.status = AgentStatus.ERROR
    
    def check_health(self) -> List[AgentRegistration]:
        """檢查健康狀態"""
        now = datetime.now()
        timeout = timedelta(seconds=self.heartbeat_timeout)
        
        unhealthy = []
        
        for registration in self.agents.values():
            if registration.status in [AgentStatus.DECOMMISSIONED]:
                continue
            
            # 心跳超時
            if now - registration.last_heartbeat > timeout:
                registration.status = AgentStatus.OFFLINE
                unhealthy.append(registration)
        
        return unhealthy
    
    def subscribe(self, event: str, callback: Callable):
        """訂閱事件"""
        if event not in self.subscribers:
            self.subscribers[event] = []
        self.subscribers[event].append(callback)
    
    def _notify(self, event: str, data: Any):
        """通知訂閱者"""
        for callback in self.subscribers.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.debug(f"Subscriber callback failed: {e}")
    
    def _update_indices(self, registration: AgentRegistration):
        """更新索引"""
        # 按類型
        if registration.agent_type not in self.by_type:
            self.by_type[registration.agent_type] = []
        self.by_type[registration.agent_type].append(registration.agent_id)
        
        # 按狀態
        if registration.status not in self.by_status:
            self.by_status[registration.status] = []
        self.by_status[registration.status].append(registration.agent_id)
    
    def _remove_from_indices(self, registration: AgentRegistration):
        """從索引移除"""
        # 按類型
        if registration.agent_type in self.by_type:
            if registration.agent_id in self.by_type[registration.agent_type]:
                self.by_type[registration.agent_type].remove(registration.agent_id)
        
        # 按狀態
        if registration.status in self.by_status:
            if registration.agent_id in self.by_status[registration.status]:
                self.by_status[registration.status].remove(registration.agent_id)
    
    def get_statistics(self) -> Dict:
        """取得統計"""
        total = len(self.agents)
        
        by_type = {}
        for agent_type, agents in self.by_type.items():
            by_type[agent_type.value] = len(agents)
        
        by_status = {}
        for status, agents in self.by_status.items():
            by_status[status.value] = len(agents)
        
        total_completed = sum(r.tasks_completed for r in self.agents.values())
        total_failed = sum(r.tasks_failed for r in self.agents.values())
        total_cost = sum(r.total_cost for r in self.agents.values())
        
        return {
            "total_agents": total,
            "by_type": by_type,
            "by_status": by_status,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "total_cost": total_cost,
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        stats = self.get_statistics()
        
        report = f"""
# 🤖 Agent Registry 報告

## 統計

| 指標 | 數值 |
|------|------|
| 總 Agent 數 | {stats['total_agents']} |
| 總完成任務 | {stats['total_tasks_completed']} |
| 失敗任務 | {stats['total_tasks_failed']} |
| 總成本 | ${stats['total_cost']:.4f} |

---

## 按類型

| 類型 | 數量 |
|------|------|
"""
        
        for agent_type, count in stats['by_type'].items():
            report += f"| {agent_type} | {count} |\n"
        
        report += f"""

## 按狀態

| 狀態 | 數量 |
|------|------|
"""
        
        for status, count in stats['by_status'].items():
            report += f"| {status} | {count} |\n"
        
        report += f"""

## Agent 列表

| 名稱 | 類型 | 狀態 | 完成 | 失敗 |
|------|------|------|------|------|
"""
        
        for registration in self.agents.values():
            if registration.status.value != "decommissioned":
                report += f"| {registration.name} | {registration.agent_type.value} | {registration.status.value} | {registration.tasks_completed} | {registration.tasks_failed} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    registry = AgentRegistry()
    
    print("=== Registering Agents ===")
    
    arch = registry.register(
        "arch-1",
        name="Architect Alice",
        agent_type=AgentType.ARCHITECT,
        capabilities=["architecture", "code_review", "system_design"]
    )
    
    dev1 = registry.register(
        "dev-1",
        name="Developer Bob",
        agent_type=AgentType.DEVELOPER,
        capabilities=["python", "api_design", "testing"]
    )
    
    dev2 = registry.register(
        "dev-2",
        name="Developer Charlie",
        agent_type=AgentType.DEVELOPER,
        capabilities=["javascript", "react", "testing"]
    )
    
    tester = registry.register(
        "test-1",
        name="Tester Dave",
        agent_type=AgentType.TESTER,
        capabilities=["testing", "automation", "performance"]
    )
    
    print(f"Registered: {arch.name}, {dev1.name}, {dev2.name}, {tester.name}")
    
    # 心跳
    registry.heartbeat("dev-1")
    
    # 模擬任務
    print("\n=== Simulating Tasks ===")
    
    registry.record_task_start("dev-1")
    print(f"{dev1.name}: task started")
    
    registry.record_task_complete("dev-1", success=True, tokens_used=1000, cost=0.05)
    print(f"{dev1.name}: task completed")
    
    # 查找
    print("\n=== Finding Agents ===")
    
    python_dev = registry.find_available(required_capabilities=["python"])
    print(f"Available Python dev: {python_dev.name if python_dev else 'None'}")
    
    any_dev = registry.find_available(agent_type=AgentType.DEVELOPER)
    print(f"Available developer: {any_dev.name if any_dev else 'None'}")
    
    # 統計
    print("\n=== Statistics ===")
    stats = registry.get_statistics()
    print(f"Total agents: {stats['total_agents']}")
    print(f"By type: {stats['by_type']}")
    print(f"By status: {stats['by_status']}")
    
    # 健康檢查
    print("\n=== Health Check ===")
    unhealthy = registry.check_health()
    print(f"Unhealthy agents: {len(unhealthy)}")
    
    # 報告
    print("\n=== Report ===")
    print(registry.generate_report())
