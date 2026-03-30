#!/usr/bin/env python3
"""
Naming Convention Checker - 命名規範檢查工具
=========================================
檢查 snake_case/PascalCase 命名規範

使用方式：
    python3 quality_gate/naming_convention_checker.py --project-dir /path/to/project
    python3 quality_gate/naming_convention_checker.py --project-dir . --output report.json

輸出：
    JSON 命名規範報告
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


class NamingConventionChecker:
    """命名規範檢查器"""
    
    # Python 命名規範
    MODULE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')  # snake_case
    CLASS_PATTERN = re.compile(r'^([A-Z][a-zA-Z0-9]*|[A-Z][a-z]+[A-Z][a-zA-Z]*)$')  # PascalCase
    FUNCTION_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')  # snake_case
    CONSTANT_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]*$')  # UPPER_SNAKE_CASE
    VARIABLE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')  # snake_case
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.violations: List[Dict] = []
    
    def check(self) -> Dict:
        """執行命名規範檢查"""
        # 1. 檢查模組命名
        self._check_module_names()
        
        # 2. 檢查類命名
        self._check_class_names()
        
        # 3. 檢查函數命名
        self._check_function_names()
        
        # 4. 檢查常數命名
        self._check_constant_names()
        
        # 5. 計算統計
        critical = len([v for v in self.violations if v.get('severity') == 'HIGH'])
        
        return {
            'passed': critical == 0,
            'total_violations': len(self.violations),
            'details': self.violations
        }
    
    def _check_module_names(self):
        """檢查模組（檔案）命名"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        for py_file in src_dir.rglob('*.py'):
            name = py_file.stem
            
            # 跳過特殊名稱
            if name.startswith('__') or name in ['__init__', 'conftest']:
                continue
            
            # 檢查是否符合 snake_case
            if not self.MODULE_PATTERN.match(name):
                self.violations.append({
                    'type': 'module',
                    'severity': 'MEDIUM',
                    'file': str(py_file.relative_to(self.project_path)),
                    'name': name,
                    'expected': 'snake_case (e.g., my_module.py)',
                    'actual': name
                })
    
    def _check_class_names(self):
        """檢查類命名"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 檢查 class 定義
                if line.startswith('class '):
                    match = re.search(r'class\s+(\w+)', line)
                    if match:
                        class_name = match.group(1)
                        
                        # 檢查是否符合 PascalCase
                        if not self.CLASS_PATTERN.match(class_name):
                            self.violations.append({
                                'type': 'class',
                                'severity': 'HIGH',
                                'file': str(py_file.relative_to(self.project_path)),
                                'line': i + 1,
                                'name': class_name,
                                'expected': 'PascalCase (e.g., MyClass)',
                                'actual': class_name
                            })
    
    def _check_function_names(self):
        """檢查函數/方法命名"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 檢查 def 定義
                if line.startswith('def '):
                    match = re.search(r'def\s+(\w+)', line)
                    if match:
                        func_name = match.group(1)
                        
                        # 跳過魔術方法
                        if func_name.startswith('__') and func_name.endswith('__'):
                            continue
                        
                        # 檢查是否符合 snake_case
                        if not self.FUNCTION_PATTERN.match(func_name):
                            self.violations.append({
                                'type': 'function',
                                'severity': 'MEDIUM',
                                'file': str(py_file.relative_to(self.project_path)),
                                'line': i + 1,
                                'name': func_name,
                                'expected': 'snake_case (e.g., my_function)',
                                'actual': func_name
                            })
    
    def _check_constant_names(self):
        """檢查常數命名"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 檢查常量定義（大寫）
                if re.match(r'^[A-Z][A-Z0-9_]*\s*=', line):
                    match = re.search(r'^([A-Z][A-Z0-9_]*)', line)
                    if match:
                        const_name = match.group(1)
                        
                        # 跳過特例
                        if const_name in ['True', 'False', 'None', 'DEBUG']:
                            continue
                        
                        # 檢查是否符合 UPPER_SNAKE_CASE
                        if not self.CONSTANT_PATTERN.match(const_name):
                            self.violations.append({
                                'type': 'constant',
                                'severity': 'MEDIUM',
                                'file': str(py_file.relative_to(self.project_path)),
                                'line': i + 1,
                                'name': const_name,
                                'expected': 'UPPER_SNAKE_CASE (e.g., MY_CONSTANT)',
                                'actual': const_name
                            })


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='命名規範檢查工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/naming_convention_checker.py
  python3 quality_gate/naming_convention_checker.py --project-dir /path/to/project
  python3 quality_gate/naming_convention_checker.py --project-dir . --output report.json
        '''
    )
    
    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='專案目錄路徑（預設：當前目錄）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='輸出 JSON 檔案路徑（可選）'
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        default=None,
        help='Phase 編號（用於 unified_gate 整合）'
    )
    
    args = parser.parse_args()
    
    # 執行命名規範檢查
    checker = NamingConventionChecker(args.project_dir)
    result = checker.check()
    
    # 輸出結果
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        # 寫入檔案
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding='utf-8')
        print(f'Report saved to: {args.output}')
    else:
        # 輸出到 stdout
        print(json_output)
    
    # 返回狀態碼
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()