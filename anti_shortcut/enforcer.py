#!/usr/bin/env python3
"""
Anti-Shortcut Enforcer - 防範捷徑系統

目標：讓走捷徑變得更困難

捷徑防範規則：
1. 每個 commit 必須有 task_id
2. 每個 task 必須有對應的 test
3. 錯誤必須被分類和確認
4. 批准者 != 操作者
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Set
from datetime import datetime
import re


class ViolationType(Enum):
    """違規模式"""
    COMMIT_WITHOUT_TASK = "commit_without_task"
    TASK_WITHOUT_TEST = "task_without_test"
    ERROR_NOT_ACKNOWLEDGED = "error_not_acknowledged"
    SELF_APPROVAL = "self_approval"
    SKIP_GATE = "skip_gate"
    BYPASS_SECURITY = "bypass_security"


@dataclass
class Violation:
    """違規記錄"""
    violation_id: str
    type: ViolationType
    description: str
    task_id: Optional[str]
    agent_id: str
    timestamp: datetime
    severity: str  # critical, warning
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AntiShortcutEnforcer:
    """
    防範捷徑
    
    功能：
    - 追蹤 task_id 與 commit 的對應
    - 確保每個 task 有對應測試
    - 檢查錯誤確認
    - 防止自己批准自己
    """
    
    def __init__(self):
        self.commits: Dict[str, str] = {}  # commit_id -> task_id
        self.tasks: Dict[str, Dict] = {}    # task_id -> {tests: [], status: }
        self.violations: List[Violation] = []
        self._task_id_pattern = re.compile(r'\[[A-Z]+-\d+\]|\bTASK-\d+\b')
    
    def check_commit_message(self, commit_message: str, commit_id: str = None) -> List[Violation]:
        """
        檢查 commit message 是否包含 task_id
        
        Args:
            commit_message: commit message
            commit_id: commit ID
        
        Returns:
            List of violations if any
        """
        violations = []
        
        # 檢查是否包含 task_id
        if not self._task_id_pattern.search(commit_message):
            violation = Violation(
                violation_id=f"vio-{len(self.violations)}",
                type=ViolationType.COMMIT_WITHOUT_TASK,
                description="Commit message must contain task_id (e.g., [TASK-123])",
                task_id=None,
                agent_id="system",
                timestamp=datetime.now(),
                severity="critical"
            )
            violations.append(violation)
            self.violations.append(violation)
        
        # 記錄 commit 與 task_id 的對應
        if commit_id:
            task_ids = self._task_id_pattern.findall(commit_message)
            for task_id in task_ids:
                self.commits[commit_id] = task_id
        
        return violations
    
    def register_task(self, task_id: str, task_type: str = "development"):
        """
        註冊任務
        
        Args:
            task_id: 任務 ID
            task_type: 任務類型
        """
        self.tasks[task_id] = {
            "task_id": task_id,
            "type": task_type,
            "tests": [],
            "status": "open",
            "created_at": datetime.now(),
        }
    
    def register_test(self, task_id: str, test_id: str):
        """
        註冊任務的測試
        
        Args:
            task_id: 任務 ID
            test_id: 測試 ID
        """
        if task_id in self.tasks:
            self.tasks[task_id]["tests"].append(test_id)
    
    def check_task_has_test(self, task_id: str) -> bool:
        """
        檢查任務是否有對應測試
        
        Args:
            task_id: 任務 ID
        
        Returns:
            bool: 是否有測試
        """
        if task_id not in self.tasks:
            return False
        
        return len(self.tasks[task_id]["tests"]) > 0
    
    def check_self_approval(self, approver_id: str, operator_id: str) -> bool:
        """
        檢查是否是自己批准自己
        
        Args:
            approver_id: 批准者 ID
            operator_id: 操作者 ID
        
        Returns:
            bool: True if self-approval (violation)
        """
        if approver_id == operator_id:
            violation = Violation(
                violation_id=f"vio-{len(self.violations)}",
                type=ViolationType.SELF_APPROVAL,
                description=f"Self-approval detected: {approver_id} approving their own operation",
                task_id=None,
                agent_id=operator_id,
                timestamp=datetime.now(),
                severity="critical"
            )
            self.violations.append(violation)
            return True
        return False
    
    def acknowledge_violation(self, violation_id: str, acknowledged_by: str) -> bool:
        """
        確認違規（需要人工確認）
        
        Args:
            violation_id: 違規 ID
            acknowledged_by: 確認者
        
        Returns:
            bool: 是否成功
        """
        for v in self.violations:
            if v.violation_id == violation_id:
                v.acknowledged = True
                v.acknowledged_by = acknowledged_by
                v.acknowledged_at = datetime.now()
                return True
        return False
    
    def get_unacknowledged_violations(self) -> List[Violation]:
        """取得未確認的違規"""
        return [v for v in self.violations if not v.acknowledged]
    
    def get_violation_summary(self) -> dict:
        """取得違規摘要"""
        unack = self.get_unacknowledged_violations()
        by_type = {}
        for v in self.violations:
            by_type.setdefault(v.type.value, 0)
            by_type[v.type.value] += 1
        
        return {
            "total": len(self.violations),
            "unacknowledged": len(unack),
            "by_type": by_type,
            "critical_unacknowledged": sum(1 for v in unack if v.severity == "critical"),
        }
    
    def get_task_coverage(self) -> dict:
        """取得任務覆蓋率"""
        total_tasks = len(self.tasks)
        tasks_with_tests = sum(1 for t in self.tasks.values() if len(t["tests"]) > 0)
        
        return {
            "total_tasks": total_tasks,
            "tasks_with_tests": tasks_with_tests,
            "coverage": f"{(tasks_with_tests/total_tasks*100):.1f}%" if total_tasks > 0 else "N/A",
        }
