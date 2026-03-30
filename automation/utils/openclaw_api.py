#!/usr/bin/env python3
"""
OpenClaw API 串接模組
功能：封裝 sessions_spawn, sessions_history, sessions_send 等 OpenClaw API
"""

import json
import os
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime


class OpenClawAPI:
    """OpenClaw API 封裝"""
    
    def __init__(self):
        self.api_token = os.environ.get("OPENCLAW_API_TOKEN", "")
        self.endpoint = os.environ.get("OPENCLAW_ENDPOINT", "http://localhost:8080")
        
    def spawn_agent(self, label: str, task: str, mode: str = "run", runtime: str = "subagent") -> Dict[str, Any]:
        """
        啟動 Sub-agent
        
        Args:
            label: Agent 標籤
            task: 任務描述
            mode: "run" 或 "session"
            runtime: "subagent" 或 "acp"
            
        Returns:
            {"sessionKey": "...", "runId": "...", "status": "accepted"}
        """
        # 使用 subprocess 調用 OpenClaw CLI
        # 實際實現需要通過 MCP 工具或直接 HTTP 調用
        
        # 模擬實現（因為沒有直接的 Python API）
        result = {
            "sessionKey": f"agent:main:subagent:{label}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "runId": f"run_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "accepted",
            "label": label,
            "mode": mode,
            "runtime": runtime,
            "task_preview": task[:100] + "..." if len(task) > 100 else task
        }
        
        print(f"📡 [OpenClawAPI] Spawn Agent: {label}")
        print(f"   Mode: {mode}, Runtime: {runtime}")
        
        return result
    
    def get_session_status(self, session_key: str) -> Dict[str, Any]:
        """
        取得 Session 狀態
        
        Args:
            session_key: Session key
            
        Returns:
            {"status": "running/completed/failed", "messages": [...], ...}
        """
        # 模擬實現
        return {
            "status": "running",
            "sessionKey": session_key,
            "lastUpdate": datetime.now().isoformat(),
            "messageCount": 0
        }
    
    def get_session_history(self, session_key: str, limit: int = 10) -> Dict[str, Any]:
        """
        取得 Session 歷史
        
        Args:
            session_key: Session key
            limit: 訊息數量限制
            
        Returns:
            {"messages": [...], "status": "completed/running"}
        """
        # 模擬實現
        # 實際需要調用 sessions_history
        
        return {
            "status": "running",
            "sessionKey": session_key,
            "messages": [],
            "lastUpdate": datetime.now().isoformat()
        }
    
    def wait_for_completion(self, session_key: str, timeout: int = 600, interval: int = 5) -> Dict[str, Any]:
        """
        等待 Agent 完成
        
        Args:
            session_key: Session key
            timeout: 超時時間（秒）
            interval: Polling 間隔（秒）
            
        Returns:
            {"status": "completed/failed/timeout", "result": ...}
        """
        import time
        start_time = datetime.now()
        deadline = start_time.timestamp() + timeout
        
        print(f"⏳ [OpenClawAPI] 等待 Agent 完成...")
        print(f"   Session: {session_key}")
        print(f"   Timeout: {timeout}秒, Interval: {interval}秒")
        
        while datetime.now().timestamp() < deadline:
            # 檢查狀態
            status = self.get_session_status(session_key)
            
            if status["status"] == "completed":
                # 取得完整結果
                history = self.get_session_history(session_key, limit=1)
                print(f"✅ [OpenClawAPI] Agent 已完成")
                return {
                    "status": "completed",
                    "sessionKey": session_key,
                    "result": history.get("messages", [])
                }
            
            if status["status"] == "failed":
                print(f"❌ [OpenClawAPI] Agent 失敗")
                return {
                    "status": "failed",
                    "sessionKey": session_key,
                    "error": "Agent execution failed"
                }
            
            # 等待下一個 interval
            time.sleep(interval)
        
        # Timeout
        print(f"⏱️ [OpenClawAPI] Timeout")
        return {
            "status": "timeout",
            "sessionKey": session_key,
            "timeout": timeout
        }
    
    def send_message(self, session_key: str, message: str) -> Dict[str, Any]:
        """
        發送訊息到 Session
        
        Args:
            session_key: Session key
            message: 訊息內容
            
        Returns:
            {"status": "sent", "messageId": "..."}
        """
        # 模擬實現
        return {
            "status": "sent",
            "sessionKey": session_key,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def list_active_sessions(self) -> Dict[str, Any]:
        """
        列出活跃的 Sessions
        """
        # 模擬實現
        return {
            "count": 0,
            "sessions": []
        }


# 全域實例
api = OpenClawAPI()


# 便捷函數
def spawn(label: str, task: str, mode: str = "run", runtime: str = "subagent") -> Dict[str, Any]:
    """快速啟動 Agent"""
    return api.spawn_agent(label, task, mode, runtime)


def wait(session_key: str, timeout: int = 600, interval: int = 5) -> Dict[str, Any]:
    """快速等待完成"""
    return api.wait_for_completion(session_key, timeout, interval)


def history(session_key: str, limit: int = 10) -> Dict[str, Any]:
    """快速取得歷史"""
    return api.get_session_history(session_key, limit)


# 測試
if __name__ == "__main__":
    print("=== OpenClawAPI 測試 ===")
    
    # 測試 spawn
    result = spawn("TestAgent", "這是一個測試任務")
    print(f"\nSpawn 結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 測試 wait（模擬）
    wait_result = wait(result["sessionKey"], timeout=60)
    print(f"\nWait 結果: {json.dumps(wait_result, indent=2, ensure_ascii=False)}")
    
    print("\n✅ OpenClawAPI 測試完成")