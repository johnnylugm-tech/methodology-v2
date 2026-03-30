"""
Ralph Mode - 命令列介面

提供 ralph CLI 子命令，用於啟動、查看和停止任務監控。

使用方法：
    python -m ralph_mode.cli start <task_id>
    python -m ralph_mode.cli status <task_id>
    python -m ralph_mode.cli stop <task_id>
    python -m ralph_mode.cli list

Author: methodology-v2
Version: 1.0.0
"""

import sys
import os
import argparse
from datetime import datetime

# Framework Enforcement
try:
    from methodology import FrameworkEnforcer
    _FRAMEWORK_OK = True
except ImportError:
    _FRAMEWORK_OK = False

from task_persistence import TaskState, TaskPersistence
from scheduler import RalphScheduler, SchedulerConfig, SchedulerManager
from state_machine import PhaseStateMachine
from progress_tracker import RalphProgressTracker


class RalphCLI:
    """
    Ralph Mode 命令列介面
    
    支援啟動、停止、查看任務監控狀態。
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.persistence = TaskPersistence()
        self.scheduler_manager = SchedulerManager()
        self._active_monitors = {}

    def run(self, args):
        """執行命令"""
        command = args.command

        if command == "start":
            return self.cmd_start(args)
        elif command == "status":
            return self.cmd_status(args)
        elif command == "stop":
            return self.cmd_stop(args)
        elif command == "list":
            return self.cmd_list(args)
        elif command == "init":
            return self.cmd_init(args)
        elif command == "advance":
            return self.cmd_advance(args)
        else:
            print(f"❌ 未知命令: {command}")
            return 1

        return 0

    def cmd_start(self, args):
        """
        啟動任務監控
        
        Usage: ralph start <task_id> [--interval SECONDS] [--background]
        """
        task_id = args.task_id

        if not task_id:
            print("❌ 請指定任務 ID")
            print("   用法: ralph start <task_id>")
            return 1

        # 檢查任務是否已存在
        existing = self.persistence.load_state(task_id)
        
        if existing and existing.status == "running":
            print(f"⚠️  任務已是運行中: {task_id}")
            print(f"   狀態: {existing.status}")
            print(f"   階段: {existing.current_phase}")
            print(f"   進度: {existing.progress:.1f}%")
            print(f"   若要重啟，請先執行: ralph stop {task_id}")
            return 1

        # 初始化任務狀態
        state = existing or TaskState(
            task_id=task_id,
            status="running",
            current_phase="init",
            progress=0.0
        )
        state.status = "running"
        state.current_phase = "init"
        
        # 保存初始狀態
        self.persistence.save_state(state)

        # 初始化進度追蹤
        progress_tracker = RalphProgressTracker(task_id)
        progress_tracker.update_progress("init", 0.0, {"event": "task_started"})

        # 建立狀態機
        sm = PhaseStateMachine()

        # 設定預設的階段推進回調
        def on_phase_enter(phase):
            progress_tracker.update_progress(phase, 0.0, {"event": "phase_enter"})
            state.current_phase = phase
            self.persistence.save_state(state)

        for phase_name in sm.DEFAULT_PHASES:
            phase_obj = sm._phases.get(phase_name)
            if phase_obj:
                phase_obj.enter_callback = lambda p=phase_name: on_phase_enter(p)

        # 啟動狀態機
        sm.start()

        # 建立排程器
        def check_task(task_id: str) -> bool:
            """檢查任務狀態"""
            state = self.persistence.load_state(task_id)
            if state is None:
                return False

            # 推進階段進度
            current_progress = state.progress
            if current_progress < 100:
                new_progress = min(100.0, current_progress + 5.0)
                state.progress = new_progress
                self.persistence.save_state(state)

                # 更新進度追蹤
                phase_progress = sm.get_phase_status(state.current_phase)
                progress_tracker.update_progress(
                    state.current_phase,
                    new_progress,
                    {"check_count": int(new_progress / 5)}
                )

                print(f"[Ralph] {task_id}: {state.current_phase} - {new_progress:.1f}%")

            # 檢查是否完成
            if new_progress >= 100.0:
                sm.advance()
                if sm.is_completed():
                    state.status = "completed"
                    self.persistence.save_state(state)
                    progress_tracker.complete_task()
                    print(f"✅ 任務完成: {task_id}")
                    return False

            return True

        # 配置排程器
        interval = args.interval or 30
        config = SchedulerConfig(
            interval_seconds=interval,
            stop_on_failure=False
        )

        scheduler = self.scheduler_manager.register(task_id, check_task, config)

        # 儲存監控實例
        self._active_monitors[task_id] = {
            "scheduler": scheduler,
            "state_machine": sm,
            "progress_tracker": progress_tracker
        }

        # 啟動排程器
        if args.background:
            scheduler.start(blocking=False)
            print(f"🚀 任務監控已啟動 (背景執行): {task_id}")
        else:
            scheduler.start(blocking=True)

        return 0

    def cmd_status(self, args):
        """
        查看任務狀態
        
        Usage: ralph status <task_id>
        """
        task_id = args.task_id

        if not task_id:
            print("❌ 請指定任務 ID")
            print("   用法: ralph status <task_id>")
            return 1

        # 嘗試從持久化載入
        state = self.persistence.load_state(task_id)
        
        # 檢查是否有活躍監控
        monitor = self._active_monitors.get(task_id)
        
        if state is None and monitor is None:
            print(f"❌ 任務不存在: {task_id}")
            print("   可用命令:")
            print("   - ralph list    (列出所有任務)")
            print("   - ralph init    (初始化新任務)")
            return 1

        # 顯示狀態
        print("=" * 50)
        print(f"任務 ID: {task_id}")
        print("=" * 50)

        if state:
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "paused": "⏸️",
                "completed": "✅",
                "failed": "❌"
            }.get(state.status, "❓")

            print(f"狀態: {status_icon} {state.status}")
            print(f"階段: {state.current_phase}")
            print(f"進度: {state.progress:.1f}%")
            print(f"最後檢查: {state.last_check or 'N/A'}")
            print(f"建立時間: {state.created_at or 'N/A'}")
            print(f"更新時間: {state.updated_at or 'N/A'}")

            # 進度條
            bar_len = 30
            filled = int(state.progress / 100 * bar_len)
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"\n進度條: [{bar}]")

        # 檢查進度檔案
        progress_file = os.path.join(
            os.getcwd(), ".ralph", "progress", "PROGRESS.md"
        )
        if os.path.exists(progress_file):
            print(f"\n📄 進度檔案存在: {progress_file}")
        else:
            print(f"\n📄 進度檔案: 未找到")

        # 排程器狀態
        if monitor:
            scheduler = monitor["scheduler"]
            sm = monitor["state_machine"]
            print(f"\n排程器: {'🟢 運行中' if scheduler.is_running() else '⚫ 已停止'}")
            print(f"狀態機: {sm.get_current_phase() or '未啟動'}")

        print("")
        return 0

    def cmd_stop(self, args):
        """
        停止任務監控
        
        Usage: ralph stop <task_id>
        """
        task_id = args.task_id

        if not task_id:
            print("❌ 請指定任務 ID")
            print("   用法: ralph stop <task_id>")
            return 1

        # 停止排程器
        if self.scheduler_manager.stop(task_id):
            print(f"🛑 排程器已停止: {task_id}")
        else:
            print(f"⚠️  排程器未運行: {task_id}")

        # 更新任務狀態
        state = self.persistence.load_state(task_id)
        if state:
            state.status = "paused"
            self.persistence.save_state(state)
            print(f"📝 任務狀態已更新為: paused")
        else:
            print(f"⚠️  任務狀態未找到: {task_id}")

        # 清理監控實例
        if task_id in self._active_monitors:
            del self._active_monitors[task_id]
            print(f"🧹 監控實例已清理: {task_id}")

        print("✅ 停止完成")
        return 0

    def cmd_list(self, args):
        """
        列出所有任務
        
        Usage: ralph list [--status STATUS]
        """
        status_filter = args.status

        tasks = self.persistence.list_tasks(status=status_filter)

        if not tasks:
            print("📭 沒有找到任務")
            print("\n提示:")
            print("   - ralph init <task_id>    (初始化新任務)")
            print("   - ralph start <task_id>   (啟動任務監控)")
            return 0

        print(f"共找到 {len(tasks)} 個任務:")
        print("-" * 60)

        for task in tasks:
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "paused": "⏸️",
                "completed": "✅",
                "failed": "❌"
            }.get(task.status, "❓")

            print(f"{status_icon} {task.task_id:<20} | {task.current_phase:<12} | {task.progress:.1f}%")

        print("-" * 60)

        # 顯示排程器狀態
        schedulers = self.scheduler_manager.list_schedulers()
        running = sum(1 for s in schedulers if s["running"])
        if running > 0:
            print(f"\n🔄 運行中的排程器: {running}")

        return 0

    def cmd_init(self, args):
        """
        初始化新任務
        
        Usage: ralph init <task_id> [--phase PHASE]
        """
        task_id = args.task_id

        if not task_id:
            print("❌ 請指定任務 ID")
            print("   用法: ralph init <task_id>")
            return 1

        # 檢查是否已存在
        existing = self.persistence.load_state(task_id)
        if existing:
            print(f"⚠️  任務已存在: {task_id}")
            print(f"   狀態: {existing.status}")
            print(f"   若要重新初始化，請先執行: ralph stop {task_id} && ralph delete {task_id}")
            return 1

        # 初始化任務
        initial_phase = args.phase or "init"
        state = TaskState(
            task_id=task_id,
            status="pending",
            current_phase=initial_phase,
            progress=0.0
        )

        if self.persistence.save_state(state):
            print(f"✅ 任務已初始化: {task_id}")
            print(f"   階段: {initial_phase}")
            print(f"   狀態: pending")
            print(f"\n下一步:")
            print(f"   ralph start {task_id}    (啟動監控)")
        else:
            print(f"❌ 任務初始化失敗")
            return 1

        return 0

    def cmd_advance(self, args):
        """
        推進任務階段
        
        Usage: ralph advance <task_id> [--to PHASE]
        """
        task_id = args.task_id

        if not task_id:
            print("❌ 請指定任務 ID")
            return 1

        state = self.persistence.load_state(task_id)
        if state is None:
            print(f"❌ 任務不存在: {task_id}")
            return 1

        # 建立狀態機
        sm = PhaseStateMachine()

        # 恢復當前階段
        if state.current_phase in sm._phases:
            sm._current_phase = state.current_phase

        # 推進階段
        if args.to:
            success = sm.transition(args.to)
        else:
            success = sm.advance()

        if success:
            new_phase = sm.get_current_phase()
            state.current_phase = new_phase
            state.progress = 0.0
            self.persistence.save_state(state)

            print(f"✅ 已推進到階段: {new_phase}")
        else:
            print(f"❌ 無法推進階段")
            return 1

        return 0


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Ralph Mode - 任務長時監控 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  ralph init task-001              # 初始化任務
  ralph start task-001             # 啟動監控
  ralph start task-001 --interval 60  # 自訂檢查間隔
  ralph status task-001            # 查看狀態
  ralph list                      # 列出所有任務
  ralph stop task-001              # 停止監控
  ralph advance task-001           # 推進到下一階段
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Ralph Mode v{RalphCLI.VERSION}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # start
    start_parser = subparsers.add_parser("start", help="啟動任務監控")
    start_parser.add_argument("task_id", help="任務 ID")
    start_parser.add_argument(
        "--interval", "-i",
        type=int,
        default=30,
        help="檢查間隔（秒），預設 30"
    )
    start_parser.add_argument(
        "--background", "-b",
        action="store_true",
        help="背景執行"
    )

    # status
    status_parser = subparsers.add_parser("status", help="查看任務狀態")
    status_parser.add_argument("task_id", help="任務 ID")

    # stop
    stop_parser = subparsers.add_parser("stop", help="停止任務監控")
    stop_parser.add_argument("task_id", help="任務 ID")

    # list
    list_parser = subparsers.add_parser("list", help="列出所有任務")
    list_parser.add_argument(
        "--status", "-s",
        choices=["pending", "running", "paused", "completed", "failed"],
        help="依狀態過濾"
    )

    # init
    init_parser = subparsers.add_parser("init", help="初始化新任務")
    init_parser.add_argument("task_id", help="任務 ID")
    init_parser.add_argument(
        "--phase", "-p",
        default="init",
        help="初始階段，預設 init"
    )

    # advance
    advance_parser = subparsers.add_parser("advance", help="推進任務階段")
    advance_parser.add_argument("task_id", help="任務 ID")
    advance_parser.add_argument(
        "--to", "-t",
        help="目標階段"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    cli = RalphCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())