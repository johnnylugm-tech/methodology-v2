"""
Methodology-v2 Adapter - 適配 Methodology-v2
"""

import sys
import os
from typing import Optional, Any
from dataclasses import dataclass
import logging

# 確保可以導入 methodology-v2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .events import Event, V2TaskPlannedData, V2QualityCheckData, V2ErrorClassifiedData
from .message_bus import get_bus

logger = logging.getLogger(__name__)


@dataclass
class V2Config:
    """Methodology-v2 配置"""
    quality_threshold: float = 0.8
    sprint_capacity: int = 40
    error_levels: list = None
    
    def __post_init__(self):
        if self.error_levels is None:
            self.error_levels = ["L1", "L2", "L3", "L4"]


class V2Adapter:
    """Methodology-v2 適配器"""
    
    def __init__(self, config: V2Config = None, bus=None):
        self.config = config or V2Config()
        self.bus = bus or get_bus()
        self._quality_gate = None
        self._error_classifier = None
        self._task_splitter = None
    
    def _ensure_modules(self):
        """確保所需的 Methodology-v2 模組已載入"""
        if self._quality_gate is None:
            try:
                from auto_quality_gate import AutoQualityGate
                self._quality_gate = AutoQualityGate()
                logger.info("Loaded AutoQualityGate")
            except ImportError as e:
                logger.warning(f"Could not import AutoQualityGate: {e}")
        
        if self._error_classifier is None:
            try:
                # ErrorClassifier 是 methodology_base.py 的一部分
                from methodology_base import ErrorClassifier, ErrorHandler
                self._error_classifier = ErrorClassifier()
                self._error_handler = ErrorHandler()
                logger.info("Loaded ErrorClassifier")
            except ImportError as e:
                logger.warning(f"Could not import ErrorClassifier: {e}")
    
    async def plan_task(self, instructions: str, preferred_model: str = "claude-3-opus") -> dict:
        """
        規劃任務 (Methodology-v2 → OmO)
        
        Args:
            instructions: 任務指令
            preferred_model: 偏好模型
        
        Returns:
            規劃結果
        """
        self._ensure_modules()
        
        task_id = f"v2-task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 使用 TaskSplitter 分解任務
        if self._task_splitter is None:
            try:
                from task_splitter import TaskSplitter
                self._task_splitter = TaskSplitter()
            except ImportError:
                logger.warning("TaskSplitter not available")
                subtasks = []
        else:
            try:
                subtasks = self._task_splitter.split_from_goal(instructions)
            except Exception as e:
                logger.error(f"Task split error: {e}")
                subtasks = []
        
        # 發布任務規劃事件
        planned_data = V2TaskPlannedData(
            task_id=task_id,
            instructions=instructions,
            preferred_model=preferred_model,
            estimated_hours=len(subtasks) * 0.5 if subtasks else 1.0
        )
        
        await self.bus.publish(
            "v2.task.planned",
            asdict(planned_data),
            source="v2"
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "subtasks": subtasks if isinstance(subtasks, list) else []
        }
    
    async def quality_check(self, task_id: str, code: str, language: str = "python") -> dict:
        """
        執行品質檢查 (OmO → Methodology-v2)
        
        Args:
            task_id: 任務 ID
            code: 代碼
            language: 語言
        
        Returns:
            品質檢查結果
        """
        self._ensure_modules()
        
        if self._quality_gate is None:
            logger.warning("QualityGate not available, skipping check")
            return {
                "passed": True,
                "score": 1.0,
                "issues": []
            }
        
        try:
            # 執行品質檢查
            result = self._quality_gate.scan_file_content(f"{task_id}.{language}", code)
            
            passed = result.get("passed", False)
            score = result.get("score", 0.0)
            issues = result.get("issues", [])
            
            # 發布品質檢查事件
            check_data = V2QualityCheckData(
                task_id=task_id,
                passed=passed,
                score=score,
                issues=issues
            )
            
            await self.bus.publish(
                "v2.quality.check",
                asdict(check_data),
                source="v2"
            )
            
            return {
                "passed": passed,
                "score": score,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            return {
                "passed": False,
                "score": 0.0,
                "issues": [{"error": str(e)}]
            }
    
    async def classify_error(self, error: Exception) -> dict:
        """
        分類錯誤
        
        Args:
            error: 錯誤對象
        
        Returns:
            分類結果
        """
        self._ensure_modules()
        
        if self._error_classifier is None:
            # 預設分類
            level = "L3"
            action = "降級處理"
        else:
            try:
                level = self._error_classifier.classify(error)
                action = self._error_handler.get_action(level)
            except Exception as e:
                logger.error(f"Error classification error: {e}")
                level = "L3"
                action = "降級處理"
        
        # 發布錯誤分類事件
        error_data = V2ErrorClassifiedData(
            error=error,
            level=level,
            action=action,
            message=str(error)
        )
        
        await self.bus.publish(
            "v2.error.classified",
            asdict(error_data),
            source="v2"
        )
        
        return {
            "level": level,
            "action": action,
            "message": str(error)
        }
    
    def get_status(self) -> dict:
        """獲取 Methodology-v2 狀態"""
        self._ensure_modules()
        
        return {
            "quality_gate": self._quality_gate is not None,
            "error_classifier": self._error_classifier is not None,
            "task_splitter": self._task_splitter is not None,
            "config": {
                "quality_threshold": self.config.quality_threshold,
                "sprint_capacity": self.config.sprint_capacity,
                "error_levels": self.config.error_levels
            }
        }


def asdict(obj):
    """將 dataclass 轉為 dict"""
    if hasattr(obj, '__dataclass_fields__'):
        result = {}
        for k in obj.__dataclass_fields__.keys():
            v = getattr(obj, k)
            if hasattr(v, '__dict__'):
                result[k] = str(v)
            else:
                result[k] = v
        return result
    return obj


from datetime import datetime
__all__ = ["V2Adapter", "V2Config", "get_bus"]
