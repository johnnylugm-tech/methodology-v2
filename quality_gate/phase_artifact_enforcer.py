#!/usr/bin/env python3
"""
Phase Artifact Enforcer - 階段產物強制執行器

功能：
- 驗證每個 Phase 的 Agent 引用上一個 Phase 的產物
- 確保階段間的傳遞是「驗證過」的
- 阻擋未引用上階段產物的執行
"""

import os
import re
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from pathlib import Path


class Phase(Enum):
    """專案階段（ASPICE 8 階段 + Constitution）"""
    CONSTITUTION = "1-constitution"      # Constitution
    SPECIFY = "2-specify"                # Phase 1: SRS
    PLAN = "3-plan"                      # Phase 2: SAD
    IMPLEMENT = "4-implement"            # Phase 3: Implementation
    VERIFY = "5-verify"                  # Phase 4: Test Plan
    SYSTEM_TEST = "6-system-test"        # Phase 5: Baseline
    QUALITY = "7-quality"                # Phase 6: Quality Report
    RISK = "8-risk"                      # Phase 7: Risk Assessment
    CONFIG = "9-config"                  # Phase 8: Config Records


@dataclass
class PhaseArtifact:
    """階段產物"""
    phase: Phase
    files: List[str]  # 產物檔案列表
    signature: str    # SHA256 signature
    created_at: str
    validated: bool = False


@dataclass
class ArtifactCheckResult:
    """產物檢查結果"""
    phase: Phase
    passed: bool
    referenced_artifacts: List[str] = field(default_factory=list)
    missing_references: List[str] = field(default_factory=list)
    message: str = ""


