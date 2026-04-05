# IntegrationManager - 迭代修復管理
# P0: Aspect 7 - 迭代修復處理

from pathlib import Path
from datetime import datetime
import json


class IntegrationManager:
    """
    管理迭代修復流程，追蹤嘗試次數，處理 HR-12/13 限制
    """
    
    def __init__(self, phase: int, task_id: str, repo_path: Path = None):
        self.phase = phase
        self.task_id = task_id
        self.repo_path = repo_path or Path(".")
        self.iterations_file = self.repo_path / ".methodology" / "iterations" / f"phase{phase}.json"
        self.iterations_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """載入迭代歷史"""
        if self.iterations_file.exists():
            return json.loads(self.iterations_file.read_text())
        return []
    
    def _save_history(self):
        """保存迭代歷史"""
        self.iterations_file.write_text(json.dumps(self.history, indent=2, ensure_ascii=False))
    
    def add_attempt(self, attempt: dict) -> dict:
        """
        記錄一次嘗試
        
        Args:
            attempt: {
                'status': 'rejected'|'approved',
                'round': int
            }
        """
        attempt['timestamp'] = datetime.now().isoformat()
        if 'round' not in attempt:
            attempt['round'] = len(self.history) + 1
        
        self.history.append(attempt)
        self._save_history()
        
        # Check HR-12
        if attempt.get('status') == 'rejected' and len(self.history) >= 5:
            return self._trigger_hr12_pause()
        
        return {
            'status': 'ok',
            'remaining': 5 - len(self.history),
            'message': f"Remaining retries: {5 - len(self.history)}"
        }
    
    def _trigger_hr12_pause(self) -> dict:
        """HR-12 觸發：5 輪後暫停"""
        return {
            'status': 'hr12_triggered',
            'remaining': 0,
            'message': f'⚠️ HR-12: Phase {self.phase} 已達 5 輪限制，請人工介入'
        }
    
    def get_stats(self) -> dict:
        """取得迭代統計"""
        total = len(self.history)
        rejected = sum(1 for a in self.history if a.get('status') == 'rejected')
        approved = sum(1 for a in self.history if a.get('status') == 'approved')
        
        return {
            'total': total,
            'rejected': rejected,
            'approved': approved,
            'remaining': max(0, 5 - total),
            'hr12_triggered': total >= 5 and rejected > 0
        }
