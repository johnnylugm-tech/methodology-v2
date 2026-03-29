#!/usr/bin/env python3
"""
TC Trace Checker - 測試用例追蹤檢查器
=================================
檢查每個 SRS FR 是否有對應的 TC，輸出覆蓋率報告

使用方式：
    python3 quality_gate/tc_trace_checker.py --project-dir /path/to/project
    python3 quality_gate/tc_trace_checker.py --project-dir /path/to/project --output report.json

Pass 條件：
    - P4-1: 每條 SRS FR 有對應 TC = 100%
    - P4-9: SRS FR 覆蓋率 = 100%

門檻：100% 覆蓋
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TCTraceChecker:
    """測試用例追蹤檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.fr_ids: Set[str] = set()
        self.tc_map: Dict[str, List[str]] = {}  # FR-ID -> TC list
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行追蹤檢查"""
        # 1. 提取所有 SRS FR-ID
        self._extract_fr_ids()
        
        # 2. 提取所有 TC
        self._extract_test_cases()
        
        # 3. 匹配 FR 和 TC
        coverage = self._match_fr_tc()
        
        # 4. 計算結果
        return self._calculate_result(coverage)
    
    def _extract_fr_ids(self):
        """從 SRS.md 提取 FR-ID"""
        srs_paths = [
            self.project_path / 'docs' / 'SRS.md',
            self.project_path / 'SRS.md',
            self.project_path / 'docs' / 'SPEC.md'
        ]
        
        for srs_path in srs_paths:
            if srs_path.exists():
                content = srs_path.read_text(encoding='utf-8')
                # 匹配 FR-001, FR-01, FR-1 等格式
                pattern = r'FR-\d+'
                self.fr_ids = set(re.findall(pattern, content))
                if self.fr_ids:
                    if self.verbose:
                        print(f"Found {len(self.fr_ids)} FR-ID from {srs_path.name}")
                    break
        
        if not self.fr_ids:
            # 嘗試從其他文檔提取
            self._extract_fr_ids_fallback()
    
    def _extract_fr_ids_fallback(self):
        """從其他文檔嘗試提取 FR-ID"""
        for doc_name in ['SPEC.md', 'requirements.md', 'features.md']:
            for base in ['docs', '.']:
                doc_path = self.project_path / base / doc_name
                if doc_path.exists():
                    content = doc_path.read_text(encoding='utf-8')
                    pattern = r'FR-\d+'
                    found = set(re.findall(pattern, content))
                    if found:
                        self.fr_ids = found
                        if self.verbose:
                            print(f"Found {len(self.fr_ids)} FR-ID from fallback {doc_name}")
                        return
    
    def _extract_test_cases(self):
        """提取所有測試用例"""
        tests_dirs = [
            self.project_path / 'tests',
            self.project_path / 'test',
            self.project_path / 'tests' / 'test_cases',
            self.project_path / 'docs' / 'test_cases'
        ]
        
        for tests_dir in tests_dirs:
            if tests_dir.exists():
                self._scan_test_dir(tests_dir)
                if self.tc_map:
                    break
    
    def _scan_test_dir(self, tests_dir: Path):
        """掃描測試目錄"""
        # 掃描 Python 測試文件
        for test_file in tests_dir.rglob('*.py'):
            content = test_file.read_text(encoding='utf-8')
            self._extract_tc_from_file(test_file, content)
        
        # 掃描 markdown 測試規格
        for md_file in tests_dir.rglob('*.md'):
            content = md_file.read_text(encoding='utf-8')
            self._extract_tc_from_md(md_file, content)
    
    def _extract_tc_from_file(self, file_path: Path, content: str):
        """從測試文件提取 TC"""
        # 查找測試函數
        test_funcs = re.findall(r'def\s+(test_\w+|_\w+)', content)
        
        # 查找 FR 引用
        fr_refs = re.findall(r'FR-\d+', content)
        
        for fr_id in fr_refs:
            if fr_id not in self.tc_map:
                self.tc_map[fr_id] = []
            for func in test_funcs:
                tc_name = f"{file_path.name}::{func}"
                if tc_name not in self.tc_map[fr_id]:
                    self.tc_map[fr_id].append(tc_name)
    
    def _extract_tc_from_md(self, file_path: Path, content: str):
        """從 MD 測試規格提取 TC"""
        # 查找 TC 標題
        tc_patterns = [
            r'###\s+TC[-_]?(\d+)',  # ### TC-001
            r'##\s+Test Case\s+(\d+)',  # ## Test Case 1
            r'^\s*TC[-_]?(\d+)\s*[:\-]',  # TC-001:
            r'\[TC[-_]?(\d+)\]'  # [TC-001]
        ]
        
        for pattern in tc_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for tc_num in matches:
                fr_refs = re.findall(r'FR-\d+', content)
                for fr_id in fr_refs:
                    if fr_id not in self.tc_map:
                        self.tc_map[fr_id] = []
                    tc_name = f"{file_path.name}::TC-{tc_num}"
                    if tc_name not in self.tc_map[fr_id]:
                        self.tc_map[fr_id].append(tc_name)
    
    def _match_fr_tc(self) -> List[Dict]:
        """匹配 FR 和 TC"""
        coverage = []
        
        for fr_id in sorted(self.fr_ids):
            # 提取 FR 編號
            fr_match = re.search(r'FR-(\d+)', fr_id)
            fr_num = fr_match.group(1) if fr_match else None
            
            # 查找對應的 TC
            tcs = []
            
            # 精確匹配
            if fr_id in self.tc_map:
                tcs.extend(self.tc_map[fr_id])
            
            # 變體匹配（FR-1 vs FR-01 vs FR-001）
            if fr_num:
                for variant in [f'FR-{fr_num.zfill(2)}', f'FR-{fr_num.zfill(3)}']:
                    if variant in self.tc_map and variant != fr_id:
                        tcs.extend(self.tc_map[variant])
            
            # 去重
            tcs = list(set(tcs))
            
            coverage.append({
                'fr_id': fr_id,
                'has_tc': len(tcs) > 0,
                'tc_count': len(tcs),
                'test_cases': tcs
            })
        
        return coverage
    
    def _calculate_result(self, coverage: List[Dict]) -> Dict:
        """計算檢查結果"""
        total_fr = len(coverage)
        covered_fr = sum(1 for c in coverage if c['has_tc'])
        uncovered = [c['fr_id'] for c in coverage if not c['has_tc']]
        
        # 門檻：100%
        coverage_rate = (covered_fr / total_fr * 100) if total_fr > 0 else 100
        passed = coverage_rate == 100 and total_fr > 0
        
        return {
            'passed': passed,
            'coverage_rate': round(coverage_rate, 2),
            'total_fr': total_fr,
            'covered_fr': covered_fr,
            'uncovered_fr': uncovered,
            'details': coverage,
            'threshold': 100,
            'phase_conditions': ['P4-1', 'P4-9']
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='TC 追蹤檢查器 - 檢查每個 SRS FR 是否有對應 TC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Pass 條件：
  - P4-1: 每條 SRS FR 有對應 TC = 100%
  - P4-9: SRS FR 覆蓋率 = 100%

範例：
  python3 quality_gate/tc_trace_checker.py
  python3 quality_gate/tc_trace_checker.py --project-dir /path/to/project
  python3 quality_gate/tc_trace_checker.py --project-dir . --output report.json --verbose
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
        '--verbose',
        action='store_true',
        help='顯示詳細輸出'
    )
    
    args = parser.parse_args()
    
    # 執行檢查
    checker = TCTraceChecker(args.project_dir, args.verbose)
    result = checker.check()
    
    # 輸出結果
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding='utf-8')
        print(f"Report saved to: {args.output}")
    else:
        print(json_output)
    
    # 返回狀態碼
    if not result['passed']:
        print(f"\n❌ FAILED: {result['coverage_rate']}% coverage (threshold: {result['threshold']}%)", file=sys.stderr)
        print(f"   Uncovered FRs: {result['uncovered_fr']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ PASSED: {result['coverage_rate']}% coverage", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
