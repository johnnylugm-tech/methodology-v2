#!/usr/bin/env python3
"""
Quality Gate Document Checker
==============================
檢查每個 Phase 是否有對應的 ASPICE 文檔

Usage:
    python quality_gate/doc_checker.py                    # 檢查當前目錄
    python quality_gate/doc_checker.py --path /path/to/prj # 檢查指定目錄
    python quality_gate/doc_checker.py --verbose          # 詳細輸出
    python quality_gate/doc_checker.py --format json       # JSON 輸出
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class DocumentRequirement:
    """文檔需求定義"""
    phase: str
    aspice_ref: str
    required_docs: List[str]
    patterns: List[str]
    required: bool = True


# ASPICE 文檔需求定義
DOCUMENT_REQUIREMENTS = [
    DocumentRequirement(
        phase="Phase 1: 需求分析",
        aspice_ref="SWE.1, SWE.2",
        required_docs=["SRS (Software Requirements Specification)"],
        patterns=[r"SRS.*\.md", r"需求規格", r"REQUIREMENTS.*\.md"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 2: 架構設計",
        aspice_ref="SWE.5",
        required_docs=["SAD (Software Architecture Description)"],
        patterns=[r"SAD.*\.md", r"架構設計", r"ARCHITECTURE.*\.md"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 3: 實作與整合",
        aspice_ref="SWE.6",
        required_docs=["Integration Plan"],
        patterns=[r"INTEGRATION", r"整合計畫"],
        required=False
    ),
    DocumentRequirement(
        phase="Phase 4: 測試",
        aspice_ref="SWE.7",
        required_docs=["Test Plan", "Test Specification"],
        patterns=[r"TEST.*PLAN", r"測試計畫", r"TEST.*SPEC"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 5: 驗證與交付",
        aspice_ref="SWE.4, SUP.8",
        required_docs=["Test Results", "Baseline Records"],
        patterns=[r"TEST.*RESULT", r"測試結果", r"BASELINE", r"RELEASE_NOTES"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 6: 品質報告",
        aspice_ref="SUP.9",
        required_docs=["Quality Report"],
        patterns=[r"QUALITY.*REPORT", r"品質報告", r"品質指標"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 7: 風險管理",
        aspice_ref="MAN.5",
        required_docs=["Risk Assessment", "Risk Register"],
        patterns=[r"RISK.*ASSESSMENT", r"風險評估", r"風險登記"],
        required=True
    ),
    DocumentRequirement(
        phase="Phase 8: 配置管理",
        aspice_ref="SUP.8",
        required_docs=["Configuration Records"],
        patterns=[r"CONFIG", r"CHANGELOG"],
        required=True
    ),
]


@dataclass
class CheckResult:
    """檢查結果"""
    phase: str
    aspice_ref: str
    found: bool = False
    files: List[str] = field(default_factory=list)
    missing: str = ""
    status: str = "MISSING"  # PASS, MISSING, WARNING


class DocumentChecker:
    """文檔檢查器"""
    
    def __init__(self, base_path: str = ".", verbose: bool = False):
        self.base_path = Path(base_path)
        self.verbose = verbose
        self.results: List[CheckResult] = []
        
    def find_documentation_files(self) -> List[Path]:
        """找出所有文檔檔案"""
        docs = []
        docs_dir = self.base_path / "docs"
        
        if docs_dir.exists():
            # 遞迴搜尋 docs 目錄
            for ext in ['.md', '.txt', '.rst']:
                docs.extend(docs_dir.rglob(f"*{ext}"))
        
        # 檢查根目錄
        for ext in ['.md', '.txt']:
            docs.extend(self.base_path.glob(f"*{ext}"))
        
        # 檢查 02-architecture/ 目錄 (Phase 2 SAD + ADR)
        arch_dir = self.base_path / "02-architecture"
        if arch_dir.exists():
            for ext in ['.md', '.txt']:
                docs.extend(arch_dir.rglob(f"*{ext}"))
        
        return docs
    
    def check_phase(self, requirement: DocumentRequirement) -> CheckResult:
        """檢查單一 Phase"""
        result = CheckResult(
            phase=requirement.phase,
            aspice_ref=requirement.aspice_ref
        )
        
        docs = self.find_documentation_files()
        
        for doc in docs:
            doc_name = doc.name.lower()
            # 檢查是否符合任一 pattern
            for pattern in requirement.patterns:
                if re.search(pattern, doc_name, re.IGNORECASE):
                    result.found = True
                    result.files.append(str(doc.relative_to(self.base_path)))
                    break
        
        if result.found:
            result.status = "PASS"
        elif requirement.required:
            result.status = "MISSING"
            result.missing = ", ".join(requirement.required_docs)
        else:
            result.status = "OPTIONAL"
            result.missing = ", ".join(requirement.required_docs)
        
        return result
    
    def check_all(self) -> Dict:
        """執行所有檢查"""
        self.results = []
        
        for req in DOCUMENT_REQUIREMENTS:
            result = self.check_phase(req)
            self.results.append(result)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """產生檢查報告"""
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "MISSING")
        optional = sum(1 for r in self.results if r.status == "OPTIONAL")
        
        report = {
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "optional": optional,
                "compliance_rate": f"{(passed/len(self.results))*100:.1f}%"
            },
            "results": []
        }
        
        for r in self.results:
            report["results"].append({
                "phase": r.phase,
                "aspice_ref": r.aspice_ref,
                "status": r.status,
                "files": r.files,
                "missing": r.missing
            })
        
        return report
    
    def print_report(self, report: Dict, format: str = "text"):
        """輸出報告"""
        if format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return
        
        # Text 格式
        print("=" * 70)
        print("📋 ASPICE Documentation Check Report")
        print("=" * 70)
        print(f"Base Path: {self.base_path}")
        print()
        
        # Summary
        summary = report["summary"]
        print(f"📊 Summary:")
        print(f"   Total Phases:    {summary['total']}")
        print(f"   ✅ Passed:       {summary['passed']}")
        print(f"   ❌ Missing:      {summary['failed']}")
        print(f"   📌 Optional:     {summary['optional']}")
        print(f"   Compliance Rate: {summary['compliance_rate']}")
        print()
        
        # Details
        print("📝 Details:")
        print("-" * 70)
        
        for r in report["results"]:
            status_icon = {
                "PASS": "✅",
                "MISSING": "❌",
                "OPTIONAL": "📌"
            }.get(r["status"], "❓")
            
            print(f"{status_icon} {r['phase']}")
            print(f"   ASPICE: {r['aspice_ref']}")
            
            if r["status"] == "PASS":
                for f in r["files"]:
                    print(f"   📄 {f}")
            elif r["status"] == "MISSING":
                print(f"   ⚠️  Missing: {r['missing']}")
            else:
                print(f"   💡 Optional: {r['missing']}")
            
            print()
        
        print("=" * 70)
        
        # Exit code
        if summary["failed"] > 0:
            print(f"⚠️  {summary['failed']} required document(s) missing!")
            return 1
        else:
            print("✅ All required documents are present!")
            return 0


def main():
    parser = argparse.ArgumentParser(
        description="ASPICE Documentation Quality Gate Checker"
    )
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Base path to check (default: current directory)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # 如果是相對路徑，轉為絕對路徑
    base_path = Path(args.path)
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    
    checker = DocumentChecker(base_path, args.verbose)
    report = checker.check_all()
    
    exit_code = checker.print_report(report, args.format)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
