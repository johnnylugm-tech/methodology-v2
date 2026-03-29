#!/usr/bin/env python3
"""
Module Tracking Checker - 模組追蹤檢查器
=================================
檢查每個模組是否有對應的邏輯審查對話記錄

使用方式：
    python3 quality_gate/module_tracking_checker.py --project-dir /path/to/project
    python3 quality_gate/module_tracking_checker.py --project-dir /path/to/project --output report.json

Pass 條件：
    - P3-8: 每個模組有同行邏輯審查對話記錄 = 必需

門檻：100% 有記錄
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class ModuleTrackingChecker:
    """模組追蹤檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.modules: Set[str] = set()
        self.module_details: Dict[str, Dict] = {}
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行模組追蹤檢查"""
        # 1. 提取所有模組
        self._extract_modules()
        
        # 2. 檢查每個模組的審查記錄
        for module in sorted(self.modules):
            detail = self._check_module_tracking(module)
            self.module_details[module] = detail
        
        # 3. 計算結果
        return self._calculate_result()
    
    def _extract_modules(self):
        """提取所有模組"""
        # 從 SAD.md 提取模組
        sad_paths = [
            self.project_path / 'docs' / 'SAD.md',
            self.project_path / 'SAD.md',
            self.project_path / 'docs' / 'architecture.md'
        ]
        
        for sad_path in sad_paths:
            if not sad_path.exists():
                continue
            
            content = sad_path.read_text(encoding='utf-8')
            
            # 提取模組名稱
            # 匹配 ## Module, ## Component, ## Module: xxx
            patterns = [
                r'##\s+(?:Module|Component)\s*[:\-]?\s*(.+)',
                r'###\s+(?:Module|Component)\s*[:\-]?\s*(.+)',
                r'^\s*-\s+(?:Module|Component)\s*[:\-]?\s*(.+)',
                r'`(\w+Module)`',
                r'`(\w+Service)`'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    module_name = match.strip().strip('`')
                    if module_name and len(module_name) < 50:
                        self.modules.add(module_name)
            
            if self.modules:
                if self.verbose:
                    print(f"Found {len(self.modules)} modules from {sad_path.name}")
                break
        
        # 從 src/ 目錄提取
        self._extract_modules_from_src()
    
    def _extract_modules_from_src(self):
        """從 src/ 目錄提取模組"""
        src_dirs = [
            self.project_path / 'src',
            self.project_path / 'app',
            self.project_path
        ]
        
        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            
            for py_file in src_dir.rglob('*.py'):
                if 'test' in py_file.parts or '__init__' in py_file.name:
                    continue
                
                # 提取類名
                content = py_file.read_text(encoding='utf-8')
                classes = re.findall(r'class\s+(\w+)', content)
                
                for class_name in classes:
                    # 過濾常見的非模組類名
                    if class_name not in ['Test', 'Tests', 'Main', 'App', 'Config']:
                        self.modules.add(class_name)
        
        if self.verbose and self.modules:
            print(f"Found {len(self.modules)} modules from src/")
    
    def _check_module_tracking(self, module: str) -> Dict:
        """檢查單個模組的審查記錄"""
        # 檢查審查記錄文件
        review_files = [
            self.project_path / 'docs' / 'reviews' / f'{module}.md',
            self.project_path / 'docs' / 'reviews' / f'{module.lower()}.md',
            self.project_path / 'review' / f'{module}.md',
            self.project_path / 'reviews' / f'{module}.md',
            self.project_path / 'docs' / 'PEER_REVIEW.md',
            self.project_path / 'PEER_REVIEW.md',
            self.project_path / 'docs' / 'logic_review.md',
            self.project_path / 'logic_review.md'
        ]
        
        has_review = False
        review_file = None
        
        for review_file_path in review_files:
            if not review_file_path.exists():
                continue
            
            content = review_file_path.read_text(encoding='utf-8')
            if module in content:
                has_review = True
                review_file = str(review_file_path)
                break
        
        # 檢查對話記錄
        conversation_files = [
            self.project_path / 'docs' / 'conversations' / f'{module}.md',
            self.project_path / 'docs' / 'conversations' / f'{module.lower()}.md',
            self.project_path / 'conversations' / f'{module}.md'
        ]
        
        has_conversation = False
        conversation_file = None
        
        for conv_file in conversation_files:
            if not conv_file.exists():
                continue
            
            content = conv_file.read_text(encoding='utf-8')
            if module in content:
                has_conversation = True
                conversation_file = str(conv_file)
                break
        
        return {
            'module': module,
            'has_review': has_review,
            'review_file': review_file,
            'has_conversation': has_conversation,
            'conversation_file': conversation_file,
            'has_tracking': has_review or has_conversation
        }
    
    def _calculate_result(self) -> Dict:
        """計算檢查結果"""
        total_modules = len(self.module_details)
        
        if total_modules == 0:
            return {
                'passed': True,  # 沒有模組也算通過
                'tracked_rate': 100,
                'total_modules': 0,
                'tracked': 0,
                'untracked': [],
                'details': [],
                'threshold': 100,
                'phase_conditions': ['P3-8']
            }
        
        tracked = [m for m, detail in self.module_details.items() 
                   if detail['has_tracking']]
        untracked = [m for m, detail in self.module_details.items() 
                    if not detail['has_tracking']]
        
        tracked_rate = (len(tracked) / total_modules * 100) if total_modules > 0 else 0
        passed = tracked_rate == 100
        
        details = []
        for module, detail in self.module_details.items():
            details.append({
                'module': module,
                'has_tracking': detail['has_tracking'],
                'has_review': detail['has_review'],
                'has_conversation': detail['has_conversation']
            })
        
        return {
            'passed': passed,
            'tracked_rate': round(tracked_rate, 2),
            'total_modules': total_modules,
            'tracked': len(tracked),
            'untracked': untracked,
            'details': details,
            'threshold': 100,
            'phase_conditions': ['P3-8']
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='模組追蹤檢查器 - 檢查每個模組是否有對應的邏輯審查對話記錄',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Pass 條件：
  - P3-8: 每個模組有同行邏輯審查對話記錄 = 必需

範例：
  python3 quality_gate/module_tracking_checker.py
  python3 quality_gate/module_tracking_checker.py --project-dir /path/to/project
  python3 quality_gate/module_tracking_checker.py --project-dir . --output report.json --verbose
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
    checker = ModuleTrackingChecker(args.project_dir, args.verbose)
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
        print(f"\n❌ FAILED: {result['tracked_rate']}% modules tracked (threshold: {result['threshold']}%)", file=sys.stderr)
        print(f"   Untracked modules: {result['untracked']}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ PASSED: {result['tracked_rate']}% modules tracked", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
