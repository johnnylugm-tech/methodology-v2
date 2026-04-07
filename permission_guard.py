#!/usr/bin/env python3
"""
PermissionGuard — 權限控制模組

功能：
- 危險操作攔截（rm, network, exec）
- 審批流程管理
- Sandbox 執行環境
- 操作日誌追蹤

用法：
    from permission_guard import PermissionGuard, Permission, Operation
    from permission_guard import ApprovalStatus
    
    pg = PermissionGuard()
    result = pg.check(Operation(file="~/.ssh/id_rsa"))
    if result.status == ApprovalStatus.DENIED:
        print("Denied")
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path


class Permission(Enum):
    """權限類型"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXEC_BASH = "exec_bash"
    NETWORK = "network"
    ENV_ACCESS = "env_access"
    EXTERNAL_API = "external_api"


class ApprovalStatus(Enum):
    """審批狀態"""
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"
    BLOCKED = "blocked"


@dataclass
class Operation:
    """操作描述"""
    type: str
    permission: Permission
    target: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalRequest:
    """審批請求"""
    operation: Operation
    requester: str
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = ""
    decided_at: Optional[str] = None
    approver: Optional[str] = None
    decision: Optional[str] = None  # 決定理由


# 危險模式
DANGEROUS_PATTERNS = {
    Permission.DELETE_FILE: [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+/(home|root|etc|var|usr|tmp|opt)",
        r"rm\s+-rf\s+\*",
        r"rm\s+-rf\s+~\/",
        r"del\s+/s/q\s+.*\*",
    ],
    Permission.EXEC_BASH: [
        r"curl\s+.*\|.*sh",
        r"wget\s+.*\|.*sh",
        r"eval\s+\$",
        r"exec\s+",
        r"fork\s+",
        r":\(\)\s*{",  # fork bomb
    ],
    Permission.NETWORK: [
        r"curl\s+https?://",
        r"wget\s+https?://",
        r"fetch\s+https?://",
        r"http\.request",
        r"requests\.get|requests\.post",
    ],
    Permission.ENV_ACCESS: [
        r"echo\s+\$?(ANTHROPIC|OPENAI|GITHUB|API).*",
        r"export\s+\w+=\$?\w+",
        r"os\.environ\.get",
    ],
}


@dataclass
class Rule:
    """權限規則"""
    permission: Permission
    allow: bool
    pattern: str = ""
    description: str = ""


