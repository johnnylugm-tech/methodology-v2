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
    python3 quality_watch.py constitution [--project <path>] [--type <srs|sad|test_plan|all>]

Lifecycle:
    methodology init → quality_watch start
    methodology finish → quality_watch stop

Constitution Integration:
    --constitution        執行 Constitution 原則檢查
    --type <check_type>   檢查類型: srs, sad, test_plan, all
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
# 延遲匯入，在需要時才匯入
WATCHDOG_AVAILABLE = False
Observer = None
FileSystemEventHandler = None

def _check_watchdog():
    global WATCHDOG_AVAILABLE, Observer, FileSystemEventHandler
    if WATCHDOG_AVAILABLE:
        return True
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        WATCHDOG_AVAILABLE = True
        return True
    except ImportError:
        print("Warning: watchdog not installed. File monitoring disabled.")
        print("Install with: pip install watchdog")
        return False

# Constitution 檢查器路徑
CONSTITUTION_CHECKER_PATH = Path(__file__).parent / "quality_gate" / "constitution"

# Decision Gate 路徑
DECISION_LOG_PATH = Path(__file__).parent / ".methodology" / "decisions" / "decision_log.json"


class DecisionRunner:
    """執行 Decision Gate 檢查"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.decision_log = self.project_path / ".methodology" / "decisions" / "decision_log.json"
    
    def run(self) -> Dict:
        """執行 Decision Gate 檢查
        
        檢查是否有未確認的 MEDIUM/HIGH 風險決策
        
        Returns:
            檢查結果字典
        """
        if not self.decision_log.exists():
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": True,
                "unconfirmed_decisions": [],
                "severity": "INFO"
            }
        
        try:
            decisions = json.loads(self.decision_log.read_text())
            
            # 找出未確認的 MEDIUM/HIGH 風險決策
            unconfirmed = [
                d for d in decisions
                if d.get("risk") in ["MEDIUM", "HIGH"] and not d.get("confirmed", False)
            ]
            
            passed = len(unconfirmed) == 0
            
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": passed,
                "unconfirmed_decisions": unconfirmed,
                "total_decisions": len(decisions),
                "severity": "CRITICAL" if not passed else "INFO"
            }
        except (json.JSONDecodeError, IOError) as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": str(e),
                "severity": "ERROR"
            }


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


class ConstitutionRunner:
    """執行 Constitution 原則檢查"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.docs_path = self.project_path / "docs"
    
    def run(self, check_type: str = "all") -> Dict:
        """執行 Constitution check
        
        Args:
            check_type: 檢查類型 (srs, sad, test_plan, all)
            
        Returns:
            檢查結果字典
        """
        if not self.docs_path.exists():
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": f"docs/ directory not found: {self.docs_path}",
                "check_type": check_type,
                "severity": "CRITICAL"
            }
        
        # 嘗試呼叫 Constitution runner
        try:
            result = subprocess.run(
                [sys.executable, str(CONSTITUTION_CHECKER_PATH / "runner.py"),
                 "--path", str(self.project_path),
                 "--type", check_type,
                 "--format", "json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "PYTHONPATH": str(self.project_path)}
            )
            
            # 解析 JSON 結果
            try:
                result_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                result_data = {
                    "passed": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": result_data.get("passed", result.returncode == 0),
                "check_type": check_type,
                "score": result_data.get("score", 0),
                "violations": result_data.get("violations", []),
                "details": result_data,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else "",
                "severity": "CRITICAL" if not result_data.get("passed", False) else "INFO"
            }
        except subprocess.TimeoutExpired:
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": "Timeout (>30s)",
                "check_type": check_type,
                "severity": "CRITICAL"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "passed": False,
                "error": str(e),
                "check_type": check_type,
                "severity": "ERROR"
            }


class WatchdogHandler:
    """檔案變更監控處理"""
    
    def __init__(self, project_path: str, log: QualityLog, runner: QualityGateRunner, 
                 constitution_runner: ConstitutionRunner = None, enable_constitution: bool = False,
                 decision_runner: DecisionRunner = None):
        self.project_path = project_path
        self.log = log
        self.runner = runner
        self.constitution_runner = constitution_runner
        self.enable_constitution = enable_constitution
        self.decision_runner = decision_runner
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
    
    def _trigger_decision_check(self):
        """觸發 Decision Gate 檢查"""
        if not self.decision_runner:
            return
        
        result = self.decision_runner.run()
        self.log.append({
            "type": "decision_gate",
            **result
        })
        
        if not result["passed"]:
            unconfirmed = result.get("unconfirmed_decisions", [])
            print(f"[QualityWatch] ⚠️ Decision Gate: {len(unconfirmed)} unconfirmed decision(s)")
            for d in unconfirmed[:3]:
                print(f"[QualityWatch] 🔴 [{d.get('risk')}] {d.get('key')}: {d.get('description', '')}")
        else:
            total = result.get("total_decisions", 0)
            print(f"[QualityWatch] ✅ Decision Gate: {total} decision(s) checked")
    
    def _trigger_constitution_check(self, file_path: str):
        """觸發 Constitution 檢查"""
        if not self.enable_constitution or not self.constitution_runner:
            return
        
        # 根據修改的檔案類型決定檢查類型
        file_name = Path(file_path).name.lower()
        
        if "srs" in file_name or "需求" in file_name:
            check_type = "srs"
        elif "sad" in file_name or "架構" in file_name:
            check_type = "sad"
        elif "test" in file_name or "測試" in file_name:
            check_type = "test_plan"
        else:
            check_type = "all"
        
        print(f"[QualityWatch] Running Constitution check ({check_type})...")
        result = self.constitution_runner.run(check_type)
        self.log.append({
            "type": "constitution",
            **result
        })
        
        if not result["passed"]:
            print(f"[QualityWatch] ⚠️ Constitution check FAILED ({check_type})")
            if result.get("severity") == "CRITICAL":
                violations = result.get("violations", [])
                for v in violations[:3]:
                    print(f"[QualityWatch] 🔴 {v.get('type', 'unknown')}: {v.get('message', '')}")
        else:
            print(f"[QualityWatch] ✅ Constitution check PASSED ({check_type}) - Score: {result.get('score', 0):.1f}%")
    
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
            
            # 如果啟用 Constitution 檢查，且修改的是 docs 目錄下的檔案
            if self.enable_constitution and "docs" in event.src_path:
                self._trigger_constitution_check(event.src_path)
            
            # Decision Gate 檢查
            self._trigger_decision_check()
            
            if not result["passed"]:
                print(f"[QualityWatch] ⚠️ Quality check FAILED")
                if result.get("severity") == "CRITICAL":
                    print(f"[QualityWatch] 🔴 CRITICAL: {result.get('error', result.get('stderr', 'Unknown'))}")


