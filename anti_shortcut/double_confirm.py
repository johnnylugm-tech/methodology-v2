#!/usr/bin/env python3
"""
Double Confirmation - 雙重確認機制

目標：關鍵操作需要雙重確認

雙重確認操作：
| 操作 | 確認機制 |
|------|---------|
| 發布到 GitHub | 需要 version 確認 |
| 修改 Constitution | 需要 human 確認 |
| 刪除檔案 | 需要 2次確認 |
| 繞過 Quality Gate | 需要 explicit approval |
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable
from datetime import datetime, timedelta
import uuid

class ConfirmationLevel(Enum):
    """確認等級"""
    NONE = "none"
    SINGLE = "single"     # 單次確認
    DOUBLE = "double"    # 雙重確認
    APPROVAL = "approval"  # 需要審批
    BLOCKED = "blocked"   # 直接阻止

@dataclass
class PendingConfirmation:
    """待確認操作"""
    confirmation_id: str
    operation: str
    description: str
    level: ConfirmationLevel
    created_at: datetime
    expires_at: datetime
    confirmations: List[str] = field(default_factory=list)  # 已確認者
    status: str = "pending"  # pending, approved, rejected, expired
    metadata: dict = field(default_factory=dict)

class DoubleConfirmation:
    """
    雙重確認機制
    
    功能：
    - 定義需要雙重確認的操作
    - 追蹤確認狀態
    - 防止意外操作
    """
    
    # 需要雙重確認的操作
    DOUBLE_CONFIRM_OPERATIONS = {
        "release": ConfirmationLevel.DOUBLE,
        "constitution_edit": ConfirmationLevel.APPROVAL,
        "delete_file": ConfirmationLevel.DOUBLE,
        "bypass_quality_gate": ConfirmationLevel.APPROVAL,
        "force_push": ConfirmationLevel.APPROVAL,
        "merge_no_review": ConfirmationLevel.BLOCKED,
        "schema_change": ConfirmationLevel.APPROVAL,
        "env_modification": ConfirmationLevel.DOUBLE,
    }
    
    def __init__(self, timeout_minutes: int = 30):
        self.timeout_minutes = timeout_minutes
        self.pending_confirmations: List[PendingConfirmation] = []
    
    def requires_confirmation(self, operation: str) -> ConfirmationLevel:
        """
        檢查操作是否需要確認
        
        Args:
            operation: 操作名稱
        
        Returns:
            ConfirmationLevel: 需要的確認等級
        """
        # 直接匹配
        if operation in self.DOUBLE_CONFIRM_OPERATIONS:
            return self.DOUBLE_CONFIRM_OPERATIONS[operation]
        
        # 模式匹配
        for key, level in self.DOUBLE_CONFIRM_OPERATIONS.items():
            if key in operation.lower():
                return level
        
        return ConfirmationLevel.NONE
    
    def create_pending(self, operation: str, description: str,
                     metadata: dict = None, requested_by: str = "agent") -> Optional[str]:
        """
        創建待確認操作
        
        Args:
            operation: 操作名稱
            description: 描述
            metadata: 額外元數據
            requested_by: 請求者
        
        Returns:
            confirmation_id if requires confirmation, None otherwise
        """
        level = self.requires_confirmation(operation)
        
        if level == ConfirmationLevel.NONE:
            return None
        
        # BLOCKED 操作直接返回特殊標記
        if level == ConfirmationLevel.BLOCKED:
            return "__BLOCKED__"
        
        pending = PendingConfirmation(
            confirmation_id=str(uuid.uuid4())[:8],
            operation=operation,
            description=description,
            level=level,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=self.timeout_minutes),
            metadata=metadata or {},
        )
        
        self.pending_confirmations.append(pending)
        return pending.confirmation_id
    
    def confirm(self, confirmation_id: str, confirmed_by: str) -> bool:
        """
        確認操作
        
        Args:
            confirmation_id: 確認 ID
            confirmed_by: 確認者
        
        Returns:
            bool: 是否成功確認
        """
        pending = self._find_pending(confirmation_id)
        if not pending:
            return False
        
        # 檢查是否過期
        if datetime.now() > pending.expires_at:
            pending.status = "expired"
            return False
        
        # 添加確認
        pending.confirmations.append(confirmed_by)
        
        # 檢查是否滿足確認要求
        if pending.level == ConfirmationLevel.SINGLE and len(pending.confirmations) >= 1:
            pending.status = "approved"
            return True
        
        if pending.level == ConfirmationLevel.DOUBLE and len(pending.confirmations) >= 2:
            pending.status = "approved"
            return True
        
        if pending.level == ConfirmationLevel.APPROVAL:
            # 需要人類審批
            # 這裡只是記錄，需要外部系統處理
            return True
        
        return False
    
    def reject(self, confirmation_id: str, rejected_by: str, reason: str = "") -> bool:
        """
        拒絕操作
        
        Args:
            confirmation_id: 確認 ID
            rejected_by: 拒絕者
            reason: 原因
        
        Returns:
            bool: 是否成功
        """
        pending = self._find_pending(confirmation_id)
        if not pending:
            return False
        
        pending.status = "rejected"
        pending.metadata["rejected_by"] = rejected_by
        pending.metadata["reject_reason"] = reason
        return True
    
    def _find_pending(self, confirmation_id: str) -> Optional[PendingConfirmation]:
        """找到待確認"""
        for p in self.pending_confirmations:
            if p.confirmation_id == confirmation_id and p.status == "pending":
                return p
        return None
    
    def is_approved(self, confirmation_id: str) -> bool:
        """檢查是否已批准"""
        pending = self._find_pending(confirmation_id)
        return pending and pending.status == "approved"
    
    def get_pending(self, operation: str = None) -> List[PendingConfirmation]:
        """取得待確認列表"""
        pending = [p for p in self.pending_confirmations if p.status == "pending"]
        if operation:
            pending = [p for p in pending if operation in p.operation]
        return pending
    
    def get_status(self, confirmation_id: str) -> Optional[dict]:
        """取得確認狀態"""
        pending = self._find_pending(confirmation_id)
        if not pending:
            # 可能在歷史中
            for p in self.pending_confirmations:
                if p.confirmation_id == confirmation_id:
                    return {
                        "confirmation_id": p.confirmation_id,
                        "operation": p.operation,
                        "status": p.status,
                        "confirmations": p.confirmations,
                        "created_at": p.created_at.isoformat(),
                    }
            return None
        
        return {
            "confirmation_id": pending.confirmation_id,
            "operation": pending.operation,
            "description": pending.description,
            "level": pending.level.value,
            "status": pending.status,
            "confirmations": pending.confirmations,
            "required": 1 if pending.level == ConfirmationLevel.SINGLE else 2,
            "created_at": pending.created_at.isoformat(),
            "expires_at": pending.expires_at.isoformat(),
        }
    
    def cleanup_expired(self):
        """清理過期的確認"""
        for p in self.pending_confirmations:
            if p.status == "pending" and datetime.now() > p.expires_at:
                p.status = "expired"


# 全域實例
_double_confirm = DoubleConfirmation()

def requires_confirmation(operation: str) -> ConfirmationLevel:
    """快速檢查操作是否需要確認"""
    return _double_confirm.requires_confirmation(operation)

def create_pending(operation: str, description: str, metadata: dict = None) -> Optional[str]:
    """快速創建待確認操作"""
    return _double_confirm.create_pending(operation, description, metadata)

def confirm(confirmation_id: str, confirmed_by: str) -> bool:
    """快速確認操作"""
    return _double_confirm.confirm(confirmation_id, confirmed_by)

def is_approved(confirmation_id: str) -> bool:
    """快速檢查是否已批准"""
    return _double_confirm.is_approved(confirmation_id)

def get_status(confirmation_id: str) -> Optional[dict]:
    """快速取得確認狀態"""
    return _double_confirm.get_status(confirmation_id)
