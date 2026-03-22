#!/usr/bin/env python3
"""
Docs Optimizer - 自動化文件優化腳本

功能：
1. 檢查版本一致性 (README badge vs cli.py VERSION)
2. 更新 README 命令數量
3. 同步案例索引 (docs/cases/README.md)
4. 檢查 TODO/FIXME 註釋
5. 檢查文件完整性

觸發方式：
- Cron job: 每小時執行
- 手動: python cron_docs_optimizer.py --check
- 修復: python cron_docs_optimizer.py --fix
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime

# 設定
WORKSPACE = Path(__file__).parent.parent
README = WORKSPACE / "README.md"
CLI_PY = WORKSPACE / "cli.py"
CASES_README = WORKSPACE / "docs" / "cases" / "README.md"
DOCS_DIR = WORKSPACE / "docs"


class DocsOptimizer:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.fixes = []
        self.warnings = []
    
    def run(self, fix=False):
        """執行文件檢查/修復"""
        self.dry_run = not fix
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Docs Optimizer {'FIX' if fix else 'CHECK'}")
        print("=" * 50)
        
        # 1. 版本一致性檢查
        self.check_version_consistency()
        
        # 2. 更新 README 命令數量
        self.check_command_count()
        
        # 3. 同步案例索引
        self.sync_case_index()
        
        # 4. 檢查 TODO/FIXME
        self.check_todos()
        
        # 5. 檢查文件完整性
        self.check_file_integrity()
        
        # 總結
        self.print_summary()
        
        return len(self.fixes) == 0
    
    def check_version_consistency(self):
        """檢查版本一致性"""
        print("\n[1/5] 版本一致性檢查...")
        
        # 讀取 README badge 版本
        badge_pattern = r'version-(v[\d.]+)-'
        with open(README, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        badge_match = re.search(badge_pattern, readme_content)
        readme_version = badge_match.group(1) if badge_match else None
        
        # 讀取 cli.py VERSION
        version_pattern = r'VERSION\s*=\s*["\']([^"\']+)["\']'
        with open(CLI_PY, 'r', encoding='utf-8') as f:
            cli_content = f.read()
        
        cli_match = re.search(version_pattern, cli_content)
        cli_version = cli_match.group(1) if cli_match else None
        
        # 比對（正規化：都加上 v 前綴）
        if readme_version and cli_version:
            readme_normalized = readme_version if readme_version.startswith('v') else f'v{readme_version}'
            cli_normalized = cli_version if cli_version.startswith('v') else f'v{cli_version}'
            
            if readme_normalized == cli_normalized:
                print(f"   ✅ 版本一致: {readme_normalized}")
            else:
                self.warnings.append(f"版本不一致: README={readme_version}, cli.py={cli_version}")
                print(f"   ⚠️ 版本不一致: README={readme_version}, cli.py={cli_version}")
                if not self.dry_run:
                    self.fix_version_consistency(readme_version, cli_version)
        else:
            self.warnings.append("無法讀取版本資訊")
            print("   ❌ 無法讀取版本資訊")
    
    def fix_version_consistency(self, readme_version, cli_version):
        """修復版本一致性"""
        # 更新 cli.py
        with open(CLI_PY, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = re.sub(
            r'VERSION\s*=\s*["\'][^"\']+["\']',
            f'VERSION = "{readme_version}"',
            content
        )
        
        with open(CLI_PY, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        self.fixes.append(f"更新 cli.py VERSION: {cli_version} → {readme_version}")
        print(f"   ✅ 已修復: cli.py {cli_version} → {readme_version}")
    
    def check_command_count(self):
        """檢查 README 命令數量"""
        print("\n[2/5] 命令數量檢查...")
        
        # 統計 cli.py 中的命令
        cmd_pattern = r'def cmd_(\w+)\('
        with open(CLI_PY, 'r', encoding='utf-8') as f:
            content = f.read()
        
        commands = re.findall(cmd_pattern, content)
        cmd_count = len(commands)
        
        print(f"   📊 CLI 命令數量: {cmd_count}")
        
        # 檢查 README 中是否需要更新
        with open(README, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        readme_cmd_section = re.search(r'## 🔧 CLI 命令.*?(?=##|\Z)', readme_content, re.DOTALL)
        if readme_cmd_section:
            readme_cmd_count = len(re.findall(r'\| `\w+` \|', readme_cmd_section.group(0)))
            if readme_cmd_count != cmd_count:
                self.warnings.append(f"命令數量不一致: README={readme_cmd_count}, 實際={cmd_count}")
                print(f"   ⚠️ README 命令數量可能過時: README={readme_cmd_count}, 實際={cmd_count}")
    
    def sync_case_index(self):
        """同步案例索引"""
        print("\n[3/5] 案例索引同步...")
        
        # 取得所有案例
        cases_dir = DOCS_DIR / "cases"
        if not cases_dir.exists():
            self.warnings.append("docs/cases/ 目錄不存在")
            print("   ❌ docs/cases/ 目錄不存在")
            return
        
        case_files = sorted(cases_dir.glob("case*.md"))
        case_count = len(case_files)
        
        print(f"   📊 案例數量: {case_count}")
        
        # 檢查 README 表格
        if CASES_README.exists():
            with open(CASES_README, 'r', encoding='utf-8') as f:
                cases_content = f.read()
            
            # 統計表格行數
            table_lines = re.findall(r'\| \d+ \|', cases_content)
            readme_case_count = len(table_lines)
            
            if readme_case_count != case_count:
                self.warnings.append(f"案例數不一致: README={readme_case_count}, 實際={case_count}")
                print(f"   ⚠️ README 案例數: {readme_case_count}, 實際: {case_count}")
    
    def check_todos(self):
        """檢查 TODO/FIXME"""
        print("\n[4/5] TODO/FIXME 檢查...")
        
        todos = []
        fixmes = []
        
        for py_file in WORKSPACE.glob("*.py"):
            if py_file.name.startswith('cron_'):
                continue
            
            with open(py_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if 'TODO' in line:
                        todos.append(f"  {py_file.name}:{i} - {line.strip()[:60]}")
                    if 'FIXME' in line:
                        fixmes.append(f"  {py_file.name}:{i} - {line.strip()[:60]}")
        
        if todos:
            print(f"   📋 TODO: {len(todos)} 處")
            for t in todos[:5]:
                print(t)
            if len(todos) > 5:
                print(f"   ... 還有 {len(todos) - 5} 處")
        
        if fixmes:
            print(f"   🔧 FIXME: {len(fixmes)} 處")
            for f in fixmes[:5]:
                print(f)
    
    def check_file_integrity(self):
        """檢查文件完整性"""
        print("\n[5/5] 文件完整性檢查...")
        
        required_files = [
            "README.md",
            "cli.py",
            "SKILL.md",
            "docs/cases/README.md",
        ]
        
        for file_path in required_files:
            full_path = WORKSPACE / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                self.warnings.append(f"缺少檔案: {file_path}")
                print(f"   ❌ 缺少: {file_path}")
        
        # 檢查核心模組
        core_modules = [
            "agent_spawner.py",
            "agent_team.py",
            "tool_registry.py",
            "hybrid_workflow.py",
        ]
        
        print("   核心模組:")
        for module in core_modules:
            if (WORKSPACE / module).exists():
                print(f"   ✅ {module}")
            else:
                self.warnings.append(f"缺少核心模組: {module}")
                print(f"   ❌ {module}")
    
    def print_summary(self):
        """印出總結"""
        print("\n" + "=" * 50)
        print("總結")
        print("=" * 50)
        
        if self.dry_run:
            print(f"模式: DRY RUN (只檢查，不修復)")
        else:
            print(f"模式: FIX (已修復)")
        
        if self.fixes:
            print(f"\n✅ 已修復 ({len(self.fixes)} 項):")
            for f in self.fixes:
                print(f"   • {f}")
        
        if self.warnings:
            print(f"\n⚠️ 警告 ({len(self.warnings)} 項):")
            for w in self.warnings:
                print(f"   • {w}")
        
        if not self.fixes and not self.warnings:
            print("\n✅ 所有檢查通過")


def main():
    fix = "--fix" in sys.argv
    
    optimizer = DocsOptimizer()
    success = optimizer.run(fix=fix)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
