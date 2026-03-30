#!/usr/bin/env python3
"""
Risk Status Checker - 風險狀態追蹤工具
=================================
檢查 RISK_REGISTER.md 中的風險狀態更新

使用方式：
    python3 quality_gate/risk_status_checker.py --project-dir /path/to/project
    python3 quality_gate/risk_status_checker.py --project-dir . --output risk_report.json

輸出：
    JSON 風險狀態報告
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class RiskStatusChecker:
    """風險狀態檢查器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.risks: List[Dict] = []
    
    def check(self) -> Dict:
        """執行風險檢查"""
        # 1. 讀取 RISK_REGISTER.md
        self._load_risk_register()
        
        # 2. 如果沒有找到，嘗試從 RISK_ASSESSMENT.md 加載
        if not self.risks:
            self._load_risk_assessment()
        
        # 3. 檢查風險狀態
        self._check_risk_status()
        
        # 4. 計算統計
        open_risks = len([r for r in self.risks if r.get('status') == 'Open'])
        closed_risks = len([r for r in self.risks if r.get('status') == 'Closed'])
        high_risks = len([r for r in self.risks if r.get('severity') == 'HIGH'])
        
        return {
            'passed': high_risks == 0,
            'total_risks': len(self.risks),
            'open_risks': open_risks,
            'closed_risks': closed_risks,
            'high_severity': high_risks,
            'details': self.risks,
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_risk_register(self):
        """從 RISK_REGISTER.md 載入風險"""
        risk_paths = [
            self.project_path / 'docs' / 'RISK_REGISTER.md',
            self.project_path / 'RISK_REGISTER.md',
            self.project_path / 'risk_register.md'
        ]
        
        for risk_path in risk_paths:
            if risk_path.exists():
                self._parse_risk_register(risk_path)
                break
    
    def _load_risk_assessment(self):
        """從 RISK_ASSESSMENT.md 載入風險"""
        risk_paths = [
            self.project_path / 'docs' / 'RISK_ASSESSMENT.md',
            self.project_path / 'RISK_ASSESSMENT.md',
            self.project_path / 'risk_assessment.md'
        ]
        
        for risk_path in risk_paths:
            if risk_path.exists():
                self._parse_risk_assessment(risk_path)
                break
    
    def _parse_risk_register(self, file_path: Path):
        """解析 RISK_REGISTER.md"""
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # 解析 Markdown 表格
        current_risk = None
        
        for line in lines:
            line = line.strip()
            
            # 跳過表格標題行
            if line.startswith('|') and '---' not in line:
                continue
            
            # 解析風險 ID
            if line.startswith('| R') or '| R' in line:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                
                if len(parts) >= 3:
                    # 嘗試識別風險 ID 和描述
                    risk_id = parts[0] if parts[0].startswith('R') else ''
                    description = parts[1] if len(parts) > 1 else ''
                    
                    if risk_id and description:
                        # 確定狀態
                        status = 'Open'
                        if 'Closed' in line or 'Mitigation' in line:
                            status = 'Closed'
                        
                        # 確定嚴重性
                        severity = 'MEDIUM'
                        if 'High' in line or '🔴' in line:
                            severity = 'HIGH'
                        elif 'Low' in line or '🟢' in line:
                            severity = 'LOW'
                        
                        self.risks.append({
                            'id': risk_id,
                            'description': description,
                            'status': status,
                            'severity': severity
                        })
    
    def _parse_risk_assessment(self, file_path: Path):
        """解析 RISK_ASSESSMENT.md"""
        content = file_path.read_text(encoding='utf-8')
        
        # 提取風險描述
        pattern = r'(R\d+)[^\n]*\s*-\s*([^\n]+)'
        matches = re.findall(pattern, content)
        
        for risk_id, description in matches:
            self.risks.append({
                'id': risk_id,
                'description': description,
                'status': 'Open',
                'severity': 'MEDIUM'
            })
    
    def _check_risk_status(self):
        """檢查風險狀態"""
        for risk in self.risks:
            # 檢查是否有監控記錄
            if not risk.get('monitoring_record'):
                risk['monitoring_record'] = 'missing'
            
            # 檢查是否有緩解措施
            if not risk.get('mitigation'):
                risk['mitigation_status'] = 'not_implemented'
            else:
                risk['mitigation_status'] = 'implemented'


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='風險狀態追蹤工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/risk_status_checker.py
  python3 quality_gate/risk_status_checker.py --project-dir /path/to/project
  python3 quality_gate/risk_status_checker.py --project-dir . --output risk_report.json
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
    
    # 執行風險檢查
    checker = RiskStatusChecker(args.project_dir)
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