#!/usr/bin/env python3
"""
Compliance Matrix Checker - 合規矩陣檢查器
=================================
檢查每個模組是否有完整合規記錄

使用方式：
    python3 quality_gate/compliance_matrix_checker.py --project-dir /path/to/project

Pass 條件：
    - P3-12: 合規矩陣完整 = 必需

門檻：100% 完整
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set


class ComplianceMatrixChecker:
    """合規矩陣檢查器"""
    
    COMPLIANCE_TYPES = ['security', 'privacy', 'performance', 'reliability', 'scalability', 'usability', 'maintainability']
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.modules: Set[str] = set()
        self.compliance_records: Dict[str, Dict] = {}
    
    def run(self, project_path: str = None) -> Dict:
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        self._extract_modules()
        self._extract_compliance_records()
        return self._calculate_result()
    
    def _extract_modules(self):
        sad_paths = [self.project_path / 'docs' / 'SAD.md', self.project_path / 'SAD.md']
        
        for sad_path in sad_paths:
            if not sad_path.exists():
                continue
            
            content = sad_path.read_text(encoding='utf-8')
            patterns = [r'##\s+(?:Module|Component)\s*[:\-]?\s*(.+)', r'###\s+(?:Module|Component)\s*[:\-]?\s*(.+)']
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                for match in matches:
                    module_name = match.strip().strip('`')
                    if module_name and len(module_name) < 50:
                        self.modules.add(module_name)
            
            if self.modules:
                break
        
        src_dirs = [self.project_path / 'src', self.project_path / 'app', self.project_path]
        
        for src_dir in src_dirs:
            if not src_dir.exists():
                continue
            
            for py_file in src_dir.rglob('*.py'):
                if 'test' in py_file.parts or '__init__' in py_file.name:
                    continue
                
                content = py_file.read_text(encoding='utf-8')
                classes = re.findall(r'class\s+(\w+)', content)
                
                for class_name in classes:
                    if class_name not in ['Test', 'Tests', 'Main', 'App', 'Config']:
                        self.modules.add(class_name)
    
    def _extract_compliance_records(self):
        compliance_paths = [
            self.project_path / 'docs' / 'COMPLIANCE_MATRIX.md',
            self.project_path / 'COMPLIANCE_MATRIX.md',
            self.project_path / 'docs' / 'compliance.md',
            self.project_path / 'compliance.md',
            self.project_path / 'docs' / 'TRACEABILITY_MATRIX.md',
            self.project_path / 'TRACEABILITY_MATRIX.md'
        ]
        
        for comp_path in compliance_paths:
            if not comp_path.exists():
                continue
            
            content = comp_path.read_text(encoding='utf-8')
            
            for module in self.modules:
                if module in content:
                    record = {'file': str(comp_path), 'compliance_types': []}
                    
                    for comp_type in self.COMPLIANCE_TYPES:
                        if comp_type in content.lower():
                            record['compliance_types'].append(comp_type)
                    
                    self.compliance_records[module] = record
            
            if self.compliance_records:
                break
    
    def _calculate_result(self) -> Dict:
        total_modules = len(self.modules)
        
        if total_modules == 0:
            return {'passed': True, 'compliance_rate': 100, 'total_modules': 0, 'compliant': 0, 'non_compliant': [], 'details': [], 'threshold': 100, 'phase_conditions': ['P3-12']}
        
        compliant = []
        non_compliant = []
        
        for module in self.modules:
            if module in self.compliance_records:
                record = self.compliance_records[module]
                if len(record.get('compliance_types', [])) > 0:
                    compliant.append(module)
                else:
                    non_compliant.append(module)
            else:
                non_compliant.append(module)
        
        compliance_rate = (len(compliant) / total_modules * 100) if total_modules > 0 else 0
        passed = compliance_rate == 100
        
        details = []
        for module in self.modules:
            details.append({
                'module': module,
                'compliant': module in compliant,
                'compliance_types': self.compliance_records.get(module, {}).get('compliance_types', [])
            })
        
        return {'passed': passed, 'compliance_rate': round(compliance_rate, 2), 'total_modules': total_modules, 'compliant': len(compliant), 'non_compliant': non_compliant, 'details': details, 'threshold': 100, 'phase_conditions': ['P3-12']}


def main():
    parser = argparse.ArgumentParser(description='合規矩陣檢查器')
    parser.add_argument('--project-dir', type=str, default='.', help='專案目錄路徑')
    parser.add_argument('--output', type=str, default=None, help='輸出 JSON 檔案路徑')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細輸出')
    args = parser.parse_args()
    
    checker = ComplianceMatrixChecker(args.project_dir, args.verbose)
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
