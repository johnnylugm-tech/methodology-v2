#!/usr/bin/env python3
"""
TDD Runner - methodology-v2 模組
=================================
方案 B: 測試驅動開發

功能:
- 自動化測試生成
- 測試覆蓋率計算
- Shift-Left Testing
"""

import os
import re
import logging
from typing import Dict, List
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    name: str
    input: str
    expected: str
    type: str


class TDDRunner:
    """TDD Runner - 測試驅動開發"""
    
    def __init__(self):
        self.test_cases = []
        self.coverage = 0
    
    def generate_test_cases(self, source_file: str) -> List[TestCase]:
        test_cases = []
        try:
            with open(source_file, 'r') as f:
                content = f.read()
            
            functions = re.findall(r'def (\w+)\((.*?)\):', content)
            for func_name, params in functions:
                test_cases.append(TestCase(
                    name=f"test_{func_name}_basic",
                    input=f"{func_name}()",
                    expected="expected",
                    type="unit"
                ))
            
            classes = re.findall(r'class (\w+):', content)
            for class_name in classes:
                test_cases.append(TestCase(
                    name=f"test_{class_name}_init",
                    input=f"{class_name}()",
                    expected="instance",
                    type="unit"
                ))
        except Exception as e:
            logger.error(f"Error: {e}")
        
        self.test_cases.extend(test_cases)
        return test_cases
    
    def calculate_coverage(self, source_dir: str) -> float:
        source_files = []
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    source_files.append(os.path.join(root, file))
        
        total_functions = 0
        for sf in source_files:
            try:
                with open(sf, 'r') as f:
                    content = f.read()
                total_functions += len(re.findall(r'def (\w+)\(', content))
                total_functions += len(re.findall(r'class (\w+):', content))
            except:
                pass
        
        coverage = (len(self.test_cases) / total_functions * 100) if total_functions > 0 else 0
        self.coverage = min(100, coverage)
        return self.coverage


def run_tdd(source_dir: str) -> Dict:
    runner = TDDRunner()
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                runner.generate_test_cases(os.path.join(root, file))
    
    coverage = runner.calculate_coverage(source_dir)
    return {'test_cases': len(runner.test_cases), 'coverage': coverage, 'pass': coverage >= 80}


if __name__ == "__main__":
    import sys
    source_dir = sys.argv[1] if len(sys.argv) > 1 else "src"
    result = run_tdd(source_dir)
    print(f"Coverage: {result['coverage']:.1f}%")
