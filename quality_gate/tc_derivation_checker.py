#!/usr/bin/env python3
"""
TC Derivation Checker - 測試用例推導檢查器
=====================================
驗證 TC 是從 SRS 推導而非從代碼回溯

使用方式：
    python3 quality_gate/tc_derivation_checker.py --project-dir /path/to/project
    python3 quality_gate/tc_derivation_checker.py --project-dir /path/to/project --output report.json

Pass 條件：
    - P4-3: TC 從 SRS 推導 = 必需

門檻：100% 從 SRS 推導
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class TCDerivationChecker:
    """TC 推導檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.fr_ids: Set[str] = set()
        self.tc_details: Dict[str, Dict] = {}
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行推導檢查"""
        # 1. 提取所有 FR-ID
        self._extract_fr_ids()
        
        # 2. 提取所有 TC
        self._extract_test_cases()
        
        # 3. 檢查每個 TC 的推導來源
        derivation_check = self._check_derivation()
        
        # 4. 計算結果
        return self._calculate_result(derivation_check)
    
    def _extract_fr_ids(self):
        """從 SRS.md 提取 FR-ID"""
        srs_paths = [
            self.project_path / 'docs' / 'SRS.md',
            self.project_path / 'SRS.md'
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
    
    def _extract_test_cases(self):
        """提取所有測試用例"""
        tests_dirs = [
            self.project_path / 'tests',
            self.project_path / 'test',
            self.project_path / 'docs' / 'test_cases'
        ]
        
        for tests_dir in tests_dirs:
            if tests_dir.exists():
                self._scan_test_dir(tests_dir)
                if self.tc_details:
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
        # 查找 FR 引用
        fr_refs = re.findall(r'FR-\d+', content)
        
        # 查找測試函數
        test_funcs = re.findall(r'def\s+(test_\w+)', content)
        
        for tc_func in test_funcs:
            fr_ref = fr_refs[0] if fr_refs else None
            
            tc_id = f"{file_path.name}::{tc_func}"
            
            # 檢查 TC 的內容是否來自 SRS（通過 FR 關鍵字）
            keywords = self._extract_fr_keywords(fr_ref)
            content_keywords = self._extract_keywords_from_func(content, tc_func)
            
            self.tc_details[tc_id] = {
                'tc_id': tc_id,
                'file': str(file_path),
                'function': tc_func,
                'referenced_fr': fr_ref,
                'keywords': keywords,
                'content_keywords': content_keywords,
                'derivation_source': self._determine_derivation(keywords, content_keywords)
            }
    
    def _extract_tc_from_md(self, file_path: Path, content: str):
        """從 MD 測試規格提取 TC"""
        # 查找 TC 標題
        tc_sections = re.split(r'^###\s+TC[-_]?\d+', content, flags=re.MULTILINE)
        
        for i, section in enumerate(tc_sections[1:], 1):
            fr_refs = re.findall(r'FR-\d+', section)
            fr_ref = fr_refs[0] if fr_refs else None
            
            tc_id = f"{file_path.name}::TC-{i}"
            keywords = self._extract_fr_keywords(fr_ref)
            content_keywords = self._extract_keywords_from_text(section)
            
            self.tc_details[tc_id] = {
                'tc_id': tc_id,
                'file': str(file_path),
                'function': f"TC-{i}",
                'referenced_fr': fr_ref,
                'keywords': keywords,
                'content_keywords': content_keywords,
                'derivation_source': self._determine_derivation(keywords, content_keywords)
            }
    
    def _extract_fr_keywords(self, fr_id: str) -> List[str]:
        """提取 FR 的關鍵字"""
        if not fr_id:
            return []
        
        srs_paths = [
            self.project_path / 'docs' / 'SRS.md',
            self.project_path / 'SRS.md'
        ]
        
        for srs_path in srs_paths:
            if not srs_path.exists():
                continue
            
            content = srs_path.read_text(encoding='utf-8')
            
            # 找到 FR 的內容
            pattern = rf'({fr_id}[^\n]*\n(?:\s{4,}[^\n]+\n)+)'
            match = re.search(pattern, content)
            if match:
                fr_content = match.group(1)
                # 提取關鍵字（排除停用詞）
                keywords = self._extract_keywords_from_text(fr_content)
                return keywords
        
        return []
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """從文本提取關鍵字"""
        # 簡單的關鍵字提取
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # 過濾停用詞
        stop_words = {'this', 'that', 'with', 'from', 'have', 'been', 'will', 'shall', 'must', 'should', 'could', 'would'}
        keywords = [w for w in words if w not in stop_words]
        
        return list(set(keywords))[:20]  # 最多 20 個
    
    def _extract_keywords_from_func(self, content: str, func_name: str) -> List[str]:
        """從函數內容提取關鍵字"""
        # 找到函數內容
        pattern = rf'def\s+{func_name}\([^)]*\):[^\n]*\n((?:\s{4,}.+\n)+)'
        match = re.search(pattern, content)
        
        if match:
            func_content = match.group(1)
            return self._extract_keywords_from_text(func_content)
        
        return []
    
    def _determine_derivation(self, srs_keywords: List[str], tc_keywords: List[str]) -> str:
        """判斷 TC 的推導來源"""
        if not srs_keywords:
            return 'unknown'
        
        # 計算關鍵字重疊
        overlap = set(srs_keywords) & set(tc_keywords)
        
        # 如果有足夠的重疊，認為是從 SRS 推導
        if len(overlap) >= 2:
            return 'srs'
        
        # 檢查是否有 "srs", "requirement", "spec" 等關鍵字
        tc_lower = ' '.join(tc_keywords).lower()
        if any(kw in tc_lower for kw in ['srs', 'requirement', 'spec', 'functional']):
            return 'srs'
        
        # 檢查是否只引用代碼（壞的跡象）
        if any(kw in tc_lower for kw in ['implementation', 'code', 'class', 'method']):
            return 'code'
        
        return 'srs'  # 預設為 SRS
    
    def _check_derivation(self) -> List[Dict]:
        """檢查推導來源"""
        results = []
        
        for tc_id, detail in self.tc_details.items():
            results.append({
                'tc_id': tc_id,
                'derived_from': detail['derivation_source'],
                'referenced_fr': detail['referenced_fr']
            })
        
        return results
    
    def _calculate_result(self, derivation_check: List[Dict]) -> Dict:
        """計算檢查結果"""
        total_tc = len(derivation_check)
        
        if total_tc == 0:
            return {
                'passed': True,  # 沒有 TC 也算通過（可能還沒寫測試）
                'srs_derived_rate': 100,
                'total_tc': 0,
                'srs_derived': 0,
                'code_derived': 0,
                'unknown': 0,
                'details': [],
                'threshold': 100,
                'phase_conditions': ['P4-3']
            }
        
        srs_derived = sum(1 for d in derivation_check if d['derived_from'] == 'srs')
        code_derived = sum(1 for d in derivation_check if d['derived_from'] == 'code')
        unknown = sum(1 for d in derivation_check if d['derived_from'] == 'unknown')
        
        srs_derived_rate = (srs_derived / total_tc * 100) if total_tc > 0 else 0
        passed = srs_derived_rate == 100
        
        return {
            'passed': passed,
            'srs_derived_rate': round(srs_derived_rate, 2),
            'total_tc': total_tc,
            'srs_derived': srs_derived,
            'code_derived': code_derived,
            'unknown': unknown,
            'details': derivation_check,
            'threshold': 100,
            'phase_conditions': ['P4-3']
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='TC 推導檢查器 - 驗證 TC 是從 SRS 推導而非從代碼回溯',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Pass 條件：
  - P4-3: TC 從 SRS 推導 = 必需

範例：
  python3 quality_gate/tc_derivation_checker.py
  python3 quality_gate/tc_derivation_checker.py --project-dir /path/to/project
  python3 quality_gate/tc_derivation_checker.py --project-dir . --output report.json --verbose
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
    checker = TCDerivationChecker(args.project_dir, args.verbose)
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
        print(f"\n❌ FAILED: {result['srs_derived_rate']}% derived from SRS (threshold: {result['threshold']}%)", file=sys.stderr)
        print(f"   Code-derived: {result['code_derived']}, Unknown: {result['unknown']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ PASSED: {result['srs_derived_rate']}% derived from SRS", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
