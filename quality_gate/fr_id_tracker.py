#!/usr/bin/env python3
"""
FR-ID Tracker - 需求追蹤自動化工具
===========================
自動檢查每個 FR-ID 是否對應到架構、元件、測試

使用方式：
    python3 quality_gate/fr_id_tracker.py --project-dir /path/to/project
    python3 quality_gate/fr_id_tracker.py --project-dir /path/to/project --output report.json

輸出：
    JSON 報告，標記追蹤到/未追蹤的 FR-ID
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class FRIDTracker:
    """FR-ID 追蹤器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.fr_ids: Set[str] = set()
        self.details: List[Dict] = []
    
    def scan(self) -> Dict:
        """執行追蹤掃描"""
        # 1. 提取所有 FR-ID
        self._extract_fr_ids_from_srs()
        
        # 2. 檢查每個 FR-ID 的追蹤狀態
        for fr_id in sorted(self.fr_ids):
            detail = self._check_fr_id_tracking(fr_id)
            self.details.append(detail)
        
        # 3. 計算統計
        tracked = [d for d in self.details if d.get('implementation') == 'found' and d.get('test') == 'found']
        untracked_ids = [d['fr_id'] for d in self.details if d.get('implementation') != 'found' or d.get('test') != 'found']
        
        return {
            'passed': len(untracked_ids) == 0,
            'total_fr_ids': len(self.fr_ids),
            'tracked': len(tracked),
            'untracked': len(untracked_ids),
            'details': self.details,
            'untracked_ids': untracked_ids
        }
    
    def _extract_fr_ids_from_srs(self):
        """從 SRS.md 提取 FR-ID"""
        srs_path = self.project_path / 'docs' / 'SRS.md'
        if not srs_path.exists():
            # 嘗試其他位置
            srs_path = self.project_path / 'SRS.md'
        
        if srs_path.exists():
            content = srs_path.read_text(encoding='utf-8')
            # 匹配 FR-001, FR-01, FR-1 等格式
            pattern = r'FR-\d+'
            self.fr_ids = set(re.findall(pattern, content))
        
        if not self.fr_ids:
            # 嘗試從其他文檔提取
            self._extract_fr_ids_from_docs()
    
    def _extract_fr_ids_from_docs(self):
        """從其他文檔嘗試提取 FR-ID"""
        for doc_name in ['SPEC.md', 'requirements.md', 'features.md']:
            doc_path = self.project_path / 'docs' / doc_name
            if not doc_path.exists():
                doc_path = self.project_path / doc_name
            
            if doc_path.exists():
                content = doc_path.read_text(encoding='utf-8')
                pattern = r'FR-\d+'
                found = set(re.findall(pattern, content))
                if found:
                    self.fr_ids = found
                    break
    
    def _check_fr_id_tracking(self, fr_id: str) -> Dict:
        """檢查單個 FR-ID 的追蹤狀態"""
        # 檢查架構（SAD.md）
        architecture = self._check_architecture(fr_id)
        
        # 檢查實作（src/ 目錄）
        implementation = self._check_implementation(fr_id)
        
        # 檢查測試（tests/ 目錄）
        test = self._check_test(fr_id)
        
        return {
            'fr_id': fr_id,
            'architecture': architecture,
            'implementation': implementation,
            'test': test
        }
    
    def _check_architecture(self, fr_id: str) -> str:
        """檢查架構對應"""
        sad_paths = [
            self.project_path / 'docs' / 'SAD.md',
            self.project_path / 'SAD.md',
            self.project_path / 'architecture.md'
        ]
        
        for sad_path in sad_paths:
            if not sad_path.exists():
                continue
            
            content = sad_path.read_text(encoding='utf-8')
            # 檢查 FR-ID 是否在 SAD 中被引用
            if fr_id in content:
                return 'found'
            
            # 嘗試提取功能描述關鍵字
            fr_num = re.search(r'FR-(\d+)', fr_id)
            if fr_num:
                # 檢查 FR-XX 是否被提及
                fr_variant = f'FR-{fr_num.group(1)}'
                if fr_variant in content:
                    return 'found'
        
        return 'missing'
    
    def _check_implementation(self, fr_id: str) -> str:
        """檢查實作對應"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        # 提取 FR 編號
        fr_match = re.search(r'FR-(\d+)', fr_id)
        if not fr_match:
            return 'missing'
        
        fr_num = fr_match.group(1)
        
        # 掃描所有 Python 文件
        for py_file in src_dir.rglob('*.py'):
            content = py_file.read_text(encoding='utf-8')
            if fr_id in content:
                return 'found'
            # 檢查 FR-XX 變體
            if f'FR-{fr_num}' in content:
                return 'found'
        
        return 'missing'
    
    def _check_test(self, fr_id: str) -> str:
        """檢查測試對應"""
        tests_dir = self.project_path / 'tests'
        if not tests_dir.exists():
            tests_dir = self.project_path / 'test'
        if not tests_dir.exists():
            return 'missing'
        
        # 提取 FR 編號
        fr_match = re.search(r'FR-(\d+)', fr_id)
        if not fr_match:
            return 'missing'
        
        fr_num = fr_match.group(1)
        
        # 掃描所有測試文件
        for test_file in tests_dir.rglob('*.py'):
            content = test_file.read_text(encoding='utf-8')
            if fr_id in content:
                return 'found'
            # 檢查 FR-XX 變體
            if f'FR-{fr_num}' in content:
                return 'found'
        
        return 'missing'


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='FR-ID 追蹤自動化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/fr_id_tracker.py
  python3 quality_gate/fr_id_tracker.py --project-dir /path/to/project
  python3 quality_gate/fr_id_tracker.py --project-dir . --output report.json
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
    
    # 執行追蹤
    tracker = FRIDTracker(args.project_dir)
    result = tracker.scan()
    
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
    
    # 返回��態碼
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()