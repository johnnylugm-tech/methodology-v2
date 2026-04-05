# ToolDispatcher - 動態工具觸發
# P0: Aspect 6 - 對的工具

from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ToolDispatcher:
    """
    根據上下文自動觸發正確的工具
    """
    
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or Path(".")
        self.hook_log_path = self.repo_path / ".methodology" / "tool_hook_log.jsonl"
        self.message_count = 0
    
    def on_spawn(self, role: str, task_id: str, artifact_paths: list = None) -> dict:
        """
        派遣 Sub-agent 時觸發
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'spawn',
            'role': role,
            'task_id': task_id,
            'artifact_paths': artifact_paths or []
        }
        
        self._log(entry)
        
        return {
            'status': 'ok',
            'logged': True,
            'message': f'Spawn logged: {role} -> {task_id}'
        }
    
    def on_message(self, role: str, message_count: int) -> dict:
        """
        訊息計數變化時觸發（ContextManager 壓縮）
        """
        self.message_count = message_count
        actions = []
        
        # L1: >50 messages
        if message_count > 50:
            actions.append('L1_compress')
        
        # L2: >100 messages  
        if message_count > 100:
            actions.append('L2_extract')
        
        # L3: >200 messages
        if message_count > 200:
            actions.append('L3_archive')
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'message_threshold',
            'message_count': message_count,
            'actions': actions
        }
        
        self._log(entry)
        
        return {
            'status': 'ok',
            'actions': actions,
            'message': f'Message count {message_count}: triggered {len(actions)} actions'
        }
    
    def on_error(self, role: str, task_id: str, error: str, level: int = None) -> dict:
        """
        錯誤發生時觸發
        """
        # Determine error level from error type
        if level is None:
            if 'Permission' in str(error):
                level = 3
            elif 'Timeout' in str(error):
                level = 2
            else:
                level = 1
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'error',
            'role': role,
            'task_id': task_id,
            'error': str(error),
            'level': level
        }
        
        self._log(entry)
        
        return {
            'status': 'logged',
            'level': level,
            'message': f'Error logged (level {level}): {error}'
        }
    
    def on_complete(self, role: str, task_id: str, result: dict) -> dict:
        """
        任務完成時觸發
        """
        confidence = result.get('confidence', 10)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'complete',
            'role': role,
            'task_id': task_id,
            'confidence': confidence,
            'status': result.get('status', 'unknown')
        }
        
        self._log(entry)
        
        return {
            'status': 'logged',
            'confidence': confidence,
            'message': f'Task {task_id} complete with confidence {confidence}'
        }
    
    def _log(self, entry: dict):
        """寫入 tool_hook_log"""
        self.hook_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.hook_log_path, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
