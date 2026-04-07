#!/usr/bin/env python3
"""
Impact Analysis - 影響分析

對標 TDAD 的 Graph-Based Impact Analysis：
- 建立原始碼和測試之間的依賴圖
- 預測變更會影響哪些測試
- 量化回歸風險

核心概念：
- Impact Graph：節點是檔案/測試，邊是依賴關係
- Change Impact：預測某個檔案變更會影響哪些測試
- Regression Risk：量化回歸風險
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime
import os
import re


class DependencyType(Enum):
    """依賴類型"""
    IMPORTS = "imports"           # import 關係
    CALLS = "calls"               # 函數調用
    INHERITS = "inherits"        # 繼承關係
    CONFIGURES = "configures"     # 配置關係


@dataclass
class Dependency:
    """依賴關係"""
    source: str    # 來源節點
    target: str    # 目標節點
    dep_type: DependencyType
    weight: float = 1.0           # 權重


@dataclass
class ChangeImpact:
    """變更影響"""
    changed_file: str
    affected_tests: List[str]
    affected_modules: List[str]
    risk_score: float            # 0-100
    recommendations: List[str]


class DependencyGraph:
    """
    依賴圖
    
    節點：檔案、模組、測試
    邊：依賴關係
    """
    
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Dependency] = []
        self.adjacency: Dict[str, List[str]] = {}  # node -> [dependent nodes]
        self.reverse_adjacency: Dict[str, List[str]] = {}  # node -> [dependencies]
    
    def add_node(self, node: str):
        """添加節點"""
        self.nodes.add(node)
        if node not in self.adjacency:
            self.adjacency[node] = []
        if node not in self.reverse_adjacency:
            self.reverse_adjacency[node] = []
    
    def add_edge(self, source: str, target: str, dep_type: DependencyType, weight: float = 1.0):
        """添加邊"""
        self.add_node(source)
        self.add_node(target)
        
        edge = Dependency(source, target, dep_type, weight)
        self.edges.append(edge)
        
        self.adjacency[source].append(target)
        self.reverse_adjacency[target].append(source)
    
    def get_dependents(self, node: str) -> List[str]:
        """取得節點的依賴者（哪些節點依賴這個節點）"""
        return self.reverse_adjacency.get(node, [])
    
    def get_dependencies(self, node: str) -> List[str]:
        """取得節點的依賴（節點依賴哪些節點）"""
        return self.adjacency.get(node, [])
    
    def to_graphviz(self) -> str:
        """導出 Graphviz 格式"""
        lines = [
            "digraph DependencyGraph {",
            "  rankdir=LR;",
            "  node [shape=box];",
        ]
        
        # 節點
        for node in sorted(self.nodes):
            node_type = self._get_node_type(node)
            shape = "ellipse" if "test" in node else "box"
            lines.append(f'  "{node}" [shape={shape}];')
        
        # 邊
        for edge in self.edges:
            lines.append(f'  "{edge.source}" -> "{edge.target}" [label="{edge.dep_type.value}"];')
        
        lines.append("}")
        return "\n".join(lines)
    
    def _get_node_type(self, node: str) -> str:
        if "test" in node:
            return "test"
        elif "src" in node or "lib" in node:
            return "source"
        else:
            return "module"


class ImpactAnalyzer:
    """
    影響分析器
    
    功能：
    - 掃描專案建立依賴圖
    - 分析變更影響
    - 量化回歸風險
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.graph = DependencyGraph()
        self.test_files: Dict[str, str] = {}  # test_file -> source_file
    
    def scan_project(self):
        """掃描專案建立依賴圖"""
        # 掃描原始碼
        for root, dirs, files in os.walk(self.project_path):
            # 忽略特定目錄
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._analyze_file(filepath)
    
    def _analyze_file(self, filepath: str):
        """分析單一檔案"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分析 import
            self._analyze_imports(filepath, content)
            
            # 如果是測試檔案，建立測試-源檔案映射
            if 'test' in filepath:
                self._link_test_to_source(filepath, content)
        except Exception:
            pass
    
    def _analyze_imports(self, filepath: str, content: str):
        """分析 import 依賴"""
        # 簡單的 import 分析
        for match in re.finditer(r'^import\s+(\w+)', content, re.MULTILINE):
            module = match.group(1)
            self.graph.add_edge(filepath, module, DependencyType.IMPORTS)
        
        for match in re.finditer(r'^from\s+(\w+)', content, re.MULTILINE):
            module = match.group(1)
            self.graph.add_edge(filepath, module, DependencyType.IMPORTS)
    
    def _link_test_to_source(self, test_file: str, content: str):
        """建立測試到源檔案的映射"""
        # 簡單的映射：test_foo.py -> foo.py
        basename = os.path.basename(test_file)
        if basename.startswith('test_'):
            source_name = basename[5:]
            # 嘗試找到對應的源檔案
            test_dir = os.path.dirname(test_file)
            possible_source = os.path.join(test_dir, source_name)
            if os.path.exists(possible_source):
                self.test_files[test_file] = possible_source
                self.graph.add_edge(test_file, possible_source, DependencyType.CALLS)
    
    def analyze_change(self, changed_file: str) -> ChangeImpact:
        """
        分析變更影響
        
        Args:
            changed_file: 變更的檔案
        
        Returns:
            ChangeImpact: 變更影響報告
        """
        # 找到所有會被影響的測試
        affected_tests = []
        affected_modules = []
        
        # 遍歷圖，找到依賴於這個檔案的所有節點
        visited = set()
        queue = [changed_file]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # 檢查是否為測試檔案
            if 'test' in current and current != changed_file:
                affected_tests.append(current)
            
            # 找到依賴於當前節點的所有節點
            for dependent in self.graph.get_dependents(current):
                if dependent not in visited:
                    queue.append(dependent)
                    if not any('test' in d for d in affected_modules):
                        affected_modules.append(dependent)
        
        # 計算風險分數
        risk_score = self._calculate_risk(changed_file, affected_tests)
        
        # 生成建議
        recommendations = []
        if affected_tests:
            recommendations.append(
                f"建議在提交前運行 {len(affected_tests)} 個相關測試"
            )
        if risk_score > 70:
            recommendations.append("高風險變更，建議進行 code review")
        
        return ChangeImpact(
            changed_file=changed_file,
            affected_tests=affected_tests,
            affected_modules=affected_modules,
            risk_score=risk_score,
            recommendations=recommendations
        )
    
    def _calculate_risk(self, changed_file: str, affected_tests: List[str]) -> float:
        """計算風險分數"""
        base_risk = 20
        
        # 變更類型
        if any(x in changed_file for x in ['core', 'base', 'foundation']):
            base_risk += 30
        
        # 測試數量
        if len(affected_tests) > 10:
            base_risk += 20
        elif len(affected_tests) > 5:
            base_risk += 10
        
        return min(100, base_risk)
    
    def get_dependency_report(self) -> dict:
        """取得依賴報告"""
        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "test_files": len(self.test_files),
            "graphviz": self.graph.to_graphviz(),
        }


def analyze_change_impact(changed_file: str) -> ChangeImpact:
    """
    便捷函數：分析變更影響
    
    Args:
        changed_file: 變更的檔案
    
    Returns:
        ChangeImpact: 變更影響報告
    """
    analyzer = ImpactAnalyzer()
    analyzer.scan_project()
    return analyzer.analyze_change(changed_file)
