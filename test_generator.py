#!/usr/bin/env python3
"""
Test Generator - 測試自動生成

根據代碼自動生成測試
"""

import os
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TestCase:
    """測試用例"""
    name: str
    function: str
    inputs: Dict[str, Any]
    expected: Any
    description: str = ""


class TestGenerator:
    """測試生成器"""
    
    def __init__(self):
        """初始化"""
        self.test_cases: List[TestCase] = []
    
    def analyze_function(self, code: str, func_name: str) -> Dict:
        """
        分析函數
        
        Args:
            code: 代碼
            func_name: 函數名
            
        Returns:
            函數資訊
        """
        # 提取函數定義
        pattern = rf'def {func_name}\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        match = re.search(pattern, code)
        
        if not match:
            return {}
        
        params_str = match.group(1)
        return_type = match.group(2)
        
        params = []
        if params_str:
            for p in params_str.split(','):
                p = p.strip()
                if p:
                    name = p.split('=')[0].strip()
                    params.append({"name": name, "type": "any"})
        
        return {
            "name": func_name,
            "params": params,
            "return_type": return_type.strip() if return_type else None
        }
    
    def generate_test_cases(self, func_info: Dict) -> List[TestCase]:
        """
        生成測試用例
        
        Args:
            func_info: 函數資訊
            
        Returns:
            測試用例列表
        """
        cases = []
        func_name = func_info.get("name", "function")
        
        # 基本測試
        cases.append(TestCase(
            name=f"test_{func_name}_basic",
            function=func_name,
            inputs={},
            expected=None,
            description="基本測試"
        ))
        
        # 邊界測試
        cases.append(TestCase(
            name=f"{func_name}_edge_cases",
            function=func_name,
            inputs={},
            expected=None,
            description="邊界測試"
        ))
        
        # 錯誤處理測試
        cases.append(TestCase(
            name=f"test_{func_name}_error",
            function=func_name,
            inputs={},
            expected=None,
            description="錯誤處理測試"
        ))
        
        return cases
    
    def generate_pytest(self, func_info: Dict, test_cases: List[TestCase]) -> str:
        """
        生成 pytest 測試
        
        Args:
            func_info: 函數資訊
            test_cases: 測試用例
            
        Returns:
            pytest 代碼
        """
        func_name = func_info.get("name", "function")
        params = func_info.get("params", [])
        
        lines = [
            '"""',
            f"Auto-generated tests for {func_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
            "import pytest",
            f"from module import {func_name}",
            "",
            "",
        ]
        
        # 生成測試函數
        for tc in test_cases:
            lines.append(f"def {tc.name}():")
            lines.append(f'    """{tc.description}"""')
            lines.append("")
            
            # 準備參數
            if params:
                lines.append("    # 準備參數")
                for p in params:
                    lines.append(f"    {p['name']} = None  # TODO: 設定測試值")
                lines.append("")
            
            # 調用函數
            if params:
                params_str = ", ".join(p['name'] for p in params)
                lines.append(f"    result = {func_name}({params_str})")
            else:
                lines.append(f"    result = {func_name}()")
            
            lines.append("")
            lines.append("    # 斷言")
            lines.append("    assert result is not None")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_unittest(self, func_info: Dict, test_cases: List[TestCase]) -> str:
        """
        生成 unittest 測試
        
        Args:
            func_info: 函數資訊
            test_cases: 測試用例
            
        Returns:
            unittest 代碼
        """
        func_name = func_info.get("name", "function")
        params = func_info.get("params", [])
        
        lines = [
            '"""',
            f"Auto-generated tests for {func_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
            "import unittest",
            "",
            "",
            f"class Test{func_name.capitalize()}(unittest.TestCase):",
            "",
        ]
        
        for tc in test_cases:
            lines.append(f"    def {tc.name}(self):")
            lines.append(f'        """{tc.description}"""')
            lines.append("        pass")
            lines.append("")
        
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    unittest.main()")
        
        return "\n".join(lines)
    
    def generate_from_file(self, file_path: str, output_path: str = None, 
                           framework: str = "pytest") -> str:
        """
        從檔案生成測試
        
        Args:
            file_path: 原始檔案路徑
            output_path: 輸出路徑
            framework: 測試框架 (pytest/unittest)
            
        Returns:
            測試代碼
        """
        # 讀取原始檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 解析所有函數
        pattern = r'def (\w+)\(([^)]*)\):'
        matches = re.finditer(pattern, code)
        
        all_tests = []
        
        for match in matches:
            func_name = match.group(1)
            func_info = self.analyze_function(code, func_name)
            
            if func_info:
                test_cases = self.generate_test_cases(func_info)
                all_tests.append((func_info, test_cases))
        
        # 生成測試代碼
        lines = [
            '"""',
            f"Auto-generated tests",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
            f"# Source: {file_path}",
            "",
        ]
        
        for func_info, test_cases in all_tests:
            if framework == "pytest":
                lines.append(self.generate_pytest(func_info, test_cases))
            else:
                lines.append(self.generate_unittest(func_info, test_cases))
            lines.append("")
        
        test_code = "\n".join(lines)
        
        # 寫入檔案
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            print(f"Generated: {output_path}")
        
        return test_code


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_generator.py <file.py>")
        print("  python test_generator.py <file.py> -o test_file.py")
        print("  python test_generator.py <file.py> -f unittest")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = None
    framework = "pytest"
    
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if len(sys.argv) > idx + 1:
            output_path = sys.argv[idx + 1]
    
    if "-f" in sys.argv:
        idx = sys.argv.index("-f")
        if len(sys.argv) > idx + 1:
            framework = sys.argv[idx + 1]
    
    generator = TestGenerator()
    test_code = generator.generate_from_file(file_path, output_path, framework)
    
    if not output_path:
        print(test_code)
