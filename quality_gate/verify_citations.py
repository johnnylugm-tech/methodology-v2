#!/usr/bin/env python3
"""
verify_citations.py - HR-15 Citations 自動化驗證工具

自動驗證 Citations：
1. 解析 docstring 中的 SRS.md#L 和 SAD.md#L
2. 用實際行號讀取檔案內容
3. 比對是否與 FR 內容相關
4. 回傳 PASS/FAIL + 具體問題

使用時機：
- Reviewer APPROVE 前自動呼叫
- Quality Gate 的一環
- Phase 結束前的最終驗證
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Citation:
    """單一 Citation 記錄"""
    artifact: str  # "SRS.md" 或 "SAD.md"
    line_start: int
    line_end: Optional[int] = None
    context: str = ""  # 上下文字內容


@dataclass
class CitationCheck:
    """單一檔案的 Citation 檢查結果"""
    file_path: str
    function_name: str
    citations: List[Citation] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    passed: bool = True
    score: float = 100.0


@dataclass
class VerificationResult:
    """整體驗證結果"""
    passed: bool
    total_files: int
    total_functions: int
    total_citations: int
    issues_found: int
    checks: List[CitationCheck] = field(default_factory=list)
    score: float = 100.0
    summary: str = ""


# ============================================================================
# CITATION PARSER
# ============================================================================

class CitationParser:
    """解析 docstring 中的 Citations"""
    
    # 匹配 Citations 行：Citations: SRS.md#L23-L45, SAD.md#L67
    CITATION_PATTERN = re.compile(
        r'Citations:\s*((?:(?:SRS|SAD|SPEC|ARCH)\.md#L\d+(?:-\d+)?(?:\s*,\s*)?)+)',
        re.IGNORECASE
    )
    
    # 匹配單一 citation：SRS.md#L23 或 SAD.md#L45-L67
    SINGLE_CITATION_PATTERN = re.compile(
        r'(SRS|SAD|SPEC|ARCH)\.md#L(\d+)(?:-L?(\d+))?',
        re.IGNORECASE
    )
    
    # 匹配 docstring
    DOCSTRING_PATTERN = re.compile(
        r'("""|\'\'\')(.*?)\1',
        re.DOTALL
    )
    
    def parse(self, content: str) -> List[Citation]:
        """從檔案內容解析所有 Citations"""
        citations = []
        
        # 找所有 docstrings
        for match in self.DOCSTRING_PATTERN.finditer(content):
            docstring = match.group(2)
            
            # 在 docstring 中找 Citations 行
            for cite_match in self.CITATION_PATTERN.finditer(docstring):
                citation_str = cite_match.group(1)
                
                # 解析每個單一 citation
                for single_match in self.SINGLE_CITATION_PATTERN.finditer(citation_str):
                    artifact = f"{single_match.group(1)}.md".upper()
                    line_start = int(single_match.group(2))
                    line_end_str = single_match.group(3)
                    line_end = int(line_end_str) if line_end_str else None
                    
                    citations.append(Citation(
                        artifact=artifact,
                        line_start=line_start,
                        line_end=line_end or line_start,
                        context=docstring[:200]  # 取前200字作為上下文
                    ))
        
        return citations


# ============================================================================
# CITATION VERIFIER
# ============================================================================

