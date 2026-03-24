#!/usr/bin/env python3
"""
Quality Watch Daemon
====================
methodology-v2 的持續品質監控

使用方式：
    python3 quality_watch.py start [--project <path>]
    python3 quality_watch.py stop [--project <path>]
    python3 quality_watch.py status [--project <path>]
    python3 quality_watch.py watch [--project <path>]

Lifecycle:
    methodology init → quality_watch start
    methodology finish → quality_watch stop
"""

import os
import sys
import json
import time
import signal
import argparse
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# 嘗試匯入 watchdog（可選）
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File monitoring disabled.")
    print("Install with: pip install watchdog")


class QualityLog:
    """品質日誌"""
    
    def __init__(self, project_path: str):
        self.log_file = Path(project_path) / ".methodology" / "quality_log.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def append(self, entry: Dict):
        """新增日誌 entry"""
        entries = self.read_all()
        entries.append(entry)
        self.log_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    
    def read_all(self) -> List[Dict]:
        """讀取所有日誌"""
        if not self.log_file.exists():
            return []
        return json.loads(self.log_file.read_text())
    
    def get_critical(self) -> List[Dict]:
        """取得所有 CRITICAL 問題"""
        return [e for e in self.read_all() if e.get("severity") == "CRITICAL"]
    
    def clear(self):
        """清除日誌"""
        self.log_file.unlink(missing_ok=True)


class QualityGateRunner:
    """執行 quality-gate 檢查"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
    
    def run(self, file_path: Optional[str] = None) -> Dict:
        """執行 quality-gate check"""
        import sys
        sys.path.insert(0, self.project_path)
        
        # 嘗試呼叫 CLI
        try:
            result = subprocess.run(
                [sys.executable, "cli.py", "quality-gate", "check"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": passed,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "file": file_path,
                "severity": "CRITICAL" if not passed else "INFO"
            }
        except subprocess.TimeoutExpired:
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": "Timeout (>60s)",
                "severity": "CRITICAL"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": str(e),
                "severity": "ERROR"
            }


class WatchdogHandler(FileSystemEventHandler):
    """檔案變更監控處理"""
    
    def __init__(self, project_path: str, log: QualityLog, runner: QualityGateRunner):
        self.project_path = project_path
        self.log = log
        self.runner = runner
        self.last_check = {}  # 防止重複檢查
        self.debounce_seconds = 2  # 防抖動秒數
    
    def should_check(self, file_path: str) -> bool:
        """檢查是否應該檢查（防抖動）"""
        now = time.time()
        last = self.last_check.get(file_path, 0)
        
        if now - last < self.debounce_seconds:
            return False
        
        self.last_check[file_path] = now
        return True
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # 跳過非程式碼檔案
        ext = Path(event.src_path).suffix
        if ext not in [".py", ".md", ".json", ".yaml", ".yml", ".sh"]:
            return
        
        if self.should_check(event.src_path):
            print(f"[QualityWatch] File modified: {event.src_path}")
            result = self.runner.run(event.src_path)
            self.log.append(result)
            
            if not result["passed"]:
                print(f"[QualityWatch] ⚠️ Quality check FAILED")
                if result.get("severity") == "CRITICAL":
                    print(f"[QualityWatch] 🔴 CRITICAL: {result.get('error', result.get('stderr', 'Unknown'))}")


class QualityWatch:
    """Quality Watch Daemon"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.pid_file = self.project_path / ".methodology" / "watch.pid"
        self.log = QualityLog(str(self.project_path))
        self.runner = QualityGateRunner(str(self.project_path))
        self.observer: Optional[Observer] = None
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """設定信號處理"""
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """收到停止信號"""
        print("[QualityWatch] Received signal, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _write_pid(self):
        """寫入 PID"""
        self.pid_file.parent.mkdir(parents=True, exist_ok=True)
        self.pid_file.write_text(str(os.getpid()))
    
    def _is_running(self) -> bool:
        """檢查是否正在運行"""
        if not self.pid_file.exists():
            return False
        
        try:
            pid = int(self.pid_file.read_text())
            # 檢查進程是否存在
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError):
            # PID 不存在或已終止
            self.pid_file.unlink(missing_ok=True)
            return False
    
    def start(self):
        """啟動 daemon"""
        if self._is_running():
            print(f"[QualityWatch] Already running (PID: {self.pid_file.read_text()})")
            return False
        
        print(f"[QualityWatch] Starting...")
        self._write_pid()
        
        if not WATCHDOG_AVAILABLE:
            print("[QualityWatch] Warning: Running without file monitoring")
            print("[QualityWatch] Will check manually with 'watch' command")
            return True
        
        # 啟動檔案監控
        handler = WatchdogHandler(str(self.project_path), self.log, self.runner)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.project_path), recursive=True)
        self.observer.start()
        
        print(f"[QualityWatch] Started (PID: {os.getpid()})")
        print(f"[QualityWatch] Monitoring: {self.project_path}")
        print(f"[QualityWatch] Log: {self.log.log_file}")
        print("[QualityWatch] Press Ctrl+C to stop")
        
        # 保持運行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        
        return True
    
    def stop(self):
        """停止 daemon"""
        if not self._is_running():
            print("[QualityWatch] Not running")
            return False
        
        pid = int(self.pid_file.read_text())
        
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"[QualityWatch] Stopped (PID: {pid})")
        except ProcessLookupError:
            print("[QualityWatch] Process not found")
        
        self.pid_file.unlink(missing_ok=True)
        return True
    
    def status(self) -> Dict:
        """取得狀態"""
        running = self._is_running()
        pid = self.pid_file.read_text() if self.pid_file.exists() else None
        
        critical = self.log.get_critical()
        
        return {
            "running": running,
            "pid": pid,
            "project": str(self.project_path),
            "critical_count": len(critical),
            "recent_critical": critical[-5:] if critical else []
        }
    
    def watch_once(self):
        """執行一次檢查（用於手動檢查）"""
        print("[QualityWatch] Running quality gate check...")
        result = self.runner.run()
        self.log.append(result)
        
        print(f"[QualityWatch] Result: {'PASS' if result['passed'] else 'FAIL'}")
        if not result["passed"]:
            print(f"[QualityWatch] Error: {result.get('error', result.get('stderr', 'See log'))}")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Quality Watch Daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "watch"],
                        help="Command to run")
    parser.add_argument("--project", "-p", default=".",
                        help="Project path (default: current directory)")
    
    args = parser.parse_args()
    
    watch = QualityWatch(args.project)
    
    if args.command == "start":
        watch.start()
    elif args.command == "stop":
        watch.stop()
    elif args.command == "status":
        status = watch.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.command == "watch":
        watch.watch_once()


if __name__ == "__main__":
    main()
