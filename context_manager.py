#!/usr/bin/env python3
"""
ContextManager — 上下文管理模組

功能：
- 三層壓縮：L1 摘要 / L2 提取 / L3 存檔
- Task 持久化
- 狀態追蹤

用法：
    from context_manager import ContextManager
    
    cm = ContextManager(state_path=".methodology/state.json")
    cm.compress(messages, level="auto")
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from enum import Enum


class CompressionLevel(Enum):
    L1_SUMMARY = "L1"   # 摘要（>50 messages）
    L2_EXTRACT = "L2"   # 提取關鍵資訊（>100 messages）
    L3_ARCHIVE = "L3"   # 存檔（>200 messages）
    AUTO = "auto"


THRESHOLDS = {
    CompressionLevel.L1_SUMMARY: 50,
    CompressionLevel.L2_EXTRACT: 100,
    CompressionLevel.L3_ARCHIVE: 200,
}


@dataclass
class TaskContext:
    """任務上下文"""
    task_id: str
    title: str
    status: str = "pending"  # pending/active/completed/blocked
    messages: List[Dict] = field(default_factory=list)
    summary: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    dependencies: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)  # name -> path


@dataclass
class CompressionResult:
    """壓縮結果"""
    original_len: int
    compressed_len: int
    level: str
    archived: bool
    archive_path: Optional[str] = None


class ContextManager:
    """
    上下文管理器
    
    解決：
    - 上下文無限增長
    - 長時間任務迷失目標
    - 多任務相互干擾
    """
    
    def __init__(self, state_path: str = ".methodology/state.json", archive_dir: str = ".methodology/archives"):
        self.state_path = Path(state_path)
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 緩存
        self._message_cache = {}
        self._task_cache = {}
    
    def compress(self, messages: List[Dict], level: str = "auto") -> CompressionResult:
        """
        壓縮訊息
        
        Args:
            messages: 原始訊息列表
            level: 壓縮級別（auto/L1/L2/L3）
            
        Returns:
            CompressionResult: 壓縮結果
        """
        original_len = len(messages)
        
        if level == "auto":
            if original_len > 200:
                level = "L3"
            elif original_len > 100:
                level = "L2"
            elif original_len > 50:
                level = "L1"
            else:
                level = "none"
        
        result = messages.copy()
        archived = False
        archive_path = None
        
        if level == "L3" and original_len > 200:
            # L3: 存檔
            archive_path = self._archive_messages(result[:-100])
            result = result[-100:]
            archived = True
        
        if level in ("L2", "L3") and len(result) > 100:
            # L2: 提取關鍵資訊
            key_info = self._extract_key_info(result)
            result = [{"role": "system", "content": key_info}] + result[-20:]
        
        if level in ("L1", "L2", "L3") and len(result) > 50:
            # L1: 摘要
            summary = self._summarize(result[-50:])
            result = result[:10] + [{"role": "user", "content": summary}]
        
        return CompressionResult(
            original_len=original_len,
            compressed_len=len(result),
            level=level,
            archived=archived,
            archive_path=archive_path
        )
    
    def _summarize(self, messages: List[Dict]) -> str:
        """L1: 產生摘要"""
        recent = messages[-20:] if len(messages) > 20 else messages
        
        # 提取事實性內容
        facts = []
        for m in recent:
            content = m.get("content", "")
            if len(content) > 10:
                facts.append(content[:100])
        
        summary = f"[Summary of {len(recent)} messages]: {' '.join(facts[:5])[:300]}..."
        return summary
    
    def _extract_key_info(self, messages: List[Dict]) -> str:
        """L2: 提取關鍵資訊"""
        tools = []
        decisions = []
        
        for m in messages:
            if m.get("role") == "assistant":
                content = m.get("content", "")
                if "tool_calls" in str(m):
                    tools.append("tool_call")
                if content.startswith("Decision:"):
                    decisions.append(content[:80])
        
        key_info = f"[Key Info] Tools used: {set(tools)}. Recent decisions: {decisions[-3:] if decisions else 'none'}."
        return key_info
    
    def _archive_messages(self, messages: List[Dict]) -> str:
        """L3: 存檔"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_hash = hashlib.md5(str(messages).encode()).hexdigest()[:8]
        archive_name = f"archive_{timestamp}_{archive_hash}.json"
        archive_path = self.archive_dir / archive_name
        
        archive_path.write_text(json.dumps(messages, indent=2, ensure_ascii=False))
        
        return str(archive_path)
    
    # ========== Task System ==========
    
    def create_task(self, task_id: str, title: str, dependencies: List[str] = None) -> TaskContext:
        """
        建立任務
        
        Args:
            task_id: 任務 ID
            title: 任務標題
            dependencies: 依賴的任務 ID 列表
            
        Returns:
            TaskContext: 任務物件
        """
        task = TaskContext(
            task_id=task_id,
            title=title,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            dependencies=dependencies or []
        )
        
        self._task_cache[task_id] = task
        self._save_task_state()
        
        return task
    
    def add_message(self, task_id: str, message: Dict):
        """為任務新增訊息"""
        if task_id not in self._task_cache:
            raise KeyError(f"Task not found: {task_id}")
        
        task = self._task_cache[task_id]
        task.messages.append(message)
        task.updated_at = datetime.now(timezone.utc).isoformat()
        
        # 自動壓縮（每 50 條）
        if len(task.messages) > 100:
            result = self.compress(task.messages, level="L2")
            task.messages = task.messages[result.compressed_len:]
            task.summary = f"[Auto-compressed {result.original_len} → {result.compressed_len}]"
    
    def complete_task(self, task_id: str, artifacts: Dict[str, str] = None):
        """標記任務完成"""
        if task_id not in self._task_cache:
            raise KeyError(f"Task not found: {task_id}")
        
        task = self._task_cache[task_id]
        task.status = "completed"
        task.updated_at = datetime.now(timezone.utc).isoformat()
        
        if artifacts:
            task.artifacts.update(artifacts)
        
        # 產生最終摘要
        if len(task.messages) > 10:
            result = self.compress(task.messages, level="L1")
            task.summary = f"[Final summary: {result.compressed_len}/{result.original_len} messages]"
        
        self._save_task_state()
    
    def get_task_state(self, task_id: str) -> Optional[Dict]:
        """取得任務狀態"""
        if task_id not in self._task_cache:
            # 從磁碟載入
            self._load_task_state()
        
        if task_id in self._task_cache:
            task = self._task_cache[task_id]
            return {
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status,
                "message_count": len(task.messages),
                "summary": task.summary,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "dependencies": task.dependencies,
                "artifacts": task.artifacts
            }
        
        return None
    
    def can_start_task(self, task_id: str) -> bool:
        """檢查任務是否可以開始（依賴是否滿足）"""
        if task_id not in self._task_cache:
            return False
        
        task = self._task_cache[task_id]
        
        for dep_id in task.dependencies:
            if dep_id in self._task_cache:
                dep_task = self._task_cache[dep_id]
                if dep_task.status != "completed":
                    return False
        
        return True
    
    def _save_task_state(self):
        """保存任務狀態到 state.json"""
        if not self.state_path.exists():
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps({}, indent=2))
        
        try:
            state = json.loads(self.state_path.read_text())
            
            tasks_data = {}
            for task_id, task in self._task_cache.items():
                tasks_data[task_id] = {
                    "task_id": task.task_id,
                    "title": task.title,
                    "status": task.status,
                    "messages": task.messages[-100:],  # 只存最近 100 條
                    "summary": task.summary,
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                    "dependencies": task.dependencies,
                    "artifacts": task.artifacts
                }
            
            state["tasks"] = tasks_data
            self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        except Exception:
            pass
    
    def _load_task_state(self):
        """從 state.json 載入任務狀態"""
        if not self.state_path.exists():
            return
        
        try:
            state = json.loads(self.state_path.read_text())
            tasks_data = state.get("tasks", {})
            
            for task_id, data in tasks_data.items():
                task = TaskContext(
                    task_id=data["task_id"],
                    title=data["title"],
                    status=data["status"],
                    messages=data.get("messages", []),
                    summary=data.get("summary"),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                    dependencies=data.get("dependencies", []),
                    artifacts=data.get("artifacts", {})
                )
                self._task_cache[task_id] = task
        except Exception:
            pass
    
    def get_all_tasks(self) -> List[Dict]:
        """取得所有任務"""
        self._load_task_state()
        
        return [
            self.get_task_state(task_id)
            for task_id in self._task_cache
        ]


