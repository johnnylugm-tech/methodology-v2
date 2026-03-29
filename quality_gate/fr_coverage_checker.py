#!/usr/bin/env python3
"""
FR Coverage Checker - 功能需求覆蓋率檢查器
=====================================
檢查每個 FR 在架構/代碼/測試的覆蓋狀態

使用方式：
    python3 quality_gate/fr_coverage_checker.py --project-dir /path/to/project
    python3 quality_gate/fr_coverage_checker.py --project-dir /path/to/project --output report.json

Pass 條件：
    - P2-10: TRACEABILITY_MATRIX 更新
    - P4-9: SRS FR 覆蓋率 = 100%

門檻：100% 覆蓋
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class FRCoverageChecker:
    """FR 覆蓋率檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.fr_ids: Set[str] = set()
        self.coverage_details: Dict[str, Dict] = {}
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行覆蓋率檢查"""
        # 1. 提取所有 FR-ID
        self._extract_fr_ids()
        
        # 2. 檢查每個 FR 的覆蓋狀態
        for fr_id in sorted(self.fr_ids):
            coverage = {
                'architecture': self._check_architecture(fr_id),
                'code': self._check_code(fr_id),
                'test': self._check_test(fr_id),
                'traceability': self._check_traceability(fr_id)
            }
            self.coverage_details[fr_id] = coverage
        
        # 3. 計算結果
        return self._calculate_result()
    
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
                pattern = r'FR-\d+'
                self.fr_ids = set(re.findall(pattern, content))
                if self.fr_ids:
                    if self.verbose:
                        print(f"Found {len(self.fr_ids)} FR-ID from {srs_path.name}")
                    break
        
        if not self.fr_ids:
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
                        return
    
    def _check_architecture(self, fr_id: str) -> bool:
        """檢查架構覆蓋"""
        sad_paths = [
            self.project_path / 'docs' / 'SAD.md',
            self.project_path / 'SAD.md',
            self.project_path / 'docs' / 'architecture.md'
        ]
        
        for sad_path in sad_paths:
            if not sad_path.exists():
                continue
            
            content = sad_path.read_text(encoding='utf-8')
            if fr_id in content:
                return True
            
            # 變體匹配
            fr_match = re.search(r'FR-(\d+)', fr_id)
            if fr_match:
                for variant in [f'FR-{fr_match.group(1).zfill(2)}', f'FR-{fr_match.group(1).zfill(3)}']:
                    if variant in content:
                        return True
        
        return False
    
    def _check_code(self, fr_id: str) -> bool:
        """檢查代碼覆蓋"""
        src_dirs = [
            self.project_path / 'src',
            self.project_path / 'app',
            self.project_path
        ]
        
        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            
            for py_file in src_dir.rglob('*.py'):
                if 'test' in py_file.parts:
                    continue
                
                content = py_file.read_text(encoding='utf-8')
                if fr_id in content:
                    return True
                
                # 變體匹配
                fr_match = re.search(r'FR-(\d+)', fr_id)
                if fr_match:
                    for variant in [f'FR-{fr_match.group(1).zfill(2)}', f'FR-{fr_match.group(1).zfill(3)}']:
                        if variant in content:
                            return True
        
        return False
    
    def _check_test(self, fr_id: str) -> bool:
        """檢查測試覆蓋"""
        tests_dirs = [
            self.project_path / 'tests',
            self.project_path / 'test'
        ]
        
        for tests_dir in tests_dirs:
            if not tests_dir.exists():
                continue
            
            for py_file in tests_dir.rglob('*.py'):
                content = py_file.read_text(encoding='utf-8')
                if fr_id in content:
                    return True
                
                fr_match = re.search(r'FR-(\d+)', fr_id)
                if fr_match:
                    for variant in [f'FR-{fr_match.group(1).zfill(2)}', f'FR-{fr_match.group(1).zfill(3)}']:
                        if variant in content:
                            return True
        
        return False
    
    def _check_traceability(self, fr_id: str) -> bool:
        """檢查 TRACEABILITY_MATRIX 覆蓋"""
        tm_paths = [
            self.project_path / 'docs' / 'TRACEABILITY_MATRIX.md',
            self.project_path / 'TRACEABILITY_MATRIX.md',
            self.project_path / 'docs' / 'traceability.md',
            self.project_path / 'traceability.md',
            self.project_path / 'SPEC_TRACKING.md'
        ]
        
        for tm_path in tm_paths:
            if not tm_path.exists():
                continue
            
            content = tm_path.read_text(encoding='utf-8')
            if fr_id in content:
                return True
            
            fr_match = re.search(r'FR-(\d+)', fr_id)
            if fr_match:
                for variant in [f'FR-{fr_match.group(1).zfill(2)}', f'FR-{fr_match.group(1).zfill(3)}']:
                    if variant in content:
                        return True
        
        return False
    
    def _calculate_result(self) -> Dict:
        """計算檢查結果"""
        total_fr = len(self.coverage_details)
        
        if total_fr == 0:
            return {
                'passed': False,
                'coverage_rate': 0,
                'total_fr': 0,
                'covered_fr': 0,
                'uncovered_fr': [],
                'details': [],
                'threshold': 100,
                'phase_conditions': ['P2-10', 'P4-9']
            }
        
        # 計算每個維度的覆蓋率
        arch_covered = sum(1 for c in self.coverage_details.values() if c['architecture'])
        code_covered = sum(1 for c in self.coverage_details.values() if c['code'])
        test_covered = sum(1 for c in self.coverage_details.values() if c['test'])
        trace_covered = sum(1 for c in self.coverage_details.values() if c['traceability'])
        
        # FR 需要在所有維度都有覆蓋才視為覆蓋
        fully_covered = []
        for fr_id, coverage in self.coverage_details.items():
            if all(coverage.values()):
                fully_covered.append(fr_id)
        
        uncovered = [fr_id for fr_id in self.coverage_details.keys() 
                     if fr_id not in fully_covered]
        
        coverage_rate = (len(fully_covered) / total_fr * 100) if total_fr > 0 else 0
        passed = coverage_rate == 100
        
        details = []
        for fr_id, coverage in self.coverage_details.items():
            details.append({
                'fr_id': fr_id,
                'covered': fr_id in fully_covered,
                'architecture': coverage['architecture'],
                'code': coverage['code'],
                'test': coverage['test'],
                'traceability': coverage['traceability']
            })
        
        return {
            'passed': passed,
            'coverage_rate': round(coverage_rate, 2),
            'total_fr': total_fr,
            'covered_fr': len(fully_covered),
            'uncovered_fr': uncovered,
            'breakdown': {
                'architecture': f"{arch_covered}/{total_fr}",
                'code': f"{code_covered}/{total_fr}",
                'test': f"{test_covered}/{total_fr}",
                'traceability': f"{trace_covered}/{total_fr}"
            },
            'details': details,
            'threshold': 100,
            'phase_conditions': ['P2-10', 'P4-9']
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='FR 覆蓋率檢查器 - 檢查 FR 在架構/代碼/測試的覆蓋狀態',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Pass 條件：
  - P2-10: TRACEABILITY_MATRIX 更新
  - P4-9: SRS FR 覆蓋率 = 100%

範例：
  python3 quality_gate/fr_coverage_checker.py
  python3 quality_gate/fr_coverage_checker.py --project-dir /path/to/project
  python3 quality_gate/fr_coverage_checker.py --project-dir . --output report.json --verbose
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
    checker = FRCoverageChecker(args.project_dir, args.verbose)
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
