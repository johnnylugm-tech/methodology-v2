#!/usr/bin/env python3
"""
Async Executor - 非同步執行器

對標 AutoGen 的 async/await 支援：
- asyncio 原生支援
- 並發任務執行
- 結果收集
- 超時控制

AI-native 實作，零額外負擔
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime
import uuid

class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class AsyncTask:
    """非同步任務"""
    task_id: str
    name: str
    coro: Awaitable
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    timeout: Optional[float] = None  # 秒
    
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "result": str(self.result)[:100] if self.result else None,
            "error": self.error,
        }

class AsyncExecutor:
    """
    非同步執行器
    
    對標 AutoGen 的 async/await：
    - 並發執行多個任務
    - 超時控制
    - 錯誤處理
    - 結果收集
    """
    
    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency
        self.tasks: Dict[str, AsyncTask] = {}
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    def create_task(self, name: str, coro: Awaitable, timeout: float = None) -> str:
        """創建非同步任務"""
        task_id = f"async-{uuid.uuid4().hex[:8]}"
        task = AsyncTask(task_id=task_id, name=name, coro=coro, timeout=timeout)
        self.tasks[task_id] = task
        return task_id
    
    async def _run_task(self, task: AsyncTask) -> Any:
        """內部執行任務"""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            try:
                if task.timeout:
                    task.result = await asyncio.wait_for(task.coro, timeout=task.timeout)
                else:
                    task.result = await task.coro
                task.status = TaskStatus.COMPLETED
            except asyncio.TimeoutError:
                task.status = TaskStatus.TIMEOUT
                task.error = f"Task timed out after {task.timeout}s"
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
            finally:
                task.completed_at = datetime.now()
            
            return task.result
    
    async def execute_all(self) -> Dict[str, Any]:
        """執行所有任務"""
        coros = [self._run_task(task) for task in self.tasks.values()]
        results = await asyncio.gather(*coros, return_exceptions=True)
        
        result_map = {}
        for task_id, result in zip(self.tasks.keys(), results):
            if isinstance(result, Exception):
                result_map[task_id] = {"error": str(result)}
            else:
                result_map[task_id] = result
        
        return result_map
    
    def get_status(self) -> dict:
        """取得執行狀態"""
        statuses = {}
        for task_id, task in self.tasks.items():
            statuses[task_id] = task.status.value
        return statuses
    
    def get_results(self) -> Dict[str, Any]:
        """取得所有結果"""
        return {task_id: task.result for task_id, task in self.tasks.items()}

# ============================================
# 便捷函數
# ============================================

async def run_async(coro: Awaitable, timeout: float = None) -> Any:
    """
    便捷函數：執行單個非同步任務
    
    Example:
        result = await run_async(agent.execute("task"))
    """
    if timeout:
        return await asyncio.wait_for(coro, timeout=timeout)
    return await coro

async def run_parallel(*coros: Awaitable, max_concurrency: int = 10) -> List[Any]:
    """
    便捷函數：並行執行多個非同步任務
    
    Example:
        results = await run_parallel(task1(), task2(), task3())
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def bounded_coro(coro):
        async with semaphore:
            return await coro
    
    bounded_coros = [bounded_coro(c) for c in coros]
    return await asyncio.gather(*bounded_coros, return_exceptions=True)
