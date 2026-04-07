"""
Ralph Mode - 定時輪詢排程器

提供任務的定時輪詢功能，支援自定義檢查函數和執行間隔。

Author: methodology-v2
Version: 1.0.0
"""

import time
import threading
from datetime import datetime
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass, field

# Framework Enforcement
try:
    from methodology import FrameworkEnforcer
    _FRAMEWORK_OK = True
except ImportError:
    _FRAMEWORK_OK = False

# 嘗試匯入 schedule 庫
try:
    import schedule
    _SCHEDULE_OK = True
except ImportError:
    _SCHEDULE_OK = False


@dataclass
class SchedulerConfig:
    """排程器配置"""
    interval_seconds: int = 30
    initial_delay: int = 5
    max_consecutive_failures: int = 3
    stop_on_failure: bool = True
    callback_on_start: Optional[Callable] = None
    callback_on_failure: Optional[Callable] = None
    callback_on_stop: Optional[Callable] = None


class RalphScheduler:
    """
    Ralph Mode 定時排程器
    
    支援定時執行任務檢查函數，適用於監控長期運行的批次任務。
    
    Attributes:
        task_id: 任務 ID
        check_func: 要執行的檢查函數
        config: 排程器配置
    
    Example:
        >>> def my_check(task_id):
        ...     print(f"檢查任務 {task_id}")
        ...     return True
        >>> scheduler = RalphScheduler("task-001", my_check)
        >>> scheduler.start()
    """

    def __init__(
        self,
        task_id: str,
        check_func: Callable[[str], bool],
        config: Optional[SchedulerConfig] = None
    ):
        """
        初始化排程器
        
        Args:
            task_id: 任務 ID
            check_func: 檢查函數，接收 task_id，返回 bool
            config: 排程器配置
        """
        self.task_id = task_id
        self.check_func = check_func
        self.config = config or SchedulerConfig()
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_run: Optional[datetime] = None
        self._consecutive_failures = 0
        self._metadata: Dict[str, Any] = {}

    def start(self, blocking: bool = False) -> None:
        """
        啟動排程器
        
        Args:
            blocking: 是否阻塞執行
        """
        if self._running:
            print(f"[Ralph] 排程器已運行: {self.task_id}")
            return

        self._running = True
        self._consecutive_failures = 0

        if blocking:
            self._run_loop()
        else:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            print(f"[Ralph] 排程器已啟動: {self.task_id}")

    def stop(self) -> None:
        """停止排程器"""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        
        print(f"[Ralph] 排程器已停止: {self.task_id}")
        
        if self.config.callback_on_stop:
            self.config.callback_on_stop(self.task_id)

    def _run_loop(self) -> None:
        """執行排程循環"""
        # 初始延遲
        time.sleep(self.config.initial_delay)

        if self.config.callback_on_start:
            self.config.callback_on_start(self.task_id)

        while self._running:
            try:
                # 執行檢查函數
                result = self.check_func(self.task_id)
                
                self._last_run = datetime.now()
                self._consecutive_failures = 0

                # 等待間隔
                time.sleep(self.config.interval_seconds)

            except Exception as e:
                self._consecutive_failures += 1
                print(f"[Ralph] 排程器錯誤 ({self.task_id}): {e}")

                if self.config.callback_on_failure:
                    self.config.callback_on_failure(
                        self.task_id,
                        e,
                        self._consecutive_failures
                    )

                # 檢查是否應該停止
                if (self.config.stop_on_failure and 
                    self._consecutive_failures >= self.config.max_consecutive_failures):
                    print(f"[Ralph] 連續失敗 {self._consecutive_failures} 次，停止排程器")
                    self._running = False
                    break

                time.sleep(self.config.interval_seconds)

    def is_running(self) -> bool:
        """檢查排程器是否運行中"""
        return self._running

    def get_last_run(self) -> Optional[datetime]:
        """取得上次執行時間"""
        return self._last_run

    def get_metadata(self) -> Dict[str, Any]:
        """取得元資料"""
        return self._metadata.copy()

    def set_metadata(self, key: str, value: Any) -> None:
        """設定元資料"""
        self._metadata[key] = value


class SchedulerManager:
    """
    排程器管理器
    
    管理多個任務的排程器，支援統一啟動和停止。
    """

    def __init__(self):
        self._schedulers: Dict[str, RalphScheduler] = {}

    def register(
        self,
        task_id: str,
        check_func: Callable[[str], bool],
        config: Optional[SchedulerConfig] = None
    ) -> RalphScheduler:
        """
        註冊排程器
        
        Args:
            task_id: 任務 ID
            check_func: 檢查函數
            config: 排程器配置
        
        Returns:
            RalphScheduler 實例
        """
        scheduler = RalphScheduler(task_id, check_func, config)
        self._schedulers[task_id] = scheduler
        return scheduler

    def start(self, task_id: str, blocking: bool = False) -> bool:
        """啟動指定任務的排程器"""
        if task_id not in self._schedulers:
            print(f"[Ralph] 排程器不存在: {task_id}")
            return False
        
        self._schedulers[task_id].start(blocking=blocking)
        return True

    def stop(self, task_id: str) -> bool:
        """停止指定任務的排程器"""
        if task_id not in self._schedulers:
            print(f"[Ralph] 排程器不存在: {task_id}")
            return False
        
        self._schedulers[task_id].stop()
        return True

    def stop_all(self) -> None:
        """停止所有排程器"""
        for scheduler in self._schedulers.values():
            scheduler.stop()

    def list_schedulers(self) -> list:
        """列出所有排程器"""
        return [
            {
                "task_id": s.task_id,
                "running": s.is_running(),
                "last_run": s.get_last_run().isoformat() if s.get_last_run() else None
            }
            for s in self._schedulers.values()
        ]