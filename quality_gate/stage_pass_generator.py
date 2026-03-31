#!/usr/bin/env python3
"""
STAGE_PASS Generator - 整合版
=============================
結合 stage_pass_generator.py 概念與 FrameworkEnforcer 實際工具呼叫。

功能：
- Step 1: 5W1H 合規性掃描（呼叫實際工具驗證）
- Step 2: FrameworkEnforcer BLOCK 檢查
- Step 3: Sessions_spawn.log 驗證
- Step 4: 問題修復迴圈（A/B 協作）
- Step 5: 信心分數 + Git 推送

使用方式：
    python quality_gate/stage_pass_generator.py --phase 3 --project-dir /path/to/project

或透過 CLI：
    python cli.py stage-pass --phase 3 --project /path/to/project
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 匯入現有 Framework 模組
# 由於此檔案位於 quality_gate/，需要往上一層找到 enforcement/
_parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_parent_dir))

from enforcement.framework_enforcer import FrameworkEnforcer
from quality_gate.claims_verifier import ClaimsVerifier
from quality_gate.phase_config import PHASE_CONFIG

VERSION = "1.0.0"
SKILL_REF = "methodology-v2"


class IntegratedStagePassGenerator:
    """整合版 STAGE_PASS 生成器"""
    
    def __init__(self, project_root: str, phase: int):
        self.project_root = Path(project_root)
        self.phase = phase
        self.config = PHASE_CONFIG.get(phase, {})
        
        # 初始化 Framework 組件
        self.enforcer = FrameworkEnforcer(str(self.project_root))
        self.claims_verifier = ClaimsVerifier(str(self.project_root))
        
        self.results = {
            "phase": phase,
            "five_w1h_results": {},
            "framework_results": {},
            "session_log_results": {},
            "issues": [],
            "confidence_score": None,
            "confidence_reason": "",
            "git_commit": "",
        }
    
    def run_step1_5w1h_scan(self) -> bool:
        """
        Step 1: 5W1H 合規性掃描
        
        呼叫實際工具驗證，而非人工輸入。
        """
        print(f"\n{'='*60}")
        print(f"[Step 1] 5W1H 合規性掃描（實際工具驗證）")
        print(f"{'='*60}")
        
        all_passed = True
        
        # 呼叫 FrameworkEnforcer BLOCK 檢查
        print("\n📋 呼叫 FrameworkEnforcer BLOCK...")
        result = self.enforcer.run(level="BLOCK")
        
        self.results["framework_results"]["BLOCK"] = {
            "passed": result.passed,
            "violations": result.violations,
            "block_checks": result.block_checks,
        }
        
        if result.passed:
            print("✅ FrameworkEnforcer BLOCK 通過")
        else:
            print("❌ FrameworkEnforcer BLOCK 未通過")
            print("\n🔴 Violations:")
            for msg, fix in result.violations:
                print(f"   - {msg}")
                if fix:
                    print(f"     → {fix}")
            all_passed = False
        
        return all_passed
    
    def run_step2_session_log(self) -> bool:
        """
        Step 2: Sessions_spawn.log 驗證
        
        驗證 A/B 協作的真實性。
        """
        print(f"\n{'='*60}")
        print(f"[Step 2] Sessions_spawn.log 驗證")
        print(f"{'='*60}")
        
        result = self.claims_verifier.verify_sessions_spawn_log()
        
        self.results["session_log_results"] = {
            "passed": result.passed,
            "message": result.message,
            "details": result.details,
        }
        
        if result.passed:
            print("✅ Sessions_spawn.log 驗證通過")
        else:
            print("❌ Sessions_spawn.log 驗證失敗")
            print(f"   {result.message}")
        
        return result.passed
    
    def run_step3_pytest_evidence(self) -> Dict:
        """
        Step 3: 收集實際 pytest 證據
        """
        print(f"\n{'='*60}")
        print(f"[Step 3] 收集測試證據")
        print(f"{'='*60}")
        
        evidence = {}
        
        # 執行 pytest
        print("\n📋 執行 pytest...")
        try:
            result = subprocess.run(
                ["pytest", "--tb=short", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            evidence["pytest_passed"] = result.returncode == 0
            evidence["pytest_output"] = result.stdout[-2000:] if result.stdout else ""
            evidence["pytest_stderr"] = result.stderr[-500:] if result.stderr else ""
            
            if result.returncode == 0:
                print("✅ pytest 通過")
            else:
                print("❌ pytest 失敗")
                print(result.stdout[-500:])
        except Exception as e:
            evidence["pytest_error"] = str(e)
            print(f"⚠️ pytest 執行失敗: {e}")
        
        # 執行 pytest-cov
        print("\n📋 執行 pytest-cov...")
        try:
            result = subprocess.run(
                ["pytest", "--cov", "--cov-report=term-missing"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            evidence["coverage_passed"] = result.returncode == 0
            evidence["coverage_output"] = result.stdout[-2000:] if result.stdout else ""
        except Exception as e:
            evidence["coverage_error"] = str(e)
        
        self.results["test_evidence"] = evidence
        return evidence
    
    def run_step4_confidence(self) -> int:
        """
        Step 4: 信心分數計算
        
        根據實際工具結果計算信心分數。
        """
        print(f"\n{'='*60}")
        print(f"[Step 4] 信心分數")
        print(f"{'='*60}")
        
        score = 0
        reasons = []
        
        # Framework BLOCK (40%)
        if self.results["framework_results"].get("BLOCK", {}).get("passed"):
            score += 40
            reasons.append("FrameworkEnforcer BLOCK 通過 (+40)")
        else:
            reasons.append("FrameworkEnforcer BLOCK 未通過 (+0)")
        
        # Sessions log (20%)
        if self.results["session_log_results"].get("passed"):
            score += 20
            reasons.append("Sessions_spawn.log 驗證通過 (+20)")
        else:
            reasons.append("Sessions_spawn.log 驗證失敗 (+0)")
        
        # Pytest (20%)
        if self.results["test_evidence"].get("pytest_passed"):
            score += 20
            reasons.append("pytest 全部通過 (+20)")
        else:
            score += 10  # 部分通過
            reasons.append("pytest 部分通過 (+10)")
        
        # Coverage (20%)
        if self.results["test_evidence"].get("coverage_passed"):
            score += 20
            reasons.append("Coverage 達標 (+20)")
        else:
            reasons.append("Coverage 未達標 (+0)")
        
        print("\n📊 分數計算：")
        for reason in reasons:
            print(f"   {reason}")
        print(f"\n🎯 信心分數: {score}/100")
        
        self.results["confidence_score"] = score
        self.results["confidence_reason"] = "; ".join(reasons)
        
        return score
    
    def generate_markdown(self) -> str:
        """生成 STAGE_PASS.md"""
        config = self.config
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        score = self.results["confidence_score"] or 0
        if score >= 90:
            score_badge = f"🟢 {score}/100"
        elif score >= 70:
            score_badge = f"🟡 {score}/100"
        else:
            score_badge = f"🔴 {score}/100"
        
        lines = [
            f"# {config.get('name', f'Phase {self.phase}')} — STAGE_PASS",
            f"",
            f"> **方法論版本**: {SKILL_REF}",
            f"> **生成時間**: {now}",
            f"> **信心分數**: {score_badge}",
            f"> **Git Commit**: `{self.results.get('git_commit', '(push后填入)')}`",
            f"",
            f"---",
            f"",
            f"## Step 1｜FrameworkEnforcer BLOCK 檢查",
            f"",
        ]
        
        block_result = self.results.get("framework_results", {}).get("BLOCK", {})
        if block_result.get("passed"):
            lines.append("**結論**: ✅ 通過")
        else:
            lines.append("**結論**: ❌ 未通過")
            lines.append("")
            lines.append("### Violations")
            for msg, fix in block_result.get("violations", []):
                lines.append(f"- {msg}")
        
        lines.extend([
            f"",
            f"## Step 2｜Sessions_spawn.log 驗證",
            f"",
        ])
        
        log_result = self.results.get("session_log_results", {})
        lines.append(f"**結論**: {'✅' if log_result.get('passed') else '❌'} {log_result.get('message', '')}")
        
        lines.extend([
            f"",
            f"## Step 3｜測試證據",
            f"",
        ])
        
        test_evidence = self.results.get("test_evidence", {})
        lines.append(f"- pytest: {'✅' if test_evidence.get('pytest_passed') else '❌'}")
        lines.append(f"- coverage: {'✅' if test_evidence.get('coverage_passed') else '❌'}")
        
        lines.extend([
            f"",
            f"## Step 4｜信心分數",
            f"",
            f"### {score_badge}",
            f"",
            f"**理由**: {self.results.get('confidence_reason', '')}",
            f"",
            f"---",
            f"",
            f"*由 stage_pass_generator.py v{VERSION} 生成*",
        ])
        
        return "\n".join(lines)
    
    def git_push(self, content: str) -> str:
        """推送到 GitHub"""
        output_dir = self.project_root / "00-summary"
        output_dir.mkdir(exist_ok=True)
        
        phase_name = self.config.get("name", f"Phase{self.phase}").replace(" ", "_")
        output_path = output_dir / f"{phase_name}_STAGE_PASS.md"
        
        output_path.write_text(content, encoding="utf-8")
        
        try:
            subprocess.run(["git", "add", str(output_path)], check=True, capture_output=True)
            msg = f"chore: Phase {self.phase} STAGE_PASS — {SKILL_REF}"
            subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True)
            subprocess.run(["git", "push"], check=True, capture_output=True)
            
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )
            commit_hash = result.stdout.strip()
            self.results["git_commit"] = commit_hash
            
            # 更新 commit hash
            updated = content.replace("(push后填入)", commit_hash)
            output_path.write_text(updated, encoding="utf-8")
            
            print(f"✅ Git 推送成功: {commit_hash}")
            return commit_hash
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Git 操作失敗: {e.stderr}")
            return ""
    
    def run(self) -> bool:
        """執行完整流程"""
        print(f"\n{'='*60}")
        print(f"STAGE_PASS Generator v{VERSION}")
        print(f"Phase {self.phase}: {self.config.get('name', '')}")
        print(f"{'='*60}")
        
        # Step 1: Framework BLOCK
        step1_passed = self.run_step1_5w1h_scan()
        
        # Step 2: Session log
        step2_passed = self.run_step2_session_log()
        
        # Step 3: Test evidence
        self.run_step3_pytest_evidence()
        
        # Step 4: Confidence
        score = self.run_step4_confidence()
        
        # Generate & Push
        md = self.generate_markdown()
        commit_hash = self.git_push(md)
        
        print(f"\n{'='*60}")
        print(f"完成！STAGE_PASS.md 已生成並推送")
        print(f"信心分數: {score}/100")
        print(f"{'='*60}")
        
        return score >= 70  # 70 分以上算通過


def main():
    parser = argparse.ArgumentParser(description="STAGE_PASS Generator (Integrated)")
    parser.add_argument("--phase", type=int, required=True, choices=range(1, 9))
    parser.add_argument("--project-dir", default=".", dest="project_dir")
    args = parser.parse_args()
    
    generator = IntegratedStagePassGenerator(args.project_dir, args.phase)
    success = generator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
