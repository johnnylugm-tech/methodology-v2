#!/usr/bin/env python3
"""
A/B Enforcer - 強制執行防線

v2.0 (2026-03-27): 代碼層級整合 - 無法饒過

變更：
- P0-1: 審查真實性驗證 → 整合進 TaskLifecycle
- P0-2: 主代理權限限制 → 整合進 AgentSpawner
- P0-3: 交換角色驗證 → 整合進 QualityGate
"""

import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# P0-1: 審查真實性驗證 → 整合進 TaskLifecycle
# ============================================================================

class ReviewEvidenceRequired(Exception):
    pass

class ReviewAuthenticityError(Exception):
    pass


class ABTaskLifecycle:
    """
    整合 A/B Enforcer 的 TaskLifecycle
    
    確保每次 Phase 完成都觸發審查驗證
    """
    
    def __init__(self):
        self.phase = 0
        self.review_evidence_log = []
        self.violations = []
    
    def complete_phase(self, phase: int, sub_agent_output: Dict) -> bool:
        """
        Phase 完成時自動觸發審查驗證
        
        不能饒過：每次 call 都會執行
        """
        self.phase = phase
        
        # P0-1: 強制驗證審查真實性
        self._validate_review_evidence(sub_agent_output)
        
        # P0-3: 強制驗證交換角色
        self._validate_swap_review(sub_agent_output)
        
        return True
    
    def _validate_review_evidence(self, output: Dict):
        """驗證審查證據（內部自動執行）"""
        evidence = output.get("review", {}).get("evidence", {})
        
        # 1. 必須有引用原文
        quoted = evidence.get("quoted_lines", [])
        if len(quoted) < 3:
            self.violations.append({
                "phase": self.phase,
                "type": "insufficient_evidence",
                "message": "審查必須引用至少 3 行原文"
            })
        
        # 2. 必須說明檢查了什麼
        if not evidence.get("what_checked"):
            self.violations.append({
                "phase": self.phase,
                "type": "missing_check_item",
                "message": "審查必須說明檢查了什麼"
            })
        
        # 3. 必須有結論
        if not evidence.get("conclusion"):
            self.violations.append({
                "phase": self.phase,
                "type": "missing_conclusion",
                "message": "審查必須有結論"
            })
    
    def _validate_swap_review(self, output: Dict):
        """驗證交換角色（內部自動執行）"""
        review = output.get("review", {})
        
        reviewers = review.get("reviewers", [])
        timestamps = review.get("review_timestamps", [])
        
        # 必須有兩個不同審查者
        if len(set(reviewers)) < 2:
            self.violations.append({
                "phase": self.phase,
                "type": "swap_review_missing",
                "message": "必須有兩個不同審查者（交換角色）"
            })
        
        # 必須有兩個時間戳
        if len(timestamps) < 2:
            self.violations.append({
                "phase": self.phase,
                "type": "swap_review_incomplete",
                "message": "缺少第二次審查時間戳"
            })
    
    def can_proceed(self) -> bool:
        """檢查是否可以進入下一個 Phase"""
        return len(self.violations) == 0
    
    def get_violations(self) -> List[Dict]:
        return self.violations


# ============================================================================
# P0-2: 主代理權限限制 → 整合進 AgentSpawner
# ============================================================================

class PermissionDenied(Exception):
    pass


class RestrictedAgentSpawner:
    """
    整合權限限制的 AgentSpawner
    
    主代理只能：read, sessions_spawn, sessions_send
    """
    
    FORBIDDEN_FOR_MAIN = {"write", "exec", "edit", "delete", "deploy"}
    
    def spawn_agent(self, agent_type: str, task: str, main_agent: bool = False) -> Dict:
        """
        產生 Sub-agent（自動權限檢查）
        
        Args:
            agent_type: Agent 類型
            task: 任務描述
            main_agent: 是否為主代理
        
        Returns:
            Dict: 產生的 agent
        
        Raises:
            PermissionDenied: 權限不足
        """
        # 如果是主代理，限制權限
        if main_agent:
            return {
                "type": agent_type,
                "allowed_tools": ["read", "sessions_spawn", "sessions_send"],
                "forbidden_tools": list(self.FORBIDDEN_FOR_MAIN),
                "role": "reviewer_only"  # 主代理只能是審查者
            }
        
        # Sub-agent 不受限制
        return {
            "type": agent_type,
            "allowed_tools": ["read", "write", "exec", "edit", "sessions_spawn", "sessions_send"],
            "role": "developer"
        }
    
    def validate_tool_call(self, agent_type: str, tool_name: str) -> bool:
        """
        驗證工具調用（每次都會檢查）
        
        不能饒過：每次工具調用都會觸發
        """
        if agent_type == "main" and tool_name in self.FORBIDDEN_FOR_MAIN:
            raise PermissionDenied(
                f"主代理禁止使用 {tool_name}。"
                f"主代理角色是『審查者』，只能讀取和發送訊息。"
            )
        return True


