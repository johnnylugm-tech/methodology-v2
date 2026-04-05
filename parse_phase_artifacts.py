# Phase Artifact Parser
# Parses outputs from previous phases for inheritance

from pathlib import Path
from typing import Dict, List, Optional


def parse_phase_artifacts(phase: int, repo_path: Path) -> dict:
    """
    解析上階段所有產出
    
    Args:
        phase: 當前 Phase（會解析 phase-1 的產出）
        repo_path: 專案路徑
    
    Returns:
        dict: 包含所有解析的 artifacts
    """
    artifacts = {}
    prev_phase = phase - 1
    
    # Phase 1 產出（從 TASK_INITIALIZATION_PROMPT）
    if prev_phase >= 1:
        tip_path = repo_path / "TASK_INITIALIZATION_PROMPT.md"
        if tip_path.exists():
            artifacts['tip'] = {
                'path': str(tip_path),
                'exists': True,
                'content_preview': tip_path.read_text()[:200] + "..."
            }
        else:
            artifacts['tip'] = {'exists': False, 'path': 'TASK_INITIALIZATION_PROMPT.md'}
    
    # Phase 2 產出（SRS.md）
    if prev_phase >= 2:
        srs_path = repo_path / "SRS.md"
        if srs_path.exists():
            content = srs_path.read_text()
            fr_count = content.count('### FR-')
            nfr_count = content.count('### NFR-')
            artifacts['srs'] = {
                'path': str(srs_path),
                'exists': True,
                'fr_count': fr_count,
                'nfr_count': nfr_count
            }
        else:
            artifacts['srs'] = {'exists': False, 'path': 'SRS.md'}
    
    # Phase 3 產出（SAD.md, ADR.md, app/）
    if prev_phase >= 3:
        # SAD paths
        sad_paths = [
            repo_path / "02-architecture" / "SAD.md",
            repo_path / "SAD.md"
        ]
        sad_path = next((p for p in sad_paths if p.exists()), None)
        if sad_path:
            content = sad_path.read_text()
            module_count = content.count('## Module')
            artifacts['sad'] = {
                'path': str(sad_path),
                'exists': True,
                'module_count': module_count
            }
        else:
            artifacts['sad'] = {'exists': False, 'path': 'SAD.md'}
        
        # ADR
        adr_paths = [
            repo_path / "02-architecture" / "ADR.md",
            repo_path / "ADR.md"
        ]
        adr_path = next((p for p in adr_paths if p.exists()), None)
        artifacts['adr'] = {'exists': adr_path is not None, 'path': str(adr_path) if adr_path else 'ADR.md'}
        
        # app/ directory
        app_path = repo_path / "app"
        if app_path.exists():
            py_files = list(app_path.glob("**/*.py"))
            artifacts['app'] = {
                'exists': True,
                'path': 'app/',
                'file_count': len(py_files)
            }
        else:
            artifacts['app'] = {'exists': False, 'path': 'app/'}
    
    # Phase 4 產出（TEST_RESULTS.md）
    if prev_phase >= 4:
        test_paths = [
            repo_path / "04-testing" / "TEST_RESULTS.md",
            repo_path / "TEST_RESULTS.md"
        ]
        test_path = next((p for p in test_paths if p.exists()), None)
        artifacts['test_results'] = {'exists': test_path is not None, 'path': str(test_path) if test_path else 'TEST_RESULTS.md'}
        
        # src/ directory
        src_path = repo_path / "src"
        artifacts['src'] = {'exists': src_path.exists(), 'path': 'src/'}
    
    # Phase 5 產出（BASELINE.md）
    if prev_phase >= 5:
        baseline_paths = [
            repo_path / "05-verify" / "BASELINE.md",
            repo_path / "BASELINE.md"
        ]
        baseline_path = next((p for p in baseline_paths if p.exists()), None)
        artifacts['baseline'] = {'exists': baseline_path is not None, 'path': str(baseline_path) if baseline_path else 'BASELINE.md'}
    
    # Phase 6 產出（QUALITY_REPORT.md）
    if prev_phase >= 6:
        qr_paths = [
            repo_path / "06-quality" / "QUALITY_REPORT.md",
            repo_path / "QUALITY_REPORT.md"
        ]
        qr_path = next((p for p in qr_paths if p.exists()), None)
        artifacts['quality_report'] = {'exists': qr_path is not None, 'path': str(qr_path) if qr_path else 'QUALITY_REPORT.md'}
    
    # Phase 7 產出（RISK_REGISTER.md）
    if prev_phase >= 7:
        rr_paths = [
            repo_path / "07-risk" / "RISK_REGISTER.md",
            repo_path / "RISK_REGISTER.md"
        ]
        rr_path = next((p for p in rr_paths if p.exists()), None)
        artifacts['risk_register'] = {'exists': rr_path is not None, 'path': str(rr_path) if rr_path else 'RISK_REGISTER.md'}
    
    # Phase 8 產出（CONFIG_RECORDS.md, requirements.lock）
    if prev_phase >= 8:
        cr_paths = [
            repo_path / "08-config" / "CONFIG_RECORDS.md",
            repo_path / "CONFIG_RECORDS.md"
        ]
        cr_path = next((p for p in cr_paths if p.exists()), None)
        artifacts['config_records'] = {'exists': cr_path is not None, 'path': str(cr_path) if cr_path else 'CONFIG_RECORDS.md'}
        
        rl_path = repo_path / "requirements.lock"
        artifacts['requirements_lock'] = {'exists': rl_path.exists(), 'path': 'requirements.lock'}
    
    return artifacts


