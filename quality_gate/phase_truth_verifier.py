#!/usr/bin/env python3
"""
Phase Truth Verifier
====================
驗證某個 Phase 是否真的通過了。

輸出：
- 自動檢查的分數
- 需要手動確認的項目清單

使用方法:
    from quality_gate.phase_truth_verifier import PhaseTruthVerifier

    verifier = PhaseTruthVerifier("/path/to/project", 3)
    result = verifier.verify()
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


class PhaseTruthVerifier:
    """Phase 真相驗證器"""

    # 權重配置
    WEIGHTS = {
        "framework_block": 0.35,      # FrameworkEnforcer BLOCK
        "session_log": 0.25,           # Sessions_spawn.log
        "pytest_pass": 0.25,          # pytest 實際通過
        "coverage": 0.15,             # 覆蓋率達標
    }

    def __init__(self, project_root: str, phase: int):
        self.project_root = Path(project_root)
        self.phase = phase
        self.results = {}

    def check_framework_block(self) -> Tuple[bool, float, str]:
        """檢查 FrameworkEnforcer BLOCK"""
        try:
            # Add enforcement to path if needed
            enforcement_path = self.project_root / "enforcement"
            if enforcement_path.exists():
                import sys
                if str(enforcement_path) not in sys.path:
                    sys.path.insert(0, str(self.project_root))

            from enforcement.framework_enforcer import FrameworkEnforcer
            enforcer = FrameworkEnforcer(str(self.project_root))
            result = enforcer.run(level="BLOCK")

            passed = result.passed
            score = 100.0 if passed else 0.0
            details = f"{len(result.block_checks)} 項檢查, {len(result.violations)} 項違規"

            return passed, score, details
        except ImportError as e:
            return False, 0.0, f"無法導入 FrameworkEnforcer: {e}"
        except Exception as e:
            return False, 0.0, f"Error: {e}"

    def check_session_log(self) -> Tuple[bool, float, str]:
        """檢查 Sessions_spawn.log"""
        log_file = self.project_root / "sessions_spawn.log"

        if not log_file.exists():
            return False, 0.0, "sessions_spawn.log 不存在"

        try:
            content = log_file.read_text()
            lines = [l for l in content.strip().split("\n") if l]

            # 檢查是否有 A/B 兩個不同的 role
            roles = set()
            sessions = set()
            for line in lines:
                try:
                    entry = json.loads(line)
                    roles.add(entry.get("role", ""))
                    sessions.add(entry.get("session_id", ""))
                except:
                    pass

            has_ab = len(roles) >= 2
            has_sessions = len(sessions) >= 2

            score = 100.0 if has_ab and has_sessions else 50.0 if has_sessions else 0.0
            details = f"{len(lines)} 筆記錄, {len(roles)} 個角色, {len(sessions)} 個 session"

            return has_ab and has_sessions, score, details
        except Exception as e:
            return False, 0.0, f"Error: {e}"

    def check_pytest(self) -> Tuple[bool, float, str]:
        """檢查 pytest 實際通過"""
        try:
            result = subprocess.run(
                ["pytest", "--tb=no", "-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            passed = result.returncode == 0
            score = 100.0 if passed else 0.0
            details = "pytest 全部通過" if passed else "pytest 有失敗"

            return passed, score, details
        except subprocess.TimeoutExpired:
            return False, 0.0, "pytest 執行超時"
        except FileNotFoundError:
            return False, 0.0, "pytest 未找到"
        except Exception as e:
            return False, 0.0, f"Error: {e}"

    def check_coverage(self) -> Tuple[bool, float, str]:
        """檢查覆蓋率"""
        threshold = 70

        try:
            result = subprocess.run(
                ["pytest", "--cov=.","--cov-report=term-missing","--tb=no","-q"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # 嘗試從輸出解析覆蓋率
            output = result.stdout + result.stderr

            coverage_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
            if coverage_match:
                coverage = int(coverage_match.group(1))
            else:
                coverage_match = re.search(r" coverage: (\d+)%", output)
                coverage = int(coverage_match.group(1)) if coverage_match else 0

            passed = coverage >= threshold
            score = min(100.0, coverage) if passed else coverage
            details = f"覆蓋率 {coverage}% (門檻 {threshold}%)"

            return passed, score, details
        except Exception as e:
            return False, 0.0, f"Error: {e}"

    def get_manual_checklist(self) -> List[Dict]:
        """生成需要手動確認的項目"""

        phase_artifacts = {
            1: ["SRS.md", "SPEC_TRACKING.md", "TRACEABILITY_MATRIX.md"],
            2: ["SAD.md", "ARCHITECTURE.md"],
            3: ["03-implementation/src/", "03-implementation/tests/"],
            4: ["TEST_PLAN.md", "TEST_RESULTS.md"],
            5: ["BASELINE.md", "VERIFICATION_REPORT.md"],
            6: ["QUALITY_REPORT.md"],
            7: ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
            8: ["CONFIG_RECORDS.md"],
        }

        checklist = []

        # 根據 Phase 添加需要確認的項目
        if self.phase in phase_artifacts:
            for artifact in phase_artifacts[self.phase]:
                path = self.project_root / artifact
                exists = path.exists()
                checklist.append({
                    "item": artifact,
                    "status": "✅ 存在" if exists else "❌ 缺失",
                    "action": f"隨機選 1 處，確認內容不是空洞的 template"
                })

        # 通用檢查
        checklist.extend([
            {
                "item": "DEVELOPMENT_LOG.md",
                "status": "✅ 存在" if (self.project_root / "DEVELOPMENT_LOG.md").exists() else "❌ 缺失",
                "action": "查看是否有實際命令輸出（不是截圖，是文字）"
            },
            {
                "item": "sessions_spawn.log",
                "status": "✅ 存在" if (self.project_root / "sessions_spawn.log").exists() else "❌ 缺失",
                "action": "隨機選 1 筆記錄，確認 task 描述合理"
            },
        ])

        return checklist

    def verify(self) -> Dict:
        """執行完整驗證"""

        print("=" * 60)
        print(f"Phase {self.phase} 真相驗證")
        print("=" * 60)
        print()

        # 執行各項檢查
        checks = [
            ("FrameworkEnforcer BLOCK", self.check_framework_block),
            ("Sessions_spawn.log", self.check_session_log),
            ("pytest 實際通過", self.check_pytest),
            ("測試覆蓋率達標", self.check_coverage),
        ]

        total_score = 0.0
        results = []

        for name, check_func in checks:
            passed, score, details = check_func()
            # Use a simple key extraction for weights
            key = name.split()[0].lower()
            if "frameworkenforcer" in key:
                weight = 0.35
            elif "sessions" in key:
                weight = 0.25
            elif "pytest" in key:
                weight = 0.25
            elif "coverage" in key or "覆蓋率" in key:
                weight = 0.15
            else:
                weight = 0.25

            weighted_score = score * weight
            total_score += weighted_score

            status = "✅" if passed else "❌"
            results.append({
                "name": name,
                "passed": passed,
                "score": score,
                "details": details,
                "weight": weight,
            })

            print(f"{status} {name:<30} {details}")

        print()
        print("=" * 60)
        verdict = "✅ 可能真實" if total_score >= 70 else "❌ 高度可疑"
        print(f"總分：{total_score:.0f}% - {verdict}")
        print("=" * 60)
        print()

        # 輸出需要手動確認的項目
        print("【需要 Johnny 手動確認】")
        print()

        checklist = self.get_manual_checklist()
        for i, item in enumerate(checklist, 1):
            print(f"{i}. [{item['item']}]")
            print(f"   狀態：{item['status']}")
            print(f"   → {item['action']}")
            print()

        return {
            "phase": self.phase,
            "total_score": total_score,
            "passed": total_score >= 70,
            "checks": results,
            "checklist": checklist,
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase Truth Verifier")
    parser.add_argument("--phase", type=int, required=True, choices=range(1, 9),
                        help="Phase number (1-8)")
    parser.add_argument("--project", default=".", help="Project root path")

    args = parser.parse_args()

    verifier = PhaseTruthVerifier(args.project, args.phase)
    result = verifier.verify()

    sys.exit(0 if result["passed"] else 1)
