#!/usr/bin/env python3
"""
Folder Structure Checker
========================
檢查 Phase 完成後的資料夾結構與產出物

使用方式：
    from quality_gate.folder_structure_checker import FolderStructureChecker
    
    checker = FolderStructureChecker("/path/to/project")
    result = checker.run(phase=1)
    
    print(f"Passed: {result['passed']}")
    print(f"Violations: {result['violations']}")

內容結構檢查（擴展）：
    from quality_gate.folder_structure_checker import FolderStructureChecker
    
    checker = FolderStructureChecker("/path/to/project", strict_mode=True)
    result = checker.run(phase=1)
    
    # 檢查 content_check 欄位
    print(f"Content Check: {result['content_check']}")
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict


# ===== Phase 1-8 內容結構定義 =====
# 每個 Phase 的每個檔案需要包含的章節
# 注意：這些檢查只適用於 SKILL.md 定義的實際交付物
PHASE_CONTENT_STRUCTURES = {
    1: {},  # Phase 1 不需要額外內容結構檢查
    2: {},  # Phase 2 不需要額外內容結構檢查
    3: {},  # Phase 3 內容檢查由代碼審查完成
    4: {},  # Phase 4 內容檢查由 pytest 完成
    5: {},  # Phase 5 內容檢查由 Quality Gate 完成
    6: {},  # Phase 6 內容檢查由 Quality Gate 完成
    7: {},  # Phase 7 內容檢查由 Risk Register 完成
    8: {}   # Phase 8 內容檢查由 Config Records 完成
}


@dataclass
class ContentCheckResult:
    """內容結構檢查結果"""
    passed: bool
    file_path: str
    missing_sections: List[str]
    found_sections: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class FolderCheckResult:
    """資料夾結構檢查結果"""
    passed: bool
    phase: int
    score: float
    missing_dirs: List[str]
    missing_files: List[str]
    content_issues: List[str]
    content_check: List[Dict]  # 新增：內容結構檢查結果
    details: Dict

    def to_dict(self) -> Dict:
        result = asdict(self)
        # 確保 content_check 欄位始終存在
        if 'content_check' not in result:
            result['content_check'] = []
        return result


class FolderStructureChecker:
    """
    檢查 Phase 完成後的資料夾結構與產出物
    
    根據 PDF (All_Phases_Folder_Structure) 定義的預期結構進行檢查
    
    Attributes:
        strict_mode: 若為 True，則啟用內容結構檢查（預設 False）
    """
    
    # Phase 1-4 的預期資料夾結構
    PHASE_STRUCTURES = {
        1: {
            "required_dirs": [
                "01-requirements",
                "00-summary"
            ],
            "required_files": [
                "01-requirements/SRS.md",
                "01-requirements/SPEC_TRACKING.md",
                "01-requirements/TRACEABILITY_MATRIX.md",
                "DEVELOPMENT_LOG.md",
                "00-summary/Phase1_STAGE_PASS.md"
            ],
            "checks": {
                "SRS_exists": "01-requirements/SRS.md",
                "SPEC_TRACKING_exists": "01-requirements/SPEC_TRACKING.md",
                "TRACEABILITY_exists": "01-requirements/TRACEABILITY_MATRIX.md",
                "DEV_LOG_exists": "DEVELOPMENT_LOG.md",
                "STAGE_PASS_exists": "00-summary/Phase1_STAGE_PASS.md",
                "SRS_has_FR": "01-requirements/SRS.md",
                "TRACEABILITY_has_FR": "01-requirements/TRACEABILITY_MATRIX.md"
            }
        },
        2: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "00-summary"
            ],
            "required_files": [
                "02-architecture/SAD.md",
                "TRACEABILITY_MATRIX.md",
                "DEVELOPMENT_LOG.md",
                "00-summary/Phase2_STAGE_PASS.md"
            ],
            "checks": {
                "SAD_exists": "02-architecture/SAD.md",
                "SAD_has_modules": "02-architecture/SAD.md",
                "SAD_has_ADR": "02-architecture/SAD.md",
                "TRACEABILITY_updated": "TRACEABILITY_MATRIX.md",
                "DEV_LOG_has_conflict": "DEVELOPMENT_LOG.md"
            }
        },
        3: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                # Standard path
                "03-implementation/src",
                "03-implementation/tests",
                # Alternative: app/ structure (e.g., tts-kokoro-v613)
                "app",
                "app/processing",
                "tests",
                "00-summary"
            ],
            "required_files": [
                "03-implementation/scripts/spec_logic_checker.py",
                "03-implementation/coverage_report/index.html",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "src_dir_exists": "03-implementation/src",
                "tests_dir_exists": "03-implementation/tests",
                "spec_logic_checker_exists": "03-implementation/scripts/spec_logic_checker.py",
                "coverage_report_exists": "03-implementation/coverage_report/index.html",
                "src_has_py_files": "03-implementation/src",
                "tests_has_test_files": "03-implementation/tests",
                "DEV_LOG_has_review": "DEVELOPMENT_LOG.md",
                # Alternative: app/ structure
                "app_dir_exists": "app",
                "app_has_py_files": "app"
            }
        },
        4: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "03-implementation",
                "04-testing",
                "tests"
            ],
            "required_files": [
                "04-testing/TEST_PLAN.md",
                "04-testing/TEST_RESULTS.md",
                "TRACEABILITY_MATRIX.md",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "TEST_PLAN_exists": "04-testing/TEST_PLAN.md",
                "TEST_RESULTS_exists": "04-testing/TEST_RESULTS.md",
                "TEST_RESULTS_has_pytest": "04-testing/TEST_RESULTS.md",
                "TEST_RESULTS_has_failure_analysis": "04-testing/TEST_RESULTS.md",
                "DEV_LOG_has_AB_review": "DEVELOPMENT_LOG.md"
            }
        },
        5: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "03-implementation",
                "04-testing",
                "05-delivery"
            ],
            "required_files": [
                "05-delivery/QUALITY_REPORT.md",
                "05-delivery/BASELINE.md",
                "05-delivery/DELIVERY_MANIFEST.md",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "QUALITY_REPORT_exists": "05-delivery/QUALITY_REPORT.md",
                "BASELINE_exists": "05-delivery/BASELINE.md",
                "DELIVERY_MANIFEST_exists": "05-delivery/DELIVERY_MANIFEST.md",
                "QUALITY_REPORT_has_summary": "05-delivery/QUALITY_REPORT.md",
                "DELIVERY_MANIFEST_has_artifacts": "05-delivery/DELIVERY_MANIFEST.md"
            }
        },
        6: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "03-implementation",
                "04-testing",
                "05-delivery",
                "06-quality"
            ],
            "required_files": [
                "06-quality/QUALITY_ASSURANCE.md",
                "06-quality/QUALITY_METRICS.md",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "QUALITY_ASSURANCE_exists": "06-quality/QUALITY_ASSURANCE.md",
                "QUALITY_METRICS_exists": "06-quality/QUALITY_METRICS.md",
                "QUALITY_ASSURANCE_has_defects": "06-quality/QUALITY_ASSURANCE.md",
                "QUALITY_METRICS_has_coverage": "06-quality/QUALITY_METRICS.md"
            }
        },
        7: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "03-implementation",
                "04-testing",
                "05-delivery",
                "06-quality",
                "07-risk"
            ],
            "required_files": [
                "07-risk/RISK_ASSESSMENT.md",
                "07-risk/RISK_REGISTER.md",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "RISK_ASSESSMENT_exists": "07-risk/RISK_ASSESSMENT.md",
                "RISK_REGISTER_exists": "07-risk/RISK_REGISTER.md",
                "RISK_ASSESSMENT_has_mitigation": "07-risk/RISK_ASSESSMENT.md",
                "RISK_REGISTER_has_tracking": "07-risk/RISK_REGISTER.md"
            }
        },
        8: {
            "required_dirs": [
                "01-requirements",
                "02-architecture",
                "03-implementation",
                "04-testing",
                "05-delivery",
                "06-quality",
                "07-risk",
                "08-configuration"
            ],
            "required_files": [
                "08-configuration/CONFIG_RECORDS.md",
                "08-configuration/BASELINE.md",
                "DEVELOPMENT_LOG.md"
            ],
            "checks": {
                "CONFIG_RECORDS_exists": "08-configuration/CONFIG_RECORDS.md",
                "BASELINE_exists": "08-configuration/BASELINE.md",
                "CONFIG_RECORDS_has_versions": "08-configuration/CONFIG_RECORDS.md",
                "BASELINE_has_stability": "08-configuration/BASELINE.md"
            }
        }
    }
    
    def __init__(self, project_path: str, strict_mode: bool = False):
        """
        初始化 FolderStructureChecker
        
        Args:
            project_path: 專案根目錄路徑
            strict_mode: 是否啟用內容結構檢查（預設 False）
        """
        self.project_path = Path(project_path)
        self.strict_mode = strict_mode
        
    def check_file_content_structure(self, file_path: str, required_sections: List[str]) -> ContentCheckResult:
        """
        檢查檔案內容結構
        
        讀取檔案內容，檢查是否包含所有 required_sections
        
        Args:
            file_path: 檔案相對路徑（相對於 project_path）
            required_sections: 需要包含的章節關鍵字列表
            
        Returns:
            ContentCheckResult: 內容結構檢查結果
                - passed: 所有章節都已找到
                - file_path: 檢查的檔案路徑
                - missing_sections: 缺失的章節列表
                - found_sections: 找到的章節列表
        """
        full_path = self.project_path / file_path
        
        if not full_path.exists():
            return ContentCheckResult(
                passed=False,
                file_path=file_path,
                missing_sections=required_sections,
                found_sections=[]
            )
        
        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception as e:
            return ContentCheckResult(
                passed=False,
                file_path=file_path,
                missing_sections=required_sections,
                found_sections=[]
            )
        
        # 檢查每個 required_section 是否存在於內容中
        found_sections = []
        missing_sections = []
        
        for section in required_sections:
            # 不分大小寫檢查
            if section.lower() in content.lower():
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        passed = len(missing_sections) == 0
        
        return ContentCheckResult(
            passed=passed,
            file_path=file_path,
            missing_sections=missing_sections,
            found_sections=found_sections
        )
        
    def run(self, phase: int) -> FolderCheckResult:
        """
        執行資料夾結構檢查
        
        Args:
            phase: Phase 編號 (1-8)
            
        Returns:
            FolderCheckResult: 檢查結果
        """
        if phase not in self.PHASE_STRUCTURES:
            return FolderCheckResult(
                passed=False,
                phase=phase,
                score=0.0,
                missing_dirs=[],
                missing_files=[],
                content_issues=[f"Unknown phase: {phase}"],
                content_check=[],
                details={"error": f"Phase {phase} not supported"}
            )
        
        structure = self.PHASE_STRUCTURES[phase]
        
        # 1. 檢查必要資料夾
        missing_dirs = self._check_required_dirs(structure["required_dirs"])
        
        # 2. 檢查必要檔案
        missing_files = self._check_required_files(structure["required_files"])
        
        # 3. 檢查內容完整性
        content_issues = self._check_content_completeness(phase, structure)
        
        # 4. 內容結構檢查（strict_mode 時啟用）
        content_check_results = []
        if self.strict_mode and phase in PHASE_CONTENT_STRUCTURES:
            phase_content_files = PHASE_CONTENT_STRUCTURES[phase]
            for file_path, required_sections in phase_content_files.items():
                result = self.check_file_content_structure(file_path, required_sections)
                content_check_results.append(result.to_dict())
        
        # 5. 計算分數
        total_checks = len(structure["required_dirs"]) + len(structure["required_files"]) + len(structure.get("checks", {}))
        
        # strict_mode 時加入內容結構檢查的權重
        if self.strict_mode:
            total_checks += len(content_check_results)
            # 內容結構檢查失敗也計入 failed_checks
            content_failed = sum(1 for r in content_check_results if not r["passed"])
            failed_checks = len(missing_dirs) + len(missing_files) + len(content_issues) + content_failed
        else:
            failed_checks = len(missing_dirs) + len(missing_files) + len(content_issues)
        
        score = ((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 100.0
        
        # 6. 判斷是否通過
        if self.strict_mode:
            # strict_mode 時：檔案存在 + 內容結構都通過才算通過
            passed = (len(missing_dirs) == 0 and 
                     len(missing_files) == 0 and 
                     len(content_issues) == 0 and
                     all(r["passed"] for r in content_check_results))
        else:
            passed = len(missing_dirs) == 0 and len(missing_files) == 0 and len(content_issues) == 0
        
        return FolderCheckResult(
            passed=passed,
            phase=phase,
            score=round(score, 2),
            missing_dirs=missing_dirs,
            missing_files=missing_files,
            content_issues=content_issues,
            content_check=content_check_results,
            details={
                "structure": structure,
                "total_checks": total_checks,
                "failed_checks": failed_checks
            }
        )
    
    def _check_required_dirs(self, required_dirs: List[str]) -> List[str]:
        """檢查必要資料夾是否存在"""
        missing = []
        for dir_path in required_dirs:
            full_path = self.project_path / dir_path
            if not full_path.exists():
                missing.append(dir_path)
            elif not full_path.is_dir():
                missing.append(dir_path)
        return missing
    
    def _check_required_files(self, required_files: List[str]) -> List[str]:
        """檢查必要檔案是否存在"""
        missing = []
        for file_path in required_files:
            # 支援萬用字元 *
            if "*" in file_path:
                pattern = file_path.replace("*", "*")
                parent_dir = self.project_path / file_path.rsplit("/", 1)[0]
                if parent_dir.exists():
                    matches = list(parent_dir.glob(file_path.rsplit("/", 1)[-1]))
                    if not matches:
                        missing.append(file_path)
                else:
                    missing.append(file_path)
            else:
                full_path = self.project_path / file_path
                if not full_path.exists():
                    missing.append(file_path)
        return missing
    
    def _check_content_completeness(self, phase: int, structure: Dict) -> List[str]:
        """檢查內容完整性"""
        issues = []
        
        # 根據不同 Phase 進行內容檢查
        if phase == 1:
            issues.extend(self._check_phase1_content(structure))
        elif phase == 2:
            issues.extend(self._check_phase2_content(structure))
        elif phase == 3:
            issues.extend(self._check_phase3_content(structure))
        elif phase == 4:
            issues.extend(self._check_phase4_content(structure))
        elif phase == 5:
            issues.extend(self._check_phase5_content(structure))
        elif phase == 6:
            issues.extend(self._check_phase6_content(structure))
        elif phase == 7:
            issues.extend(self._check_phase7_content(structure))
        elif phase == 8:
            issues.extend(self._check_phase8_content(structure))
            
        return issues
    
    def _check_phase1_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 1 內容完整性"""
        issues = []
        
        # 檢查 SRS.md 是否包含 FR
        srs_path = self.project_path / "01-requirements/SRS.md"
        if srs_path.exists():
            content = srs_path.read_text(encoding="utf-8")
            if "FR-" not in content and "FR:" not in content:
                issues.append("SRS.md missing FR (Functional Requirements)")
        else:
            issues.append("SRS.md does not exist")
        
        # 檢查 TRACEABILITY_MATRIX.md 的 FR 欄位
        trace_path = self.project_path / "01-requirements/TRACEABILITY_MATRIX.md"
        if trace_path.exists():
            content = trace_path.read_text(encoding="utf-8")
            # 檢查是否有 FR 欄位且已填
            if "FR" in content:
                # 簡單檢查：是否有非空的 FR 欄位
                if not re.search(r'FR-\d+|FR:\d+', content):
                    issues.append("TRACEABILITY_MATRIX.md FR column not filled")
            else:
                issues.append("TRACEABILITY_MATRIX.md missing FR column")
        else:
            issues.append("TRACEABILITY_MATRIX.md does not exist")
        
        # 檢查 DEVELOPMENT_LOG.md 是否有 Quality Gate 輸出
        dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
        if dev_log_path.exists():
            content = dev_log_path.read_text(encoding="utf-8")
            if "Quality Gate" not in content and "quality_gate" not in content.lower():
                issues.append("DEVELOPMENT_LOG.md missing Quality Gate output")
        else:
            issues.append("DEVELOPMENT_LOG.md does not exist")
        
        return issues
    
    def _check_phase2_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 2 內容完整性"""
        issues = []
        
        # 檢查 SAD.md 是否包含模組設計
        sad_path = self.project_path / "02-architecture/SAD.md"
        if sad_path.exists():
            content = sad_path.read_text(encoding="utf-8")
            # 檢查是否有模組相關內容
            if "module" not in content.lower() and "Module" not in content:
                issues.append("SAD.md missing module design")
            # 檢查是否有 ADR
            if "ADR" not in content and "Architecture Decision" not in content:
                issues.append("SAD.md missing ADR records")
        else:
            issues.append("SAD.md does not exist")
        
        # 檢查 DEVELOPMENT_LOG.md 是否包含 Conflict Log
        dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
        if dev_log_path.exists():
            content = dev_log_path.read_text(encoding="utf-8")
            if "conflict" not in content.lower() and "Conflict" not in content:
                issues.append("DEVELOPMENT_LOG.md missing Conflict Log")
        else:
            issues.append("DEVELOPMENT_LOG.md does not exist")
        
        return issues
    
    def _check_phase3_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 3 內容完整性"""
        issues = []
        
        # 檢查 src 目錄是否有 Python 檔案
        src_dir = self.project_path / "03-implementation/src"
        if src_dir.exists():
            py_files = list(src_dir.glob("*.py"))
            if not py_files:
                issues.append("03-implementation/src has no Python files")
        else:
            issues.append("03-implementation/src directory does not exist")
        
        # 檢查 tests 目錄是否有測試檔案
        tests_dir = self.project_path / "03-implementation/tests"
        if tests_dir.exists():
            test_files = list(tests_dir.glob("test_*.py"))
            if not test_files:
                issues.append("03-implementation/tests has no test files")
        else:
            issues.append("03-implementation/tests directory does not exist")
        
        # 檢查 DEVELOPMENT_LOG.md 是否包含邏輯審查對話
        dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
        if dev_log_path.exists():
            content = dev_log_path.read_text(encoding="utf-8")
            if "review" not in content.lower() and "Review" not in content:
                issues.append("DEVELOPMENT_LOG.md missing review dialogue")
        else:
            issues.append("DEVELOPMENT_LOG.md does not exist")
        
        return issues
    
    def _check_phase4_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 4 內容完整性"""
        issues = []
        
        # 檢查 TEST_RESULTS.md 是否包含 pytest 輸出
        results_path = self.project_path / "04-testing/TEST_RESULTS.md"
        if results_path.exists():
            content = results_path.read_text(encoding="utf-8")
            if "pytest" not in content.lower() and "passed" not in content.lower():
                issues.append("TEST_RESULTS.md missing pytest output")
            # 檢查是否有失敗案例的根本原因分析
            if "failed" in content.lower():
                if "root cause" not in content.lower() and "原因" not in content:
                    issues.append("TEST_RESULTS.md missing failure root cause analysis")
        else:
            issues.append("TEST_RESULTS.md does not exist")
        
        # 檢查 DEVELOPMENT_LOG.md 是否包含 A/B 審查記錄
        dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
        if dev_log_path.exists():
            content = dev_log_path.read_text(encoding="utf-8")
            if "A/B" not in content and "AB" not in content and "review" not in content.lower():
                issues.append("DEVELOPMENT_LOG.md missing A/B review records")
        else:
            issues.append("DEVELOPMENT_LOG.md does not exist")
        
        return issues
    
    def _check_phase5_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 5 驗證與交付內容完整性"""
        issues = []
        
        # 檢查 QUALITY_REPORT.md 是否包含摘要
        report_path = self.project_path / "05-delivery/QUALITY_REPORT.md"
        if report_path.exists():
            content = report_path.read_text(encoding="utf-8")
            if "summary" not in content.lower() and "摘要" not in content:
                issues.append("QUALITY_REPORT.md missing summary")
        else:
            issues.append("QUALITY_REPORT.md does not exist")
        
        # 檢查 DELIVERY_MANIFEST.md 是否包含產出物清單
        manifest_path = self.project_path / "05-delivery/DELIVERY_MANIFEST.md"
        if manifest_path.exists():
            content = manifest_path.read_text(encoding="utf-8")
            if "artifact" not in content.lower() and "產出" not in content:
                issues.append("DELIVERY_MANIFEST.md missing artifacts list")
        else:
            issues.append("DELIVERY_MANIFEST.md does not exist")
        
        # 檢查 DEVELOPMENT_LOG.md 是否包含交付記錄
        dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
        if dev_log_path.exists():
            content = dev_log_path.read_text(encoding="utf-8")
            if "delivery" not in content.lower() and "交付" not in content:
                issues.append("DEVELOPMENT_LOG.md missing delivery records")
        else:
            issues.append("DEVELOPMENT_LOG.md does not exist")
        
        return issues
    
    def _check_phase6_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 6 品質確保內容完整性"""
        issues = []
        
        # 檢查 QUALITY_ASSURANCE.md 是否包含缺陷追蹤
        qa_path = self.project_path / "06-quality/QUALITY_ASSURANCE.md"
        if qa_path.exists():
            content = qa_path.read_text(encoding="utf-8")
            if "defect" not in content.lower() and "bug" not in content.lower() and "缺陷" not in content:
                issues.append("QUALITY_ASSURANCE.md missing defect tracking")
        else:
            issues.append("QUALITY_ASSURANCE.md does not exist")
        
        # 檢查 QUALITY_METRICS.md 是否包含覆蓋率
        metrics_path = self.project_path / "06-quality/QUALITY_METRICS.md"
        if metrics_path.exists():
            content = metrics_path.read_text(encoding="utf-8")
            if "coverage" not in content.lower() and "覆蓋率" not in content:
                issues.append("QUALITY_METRICS.md missing coverage metrics")
        else:
            issues.append("QUALITY_METRICS.md does not exist")
        
        return issues
    
    def _check_phase7_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 7 風險管理內容完整性"""
        issues = []
        
        # 檢查 RISK_ASSESSMENT.md 是否包含緩解措施
        assessment_path = self.project_path / "07-risk/RISK_ASSESSMENT.md"
        if assessment_path.exists():
            content = assessment_path.read_text(encoding="utf-8")
            if "mitigation" not in content.lower() and "緩解" not in content:
                issues.append("RISK_ASSESSMENT.md missing mitigation strategies")
        else:
            issues.append("RISK_ASSESSMENT.md does not exist")
        
        # 檢查 RISK_REGISTER.md 是否包含追蹤狀態
        register_path = self.project_path / "07-risk/RISK_REGISTER.md"
        if register_path.exists():
            content = register_path.read_text(encoding="utf-8")
            if "status" not in content.lower() and "狀態" not in content:
                issues.append("RISK_REGISTER.md missing status tracking")
        else:
            issues.append("RISK_REGISTER.md does not exist")
        
        return issues
    
    def _check_phase8_content(self, structure: Dict) -> List[str]:
        """檢查 Phase 8 配置管理內容完整性"""
        issues = []
        
        # 檢查 CONFIG_RECORDS.md 是否包含版本資訊
        config_path = self.project_path / "08-configuration/CONFIG_RECORDS.md"
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8")
            if "version" not in content.lower() and "版本" not in content:
                issues.append("CONFIG_RECORDS.md missing version information")
        else:
            issues.append("CONFIG_RECORDS.md does not exist")
        
        # 檢查 BASELINE.md 是否包含穩定性記錄
        baseline_path = self.project_path / "08-configuration/BASELINE.md"
        if baseline_path.exists():
            content = baseline_path.read_text(encoding="utf-8")
            if "stable" not in content.lower() and "穩定" not in content:
                issues.append("BASELINE.md missing stability records")
        else:
            issues.append("BASELINE.md does not exist")
        
        return issues
    
    def check_all_phases(self) -> Dict[int, FolderCheckResult]:
        """檢查所有 Phase 的資料夾結構"""
        results = {}
        for phase in range(1, 9):
            results[phase] = self.run(phase)
        return results


# ===== 快速函式入口 =====
def check_folder_structure(project_path: str, phase: int = None, strict_mode: bool = False) -> Dict:
    """
    快速檢查資料夾結構
    
    Args:
        project_path: 專案路徑
        phase: Phase 編號 (1-8)，若為 None 則檢查所有 Phase
        strict_mode: 是否啟用內容結構檢查（預設 False）
        
    Returns:
        Dict: 檢查結果
    """
    checker = FolderStructureChecker(project_path, strict_mode=strict_mode)
    
    if phase is not None:
        result = checker.run(phase)
        return result.to_dict()
    else:
        results = checker.check_all_phases()
        return {phase: r.to_dict() for phase, r in results.items()}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python folder_structure_checker.py <project_path> [phase] [--strict]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    phase = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else None
    strict_mode = "--strict" in sys.argv
    
    result = check_folder_structure(project_path, phase, strict_mode=strict_mode)
    print(f"Result: {result}")
