#!/usr/bin/env python3
"""
規格書合規性驗證 Script
=========================
自動檢查實作是否符合 PDF 規格書要求

使用方法：
    python verify_spec_compliance.py /path/to/project
    python verify_spec_compliance.py /path/to/project --fix
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Tuple, List, Dict


class SpecComplianceChecker:
    """規格書合規性檢查器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues = []
        self.passed = []
    
    def check_all(self) -> Dict:
        """執行所有檢查"""
        checks = [
            self.check_audio_merge,
            self.check_splitters,
            self.check_retry_mechanism,
            self.check_circuit_breaker,
            self.check_logging,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.issues.append(f"檢查執行失敗: {check.__name__} - {e}")
        
        return {
            "passed": self.passed,
            "issues": self.issues,
            "total": len(self.passed) + len(self.issues),
            "score": f"{len(self.passed)}/{len(self.passed) + len(self.issues)}"
        }
    
    # ========== 檢查項目 ==========
    
    def check_audio_merge(self):
        """檢查音訊合併是否正確處理所有段落"""
        cli_file = self.project_path / "src" / "cli.py"
        
        if not cli_file.exists():
            self.issues.append("cli.py 不存在")
            return
        
        content = cli_file.read_text()
        
        # 錯誤模式：shutil.copy(temp_files[0], ...)
        if re.search(r"shutil\.copy\(temp_files\[0\]", content):
            self.issues.append("音訊合併：只複製第一段，未合併所有段落 (P6)")
            return
        
        # 正確模式：for ... in temp_files: ... write
        if "for temp_file in temp_files" in content and "write(f.read())" in content:
            self.passed.append("音訊合併：正確處理所有段落 (P6)")
        else:
            self.issues.append("音訊合併：未找到合併邏輯")
    
    def check_splitters(self):
        """檢查分段標記是否包含換行符"""
        text_processor_file = self.project_path / "src" / "text_processor.py"
        
        if not text_processor_file.exists():
            self.issues.append("text_processor.py 不存在")
            return
        
        content = text_processor_file.read_text()
        
        # 檢查 DEFAULT_SPLITTERS 是否包含 \n
        if r'"\n"' in content or r"'\n'" in content:
            self.passed.append("分段標記：包含換行符 \\n (P8)")
        else:
            self.issues.append("分段標記：未包含換行符 \\n (P8)")
    
    def check_retry_mechanism(self):
        """檢查重試機制是否有指數退避"""
        retry_file = self.project_path / "src" / "retry_handler.py"
        
        if not retry_file.exists():
            self.issues.append("retry_handler.py 不存在")
            return
        
        content = retry_file.read_text()
        
        # 指數退避模式：2 ** attempt 或 pow(2, attempt)
        if "2 ** attempt" in content or "pow(2, attempt)" in content:
            self.passed.append("重試機制：指數退避已實現")
        else:
            self.issues.append("重試機制：未找到指數退避邏輯")
    
    def check_circuit_breaker(self):
        """檢查熔斷器是否有完整實作"""
        retry_file = self.project_path / "src" / "retry_handler.py"
        
        if not retry_file.exists():
            return
        
        content = retry_file.read_text()
        
        # 檢查是否有狀態機
        if "CircuitState" in content or "CircuitBreaker" in content:
            # 檢查是否只是空殼
            if "return await self.execute_with_retry" in content and "CircuitBreaker" not in content[:content.find("return await")]:
                self.issues.append("熔斷器：僅有空殼實作")
            else:
                self.passed.append("熔斷器：狀態機已實現")
    
    def check_logging(self):
        """檢查是否有適當的日誌記錄"""
        cli_file = self.project_path / "src" / "cli.py"
        
        if not cli_file.exists():
            return
        
        content = cli_file.read_text()
        
        if "logging" in content and ("logger.error" in content or "logger.info" in content):
            self.passed.append("錯誤日誌：已實現 logging")
        elif "print(" in content:
            self.issues.append("錯誤日誌：僅使用 print()，建議改用 logging")


def main():
    parser = argparse.ArgumentParser(description="規格書合規性驗證")
    parser.add_argument("project_path", help="專案路徑")
    parser.add_argument("--fix", action="store_true", help="嘗試自動修復")
    parser.add_argument("--json", action="store_true", help="JSON 輸出")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.project_path):
        print(f"錯誤：路徑不存在或不是目錄: {args.project_path}")
        sys.exit(1)
    
    checker = SpecComplianceChecker(args.project_path)
    result = checker.check_all()
    
    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 50)
        print("規格書合規性檢查報告")
        print("=" * 50)
        print(f"分數: {result['score']}")
        print()
        
        if result['passed']:
            print("✅ 通過項目:")
            for p in result['passed']:
                print(f"  • {p}")
            print()
        
        if result['issues']:
            print("❌ 問題項目:")
            for issue in result['issues']:
                print(f"  • {issue}")
            print()
        
        if not result['passed'] and not result['issues']:
            print("無檢查結果，請確認專案結構")
    
    sys.exit(0 if not result['issues'] else 1)


if __name__ == "__main__":
    main()