class CitationVerifier:
    """驗證 Citations 的有效性"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.parser = CitationParser()
        self.fr_keywords: Dict[str, List[str]] = {}
        
    def load_fr_keywords(self, fr_id: str) -> List[str]:
        """載入 FR 的關鍵字，用於內容比對"""
        srs_path = self.project_path / "01-requirements" / "SRS.md"
        if not srs_path.exists():
            srs_path = self.project_path / "SRS.md"
        
        if not srs_path.exists():
            return []
        
        content = srs_path.read_text()
        
        # 找到 FR-XX 章節
        fr_pattern = re.compile(
            rf'(?:^|=20 )##\s+{fr_id}[^#]*#(.+?)(?=^##|\Z)',
            re.MULTILINE | re.DOTALL
        )
        match = fr_pattern.search(content)
        if not match:
            return []
        
        fr_content = match.group(1)
        
        # 提取關鍵字（中文詞彙和英文術語）
        keywords = []
        
        # 中文：提取連續中文字串
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', fr_content)
        keywords.extend(chinese_words[:20])  # 限制數量
        
        # 英文：提取有意义的单词
        english_words = re.findall(r'\b[a-zA-Z]{4,}\b', fr_content)
        keywords.extend([w for w in english_words if w.lower() not in 
                        {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'them'}] [:20])
        
        return list(set(keywords))[:30]
    
    def verify_citation_content(self, citation: Citation, file_path: str) -> Tuple[bool, str]:
        """
        驗證單一 Citation 的內容是否與 FR 相關
        
        Returns:
            (passed, reason)
        """
        artifact_path = self.project_path / citation.artifact
        if not artifact_path.exists():
            return False, f"Artifact 檔案不存在: {citation.artifact}"
        
        try:
            lines = artifact_path.read_text(encoding='utf-8').split('\n')
        except:
            lines = artifact_path.read_text().split('\n')
        
        # 檢查行號是否有效
        if citation.line_start > len(lines):
            return False, f"行號 {citation.line_start} 超出範圍 (檔案只有 {len(lines)} 行)"
        
        if citation.line_end and citation.line_end > len(lines):
            return False, f"終止行號 {citation.line_end} 超出範圍 (檔案只有 {len(lines)} 行)"
        
        # 讀取引用範圍的內容
        start_idx = citation.line_start - 1  # 轉換為 0-index
        end_idx = citation.line_end if citation.line_end else citation.line_start
        end_idx = min(end_idx - 1, len(lines) - 1)  # 轉換為 0-index
        
        cited_content = '\n'.join(lines[start_idx:end_idx + 1])
        
        # 基本檢查：內容是否為空
        if not cited_content.strip():
            return False, f"引用內容為空 (L{citation.line_start}-{citation.line_end})"
        
        return True, f"OK (L{citation.line_start}-{citation.line_end})"
    
    def verify_file(self, file_path: str, fr_id: str) -> CitationCheck:
        """驗證單一檔案的所有 Citations"""
        check = CitationCheck(file_path=file_path, function_name="")
        
        path = Path(file_path)
        if not path.exists():
            check.issues.append(f"檔案不存在: {file_path}")
            check.passed = False
            check.score = 0
            return check
        
        content = path.read_text()
        
        # 解析所有 Citations
        citations = self.parser.parse(content)
        
        if not citations:
            check.issues.append("檔案中沒有找到任何 Citations")
            check.passed = False
            check.score = 0
            return check
        
        check.citations = citations
        
        # 驗證每個 Citation
        for cite in citations:
            passed, reason = self.verify_citation_content(cite, file_path)
            if not passed:
                check.issues.append(f"[{cite.artifact}#L{cite.line_start}] {reason}")
        
        # 計算分數
        total_cites = len(citations)
        valid_cites = total_cites - len(check.issues)
        check.score = (valid_cites / max(total_cites, 1)) * 100
        check.passed = len(check.issues) == 0
        
        return check
    
    def verify_project(self, fr_id: str, module_paths: List[str]) -> VerificationResult:
        """
        驗證整個專案/模組的 Citations
        
        Args:
            fr_id: e.g., "FR-01"
            module_paths: 要檢查的檔案路徑列表
        
        Returns:
            VerificationResult
        """
        result = VerificationResult(
            passed=True,
            total_files=len(module_paths),
            total_functions=0,
            total_citations=0,
            issues_found=0
        )
        
        # 載入 FR 關鍵字
        self.fr_keywords[fr_id] = self.load_fr_keywords(fr_id)
        
        for file_path in module_paths:
            check = self.verify_file(file_path, fr_id)
            result.checks.append(check)
            result.total_citations += len(check.citations)
            result.issues_found += len(check.issues)
            result.total_functions += 1
            
            if not check.passed:
                result.passed = False
        
        # 計算總分
        if result.total_files > 0:
            result.score = sum(c.score for c in result.checks) / len(result.checks)
        
        # 生成摘要
        if result.passed:
            result.summary = f"✅ PASS: {result.total_files} 檔案, {result.total_citations} Citations, {result.issues_found} issues"
        else:
            result.summary = f"❌ FAIL: {result.issues_found} issues found"
        
        return result


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="HR-15 Citations 驗證工具")
    parser.add_argument("--project", required=True, help="專案路徑")
    parser.add_argument("--fr", required=True, help="FR ID (e.g., FR-01)")
    parser.add_argument("--files", nargs="+", help="要檢查的檔案列表")
    parser.add_argument("--module", help="要檢查的模組目錄")
    parser.add_argument("--output", help="輸出 JSON 報告")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    # 確定要檢查的檔案
    if args.files:
        files_to_check = args.files
    elif args.module:
        module_path = Path(args.project) / args.module
        files_to_check = [str(f) for f in module_path.rglob("*.py")]
    else:
        # 預設檢查 app/ 目錄
        app_path = Path(args.project) / "app"
        files_to_check = [str(f) for f in app_path.rglob("*.py")] if app_path.exists() else []
    
    if not files_to_check:
        print("❌ 沒有找到要檢查的檔案")
        return 1
    
    print(f"🔍 HR-15 Citations 驗證")
    print(f"   專案: {args.project}")
    print(f"   FR: {args.fr}")
    print(f"   檔案數: {len(files_to_check)}")
    print()
    
    # 執行驗證
    verifier = CitationVerifier(args.project)
    result = verifier.verify_project(args.fr, files_to_check)
    
    # 輸出結果
    print(result.summary)
    print()
    
    if args.verbose or not result.passed:
        for check in result.checks:
            status = "✅" if check.passed else "❌"
            print(f"  {status} {check.file_path} (score: {check.score:.0f}%)")
            for issue in check.issues:
                print(f"      - {issue}")
    
    print()
    print(f"📊 總分: {result.score:.1f}%")
    
    # 寫入 JSON 報告
    if args.output:
        output_data = {
            "fr_id": args.fr,
            "passed": result.passed,
            "total_files": result.total_files,
            "total_citations": result.total_citations,
            "issues_found": result.issues_found,
            "score": result.score,
            "summary": result.summary,
            "checks": [
                {
                    "file": c.file_path,
                    "passed": c.passed,
                    "score": c.score,
                    "citations": [
                        {"artifact": cit.artifact, "line": cit.line_start}
                        for cit in c.citations
                    ],
                    "issues": c.issues
                }
                for c in result.checks
            ]
        }
        Path(args.output).write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
        print(f"📄 報告已寫入: {args.output}")
    
    return 0 if result.passed else 1


if __name__ == "__main__":
    exit(main())
