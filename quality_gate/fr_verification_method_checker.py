#!/usr/bin/env python3
"""
FR Verification Method Checker - FR 驗證方法檢查器
==========================================
檢查每條 FR 是否有邏輯驗證方法

使用方式：
    python3 quality_gate/fr_verification_method_checker.py --project-dir /path/to/project
    python3 quality_gate/fr_verification_method_checker.py --project-dir /path/to/project --output report.json

Pass 條件：
    - P1-6: 每條 FR 有邏輯驗證方法 = 100%

門檻：100% 有方法
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class FRVerificationMethodChecker:
    """FR 驗證方法檢查器"""
    
    # 驗證方法關鍵字
    VERIFICATION_KEYWORDS = {
        'test': ['test', 'testing', '驗證', '測試'],
        'review': ['review', 'reviewer', '審查', '審閱'],
        'static': ['static analysis', 'lint', 'pylint', 'flake8'],
        'dynamic': ['dynamic test', 'runtime test', 'integration test'],
        'inspection': ['inspection', 'inspect', '檢查'],
        'analysis': ['analysis', 'analyze', '分析'],
        'verification': ['verification', 'verify', '驗證'],
        'validation': ['validation', 'validate', '確認']
    }
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.fr_ids: Set[str] = set()
        self.fr_details: Dict[str, Dict] = {}
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行驗證方法檢查"""
        # 1. 提取所有 FR-ID
        self._extract_fr_ids()
        
        # 2. 檢查每個 FR 的驗證方法
        for fr_id in sorted(self.fr_ids):
            detail = self._check_verification_method(fr_id)
            self.fr_details[fr_id] = detail
        
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
    
    def _extract_fr_content(self, fr_id: str) -> str:
        """提取單個 FR 的內容"""
        srs_paths = [
            self.project_path / 'docs' / 'SRS.md',
            self.project_path / 'SRS.md'
        ]
        
        for srs_path in srs_paths:
            if not srs_path.exists():
                continue
            
            content = srs_path.read_text(encoding='utf-8')
            
            # 嘗試找到 FR 的完整內容
            # 匹配 FR-XX 到下一個 FR 或章節
            pattern = rf'({fr_id}[^\n]*\n(?:\s{4,}[^\n]+\n)+)'
            match = re.search(pattern, content)
            if match:
                return match.group(1)
            
            # 簡單匹配：FR-XX 開頭的行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if fr_id in line:
                    # 收集後續行直到下一個 FR
                    fr_lines = []
                    for j in range(i, min(i + 10, len(lines))):
                        fr_lines.append(lines[j])
                    return '\n'.join(fr_lines)
        
        return ''
    
    def _check_verification_method(self, fr_id: str) -> Dict:
        """檢查單個 FR 的驗證方法"""
        fr_content = self._extract_fr_content(fr_id)
        
        # 查找驗證方法關鍵字
        found_methods = []
        for method_type, keywords in self.VERIFICATION_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in fr_content.lower():
                    found_methods.append(method_type)
                    break
        
        # 去重
        found_methods = list(set(found_methods))
        
        # 檢查測試文件
        test_methods = self._check_test_methods(fr_id)
        found_methods.extend(test_methods)
        found_methods = list(set(found_methods))
        
        return {
            'fr_id': fr_id,
            'has_verification_method': len(found_methods) > 0,
            'methods': found_methods,
            'content_preview': fr_content[:200] if fr_content else ''
        }
    
    def _check_test_methods(self, fr_id: str) -> List[str]:
        """檢查是否有對應的測試"""
        methods = []
        
        tests_dirs = [
            self.project_path / 'tests',
            self.project_path / 'test'
        ]
        
        fr_match = re.search(r'FR-(\d+)', fr_id)
        fr_num = fr_match.group(1) if fr_match else None
        
        for tests_dir in tests_dirs:
            if not tests_dir.exists():
                continue
            
            for py_file in tests_dir.rglob('*.py'):
                content = py_file.read_text(encoding='utf-8')
                
                # 檢查是否包含這個 FR
                if fr_id in content:
                    methods.append('test')
                    break
                
                if fr_num:
                    # 變體匹配
                    for variant in [f'FR-{fr_num.zfill(2)}', f'FR-{fr_num.zfill(3)}']:
                        if variant in content:
                            methods.append('test')
                            break
        
        return methods
    
    def _calculate_result(self) -> Dict:
        """計算檢查結果"""
        total_fr = len(self.fr_details)
        
        if total_fr == 0:
            return {
                'passed': False,
                'coverage_rate': 0,
                'total_fr': 0,
                'covered_fr': 0,
                'uncovered_fr': [],
                'details': [],
                'threshold': 100,
                'phase_conditions': ['P1-6']
            }
        
        covered = [fr_id for fr_id, detail in self.fr_details.items() 
                   if detail['has_verification_method']]
        uncovered = [fr_id for fr_id, detail in self.fr_details.items() 
                    if not detail['has_verification_method']]
        
        coverage_rate = (len(covered) / total_fr * 100) if total_fr > 0 else 0
        passed = coverage_rate == 100
        
        details = []
        for fr_id, detail in self.fr_details.items():
            details.append({
                'fr_id': fr_id,
                'has_verification_method': detail['has_verification_method'],
                'methods': detail['methods']
            })
        
        return {
            'passed': passed,
            'coverage_rate': round(coverage_rate, 2),
            'total_fr': total_fr,
            'covered_fr': len(covered),
            'uncovered_fr': uncovered,
            'details': details,
            'threshold': 100,
            'phase_conditions': ['P1-6']
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='FR 驗證方法檢查器 - 檢查每條 FR 是否有邏輯驗證方法',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Pass 條件：
  - P1-6: 每條 FR 有邏輯驗證方法 = 100%

範例：
  python3 quality_gate/fr_verification_method_checker.py
  python3 quality_gate/fr_verification_method_checker.py --project-dir /path/to/project
  python3 quality_gate/fr_verification_method_checker.py --project-dir . --output report.json --verbose
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
    checker = FRVerificationMethodChecker(args.project_dir, args.verbose)
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
        print(f"\n❌ FAILED: {result['coverage_rate']}% have verification methods (threshold: {result['threshold']}%)", file=sys.stderr)
        print(f"   FRs without methods: {result['uncovered_fr']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ PASSED: {result['coverage_rate']}% have verification methods", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
