#!/usr/bin/env python3
"""
ApprovalFlow - 多級審批流程引擎

支援多級審批、條件審批、超時處理
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class ApprovalStatus(Enum):
    """審批狀態"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalLevel(Enum):
    """審批級別"""
    L1 = "l1"  # 組長
    L2 = "l2"  # 經理
    L3 = "l3"  # 總監
    L4 = "l4"  # VP
    FINAL = "final"  # 最終審批


@dataclass
class ApprovalRule:
    """審批規則"""
    id: str
    name: str
    description: str = ""
    
    # 審批級別
    levels: List[ApprovalLevel] = None  # 審批順序
    
    # 條件
    condition: Callable = None  # 何時需要這個審批
    threshold: float = None  # 門檻值
    
    # 配置
    auto_approve: bool = False  # 自動通過
    require_all: bool = True  # 是否需要全部批准
    
    # 超時
    timeout_hours: int = 24  # 超時小時數
    timeout_action: str = "escalate"  # expire, escalate, auto_approve
    
    def __post_init__(self):
        if self.levels is None:
            self.levels = [ApprovalLevel.L1]


@dataclass
class ApprovalStep:
    """審批步驟"""
    id: str
    level: ApprovalLevel
    approver: str  # 審批人 ID 或角色
    
    # 配置
    required: bool = True
    min_approvals: int = 1  # 最少需要的批准數
    
    # 狀態
    status: ApprovalStatus = ApprovalStatus.PENDING
    approvals: List[Dict] = field(default_factory=list)  # [{approver, status, comment, timestamp}]
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = None
    deadline: datetime = None
    
    # 配置
    timeout_hours: int = 24
    timeout_action: str = "escalate"


@dataclass
class ApprovalRequest:
    """審批請求"""
    id: str
    name: str
    description: str
    
    # 申請人
    requester: str
    requester_name: str = ""
    
    # 類型
    approval_type: str  # "code_review", "deployment", "budget", etc.
    
    # 內容
    resource_id: str = None  # 相關資源 ID
    resource_type: str = None  # 資源類型
    changes: Dict = field(default_factory=dict)  # 變更內容
    
    # 規則
    rule_id: str = None
    rule: ApprovalRule = None
    
    # 審批步驟
    steps: List[ApprovalStep] = field(default_factory=list)
    current_step_index: int = 0
    
    # 狀態
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # 上下文
    context: Dict = field(default_factory=dict)
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "approval_type": self.approval_type,
            "requester": self.requester,
            "status": self.status.value,
            "current_step": self.current_step_index + 1,
            "total_steps": len(self.steps),
            "created_at": self.created_at.isoformat(),
        }


