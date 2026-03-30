#!/usr/bin/env python3
"""
Threat Analyzer - 安全威脅分析工具
==========================
使用 STRIDE 框架自動分析系統威脅

STRIDE:
- Spoofing (身份偽裝)
- Tampering (資料篡改)
- Repudiation (否認)
- Information Disclosure (資訊洩露)
- Denial of Service (拒絕服務)
- Elevation of Privilege (權限提升)

使用方式：
    python3 quality_gate/threat_analyzer.py --project-dir /path/to/project
    python3 quality_gate/threat_analyzer.py --project-dir /path/to/project --output report.json

輸出：
    JSON 威脅分類報告
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


class ThreatAnalyzer:
    """STRIDE 威脅分析器"""
    
    # STRIDE 威脅類型對應的安全機制
    THREAT_MITIGATION = {
        'spoofing': ['Authentication', 'Session Management', 'PKI'],
        'tampering': ['Input Validation', 'Integrity Checking', 'Encryption'],
        'repudiation': ['Logging', 'Audit Trail', 'Digital Signature'],
        'information_disclosure': ['Encryption', 'Access Control', 'Data Masking'],
        'denial_of_service': ['Rate Limiting', 'Circuit Breaker', 'Load Balancing'],
        'elevation_of_privilege': ['Authorization', 'Role-Based Access', 'Principle of Least Privilege']
    }
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.threats: List[Dict] = []
    
    def analyze(self) -> Dict:
        """執行威脅分析"""
        # 1. 分析代碼威脅
        self._analyze_code_threats()
        
        # 2. 分析架構威脅
        self._analyze_architecture_threats()
        
        # 3. 分析配置威脅
        self._analyze_config_threats()
        
        # 4. 計算威脅等級
        high_severity = len([t for t in self.threats if t.get('severity') == 'HIGH'])
        medium_severity = len([t for t in self.threats if t.get('severity') == 'MEDIUM'])
        
        return {
            'passed': high_severity == 0,
            'total_threats': len(self.threats),
            'high_severity': high_severity,
            'medium_severity': medium_severity,
            'details': self.threats,
            'summary': {
                'spoofing': self._count_by_category('spoofing'),
                'tampering': self._count_by_category('tampering'),
                'repudiation': self._count_by_category('repudiation'),
                'information_disclosure': self._count_by_category('information_disclosure'),
                'denial_of_service': self._count_by_category('denial_of_service'),
                'elevation_of_privilege': self._count_by_category('elevation_of_privilege')
            }
        }
    
    def _analyze_code_threats(self):
        """分析代碼中的威脅"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        # 掃描所有 Python 文件
        for py_file in src_dir.rglob('*.py'):
            self._check_file_threats(py_file)
    
    def _check_file_threats(self, file_path: Path):
        """檢查單個檔案的威脅"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return
        
        lines = content.split('\n')
        
        # 1. Spoofing (身份偽裝威脅)
        if 'password' in content.lower() and 'hash' not in content.lower():
            self.threats.append({
                'category': 'spoofing',
                'severity': 'HIGH',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '密碼存儲未使用 hash',
                'mitigation': '使用 bcrypt 或 Argon2 進行密碼 hash'
            })
        
        if 'api_key' in content.lower() and 'os.getenv' not in content:
            self.threats.append({
                'category': 'spoofing',
                'severity': 'MEDIUM',
                'file': str(file_path.relative_to(self.project_path)),
                'description': 'API Key 可能硬編碼',
                'mitigation': '使用環境變量存取敏感資訊'
            })
        
        # 2. Tampering (資料篡改威脅)
        if 'exec(' in content or 'eval(' in content:
            self.threats.append({
                'category': 'tampering',
                'severity': 'HIGH',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '使用 eval/exec 可能導致程式碼注入',
                'mitigation': '避免使用 eval/exec，使用安全解析器'
            })
        
        if 'pickle.load' in content:
            self.threats.append({
                'category': 'tampering',
                'severity': 'HIGH',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '使用 pickle.load 可能導致反序列化攻擊',
                'mitigation': '使用 JSON 或安全的序列化格式'
            })
        
        # 3. Repudiation (否認威脅)
        if 'logger' not in content.lower() and len(lines) > 50:
            self.threats.append({
                'category': 'repudiation',
                'severity': 'MEDIUM',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '缺少日誌記錄',
                'mitigation': '添加結構化日誌記錄'
            })
        
        # 4. Information Disclosure (資訊洩露威脅)
        if 'debug' in content.lower() and 'DEBUG' not in content:
            for i, line in enumerate(lines):
                if 'print(' in line and ('debug' in line.lower() or 'log' in line.lower()):
                    self.threats.append({
                        'category': 'information_disclosure',
                        'severity': 'LOW',
                        'file': str(file_path.relative_to(self.project_path)),
                        'line': i + 1,
                        'description': '可能洩露敏感資訊的 debug 輸出',
                        'mitigation': '使用日誌框架而非 print'
                    })
                    break
        
        # 5. Denial of Service (拒絕服務威脅)
        if 'while' in content and 'input' in content:
            # 檢查是否有無限迴圈風險
            self.threats.append({
                'category': 'denial_of_service',
                'severity': 'MEDIUM',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '可能有無限迴圈風險',
                'mitigation': '添加迴圈終止條件和超時機制'
            })
        
        # 6. Elevation of Privilege (權限提升威脅)
        if 'chmod 777' in content or 'chmod(' in content and '0o777' in content:
            self.threats.append({
                'category': 'elevation_of_privilege',
                'severity': 'HIGH',
                'file': str(file_path.relative_to(self.project_path)),
                'description': '檔案權限設置過於寬鬆',
                'mitigation': '使用最小權限原則'
            })
    
    def _analyze_architecture_threats(self):
        """分析架構威脅"""
        sad_path = self.project_path / 'docs' / 'SAD.md'
        if not sad_path.exists():
            sad_path = self.project_path / 'SAD.md'
        
        if not sad_path.exists():
            return
        
        content = sad_path.read_text(encoding='utf-8')
        
        # 檢查是否有身份驗證機制
        if 'authentication' not in content.lower() and 'auth' not in content.lower():
            self.threats.append({
                'category': 'spoofing',
                'severity': 'HIGH',
                'file': 'SAD.md',
                'description': '缺少身份驗證機制說明',
                'mitigation': '在 SAD 中定義身份驗證架構'
            })
        
        # 檢查是否有加密機制
        if 'encrypt' not in content.lower() and 'tls' not in content.lower():
            self.threats.append({
                'category': 'information_disclosure',
                'severity': 'HIGH',
                'file': 'SAD.md',
                'description': '缺少加密機制說明',
                'mitigation': '在 SAD 中定義加密傳輸架構'
            })
    
    def _analyze_config_threats(self):
        """分析配置威脅"""
        config_files = [
            self.project_path / '.env.example',
            self.project_path / 'config.yaml',
            self.project_path / 'config.json'
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    content = config_file.read_text(encoding='utf-8')
                except Exception:
                    continue
                
                # 檢查是否包含敏感資訊
                if 'password' in content.lower() or 'secret' in content.lower():
                    self.threats.append({
                        'category': 'information_disclosure',
                        'severity': 'HIGH',
                        'file': str(config_file.name),
                        'description': '配置檔案可能包含敏感資訊',
                        'mitigation': '確保敏感資訊在 .env 中管理，不提交到版本控制'
                    })
    
    def _count_by_category(self, category: str) -> int:
        """計算某類別的威脅數量"""
        return len([t for t in self.threats if t.get('category') == category])


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='STRIDE 安全威脅分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/threat_analyzer.py
  python3 quality_gate/threat_analyzer.py --project-dir /path/to/project
  python3 quality_gate/threat_analyzer.py --project-dir . --output report.json
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
    
    # 執行威脅分析
    analyzer = ThreatAnalyzer(args.project_dir)
    result = analyzer.analyze()
    
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