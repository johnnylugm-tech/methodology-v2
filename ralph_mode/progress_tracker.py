"""
Ralph Mode - 進度追蹤器

追蹤並記錄任務的執行進度，支援寫入 PROGRESS.md 檔案。

Author: methodology-v2
Version: 1.0.0
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Framework Enforcement
try:
    from methodology import FrameworkEnforcer
    _FRAMEWORK_OK = True
except ImportError:
    _FRAMEWORK_OK = False


class RalphProgressTracker:
    """
    Ralph Mode 進度追蹤器
    
    追蹤任務的執行進度，並將進度寫入 PROGRESS.md 檔案。
    
    Attributes:
        task_id: 任務 ID
        progress_file: 進度檔案路徑
    
    Example:
        >>> tracker = RalphProgressTracker("task-001")
        >>> tracker.update_progress("init", 25.0)
        >>> tracker.update_progress("run_batch", 50.0)
        >>> print(tracker.get_progress())
    """

    def __init__(self, task_id: str, output_dir: Optional[str] = None):
        """
        初始化進度追蹤器
        
        Args:
            task_id: 任務 ID
            output_dir: 輸出目錄，預設為 .ralph/progress
        """
        self.task_id = task_id
        
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), ".ralph", "progress")
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.output_dir / "PROGRESS.md"
        self._progress_data: Dict[str, Any] = {
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "phases": {},
            "current_phase": "init",
            "overall_progress": 0.0,
            "last_updated": None
        }

    def update_progress(
        self,
        phase: str,
        progress: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新進度
        
        Args:
            phase: 階段名稱
            progress: 進度值 (0-100)
            metadata: 額外元資料
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新階段進度
            if phase not in self._progress_data["phases"]:
                self._progress_data["phases"][phase] = {
                    "started_at": datetime.now().isoformat(),
                    "updates": []
                }
            
            update = {
                "timestamp": datetime.now().isoformat(),
                "progress": max(0.0, min(100.0, progress)),
                "metadata": metadata or {}
            }
            self._progress_data["phases"][phase]["updates"].append(update)
            self._progress_data["phases"][phase]["current_progress"] = progress
            
            # 更新當前階段和總進度
            self._progress_data["current_phase"] = phase
            self._progress_data["last_updated"] = datetime.now().isoformat()
            
            # 計算整體進度
            self._recalculate_overall_progress()
            
            # 寫入檔案
            return self._write_progress_file()

        except Exception as e:
            print(f"[Ralph] 更新進度失敗: {e}")
            return False

    def _recalculate_overall_progress(self) -> None:
        """重新計算整體進度"""
        phases = self._progress_data["phases"]
        if not phases:
            return

        total_progress = sum(
            phase_data.get("current_progress", 0.0)
            for phase_data in phases.values()
        )
        self._progress_data["overall_progress"] = total_progress / len(phases)

    def _write_progress_file(self) -> bool:
        """寫入進度檔案"""
        try:
            content = self._generate_markdown()
            self.progress_file.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            print(f"[Ralph] 寫入進度檔案失敗: {e}")
            return False

    def _generate_markdown(self) -> str:
        """生成 Markdown 格式的進度報告"""
        lines = [
            f"# 任務進度追蹤: {self.task_id}",
            "",
            f"**起始時間**: {self._progress_data['started_at']}",
            f"**最後更新**: {self._progress_data['last_updated'] or 'N/A'}",
            f"**當前階段**: {self._progress_data['current_phase']}",
            f"**整體進度**: {self._progress_data['overall_progress']:.1f}%",
            "",
            "## 階段詳情",
            ""
        ]

        # Phase 定義的標準順序
        phase_order = ["init", "run_batch", "extract", "eval", "report", "done"]
        
        for phase_name in phase_order:
            if phase_name in self._progress_data["phases"]:
                phase_data = self._progress_data["phases"][phase_name]
                progress = phase_data.get("current_progress", 0.0)
                started = phase_data.get("started_at", "N/A")
                
                # 進度條
                bar_len = 20
                filled = int(progress / 100 * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                
                lines.append(f"### {phase_name}")
                lines.append(f"- **進度**: {progress:.1f}% `{bar}`")
                lines.append(f"- **開始時間**: {started}")
                
                if phase_data.get("updates"):
                    last_update = phase_data["updates"][-1]
                    lines.append(f"- **最後更新**: {last_update['timestamp']}")
                    
                    if last_update.get("metadata"):
                        for k, v in last_update["metadata"].items():
                            lines.append(f"  - {k}: {v}")
                
                lines.append("")

        # 其他未定義的階段
        for phase_name, phase_data in self._progress_data["phases"].items():
            if phase_name not in phase_order:
                progress = phase_data.get("current_progress", 0.0)
                lines.append(f"### {phase_name}")
                lines.append(f"- **進度**: {progress:.1f}%")
                lines.append("")

        # 總結
        lines.extend([
            "## 總結",
            "",
            f"- **任務 ID**: {self.task_id}",
            f"- **運行了**: {self._calculate_duration()}",
            f"- **更新次數**: {self._count_updates()}",
            ""
        ])

        return "\n".join(lines)

    def _calculate_duration(self) -> str:
        """計算任務運行時長"""
        started = self._progress_data.get("started_at")
        if not started:
            return "N/A"
        
        try:
            start_dt = datetime.fromisoformat(started)
            now = datetime.now()
            duration = now - start_dt
            
            hours, remainder = divmod(int(duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except Exception:
            return "N/A"

    def _count_updates(self) -> int:
        """計算更新次數"""
        total = 0
        for phase_data in self._progress_data["phases"].values():
            total += len(phase_data.get("updates", []))
        return total

    def get_progress(self) -> Dict[str, Any]:
        """取得進度資料"""
        return self._progress_data.copy()

    def get_phase_progress(self, phase: str) -> Optional[float]:
        """取得特定階段的進度"""
        if phase not in self._progress_data["phases"]:
            return None
        return self._progress_data["phases"][phase].get("current_progress")

    def complete_phase(self, phase: str) -> bool:
        """標記階段完成（進度 100%）"""
        return self.update_progress(phase, 100.0, {"status": "completed"})

    def complete_task(self) -> bool:
        """標記任務完成"""
        self._progress_data["completed_at"] = datetime.now().isoformat()
        return self._write_progress_file()

    def get_summary(self) -> str:
        """取得進度摘要"""
        return (
            f"Task: {self.task_id} | "
            f"Phase: {self._progress_data['current_phase']} | "
            f"Progress: {self._progress_data['overall_progress']:.1f}%"
        )