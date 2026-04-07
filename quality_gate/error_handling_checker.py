#!/usr/bin/env python3
"""
Error Handling Checker - 錯誤處理檢查器
=================================
檢查錯誤處理是否對應 L1-L6 分類

使用方式：
    python3 quality_gate/error_handling_checker.py --project-dir /path/to/project

Pass 條件：
    - P2-7: 錯誤處理對應 L1-L6 分類 = 100%

門檻：100% 有對應分類
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class ErrorHandlingChecker:
    """錯誤處理檢查器"""
    
    # L1-L6 錯誤分類
    ERROR_CLASSIFICATION = {
        'L1': 'Input Validation Error - 輸入驗證錯誤',
        'L2': 'Authentication Error - 認證錯誤',
        'L3': 'Authorization Error - 授權錯誤',
        'L4': 'Resource Not Found Error - 資源不存在錯誤',
        'L5': 'Business Logic Error - 業務邏輯錯誤',
        'L6': 'System Error - 系統錯誤'
    }
    
    # 每個分類的關鍵字
    ERROR_KEYWORDS = {
        'L1': ['validation', 'validate', 'invalid', 'required', 'format', 'pattern', 'regex', 'length', 'range', '驗證', '格式'],
        'L2': ['auth', 'authentication', 'login', 'credential', 'token', 'password', 'unauthorized', '認證', '登入'],
        'L3': ['permission', 'authorize', 'access', 'forbidden', 'role', 'privilege', 'acl', '授權', '權限'],
        'L4': ['not found', '404', 'missing', 'does not exist', 'no such', '不存在', '找不到'],
        'L5': ['business', 'logic', 'rule', 'constraint', 'invalid state', '業務', '邏輯'],
        'L6': ['system', 'internal', 'database', 'network', 'timeout', 'crash', 'exception', '系統', '內部']
    }
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.errors: List[Dict] = []
    
    def run(self, project_path: str = None) -> Dict:
        """執行檢查（兼容介面）"""
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        """執行錯誤處理檢查"""
        self._extract_error_handling()
        classified_errors = self._classify_errors()
        return self._calculate_result(classified_errors)
    
    def _extract_error_handling(self):
        """提取所有錯誤處理"""
        src_dirs = [self.project_path / 'src', self.project_path / 'app', self.project_path]
        
        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            
            for py_file in src_dir.rglob('*.py'):
                if 'test' in py_file.parts:
                    continue
                
                content = py_file.read_text(encoding='utf-8')
                self._extract_from_file(py_file, content)
        
        self._extract_from_sad()
        
        if self.verbose:
            print(f"Found {len(self.errors)} error handling entries")
    
    def _extract_from_file(self, file_path: Path, content: str):
        """從代碼文件提取錯誤處理"""
        exception_classes = re.findall(r'class\s+(\w+(?:Error|Exception)\w*)', content)
        exception_handles = re.findall(r'except\s+(\w+)', content)
        
        for exc_class in exception_classes:
            self.errors.append({'source': 'code', 'file': str(file_path), 'type': 'exception_class', 'name': exc_class, 'message': exc_class})
        
        for exc_handle in exception_handles:
            self.errors.append({'source': 'code', 'file': str(file_path), 'type': 'exception_handle', 'name': exc_handle, 'message': ''})
    
    def _extract_from_sad(self):
        """從 SAD.md 提取錯誤處理設計"""
        sad_paths = [self.project_path / 'docs' / 'SAD.md', self.project_path / 'SAD.md']
        
        for sad_path in sad_paths:
            if not sad_path.exists():
                continue
            
            content = sad_path.read_text(encoding='utf-8')
            error_sections = re.split(r'^#{1,3}\s+(?:Error|Exception|Fault).+', content, flags=re.MULTILINE)
            
            for section in error_sections[1:]:
                patterns = [r'([A-Z]\w+\s+Error)', r'-\s+(\w+\s+error)', r'([A-Z]\w+Exception)']
                for pattern in patterns:
                    matches = re.findall(pattern, section, re.IGNORECASE)
                    for match in matches:
                        self.errors.append({'source': 'architecture', 'file': str(sad_path), 'type': 'error_design', 'name': match, 'message': match})
    
    def _classify_errors(self) -> List[Dict]:
        """分類錯誤"""
        classified = []
        
        for error in self.errors:
            name = error.get('name', '') or ''
            message = error.get('message', '') or ''
            combined = f"{name} {message}".lower()
            
            classification = None
            for level, keywords in self.ERROR_KEYWORDS.items():
                if any(kw.lower() in combined for kw in keywords):
                    classification = level
                    break
            
            classified.append({**error, 'classification': classification, 'classification_desc': self.ERROR_CLASSIFICATION.get(classification, 'Unclassified')})
        
        return classified
    
    def _calculate_result(self, classified_errors: List[Dict]) -> Dict:
        """計算檢查結果"""
        total_errors = len(classified_errors)
        
        if total_errors == 0:
            return {'passed': False, 'classified_rate': 0, 'total_errors': 0, 'classified': 0, 'unclassified': [], 'details': [], 'threshold': 100, 'phase_conditions': ['P2-7']}
        
        classification_counts = {level: 0 for level in self.ERROR_CLASSIFICATION.keys()}
        
        classified_errors_list = []
        unclassified = []
        
        for error in classified_errors:
            if error['classification']:
                classification_counts[error['classification']] += 1
                classified_errors_list.append(error)
            else:
                unclassified.append({'name': error.get('name', ''), 'file': error.get('file', ''), 'type': error.get('type', '')})
        
        classified_count = len(classified_errors_list)
        classified_rate = (classified_count / total_errors * 100) if total_errors > 0 else 0
        passed = classified_rate == 100
        
        return {'passed': passed, 'classified_rate': round(classified_rate, 2), 'total_errors': total_errors, 'classified': classified_count, 'unclassified_count': len(unclassified), 'unclassified': unclassified[:10], 'breakdown': classification_counts, 'details': classified_errors_list[:50], 'threshold': 100, 'phase_conditions': ['P2-7']}


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='錯誤處理檢查器 - 檢查錯誤處理是否對應 L1-L6 分類')
    parser.add_argument('--project-dir', type=str, default='.', help='專案目錄路徑')
    parser.add_argument('--output', type=str, default=None, help='輸出 JSON 檔案路徑')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細輸出')
    args = parser.parse_args()
    
    checker = ErrorHandlingChecker(args.project_dir, args.verbose)
    result = checker.check()
    
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding='utf-8')
        print(f"Report saved to: {args.output}")
    else:
        print(json_output)
    
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
