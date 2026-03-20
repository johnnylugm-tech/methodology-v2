#!/usr/bin/env python3
"""
MethodologyCore - 統一入口

提供一致的初始化和使用介面
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MethodologyConfig:
    """統一配置"""
    # 專案設定
    project_name: str = "Untitled Project"
    debug: bool = False
    
    # 儲存設定
    storage_path: str = "~/.methodology/projects.db"
    
    # 預設模型
    default_model: str = "gpt-4o"
    
    # 預算設定
    monthly_budget: float = 100.0
    
    # 功能開關
    enable_audit: bool = True
    enable_monitoring: bool = True
    enable_quality_gate: bool = True
    
    # MCP 服務
    mcp_services: List[str] = field(default_factory=list)


class MethodologyCore:
    """
    統一入口
    
    使用方式：
    
    ```python
    from methodology import MethodologyCore
    
    # 初始化
    core = MethodologyCore()
    
    # 或者自訂配置
    core = MethodologyCore(config=MethodologyConfig(
        project_name="My Project",
        monthly_budget=500
    ))
    
    # 使用各模組
    core.tasks.add("新任務")
    core.costs.track(...)
    ```
    """
    
    def __init__(self, config: MethodologyConfig = None):
        self.config = config or MethodologyConfig()
        
        # 延遲載入
        self._tasks = None
        self._costs = None
        self._project = None
        self._workflow = None
        self._registry = None
        self._bus = None
        self._audit = None
    
    # ==================== 懶載入屬性 ====================
    
    @property
    def tasks(self):
        """任務管理"""
        if self._tasks is None:
            from .task_splitter_v2 import TaskSplitter
            self._tasks = TaskSplitter()
        return self._tasks
    
    @property
    def costs(self):
        """成本追蹤"""
        if self._costs is None:
            from .cost_allocator import CostAllocator
            self._costs = CostAllocator()
        return self._costs
    
    @property
    def project(self):
        """專案管理"""
        if self._project is None:
            from .project import Project
            self._project = Project.create(
                name=self.config.project_name,
                db_path=self.config.storage_path
            )
        return self._project
    
    @property
    def workflow(self):
        """工作流"""
        if self._workflow is None:
            from .workflow_graph import WorkflowGraph
            self._workflow = WorkflowGraph(name=self.config.project_name)
        return self._workflow
    
    @property
    def agents(self):
        """Agent Registry"""
        if self._registry is None:
            from .agent_registry import AgentRegistry
            self._registry = AgentRegistry()
        return self._registry
    
    @property
    def bus(self):
        """Message Bus"""
        if self._bus is None:
            from .message_bus import MessageBus
            self._bus = MessageBus()
        return self._bus
    
    @property
    def audit(self):
        """審計日誌"""
        if self._audit is None:
            from .audit_logger import AuditLogger
            self._audit = AuditLogger()
        return self._audit
    
    # ==================== 快捷方法 ====================
    
    def create_task(self, name: str, **kwargs):
        """快速建立任務"""
        if hasattr(self.tasks, 'add_task'):
            return self.tasks.add_task(name, **kwargs)
        return None
    
    def track_cost(self, amount: float, **kwargs):
        """快速記錄成本"""
        self.costs.add_entry(amount=amount, **kwargs)
    
    def register_agent(self, agent_id: str, name: str, **kwargs):
        """快速注册 Agent"""
        self.agents.register(agent_id, name, **kwargs)
    
    def publish_event(self, topic: str, payload: Any):
        """發布事件"""
        from .message_bus import MessageType
        self.bus.publish(topic, payload, MessageType.EVENT)
    
    def log_action(self, action: str, resource: str, **kwargs):
        """記錄操作"""
        if self.config.enable_audit:
            from .audit_logger import ActionType, ResourceType
            self.audit.log(ActionType.UPDATE, ResourceType(resource), "", kwargs)
    
    # ==================== 生命週期 ====================
    
    def save(self):
        """保存所有狀態"""
        if self._project:
            self._project.save()
    
    def load(self, project_id: str):
        """載入專案"""
        from .project import Project
        self._project = Project.load(project_id, self.config.storage_path)
        return self._project
    
    def export(self) -> Dict:
        """導出配置"""
        return {
            "config": {
                "project_name": self.config.project_name,
                "debug": self.config.debug,
                "storage_path": self.config.storage_path,
                "default_model": self.config.default_model,
                "monthly_budget": self.config.monthly_budget,
            },
            "stats": {
                "agents": len(self.agents.agents) if self._registry else 0,
                "tasks": len(self.tasks.tasks) if self._tasks else 0,
            }
        }


# ============================================================================
# 便捷工廠函數
# ============================================================================

def create_pm_setup() -> MethodologyCore:
    """建立 PM 常用配置"""
    from .MethodologyConfig
    config = MethodologyConfig(
        project_name="AI 開發專案",
        debug=False,
        enable_audit=True,
        enable_monitoring=True,
        enable_quality_gate=True,
    )
    return MethodologyCore(config=config)


def create_minimal_setup() -> MethodologyCore:
    """建立最小配置"""
    config = MethodologyConfig(
        project_name="Quick Project",
        debug=True,
        enable_audit=False,
        enable_monitoring=False,
        enable_quality_gate=False,
    )
    return MethodologyCore(config=config)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=== MethodologyCore Demo ===\n")
    
    # 初始化
    core = MethodologyCore()
    
    print(f"Project: {core.config.project_name}")
    
    # 任務
    print("\n--- Tasks ---")
    if hasattr(core.tasks, 'split_from_goal'):
        tasks = core.tasks.split_from_goal("開發一個 AI 客服系統")
        print(f"Created {len(tasks)} tasks")
    
    # Agent
    print("\n--- Agents ---")
    from .agent_registry import AgentType
    core.agents.register("dev-1", "Developer", AgentType.DEVELOPER)
    print(f"Registered agents: {len(core.agents.agents)}")
    
    # Event
    print("\n--- Events ---")
    core.publish_event("task:created", {"task_id": "task-1"})
    print(f"Queue size: {core.bus.get_queue_status()['queue_size']}")
    
    # Audit
    print("\n--- Audit ---")
    core.log_action("test", "system")
    print(f"Total messages: {len(core.audit.get_statistics())}")
    
    print("\n=== Done ===")

# ==================== Extensions 整合 ====================

@property
def extensions(self):
    """Extensions 整合層"""
    if self._extensions is None:
        from .extensions import create_extensions
        self._extensions = create_extensions(core=self)
    return self._extensions

def scan_security(self, target: str):
    """安全掃描 (整合 SecurityAuditor)"""
    return self.extensions.scan_security(target)

def track_cost(self, model: str, input_tokens: int, output_tokens: int):
    """成本追蹤 (整合 CostOptimizer)"""
    self.extensions.track_cost(model, input_tokens, output_tokens)
    # 同時更新 router
    if hasattr(self, '_router'):
        self._router.track_usage(model, input_tokens, output_tokens)

def generate_workflow_diagram(self, workflow):
    """生成工作流圖表 (整合 WorkflowVisualizer)"""
    return self.extensions.visualize.generate_diagram(workflow)
