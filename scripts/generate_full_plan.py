#!/usr/bin/env python3
"""
Generate Full Plan with Phase-Specific Detailed Tasks

This script parses previous phase artifacts to generate detailed tasks
for each phase in the methodology-v2 framework.

Phase Artifacts Mapping:
- Phase 1: (no previous artifacts)
- Phase 2: SRS.md → Architecture requirements
- Phase 3: SRS.md + SAD.md → Implementation tasks
- Phase 4: SRS.md + SAD.md + Code → Testing tasks
- Phase 5: TEST_RESULTS.md + BASELINE.md → Verification tasks
- Phase 6: QUALITY_REPORT.md → Quality assurance tasks
- Phase 7: RISK_REGISTER.md → Risk management tasks
- Phase 8: CONFIG_RECORDS.md → Configuration tasks

Usage:
    python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project
    python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project --output phase3_FULL.md
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================================
# Phase-Specific Parsers
# ============================================================================

def parse_srs_fr_sections(srs_path: Path) -> List[Dict]:
    """Parse SRS.md to extract FR sections"""
    if not srs_path.exists():
        return []
    
    # v6.103 fix: Read FRs from both SRS.md and SAD.md
    # SRS.md may not have all FRs (e.g., FR-09 exists in SAD but not SRS)
    content = srs_path.read_text(encoding='utf-8')
    
    # Also read SAD.md for complete FR list
    # repo_path = srs_path.parent.parent (01-requirements -> project root)
    repo_path = srs_path.parent.parent
    sad_path = repo_path / "02-architecture" / "SAD.md"
    if sad_path.exists():
        sad_content = sad_path.read_text(encoding='utf-8')
        content += "\n" + sad_content
    
    # Find all FR sections (FR-01 to FR-99)
    fr_pattern = re.compile(r'(### FR-(\d+)：[^\n]+\n\n)(.*?)(?=\n---\n|\n### FR-\d+|$)', re.DOTALL)
    
    frs = []
    for m in fr_pattern.finditer(content):
        fr_num = f"FR-{m.group(2).zfill(2)}"
        title = m.group(1).strip().split('\n')[0].replace('### ', '')
        details = m.group(3).strip()
        
        # Extract description
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
            'raw_details': details[:500]
        })
    
    return frs


def parse_sad_modules(repo_path: Path) -> Dict:
    """Parse SAD.md to get FR -> module mapping"""
    sad_paths = [
        repo_path / "02-architecture" / "SAD.md",
        repo_path / "SAD.md",
        repo_path / "templates" / "SAD.md",
    ]
    
    for sad_path in sad_paths:
        if not sad_path.exists():
            continue
        
        content = sad_path.read_text(encoding='utf-8')
        
        # Find FR to file mapping from table
        # Use ^ anchor (MULTILINE) to avoid cross-line matching issues
        simple_pattern = re.compile(
            r'^\s*\|\s*\*\*FR-(\d+)\*\*[^*\n]*`((?:app/|03-development/src/)[^\s`]+)`',
            re.MULTILINE
        )
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
                # Normalize path: ensure app/ prefix (project standard)
                if file_path.startswith('03-development/src/'):
                    file_path = file_path.replace('03-development/src/', 'app/')
                elif not file_path.startswith('app/'):
                    file_path = f"app/{file_path}"
                modules[f"FR-{fr_num}"] = {
                    'module': filename,
                    'file': file_path
                }
        
        if modules:
            return modules
    
    return {}


def parse_test_plan(repo_path: Path) -> List[Dict]:
    """Parse TEST_PLAN.md to extract test requirements"""
    test_plan_paths = [
        repo_path / "04-testing" / "TEST_PLAN.md",
        repo_path / "TEST_PLAN.md",
        repo_path / "docs" / "TEST_PLAN.md",
    ]
    
    for tp_path in test_plan_paths:
        if not tp_path.exists():
            continue
        
        content = tp_path.read_text(encoding='utf-8')
        
        # Extract test categories
        test_pattern = re.compile(r'(###\s+\d+\.\d+\s+[^\n]+\n)(.*?)(?=\n###|\n##|\Z)', re.DOTALL)
        tests = []
        
        for m in test_pattern.finditer(content):
            title = m.group(1).strip().replace('### ', '')
            details = m.group(2).strip()[:300]
            tests.append({
                'title': title,
                'details': details
            })
        
        if tests:
            return tests
    
    return []


def parse_quality_report(repo_path: Path) -> Dict:
    """Parse QUALITY_REPORT.md"""
    qr_paths = [
        repo_path / "06-quality" / "QUALITY_REPORT.md",
        repo_path / "QUALITY_REPORT.md",
        repo_path / "docs" / "QUALITY_REPORT.md",
    ]
    
    for qr_path in qr_paths:
        if not qr_path.exists():
            continue
        
        content = qr_path.read_text(encoding='utf-8')
        
        # Extract quality metrics
        metrics = re.findall(r'\*\*([^\*]+)\*\*：(.+?)(?:\n|$)', content)
        
        return {
            'metrics': [(k.strip(), v.strip()) for k, v in metrics],
            'content_preview': content[:500]
        }
    
    return {}


def parse_risk_register(repo_path: Path) -> List[Dict]:
    """Parse RISK_REGISTER.md"""
    rr_paths = [
        repo_path / "07-risk" / "RISK_REGISTER.md",
        repo_path / "RISK_REGISTER.md",
        repo_path / "docs" / "RISK_REGISTER.md",
    ]
    
    for rr_path in rr_paths:
        if not rr_path.exists():
            continue
        
        content = rr_path.read_text(encoding='utf-8')
        
        # Extract risk entries
        risk_pattern = re.compile(r'\|\s*([^\|]+)\s*\|.*?\|.*?\|.*?\|', re.MULTILINE)
        risks = []
        for m in risk_pattern.finditer(content):
            risk_name = m.group(1).strip()
            if risk_name and len(risk_name) > 3:
                risks.append({'name': risk_name})
        
        if risks:
            return risks[:20]  # Limit to 20 risks
    
    return []


def parse_config_records(repo_path: Path) -> List[Dict]:
    """Parse CONFIG_RECORDS.md"""
    cr_paths = [
        repo_path / "08-configuration" / "CONFIG_RECORDS.md",
        repo_path / "CONFIG_RECORDS.md",
        repo_path / "docs" / "CONFIG_RECORDS.md",
    ]
    
    for cr_path in cr_paths:
        if not cr_path.exists():
            continue
        
        content = cr_path.read_text(encoding='utf-8')
        
        # Extract config items
        config_pattern = re.compile(r'\|\s*([^\|]+)\s*\|.*?\|.*?\|', re.MULTILINE)
        configs = []
        for m in config_pattern.finditer(content):
            config_name = m.group(1).strip()
            if config_name and len(config_name) > 3:
                configs.append({'name': config_name})
        
        if configs:
            return configs[:20]
    
    return []


def parse_srs_nfr_sections(srs_path: Path) -> List[Dict]:
    """Parse SRS.md to extract NFR sections"""
    if not srs_path.exists():
        return []
    
    content = srs_path.read_text(encoding='utf-8')
    
    # Find NFR sections
    nfr_pattern = re.compile(r'(### NFR-(\d+)：[^\n]+\n\n)(.*?)(?=\n---\n|\n###|\n##|\Z)', re.DOTALL)
    
    nfrs = []
    for m in nfr_pattern.finditer(content):
        nfr_num = f"NFR-{m.group(2).zfill(2)}"
        title = m.group(1).strip().split('\n')[0].replace('### ', '')
        details = m.group(3).strip()[:400]
        
        nfrs.append({
            'nfr': nfr_num,
            'title': title,
            'details': details
        })
    
    return nfrs


# ============================================================================
# Phase Task Generators
# ============================================================================

def generate_phase1_tasks(repo_path: Path, srs_path: Path) -> List[str]:
    """Generate Phase 1 detailed tasks (Requirements Specification)"""
    lines = []
    lines.append("## Phase 1 任務：需求規格制定")
    lines.append("")
    lines.append("### Phase 1 概述")
    lines.append("Phase 1 是專案起點，主要任務是制定完整的軟體需求規格（SRS）。")
    lines.append("")
    
    frs = parse_srs_fr_sections(srs_path)
    nfrs = parse_srs_nfr_sections(srs_path)
    
    if frs:
        lines.append("### FR 需求（共 {} 項）".format(len(frs)))
        lines.append("")
        for fr in frs:
            lines.append(f"#### {fr['fr']}: {fr['title']}")
            lines.append(f"**任務**：{fr['desc']}")
            if fr['requirements']:
                lines.append("**需求內容**：")
                for req in fr['requirements'][:5]:
                    lines.append(f"- {req}")
            lines.append("")
    
    if nfrs:
        lines.append("### NFR 非功能需求（共 {} 項）".format(len(nfrs)))
        lines.append("")
        for nfr in nfrs:
            lines.append(f"#### {nfr['nfr']}: {nfr['title']}")
            lines.append(f"**要求**：{nfr['details'][:200]}")
            lines.append("")
    
    lines.append("### Phase 1 交付物")
    lines.append("- [ ] `SRS.md` - 軟體需求規格文件")
    lines.append("- [ ] `SPEC_TRACKING.md` - 規格追蹤矩陣")
    lines.append("- [ ] `TRACEABILITY_MATRIX.md` - 需求追蹤矩陣")
    lines.append("")
    
    return lines


def generate_phase2_tasks(repo_path: Path, srs_path: Path) -> List[str]:
    """Generate Phase 2 detailed tasks (Architecture Design)"""
    lines = []
    lines.append("## Phase 2 任務：架構設計")
    lines.append("")
    lines.append("### Phase 2 概述")
    lines.append("Phase 2 基於 SRS 進行系統架構設計，產出 SAD 和 ADR。")
    lines.append("")
    
    frs = parse_srs_fr_sections(srs_path)
    modules = parse_sad_modules(repo_path)
    
    if frs:
        lines.append("### FR 對應架構（共 {} 項）".format(len(frs)))
        lines.append("")
        for fr in frs:
            lines.append(f"#### {fr['fr']}: {fr['title']}")
            lines.append(f"**需求**：{fr['desc']}")
            
            mod = modules.get(fr['fr'], {})
            if mod:
                lines.append(f"**對應模組**：")
                lines.append(f"- 模組：`{mod.get('module', 'N/A')}`")
                lines.append(f"- 檔案：`{mod.get('file', 'N/A')}`")
            lines.append("")
    
    lines.append("### Phase 2 交付物")
    lines.append("- [ ] `SAD.md` - 軟體架構文件")
    lines.append("- [ ] `ADR.md` - 架構決策記錄")
    lines.append("- [ ] `ARCHITECTURE_DIAGRAM.md` - 架構圖")
    lines.append("")
    
    return lines


def generate_phase3_tasks(repo_path: Path, srs_path: Path) -> List[str]:
    """Generate Phase 3 detailed tasks (Implementation)"""
    lines = []
    lines.append("## Phase 3 任務：代碼實作")
    lines.append("")
    lines.append("### Phase 3 概述")
    lines.append("Phase 3 依據 SAD 實作所有 FR 模組，包含單元測試。")
    lines.append("")
    
    frs = parse_srs_fr_sections(srs_path)
    modules = parse_sad_modules(repo_path)
    
    if frs:
        lines.append("### FR 實作任務（共 {} 項）".format(len(frs)))
        lines.append("")
        for fr in frs:
            lines.append(f"#### {fr['fr']}: {fr['title']}")
            lines.append(f"**任務**：{fr['desc']}")
            
            if fr['requirements']:
                lines.append("**SRS 要求**：")
                for req in fr['requirements'][:5]:
                    lines.append(f"- {req}")
            
            if fr['test_cases']:
                lines.append("**測試案例**：")
                for inp, out in fr['test_cases']:
                    lines.append(f"- 輸入「{inp}」→ 輸出「{out}」")
            
            mod = modules.get(fr['fr'], {})
            if mod:
                lines.append("**SAD 對應**：")
                lines.append(f"- 模組：`{mod.get('module', 'N/A')}`")
                lines.append(f"- 檔案：`{mod.get('file', 'N/A')}`")
            
            lines.append("**Forbidden**：")
            lines.append("- ❌ app/infrastructure/（已廢除）")
            lines.append("- ❌ @covers: L1 Error")
            lines.append("- ❌ @type: edge")
            lines.append("")
    
    lines.append("### Phase 3 交付物")
    lines.append("- [ ] `app/processing/` - 處理模組")
    lines.append("- [ ] `app/synth/` - 合成模組")
    lines.append("- [ ] `app/infrastructure/` - 基礎設施模組")
    lines.append("- [ ] `app/api/` - API 路由")
    lines.append("- [ ] `app/cli/` - CLI 工具")
    lines.append("- [ ] `app/backend/` - 後端整合")
    lines.append("- [ ] `tests/` - 單元測試")
    lines.append("")
    
    return lines


def generate_phase4_tasks(repo_path: Path, srs_path: Path) -> List[str]:
    """Generate Phase 4 detailed tasks (Testing)"""
    lines = []
    lines.append("## Phase 4 任務：測試規劃與執行")
    lines.append("")
    lines.append("### Phase 4 概述")
    lines.append("Phase 4 基於 Phase 3 代碼制定完整測試計畫並執行。")
    lines.append("")
    
    frs = parse_srs_fr_sections(srs_path)
    test_plans = parse_test_plan(repo_path)
    
    if test_plans:
        lines.append("### 測試項目（共 {} 項）".format(len(test_plans)))
        lines.append("")
        for tp in test_plans:
            lines.append(f"#### {tp['title']}")
            lines.append(f"**內容**：{tp['details'][:200]}")
            lines.append("")
    else:
        lines.append("### FR 測試覆蓋")
        lines.append("")
        for fr in frs:
            lines.append(f"#### {fr['fr']}: {fr['title']}")
            lines.append(f"**測試目標**：驗證 {fr['desc']}")
            if fr['test_cases']:
                lines.append("**測試案例**：")
                for inp, out in fr['test_cases']:
                    lines.append(f"- 輸入「{inp}」→ 輸出「{out}」")
            lines.append("")
    
    lines.append("### Phase 4 交付物")
    lines.append("- [ ] `TEST_PLAN.md` - 測試計畫")
    lines.append("- [ ] `TEST_RESULTS.md` - 測試結果")
    lines.append("- [ ] `COVERAGE_REPORT.md` - 覆蓋率報告")
    lines.append("")
    
    return lines


def generate_phase5_tasks(repo_path: Path) -> List[str]:
    """Generate Phase 5 detailed tasks (Verification)"""
    lines = []
    lines.append("## Phase 5 任務：驗證交付")
    lines.append("")
    lines.append("### Phase 5 概述")
    lines.append("Phase 5 依據測試結果進行系統驗證，確保符合需求。")
    lines.append("")
    
    lines.append("### 驗證項目")
    lines.append("- [ ] 整合測試通過")
    lines.append("- [ ] 效能測試達標")
    lines.append("- [ ] 安全掃描通過")
    lines.append("- [ ] Baseline 建立完成")
    lines.append("")
    
    lines.append("### Phase 5 交付物")
    lines.append("- [ ] `BASELINE.md` - 系統基線")
    lines.append("- [ ] `MONITORING_PLAN.md` - 監控計畫")
    lines.append("- [ ] `VERIFICATION_REPORT.md` - 驗證報告")
    lines.append("")
    
    return lines


def generate_phase6_tasks(repo_path: Path) -> List[str]:
    """Generate Phase 6 detailed tasks (Quality Assurance)"""
    lines = []
    lines.append("## Phase 6 任務：品質保證")
    lines.append("")
    lines.append("### Phase 6 概述")
    lines.append("Phase 6 進行全面品質評估，確保系統達到發布標準。")
    lines.append("")
    
    qr = parse_quality_report(repo_path)
    if qr.get('metrics'):
        lines.append("### 品質指標")
        lines.append("")
        for metric, value in qr['metrics']:
            lines.append(f"- **{metric}**：{value}")
        lines.append("")
    
    lines.append("### Phase 6 交付物")
    lines.append("- [ ] `QUALITY_REPORT.md` - 品質報告")
    lines.append("- [ ] `RELEASE_NOTES.md` - 發布備註")
    lines.append("- [ ] `FINAL_SIGN_OFF.md` - 最終確認")
    lines.append("")
    
    return lines


def generate_phase7_tasks(repo_path: Path) -> List[str]:
    """Generate Phase 7 detailed tasks (Risk Management)"""
    lines = []
    lines.append("## Phase 7 任務：風險管理")
    lines.append("")
    lines.append("### Phase 7 概述")
    lines.append("Phase 7 識別、追蹤並緩解所有已識別的風險。")
    lines.append("")
    
    risks = parse_risk_register(repo_path)
    if risks:
        lines.append("### 風險註冊表（共 {} 項）".format(len(risks)))
        lines.append("")
        for risk in risks:
            lines.append(f"- **{risk['name']}**：需制定緩解策略")
        lines.append("")
    else:
        lines.append("### 風險類別")
        lines.append("- 技術風險")
        lines.append("- 排程風險")
        lines.append("- 資源風險")
        lines.append("- 外部風險")
        lines.append("")
    
    lines.append("### Phase 7 交付物")
    lines.append("- [ ] `RISK_REGISTER.md` - 風險註冊表")
    lines.append("- [ ] `RISK_MITIGATION_PLANS.md` - 緩解計畫")
    lines.append("- [ ] `RISK_STATUS_REPORT.md` - 風險狀態報告")
    lines.append("")
    
    return lines


def generate_phase8_tasks(repo_path: Path) -> List[str]:
    """Generate Phase 8 detailed tasks (Configuration Management)"""
    lines = []
    lines.append("## Phase 8 任務：配置管理")
    lines.append("")
    lines.append("### Phase 8 概述")
    lines.append("Phase 8 建立完整的配置管理系統，確保可追溯性。")
    lines.append("")
    
    configs = parse_config_records(repo_path)
    if configs:
        lines.append("### 配置項目（共 {} 項）".format(len(configs)))
        lines.append("")
        for config in configs:
            lines.append(f"- **{config['name']}**：需建立配置記錄")
        lines.append("")
    else:
        lines.append("### 配置類別")
        lines.append("- 環境配置")
        lines.append("- 部署配置")
        lines.append("- 安全配置")
        lines.append("- 監控配置")
        lines.append("")
    
    lines.append("### Phase 8 交付物")
    lines.append("- [ ] `CONFIG_RECORDS.md` - 配置記錄")
    lines.append("- [ ] `DEPLOYMENT_CHECKLIST.md` - 部署檢查清單")
    lines.append("- [ ] `ENVIRONMENT_SPEC.md` - 環境規格")
    lines.append("")
    
    return lines


# ============================================================================
# Main Generator
# ============================================================================

def generate_full_plan(phase: int, repo_path: Path, output_path: Path = None) -> Optional[str]:
    """Generate full plan with phase-specific detailed tasks"""
    
    # Phase-specific artifact paths
    srs_paths = [
        repo_path / "SRS.md",
        repo_path / "01-requirements" / "SRS.md",
        repo_path / "docs" / "SRS.md",
    ]
    srs_path = next((p for p in srs_paths if p.exists()), None)
    
    # Generate phase-specific tasks
    generators = {
        1: lambda: generate_phase1_tasks(repo_path, srs_path),
        2: lambda: generate_phase2_tasks(repo_path, srs_path),
        3: lambda: generate_phase3_tasks(repo_path, srs_path),
        4: lambda: generate_phase4_tasks(repo_path, srs_path),
        5: lambda: generate_phase5_tasks(repo_path),
        6: lambda: generate_phase6_tasks(repo_path),
        7: lambda: generate_phase7_tasks(repo_path),
        8: lambda: generate_phase8_tasks(repo_path),
    }
    
    generator = generators.get(phase)
    if not generator:
        print(f"❌ Unknown phase: {phase}")
        return None
    
    print(f"📋 Generating Phase {phase} tasks...")
    
    task_lines = generator()
    
    # Build full plan
    phase_names = {
        1: "需求規格",
        2: "架構設計",
        3: "代碼實作",
        4: "測試",
        5: "驗證交付",
        6: "品質保證",
        7: "風險管理",
        8: "配置管理"
    }
    
    plan_lines = [
        f"# Phase {phase} 完整執行計劃 — {repo_path.name}",
        "",
        f"> **版本**: v6.49.0",
        f"> **專案**: {repo_path.name}",
        f"> **日期**: {datetime.now().strftime('%Y-%m-%d')}",
        f"> **Framework**: methodology-v2 v6.49.0",
        f"> **Phase**: {phase} - {phase_names.get(phase, 'Unknown')}",
        f"> **狀態**: 完整版（含 Phase {phase} 詳細任務）",
        "",
        "---",
        "",
    ]
    
    plan_lines.extend(task_lines)
    
    plan_text = '\n'.join(plan_lines)
    
    if output_path:
        output_path.write_text(plan_text, encoding='utf-8')
        print(f"💾 Full plan saved to: {output_path}")
    
    return plan_text


def main():
    parser = argparse.ArgumentParser(
        description='Generate full plan with phase-specific detailed tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project
    python3 scripts/generate_full_plan.py --phase 5 --repo /path/to/project --output phase5_FULL.md
        """
    )
    parser.add_argument('--phase', type=int, required=True, help='Phase number (1-8)')
    parser.add_argument('--repo', type=str, required=True, help='Repository path')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--no-output', action='store_true', help='Print to stdout instead of saving to file')
    
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
        if args.no_output:
            # Print full plan to stdout for piping
            print(plan)
        else:
            print(f"\n✅ Full plan generated ({len(plan)} chars)")
            print(plan[:1500])
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
