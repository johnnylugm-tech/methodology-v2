#!/usr/bin/env python3
"""
Complexity Checker
================
計算函數的 cyclomatic complexity
"""

import ast
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FunctionComplexity:
    name: str
    file: str
    line: int
    complexity: int
    threshold: int = 10

class ComplexityChecker:
    """
    檢查代碼複雜度
    
    使用方式：
    
    ```python
    checker = ComplexityChecker()
    result = checker.check_file("src/main.py")
    
    for func in result.violations:
        print(f"{func.name}: {func.complexity} (limit: {func.threshold})")
    ```
    """
    
    def __init__(self, threshold: int = 10):
        self.threshold = threshold
    
    def check_file(self, file_path: str) -> 'ComplexityResult':
        """檢查單個檔案"""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > self.threshold:
                    violations.append(FunctionComplexity(
                        name=node.name,
                        file=file_path,
                        line=node.lineno,
                        complexity=complexity,
                        threshold=self.threshold
                    ))
        
        return ComplexityResult(
            file=file_path,
            total_functions=len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
            violations=violations,
            passed=len(violations) == 0
        )
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """計算複雜度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

@dataclass
class ComplexityResult:
    file: str
    total_functions: int
    violations: List[FunctionComplexity]
    passed: bool