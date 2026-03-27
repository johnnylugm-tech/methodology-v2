#!/usr/bin/env python3
"""
A/B Enforcer - 強制執行防線

v1.0 (2026-03-27): 修復 3 大漏洞
- P0-1: 審查真實性驗證
- P0-2: 主代理權限限制
- P0-3: 交換角色驗證
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# P0-1: 審查真實性驗證
# ============================================================================

class ReviewEvidenceRequired(Exception):
    pass

class ReviewAuthenticityError(Exception):
    pass


@dataclass
class ReviewEvidence:
    what_checked: str
    evidence_found: str
    problem_identified: str
    why_no_questions: str
    quoted_lines: List[str]
    review_duration: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ReviewEvidenceEnforcer:
    """審查真實性驗證器 - 防止假裝審查"""
    
    MIN_QUOTED_LINES = 3
    MIN_REVIEW_TIME_PER_1000_CHARS = 3
    
    @classmethod
    def validate_review(cls, review_content: str, output: Dict[str, Any]) -> ReviewEvidence:
        evidence = output.get("evidence", {})
        
        # 1. 檢查必要欄位
        required_fields = ["what_checked", "evidence_found", "conclusion"]
        for field_name in required_fields:
            if not evidence.get(field_name):
                raise ReviewEvidenceRequired(f"審查缺少必要欄位: {field_name}")
        
        # 2. 檢查引用原文
        quoted_lines = evidence.get("quoted_lines", [])
        if len(quoted_lines) < cls.MIN_QUOTED_LINES:
            raise ReviewEvidenceRequired(f"審查必須引用至少 {cls.MIN_QUOTED_LINES} 行原文")
        
        # 3. 檢查時間合理性
        content_length = len(review_content)
        min_time = (content_length / 1000) * cls.MIN_REVIEW_TIME_PER_1000_CHARS
        review_time = evidence.get("review_duration", 0)
        
        if review_time < min_time * 0.5:
            raise ReviewAuthenticityError(f"審查時間太短，可能沒看")
        
        # 4. 如果沒問題，必須說明為什麼
        if not evidence.get("problem_identified") and not evidence.get("why_no_questions"):
            raise ReviewEvidenceRequired("必須說明『為什麼沒問題』")
        
        return ReviewEvidence(
            what_checked=evidence.get("what_checked", ""),
            evidence_found=evidence.get("evidence_found", ""),
            problem_identified=evidence.get("problem_identified", ""),
            why_no_questions=evidence.get("why_no_questions", ""),
            quoted_lines=quoted_lines,
            review_duration=review_time
        )


# ============================================================================
# P0-2: 主代理權限限制
# ============================================================================

class PermissionDenied(Exception):
    pass


class AgentType(Enum):
    MAIN = "main"
    SUB = "sub"


class MainAgentPermissionRestrictor:
    """主代理權限限制器 - 防止不受控"""
    
    ALLOWED_TOOLS = {"read", "sessions_spawn", "sessions_send", "sessions_list", "sessions_history"}
    FORBIDDEN_TOOLS = {"write", "exec", "edit", "delete"}
    
    @classmethod
    def check_permission(cls, agent_type: AgentType, tool_name: str) -> bool:
        if agent_type != AgentType.MAIN:
            return True
        
        if tool_name in cls.FORBIDDEN_TOOLS:
            raise PermissionDenied(f"主代理禁止使用: {tool_name}。只能讀取和發訊，不能執行或寫入。")
        
        if tool_name not in cls.ALLOWED_TOOLS:
            raise PermissionDenied(f"主代理未授權: {tool_name}")
        
        return True


# ============================================================================
# P0-3: 交換角色驗證
# ============================================================================

class SwapReviewError(Exception):
    pass


class SwapReviewVerifier:
    """交換角色驗證器 - 確保兩雙眼睛"""
    
    MIN_TIME_BETWEEN_REVIEWS = 60
    
    @classmethod
    def verify_swap_completed(cls, phase: int, review_record: Dict) -> Dict:
        reviewers = review_record.get("reviewers", [])
        unique_reviewers = set(reviewers)
        
        if len(unique_reviewers) < 2:
            raise SwapReviewError(f"Phase {phase}: 必須有兩個不同審查者")
        
        timestamps = review_record.get("review_timestamps", [])
        if len(timestamps) < 2:
            raise SwapReviewError(f"Phase {phase}: 缺少第二次審查")
        
        try:
            t1 = datetime.fromisoformat(timestamps[0])
            t2 = datetime.fromisoformat(timestamps[1])
            time_diff = (t2 - t1).total_seconds()
        except:
            raise SwapReviewError(f"Phase {phase}: 時間格式錯誤")
        
        if time_diff < cls.MIN_TIME_BETWEEN_REVIEWS:
            raise SwapReviewError(f"Phase {phase}: 交換審查時間間隔不足")
        
        if t2 <= t1:
            raise SwapReviewError(f"Phase {phase}: 交換審查順序錯誤")
        
        return {
            "phase": phase,
            "reviewer_1": list(unique_reviewers)[0],
            "reviewer_2": list(unique_reviewers)[1],
            "timestamp_1": timestamps[0],
            "timestamp_2": timestamps[1],
            "approved": review_record.get("approvals", [False, False])
        }


# ============================================================================
# 統一介面
# ============================================================================

class ABEnforcer:
    """A/B 協作強制執行器"""
    
    def __init__(self):
        self.violations = []
    
    def check_tool(self, agent_type: str, tool_name: str):
        try:
            agent = AgentType.MAIN if agent_type == "main" else AgentType.SUB
            MainAgentPermissionRestrictor.check_permission(agent, tool_name)
        except PermissionDenied as e:
            self.violations.append({"type": "permission", "error": str(e)})
            raise
    
    def validate_review(self, content: str, output: Dict):
        try:
            ReviewEvidenceEnforcer.validate_review(content, output)
        except (ReviewEvidenceRequired, ReviewAuthenticityError) as e:
            self.violations.append({"type": "review", "error": str(e)})
            raise
    
    def verify_swap(self, phase: int, record: Dict):
        try:
            SwapReviewVerifier.verify_swap_completed(phase, record)
        except SwapReviewError as e:
            self.violations.append({"type": "swap", "error": str(e)})
            raise
    
    def get_violations(self):
        return self.violations


# ============================================================================
# 便捷函數
# ============================================================================

def enforce_tool(agent_type: str, tool_name: str):
    """enforce_tool('main', 'write') → 會 raise"""
    enforcer = ABEnforcer()
    enforcer.check_tool(agent_type, tool_name)
    return True

def enforce_review(content: str, output: Dict):
    """enforce_review(review_content, output) → 會 raise"""
    enforcer = ABEnforcer()
    enforcer.validate_review(content, output)
    return True

def enforce_swap(phase: int, record: Dict):
    """enforce_swap(1, review_record) → 會 raise"""
    enforcer = ABEnforcer()
    enforcer.verify_swap(phase, record)
    return True