"""
Ralph Mode - Lifecycle Manager

Ralph Mode 生命週期管理：start / stop / check / alert。

Author: methodology-v2
Version: 1.0.0
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

from .schema_validator import SessionsSpawnLogValidator, ValidationResult, RalphSchemaError
from .alert_manager import AlertManager, AlertLevel, get_default_manager
from .output_verifier import OutputVerifier, VerificationResult


class EndReason(Enum):
    """終止原因"""
    COMPLETED = "all_completed"      # M1: 所有 FR 完成
    TIMEOUT = "timeout"              # M2: HR-13 超時
    USER_STOP = "user_stop"          # M3: 用戶手動終止
    ERROR = "error"                  # 錯誤


@dataclass
class TaskState:
    """Ralph 任務狀態"""
    task_id: str
    phase: int
    status: str  # running, completed, failed, stopped
    current_phase: str = "run_batch"  # init, run_batch, postflight, done
    progress: float = 0.0
    created_at: str = None
    updated_at: str = None
    started_at: str = None
    ended_at: str = None
    estimated_minutes: int = 60
    fr_total: int = 0
    fr_completed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskState":
        return cls(**data)


@dataclass
class CheckResult:
    """Ralph 檢查結果"""
    status: str  # running, completed, timeout, hr13_triggered
    progress: float
    fr_total: int
    fr_completed: int
    fr_pending: int
    fr_failed: int
    elapsed_minutes: float
    estimated_minutes: int
    hr13_triggered: bool = False
    message: str = ""


class RalphLifecycleManager:
    """
    Ralph Mode 生命週期管理器
    
    職責：
    - 啟動/停止 Ralph
    - 檢查執行狀態
    - 發送 Alert
    
    MVP 核心功能（M1/M2/M3）：
    - M1: 所有 FR COMPLETED → STOP + SUCCESS
    - M2: HR-13 超時 → Alert，等待用戶
    - M3: 用戶手動終止 → STOP + INFO
    
    Example:
        >>> manager = RalphLifecycleManager(Path("/repo"))
        >>> task_id = manager.start(phase=3, estimated_minutes=60)
        >>> result = manager.check()
        >>> if result.status == "completed":
        ...     manager.stop(reason="completed")
    """
    
    HR13_MULTIPLIER = 3  # HR-13: 預估時間 × 3
    CHECK_INTERVAL_SECONDS = 60  # 每 60 秒檢查一次
    
    def __init__(self, repo_path: Path):
        """
        初始化 LifecycleManager
        
        Args:
            repo_path: 專案根目錄
        """
        self.repo_path = Path(repo_path)
        self.state_dir = self.repo_path / ".ralph" / "tasks"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_path = self.repo_path / ".methodology" / "sessions_spawn.log"
        
        self.validator = SessionsSpawnLogValidator()
        self.alert_mgr = get_default_manager()
        self.output_verifier = OutputVerifier(self.repo_path)
        
        self._current_task_id: Optional[str] = None
        self._current_state: Optional[TaskState] = None
    
    # ============== Lifecycle Methods ==============
    
    def start(self, phase: int, estimated_minutes: int = 60, fr_list: List[str] = None) -> str:
        """
        啟動 Ralph 任務
        
        Args:
            phase: Phase 編號
            estimated_minutes: 預估執行時間（分鐘）
            fr_list: FR 列表
            
        Returns:
            task_id
            
        Raises:
            RalphSchemaError: 如果 sessions_spawn.log schema 不相容
        """
        # 驗證或初始化 log
        self._ensure_log_file()
        
        # 驗證 schema
        validation = self.validator.validate_path(self.log_path)
        if not validation.ok:
            raise RalphSchemaError(validation.error)
        
        if validation.warning:
            print(f"⚠️  {validation.warning}")
        
        # 建立 task_id
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        task_id = f"phase-{phase}-{timestamp}"
        
        # 建立 TaskState
        state = TaskState(
            task_id=task_id,
            phase=phase,
            status="running",
            current_phase="run_batch",
            estimated_minutes=estimated_minutes,
            fr_total=len(fr_list) if fr_list else 0,
            metadata={
                "estimated_minutes": estimated_minutes,
                "hr_list": fr_list or []
            }
        )
        state.started_at = datetime.now(timezone.utc).isoformat()
        
        # 保存狀態
        self._save_state(state)
        
        self._current_task_id = task_id
        self._current_state = state
        
        # 發送啟動通知
        self.alert_mgr.send(
            level=AlertLevel.INFO,
            title=f"🔄 Phase {phase} Ralph 啟動",
            message=f"預估時間: {estimated_minutes} 分鐘",
            task_id=task_id,
            phase=phase
        )
        
        print(f"[Ralph] Started: {task_id}")
        return task_id
    
    def stop(self, reason: str = "completed", task_id: str = None) -> None:
        """
        停止 Ralph 任務
        
        Args:
            reason: 終止原因 (completed, timeout, user_stop, error)
            task_id: 任務 ID（預設使用當前任務）
        """
        task_id = task_id or self._current_task_id
        if not task_id:
            print("[Ralph] No active task to stop")
            return
        
        # 載入狀態
        state = self._load_state(task_id)
        if not state:
            print(f"[Ralph] Task not found: {task_id}")
            return
        
        # 更新狀態
        state.status = "stopped"
        state.ended_at = datetime.now(timezone.utc).isoformat()
        
        # 計算耗時
        if state.started_at:
            started = datetime.fromisoformat(state.started_at)
            ended = datetime.now(timezone.utc)
            duration = (ended - started).total_seconds() / 60
            state.metadata["duration_minutes"] = duration
        
        state.metadata["end_reason"] = reason
        
        # 保存
        self._save_state(state)
        
        # 發送通知
        level_map = {
            "completed": AlertLevel.SUCCESS,
            "timeout": AlertLevel.CRITICAL,
            "user_stop": AlertLevel.INFO,
            "error": AlertLevel.ERROR
        }
        
        title_map = {
            "completed": f"✅ Phase {state.phase} 完成",
            "timeout": f"⏰ Phase {state.phase} 超時",
            "user_stop": f"ℹ️ Phase {state.phase} 已終止",
            "error": f"❌ Phase {state.phase} 錯誤"
        }
        
        message_parts = [f"FR 完成: {state.fr_completed}/{state.fr_total}"]
        if "duration_minutes" in state.metadata:
            message_parts.append(f"耗時: {state.metadata['duration_minutes']:.1f} 分鐘")
        if reason == "timeout":
            message_parts.append(f"原因: HR-13 超時")
        
        self.alert_mgr.send(
            level=level_map.get(reason, AlertLevel.INFO),
            title=title_map.get(reason, f"Phase {state.phase} 終止"),
            message=", ".join(message_parts),
            task_id=task_id,
            phase=state.phase
        )
        
        # 清理當前任務
        if task_id == self._current_task_id:
            self._current_task_id = None
            self._current_state = None
        
        print(f"[Ralph] Stopped: {task_id} (reason: {reason})")
    
    def check(self, task_id: str = None) -> CheckResult:
        """
        檢查 Ralph 任務狀態
        
        這個函數會被 RalphScheduler 每 60 秒呼叫一次。
        
        Args:
            task_id: 任務 ID（預設使用當前任務）
            
        Returns:
            CheckResult
        """
        task_id = task_id or self._current_task_id
        if not task_id:
            return CheckResult(
                status="idle",
                progress=0,
                fr_total=0,
                fr_completed=0,
                fr_pending=0,
                fr_failed=0,
                elapsed_minutes=0,
                estimated_minutes=0,
                message="No active task"
            )
        
        # 載入狀態
        state = self._load_state(task_id)
        if not state:
            return CheckResult(
                status="error",
                progress=0,
                fr_total=0,
                fr_completed=0,
                fr_pending=0,
                fr_failed=0,
                elapsed_minutes=0,
                estimated_minutes=0,
                message=f"Task not found: {task_id}"
            )
        
        # 讀取 log
        log_content = self._read_log()
        
        # 計算 FR 狀態
        entries = log_content.get("entries", [])
        expected_frs = state.metadata.get("hr_list", [])
        fr_status = self._aggregate_fr_status(entries, expected_frs)
        
        fr_completed = fr_status["completed"]
        fr_failed = fr_status["failed"]
        fr_pending = fr_status["pending"]
        
        # Use state's fr_total if set, otherwise count from log
        fr_total = state.fr_total if state.fr_total > 0 else len(fr_status["frs"])
        
        progress = (fr_completed / fr_total * 100) if fr_total > 0 else 0
        
        # 計算耗時
        elapsed = 0
        if state.started_at:
            started = datetime.fromisoformat(state.started_at)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 60
        
        # HR-13 超時檢查
        hr13_threshold = state.estimated_minutes * self.HR13_MULTIPLIER
        hr13_triggered = elapsed > hr13_threshold and fr_pending > 0
        
        # 更新狀態
        state.fr_completed = fr_completed
        state.progress = progress
        state.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_state(state)
        
        # 構建結果
        result = CheckResult(
            status="running" if fr_pending > 0 else "completed",
            progress=progress,
            fr_total=fr_total,
            fr_completed=fr_completed,
            fr_pending=fr_pending,
            fr_failed=fr_failed,
            elapsed_minutes=elapsed,
            estimated_minutes=state.estimated_minutes,
            hr13_triggered=hr13_triggered,
            message=""
        )
        
        # HR-13 Alert
        if hr13_triggered:
            result.status = "timeout"
            result.message = f"HR-13 triggered: {elapsed:.0f} min > {hr13_threshold} min"
            self._alert_hr13_timeout(elapsed, state.estimated_minutes, state.phase, task_id)
        
        return result
    
    # ============== Helper Methods ==============
    
    def _ensure_log_file(self) -> None:
        """確保 sessions_spawn.log 存在並使用正確 schema"""
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.write_text(json.dumps(self.validator.create_empty_log(), indent=2))
            print(f"[Ralph] Created sessions_spawn.log with schema {self.validator.CURRENT_SCHEMA}")
    
    def _read_log(self) -> Dict[str, Any]:
        """讀取 sessions_spawn.log"""
        if not self.log_path.exists():
            return {"schema_version": "1.0", "entries": []}
        
        try:
            return json.loads(self.log_path.read_text())
        except:
            return {"schema_version": "1.0", "entries": []}
    
    def _aggregate_fr_status(self, entries: List[Dict], expected_frs: List[str] = None) -> Dict[str, Any]:
        """
        聚合 FR 狀態
        
        Args:
            entries: log entries
            expected_frs: 預期的 FR 列表（從 start() 時傳入的 fr_list）
        """
        # Initialize tracking for all expected FRs
        frs = {}
        if expected_frs:
            for fr in expected_frs:
                frs[fr] = {"completed": 0, "failed": 0, "pending": 0, "seen": False}
        
        # Process log entries
        for entry in entries:
            fr = entry.get("fr", "UNKNOWN")
            status = entry.get("status", "UNKNOWN")
            
            # Initialize FR if not seen before
            if fr not in frs:
                frs[fr] = {"completed": 0, "failed": 0, "pending": 0}
            
            frs[fr]["seen"] = True
            
            if status == "COMPLETED":
                frs[fr]["completed"] += 1
            elif status == "FAILED":
                frs[fr]["failed"] += 1
            else:
                frs[fr]["pending"] += 1
        
        # Count final states (each FR has only ONE final state)
        result = {"frs": [], "completed": 0, "failed": 0, "pending": 0}
        for fr, counts in frs.items():
            result["frs"].append(fr)
            if not counts["seen"]:
                # FR was initialized but never appeared in log → pending
                result["pending"] += 1
            elif counts["completed"] > 0:
                result["completed"] += 1
            elif counts["failed"] > 0:
                result["failed"] += 1
            else:
                result["pending"] += 1
        
        return result
    
    def _load_state(self, task_id: str) -> Optional[TaskState]:
        """載入 TaskState"""
        state_path = self.state_dir / f"{task_id}.json"
        if not state_path.exists():
            return None
        
        try:
            data = json.loads(state_path.read_text())
            return TaskState.from_dict(data)
        except:
            return None
    
    def _save_state(self, state: TaskState) -> None:
        """保存 TaskState"""
        state_path = self.state_dir / f"{state.task_id}.json"
        state_path.write_text(json.dumps(state.to_dict(), indent=2))
    
    def _alert_hr13_timeout(self, elapsed: float, estimated: float, phase: int, task_id: str) -> None:
        """發送 HR-13 超時 Alert"""
        self.alert_mgr.send(
            level=AlertLevel.CRITICAL,
            title=f"🔴 HR-13 Phase {phase} 超時",
            message=(
                f"已執行: {elapsed:.0f} 分鐘\n"
                f"預估時間: {estimated} 分鐘\n"
                f"HR-13 閾值: {estimated * self.HR13_MULTIPLIER} 分鐘"
            ),
            task_id=task_id,
            phase=phase
        )
    
    # ============== L2 Verification ==============
    
    def verify_fr_output(self, fr_task: Dict[str, Any]) -> VerificationResult:
        """
        驗證 FR 產出（L2 驗證）
        
        Args:
            fr_task: {
                "fr": "FR-01",
                "expected_outputs": [...],
                // 或
                "task_text": "..."
            }
            
        Returns:
            VerificationResult
        """
        result = self.output_verifier.verify_fr(fr_task)
        
        if not result.passed:
            self.alert_mgr.send(
                level=AlertLevel.WARNING,
                title=f"⚠️ FR-{fr_task.get('fr', 'UNKNOWN')} 產出驗證失敗",
                message="\n".join(result.errors),
                phase=self._current_state.phase if self._current_state else None
            )
        
        return result
    
    # ============== Query Methods ==============
    
    def get_running_ralph(self, phase: int) -> Optional[TaskState]:
        """
        取得指定 Phase 的運行中 Ralph
        
        Args:
            phase: Phase 編號
            
        Returns:
            TaskState 如果存在，否則 None
        """
        for state_file in self.state_dir.glob("*.json"):
            try:
                data = json.loads(state_file.read_text())
                state = TaskState.from_dict(data)
                if state.phase == phase and state.status == "running":
                    return state
            except:
                continue
        return None
    
    def list_running_ralphs(self) -> List[TaskState]:
        """列出所有運行中的 Ralph"""
        running = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                data = json.loads(state_file.read_text())
                state = TaskState.from_dict(data)
                if state.status == "running":
                    running.append(state)
            except:
                continue
        return running
