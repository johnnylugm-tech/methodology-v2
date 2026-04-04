#!/usr/bin/env python3
"""
Generate Full Plan with FR Detailed Tasks

This script parses SRS.md to extract FR detailed requirements
and generates a comprehensive plan.

Usage:
    python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project
    python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project --output plan_FULL.md
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime


def parse_srs_fr_sections(srs_path: Path) -> list:
    """Parse SRS.md to extract FR sections"""
    content = srs_path.read_text(encoding='utf-8')
    
    # Find all FR sections (FR-01 to FR-99)
    fr_pattern = re.compile(r'(### FR-(\d+)：[^\n]+\n\n)(.*?)(?=\n---\n|\n### FR-\d+|$)', re.DOTALL)
    
    frs = []
    for m in fr_pattern.finditer(content):
        fr_num = f"FR-{m.group(2).zfill(2)}"
        title = m.group(1).strip().split('\n')[0].replace('### ', '')
        details = m.group(3).strip()
        
        # Extract description and test cases
        desc_match = re.search(r'\*\*描述\*\*：(.+?)(?:\n|$)', details, re.DOTALL)
        desc = desc_match.group(1).strip() if desc_match else ""
        
        # Extract test cases
        test_cases = re.findall(r'測試案例：[^「」]+「([^」]+)」[^「」]+「([^」]+)」', details)
        
        # Extract key requirements
        req_lines = []
        if '內容' in details:
            content_section = details.split('內容')[1].split('**')[0].strip()
            req_lines = [l.strip() for l in content_section.split('\n') if l.strip() and l.strip().startswith('-')]
        
        frs.append({
            'fr': fr_num,
            'title': title,
            'desc': desc,
            'test_cases': test_cases,
            'requirements': req_lines,
            'raw_details': details[:500]  # First 500 chars for reference
        })
    
    return frs


def generate_fr_detailed_task(fr: dict, module_info: dict = None) -> str:
    """Generate detailed task section for a single FR"""
    module_name = module_info.get('module', 'Unknown') if module_info else 'Unknown'
    file_path = module_info.get('file', '') if module_info else ''
    
    lines = [f"### {fr['fr']}: {fr['title']}"]
    lines.append("")
    lines.append(f"**任務**：{fr['desc']}")
    lines.append("")
    
    if fr['requirements']:
        lines.append("**SRS 要求**：")
        for req in fr['requirements']:
            lines.append(f"- {req}")
        lines.append("")
    
    if fr['test_cases']:
        lines.append("**測試案例**：")
        for input_text, output_text in fr['test_cases']:
            lines.append(f"- 輸入「{input_text}」→ 輸出「{output_text}」")
        lines.append("")
    
    if file_path:
        lines.append(f"**SAD 對應**：")
        lines.append(f"- 模組：`{module_name}`")
        lines.append(f"- 檔案：`{file_path}`")
        lines.append("")
    
    lines.append("**Forbidden**：")
    lines.append("- ❌ app/infrastructure/")
    lines.append("- ❌ @covers: L1 Error")
    lines.append("- ❌ @type: edge")
    lines.append("")
    
    return '\n'.join(lines)


def parse_sad_modules(repo_path: Path) -> dict:
    """Parse SAD.md to get FR -> module mapping"""
    sad_paths = [
        repo_path / "02-architecture" / "SAD.md",
        repo_path / "SAD.md",
    ]
    
    for sad_path in sad_paths:
        if not sad_path.exists():
            continue
        
        content = sad_path.read_text(encoding='utf-8')
        
        # Find FR to file mapping from table
        simple_pattern = re.compile(r'FR-(\d+)[^\n]*?`?(app/[^\s`]+)`?', re.DOTALL)
        modules = {}
        seen = set()
        
        for m in simple_pattern.finditer(content):
            fr_num = m.group(1)
            if fr_num in seen:
                continue
            file_path = m.group(2) or ""
            seen.add(fr_num)
            
            if '/' in file_path:
                filename = file_path.split('/')[-1].replace('.py', '')
                modules[f"FR-{fr_num}"] = {
                    'module': filename,
                    'file': file_path
                }
        
        if modules:
            return modules
    
    return {}


def generate_full_plan(phase: int, repo_path: Path, output_path: Path = None) -> str:
    """Generate full plan with detailed FR tasks"""
    
    # Find SRS.md
    srs_paths = [
        repo_path / "SRS.md",
        repo_path / "01-requirements" / "SRS.md",
        repo_path / "docs" / "SRS.md",
    ]
    
    srs_path = None
    for p in srs_paths:
        if p.exists():
            srs_path = p
            break
    
    if not srs_path:
        print(f"❌ SRS.md not found in {repo_path}")
        return None
    
    # Parse SRS and SAD
    frs = parse_srs_fr_sections(srs_path)
    modules = parse_sad_modules(repo_path)
    
    print(f"✅ Parsed {len(frs)} FRs from SRS.md")
    print(f"✅ Found {len(modules)} module mappings from SAD.md")
    
    # Generate plan
    plan_lines = [
        f"# Phase {phase} 完整執行計劃 — {repo_path.name}",
        "",
        f"> **版本**: v6.34.0",
        f"> **專案**: {repo_path.name}",
        f"> **日期**: {datetime.now().strftime('%Y-%m-%d')}",
        f"> **Framework**: methodology-v2 v6.34.0",
        f"> **狀態**: 完整版（含 FR 詳細任務）",
        "",
        "---",
        "",
        "## FR 詳細任務",
        "",
    ]
    
    for fr in frs:
        module_info = modules.get(fr['fr'], {})
        task = generate_fr_detailed_task(fr, module_info)
        plan_lines.append(task)
        plan_lines.append("---")
        plan_lines.append("")
    
    plan_text = '\n'.join(plan_lines)
    
    if output_path:
        output_path.write_text(plan_text, encoding='utf-8')
        print(f"💾 Full plan saved to: {output_path}")
    
    return plan_text


def main():
    parser = argparse.ArgumentParser(description='Generate full plan with FR detailed tasks')
    parser.add_argument('--phase', type=int, required=True, help='Phase number (e.g., 3)')
    parser.add_argument('--repo', type=str, required=True, help='Repository path')
    parser.add_argument('--output', type=str, help='Output file path')
    
    args = parser.parse_args()
    
    repo_path = Path(args.repo)
    if not repo_path.exists():
        print(f"❌ Repository not found: {repo_path}")
        return 1
    
    output_path = Path(args.output) if args.output else None
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plan = generate_full_plan(args.phase, repo_path, output_path)
    
    if plan:
        print(f"\n✅ Full plan generated ({len(plan)} chars)")
        print(plan[:2000])  # Print first 2000 chars
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
