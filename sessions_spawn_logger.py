# Sessions Spawn Logger - 自動記錄 sub-agent 派遣
# 解決方案：SubagentIsolator.spawn() hook 自動寫入 log

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class SessionsSpawnLogger:
    """
    自動記錄 sessions_spawn 派遣事件
    
    使用方式：
        from sessions_spawn_logger import SessionsSpawnLogger
        
        logger = SessionsSpawnLogger(repo_path)
        logger.log_spawn(role="developer", task="FR-01", session_id="xxx")
    """
    
    LOG_FILENAME = ".methodology/sessions_spawn.log"
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.log_path = self.repo_path / self.LOG_FILENAME
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _ensure_initialized(self):
        """確保 log 檔案存在"""
        if not self.log_path.exists():
            self.log_path.write_text("")
    
    def log_spawn(
        self,
        role: str,
        task: str,
        session_id: str,
        confidence: Optional[int] = None,
        status: str = "SPAWNED",
        **kwargs
    ) -> Dict[str, Any]:
        """
        記錄一次 sub-agent 派遣
        
        Args:
            role: "developer" | "reviewer"
            task: 任務描述（如 "FR-01"）
            session_id: session key
            confidence: 信心度（可選）
            status: "SPAWNED" | "COMPLETED" | "FAILED"
            **kwargs: 其他欄位
        """
        self._ensure_initialized()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "task": task,
            "session_id": session_id,
            "status": status,
        }
        
        if confidence is not None:
            entry["confidence"] = confidence
        
        entry.update(kwargs)
        
        # 寫入一行 JSON
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return entry
    
    def validate(self) -> Dict[str, Any]:
        """
        驗證 log 格式
        
        Returns:
            {"valid": bool, "count": int, "errors": list}
        """
        if not self.log_path.exists():
            return {"valid": True, "count": 0, "errors": []}
        
        content = self.log_path.read_text().strip()
        if not content:
            return {"valid": True, "count": 0, "errors": []}
        
        lines = [l for l in content.split("\n") if l.strip()]
        errors = []
        count = 0
        
        for i, line in enumerate(lines):
            try:
                # 移除可能的行首逗號
                if line.startswith(","):
                    line = line[1:]
                entry = json.loads(line)
                
                # 驗證必要欄位
                for field in ["role", "session_id"]:
                    if field not in entry:
                        errors.append(f"Line {i+1}: missing {field}")
                
                count += 1
            except json.JSONDecodeError as e:
                errors.append(f"Line {i+1}: {e}")
        
        return {
            "valid": len(errors) == 0,
            "count": count,
            "errors": errors
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """取得 log 摘要"""
        result = self.validate()
        
        # 統計各 role
        role_counts = {}
        fr_tasks = set()
        
        if self.log_path.exists():
            content = self.log_path.read_text().strip()
            lines = [l for l in content.split("\n") if l.strip()]
            
            for line in lines:
                try:
                    if line.startswith(","):
                        line = line[1:]
                    entry = json.loads(line)
                    role = entry.get("role", "unknown")
                    role_counts[role] = role_counts.get(role, 0) + 1
                    
                    task = entry.get("task", "")
                    if task:
                        fr_tasks.add(task.split()[0] if " " in task else task)
                except:
                    pass
        
        return {
            "total_entries": result["count"],
            "role_counts": role_counts,
            "fr_tasks": sorted(fr_tasks),
            "valid": result["valid"]
        }


def log_spawn_event(
    repo_path: Path,
    role: str,
    task: str,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    便利函數：直接記錄一次派遣
    
    Usage:
        from sessions_spawn_logger import log_spawn_event
        
        result = log_spawn_event(
            repo_path=Path("/path/to/repo"),
            role="developer",
            task="FR-01",
            session_id="abc123"
        )
    """
    logger = SessionsSpawnLogger(repo_path)
    return logger.log_spawn(role=role, task=task, session_id=session_id, **kwargs)
