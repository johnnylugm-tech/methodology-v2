"""
OmO Adapter - 適配 OmO (oh-my-opencode)
"""

import subprocess
import json
import os
from typing import Optional, Callable, Any
from dataclasses import dataclass
import logging

from .events import Event, OMTaskData, OMTaskCompletedData
from .message_bus import get_bus

logger = logging.getLogger(__name__)


@dataclass
class OmOConfig:
    """OmO 配置"""
    api_key: str = None
    preferred_models: list = None
    timeout: int = 30
    workspace: str = None


class OmOAdapter:
    """OmO 適配器 - 對接 oh-my-opencode"""
    
    def __init__(self, config: OmOConfig = None, bus=None):
        self.config = config or OmOConfig()
        self.bus = bus or get_bus()
        self._setup_env()
    
    def _setup_env(self):
        """設定環境變數"""
        if self.config.api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.config.api_key
    
    async def execute_task(self, instructions: str, model: str = None) -> dict:
        """
        執行 OmO 任務
        
        Args:
            instructions: 任務指令
            model: 偏好模型 (可選)
        
        Returns:
            執行結果
        """
        task_id = f"om-task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 發布任務開始事件
        await self.bus.publish(
            "om.task.started",
            {
                "task_id": task_id,
                "instructions": instructions,
                "model": model or "auto"
            },
            source="om"
        )
        
        try:
            # 構建命令
            cmd = ["oh-my-opencode"]
            if model:
                cmd.extend(["--model", model])
            cmd.extend(["--task", instructions])
            
            # 執行
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                cwd=self.config.workspace
            )
            
            if result.returncode == 0:
                # 發布任務完成事件
                completed_data = OMTaskCompletedData(
                    task_id=task_id,
                    code=result.stdout,
                    result={"output": result.stdout},
                    language="python"
                )
                
                await self.bus.publish(
                    "om.task.completed",
                    asdict(completed_data),
                    source="om"
                )
                
                return {"success": True, "task_id": task_id, "output": result.stdout}
            else:
                # 發布任務失敗事件
                await self.bus.publish(
                    "om.task.failed",
                    {"task_id": task_id, "error": result.stderr},
                    source="om"
                )
                
                return {"success": False, "task_id": task_id, "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            await self.bus.publish(
                "om.task.failed",
                {"task_id": task_id, "error": "Timeout"},
                source="om"
            )
            return {"success": False, "task_id": task_id, "error": "Timeout"}
        except Exception as e:
            logger.error(f"OmO execution error: {e}")
            await self.bus.publish(
                "om.task.failed",
                {"task_id": task_id, "error": str(e)},
                source="om"
            )
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    def get_status(self) -> dict:
        """獲取 OmO 狀態"""
        try:
            result = subprocess.run(
                ["oh-my-opencode", "--version"],
                capture_output=True,
                text=True
            )
            version = result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            version = "not installed"
        
        return {
            "installed": self._is_installed(),
            "version": version,
            "config": {
                "preferred_models": self.config.preferred_models,
                "timeout": self.config.timeout
            }
        }
    
    def _is_installed(self) -> bool:
        """檢查是否已安裝"""
        try:
            subprocess.run(
                ["oh-my-opencode", "--version"],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
    
    def register_hooks(self):
        """
        註冊 OmO Hooks (預留介面)
        
        這個方法預留給未來整合 OmO 的 48 Hooks 系統
        目前通過 subprocess 調用
        """
        logger.info("OmO hooks registration (placeholder - using subprocess for now)")
        pass


def asdict(obj):
    """將 dataclass 轉為 dict"""
    if hasattr(obj, '__dataclass_fields__'):
        return {
            k: getattr(obj, k) 
            for k in obj.__dataclass_fields__.keys()
        }
    return obj


from datetime import datetime
__all__ = ["OmOAdapter", "OmOConfig", "get_bus"]
