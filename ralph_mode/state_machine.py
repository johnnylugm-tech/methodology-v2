"""
Ralph Mode - 階段狀態機

定義任務的階段轉換邏輯，支援自定義階段和轉換條件。

Author: methodology-v2
Version: 1.0.0
"""

from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Framework Enforcement
try:
    from methodology import FrameworkEnforcer
    _FRAMEWORK_OK = True
except ImportError:
    _FRAMEWORK_OK = False


class PhaseStatus(Enum):
    """階段狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseTransition:
    """階段轉換定義"""
    from_phase: str
    to_phase: str
    condition: Optional[Callable[[], bool]] = None
    on_transition: Optional[Callable[[], Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase:
    """階段定義"""
    name: str
    status: PhaseStatus = PhaseStatus.PENDING
    enter_callback: Optional[Callable] = None
    exit_callback: Optional[Callable] = None
    check_callback: Optional[Callable[[], bool]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def enter(self) -> None:
        """進入階段"""
        self.status = PhaseStatus.RUNNING
        if self.enter_callback:
            self.enter_callback()

    def exit(self, success: bool = True) -> None:
        """離開階段"""
        self.status = PhaseStatus.COMPLETED if success else PhaseStatus.FAILED
        if self.exit_callback:
            self.exit_callback()


class PhaseStateMachine:
    """
    Ralph Mode 階段狀態機
    
    管理任務的階段轉換，支援自定義階段和轉換條件。
    
    Attributes:
        phases: 定義的所有階段列表
        transitions: 定義的轉換規則列表
    
    Example:
        >>> sm = PhaseStateMachine()
        >>> sm.add_phase("init")
        >>> sm.add_phase("run_batch")
        >>> sm.add_transition("init", "run_batch")
        >>> sm.transition("run_batch")
    """

    DEFAULT_PHASES = ["init", "run_batch", "extract", "eval", "report", "done"]

    def __init__(self, phases: Optional[List[str]] = None):
        """
        初始化狀態機
        
        Args:
            phases: 階段名稱列表，預設為標準階段
        """
        self._phases: Dict[str, Phase] = {}
        self._transitions: List[PhaseTransition] = []
        self._current_phase: Optional[str] = None
        self._phase_history: List[str] = []

        # 初始化預設階段
        if phases is None:
            phases = self.DEFAULT_PHASES
        
        for phase_name in phases:
            self.add_phase(phase_name)

    def add_phase(
        self,
        name: str,
        enter_callback: Optional[Callable] = None,
        exit_callback: Optional[Callable] = None,
        check_callback: Optional[Callable[[], bool]] = None
    ) -> "PhaseStateMachine":
        """
        添加階段
        
        Args:
            name: 階段名稱
            enter_callback: 進入階段的回調函數
            exit_callback: 離開階段的回調函數
            check_callback: 檢查是否可以進入的回調函數
        
        Returns:
            self (鏈式調用)
        """
        self._phases[name] = Phase(
            name=name,
            enter_callback=enter_callback,
            exit_callback=exit_callback,
            check_callback=check_callback
        )
        return self

    def add_transition(
        self,
        from_phase: str,
        to_phase: str,
        condition: Optional[Callable[[], bool]] = None,
        on_transition: Optional[Callable[[], Any]] = None
    ) -> "PhaseStateMachine":
        """
        添加轉換規則
        
        Args:
            from_phase: 起始階段
            to_phase: 目標階段
            condition: 轉換條件函數，返回 bool
            on_transition: 轉換時的回調函數
        
        Returns:
            self (鏈式調用)
        """
        transition = PhaseTransition(
            from_phase=from_phase,
            to_phase=to_phase,
            condition=condition,
            on_transition=on_transition
        )
        self._transitions.append(transition)
        return self

    def can_transition(self, to_phase: str) -> bool:
        """
        檢查是否可以轉換到目標階段
        
        Args:
            to_phase: 目標階段名稱
        
        Returns:
            bool: 是否可以轉換
        """
        if self._current_phase is None:
            # 初始階段
            return to_phase == self._get_initial_phase()

        if to_phase not in self._phases:
            return False

        # 檢查是否有有效的轉換規則
        for transition in self._transitions:
            if (transition.from_phase == self._current_phase and
                transition.to_phase == to_phase):
                if transition.condition is None:
                    return True
                return transition.condition()

        # 預設：允許按順序轉換到下一個階段
        phase_names = list(self._phases.keys())
        current_idx = phase_names.index(self._current_phase)
        target_idx = phase_names.index(to_phase) if to_phase in phase_names else -1
        
        return target_idx == current_idx + 1

    def transition(self, to_phase: str, force: bool = False) -> bool:
        """
        執行階段轉換
        
        Args:
            to_phase: 目標階段名稱
            force: 是否強制轉換（跳過條件檢查）
        
        Returns:
            bool: 轉換是否成功
        """
        if not force and not self.can_transition(to_phase):
            print(f"[Ralph] 無法從 {self._current_phase} 轉換到 {to_phase}")
            return False

        # 離開當前階段
        if self._current_phase and self._current_phase in self._phases:
            current = self._phases[self._current_phase]
            current.exit(success=True)

        # 執行轉換回調
        for transition in self._transitions:
            if (transition.from_phase == self._current_phase and
                transition.to_phase == to_phase):
                if transition.on_transition:
                    transition.on_transition()

        # 進入新階段
        self._phase_history.append(self._current_phase or "init")
        self._current_phase = to_phase
        
        if to_phase in self._phases:
            self._phases[to_phase].enter()

        return True

    def get_current_phase(self) -> Optional[str]:
        """取得當前階段"""
        return self._current_phase

    def get_phase_status(self, phase_name: str) -> Optional[PhaseStatus]:
        """取得階段狀態"""
        if phase_name not in self._phases:
            return None
        return self._phases[phase_name].status

    def get_phase_history(self) -> List[str]:
        """取得階段歷史"""
        return self._phase_history.copy()

    def is_completed(self) -> bool:
        """檢查是否完成所有階段"""
        return self._current_phase == "done"

    def reset(self) -> None:
        """重置狀態機"""
        self._current_phase = None
        self._phase_history = []
        for phase in self._phases.values():
            phase.status = PhaseStatus.PENDING

    def _get_initial_phase(self) -> str:
        """取得初始階段"""
        phase_names = list(self._phases.keys())
        return phase_names[0] if phase_names else "init"

    def start(self) -> bool:
        """啟動狀態機（進入第一個階段）"""
        initial = self._get_initial_phase()
        return self.transition(initial, force=True)

    def advance(self) -> bool:
        """
        推進到下一個階段
        
        Returns:
            bool: 推進是否成功
        """
        if self._current_phase is None:
            return self.start()

        phase_names = list(self._phases.keys())
        current_idx = phase_names.index(self._current_phase)
        
        if current_idx >= len(phase_names) - 1:
            return False

        next_phase = phase_names[current_idx + 1]
        return self.transition(next_phase)

    def get_state_dict(self) -> Dict[str, Any]:
        """取得狀態字典（用於序列化）"""
        return {
            "current_phase": self._current_phase,
            "phase_history": self._phase_history,
            "phases": {
                name: {
                    "status": phase.status.value,
                    "metadata": phase.metadata
                }
                for name, phase in self._phases.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseStateMachine":
        """從字典還原狀態機"""
        phases = list(data.get("phases", {}).keys())
        sm = cls(phases=phases)
        
        sm._current_phase = data.get("current_phase")
        sm._phase_history = data.get("phase_history", [])
        
        return sm