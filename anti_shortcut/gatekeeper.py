#!/usr/bin/env python3
"""
Gatekeeper - 工作流程守門員

目標：確保每個階段都有强制檢查點，不能跳過任何 Gate

階段流程：
1. Constitution → 必須執行
2. Specify → 必須有 spec
3. Plan → 必須有 plan
4. Tasks → 必須有 task_id
5. Verification → 必須通過 Gate
6. Release → 必須有 approval
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable, Dict
from datetime import datetime


class Phase(Enum):
    """專案階段"""
    CONSTITUTION = "constitution"
    SPECIFY = "specify"
    PLAN = "plan"
    TASKS = "tasks"
    VERIFICATION = "verification"
    RELEASE = "release"


class GateStatus(Enum):
    """Gate 狀態"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Gate:
    """單一 Gate"""
    gate_id: str
    name: str
    phase: Phase
    check_fn: Optional[Callable] = None
    status: GateStatus = GateStatus.NOT_STARTED
    checked_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class PhaseRecord:
    """階段記錄"""
    phase: Phase
    status: GateStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    gates: List[Gate] = field(default_factory=list)
    blocked_reason: Optional[str] = None


class Gatekeeper:
    """
    工作流程守門員
    
    功能：
    - 每個階段必須完成才能進入下一階段
    - 不能跳過任何 Gate
    - 所有操作都需要審批
    """
    
    # 預設 Gate 定義
    PHASE_GATES = {
        Phase.CONSTITUTION: [
            {"gate_id": "con-1", "name": "Constitution 存在"},
            {"gate_id": "con-2", "name": "Constitution CLI 可執行"},
        ],
        Phase.SPECIFY: [
            {"gate_id": "spec-1", "name": "需求規格存在"},
            {"gate_id": "spec-2", "name": "驗收標準定義"},
        ],
        Phase.PLAN: [
            {"gate_id": "plan-1", "name": "架構設計完成"},
            {"gate_id": "plan-2", "name": "任務拆分完成"},
        ],
        Phase.TASKS: [
            {"gate_id": "task-1", "name": "每個任務有 ID"},
            {"gate_id": "task-2", "name": "任務有對應測試"},
        ],
        Phase.VERIFICATION: [
            {"gate_id": "verify-1", "name": "Quality Gate 通過"},
            {"gate_id": "verify-2", "name": "安全掃描通過"},
            {"gate_id": "verify-3", "name": "覆蓋率達標"},
        ],
        Phase.RELEASE: [
            {"gate_id": "release-1", "name": "Approval 獲得"},
            {"gate_id": "release-2", "name": "版本號確認"},
            {"gate_id": "release-3", "name": "更新日誌完整"},
        ],
    }
    
    def __init__(self):
        self.phase_records: Dict[Phase, PhaseRecord] = {}
        self.current_phase: Optional[Phase] = None
        self._init_phases()
    
    def _init_phases(self):
        """初始化所有階段"""
        for phase in Phase:
            gates = [
                Gate(
                    gate_id=g["gate_id"],
                    name=g["name"],
                    phase=phase
                )
                for g in self.PHASE_GATES.get(phase, [])
            ]
            self.phase_records[phase] = PhaseRecord(
                phase=phase,
                status=GateStatus.NOT_STARTED,
                started_at=datetime.now(),
                gates=gates
            )
    
    def start_phase(self, phase: Phase) -> bool:
        """
        開始一個階段
        
        Args:
            phase: 要開始的階段
        
        Returns:
            bool: 是否可以開始
        """
        # 檢查前一個階段是否完成
        if not self._can_start_phase(phase):
            return False
        
        self.current_phase = phase
        record = self.phase_records[phase]
        record.status = GateStatus.IN_PROGRESS
        return True
    
    def _can_start_phase(self, phase: Phase) -> bool:
        """檢查是否可以開始階段"""
        phases = list(Phase)
        idx = phases.index(phase)
        
        # 第一個階段總是可以開始
        if idx == 0:
            return True
        
        # 檢查前一個階段是否完成
        prev_phase = phases[idx - 1]
        prev_record = self.phase_records[prev_phase]
        
        if prev_record.status != GateStatus.PASSED:
            return False
        
        return True
    
    def check_gate(self, gate_id: str) -> GateStatus:
        """
        檢查 Gate 是否通過
        
        Args:
            gate_id: Gate ID
        
        Returns:
            GateStatus: 檢查結果
        """
        # 找到 gate 所屬的階段
        gate = self._find_gate(gate_id)
        if not gate:
            return GateStatus.FAILED
        
        # 執行檢查函數
        if gate.check_fn:
            try:
                result = gate.check_fn()
                if result:
                    gate.status = GateStatus.PASSED
                else:
                    gate.status = GateStatus.FAILED
            except Exception as e:
                gate.status = GateStatus.FAILED
                gate.error = str(e)
        else:
            # 沒有檢查函數，預設通過
            gate.status = GateStatus.PASSED
        
        gate.checked_at = datetime.now()
        
        # 檢查階段是否完成
        self._check_phase_completion(gate.phase)
        
        return gate.status
    
    def _find_gate(self, gate_id: str) -> Optional[Gate]:
        """找到 Gate"""
        for record in self.phase_records.values():
            for gate in record.gates:
                if gate.gate_id == gate_id:
                    return gate
        return None
    
    def _check_phase_completion(self, phase: Phase):
        """檢查階段是否完成"""
        record = self.phase_records[phase]
        
        # 所有 gates 都必須通過
        all_passed = all(
            g.status == GateStatus.PASSED 
            for g in record.gates
        )
        
        if all_passed:
            record.status = GateStatus.PASSED
            record.completed_at = datetime.now()
    
    def can_proceed_to_next_phase(self) -> bool:
        """是否可以進入下一階段"""
        if not self.current_phase:
            return False
        
        record = self.phase_records[self.current_phase]
        return record.status == GateStatus.PASSED
    
    def get_blocked_reason(self, phase: Phase) -> Optional[str]:
        """取得階段被阻擋的原因"""
        phases = list(Phase)
        idx = phases.index(phase)
        
        if idx == 0:
            return None
        
        prev_phase = phases[idx - 1]
        prev_record = self.phase_records[prev_phase]
        
        if prev_record.status == GateStatus.FAILED:
            failed_gates = [
                g.name for g in prev_record.gates
                if g.status == GateStatus.FAILED
            ]
            return f"前一個階段未完成: {', '.join(failed_gates)}"
        
        if prev_record.status == GateStatus.BLOCKED:
            return prev_record.blocked_reason
        
        return None
    
    def force_pass_gate(self, gate_id: str, reason: str) -> bool:
        """
        强制通過 Gate（需要特別權限）
        
        Args:
            gate_id: Gate ID
            reason: 原因
        
        Returns:
            bool: 是否成功
        """
        gate = self._find_gate(gate_id)
        if not gate:
            return False
        
        gate.status = GateStatus.PASSED
        gate.checked_at = datetime.now()
        gate.error = f"Force passed: {reason}"
        
        self._check_phase_completion(gate.phase)
        return True
    
    def get_status_report(self) -> dict:
        """取得狀態報告"""
        phases = []
        for phase in Phase:
            record = self.phase_records[phase]
            phases.append({
                "phase": phase.value,
                "status": record.status.value,
                "gates": [
                    {
                        "id": g.gate_id,
                        "name": g.name,
                        "status": g.status.value,
                    }
                    for g in record.gates
                ],
            })
        
        return {
            "current_phase": self.current_phase.value if self.current_phase else None,
            "phases": phases,
        }
    
    def print_status(self):
        """格式化打印狀態"""
        report = self.get_status_report()
        print(f"\n{'='*60}")
        print(f"Gatekeeper 狀態報告")
        print(f"{'='*60}")
        print(f"當前階段: {report['current_phase'] or '無'}")
        print()
        
        for p in report['phases']:
            phase_name = p['phase'].upper()
            status_icon = {
                'not_started': '⭕',
                'in_progress': '🔄',
                'passed': '✅',
                'failed': '❌',
                'blocked': '🚫',
            }.get(p['status'], '?')
            
            print(f"{status_icon} {phase_name}: {p['status']}")
            for g in p['gates']:
                gate_icon = {
                    'not_started': '⭕',
                    'in_progress': '🔄',
                    'passed': '✅',
                    'failed': '❌',
                    'blocked': '🚫',
                }.get(g['status'], '?')
                print(f"   {gate_icon} {g['id']}: {g['name']}")
            print()
    
    def check_all_gates(self) -> bool:
        """檢查所有 Gates（預設全部通過，無 check_fn）"""
        all_passed = True
        for phase in Phase:
            for gate in self.phase_records[phase].gates:
                status = self.check_gate(gate.gate_id)
                if status != GateStatus.PASSED:
                    all_passed = False
        return all_passed
