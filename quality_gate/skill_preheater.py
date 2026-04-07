#!/usr/bin/env python3
"""
SKILL.md Preheater - 預熱程序
=============================
在執行任務前，強制 Agent 複習並回答 SKILL.md 相關問題。
"""

from pathlib import Path
from typing import List, Dict

class SkillPreheater:
    """SKILL.md 預熱程序"""
    
    def __init__(self, skill_path: str = "SKILL.md"):
        self.skill_path = Path(skill_path)
        self.content = self.skill_path.read_text() if self.skill_path.exists() else ""
    
    def generate_questions(self, phase: int) -> List[str]:
        """根據 Phase 生成預熱問題"""
        
        questions = [
            f"Phase {phase} 的 WHO（角色分工）定義是什麼？",
            f"Phase {phase} 的 WHAT（交付物）清單有哪些？",
            f"Phase {phase} 的 WHEN（時序門檻）是什麼？",
            f"Phase {phase} 的 BLOCK 級別包含哪些檢查？",
            f"Phase {phase} 的 Constitution 類型是什麼？",
        ]
        
        return questions
    
    def verify_answers(self, answers: List[str]) -> Dict:
        """驗證答案是否提到關鍵內容"""
        
        # 檢查每個答案是否非空且有意義
        valid_count = sum(1 for a in answers if len(a.strip()) > 20)
        
        return {
            "valid_count": valid_count,
            "total": len(answers),
            "passed": valid_count >= 3,  # 至少 3 題回答完整
            "score": valid_count / len(answers) * 100
        }
    
    def run_preflight(self, phase: int) -> Dict:
        """執行預檢查"""
        
        questions = self.generate_questions(phase)
        
        print(f"\n{'='*60}")
        print(f"預熱程序 - Phase {phase}")
        print(f"{'='*60}")
        print("\n請回答以下問題（回答後才能開始任務）：\n")
        
        for i, q in enumerate(questions, 1):
            print(f"{i}. {q}")
        
        return {
            "questions": questions,
            "instructions": "請在 DEVELOPMENT_LOG.md 中記錄你的回答"
        }
