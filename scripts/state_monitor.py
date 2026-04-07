#!/usr/bin/env python3
"""
state_monitor.py — Runtime Metrics 趨勢檢查
==========================================

每 5 分鐘執行，檢查預警阈值，發送 Telegram 通知

使用方式：
    python state_monitor.py --check-trends
    python state_monitor.py --project-path /path/to/project

Crontab 設定：
    */5 * * * * cd /path/to/project && python3 .methodology/state_monitor.py --check-trends
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# 預警阈值設定
THRESHOLDS = {
    "blocks": 5,              # BLOCK 次數警戒線
    "ab_rounds": 5,           # A/B 來回警戒線（HR-12）
    "elapsed_minutes": 120,   # Phase 執行時間警戒線（預設值，會動態計算）
    "integrity_min": 40,      # Integrity 分數底線（HR-14）
}

DEFAULT_STATE_PATH = ".methodology/state.json"


def check_trends(project_path: str) -> int:
    """
    檢查趨勢並發送預警
    
    Returns:
        0: 無預警或檢查成功
        1: 有預警觸發
    """
    state_path = Path(project_path) / DEFAULT_STATE_PATH
    
    if not state_path.exists():
        print(f"⚠️  state.json not found at {state_path}")
        print("   Phase may not have started yet, or project path is incorrect.")
        return 0  # 不算錯誤，只是還沒開始
    
    try:
        state = json.loads(state_path.read_text())
    except Exception as e:
        print(f"❌  Failed to read state.json: {e}")
        return 1
    
    ps = state.get("phase_state", {})
    
    # 計算已耗費時間
    started = ps.get("started_at")
    elapsed_minutes = 0
    if started:
        try:
            start_time = datetime.fromisoformat(started)
            elapsed_seconds = (datetime.now(timezone.utc) - start_time).total_seconds()
            elapsed_minutes = int(elapsed_seconds // 60)
            ps["elapsed_minutes"] = elapsed_minutes
        except Exception as e:
            print(f"⚠️  Failed to parse started_at: {e}")
    
    # 檢查預警阈值
    alerts = []
    
    blocks = ps.get("blocks", 0)
    if blocks >= THRESHOLDS["blocks"]:
        alerts.append({
            "type": "BLOCK_COUNT_HIGH",
            "current": blocks,
            "threshold": THRESHOLDS["blocks"],
            "message": f"B BLOCK 次數過高: {blocks} (警戒線: {THRESHOLDS['blocks']})"
        })
    
    ab_rounds = ps.get("ab_rounds", 0)
    if ab_rounds >= THRESHOLDS["ab_rounds"]:
        alerts.append({
            "type": "AB_ROUND_HIGH", 
            "current": ab_rounds,
            "threshold": THRESHOLDS["ab_rounds"],
            "message": f"⚠️  A/B 來回過多: {ab_rounds} (警戒線: {THRESHOLDS['ab_rounds']})"
        })
    
    # HR-13: Phase 執行時間上限（3× 預估時間）
    estimated_minutes = ps.get("estimated_minutes", THRESHOLDS["elapsed_minutes"] // 3)
    timeout_threshold = estimated_minutes * 3
    if elapsed_minutes >= timeout_threshold:
        alerts.append({
            "type": "PHASE_TIMEOUT",
            "current": elapsed_minutes,
            "threshold": timeout_threshold,
            "estimated": estimated_minutes,
            "message": f"⏱️  Phase 執行過久: {elapsed_minutes} 分鐘 (預估: {estimated_minutes}, 警戒線: {timeout_threshold})"
        })
    
    # HR-14: Integrity 分數底線
    integrity_score = ps.get("integrity_score", 100)
    if integrity_score < THRESHOLDS["integrity_min"]:
        alerts.append({
            "type": "INTEGRITY_LOW",
            "current": integrity_score,
            "threshold": THRESHOLDS["integrity_min"],
            "message": f"🔒  Integrity 分數過低: {integrity_score} (底線: {THRESHOLDS['integrity_min']})"
        })
    
    # 寫回 state.json
    ps["last_check_at"] = datetime.now(timezone.utc).isoformat()
    state["phase_state"] = ps
    state["trend_alerts"] = [a["type"] for a in alerts]  # 只存 type 列表
    
    try:
        state_path.write_text(json.dumps(state, indent=2))
    except Exception as e:
        print(f"⚠️  Failed to write state.json: {e}")
    
    # 發送預警（只有新的 alert 或 超過阈值才發）
    if alerts:
        print(f"🚨  Found {len(alerts)} alert(s):")
        for alert in alerts:
            print(f"    {alert['message']}")
        
        send_telegram_alert(state, alerts)
        return 1
    else:
        print(f"✅  No alerts. Phase {state.get('current_phase', '?')} running for {elapsed_minutes} min")
        return 0


def send_telegram_alert(state: dict, alerts: list):
    """
    發送 Telegram 預警通知
    """
    phase = state.get("current_phase", "?")
    ps = state.get("phase_state", {})
    
    # 構建訊息
    lines = [
        f"🚨  [Phase {phase} Runtime Alert]",
        ""
    ]
    
    for alert in alerts:
        lines.append(alert["message"])
    
    lines.extend([
        "",
        "📊  當前狀態:",
        f"   - BLOCK: {ps.get('blocks', 0)} 次",
        f"   - A/B 來回: {ps.get('ab_rounds', 0)} 輪",
        f"   - 已耗時: {ps.get('elapsed_minutes', 0)} 分鐘",
        f"   - 最後分數: {ps.get('last_gate_score', 'N/A')}",
        "",
        "💡  建議: 檢查 FrameworkEnforcer 輸出或考慮分割 Phase"
    ])
    
    message = "\n".join(lines)
    
    # 使用 message tool 發送
    try:
        import subprocess
        # 呼叫 OpenClaw message tool
        result = subprocess.run([
            "openclaw", "message",
            "--action", "send",
            "--channel", "telegram",
            "--message", message
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("    ✅  Telegram notification sent")
        else:
            print(f"    ⚠️  Telegram notification failed: {result.stderr}")
    except FileNotFoundError:
        print("    ⚠️  openclaw command not found, skipping Telegram notification")
    except Exception as e:
        print(f"    ⚠️  Failed to send Telegram: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Runtime Metrics State Monitor - 檢查 Phase 執行趨勢並發送預警"
    )
    parser.add_argument(
        "--check-trends",
        action="store_true",
        help="執行趨勢檢查"
    )
    parser.add_argument(
        "--project-path",
        type=str,
        default=".",
        help="專案路徑 (預設: .)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只顯示，不發送通知"
    )
    
    args = parser.parse_args()
    
    # 如果沒有參數，顯示說明
    if len(sys.argv) == 1:
        print(__doc__)
        print("\n使用方法：")
        print("  1. 手動執行: python state_monitor.py --check-trends")
        print("  2. Cron Job:  */5 * * * * python3 state_monitor.py --check-trends")
        print("\n預警阈值：")
        for key, value in THRESHOLDS.items():
            print(f"  - {key}: {value}")
        return 0
    
    return check_trends(args.project_path)


if __name__ == "__main__":
    sys.exit(main())