def get_artifacts_summary(phase: int, repo_path: Path) -> str:
    """
    產生 Phase artifacts 的摘要文字（用於 Plan）
    """
    if phase == 1:
        return "> Phase 1 是首個 Phase，無上階段產出需承接。直接讀取 TASK_INITIALIZATION_PROMPT.md。"
    
    artifacts = parse_phase_artifacts(phase, repo_path)
    prev_phase = phase - 1
    
    lines = [f"> 上階段（Phase {prev_phase}）產出摘要："]
    lines.append("")
    lines.append("| 產出 | 狀態 | 路徑 |")
    lines.append("|------|:-----:|------|")
    
    summary_map = {
        'tip': ('任務初始化', 'TASK_INITIALIZATION_PROMPT.md'),
        'srs': ('需求規格', 'SRS.md'),
        'sad': ('系統架構', 'SAD.md'),
        'adr': ('架構決策', 'ADR.md'),
        'app': ('代碼實作', 'app/'),
        'test_results': ('測試結果', 'TEST_RESULTS.md'),
        'baseline': ('系統基線', 'BASELINE.md'),
        'quality_report': ('品質報告', 'QUALITY_REPORT.md'),
        'risk_register': ('風險註冊', 'RISK_REGISTER.md'),
        'config_records': ('配置記錄', 'CONFIG_RECORDS.md'),
        'requirements_lock': ('依賴鎖定', 'requirements.lock'),
    }
    
    for key, (name, default_path) in summary_map.items():
        if key in artifacts:
            exists = artifacts[key].get('exists', False)
            status = "✅" if exists else "❌"
            path = artifacts[key].get('path', default_path)
            
            # Add extra info for some artifacts
            extra = ""
            if key == 'srs' and exists:
                fr = artifacts[key].get('fr_count', 0)
                nfr = artifacts[key].get('nfr_count', 0)
                extra = f" ({fr} FR, {nfr} NFR)"
            elif key == 'sad' and exists:
                mod = artifacts[key].get('module_count', 0)
                extra = f" ({mod} modules)"
            elif key == 'app' and exists:
                cnt = artifacts[key].get('file_count', 0)
                extra = f" ({cnt} files)"
            
            lines.append(f"| {status} {name} | {status} | `{path}`{extra} |")
    
    lines.append("")
    lines.append("> ⚠️ 請在執行前確認上階段產出存在且完整。")
    
    return "\n".join(lines)
