#!/usr/bin/env python3
"""
Citation Enforcer - 強制引用
===========================
要求 Agent 的每個聲稱必須附上 SKILL.md 的具體行號或章節。
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

class CitationEnforcer:
    """強制引用 SKILL.md"""
    
    def __init__(self, skill_path: str = "SKILL.md"):
        self.skill_path = Path(skill_path)
        self.content = self.skill_path.read_text() if self.skill_path.exists() else ""
        self.lines = self.content.split('\n')
    
    def find_citation(self, keyword: str) -> Optional[Dict]:
        """根據關鍵字找到 SKILL.md 中的引用"""
        
        for i, line in enumerate(self.lines, 1):
            if keyword.lower() in line.lower():
                return {
                    "line_number": i,
                    "content": line.strip(),
                    "context": self._get_context(i)
                }
        
        return None
    
    def _get_context(self, line_num: int, context_lines: int = 2) -> str:
        """取得行號周圍的上下文"""
        
        start = max(0, line_num - context_lines - 1)
        end = min(len(self.lines), line_num + context_lines)
        
        context = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context.append(f"{prefix}{self.lines[i]}")
        
        return "\n".join(context)
    
    def extract_required_citations(self, phase: int) -> List[Dict]:
        """根據 Phase 提取必須引用的內容"""
        
        required = []
        
        # Phase 相關的關鍵字
        phase_keywords = {
            1: ["Phase 1", "SRS", "SPEC_TRACKING", "architect", "reviewer"],
            2: ["Phase 2", "SAD", "architect", "reviewer", "模組"],
            3: ["Phase 3", "developer", "reviewer", "Lazy Init"],
            4: ["Phase 4", "TEST_PLAN", "qa", "pytest"],
            5: ["Phase 5", "BASELINE", "devops"],
            6: ["Phase 6", "QUALITY_REPORT", "qa"],
            7: ["Phase 7", "RISK", "qa"],
            8: ["Phase 8", "CONFIG", "devops"],
        }
        
        keywords = phase_keywords.get(phase, [])
        
        for keyword in keywords:
            citation = self.find_citation(keyword)
            if citation:
                required.append({
                    "keyword": keyword,
                    "citation": citation
                })
        
        return required
    
    def verify_citations(self, claims: List[str]) -> Dict:
        """驗證 claims 是否包含有效引用"""
        
        valid_citations = []
        invalid_claims = []
        
        for claim in claims:
            # 檢查是否包含行號引用（如 "line 123" 或 "第123行"）
            line_ref = re.search(r'(?:line|第)(\d+)', claim, re.IGNORECASE)
            section_ref = re.search(r'###\s*(.+?)(?:\n|$)', claim)
            
            if line_ref or section_ref:
                valid_citations.append({
                    "claim": claim,
                    "line_ref": line_ref.group(1) if line_ref else None,
                    "section_ref": section_ref.group(1) if section_ref else None
                })
            else:
                invalid_claims.append(claim)
        
        return {
            "total_claims": len(claims),
            "valid_citations": len(valid_citations),
            "invalid_claims": len(invalid_claims),
            "passed": len(invalid_claims) == 0,
            "details": {
                "valid": valid_citations,
                "invalid": invalid_claims
            }
        }
    
    def run_citation_check(self, phase: int) -> Dict:
        """執行引用檢查"""
        
        required = self.extract_required_citations(phase)
        
        print(f"\n{'='*60}")
        print(f"強制引用檢查 - Phase {phase}")
        print(f"{'='*60}")
        print(f"\n你必須在 claims 中引用以下內容：\n")
        
        for item in required:
            citation = item['citation']
            print(f"• 關鍵字：「{item['keyword']}」")
            print(f"  行號：{citation['line_number']}")
            print(f"  內容：{citation['content'][:50]}...")
            print()
        
        return {
            "required": required,
            "instructions": "每個聲稱必須包含 SKILL.md 的行號引用"
        }