class PermissionGuard:
    """
    權限守衛
    
    解決：
    - 危險操作自動攔截
    - 審批流程管理
    - 詳細日誌追蹤
    """
    
    # 預設允許的白名單
    ALLOW_PATTERNS = {
        Permission.READ_FILE: [
            r"^/Users/.*",
            r"^~/.*",
            r"^./.*",
        ],
        Permission.WRITE_FILE: [
            r"^./.*",
            r"^/tmp/.*",
        ],
        Permission.EXEC_BASH: [
            r"^git\s+",
            r"^python\s+",
            r"^ls\s+",
            r"^cd\s+",
            r"^echo\s+",
            r"^cat\s+",
            r"^grep\s+",
            r"^find\s+",
        ],
    }
    
    def __init__(self, state_path: str = ".methodology/state.json"):
        self.state_path = Path(state_path)
        self.pending_requests = []  # 待審批
        self.approval_history = []  # 審批歷史
        self.denied_count = 0
        self.approved_count = 0
    
    def check(self, operation: Operation) -> ApprovalRequest:
        """
        檢查操作是否允許
        
        Args:
            operation: 操作描述
            
        Returns:
            ApprovalRequest: 審批請求
        """
        request = ApprovalRequest(
            operation=operation,
            requester="system",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        
        # 檢查危險模式
        danger_result = self._check_dangerous(operation)
        if danger_result:
            request.status = ApprovalStatus.DENIED
            request.decision = f"Dangerous pattern detected: {danger_result}"
            self.denied_count += 1
            self._log(request)
            return request
        
        # 檢查允許模式
        allow_result = self._check_allow(operation)
        if allow_result:
            request.status = ApprovalStatus.APPROVED
            request.decision = f"Allowed by pattern: {allow_result}"
            self.approved_count += 1
            self._log(request)
            return request
        
        # 進入審批流程
        request.status = ApprovalStatus.PENDING
        self.pending_requests.append(request)
        self._log(request)
        
        return request
    
    def _check_dangerous(self, operation: Operation) -> Optional[str]:
        """檢查危險模式"""
        patterns = DANGEROUS_PATTERNS.get(operation.permission, [])
        
        for pattern in patterns:
            if re.search(pattern, operation.target, re.IGNORECASE):
                return pattern
        
        return None
    
    def _check_allow(self, operation: Operation) -> Optional[str]:
        """檢查允許模式"""
        patterns = self.ALLOW_PATTERNS.get(operation.permission, [])
        
        for pattern in patterns:
            if re.match(pattern, operation.target):
                return pattern
        
        return None
    
    def approve(self, request: ApprovalRequest, approver: str = "human") -> bool:
        """
        審批通過
        
        Args:
            request: 審批請求
            approver: 審批人
            
        Returns:
            bool: 是否成功
        """
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.APPROVED
        request.approver = approver
        request.decided_at = datetime.now(timezone.utc).isoformat()
        self.approved_count += 1
        self._log(request)
        
        return True
    
    def deny(self, request: ApprovalRequest, approver: str = "human", reason: str = "") -> bool:
        """
        審批拒絕
        
        Returns:
            bool: 是否成功
        """
        if request.status != ApprovalStatus.PENDING:
            return False
        
        request.status = ApprovalStatus.DENIED
        request.approver = approver
        request.decision = reason
        request.decided_at = datetime.now(timezone.utc).isoformat()
        self.denied_count += 1
        self._log(request)
        
        return True
    
    def block_all(self, reason: str = "Emergency block"):
        """
        緊急封鎖（HR-14 觸發時）
        """
        for request in self.pending_requests:
            request.status = ApprovalStatus.BLOCKED
            request.decision = reason
            request.decided_at = datetime.now(timezone.utc).isoformat()
            self._log(request)
        
        self.pending_requests.clear()
    
    def _log(self, request: ApprovalRequest):
        """寫入日誌"""
        log_entry = {
            "operation": {
                "type": request.operation.type,
                "permission": request.operation.permission.value,
                "target": request.operation.target
            },
            "status": request.status.value,
            "requester": request.requester,
            "approver": request.approver,
            "decision": request.decision,
            "created_at": request.created_at,
            "decided_at": request.decided_at
        }
        
        self.approval_history.append(log_entry)
        
        # 保存到 state.json
        self._save_state()
    
    def _save_state(self):
        """保存狀態"""
        if not self.state_path.exists():
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            state = {}
            if self.state_path.exists():
                state = json.loads(self.state_path.read_text())
            
            state["permission_guard"] = {
                "denied_count": self.denied_count,
                "approved_count": self.approved_count,
                "pending_count": len(self.pending_requests),
                "history": self.approval_history[-100:]  # 只存最近 100 條
            }
            
            self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        except Exception:
            pass
    
    def get_stats(self) -> Dict:
        """取得統計"""
        total = self.approved_count + self.denied_count
        approval_rate = self.approved_count / total if total > 0 else 0
        
        return {
            "approved": self.approved_count,
            "denied": self.denied_count,
            "pending": len(self.pending_requests),
            "approval_rate": approval_rate
        }


# CLI 介面
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PermissionGuard CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # check
    check_parser = subparsers.add_parser("check", help="Check operation")
    check_parser.add_argument("--type", required=True, help="Operation type")
    check_parser.add_argument("--permission", required=True, help="Permission type")
    check_parser.add_argument("--target", required=True, help="Target")
    
    # approve
    approve_parser = subparsers.add_parser("approve", help="Approve request")
    approve_parser.add_argument("--index", type=int, required=True, help="Request index")
    
    # deny
    deny_parser = subparsers.add_parser("deny", help="Deny request")
    deny_parser.add_argument("--index", type=int, required=True)
    deny_parser.add_argument("--reason", default="")
    
    # stats
    stats_parser = subparsers.add_parser("stats", help="Show stats")
    
    # block
    block_parser = subparsers.add_parser("block", help="Block all pending")
    block_parser.add_argument("--reason", default="Emergency")
    
    args = parser.parse_args()
    
    pg = PermissionGuard()
    
    if args.command == "check":
        perm = Permission(args.permission)
        op = Operation(type=args.type, permission=perm, target=args.target)
        result = pg.check(op)
        print(f"Status: {result.status.value}")
        print(f"Decision: {result.decision}")
    
    elif args.command == "approve":
        if 0 <= args.index < len(pg.pending_requests):
            pg.approve(pg.pending_requests[args.index])
            print("Approved")
    
    elif args.command == "deny":
        if 0 <= args.index < len(pg.pending_requests):
            pg.deny(pg.pending_requests[args.index], reason=args.reason)
            print("Denied")
    
    elif args.command == "stats":
        stats = pg.get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.command == "block":
        pg.block_all(args.reason)
        print(f"Blocked {len(pg.pending_requests)} requests")


if __name__ == "__main__":
    main()