# CLI 介面
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ContextManager CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # compress
    compress_parser = subparsers.add_parser("compress", help="Compress messages")
    compress_parser.add_argument("--input", required=True, help="Input JSON file")
    compress_parser.add_argument("--level", default="auto", choices=["auto", "L1", "L2", "L3", "none"])
    compress_parser.add_argument("--output", help="Output file")
    
    # task
    task_parser = subparsers.add_parser("task", help="Task operations")
    task_parser.add_argument("--create", metavar="ID", help="Create task")
    task_parser.add_argument("--title", help="Task title")
    task_parser.add_argument("--status", help="Show task status")
    task_parser.add_argument("--list", action="store_true", help="List all tasks")
    
    args = parser.parse_args()
    
    cm = ContextManager()
    
    if args.command == "compress":
        messages = json.loads(Path(args.input).read_text())
        result = cm.compress(messages, args.level)
        
        output = args.output or args.input.replace(".json", "_compressed.json")
        Path(output).write_text(json.dumps(messages[:result.compressed_len], indent=2))
        
        print(f"Compressed: {result.original_len} → {result.compressed_len} (Level: {result.level})")
        if result.archived:
            print(f"Archived: {result.archive_path}")
    
    elif args.command == "task":
        if args.create:
            task = cm.create_task(args.create, args.title or args.create)
            print(f"Created: {task.task_id}")
        
        elif args.status:
            state = cm.get_task_state(args.status)
            if state:
                print(json.dumps(state, indent=2))
            else:
                print(f"Task not found: {args.status}")
        
        elif args.list:
            tasks = cm.get_all_tasks()
            for t in tasks:
                print(f"[{t['status']}] {t['task_id']}: {t['title']}")


if __name__ == "__main__":
    main()