# ============================================================================
# P0-3: 交換角色驗證 → 整合進 QualityGate
# ============================================================================

class SwapReviewError(Exception):
    pass


class ABQualityGate:
    """
    整合交換驗證的 QualityGate
    
    每次 Phase Gate 都會檢查交換審查
    """
    
    MIN_TIME_BETWEEN_REVIEWS = 60  # 至少 60 秒
    
    def check(self, phase: int, deliverables: Dict, review_record: Dict) -> bool:
        """
        Quality Gate 檢查（自動包含交換驗證）
        
        不能饒過：每次 Phase 完成都會觸發
        """
        violations = []
        
        # 1. 文檔完整性檢查
        if not deliverables.get("completed"):
            violations.append("交付物不完整")
        
        # 2. P0-3: 交換角色驗證
        reviewers = review_record.get("reviewers", [])
        timestamps = review_record.get("review_timestamps", [])
        
        # 兩個不同審查者
        if len(set(reviewers)) < 2:
            violations.append(f"Phase {phase}: 必須有兩個不同審查者")
        
        # 兩個時間戳
        if len(timestamps) < 2:
            violations.append(f"Phase {phase}: 缺少第二次審查")
        
        # 時間間隔
        if len(timestamps) >= 2:
            try:
                t1 = datetime.fromisoformat(timestamps[0])
                t2 = datetime.fromisoformat(timestamps[1])
                diff = (t2 - t1).total_seconds()
                if diff < self.MIN_TIME_BETWEEN_REVIEWS:
                    violations.append(f"Phase {phase}: 交換審查時間間隔不足")
            except Exception:
                violations.append(f"Phase {phase}: 時間格式錯誤")
        
        if violations:
            raise Exception(f"Quality Gate 失敗: {'; '.join(violations)}")
        
        return True


# ============================================================================
# 整合後的統一介面
# ============================================================================

class ABEnforcerV2:
    """
    A/B Enforcer v2.0 - 代碼層級整合
    
    所有防線都整合進 framework 核心
    不能饒過：每次流程都會執行
    """
    
    def __init__(self):
        self.lifecycle = ABTaskLifecycle()
        self.spawner = RestrictedAgentSpawner()
        self.quality_gate = ABQualityGate()
    
    def on_phase_complete(self, phase: int, sub_agent_output: Dict):
        """Phase 完成時自動觸發所有驗證"""
        # 自動驗證
        self.lifecycle.complete_phase(phase, sub_agent_output)
        
        # 檢查是否可以繼續
        if not self.lifecycle.can_proceed():
            raise Exception(
                f"Phase {phase} 驗證失敗: "
                f"{self.lifecycle.get_violations()}"
            )
    
    def on_tool_call(self, agent_type: str, tool_name: str):
        """工具調用時自動檢查權限"""
        self.spawner.validate_tool_call(agent_type, tool_name)
    
    def on_quality_gate(self, phase: int, deliverables: Dict, review_record: Dict):
        """Quality Gate 時自動驗證交換"""
        self.quality_gate.check(phase, deliverables, review_record)


# ============================================================================
# 全域實例（自動載入）
# ============================================================================

# 當 import methodology 時自動載入
_ab_enforcer = ABEnforcerV2()

def get_ab_enforcer() -> ABEnforcerV2:
    """取得 A/B Enforcer 實例"""
    return _ab_enforcer


# ============================================================================
#便捷函數
# ============================================================================

def enforce_phase_complete(phase: int, output: Dict):
    """enforce_phase_complete(1, sub_agent_output) - Phase 完成時呼叫"""
    enforcer = get_ab_enforcer()
    enforcer.on_phase_complete(phase, output)

def enforce_tool_call(agent_type: str, tool_name: str):
    """enforce_tool_call('main', 'write') - 工具調用前呼叫"""
    enforcer = get_ab_enforcer()
    enforcer.on_tool_call(agent_type, tool_name)

def enforce_quality_gate(phase: int, deliverables: Dict, review_record: Dict):
    """enforce_quality_gate(1, deliverables, review_record) - Quality Gate 時呼叫"""
    enforcer = get_ab_enforcer()
    enforcer.on_quality_gate(phase, deliverables, review_record)