class ApprovalFlow:
    """多級審批流程引擎"""
    
    def __init__(self):
        # 審批規則
        self.rules: Dict[str, ApprovalRule] = {}
        
        # 審批請求
        self.requests: Dict[str, ApprovalRequest] = {}
        
        # 待審批（按審批人索引）
        self.pending_by_approver: Dict[str, List[str]] = defaultdict(list)
        self.pending_by_level: Dict[ApprovalLevel, List[str]] = defaultdict(list)
        
        # 監聽器
        self.listeners: Dict[str, List[Callable]] = {
            "approval_created": [],
            "approval_completed": [],
            "approval_rejected": [],
            "approval_expired": [],
            "step_completed": [],
        }
        
        # 統計
        self.stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "expired": 0,
        }
        
        # 載入預設規則
        self._load_default_rules()
    
    def _load_default_rules(self):
        """載入預設審批規則"""
        # 代碼審查
        self.add_rule(
            name="Code Review",
            description="代碼審查批准",
            levels=[ApprovalLevel.L1, ApprovalLevel.L2],
            approval_type="code_review",
        )
        
        # 部署審批
        self.add_rule(
            name="Deployment",
            description="部署到生產環境",
            levels=[ApprovalLevel.L1, ApprovalLevel.L2, ApprovalLevel.L3],
            approval_type="deployment",
            timeout_hours=4,
        )
        
        # 預算審批
        self.add_rule(
            name="Budget",
            description="預算申請",
            levels=[ApprovalLevel.L1, ApprovalLevel.L2, ApprovalLevel.L3, ApprovalLevel.L4],
            approval_type="budget",
            threshold=10000,  # > 10000 需要 L4
        )
        
        # 小額審批
        self.add_rule(
            name="Small Budget",
            description="小額支出",
            levels=[ApprovalLevel.L1],
            approval_type="budget",
            threshold=1000,
            auto_approve=False,
        )
    
    def add_rule(self, name: str, description: str = "",
               levels: List[ApprovalLevel] = None,
               condition: Callable = None,
               threshold: float = None,
               approval_type: str = None,
               **config) -> str:
        """新增審批規則"""
        rule_id = f"rule-{len(self.rules) + 1}"
        
        rule = ApprovalRule(
            id=rule_id,
            name=name,
            description=description,
            levels=levels or [ApprovalLevel.L1],
            condition=condition,
            threshold=threshold,
            **config
        )
        
        self.rules[rule_id] = rule
        return rule_id
    
    def create_request(self, name: str, description: str,
                     requester: str, requester_name: str = "",
                     approval_type: str = None,
                     rule_id: str = None,
                     resource_id: str = None,
                     resource_type: str = None,
                     **context) -> str:
        """建立審批請求"""
        # 選擇規則
        rule = None
        if rule_id and rule_id in self.rules:
            rule = self.rules[rule_id]
        elif approval_type:
            # 根據類型查找
            for r in self.rules.values():
                if r.approval_type == approval_type:
                    rule = r
                    break
        
        if not rule:
            # 使用預設規則
            rule = self.rules.get("rule-1")
        
        request_id = f"approval-{uuid.uuid4().hex[:12]}"
        
        # 建立審批步驟
        steps = []
        for level in rule.levels:
            step = ApprovalStep(
                id=f"{request_id}-step-{len(steps)}",
                level=level,
                approver=self._get_default_approver(level),
                timeout_hours=rule.timeout_hours,
                timeout_action=rule.timeout_action,
            )
            
            if rule.timeout_hours:
                step.deadline = step.created_at + timedelta(hours=rule.timeout_hours)
            
            steps.append(step)
        
        request = ApprovalRequest(
            id=request_id,
            name=name,
            description=description,
            requester=requester,
            requester_name=requester_name,
            approval_type=approval_type or "general",
            rule_id=rule.id if rule else None,
            rule=rule,
            steps=steps,
            resource_id=resource_id,
            resource_type=resource_type,
            context=context,
        )
        
        self.requests[request_id] = request
        self.stats["total_requests"] += 1
        
        # 更新索引
        self._update_indices(request)
        
        # 通知監聽器
        self._notify("approval_created", request)
        
        return request_id
    
    def approve(self, request_id: str, approver: str,
              comment: str = "", level: ApprovalLevel = None) -> bool:
        """批准"""
        request = self.requests.get(request_id)
        if not request:
            return False
        
        # 找到當前步驟
        if level:
            # 指定級別批准
            step_index = next((i for i, s in enumerate(request.steps) if s.level == level), None)
        else:
            step_index = request.current_step_index
        
        if step_index is None or step_index >= len(request.steps):
            return False
        
        step = request.steps[step_index]
        
        # 檢查是否已經批准
        if any(a["approver"] == approver for a in step.approvals):
            return False  # 已經批准過
        
        # 記錄批准
        step.approvals.append({
            "approver": approver,
            "status": ApprovalStatus.APPROVED,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        })
        
        # 檢查是否完成當前步驟
        if len(step.approvals) >= step.min_approvals:
            step.status = ApprovalStatus.APPROVED
            step.completed_at = datetime.now()
            
            # 移動到下一步
            if request.current_step_index < len(request.steps) - 1:
                request.current_step_index += 1
            else:
                # 所有步驟完成
                request.status = ApprovalStatus.APPROVED
                request.completed_at = datetime.now()
                self.stats["approved"] += 1
                self._notify("approval_completed", request)
        
        # 更新索引
        self._update_indices(request)
        
        return True
    
    def reject(self, request_id: str, approver: str,
             comment: str = "", level: ApprovalLevel = None) -> bool:
        """拒絕"""
        request = self.requests.get(request_id)
        if not request:
            return False
        
        step_index = level and next((i for i, s in enumerate(request.steps) if s.level == level), None)
        if step_index is None:
            step_index = request.current_step_index
        
        if step_index >= len(request.steps):
            return False
        
        step = request.steps[step_index]
        
        # 記錄拒絕
        step.approvals.append({
            "approver": approver,
            "status": ApprovalStatus.REJECTED,
            "comment": comment,
            "timestamp": datetime.now().isoformat(),
        })
        
        step.status = ApprovalStatus.REJECTED
        step.completed_at = datetime.now()
        request.status = ApprovalStatus.REJECTED
        request.completed_at = datetime.now()
        
        self.stats["rejected"] += 1
        self._notify("approval_rejected", request)
        
        # 更新索引
        self._update_indices(request)
        
        return True
    
    def cancel(self, request_id: str) -> bool:
        """取消"""
        request = self.requests.get(request_id)
        if not request:
            return False
        
        request.status = ApprovalStatus.CANCELLED
        request.completed_at = datetime.now()
        
        # 更新索引
        self._update_indices(request)
        
        return True
    
    def check_timeout(self) -> List[str]:
        """檢查超時"""
        expired = []
        now = datetime.now()
        
        for request in self.requests.values():
            if request.status != ApprovalStatus.PENDING:
                continue
            
            current_step = request.steps[request.current_step_index]
            
            if current_step.deadline and now > current_step.deadline:
                if current_step.timeout_action == "expire":
                    current_step.status = ApprovalStatus.EXPIRED
                    request.status = ApprovalStatus.EXPIRED
                    request.completed_at = now
                    expired.append(request.id)
                    self.stats["expired"] += 1
                    self._notify("approval_expired", request)
                
                elif current_step.timeout_action == "escalate":
                    # 升級到下一級
                    if request.current_step_index < len(request.steps) - 1:
                        request.current_step_index += 1
        
        return expired
    
    def get_pending(self, approver: str = None) -> List[Dict]:
        """取得待審批"""
        if approver:
            request_ids = self.pending_by_approver.get(approver, [])
            return [self.requests[rid].to_dict() for rid in request_ids if rid in self.requests]
        
        pending = []
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING:
                pending.append(request.to_dict())
        
        return pending
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """取得審批請求"""
        return self.requests.get(request_id)
    
    def subscribe(self, event: str, callback: Callable):
        """訂閱事件"""
        if event in self.listeners:
            self.listeners[event].append(callback)
    
    def _notify(self, event: str, data: Any):
        """通知監聽器"""
        for callback in self.listeners.get(event, []):
            try:
                callback(data)
            except Exception:
                pass
    
    def _update_indices(self, request: ApprovalRequest):
        """更新索引"""
        # 清除舊索引
        for step in request.steps:
            if step.approver in self.pending_by_approver:
                if request.id in self.pending_by_approver[step.approver]:
                    self.pending_by_approver[step.approver].remove(request.id)
            
            if step.level in self.pending_by_level:
                if request.id in self.pending_by_level[step.level]:
                    self.pending_by_level[step.level].remove(request.id)
        
        # 如果還在審批中，加入索引
        if request.status == ApprovalStatus.PENDING:
            current_step = request.steps[request.current_step_index]
            if current_step.status == ApprovalStatus.PENDING:
                self.pending_by_approver[current_step.approver].append(request.id)
                self.pending_by_level[current_step.level].append(request.id)
    
    def _get_default_approver(self, level: ApprovalLevel) -> str:
        """取得預設審批人"""
        level_approvers = {
            ApprovalLevel.L1: "lead",
            ApprovalLevel.L2: "manager",
            ApprovalLevel.L3: "director",
            ApprovalLevel.L4: "vp",
            ApprovalLevel.FINAL: "ceo",
        }
        return level_approvers.get(level, "admin")
    
    def get_statistics(self) -> Dict:
        """取得統計"""
        return {
            "total_requests": self.stats["total_requests"],
            "approved": self.stats["approved"],
            "rejected": self.stats["rejected"],
            "expired": self.stats["expired"],
            "pending": sum(1 for r in self.requests.values() if r.status == ApprovalStatus.PENDING),
            "rules_count": len(self.rules),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        stats = self.get_statistics()
        
        report = f"""
# ✅ ApprovalFlow 報告

## 統計

| 指標 | 數值 |
|------|------|
| 總請求數 | {stats['total_requests']} |
| 待審批 | {stats['pending']} |
| 已批准 | {stats['approved']} |
| 已拒絕 | {stats['rejected']} |
| 已過期 | {stats['expired']} |
| 規則數 | {stats['rules_count']} |

---

## 審批規則

| 規則 | 審批級別 |
|------|----------|
"""
        
        for rule_id, rule in self.rules.items():
            levels = " → ".join([l.value.upper() for l in rule.levels])
            report += f"| {rule.name} | {levels} |\n"
        
        report += f"""

## 待審批列表

| ID | 名稱 | 類型 | 申請人 | 當前步驟 |
|------|------|------|--------|----------|
"""
        
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING:
                current = request.current_step_index + 1
                total = len(request.steps)
                report += f"| {request.id} | {request.name} | {request.approval_type} | {request.requester_name or request.requester} | {current}/{total} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    flow = ApprovalFlow()
    
    print("=== Rules ===")
    for rule_id, rule in flow.rules.items():
        print(f"{rule.name}: {[l.value for l in rule.levels]}")
    
    print("\n=== Creating Approval Request ===")
    
    # 代碼審查
    req_id = flow.create_request(
        name="登入功能代碼審查",
        description="請審查登入功能的代碼變更",
        requester="dev-1",
        requester_name="大明",
        approval_type="code_review",
        resource_id="login-module",
        resource_type="code",
    )
    print(f"Created: {req_id}")
    
    print("\n=== Pending Approvals ===")
    pending = flow.get_pending()
    print(f"Pending count: {len(pending)}")
    
    print("\n=== Approving ===")
    
    # L1 批准
    result = flow.approve(req_id, "lead", comment="LGTM")
    print(f"L1 approve: {result}")
    
    # L2 批准
    result = flow.approve(req_id, "manager", comment="看起來不錯")
    print(f"L2 approve: {result}")
    
    # 檢查狀態
    request = flow.get_request(req_id)
    print(f"Final status: {request.status.value}")
    
    # 統計
    print("\n=== Statistics ===")
    stats = flow.get_statistics()
    print(f"Approved: {stats['approved']}")
    print(f"Pending: {stats['pending']}")
    
    # 報告
    print("\n=== Report ===")
    print(flow.generate_report())
