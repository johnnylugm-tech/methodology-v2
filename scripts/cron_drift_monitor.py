#!/usr/bin/env python3
"""
Cron job script for Drift Monitor.
執行頻率：每小時一次（可在 crontab 中設定）

Usage:
    # 在 crontab 中加入：
    0 * * * * /path/to/venv/bin/python /path/to/project/scripts/cron_drift_monitor.py
    
    # 或使用 openclaw cron（如果有的話）
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quality_gate.drift_monitor import DriftMonitor
from orchestration import create_feedback_store


def main():
    project_path = os.environ.get("DRIFT_PROJECT_PATH", str(project_root))

    # Ensure logs directory exists
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Create log file path
    log_file = logs_dir / "drift_monitor.log"

    # Redirect stdout to log file (append mode)
    original_stdout = sys.stdout
    with open(log_file, "a") as f:
        sys.stdout = f
        try:
            _run_monitor(project_path)
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.stdout = original_stdout
            print(f"DRIFT MONITOR ERROR: {e}")
            return 1
        finally:
            sys.stdout = original_stdout
    return 0


def _run_monitor(project_path: str):
    # Establish integrated system
    store = create_feedback_store()
    monitor = DriftMonitor(project_path=project_path, feedback_store=store)

    # Execute drift check
    alert = monitor.run_and_alert()

    if alert:
        print(f"[{alert.timestamp}] DRIFT ALERT: {alert.severity.upper()} - {alert.message}")
        print(f"  Drift score: {alert.drift_score}")
        print(f"  Artifacts: {', '.join(alert.artifacts)}")
        print(f"  Recommended action: {alert.recommended_action}")
        print(f"  Alert ID: {alert.id}")
        # Return non-zero exit code so cron knows there's a problem
        raise SystemExit(1)
    else:
        print(f"[{__import__('datetime').datetime.now().isoformat()}] No drift detected.")


if __name__ == "__main__":
    sys.exit(main())
