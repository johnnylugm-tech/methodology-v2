#!/usr/bin/env python3
"""
Coupling Analyzer
================
分析模組之間的耦合度
"""

import ast
from typing import Dict, Set
from collections import defaultdict
from dataclasses import dataclass

class CouplingAnalyzer:
    """
    分析模組耦合度
    
    使用方式：
    
    ```python
    analyzer = CouplingAnalyzer()
    result = analyzer.analyze_directory("src/")
    
    print(f"Afferent Coupling: {result.afferent}")
    print(f"Efferent Coupling: {result.efferent}")
    print(f"Instability: {result.instability}")
    ```
    """
    
    def __init__(self):
        self.modules = {}
        self.imports = defaultdict(set)
        self.imported_by = defaultdict(set)
    
    def analyze_directory(self, dir_path: str) -> 'CouplingResult':
        """分析目錄下所有 Python 檔案"""
        import os
        
        for root, _, files in os.walk(dir_path):
            for f in files:
                if f.endswith('.py') and not f.startswith('__'):
                    file_path = os.path.join(root, f)
                    try:
                        self._analyze_file(file_path)
                    except:
                        pass
        
        return self._calculate_metrics()
    
    def _analyze_file(self, file_path: str):
        """分析單個檔案的 imports"""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        module_name = file_path.replace('/', '.').replace('.py', '')
        self.modules[module_name] = file_path
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports[module_name].add(alias.name)
                    self.imported_by[alias.name].add(module_name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.imports[module_name].add(node.module)
                    self.imported_by[node.module].add(module_name)
    
    def _calculate_metrics(self) -> 'CouplingResult':
        """計算耦合指標"""
        afferent = len(self.imported_by)
        efferent = len(self.imports)
        total = afferent + efferent
        
        instability = efferent / total if total > 0 else 0
        
        return CouplingResult(
            afferent=afferent,
            efferent=efferent,
            instability=instability,
            modules=self.modules
        )

@dataclass
class CouplingResult:
    afferent: int  # 被其他模組導入
    efferent: int  # 導入其他模組
    instability: float  # 不穩定性 (0-1)
    modules: Dict