class PhaseArtifactRegistry:
    """
    階段產物註冊表
    
    記錄每個 Phase 的產物，並驗證下階段是否引用
    """
    
    # Phase 產物對應表（ASPICE 8 階段 + Constitution）
    # 注意：支援兩種命名慣例
    #   - 傳統: 01-specify/, 02-plan/, etc.
    #   - 專案: 01-requirements/, 02-architecture/, etc.
    PHASE_ARTIFACTS = {
        Phase.CONSTITUTION: {
            "required": ["CONSTITUTION.md", "constitution/"],
            "output_dir": "constitution",
            "alt_dirs": ["constitution"],
        },
        Phase.SPECIFY: {  # Phase 1
            "required": ["SRS.md", "SPEC_TRACKING.md", "TRACEABILITY_MATRIX.md"],
            "output_dir": "01-requirements",
            "alt_dirs": ["01-specify", "01-requirements", "requirements"],
            "depends_on": [Phase.CONSTITUTION],
        },
        Phase.PLAN: {  # Phase 2
            "required": ["SAD.md", "ADR.md", "ARCHITECTURE.md"],
            "output_dir": "02-architecture",
            "alt_dirs": ["02-plan", "02-architecture", "architecture", "plan"],
            "depends_on": [Phase.SPECIFY],
        },
        Phase.IMPLEMENT: {  # Phase 3
            "required": ["src/", "tests/"],
            "output_dir": "03-implementation",
            "alt_dirs": ["03-implement", "03-implementation", "implementation", "src", "app"],
            "depends_on": [Phase.PLAN],
        },
        Phase.VERIFY: {  # Phase 4
            "required": ["TEST_PLAN.md", "TEST_RESULTS.md"],
            "output_dir": "04-testing",
            "alt_dirs": ["04-verify", "04-testing", "testing", "verify"],
            "depends_on": [Phase.IMPLEMENT],
        },
        Phase.SYSTEM_TEST: {  # Phase 5
            "required": ["TEST_RESULTS.md", "BASELINE.md", "VERIFICATION_REPORT.md"],
            "output_dir": "05-verify",
            "alt_dirs": ["05-system-test", "05-verify", "verify"],
            "depends_on": [Phase.VERIFY],
        },
        Phase.QUALITY: {  # Phase 6
            "required": ["QUALITY_REPORT.md", "MONITORING_PLAN.md"],
            "output_dir": "06-quality",
            "alt_dirs": ["06-quality", "quality"],
            "depends_on": [Phase.SYSTEM_TEST],
        },
        Phase.RISK: {  # Phase 7
            "required": ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
            "output_dir": "07-risk",
            "alt_dirs": ["07-risk", "risk"],
            "depends_on": [Phase.QUALITY],
        },
        Phase.CONFIG: {  # Phase 8
            "required": ["CONFIG_RECORDS.md", "RELEASE_CHECKLIST.md"],
            "output_dir": "08-config",
            "alt_dirs": ["08-config", "08-configuration", "config", "configuration"],
            "depends_on": [Phase.RISK],
        },
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts: Dict[Phase, PhaseArtifact] = {}
        self._scan_existing_artifacts()
    
    def _scan_existing_artifacts(self):
        """掃描現有產物（支援多個可能的目錄名）"""
        for phase in Phase:
            config = self.PHASE_ARTIFACTS.get(phase, {})
            output_dir = config.get("output_dir", "")
            alt_dirs = config.get("alt_dirs", [])
            
            # 嘗試多個可能的目錄名
            found_dir = None
            for dir_name in [output_dir] + alt_dirs:
                if dir_name and (self.project_root / dir_name).exists():
                    found_dir = dir_name
                    break
            
            if found_dir:
                files = list((self.project_root / found_dir).rglob("*"))
                file_paths = [str(f.relative_to(self.project_root)) for f in files if f.is_file()]
                
                # 計算 signature
                signature = self._compute_signature(file_paths)
                
                self.artifacts[phase] = PhaseArtifact(
                    phase=phase,
                    files=file_paths,
                    signature=signature,
                    created_at="",
                    validated=True
                )
    
    def _compute_signature(self, files: List[str]) -> str:
        """計算檔案列表的 SHA256 signature"""
        content = "|".join(sorted(files))
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_required_artifacts(self, phase: Phase) -> List[str]:
        """取得某個 Phase 需要的前置產物"""
        config = self.PHASE_ARTIFACTS.get(phase, {})
        depends_on = config.get("depends_on", [])
        
        required = []
        for prev_phase in depends_on:
            prev_config = self.PHASE_ARTIFACTS.get(prev_phase, {})
            required.extend(prev_config.get("required", []))
        
        return required
    
    def verify_phase_link(self, prev_phase: Phase, current_phase: Phase) -> ArtifactCheckResult:
        """
        驗證 current_phase 是否正確引用 prev_phase 的產物
        
        檢查方式：
        1. 確認 prev_phase 的產物目錄存在
        2. 掃描 current_phase 的相關檔案，檢查是否有引用 prev_phase 的關鍵字
        """
        prev_config = self.PHASE_ARTIFACTS.get(prev_phase, {})
        curr_config = self.PHASE_ARTIFACTS.get(current_phase, {})
        
        prev_output_dir = prev_config.get("output_dir", "")
        curr_output_dir = curr_config.get("output_dir", "")
        prev_alt_dirs = prev_config.get("alt_dirs", [])
        curr_alt_dirs = curr_config.get("alt_dirs", [])
        
        # Find existing prev_phase directory (check output_dir + alt_dirs)
        prev_path = None
        for dir_name in [prev_output_dir] + prev_alt_dirs:
            if dir_name and (self.project_root / dir_name).exists():
                prev_path = self.project_root / dir_name
                break
        
        # Find existing curr_phase directory (check output_dir + alt_dirs)
        curr_path = None
        for dir_name in [curr_output_dir] + curr_alt_dirs:
            if dir_name and (self.project_root / dir_name).exists():
                curr_path = self.project_root / dir_name
                break
        
        # 檢查 prev_phase 的產物是否存在
        if prev_path is None or not prev_path.exists():
            return ArtifactCheckResult(
                phase=current_phase,
                passed=False,
                message=f"Previous phase artifact directory not found: {prev_output_dir} (tried alt_dirs: {prev_alt_dirs})"
            )
        
        # 收集 prev_phase 的所有檔案
        prev_files = []
        if prev_path.exists():
            prev_files = [str(f.relative_to(self.project_root)) for f in prev_path.rglob("*") if f.is_file()]
        
        # 收集 current_phase 的所有檔案內容
        curr_content = ""
        if curr_path and curr_path.exists():
            for f in curr_path.rglob("*"):
                if f.is_file():
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        curr_content += content + "\n"
                    except Exception:
                        pass
        
        # 檢查 current_phase 是否引用了 prev_phase 的關鍵字
        referenced = []
        missing_refs = []
        
        # 檢查 phase 名稱/目錄名稱是否出現在 current_phase 的內容中
        prev_phase_markers = [
            prev_phase.value,
            prev_output_dir,
            prev_output_dir.replace("/", "").replace("-", "_"),
        ]
        
        for marker in prev_phase_markers:
            if marker in curr_content or marker.lower() in curr_content.lower():
                referenced.append(marker)
        
        # 檢查是否有引用 prev_phase 的檔案
        for pf in prev_files:
            pf_name = Path(pf).name
            if pf_name in curr_content:
                referenced.append(pf)
        
        # 檢查通用引用模式
        reference_patterns = [
            r"based on",
            r"derived from",
            r"according to",
            r"based upon",
            r"continuation of",
            r"extends",
            r"following the",
            r"per the",
            r"as defined in",
        ]
        
        for pattern in reference_patterns:
            if re.search(pattern, curr_content, re.IGNORECASE):
                referenced.append(f"pattern:{pattern}")
        
        passed = len(referenced) > 0 or len(prev_files) == 0
        
        return ArtifactCheckResult(
            phase=current_phase,
            passed=passed,
            referenced_artifacts=referenced,
            missing_references=missing_refs if not passed else [],
            message=f"Phase link verification: {'passed' if passed else 'failed'}"
        )
    
    def check_phase_dependencies(self, phase: Phase) -> ArtifactCheckResult:
        """檢查某個 Phase 的依賴是否滿足"""
        required_artifacts = self.get_required_artifacts(phase)
        
        missing = []
        for artifact_pattern in required_artifacts:
            found = False
            for existing_phase, artifact in self.artifacts.items():
                for f in artifact.files:
                    if re.search(artifact_pattern.replace("*", ".*"), f):
                        found = True
                        break
                if found:
                    break
            if not found:
                missing.append(artifact_pattern)
        
        return ArtifactCheckResult(
            phase=phase,
            passed=len(missing) == 0,
            missing_references=missing,
            message=f"Phase {phase.value} requires: {required_artifacts}"
        )


class PhaseArtifactEnforcer:
    """
    階段產物強制執行器
    
    使用方式：
    
    ```python
    enforcer = PhaseArtifactEnforcer(project_root=".")
    
    # 檢查是否可以進入下一個 Phase
    result = enforcer.can_proceed_to("3-plan")
    
    if not result.passed:
        print(f"Blocked: {result.missing_references}")
        # 阻擋執行
    ```
    """
    
    def __init__(self, project_root: str = "."):
        self.registry = PhaseArtifactRegistry(project_root)
    
    def can_proceed_to(self, phase_name: str) -> ArtifactCheckResult:
        """檢查是否可以進入指定 Phase"""
        try:
            phase = Phase(phase_name)
        except ValueError:
            return ArtifactCheckResult(
                phase=None,
                passed=False,
                message=f"Unknown phase: {phase_name}"
            )
        
        return self.registry.check_phase_dependencies(phase)
    
    def validate_artifact_reference(self, phase_name: str, content: str) -> bool:
        """
        驗證執行 content 是否引用了上階段產物
        
        檢查關鍵字：
        - Phase 名稱 (e.g., "2-specify", "constitution")
        - 檔案路徑
        - 關鍵詞 (e.g., "based on", "derived from", "according to")
        """
        try:
            phase = Phase(phase_name)
        except ValueError:
            return True  # 未知 Phase 跳過
        
        required_artifacts = self.registry.get_required_artifacts(phase)
        
        # 檢查是否有引用
        for artifact in required_artifacts:
            # 移除正則特殊字符
            pattern = artifact.replace("*", "").replace("/", "[/\\\\]")
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # 檢查通用引用模式
        reference_patterns = [
            r"based on",
            r"derived from",
            r"according to",
            r"based upon",
            r"continuation of",
        ]
        
        for pattern in reference_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return len(required_artifacts) == 0  # 沒有依賴則通過
    
    def enforce(self, phase_name: str, agent_prompt: str = "") -> ArtifactCheckResult:
        """
        強制執行檢查
        
        1. 檢查上階段產物是否存在
        2. 檢查 Agent prompt 是否引用上階段產物
        """
        result = self.can_proceed_to(phase_name)
        
        if not result.passed:
            result.message = f"🚫 BLOCKED: Missing required artifacts from previous phases:\n"
            result.message += "\n".join(f"  - {m}" for m in result.missing_references)
            return result
        
        # 如果有 Agent prompt，檢查是否引用
        if agent_prompt and not self.validate_artifact_reference(phase_name, agent_prompt):
            result.passed = False
            result.message = f"⚠️ WARNING: Agent prompt for {phase_name} does not reference previous phase artifacts"
            return result
        
        result.message = f"✅ Phase {phase_name} artifact check passed"
        return result

    def enforce_all(self) -> dict:
        """
        執行所有 Phase 的產物檢查（僅檢查到最後一個存在的 Phase）

        Returns:
            dict: {
                "passed": bool,  # 所有已存在 Phase 都通過為 True
                "results": {
                    phase_name: {
                        "passed": bool,
                        "message": str,
                        "missing_references": list
                    }
                }
            }
        """
        results = {}
        all_passed = True

        # Re-scan artifacts to pick up any newly created directories
        self.registry._scan_existing_artifacts()

        # Find the highest existing phase (check both primary and alt dirs)
        existing_phases = []
        for phase in Phase:
            config = self.registry.PHASE_ARTIFACTS.get(phase, {})
            output_dir = config.get("output_dir", "")
            alt_dirs = config.get("alt_dirs", [])
            
            found = False
            for dir_name in [output_dir] + alt_dirs:
                if dir_name and (self.registry.project_root / dir_name).exists():
                    found = True
                    break
            
            if found:
                existing_phases.append(phase)

        # Only check up to the highest existing phase
        phases_to_check = existing_phases if existing_phases else list(Phase)

        for phase in phases_to_check:
            result = self.can_proceed_to(phase.value)
            results[phase.name.lower()] = {
                "passed": result.passed,
                "message": result.message,
                "missing_references": result.missing_references
            }
            if not result.passed:
                all_passed = False

        return {
            "passed": all_passed,
            "results": results
        }


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase Artifact Enforcer")
    parser.add_argument("--phase", help="Phase to check (e.g., 3-plan)")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    enforcer = PhaseArtifactEnforcer(args.project_root)
    
    if args.phase:
        result = enforcer.enforce(args.phase)
        
        if args.json:
            print(json.dumps({
                "phase": result.phase.value if result.phase else None,
                "passed": result.passed,
                "missing_references": result.missing_references,
                "message": result.message,
            }))
        else:
            print(result.message)
            if not result.passed:
                print("Missing:", result.missing_references)
                exit(1)
    else:
        # 檢查所有 Phase
        print("📋 Phase Artifact Check Report")
        print("=" * 50)
        
        all_passed = True
        for phase in Phase:
            result = enforcer.can_proceed_to(phase.value)
            status = "✅" if result.passed else "❌"
            print(f"{status} {phase.value}: {result.message}")
            if not result.passed:
                all_passed = False
        
        exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()