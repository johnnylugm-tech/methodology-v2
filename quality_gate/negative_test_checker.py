#!/usr/bin/env python3
"""
Negative Test Checker - 負面測試檢查器
=================================
檢查負面測試是否覆蓋關鍵約束

使用方式：
    python3 quality_gate/negative_test_checker.py --project-dir /path/to/project

Pass 條件：
    - P3-13: 負面測試覆蓋關鍵約束 = 必需
    - P4-4: 負面測試包含關鍵約束 = 必需

門檻：100% 覆蓋
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class NegativeTestChecker:
    """負面測試檢查器"""
    
    CONSTRAINT_TYPES = {
        'input_validation': ['null', 'empty', 'invalid', 'format', 'range', 'type', 'length', 'max', 'min'],
        'boundary': ['edge', 'boundary', 'max', 'min', 'overflow', 'underflow', 'limit'],
        'error_handling': ['error', 'exception', 'fail', 'timeout', 'retry', 'fallback'],
        'security': ['auth', 'permission', 'injection', 'xss', 'csrf', 'sql'],
        'concurrency': ['race', 'concurrent', 'parallel', 'thread', 'lock', 'sync']
    }
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.fr_ids: Set[str] = set()
        self.negative_tests: List[Dict] = []
    
    def run(self, project_path: str = None) -> Dict:
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        self._extract_fr_ids()
        self._extract_negative_tests()
        return self._calculate_result()
    
    def _extract_fr_ids(self):
        srs_paths = [self.project_path / 'docs' / 'SRS.md', self.project_path / 'SRS.md']
        
        for srs_path in srs_paths:
            if srs_path.exists():
                content = srs_path.read_text(encoding='utf-8')
                pattern = r'FR-\d+'
                self.fr_ids = set(re.findall(pattern, content))
                if self.fr_ids:
                    if self.verbose:
                        print(f"Found {len(self.fr_ids)} FR-ID")
                    break
    
    def _extract_negative_tests(self):
        tests_dirs = [self.project_path / 'tests', self.project_path / 'test']
        
        for tests_dir in tests_dirs:
            if not tests_dir.exists():
                continue
            
            for test_file in tests_dir.rglob('*.py'):
                content = test_file.read_text(encoding='utf-8')
                self._extract_from_file(test_file, content)
    
    def _extract_from_file(self, file_path: Path, content: str):
        test_funcs = re.findall(r'def\s+(test_\w+)', content)
        
        for func in test_funcs:
            func_content_match = re.search(rf'def\s+{func}\([^)]*\):[^\n]*\n((?:\s+.+\n)+)', content)
            if not func_content_match:
                continue
            
            func_content = func_content_match.group(1)
            func_lower = func.lower()
            content_lower = func_content.lower()
            
            is_negative = any(kw in func_lower or kw in content_lower for kw in ['error', 'fail', 'invalid', 'exception', 'null', 'empty', 'wrong', 'denied', 'reject', 'negative'])
            
            if is_negative:
                fr_refs = re.findall(r'FR-\d+', func_content)
                
                constraint_types = []
                for ctype, keywords in self.CONSTRAINT_TYPES.items():
                    if any(kw in content_lower for kw in keywords):
                        constraint_types.append(ctype)
                
                self.negative_tests.append({
                    'test_file': str(file_path),
                    'test_function': func,
                    'fr_refs': fr_refs,
                    'constraint_types': constraint_types
                })
    
    def _calculate_result(self) -> Dict:
        total_fr = len(self.fr_ids)
        
        if total_fr == 0:
            return {'passed': True, 'coverage_rate': 100, 'total_fr': 0, 'covered_fr': 0, 'uncovered_fr': [], 'details': [], 'threshold': 100, 'phase_conditions': ['P3-13', 'P4-4']}
        
        fr_with_negative_tests = set()
        for test in self.negative_tests:
            for fr in test['fr_refs']:
                fr_with_negative_tests.add(fr)
        
        uncovered = [fr for fr in self.fr_ids if fr not in fr_with_negative_tests]
        
        coverage_rate = (len(fr_with_negative_tests) / total_fr * 100) if total_fr > 0 else 0
        passed = coverage_rate == 100
        
        details = []
        for test in self.negative_tests:
            details.append({
                'test': test['test_function'],
                'file': test['test_file'],
                'fr_refs': test['fr_refs'],
                'constraint_types': test['constraint_types']
            })
        
        return {'passed': passed, 'coverage_rate': round(coverage_rate, 2), 'total_fr': total_fr, 'covered_fr': len(fr_with_negative_tests), 'uncovered_fr': uncovered, 'total_negative_tests': len(self.negative_tests), 'details': details, 'threshold': 100, 'phase_conditions': ['P3-13', 'P4-4']}


def main():
    parser = argparse.ArgumentParser(description='負面測試檢查器')
    parser.add_argument('--project-dir', type=str, default='.', help='專案目錄路徑')
    parser.add_argument('--output', type=str, default=None, help='輸出 JSON 檔案路徑')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細輸出')
    args = parser.parse_args()
    
    checker = NegativeTestChecker(args.project_dir, args.verbose)
    result = checker.check()
    
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json_output, encoding='utf-8')
        print(f"Report saved to: {args.output}")
    else:
        print(json_output)
    
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
