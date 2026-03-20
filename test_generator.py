#!/usr/bin/env python3
"""
Test Generator - 測試自動生成 v2

增強版：支援 Mock、Fixtures、Parameterized Tests、Coverage 分析
"""

import os
import re
import ast
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum


class TestFramework(Enum):
    """測試框架"""
    PYTEST = "pytest"
    UNITTEST = "unittest"
    BOTH = "both"


class MockStrategy(Enum):
    """Mock 策略"""
    AUTO = "auto"
    MANUAL = "manual"
    NONE = "none"


@dataclass
class TestCase:
    """測試用例"""
    name: str
    function: str
    inputs: Dict[str, Any]
    expected: Any
    description: str = ""
    tags: List[str] = field(default_factory=list)
    mock_calls: List[str] = field(default_factory=list)


@dataclass
class ParameterizedCase:
    """參數化測試"""
    test_name: str
    params: List[Dict[str, Any]]
    expected_key: str = "expected"


@dataclass
class FunctionInfo:
    """函數資訊"""
    name: str
    params: List[Dict]
    return_type: str = None
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    complexity: int = 1


class TestGenerator:
    """測試生成器 v2"""
    
    # 類型映射
    TYPE_MAPPING = {
        "str": '""',
        "int": "0",
        "float": "0.0",
        "bool": "True",
        "list": "[]",
        "dict": "{}",
        "tuple": "()",
        "None": "None",
    }
    
    def __init__(self, framework: TestFramework = TestFramework.PYTEST):
        self.framework = framework
        self.test_cases: List[TestCase] = []
        self.functions: List[FunctionInfo] = []
    
    def parse_file(self, file_path: str) -> List[FunctionInfo]:
        """
        解析 Python 檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            函數資訊列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._parse_regex(content)
        
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._parse_function_node(node)
                if func_info:
                    functions.append(func_info)
        
        self.functions = functions
        return functions
    
    def _parse_function_node(self, node: ast.FunctionDef) -> Optional[FunctionInfo]:
        """解析 AST 函數節點"""
        # 取得參數
        params = []
        for arg in node.args.args:
            param_type = None
            if arg.annotation:
                param_type = self._get_annotation_name(arg.annotation)
            params.append({
                "name": arg.arg,
                "type": param_type,
                "default": self._get_default_value(arg)
            })
        
        # 取得回傳類型
        return_type = None
        if node.returns:
            return_type = self._get_annotation_name(node.returns)
        
        # 取得 docstring
        docstring = ast.get_docstring(node) or ""
        
        # 取得裝飾器
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        return FunctionInfo(
            name=node.name,
            params=params,
            return_type=return_type,
            docstring=docstring,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            complexity=self._estimate_complexity(node)
        )
    
    def _get_annotation_name(self, node: ast.AST) -> str:
        """取得類型註釋名稱"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_annotation_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation_name(node.value)}[{self._get_annotation_name(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        return "Any"
    
    def _get_decorator_name(self, node: ast.AST) -> str:
        """取得裝飾器名稱"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return node.attr
        return "unknown"
    
    def _get_default_value(self, arg: ast.arg) -> Any:
        """取得參數預設值"""
        # 簡化版本
        return None
    
    def _estimate_complexity(self, node: ast.FunctionDef) -> int:
        """估算複雜度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += 1
        return complexity
    
    def _parse_regex(self, code: str) -> List[FunctionInfo]:
        """使用正則表達式解析"""
        functions = []
        pattern = r'def (\w+)\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        
        for match in re.finditer(pattern, code):
            func_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3)
            
            params = []
            if params_str:
                for p in params_str.split(','):
                    p = p.strip()
                    if p:
                        name = p.split('=')[0].strip()
                        params.append({"name": name, "type": "Any"})
            
            functions.append(FunctionInfo(
                name=func_name,
                params=params,
                return_type=return_type.strip() if return_type else None
            ))
        
        return functions
    
    def generate_test_cases(self, func_info: FunctionInfo) -> List[TestCase]:
        """
        生成測試用例
        
        Args:
            func_info: 函數資訊
            
        Returns:
            測試用例列表
        """
        cases = []
        func_name = func_info.name
        
        # 1. 基本測試
        cases.append(TestCase(
            name=f"test_{func_name}_basic",
            function=func_name,
            inputs=self._generate_inputs(func_info.params),
            expected=self._generate_expected(func_info.return_type),
            description=f"基本測試: {func_name}",
            tags=["basic"]
        ))
        
        # 2. 邊界值測試
        cases.append(TestCase(
            name=f"test_{func_name}_edge_cases",
            function=func_name,
            inputs=self._generate_edge_inputs(func_info.params),
            expected=None,
            description=f"邊界值測試: {func_name}",
            tags=["edge"]
        ))
        
        # 3. 錯誤處理測試
        if func_info.complexity > 2:
            cases.append(TestCase(
                name=f"test_{func_name}_error_handling",
                function=func_name,
                inputs=self._generate_error_inputs(func_info.params),
                expected=Exception,
                description=f"錯誤處理測試: {func_name}",
                tags=["error"]
            ))
        
        # 4. 類型測試
        cases.append(TestCase(
            name=f"test_{func_name}_type_check",
            function=func_name,
            inputs=self._generate_inputs(func_info.params),
            expected=None,
            description=f"類型檢查: {func_name}",
            tags=["type"]
        ))
        
        return cases
    
    def _generate_inputs(self, params: List[Dict]) -> Dict[str, Any]:
        """生成測試輸入"""
        inputs = {}
        for p in params:
            ptype = p.get("type", "Any")
            default = p.get("default")
            
            if default is not None:
                inputs[p["name"]] = default
            elif ptype in self.TYPE_MAPPING:
                try:
                    inputs[p["name"]] = eval(self.TYPE_MAPPING[ptype])
                except:
                    inputs[p["name"]] = None
            else:
                inputs[p["name"]] = None
        
        return inputs
    
    def _generate_edge_inputs(self, params: List[Dict]) -> Dict[str, Any]:
        """生成邊界值輸入"""
        inputs = {}
        for p in params:
            ptype = p.get("type", "Any")
            
            if ptype == "int":
                inputs[p["name"]] = 0
            elif ptype == "float":
                inputs[p["name"]] = 0.0
            elif ptype == "str":
                inputs[p["name"]] = ""
            elif ptype == "list":
                inputs[p["name"]] = []
            elif ptype == "dict":
                inputs[p["name"]] = {}
            else:
                inputs[p["name"]] = None
        
        return inputs
    
    def _generate_error_inputs(self, params: List[Dict]) -> Dict[str, Any]:
        """生成錯誤輸入"""
        inputs = {}
        for p in params:
            inputs[p["name"]] = None  # None 通常會觸發錯誤
        return inputs
    
    def _generate_expected(self, return_type: str) -> Any:
        """生成預期輸出"""
        if return_type and return_type in self.TYPE_MAPPING:
            try:
                return eval(self.TYPE_MAPPING[return_type])
            except:
                pass
        return None
    
    def generate_pytest(self, func_info: FunctionInfo, 
                       test_cases: List[TestCase],
                       fixtures: bool = True,
                       mocks: bool = True) -> str:
        """
        生成 pytest 測試
        
        Args:
            func_info: 函數資訊
            test_cases: 測試用例
            fixtures: 是否生成 fixtures
            mocks: 是否生成 mocks
            
        Returns:
            pytest 代碼
        """
        func_name = func_info.name
        params = func_info.params
        is_async = func_info.is_async
        
        lines = [
            '"""',
            f"Auto-generated tests for {func_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
            "import pytest",
            "from unittest.mock import Mock, patch, MagicMock",
            f"from module import {func_name}",
            "",
        ]
        
        # 生成 fixtures
        if fixtures and params:
            lines.append("")
            lines.append("@pytest.fixture")
            lines.append("def sample_inputs():")
            lines.append('    """樣例輸入 fixture"""')
            lines.append("    return {")
            for p in params:
                lines.append(f'        "{p["name"]}": None,  # TODO: 設定值')
            lines.append("    }")
        
        # 生成 mock fixtures
        if mocks:
            lines.append("")
            lines.append("@pytest.fixture")
            lines.append("def mock_external_service():")
            lines.append('    """Mock 外部服務"""')
            lines.append("    with patch('module.external_service') as mock:")
            lines.append("        mock.return_value = {'status': 'ok'}")
            lines.append("        yield mock")
        
        # 生成測試函數
        lines.append("")
        for tc in test_cases:
            lines.append(self._generate_pytest_function(tc, params, is_async, fixtures, mocks))
        
        # 生成參數化測試
        lines.append("")
        lines.append(self._generate_parametrized_test(func_info))
        
        return "\n".join(lines)
    
    def _generate_pytest_function(self, tc: TestCase, params: List[Dict],
                                  is_async: bool, fixtures: bool,
                                  mocks: bool) -> str:
        """生成單個 pytest 函數"""
        func_name = tc.function
        
        # 函數定義
        async_prefix = "async " if is_async else ""
        lines = [f"def {async_prefix}{tc.name}():",
                 f'    """測試用例: {tc.description}"""']
        
        # 使用 fixtures
        if fixtures and params:
            lines.append("    inputs = sample_inputs()")
            if mocks:
                lines.append("    mock_service = mock_external_service()")
        
        # 準備參數
        if params:
            lines.append("")
            lines.append("    # 準備參數")
            for p in params:
                lines.append(f"    {p['name']} = inputs['{p['name']}']")
        
        # Mock 設定
        if tc.mock_calls:
            lines.append("")
            for mock_call in tc.mock_calls:
                lines.append(f"    {mock_call}")
        
        # 調用函數
        lines.append("")
        params_str = ", ".join(p['name'] for p in params) if params else ""
        if is_async:
            lines.append(f"    result = await {func_name}({params_str})")
        else:
            lines.append(f"    result = {func_name}({params_str})")
        
        # 斷言
        lines.append("")
        lines.append("    # 斷言")
        if tc.expected is None:
            lines.append("    assert result is not None  # TODO: 修正斷言")
        elif tc.expected == Exception:
            lines.append("    with pytest.raises(Exception):")
            lines.append(f"        {func_name}({params_str})")
            return "\n".join(lines)
        else:
            lines.append(f"    expected = {repr(tc.expected)}")
            lines.append("    assert result == expected")
        
        return "\n".join(lines)
    
    def _generate_parametrized_test(self, func_info: FunctionInfo) -> str:
        """生成參數化測試"""
        func_name = func_info.name
        params = func_info.params
        
        lines = [
            "@pytest.mark.parametrize(",
            '    "test_case",',
            '    [',
            '        {"name": "basic", "params": {...}},',
            '        {"name": "edge", "params": {...}},',
            '        {"name": "error", "params": {...}},',
            '    ]',
            ")"
        ]
        
        return "\n".join(lines)
    
    def generate_unittest(self, func_info: FunctionInfo,
                         test_cases: List[TestCase]) -> str:
        """生成 unittest 測試"""
        func_name = func_info.name
        params = func_info.params
        
        lines = [
            '"""',
            f"Auto-generated tests for {func_name}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            '"""',
            "",
            "import unittest",
            "from unittest.mock import Mock, patch",
            f"from module import {func_name}",
            "",
            "",
            f"class Test{func_name.capitalize()}(unittest.TestCase):",
            "",
        ]
        
        for tc in test_cases:
            lines.append(f"    def {tc.name}(self):")
            lines.append(f'        """{tc.description}"""')
            
            # 準備參數
            if params:
                lines.append("        # 準備參數")
                for p in params:
                    lines.append(f"        {p['name']} = None  # TODO: 設定值")
                lines.append("")
            
            # 調用
            params_str = ", ".join(p['name'] for p in params) if params else ""
            lines.append(f"        result = {func_name}({params_str})")
            
            # 斷言
            lines.append("")
            lines.append("        # 斷言")
            if tc.expected is None:
                lines.append("        self.assertIsNotNone(result)  # TODO: 修正")
            elif tc.expected == Exception:
                lines.append("        self.assertRaises(Exception, ")
                lines.append(f"            lambda: {func_name}({params_str}))")
            else:
                lines.append(f"        self.assertEqual(result, {repr(tc.expected)})")
            
            lines.append("")
        
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    unittest.main()")
        
        return "\n".join(lines)
    
    def generate_coverage_config(self, functions: List[FunctionInfo]) -> str:
        """生成 coverage 配置"""
        func_names = [f.name for f in functions]
        
        lines = [
            "[run]",
            "source = src",
            "omit =",
            "    */tests/*",
            "    */__pycache__/*",
            "",
            "[report]",
            "exclude_lines =",
            "    pragma: no cover",
            "    def __repr__",
            "    raise NotImplementedError",
            "    if __name__ == .__main__.:",
            "",
            f"functions = {', '.join(func_names)}",
        ]
        
        return "\n".join(lines)
    
    def generate_ci_config(self) -> str:
        """生成 CI 配置"""
        return """# pytest.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-report=html
    - name: Upload coverage
      uses: codecov/codecov-action@v4
"""
    
    def generate_from_file(self, file_path: str, output_dir: str = None,
                          framework: TestFramework = TestFramework.PYTEST) -> Dict:
        """
        從檔案生成測試
        
        Args:
            file_path: 原始檔案路徑
            output_dir: 輸出目錄
            framework: 測試框架
            
        Returns:
            生成結果
        """
        # 解析檔案
        functions = self.parse_file(file_path)
        
        if not functions:
            return {"error": "No functions found", "file": file_path}
        
        results = {
            "file": file_path,
            "functions": len(functions),
            "tests": [],
            "errors": []
        }
        
        # 確保輸出目錄存在
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 為每個函數生成測試
        for func_info in functions:
            try:
                test_cases = self.generate_test_cases(func_info)
                
                if framework in [TestFramework.PYTEST, TestFramework.BOTH]:
                    test_code = self.generate_pytest(func_info, test_cases)
                    output_path = os.path.join(output_dir or ".", 
                                             f"test_{func_info.name}.py")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(test_code)
                    results["tests"].append(output_path)
                
                if framework == TestFramework.UNITTEST:
                    test_code = self.generate_unittest(func_info, test_cases)
                    output_path = os.path.join(output_dir or ".", 
                                             f"test_{func_info.name}_unittest.py")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(test_code)
                    results["tests"].append(output_path)
                    
            except Exception as e:
                results["errors"].append({
                    "function": func_info.name,
                    "error": str(e)
                })
        
        return results


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_generator.py <file.py>")
        print("  python test_generator.py <file.py> -o tests/")
        print("  python test_generator.py <file.py> -f both")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_dir = None
    framework = TestFramework.PYTEST
    
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if len(sys.argv) > idx + 1:
            output_dir = sys.argv[idx + 1]
    
    if "-f" in sys.argv:
        idx = sys.argv.index("-f")
        if len(sys.argv) > idx + 1:
            fw = sys.argv[idx + 1].lower()
            if fw == "unittest":
                framework = TestFramework.UNITTEST
            elif fw == "both":
                framework = TestFramework.BOTH
    
    generator = TestGenerator(framework=framework)
    result = generator.generate_from_file(file_path, output_dir, framework)
    
    print(f"\n✅ Generated {len(result['tests'])} test files")
    for test in result['tests']:
        print(f"   - {test}")
    
    if result.get('errors'):
        print(f"\n⚠️ {len(result['errors'])} errors:")
        for err in result['errors']:
            print(f"   - {err['function']}: {err['error']}")
