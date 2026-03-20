#!/usr/bin/env python3
"""
WorkflowGraph - DAG 工作流引擎

支援條件分支、並行執行、超時控制的 DAG 工作流
"""

import json
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import threading


class NodeStatus(Enum):
    """節點狀態"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"


class NodeType(Enum):
    """節點類型"""
    TASK = "task"           # 普通任務
    START = "start"         # 開始節點
    END = "end"             # 結束節點
    CONDITION = "condition" # 條件節點
    PARALLEL = "parallel"   # 並行執行
    MERGE = "merge"         # 合併節點


@dataclass
class WorkflowNode:
    """工作流節點"""
    id: str
    name: str
    type: NodeType = NodeType.TASK
    
    # 執行配置
    func: Callable = None  # 可執行的函數
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    
    # 依賴
    depends_on: List[str] = field(default_factory=list)
    conditions: Dict[str, Callable] = None  # 條件分支
    
    # 配置
    timeout_seconds: int = 300
    retry_count: int = 0
    critical: bool = False  # 關鍵任務
    
    # 狀態（运行时填充）
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None
    error: str = None
    started_at: datetime = None
    completed_at: datetime = None
    attempts: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "depends_on": self.depends_on,
            "attempts": self.attempts,
        }


@dataclass
class WorkflowEdge:
    """工作流邊"""
    from_node: str
    to_node: str
    condition: Callable = None  # 條件
    label: str = ""


@dataclass
class WorkflowExecution:
    """工作流執行實例"""
    id: str
    name: str
    nodes: Dict[str, WorkflowNode]
    edges: List[WorkflowEdge]
    
    # 狀態
    status: str = "pending"  # pending, running, completed, failed, cancelled
    started_at: datetime = None
    completed_at: datetime = None
    
    # 結果
    results: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    
    # 配置
    max_parallel: int = 3


class WorkflowGraph:
    """DAG 工作流引擎"""
    
    def __init__(self, workflow_id: str = None, name: str = "Workflow"):
        self.workflow_id = workflow_id or f"wf-{datetime.now().timestamp()}"
        self.name = name
        
        # 圖結構
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        
        # 索引
        self.adjacency: Dict[str, List[str]] = defaultdict(list)  # node -> successors
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # node -> predecessors
        
        # 執行器
        self.executor: WorkflowExecutor = None
        
        # 鎖
        self.lock = threading.RLock()
    
    def add_node(self, node_id: str, name: str,
                node_type: NodeType = NodeType.TASK,
                func: Callable = None,
                depends_on: List[str] = None,
                **config) -> WorkflowNode:
        """新增節點"""
        with self.lock:
            if node_id in self.nodes:
                raise ValueError(f"Node {node_id} already exists")
            
            node = WorkflowNode(
                id=node_id,
                name=name,
                type=node_type,
                func=func,
                depends_on=depends_on or [],
                **config
            )
            
            self.nodes[node_id] = node
            return node
    
    def add_edge(self, from_node: str, to_node: str,
                condition: Callable = None, label: str = ""):
        """新增邊"""
        if from_node not in self.nodes:
            raise ValueError(f"From node {from_node} not found")
        if to_node not in self.nodes:
            raise ValueError(f"To node {to_node} not found")
        
        edge = WorkflowEdge(
            from_node=from_node,
            to_node=to_node,
            condition=condition,
            label=label,
        )
        
        self.edges.append(edge)
        self.adjacency[from_node].append(to_node)
        self.reverse_adjacency[to_node].append(from_node)
    
    def add_condition_node(self, node_id: str, name: str,
                          conditions: Dict[str, Callable]):
        """新增條件節點"""
        return self.add_node(
            node_id=node_id,
            name=name,
            node_type=NodeType.CONDITION,
            conditions=conditions,
        )
    
    def add_parallel_nodes(self, node_ids: List[str], name: str = "Parallel",
                         depends_on: List[str] = None):
        """新增並行節點組"""
        for node_id in node_ids:
            self.add_node(
                node_id=node_id,
                name=f"{name}: {node_id}",
                node_type=NodeType.PARALLEL,
                depends_on=depends_on,
            )
        
        return node_ids
    
    def _topological_sort(self) -> List[str]:
        """拓撲排序 (Kahn's algorithm)"""
        # 計算入度
        in_degree = {node_id: len(self.reverse_adjacency[node_id]) 
                     for node_id in self.nodes}
        
        # 找到所有入度為 0 的節點
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []
        
        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)
            
            for successor in self.adjacency[node_id]:
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)
        
        return sorted_nodes
    
    def _get_ready_nodes(self, completed: Set[str]) -> List[str]:
        """取得準備好的節點"""
        ready = []
        
        for node_id, node in self.nodes.items():
            if node.status != NodeStatus.PENDING:
                continue
            
            # 檢查所有依賴是否完成
            deps_met = all(dep in completed for dep in node.depends_on)
            
            if deps_met:
                ready.append(node_id)
        
        return ready
    
    def _evaluate_condition(self, node: WorkflowNode, context: Dict) -> Optional[List[str]]:
        """評估條件"""
        if node.type != NodeType.CONDITION:
            return None
        
        if not node.conditions:
            return None
        
        # 執行條件函數
        for branch_name, condition_func in node.conditions.items():
            try:
                result = condition_func(context)
                if result:
                    return [branch_name]
            except Exception:
                pass
        
        return None
    
    def validate(self) -> bool:
        """驗證工作流"""
        # 檢查循環依賴
        sorted_nodes = self._topological_sort()
        
        if len(sorted_nodes) != len(self.nodes):
            return False  # 有循環依賴
        
        # 檢查缺失的依賴
        for node_id, node in self.nodes.items():
            for dep in node.depends_on:
                if dep not in self.nodes:
                    return False
        
        return True
    
    def execute(self, initial_context: Dict = None,
               max_parallel: int = 3) -> WorkflowExecution:
        """執行工作流"""
        if not self.validate():
            raise ValueError("Workflow validation failed")
        
        execution = WorkflowExecution(
            id=f"exec-{datetime.now().timestamp()}",
            name=self.name,
            nodes=self.nodes.copy(),
            edges=self.edges.copy(),
            max_parallel=max_parallel,
        )
        
        execution.started_at = datetime.now()
        execution.status = "running"
        
        context = initial_context or {}
        completed: Set[str] = set()
        running: Set[str] = set()
        
        # 並發控制
        semaphore = threading.Semaphore(max_parallel)
        
        def run_node(node_id: str) -> Any:
            node = self.nodes[node_id]
            
            with semaphore:
                node.status = NodeStatus.RUNNING
                node.started_at = datetime.now()
                node.attempts += 1
                running.add(node_id)
                
                try:
                    # 執行
                    if node.func:
                        result = node.func(*node.args, **node.kwargs)
                    else:
                        result = None
                    
                    node.result = result
                    node.status = NodeStatus.COMPLETED
                    node.completed_at = datetime.now()
                    completed.add(node_id)
                    
                    return result
                    
                except Exception as e:
                    node.error = str(e)
                    
                    # 檢查是否需要重試
                    if node.attempts < node.retry_count + 1:
                        node.status = NodeStatus.WAITING
                    else:
                        node.status = NodeStatus.FAILED
                        if node.critical:
                            execution.status = "failed"
                    
                    running.discard(node_id)
                    return None
        
        # 使用執行緒池執行
        threads = []
        
        while len(completed) < len(self.nodes):
            # 檢查是否失敗
            if execution.status == "failed":
                break
            
            # 取得準備好的節點
            ready = self._get_ready_nodes(completed)
            
            # 過濾正在運行的
            ready = [r for r in ready if r not in running]
            
            if not ready:
                # 沒有準備好的節點，可能在等待或死鎖
                if not running:
                    break
                continue
            
            # 啟動準備好的節點
            for node_id in ready[:max_parallel - len(running)]:
                thread = threading.Thread(target=lambda nid=node_id: run_node(nid))
                threads.append(thread)
                thread.start()
        
        # 等待所有執行緒完成
        for thread in threads:
            thread.join(timeout=600)
        
        # 更新執行狀態
        if execution.status != "failed":
            failed_count = sum(1 for n in self.nodes.values() if n.status == NodeStatus.FAILED)
            if failed_count > 0:
                execution.status = "failed"
            else:
                execution.status = "completed"
        
        execution.completed_at = datetime.now()
        
        # 收集結果
        for node_id, node in self.nodes.items():
            execution.results[node_id] = node.result
            if node.error:
                execution.errors[node_id] = node.error
        
        return execution
    
    def get_status(self) -> Dict:
        """取得狀態"""
        status_counts = defaultdict(int)
        
        for node in self.nodes.values():
            status_counts[node.status.value] += 1
        
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "total_nodes": len(self.nodes),
            "edges": len(self.edges),
            "status": status_counts,
            "valid": self.validate(),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        status = self.get_status()
        
        report = f"""
# 🔄 Workflow 報告

## {self.name}

| 指標 | 數值 |
|------|------|
| 工作流 ID | {status['workflow_id']} |
| 節點數 | {status['total_nodes']} |
| 邊數 | {status['edges']} |
| 有效 | {'✅ 是' if status['valid'] else '❌ 否'} |

---

## 節點狀態

| 狀態 | 數量 |
|------|------|
"""
        
        for node_status, count in status_counts.items():
            report += f"| {node_status} | {count} |\n"
        
        report += f"""

## 節點詳情

| ID | 名稱 | 類型 | 狀態 |
|------|------|------|------|
"""
        
        for node_id, node in self.nodes.items():
            status_icon = {
                "pending": "⏳",
                "ready": "📋",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "waiting": "⏰",
            }.get(node.status.value, "❓")
            
            report += f"| {node_id} | {node.name} | {node.type.value} | {status_icon} {node.status.value} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import time
    
    # 建立工作流
    wf = WorkflowGraph(name="AI 系統開發工作流")
    
    # 定義節點
    design = wf.add_node("design", "系統設計", func=lambda: time.sleep(0.1) or "架構完成")
    backend = wf.add_node("backend", "後端開發", depends_on=["design"], 
                         func=lambda: time.sleep(0.1) or "後端完成")
    frontend = wf.add_node("frontend", "前端開發", depends_on=["design"],
                          func=lambda: time.sleep(0.1) or "前端完成")
    api_test = wf.add_node("api_test", "API 測試", depends_on=["backend"],
                          func=lambda: time.sleep(0.1) or "API 測試完成")
    ui_test = wf.add_node("ui_test", "UI 測試", depends_on=["frontend"],
                         func=lambda: time.sleep(0.1) or "UI 測試完成")
    deploy = wf.add_node("deploy", "部署", depends_on=["api_test", "ui_test"],
                        func=lambda: time.sleep(0.1) or "部署完成")
    
    # 添加條件節點
    def check_approval(context):
        return context.get("approved", False)
    
    wf.add_condition_node(
        "approval",
        "審批檢查",
        conditions={
            "approved": check_approval,
        }
    )
    
    # 添加邊
    wf.add_edge("design", "approval")
    
    print("=== Workflow Nodes ===")
    for node_id, node in wf.nodes.items():
        print(f"{node_id}: {node.name} (depends on: {node.depends_on})")
    
    print("\n=== Validating ===")
    print(f"Valid: {wf.validate()}")
    
    print("\n=== Executing ===")
    execution = wf.execute(initial_context={"approved": True})
    
    print(f"Status: {execution.status}")
    print(f"Duration: {(execution.completed_at - execution.started_at).total_seconds():.2f}s")
    
    print("\n=== Results ===")
    for node_id, result in execution.results.items():
        node = wf.nodes[node_id]
        print(f"{node_id}: {result} ({node.status.value})")
    
    print("\n=== Report ===")
    print(wf.generate_report())
