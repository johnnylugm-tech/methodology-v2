#!/usr/bin/env python3
"""
Verification Gates - 驗證關卡

AI-native 特點：
- 條件觸發，不阻礙流程
- 自動檢查，不增加負擔

使用方法：
    from verification_gate import VerificationGates, Gate, GateStatus

    # 基本用法
    gates = VerificationGates()
    gates.register_gate("task_created", Gate("任務建立", required_output="task_spec"))
    gates.gate_sequence = ["task_created"]

    result = gates.execute_sequence({"task_spec": {"title": "Test"}})
    print(gates.get_status())
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime


class GateStatus(Enum):
    """關卡狀態枚舉"""
    NOT_REACHED = "not_reached"
    PASSED = "passed"
    FAILED = "failed"
    BYPASSED = "bypassed"


class Gate:
    """單一驗證關卡

    Attributes:
        name: 關卡名稱
        required_output: 需要的產出鍵
        validator: 自定義驗證函數
        auto_pass: 是否自動通過
        status: 當前狀態
        verified_at: 驗證時間
        evidence: 驗證證據
    """

    def __init__(
        self,
        name: str,
        required_output: str = None,
        validator: Callable = None,
        auto_pass: bool = False
    ):
        self.name = name
        self.required_output = required_output
        self.validator = validator
        self.auto_pass = auto_pass
        self.status = GateStatus.NOT_REACHED
        self.verified_at: Optional[datetime] = None
        self.evidence: Optional[Any] = None

    def check(self, context: dict) -> bool:
        """檢查關卡是否通過

        Args:
            context: 執行上下文，包含各階段產出

        Returns:
            bool: 關卡是否通過
        """
        if self.auto_pass:
            self.status = GateStatus.PASSED
            self.verified_at = datetime.now()
            self.evidence = {"auto_pass": True}
            return True

        if self.validator:
            try:
                result = self.validator(context)
                self.status = GateStatus.PASSED if result else GateStatus.FAILED
                self.verified_at = datetime.now()
                self.evidence = {"validator_result": result}
                return result
            except Exception as e:
                self.status = GateStatus.FAILED
                self.verified_at = datetime.now()
                self.evidence = {"error": str(e)}
                return False

        # 檢查 required_output
        if self.required_output:
            if self.required_output in context:
                self.status = GateStatus.PASSED
                self.verified_at = datetime.now()
                self.evidence = {"output_found": self.required_output}
                return True
            else:
                self.status = GateStatus.NOT_REACHED
                return False

        return False

    def bypass(self, reason: str = None):
        """手動繞過關卡"""
        self.status = GateStatus.BYPASSED
        self.verified_at = datetime.now()
        self.evidence = {"bypass_reason": reason or "manual_bypass"}

    def reset(self):
        """重置關卡狀態"""
        self.status = GateStatus.NOT_REACHED
        self.verified_at = None
        self.evidence = None


class VerificationGates:
    """驗證關卡管理器

    管理多個關卡的註冊、執行和狀態追蹤。

    Attributes:
        gates: 已註冊的關卡字典
        gate_sequence: 關卡執行順序
    """

    # 預設關卡定義工廠
    DEFAULT_GATES = {
        "task_created": {
            "name": "任務建立",
            "required_output": "task_spec",
            "auto_pass": False
        },
        "agent_assigned": {
            "name": "分派代理",
            "required_output": "assignment",
            "auto_pass": False
        },
        "output_generated": {
            "name": "產出產生",
            "required_output": "result",
            "auto_pass": False
        },
        "quality_check": {
            "name": "品質檢查",
            "auto_pass": False
        },
        "human_approved": {
            "name": "人類審批",
            "required_output": "approval",
            "auto_pass": False
        },
        "completed": {
            "name": "任務完成",
            "required_output": "final_result",
            "auto_pass": False
        },
    }

    def __init__(self):
        self.gates: Dict[str, Gate] = {}
        self.gate_sequence: List[str] = []

    def register_gate(self, gate_id: str, gate: Gate):
        """註冊關卡

        Args:
            gate_id: 關卡唯一識別符
            gate: Gate 實例
        """
        self.gates[gate_id] = gate

    def register_default_gates(self, gate_ids: List[str] = None):
        """註冊預設關卡

        Args:
            gate_ids: 要註冊的關卡 ID 列表，None 表示全部
        """
        if gate_ids is None:
            gate_ids = list(self.DEFAULT_GATES.keys())

        for gate_id in gate_ids:
            if gate_id in self.DEFAULT_GATES:
                config = self.DEFAULT_GATES[gate_id]
                self.register_gate(
                    gate_id,
                    Gate(
                        name=config["name"],
                        required_output=config.get("required_output"),
                        auto_pass=config.get("auto_pass", False)
                    )
                )

    def execute_sequence(self, context: dict) -> dict:
        """執行所有關卡

        Args:
            context: 執行上下文

        Returns:
            dict: 各關卡執行結果
        """
        results = {}
        for gate_id in self.gate_sequence:
            gate = self.gates.get(gate_id)
            if gate:
                results[gate_id] = gate.check(context)
        return results

    def check_gate(self, gate_id: str, context: dict) -> bool:
        """檢查單一關卡

        Args:
            gate_id: 關卡 ID
            context: 執行上下文

        Returns:
            bool: 關卡是否通過
        """
        gate = self.gates.get(gate_id)
        if not gate:
            return False
        return gate.check(context)

    def get_status(self) -> dict:
        """取得所有關卡狀態

        Returns:
            dict: 各關卡的詳細狀態
        """
        return {
            gate_id: {
                "name": gate.name,
                "status": gate.status.value,
                "verified_at": gate.verified_at.isoformat() if gate.verified_at else None,
                "evidence": gate.evidence
            }
            for gate_id, gate in self.gates.items()
        }

    def get_passed_count(self) -> int:
        """取得已通過關卡數"""
        return sum(1 for g in self.gates.values() if g.status == GateStatus.PASSED)

    def get_failed_count(self) -> int:
        """取得失敗關卡數"""
        return sum(1 for g in self.gates.values() if g.status == GateStatus.FAILED)

    def reset_all(self):
        """重置所有關卡"""
        for gate in self.gates.values():
            gate.reset()


class HITLGates(VerificationGates):
    """HITL 專用關卡流程

    適用於需要人類審批的工作流。
    """

    def __init__(self):
        super().__init__()
        # HITL 標配流程：建立 -> 產出 -> 審批 -> 完成
        self.gate_sequence = [
            "task_created",
            "output_generated",
            "human_approved",
            "completed"
        ]
        self.register_default_gates(self.gate_sequence)


class AutonomousGates(VerificationGates):
    """全自動關卡流程

    適用於不需要人類審批的工作流。
    """

    def __init__(self):
        super().__init__()
        self.gate_sequence = [
            "task_created",
            "agent_assigned",
            "output_generated",
            "quality_check",
            "completed"
        ]
        self.register_default_gates(self.gate_sequence)


# ============================================================================
# 範例與測試
# ============================================================================

if __name__ == "__main__":
    print("=== Verification Gates Demo ===\n")

    # 基本範例
    gates = VerificationGates()
    gates.register_gate("task_created", Gate("任務建立", required_output="task_spec"))
    gates.register_gate("output_generated", Gate("產出產生", required_output="result"))
    gates.gate_sequence = ["task_created", "output_generated"]

    # 測試上下文
    context = {
        "task_spec": {"title": "Test Task", "id": "task-1"},
        "result": {"output": "Generated content"}
    }

    results = gates.execute_sequence(context)
    print("Execution results:", results)
    print("\nGate status:")
    for gate_id, status in gates.get_status().items():
        print(f"  {gate_id}: {status}")

    print("\n=== HITL Gates Demo ===\n")
    hitl = HITLGates()
    hitl_context = {
        "task_spec": {"title": "Approval Task"},
        "result": {"content": "..."},
        "approval": {"approved_by": "manager-1", "timestamp": "2024-01-01"}
    }
    hitl_results = hitl.execute_sequence(hitl_context)
    print("HITL results:", hitl_results)
