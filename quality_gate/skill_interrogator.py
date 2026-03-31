#!/usr/bin/env python3
"""
SKILL.md Interrogator - 拷問法
===============================
執行任務後，随機抽查 Agent 對 SKILL.md 的理解。
"""

import random
from pathlib import Path
from typing import List, Dict, Tuple

class SkillInterrogator:
    """SKILL.md 拷問程序"""
    
    QUESTIONS = [
        {
            "category": "BLOCK 检查",
            "question": "FrameworkEnforcer BLOCK 級別包含幾項檢查？",
            "answer_hints": ["6", "SPEC_TRACKING", "CONSTITUTION_SCORE", "ASPICE"]
        },
        {
            "category": "Constitution",
            "question": "Constitution runner.py 的 command 是什麼？",
            "answer_hints": ["python", "constitution/runner.py", "--type"]
        },
        {
            "category": "Phase 流程",
            "question": "Phase N 完成後，下一步是什麼？",
            "answer_hints": ["Johnny", "phase-verify", "HITL", "CONFIRM"]
        },
        {
            "category": "A/B 協作",
            "question": "sessions_spawn 的必要參數有哪些？",
            "answer_hints": ["task", "runtime", "mode"]
        },
        {
            "category": "產出物",
            "question": "Phase 3 的必要產出物有哪些？",
            "answer_hints": ["03-implementation/src", "tests", "COMPLIANCE_MATRIX"]
        },
        {
            "category": "驗證",
            "question": "phase-verify 的分數門檻是多少？",
            "answer_hints": ["70", "70%", "可能真實"]
        },
        {
            "category": "5W1H",
            "question": "5W1H 中的 WHEN 代表什麼？",
            "answer_hints": ["時序", "門檻", "時機"]
        },
    ]
    
    def __init__(self, skill_path: str = "SKILL.md"):
        self.skill_path = Path(skill_path)
        self.content = self.skill_path.read_text() if self.skill_path.exists() else ""
    
    def generate_exam(self, num_questions: int = 3) -> List[Dict]:
        """生成抽查試卷"""
        
        selected = random.sample(self.QUESTIONS, min(num_questions, len(self.QUESTIONS)))
        
        print(f"\n{'='*60}")
        print(f"SKILL.md 抽查 - 請回答以下問題")
        print(f"{'='*60}\n")
        
        for i, q in enumerate(selected, 1):
            print(f"{i}. [{q['category']}] {q['question']}")
        
        return selected
    
    def verify_answer(self, question: Dict, answer: str) -> Tuple[bool, str]:
        """驗證答案是否正確"""
        
        answer_lower = answer.lower()
        
        # 檢查答案是否包含關鍵提示
        hints_found = sum(1 for hint in question['answer_hints'] 
                        if hint.lower() in answer_lower)
        
        passed = hints_found >= 1 and len(answer.strip()) > 10
        
        if passed:
            feedback = f"✅ 通過（找到 {hints_found} 個關鍵提示）"
        else:
            feedback = f"❌ 未通過（需要至少 1 個關鍵提示）"
        
        return passed, feedback
    
    def run_interrogation(self, phase: int, num_questions: int = 3) -> Dict:
        """執行拷問"""
        
        questions = self.generate_exam(num_questions)
        
        return {
            "phase": phase,
            "questions": questions,
            "instructions": "請在 DEVELOPMENT_LOG.md 中記錄你的回答"
        }
