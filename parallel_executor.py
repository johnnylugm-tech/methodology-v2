#!/usr/bin/env python3
"""
Parallel Executor - 並行執行器

支援任務並行執行
"""

import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import threading
import queue
import time


class TaskState(Enum):
    """任務狀態"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ParallelTask:
    """並行任務"""
    id: str
    name: str
    func: Callable = None
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: int = 0  # 越大越先執行
    timeout: int = 300  # 秒
    dependencies: List[str] = field(default_factory=list)  # 任務 ID 列表
    
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: str = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime = None
    completed_at: datetime = None
    duration_ms: float = 0.0
    
    def __hash__(self):
        return hash(self.id)


@dataclass
class Worker:
    """工作者"""
    id: str
    name: str
    is_busy: bool = False
    current_task_id: str = None
    max_concurrent: int = 1
    capabilities: List[str] = field(default_factory=list)


class ExecutionResult:
    """執行結果"""
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.completed: List[str] = []
        self.failed: List[str] = []
        self.duration_ms: float = 0.0


class ParallelExecutor:
    """並行執行器"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.tasks: Dict[str, ParallelTask] = {}
        self.workers: Dict[str, Worker] = {}
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.results: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.lock = threading.Lock()
        self.start_time: datetime = None
        self.execution_history: List[Dict] = []
    
    def add_worker(self, name: str, max_concurrent: int = 1,
                  capabilities: List[str] = None) -> str:
        """新增工作者"""
        worker_id = f"worker-{len(self.workers) + 1}"
        
        worker = Worker(
            id=worker_id,
            name=name,
            max_concurrent=max_concurrent,
            capabilities=capabilities or []
        )
        
        self.workers[worker_id] = worker
        return worker_id
    
    def add_task(self, name: str, func: Callable,
                args: tuple = None, kwargs: dict = None,
                priority: int = 0, timeout: int = 300,
                dependencies: List[str] = None,
                required_worker: str = None) -> str:
        """新增任務"""
        task_id = f"task-{len(self.tasks) + 1}"
        
        task = ParallelTask(
            id=task_id,
            name=name,
            func=func,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            timeout=timeout,
            dependencies=dependencies or [],
        )
        
        self.tasks[task_id] = task
        
        # 加入佇列
        self.task_queue.put((-priority, task_id))
        
        return task_id
    
    def _check_dependencies(self, task_id: str) -> bool:
        """檢查依賴是否滿足"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        for dep_id in task.dependencies:
            dep = self.tasks.get(dep_id)
            if not dep or dep.state != TaskState.COMPLETED:
                return False
        
        return True
    
    def _get_ready_tasks(self) -> List[str]:
        """取得準備好的任務"""
        ready = []
        
        # 遍歷佇列中的任務
        temp_items = []
        while not self.task_queue.empty():
            try:
                priority, tid = self.task_queue.get_nowait()
                temp_items.append((priority, tid))
                
                if self._check_dependencies(tid):
                    ready.append(tid)
                else:
                    # 重新放回佇列
                    self.task_queue.put((priority, tid))
            except queue.Empty:
                break
        
        # 重新放回剩餘任務
        for priority, tid in temp_items:
            if tid not in ready:
                self.task_queue.put((priority, tid))
        
        return ready
    
    def _execute_task(self, task_id: str, worker_id: str) -> Any:
        """執行任務"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        worker = self.workers.get(worker_id)
        
        with self.lock:
            task.state = TaskState.RUNNING
            task.started_at = datetime.now()
            if worker:
                worker.is_busy = True
                worker.current_task_id = task_id
        
        try:
            # 執行任務（帶超時）
            if task.timeout > 0:
                result = self._execute_with_timeout(task, task.timeout)
            else:
                result = task.func(*task.args, **task.kwargs)
            
            task.result = result
            task.state = TaskState.COMPLETED
            task.duration_ms = (datetime.now() - task.started_at).total_seconds() * 1000
            
            return result
            
        except Exception as e:
            task.error = str(e)
            task.state = TaskState.FAILED
            task.duration_ms = (datetime.now() - task.started_at).total_seconds() * 1000
            
            return None
        
        finally:
            with self.lock:
                if worker:
                    worker.is_busy = False
                    worker.current_task_id = None
    
    def _execute_with_timeout(self, task: ParallelTask, timeout: int) -> Any:
        """帶超時的執行"""
        result = [None]
        error = [None]
        done = [False]
        
        def run():
            try:
                result[0] = task.func(*task.args, **task.kwargs)
            except Exception as e:
                error[0] = e
            finally:
                done[0] = True
        
        thread = threading.Thread(target=run)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if not done[0]:
            raise TimeoutError(f"Task {task.id} timed out after {timeout}s")
        
        if error[0]:
            raise error[0]
        
        return result[0]
    
    def execute_all(self, wait: bool = True) -> ExecutionResult:
        """執行所有任務"""
        self.start_time = datetime.now()
        
        result = ExecutionResult()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures: Dict[Future, str] = {}
            
            while True:
                # 取得準備好的任務
                ready_tasks = self._get_ready_tasks()
                
                # 提交準備好的任務
                for task_id in ready_tasks:
                    task = self.tasks[task_id]
                    if task.state == TaskState.PENDING or task.state == TaskState.QUEUED:
                        task.state = TaskState.QUEUED
                        
                        # 選擇一個可用的工作者
                        worker_id = self._select_worker(task)
                        
                        if worker_id:
                            future = executor.submit(self._execute_task, task_id, worker_id)
                            futures[future] = task_id
                
                # 檢查是否完成
                if not futures:
                    break
                
                # 等待完成
                if wait:
                    done_futures = []
                    for future in as_completed(futures, timeout=1):
                        task_id = futures[future]
                        done_futures.append(future)
                        
                        try:
                            res = future.result()
                            self.results[task_id] = res
                            result.results[task_id] = res
                            result.completed.append(task_id)
                        except Exception as e:
                            self.errors[task_id] = str(e)
                            result.errors[task_id] = str(e)
                            result.failed.append(task_id)
                    
                    for future in done_futures:
                        del futures[future]
                
                # 如果不等待，快速檢查
                else:
                    break
                
                # 檢查是否所有任務都已處理
                pending = sum(1 for t in self.tasks.values() 
                           if t.state in [TaskState.PENDING, TaskState.QUEUED, TaskState.RUNNING])
                if pending == 0:
                    break
                
                time.sleep(0.1)
        
        result.duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        
        # 記錄歷史
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "tasks_count": len(self.tasks),
            "completed": len(result.completed),
            "failed": len(result.failed),
            "duration_ms": result.duration_ms,
        })
        
        return result
    
    def _select_worker(self, task: ParallelTask) -> Optional[str]:
        """選擇工作者"""
        available = [
            w for w in self.workers.values()
            if not w.is_busy
        ]
        
        if not available:
            return None
        
        # 選擇能執行任務的工作者
        for worker in available:
            if not task.kwargs.get('required_capabilities'):
                return worker.id
            
            required = set(task.kwargs.get('required_capabilities', []))
            if required.issubset(set(worker.capabilities)):
                return worker.id
        
        # 如果沒有符合條件的，返回任何可用的
        return available[0].id if available else None
    
    def get_task_status(self, task_id: str = None) -> Dict:
        """取得任務狀態"""
        if task_id:
            task = self.tasks.get(task_id)
            if not task:
                return {}
            
            return {
                "id": task.id,
                "name": task.name,
                "state": task.state.value,
                "priority": task.priority,
                "dependencies": task.dependencies,
                "result": str(task.result)[:100] if task.result else None,
                "error": task.error,
                "duration_ms": task.duration_ms,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            }
        
        # 所有任務
        return {
            "total": len(self.tasks),
            "pending": sum(1 for t in self.tasks.values() if t.state == TaskState.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.state == TaskState.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.state == TaskState.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.state == TaskState.FAILED),
            "tasks": [
                {
                    "id": t.id,
                    "name": t.name,
                    "state": t.state.value,
                }
                for t in self.tasks.values()
            ]
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任務"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED]:
            return False
        
        task.state = TaskState.CANCELLED
        return True
    
    def get_worker_status(self) -> List[Dict]:
        """取得工作者狀態"""
        return [
            {
                "id": w.id,
                "name": w.name,
                "is_busy": w.is_busy,
                "current_task": w.current_task_id,
                "max_concurrent": w.max_concurrent,
            }
            for w in self.workers.values()
        ]
    
    def get_execution_summary(self) -> Dict:
        """取得執行摘要"""
        completed = [t for t in self.tasks.values() if t.state == TaskState.COMPLETED]
        failed = [t for t in self.tasks.values() if t.state == TaskState.FAILED]
        
        total_duration = sum(t.duration_ms for t in completed)
        avg_duration = total_duration / len(completed) if completed else 0
        
        return {
            "total_tasks": len(self.tasks),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(self.tasks) if self.tasks else 0,
            "total_duration_ms": total_duration,
            "avg_task_duration_ms": avg_duration,
            "parallelism": self.max_workers,
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        summary = self.get_execution_summary()
        task_status = self.get_task_status()
        worker_status = self.get_worker_status()
        
        report = f"""
# ⚡ Parallel Execution 報告

## 執行摘要

| 指標 | 數值 |
|------|------|
| 總任務數 | {summary['total_tasks']} |
| 完成 | {summary['completed']} |
| 失敗 | {summary['failed']} |
| 成功率 | {summary['success_rate']:.1%} |
| 總執行時間 | {summary['total_duration_ms']:.0f}ms |
| 平均任務時間 | {summary['avg_task_duration_ms']:.0f}ms |
| 並行度 | {summary['parallelism']} |

---

## 工作者狀態

| 工作者 | 狀態 | 當前任務 |
|--------|------|----------|
"""
        
        for w in worker_status:
            status = "🔄 工作中" if w['is_busy'] else "✅ 空閒"
            report += f"| {w['name']} | {status} | {w['current_task'] or '-'} |\n"
        
        report += f"""

## 任務狀態

| 任務 | 狀態 | 耗時 |
|------|------|------|
"""
        
        for t in task_status.get('tasks', []):
            state_icon = {
                "pending": "⏳",
                "queued": "📤",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌",
                "cancelled": "🚫",
            }.get(t['state'], "❓")
            
            report += f"| {t['name']} | {state_icon} {t['state']} | - |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    executor = ParallelExecutor(max_workers=3)
    
    # 新增工作者
    executor.add_worker("Worker-1", max_concurrent=2)
    executor.add_worker("Worker-2", max_concurrent=2)
    executor.add_worker("Worker-3", max_concurrent=1)
    
    # 定義任務
    def task1():
        time.sleep(0.5)
        return "Task 1 done"
    
    def task2():
        time.sleep(0.3)
        return "Task 2 done"
    
    def task3():
        time.sleep(0.4)
        return "Task 3 done"
    
    # 新增任務
    print("=== Adding Tasks ===")
    t1 = executor.add_task("任務 1", task1, priority=3)
    t2 = executor.add_task("任務 2", task2, priority=2)
    t3 = executor.add_task("任務 3", task3, priority=1)
    
    # 帶依賴的任務
    def task4():
        time.sleep(0.2)
        return "Task 4 done"
    
    executor.add_task("任務 4 (依賴任務 1)", task4, priority=4, dependencies=[t1])
    
    # 執行
    print("=== Executing ===")
    result = executor.execute_all()
    
    print(f"\nCompleted: {len(result.completed)}")
    print(f"Failed: {len(result.failed)}")
    print(f"Duration: {result.duration_ms:.0f}ms")
    
    # 狀態
    print("\n=== Task Status ===")
    for task_id, res in result.results.items():
        print(f"{task_id}: {res}")
    
    for task_id, err in result.errors.items():
        print(f"{task_id}: ERROR - {err}")
    
    # 摘要
    print("\n=== Summary ===")
    summary = executor.get_execution_summary()
    print(f"Success rate: {summary['success_rate']:.1%}")
    
    # 報告
    print("\n=== Report ===")
    print(executor.generate_report())
