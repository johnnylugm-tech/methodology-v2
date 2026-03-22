#!/usr/bin/env python3
"""
Workflow Graph - 工作流圖結構視覺化

對標 LangGraph 的圖結構概念：
- 節點定義（Task, Agent, Condition, Output）
- 邊定義（順序、分支、合併）
- 圖遍歷
- ASCII / DOT / JSON 導出

AI-native 實作，零額外負擔
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid

class NodeType(Enum):
    """節點類型"""
    TASK = "task"
    AGENT = "agent"
    CONDITION = "condition"
    MERGE = "merge"
    OUTPUT = "output"
    START = "start"
    END = "end"

class EdgeType(Enum):
    """邊類型"""
    SEQUENCE = "sequence"      # 順序
    BRANCH = "branch"          # 分支
    MERGE = "merge"            # 合併
    FEEDBACK = "feedback"      # 回饋循環

@dataclass
class GraphNode:
    """圖節點"""
    node_id: str
    name: str
    node_type: NodeType
    config: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "type": self.node_type.value,
            "config": self.config,
        }

@dataclass
class GraphEdge:
    """圖邊"""
    edge_id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    condition: Optional[Callable] = None  # 分支條件
    weight: float = 1.0
    
    def should_traverse(self, context: dict) -> bool:
        """判斷是否應該遍歷此邊"""
        if self.edge_type == EdgeType.BRANCH and self.condition:
            return self.condition(context)
        return True

class WorkflowGraph:
    """
    工作流圖結構
    
    對標 LangGraph 的圖結構：
    - 視覺化表示
    - 條件分支
    - 並行執行
    - 循環支援
    """
    
    def __init__(self, name: str = "workflow"):
        self.graph_id = f"graph-{uuid.uuid4().hex[:8]}"
        self.name = name
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.start_node: Optional[str] = None
        self.end_nodes: List[str] = []
    
    def add_node(self, name: str, node_type: NodeType, config: Dict = None) -> str:
        """添加節點"""
        node_id = f"node-{uuid.uuid4().hex[:8]}"
        node = GraphNode(node_id=node_id, name=name, node_type=node_type, config=config or {})
        self.nodes[node_id] = node
        return node_id
    
    def add_edge(self, source_id: str, target_id: str, edge_type: EdgeType = EdgeType.SEQUENCE, condition: Callable = None) -> str:
        """添加邊"""
        edge_id = f"edge-{uuid.uuid4().hex[:8]}"
        edge = GraphEdge(edge_id=edge_id, source_id=source_id, target_id=target_id, edge_type=edge_type, condition=condition)
        self.edges[edge_id] = edge
        return edge_id
    
    def set_start(self, node_id: str):
        """設定起始節點"""
        self.start_node = node_id
    
    def set_end(self, node_id: str):
        """設定結束節點"""
        if node_id not in self.end_nodes:
            self.end_nodes.append(node_id)
    
    def to_ascii(self) -> str:
        """導出 ASCII 圖"""
        lines = [f"Workflow: {self.name}", "=" * 50]
        for node_id, node in self.nodes.items():
            prefix = "→ " if node_id == self.start_node else "  "
            suffix = " [END]" if node_id in self.end_nodes else ""
            lines.append(f"{prefix}{node.name} ({node.node_type.value}){suffix}")
            # 輸出邊
            for edge in self.edges.values():
                if edge.source_id == node_id:
                    target = self.nodes.get(edge.target_id)
                    if target:
                        lines.append(f"   └─[{edge.edge_type.value}]→ {target.name}")
        return "\n".join(lines)
    
    def to_dot(self) -> str:
        """導出 DOT 格式（Graphviz）"""
        lines = [f'digraph "{self.name}" {{', '  rankdir=LR;']
        for node_id, node in self.nodes.items():
            shape = "box" if node.node_type == NodeType.TASK else "diamond" if node.node_type == NodeType.CONDITION else "oval"
            lines.append(f'  {node_id} [label="{node.name}", shape={shape}];')
        for edge in self.edges.values():
            lines.append(f'  {edge.source_id} -> {edge.target_id} [label="{edge.edge_type.value}"];')
        lines.append('}')
        return "\n".join(lines)
    
    def to_json(self) -> dict:
        """導出 JSON"""
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [{"source": e.source_id, "target": e.target_id, "type": e.edge_type.value} for e in self.edges.values()],
            "start": self.start_node,
            "ends": self.end_nodes,
        }
    
    def get_next_nodes(self, node_id: str, context: dict = None) -> List[str]:
        """取得下一個節點"""
        context = context or {}
        next_nodes = []
        for edge in self.edges.values():
            if edge.source_id == node_id:
                if edge.should_traverse(context):
                    next_nodes.append(edge.target_id)
        return next_nodes
    
    def visualize(self) -> str:
        """返回視覺化表示"""
        return self.to_ascii()


# =============================================================================
# 便捷工廠函數
# =============================================================================

def create_linear_flow(name: str, tasks: List[str]) -> WorkflowGraph:
    """創建線性工作流"""
    wf = WorkflowGraph(name=name)
    prev_id = None
    for task_name in tasks:
        task_id = wf.add_node(task_name, NodeType.TASK)
        if prev_id:
            wf.add_edge(prev_id, task_id, EdgeType.SEQUENCE)
        else:
            wf.set_start(task_id)
        prev_id = task_id
    wf.set_end(task_id)
    return wf

def create_branch_flow(name: str, condition_node: str, branches: Dict[str, str], merge_node: str = None) -> WorkflowGraph:
    """創建分支工作流"""
    wf = WorkflowGraph(name=name)
    cond_id = wf.add_node(condition_node, NodeType.CONDITION)
    wf.set_start(cond_id)
    
    for branch_name, branch_task in branches.items():
        branch_id = wf.add_node(branch_task, NodeType.TASK)
        wf.add_edge(cond_id, branch_id, EdgeType.BRANCH, condition=lambda ctx: ctx.get("branch") == branch_name)
        if merge_node:
            merge_id = wf.add_node(merge_node, NodeType.MERGE)
            wf.add_edge(branch_id, merge_id, EdgeType.SEQUENCE)
            wf.set_end(merge_id)
        else:
            wf.set_end(branch_id)
    return wf


if __name__ == "__main__":
    # 快速範例
    wf = WorkflowGraph("Example Workflow")
    
    start = wf.add_node("Start", NodeType.START)
    task1 = wf.add_node("Process Data", NodeType.TASK)
    cond = wf.add_node("Check Result", NodeType.CONDITION)
    task2a = wf.add_node("Handle Success", NodeType.TASK)
    task2b = wf.add_node("Handle Error", NodeType.TASK)
    end = wf.add_node("End", NodeType.END)
    
    wf.set_start(start)
    wf.add_edge(start, task1)
    wf.add_edge(task1, cond)
    wf.add_edge(cond, task2a, EdgeType.BRANCH)
    wf.add_edge(cond, task2b, EdgeType.BRANCH)
    wf.add_edge(task2a, end)
    wf.add_edge(task2b, end)
    wf.set_end(end)
    
    print(wf.visualize())
    print("\n--- JSON Export ---")
    import json
    print(json.dumps(wf.to_json(), indent=2))