class QualityWatch:
    """Quality Watch Daemon"""
    
    def __init__(self, project_path: str, enable_constitution: bool = False):
        self.project_path = Path(project_path).resolve()
        self.pid_file = self.project_path / ".methodology" / "watch.pid"
        self.log = QualityLog(str(self.project_path))
        self.runner = QualityGateRunner(str(self.project_path))
        self.constitution_runner = ConstitutionRunner(str(self.project_path))
        self.decision_runner = DecisionRunner(str(self.project_path))
        self.enable_constitution = enable_constitution
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
        
        if not _check_watchdog():
            print("[QualityWatch] Warning: Running without file monitoring")
            print("[QualityWatch] Will check manually with 'watch' command")
            return True
        
        # 啟動檔案監控
        handler = WatchdogHandler(
            str(self.project_path), 
            self.log, 
            self.runner,
            self.constitution_runner,
            self.enable_constitution,
            self.decision_runner
        )
        self.observer = Observer()
        self.observer.schedule(handler, str(self.project_path), recursive=True)
        self.observer.start()
        
        print(f"[QualityWatch] Started (PID: {os.getpid()})")
        print(f"[QualityWatch] Monitoring: {self.project_path}")
        print(f"[QualityWatch] Log: {self.log.log_file}")
        
        if self.enable_constitution:
            print("[QualityWatch] Constitution checks: ENABLED")
        
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
    
    def watch_once(self, check_constitution: bool = False, constitution_type: str = "all"):
        """執行一次檢查（用於手動檢查）"""
        print("[QualityWatch] Running quality gate check...")
        result = self.runner.run()
        self.log.append(result)
        
        print(f"[QualityWatch] Quality Gate Result: {'PASS' if result['passed'] else 'FAIL'}")
        if not result["passed"]:
            print(f"[QualityWatch] Error: {result.get('error', result.get('stderr', 'See log'))}")
        
        # Constitution 檢查
        if check_constitution:
            print(f"\n[QualityWatch] Running Constitution check ({constitution_type})...")
            const_result = self.constitution_runner.run(constitution_type)
            self.log.append({
                "type": "constitution",
                **const_result
            })
            
            print(f"[QualityWatch] Constitution Result: {'PASS' if const_result['passed'] else 'FAIL'}")
            print(f"[QualityWatch] Score: {const_result.get('score', 0):.1f}%")
            
            if not const_result["passed"]:
                violations = const_result.get("violations", [])
                for v in violations[:3]:
                    print(f"[QualityWatch] \u26a0\ufe0f  {v.get('type', 'unknown')}: {v.get('message', '')}")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Quality Watch Daemon")
    parser.add_argument("command", choices=["start", "stop", "status", "watch", "constitution"],
                        help="Command to run")
    parser.add_argument("--project", "-p", default=".",
                        help="Project path (default: current directory)")
    
    # Constitution 選項
    parser.add_argument("--constitution", "-c", action="store_true",
                        help="Enable Constitution checks")
    parser.add_argument("--type", "-t", choices=["srs", "sad", "test_plan", "all"], 
                        default="all",
                        help="Constitution check type (default: all)")
    
    args = parser.parse_args()
    
    watch = QualityWatch(args.project, enable_constitution=args.constitution)
    
    if args.command == "start":
        watch.start()
    elif args.command == "stop":
        watch.stop()
    elif args.command == "status":
        status = watch.status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.command == "watch":
        watch.watch_once(check_constitution=args.constitution, constitution_type=args.type)
    elif args.command == "constitution":
        # 專門的 Constitution 檢查命令
        print(f"[QualityWatch] Running Constitution check ({args.type})...")
        result = watch.constitution_runner.run(args.type)
        
        # 格式化輸出
        if result["passed"]:
            print(f"\u2705 Constitution check PASSED - Score: {result.get('score', 0):.1f}%")
        else:
            print(f"\u274c Constitution check FAILED - Score: {result.get('score', 0):.1f}%")
            
            violations = result.get("violations", [])
            if violations:
                print("\nViolations:")
                for v in violations:
                    print(f"  \u2022 [{v.get('severity', 'UNKNOWN')}] {v.get('type', 'unknown')}: {v.get('message', '')}")


if __name__ == "__main__":
    main()
