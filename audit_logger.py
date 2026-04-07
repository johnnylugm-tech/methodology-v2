#!/usr/bin/env python3
"""
Audit Logger - 審計日誌

完整操作軌跡記錄
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum


class ActionType(Enum):
    """操作類型"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"
    LOGOUT = "logout"
    GRANT = "grant"
    REVOKE = "revoke"


class ResourceType(Enum):
    """資源類型"""
    TASK = "task"
    PROJECT = "project"
    SPRINT = "sprint"
    USER = "user"
    BUDGET = "budget"
    DOCUMENT = "document"
    MODEL = "model"


@dataclass
class AuditEntry:
    """審計項目"""
    id: str
    timestamp: datetime
    user_id: str
    user_name: str
    action: ActionType
    resource_type: ResourceType
    resource_id: str
    resource_name: str = ""
    details: Dict = field(default_factory=dict)
    ip_address: str = None
    user_agent: str = None
    session_id: str = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "user_name": self.user_name,
            "action": self.action.value,
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
        }


class AuditLogger:
    """審計日誌系統"""
    
    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.current_user_id: str = None
        self.current_session_id: str = None
    
    def set_context(self, user_id: str, user_name: str, session_id: str = None):
        """設定上下文"""
        self.current_user_id = user_id
        self.current_session_id = session_id or f"sess-{datetime.now().timestamp()}"
    
    def log(self, action: ActionType, resource_type: ResourceType,
           resource_id: str, resource_name: str = "",
           details: Dict = None, **kwargs) -> str:
        """記錄操作"""
        if not self.current_user_id:
            raise ValueError("User context not set. Call set_context() first.")
        
        entry_id = f"audit-{len(self.entries) + 1}"
        
        entry = AuditEntry(
            id=entry_id,
            timestamp=datetime.now(),
            user_id=self.current_user_id,
            user_name=kwargs.get("user_name", "Unknown"),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details or {},
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            session_id=self.current_session_id,
        )
        
        self.entries.append(entry)
        return entry_id
    
    def log_create(self, resource_type: ResourceType, resource_id: str,
                  resource_name: str = "", details: Dict = None):
        """記錄建立"""
        return self.log(ActionType.CREATE, resource_type, resource_id, resource_name, details)
    
    def log_update(self, resource_type: ResourceType, resource_id: str,
                  resource_name: str = "", details: Dict = None):
        """記錄更新"""
        return self.log(ActionType.UPDATE, resource_type, resource_id, resource_name, details)
    
    def log_delete(self, resource_type: ResourceType, resource_id: str,
                  resource_name: str = "", details: Dict = None):
        """記錄刪除"""
        return self.log(ActionType.DELETE, resource_type, resource_id, resource_name, details)
    
    def log_execute(self, resource_type: ResourceType, resource_id: str,
                   resource_name: str = "", details: Dict = None):
        """記錄執行"""
        return self.log(ActionType.EXECUTE, resource_type, resource_id, resource_name, details)
    
    def get_user_activity(self, user_id: str,
                          start_date: datetime = None,
                          end_date: datetime = None) -> List[Dict]:
        """取得用戶活動"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        user_entries = [e for e in filtered if e.user_id == user_id]
        
        return [e.to_dict() for e in user_entries]
    
    def get_resource_history(self, resource_id: str) -> List[Dict]:
        """取得資源歷史"""
        resource_entries = [e for e in self.entries if e.resource_id == resource_id]
        return [e.to_dict() for e in resource_entries]
    
    def get_timeline(self, start_date: datetime = None,
                    end_date: datetime = None) -> List[Dict]:
        """取得時間線"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        return [e.to_dict() for e in filtered]
    
    def search(self, query: str, 
              filters: Dict = None) -> List[Dict]:
        """搜尋"""
        results = []
        
        for entry in self.entries:
            # 檢查關鍵字
            text = f"{entry.resource_name} {entry.action.value} {entry.resource_type.value}"
            text += " " + " ".join(str(v) for v in entry.details.values())
            
            if query.lower() not in text.lower():
                continue
            
            # 檢查過濾器
            if filters:
                if "user_id" in filters and entry.user_id != filters["user_id"]:
                    continue
                if "action" in filters and entry.action.value != filters["action"]:
                    continue
                if "resource_type" in filters and entry.resource_type.value != filters["resource_type"]:
                    continue
            
            results.append(entry.to_dict())
        
        return results
    
    def get_statistics(self, start_date: datetime = None,
                      end_date: datetime = None) -> Dict:
        """取得統計"""
        filtered = self.entries
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        # 按用戶統計
        by_user = defaultdict(int)
        # 按操作統計
        by_action = defaultdict(int)
        # 按資源類型統計
        by_resource = defaultdict(int)
        # 按小時統計
        by_hour = defaultdict(int)
        
        for e in filtered:
            by_user[e.user_id] += 1
            by_action[e.action.value] += 1
            by_resource[e.resource_type.value] += 1
            by_hour[e.timestamp.hour] += 1
        
        return {
            "total_entries": len(filtered),
            "unique_users": len(by_user),
            "by_user": dict(by_user),
            "by_action": dict(by_action),
            "by_resource_type": dict(by_resource),
            "by_hour": dict(by_hour),
        }
    
    def generate_report(self) -> str:
        """生成報告"""
        stats = self.get_statistics()
        
        report = f"""
# 📋 審計報告

## 總覽

| 指標 | 數值 |
|------|------|
| 總記錄數 | {stats['total_entries']} |
| 使用者數 | {stats['unique_users']} |

---

## 按操作

| 操作 | 次數 |
|------|------|
"""
        
        for action, count in sorted(stats['by_action'].items(), key=lambda x: -x[1]):
            report += f"| {action} | {count} |\n"
        
        report += f"""

## 按資源類型

| 資源 | 次數 |
|------|------|
"""
        
        for resource, count in sorted(stats['by_resource_type'].items(), key=lambda x: -x[1]):
            report += f"| {resource} | {count} |\n"
        
        return report


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    logger = AuditLogger()
    
    # 設定上下文
    logger.set_context("user-1", "Johnny")
    
    # 記錄操作
    print("=== Logging Actions ===")
    
    logger.log_create(
        ResourceType.TASK, "task-1", "登入功能",
        details={"priority": "high", "estimate": "4h"}
    )
    
    logger.log_update(
        ResourceType.TASK, "task-1", "登入功能",
        details={"status": "in_progress", "assignee": "johnny"}
    )
    
    logger.log_execute(
        ResourceType.MODEL, "gpt-4o", "AI 推理",
        details={"tokens": 1500, "cost": 0.0075}
    )
    
    # 取得統計
    print("\n=== Statistics ===")
    stats = logger.get_statistics()
    print(f"Total entries: {stats['total_entries']}")
    print(f"By action: {stats['by_action']}")
    print(f"By resource: {stats['by_resource_type']}")
    
    # 用戶活動
    print("\n=== User Activity ===")
    activity = logger.get_user_activity("user-1")
    print(f"Activity count: {len(activity)}")
    
    # 報告
    print("\n=== Report ===")
    print(logger.generate_report())
