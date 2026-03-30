#!/usr/bin/env python3
"""
異步等待模組
功能：使用 polling 方式等待 Agent 完成，並支援 callback
"""

import time
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any

# 嘗試導入 OpenClawAPI
try:
    from openclaw_api import api
    HAS_OPENCLAW_API = True
except ImportError:
    HAS_OPENCLAW_API = False


class AsyncWaiter:
    """異步等待 Agent 完成"""
    
    def __init__(self, interval: int = 5):
        """
        初始化
        
        Args:
            interval: Polling 間隔（秒）
        """
        self.interval = interval
        self.total_waited = 0
        
    def wait(self, session_key: str, timeout: int = 600, callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        等待 Agent 完成
        
        Args:
            session_key: Agent session key
            timeout: 超時時間（秒）
            callback: 完成後的回調函數
            
        Returns:
            {"status": "completed/failed/timeout", "sessionKey": ..., "elapsed": ...}
        """
        start_time = datetime.now()
        deadline = start_time + timedelta(seconds=timeout)
        
        print(f"⏳ [AsyncWaiter] 等待 Agent 完成...")
        print(f"   Session: {session_key}")
        print(f"   Timeout: {timeout}秒")
        
        while datetime.now() < deadline:
            # 檢查 Agent 狀態
            status = self.check_status(session_key)
            
            elapsed = (datetime.now() - start_time).seconds
            self.total_waited = elapsed
            
            if status["status"] == "completed":
                print(f"✅ [AsyncWaiter] Agent 已完成 (耗時: {elapsed}秒)")
                
                # 觸發 callback
                if callback:
                    print(f"📞 [AsyncWaiter] 觸發 callback...")
                    callback(status)
                
                return {
                    "status": "completed",
                    "sessionKey": session_key,
                    "elapsed": elapsed,
                    "result": status.get("result")
                }
            
            if status["status"] == "failed":
                print(f"❌ [AsyncWaiter] Agent 失敗")
                return {
                    "status": "failed",
                    "sessionKey": session_key,
                    "elapsed": elapsed,
                    "error": status.get("error")
                }
            
            # 等待下一個 interval
            print(f"   已等待 {elapsed}秒... (每 {self.interval}秒檢查一次)")
            time.sleep(self.interval)
        
        # Timeout
        print(f"⏱️ [AsyncWaiter] Timeout (超過 {timeout}秒)")
        return {
            "status": "timeout",
            "sessionKey": session_key,
            "timeout": timeout,
            "elapsed": timeout
        }
    
    def check_status(self, session_key: str) -> Dict[str, Any]:
        """
        檢查 Agent 狀態
        """
        if HAS_OPENCLAW_API:
            # 使用 OpenClaw API
            return api.get_session_status(session_key)
        else:
            # 模擬實現
            return {
                "status": "running",
                "sessionKey": session_key
            }
    
    def wait_with_retry(self, session_key: str, timeout: int = 600, max_retries: int = 3, interval: int = 5) -> Dict[str, Any]:
        """
        等待並自動重試
        
        Args:
            session_key: Agent session key
            timeout: 每次嘗試的超時時間
            max_retries: 最大重試次數
            interval: Polling 間隔
            
        Returns:
            最終結果
        """
        retries = 0
        
        while retries < max_retries:
            print(f"🔄 [AsyncWaiter] 嘗試 {retries + 1}/{max_retries}")
            
            result = self.wait(session_key, timeout, interval=interval)
            
            if result["status"] == "completed":
                return result
            
            if result["status"] == "failed":
                print(f"❌ [AsyncWaiter] 嘗試 {retries + 1} 失敗，重試中...")
                retries += 1
                time.sleep(2)  # 等待後重試
            
            if result["status"] == "timeout":
                print(f"⏱️ [AsyncWaiter] 超時，重試中...")
                retries += 1
                time.sleep(2)
        
        return {
            "status": "failed",
            "sessionKey": session_key,
            "error": f"已重試 {max_retries} 次仍然失敗",
            "retries": max_retries
        }


# 全域實例
waiter = AsyncWaiter()


# 便捷函數
def wait_for_agent(session_key: str, timeout: int = 600, callback: Optional[Callable] = None) -> Dict[str, Any]:
    """快速等待 Agent 完成"""
    return waiter.wait(session_key, timeout, callback)


def wait_with_retry(session_key: str, timeout: int = 600, max_retries: int = 3) -> Dict[str, Any]:
    """快速等待並重試"""
    return waiter.wait_with_retry(session_key, timeout, max_retries)


# 測試
if __name__ == "__main__":
    print("=== AsyncWaiter 測試 ===")
    
    # 模擬 session key
    test_session = "test-session-123"
    
    # 測試 wait（模擬）
    result = wait_for_agent(test_session, timeout=60)
    print(f"\n結果: {result}")
    
    print("\n✅ AsyncWaiter 測試完成")