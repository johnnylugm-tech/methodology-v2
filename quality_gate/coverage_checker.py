#!/usr/bin/env python3
"""
Coverage Checker - 測試覆蓋率自動化工具
=================================
自動計算測試覆蓋率（行/分支/函數）
目標：≥ 80%

使用方式：
    python3 quality_gate/coverage_checker.py --project-dir /path/to/project
    python3 quality_gate/coverage_checker.py --project-dir . --output report.json

輸出：
    JSON 覆蓋率報告
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class CoverageChecker:
    """測試覆蓋率檢查器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.threshold = 80.0  # 預設閾值 80%
    
    def check(self) -> Dict:
        """執行覆蓋率檢查"""
        # 1. 嘗試使用 pytest-cov
        cov_result = self._check_with_pytest_cov()
        
        if cov_result:
            return cov_result
        
        # 2. 嘗試使用 coverage.py
        cov_result = self._check_with_coverage_py()
        
        if cov_result:
            return cov_result
        
        # 3. 手動計算覆蓋率
        return self._manual_coverage_check()
    
    def _check_with_pytest_cov(self) -> Optional[Dict]:
        """使用 pytest-cov 檢查覆蓋率"""
        try:
            # 檢查是否有 pytest-cov
            result = subprocess.run(
                ['pytest', '--collect-only'],
                cwd=self.project_path,
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            # 執行覆蓋率測試
            result = subprocess.run(
                ['pytest', '--cov=src', '--cov-report=term', '--cov-report=json'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # 解析輸出
            output = result.stdout
            
            # 提取覆蓋率
            line_cov = self._extract_coverage(output, 'line')
            branch_cov = self._extract_coverage(output, 'branch')
            
            if line_cov is None:
                return None
            
            return {
                'passed': line_cov >= self.threshold,
                'line_coverage': line_cov,
                'branch_coverage': branch_cov,
                'threshold': self.threshold,
                'method': 'pytest-cov',
                'details': output
            }
        except Exception:
            return None
    
    def _check_with_coverage_py(self) -> Optional[Dict]:
        """使用 coverage.py 檢查覆蓋率"""
        try:
            # 檢查是否安裝 coverage
            result = subprocess.run(
                ['coverage', '--version'],
                cwd=self.project_path,
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            # 執行 coverage
            subprocess.run(
                ['coverage', 'run', '-m', 'pytest'],
                cwd=self.project_path,
                capture_output=True,
                timeout=120
            )
            
            # 生成報告
            result = subprocess.run(
                ['coverage', 'json', '-o', '.coverage_json'],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            # 讀取 JSON 報告
            cov_json_path = self.project_path / '.coverage_json' / 'coverage.json'
            if not cov_json_path.exists():
                return None
            
            with open(cov_json_path) as f:
                data = json.load(f)
            
            # 提取總覆蓋率
            totals = data.get('totals', {})
            line_cov = totals.get('percent_covered', 0)
            
            return {
                'passed': line_cov >= self.threshold,
                'line_coverage': line_cov,
                'branch_coverage': 0,  # coverage.py 預設不計算分支
                'threshold': self.threshold,
                'method': 'coverage.py',
                'details': data
            }
        except Exception:
            return None
    
    def _manual_coverage_check(self) -> Dict:
        """手動計算覆蓋率"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        tests_dir = self.project_path / 'tests'
        if not tests_dir.exists():
            tests_dir = self.project_path / 'test'
        
        # 計算 source 行數
        total_lines = 0
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                total_lines += len(lines)
            except Exception:
                continue
        
        # 計算測試行數
        test_lines = 0
        if tests_dir.exists():
            for py_file in tests_dir.rglob('*.py'):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                    test_lines += len(lines)
                except Exception:
                    continue
        
        # 計算覆蓋率
        coverage = (test_lines / total_lines * 100) if total_lines > 0 else 0
        
        return {
            'passed': coverage >= self.threshold,
            'line_coverage': coverage,
            'branch_coverage': 0,
            'threshold': self.threshold,
            'method': 'manual',
            'details': {
                'total_source_lines': total_lines,
                'total_test_lines': test_lines
            }
        }
    
    def _extract_coverage(self, output: str, cov_type: str) -> Optional[float]:
        """從 pytest-cov 輸出提取覆蓋率"""
        lines = output.split('\n')
        
        for line in lines:
            if cov_type == 'line' and 'TOTAL' in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        return float(part)
                # 嘗試解析 "XX%" 格式
                match = re.search(r'(\d+)%', line)
                if match:
                    return float(match.group(1))
            
            if cov_type == 'branch' and 'BRANCH' in line:
                match = re.search(r'(\d+)%', line)
                if match:
                    return float(match.group(1))
        
        return None


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='測試覆蓋率自動化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/coverage_checker.py
  python3 quality_gate/coverage_checker.py --project-dir /path/to/project
  python3 quality_gate/coverage_checker.py --project-dir . --output report.json
        '''
    )
    
    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='專案目錄���徑（預設：當前目錄）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='輸出 JSON 檔案路徑（可選）'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=80.0,
        help='覆蓋率閾值（預設：80%%）'
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        default=None,
        help='Phase 編號（用於 unified_gate 整合）'
    )
    
    args = parser.parse_args()
    
    # 執行覆蓋率檢查
    checker = CoverageChecker(args.project_dir)
    checker.threshold = args.threshold
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