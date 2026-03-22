#!/usr/bin/env python3
"""
Recovery Controller - 災難恢復控制中心

功能：
- 失敗偵測
- 恢復計劃生成
- 自動/手動恢復執行
- 人類通知
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import uuid
import traceback

class FailureType(Enum):
    """失敗類型"""
    TRANSIENT = "transient"           # 短暫錯誤（網路、限流）
    LLM_RECOVERABLE = "llm_recoverable"  # LLM 可恢復
    USER_FIXABLE = "user_fixable"    # 用戶可修復
    SYSTEM_BUG = "system_bug"        # 系統 bug
    HARDWARE = "hardware"             # 硬體故障
    UNKNOWN = "unknown"               # 未知

class FailureSeverity(Enum):
    """嚴重程度"""
    LOW = "low"       # 可以忽略
    MEDIUM = "medium"  # 需要關注
    HIGH = "high"     # 需要介入
    CRITICAL = "critical"  # 災難性

@dataclass
class FailureReport:
    """失敗報告"""
    failure_id: str
    agent_id: str
    task_id: str
    failure_type: FailureType
    severity: FailureSeverity
    message: str
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Dict = field(default_factory=dict)
    occurred_at: datetime = field(default=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "failure_id": self.failure_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "failure_type": self.failure_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "exception": self.exception,
            "occurred_at": self.occurred_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

@dataclass
class RecoveryStep:
    """恢復步驟"""
    step_id: str
    description: str
    action_type: str  # retry, rollback, escalate, notify, wait
    target_state: Optional[Dict] = None
    rollback_action: Optional[str] = None
    estimated_duration: int = 0  # 秒

@dataclass
class RecoveryPlan:
    """恢復計劃"""
    plan_id: str
    failure_id: str
    steps: List[RecoveryStep]
    auto_executable: bool = False
    requires_human_approval: bool = False
    estimated_total_time: int = 0  # 秒
    success_probability: float = 0.0  # 0.0 - 1.0
    created_at: datetime = field(default=datetime.now)

class RecoveryController:
    """
    災難恢復控制中心
    
    功能：
    - 失敗偵測與分類
    - 恢復計劃生成
    - 自動/手動恢復執行
    - 人類通知
    """
    
    def __init__(self, notification_handler: Callable = None):
        self.failures: Dict[str, FailureReport] = {}
        self.plans: Dict[str, RecoveryPlan] = {}
        self.notification_handler = notification_handler  # 通知回調
        
        # 恢復策略
        self.recovery_strategies: Dict[FailureType, Callable] = {
            FailureType.TRANSIENT: self._recover_transient,
            FailureType.LLM_RECOVERABLE: self._recover_llm,
            FailureType.USER_FIXABLE: self._recover_user_fixable,
            FailureType.SYSTEM_BUG: self._recover_system_bug,
            FailureType.HARDWARE: self._recover_hardware,
        }
    
    def detect_failure(self, agent_id: str, task_id: str, exception: Exception,
                       context: Dict = None) -> FailureReport:
        """
        偵測失敗並分類
        
        Args:
            agent_id: Agent ID
            task_id: 任務 ID
            exception: 異常對象
            context: 額外上下文
        
        Returns:
            FailureReport: 失敗報告
        """
        failure_id = f"fail-{uuid.uuid4().hex[:12]}"
        
        # 分類失敗類型
        failure_type = self._classify_failure(exception)
        severity = self._determine_severity(failure_type, exception)
        
        report = FailureReport(
            failure_id=failure_id,
            agent_id=agent_id,
            task_id=task_id,
            failure_type=failure_type,
            severity=severity,
            message=str(exception),
            exception=type(exception).__name__,
            stack_trace=traceback.format_exc(),
            context=context or {},
        )
        
        self.failures[failure_id] = report
        
        # 通知（如果是高嚴重性）
        if severity in [FailureSeverity.HIGH, FailureSeverity.CRITICAL]:
            self._notify_failure(report)
        
        return report
    
    def _classify_failure(self, exception: Exception) -> FailureType:
        """分類失敗類型"""
        exc_type = type(exception).__name__.lower()
        exc_msg = str(exception).lower()
        
        # 瞬態錯誤
        if any(kw in exc_msg for kw in ["timeout", "connection", "503", "rate limit", "429", "network"]):
            return FailureType.TRANSIENT
        
        # LLM 可恢復
        if any(kw in exc_msg for kw in ["tool", "parse", "json", "output", "invalid"]):
            return FailureType.LLM_RECOVERABLE
        
        # 用戶可修復
        if any(kw in exc_msg for kw in ["input", "missing", "required", "permission"]):
            return FailureType.USER_FIXABLE
        
        # 硬體/系統
        if any(kw in exc_type for kw in ["memory", "disk", "cpu", "hardware", "fatal"]):
            return FailureType.HARDWARE
        
        # 系統 bug
        if any(kw in exc_type for kw in ["assertion", "attributeerror", "typeerror", "valueerror"]):
            return FailureType.SYSTEM_BUG
        
        return FailureType.UNKNOWN
    
    def _determine_severity(self, failure_type: FailureType, exception: Exception) -> FailureSeverity:
        """確定嚴重程度"""
        severity_map = {
            FailureType.TRANSIENT: FailureSeverity.LOW,
            FailureType.LLM_RECOVERABLE: FailureSeverity.MEDIUM,
            FailureType.USER_FIXABLE: FailureSeverity.MEDIUM,
            FailureType.SYSTEM_BUG: FailureSeverity.HIGH,
            FailureType.HARDWARE: FailureSeverity.CRITICAL,
            FailureType.UNKNOWN: FailureSeverity.MEDIUM,
        }
        return severity_map.get(failure_type, FailureSeverity.MEDIUM)
    
    def _notify_failure(self, report: FailureReport):
        """通知失敗"""
        if self.notification_handler:
            self.notification_handler(report)
    
    def create_recovery_plan(self, failure_id: str) -> Optional[RecoveryPlan]:
        """
        建立恢復計劃
        
        Args:
            failure_id: 失敗報告 ID
        
        Returns:
            RecoveryPlan: 恢復計劃，如果失敗不存在則返回 None
        """
        report = self.failures.get(failure_id)
        if not report:
            return None
        
        # 根據失敗類型獲取策略
        strategy = self.recovery_strategies.get(report.failure_type)
        if not strategy:
            return None
        
        # 生成計劃
        plan = strategy(report)
        plan.failure_id = failure_id
        
        self.plans[plan.plan_id] = plan
        
        # 如果需要人類批准，通知
        if plan.requires_human_approval:
            self._notify_plan_requires_approval(plan, report)
        
        return plan
    
    def _recover_transient(self, report: FailureReport) -> RecoveryPlan:
        """瞬態錯誤恢復策略"""
        return RecoveryPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:12]}",
            failure_id=report.failure_id,
            steps=[
                RecoveryStep(
                    step_id=f"step-1",
                    description="等待 5 秒",
                    action_type="wait",
                    estimated_duration=5,
                ),
                RecoveryStep(
                    step_id=f"step-2",
                    description="重試操作",
                    action_type="retry",
                    estimated_duration=30,
                ),
                RecoveryStep(
                    step_id=f"step-3",
                    description="如果仍然失敗，指標誌並上報",
                    action_type="escalate",
                    estimated_duration=10,
                ),
            ],
            auto_executable=True,
            requires_human_approval=False,
            estimated_total_time=45,
            success_probability=0.8,
        )
    
    def _recover_llm(self, report: FailureReport) -> RecoveryPlan:
        """LLM 可恢復錯誤策略"""
        return RecoveryPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:12]}",
            failure_id=report.failure_id,
            steps=[
                RecoveryStep(
                    step_id=f"step-1",
                    description="記錄錯誤並反饋給 LLM",
                    action_type="notify",
                    estimated_duration=5,
                ),
                RecoveryStep(
                    step_id=f"step-2",
                    description="讓 LLM 重新生成",
                    action_type="retry",
                    estimated_duration=60,
                ),
                RecoveryStep(
                    step_id=f"step-3",
                    description="驗證新輸出",
                    action_type="rollback",
                    estimated_duration=30,
                ),
            ],
            auto_executable=True,
            requires_human_approval=False,
            estimated_total_time=95,
            success_probability=0.7,
        )
    
    def _recover_user_fixable(self, report: FailureReport) -> RecoveryPlan:
        """用戶可修復錯誤策略"""
        return RecoveryPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:12]}",
            failure_id=report.failure_id,
            steps=[
                RecoveryStep(
                    step_id=f"step-1",
                    description="暫停並通知用戶",
                    action_type="notify",
                    estimated_duration=5,
                ),
                RecoveryStep(
                    step_id=f"step-2",
                    description="等待用戶提供必要訊息",
                    action_type="wait",
                    estimated_duration=300,  # 等待 5 分鐘
                ),
                RecoveryStep(
                    step_id=f"step-3",
                    description="用戶提供後繼續執行",
                    action_type="retry",
                    estimated_duration=60,
                ),
            ],
            auto_executable=False,
            requires_human_approval=True,
            estimated_total_time=365,
            success_probability=0.9,
        )
    
    def _recover_system_bug(self, report: FailureReport) -> RecoveryPlan:
        """系統 bug 策略"""
        return RecoveryPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:12]}",
            failure_id=report.failure_id,
            steps=[
                RecoveryStep(
                    step_id=f"step-1",
                    description="記錄詳細錯誤信息",
                    action_type="notify",
                    estimated_duration=10,
                ),
                RecoveryStep(
                    step_id=f"step-2",
                    description="回滾到最後穩定狀態",
                    action_type="rollback",
                    estimated_duration=60,
                ),
                RecoveryStep(
                    step_id=f"step-3",
                    description="通知開發團隊",
                    action_type="escalate",
                    estimated_duration=15,
                ),
            ],
            auto_executable=False,
            requires_human_approval=True,
            estimated_total_time=85,
            success_probability=0.6,
        )
    
    def _recover_hardware(self, report: FailureReport) -> RecoveryPlan:
        """硬體故障策略"""
        return RecoveryPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:12]}",
            failure_id=report.failure_id,
            steps=[
                RecoveryStep(
                    step_id=f"step-1",
                    description="緊急通知",
                    action_type="notify",
                    estimated_duration=5,
                ),
                RecoveryStep(
                    step_id=f"step-2",
                    description="保存所有狀態到磁碟",
                    action_type="rollback",
                    estimated_duration=120,
                ),
                RecoveryStep(
                    step_id=f"step-3",
                    description="等待硬體恢復",
                    action_type="wait",
                    estimated_duration=600,
                ),
                RecoveryStep(
                    step_id=f"step-4",
                    description="重新初始化並恢復",
                    action_type="retry",
                    estimated_duration=180,
                ),
            ],
            auto_executable=False,
            requires_human_approval=True,
            estimated_total_time=905,
            success_probability=0.5,
        )
    
    def _notify_plan_requires_approval(self, plan: RecoveryPlan, report: FailureReport):
        """通知計劃需要批准"""
        if self.notification_handler:
            self.notification_handler({
                "type": "recovery_plan_requires_approval",
                "plan": plan,
                "failure": report,
            })
    
    def execute_recovery(self, plan_id: str, approved: bool = False) -> dict:
        """
        執行恢復計劃
        
        Args:
            plan_id: 計劃 ID
            approved: 是否已獲得批准
        
        Returns:
            執行結果
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}
        
        report = self.failures.get(plan.failure_id)
        
        # 檢查是否需要批准
        if plan.requires_human_approval and not approved:
            return {
                "status": "pending_approval",
                "plan_id": plan_id,
                "message": "This plan requires human approval"
            }
        
        # 執行步驟（這裡只是模擬）
        results = []
        for step in plan.steps:
            results.append({
                "step_id": step.step_id,
                "status": "executed",
                "description": step.description,
            })
        
        # 更新失敗狀態
        if report:
            report.resolved = True
            report.resolved_at = datetime.now()
        
        return {
            "status": "completed",
            "plan_id": plan_id,
            "steps_executed": len(results),
            "results": results,
        }
    
    def get_failure_history(self, agent_id: str = None, limit: int = 100) -> List[FailureReport]:
        """取得失敗歷史"""
        failures = list(self.failures.values())
        
        if agent_id:
            failures = [f for f in failures if f.agent_id == agent_id]
        
        # 按時間排序
        failures.sort(key=lambda x: x.occurred_at, reverse=True)
        
        return failures[:limit]
    
    def get_active_failures(self) -> List[FailureReport]:
        """取得未解決的失敗"""
        return [f for f in self.failures.values() if not f.resolved]
    
    def get_recovery_status(self) -> dict:
        """取得恢復狀態"""
        total_failures = len(self.failures)
        resolved_failures = sum(1 for f in self.failures.values() if f.resolved)
        active_plans = len([p for p in self.plans.values() if p.requires_human_approval])
        
        return {
            "total_failures": total_failures,
            "resolved_failures": resolved_failures,
            "active_failures": total_failures - resolved_failures,
            "pending_approval_plans": active_plans,
            "by_type": {
                ft.value: sum(1 for f in self.failures.values() if f.failure_type == ft)
                for ft in FailureType
            },
            "by_severity": {
                sv.value: sum(1 for f in self.failures.values() if f.severity == sv)
                for sv in FailureSeverity
            },
        }
