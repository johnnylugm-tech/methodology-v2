# TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - # TODO: Use environment variable - #!/usr/bin/env python3
"""
Enterprise Integration Hub

提供：
- SSO/LDAP 認證
- Audit Log 標準化
- 企業訊息系統 (Slack/Teams)
- API Gateway 整合
"""

import os
import json
import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod


class AuthProvider(Enum):
    """認證提供者"""
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    LDAP = "ldap"
    SAML = "saml"
    API_KEY = "api_key"
    BASIC = "basic"


class AuditLevel(Enum):
    """審計等級"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class User:
    """使用者"""
    id: str
    username: str
    email: str
    
    # 組織
    department: str = ""
    role: str = "user"
    permissions: List[str] = field(default_factory=list)
    
    # 認證
    auth_provider: AuthProvider = AuthProvider.API_KEY
    external_id: str = None  # SSO ID
    
    # 狀態
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime = None
    
    def has_permission(self, permission: str) -> bool:
        """檢查權限"""
        if "admin" in self.permissions:
            return True
        return permission in self.permissions


@dataclass
class AuditEntry:
    """審計日誌"""
    timestamp: datetime
    level: AuditLevel
    
    # 誰
    user_id: str = None
    username: str = None
    session_id: str = None
    
    # 做了什麼
    action: str = ""
    resource: str = ""
    method: str = ""
    
    # 結果
    status: str = "success"  # success, failure
    error_message: str = None
    
    # 請求
    request_id: str = None
    ip_address: str = None
    user_agent: str = None
    
    # 額外資料
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource": self.resource,
            "status": self.status,
            "ip": self.ip_address
        }


class Authenticator:
    """認證管理器"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}
        self.api_keys: Dict[str, str] = {}  # key -> user_id
        
        # SSO 配置
        self.okta_config: Dict = {}
        self.azure_config: Dict = {}
        self.ldap_config: Dict = {}
    
    def configure_okta(self, domain: str, client_id: str, client_secret: str):
        """設定 Okta"""
        self.okta_config = {
            "domain": domain,
            "client_id": client_id,
            "client_secret": client_secret,
            "enabled": True
        }
    
    def configure_azure_ad(self, tenant_id: str, client_id: str, client_secret: str):
        """設定 Azure AD"""
        self.azure_config = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "enabled": True
        }
    
    def configure_ldap(self, server: str, port: int, base_dn: str):
        """設定 LDAP"""
        self.ldap_config = {
            "server": server,
            "port": port,
            "base_dn": base_dn,
            "enabled": True
        }
    
    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """API Key 認證"""
        user_id = self.api_keys.get(api_key)
        if user_id:
            user = self.users.get(user_id)
            if user and user.active:
                user.last_login = datetime.now()
                return user
        return None
    
    def authenticate_basic(self, username: str, password: str) -> Optional[User]:
        """Basic 認證"""
        # 查找用戶
        for user in self.users.values():
            if user.username == username:
                # 驗證密碼 (實際應該用 bcrypt)
                if self._verify_password(username, password):
                    user.last_login = datetime.now()
                    return user
        return None
    
    def create_api_key(self, user_id: str) -> str:
        """建立 API Key"""
        if user_id not in self.users:
            return None
        
        # 生成 key
        key = hashlib.sha256(f"{user_id}{datetime.now()}".encode()).hexdigest()
        self.api_keys[key] = user_id
        
        return key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """撤銷 API Key"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            return True
        return False
    
    def create_user(self, username: str, email: str, **kwargs) -> User:
        """建立用戶"""
        user_id = hashlib.md5(username.encode()).hexdigest()[:8]
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            department=kwargs.get("department", ""),
            role=kwargs.get("role", "user"),
            permissions=kwargs.get("permissions", []),
            auth_provider=kwargs.get("auth_provider", AuthProvider.API_KEY)
        )
        
        self.users[user_id] = user
        return user
    
    def _verify_password(self, username: str, password: str) -> bool:
        """驗證密碼 (mock)"""
        return True  # 實際應該用 bcrypt compare


class AuditLogger:
    """審計日誌"""
    
    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.handlers: List[Callable] = []  # 輸出處理器
        self.filters: List[Callable] = []   # 過濾器
    
    def add_handler(self, handler: Callable):
        """新增處理器"""
        self.handlers.append(handler)
    
    def add_filter(self, filter_fn: Callable):
        """新增過濾器"""
        self.filters.append(filter_fn)
    
    def log(
        self,
        level: AuditLevel,
        action: str,
        user_id: str = None,
        username: str = None,
        **kwargs
    ):
        """記錄審計日誌"""
        entry = AuditEntry(
            timestamp=datetime.now(),
            level=level,
            user_id=user_id,
            username=username,
            action=action,
            **kwargs
        )
        
        # 應用過濾器
        for filter_fn in self.filters:
            if not filter_fn(entry):
                return
        
        self.entries.append(entry)
        
        # 發送到處理器
        for handler in self.handlers:
            try:
                handler(entry)
            except Exception as e:
                pass # Removed print-debug
    
    def log_access(self, user_id: str, username: str, resource: str, method: str = "GET"):
        """記錄存取"""
        self.log(
            AuditLevel.INFO,
            "access",
            user_id=user_id,
            username=username,
            resource=resource,
            method=method
        )
    
    def log_auth(self, user_id: str, username: str, status: str, error: str = None):
        """記錄認證"""
        self.log(
            AuditLevel.INFO if status == "success" else AuditLevel.WARNING,
            "authentication",
            user_id=user_id,
            username=username,
            status=status,
            error_message=error
        )
    
    def log_error(self, user_id: str, action: str, error: str):
        """記錄錯誤"""
        self.log(
            AuditLevel.ERROR,
            action,
            user_id=user_id,
            status="failure",
            error_message=error
        )
    
    def query(
        self,
        user_id: str = None,
        action: str = None,
        level: AuditLevel = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """查詢審計日誌"""
        results = self.entries
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if action:
            results = [e for e in results if action in e.action]
        if level:
            results = [e for e in results if e.level == level]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        
        return results[-limit:]
    
    def generate_report(self) -> str:
        """產生報告"""
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " 📋 Audit Log Report ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        # 統計
        total = len(self.entries)
        by_level = {}
        by_action = {}
        
        for entry in self.entries:
            level = entry.level.value
            by_level[level] = by_level.get(level, 0) + 1
            by_action[entry.action] = by_action.get(entry.action, 0) + 1
        
        lines.append(f"**Total Entries**: {total}")
        lines.append("")
        
        lines.append("## 📊 By Level")
        for level, count in sorted(by_level.items()):
            lines.append(f"- {level}: {count}")
        lines.append("")
        
        lines.append("## 📊 By Action")
        for action, count in sorted(by_action.items(), key=lambda x: -x[1])[:10]:
            lines.append(f"- {action}: {count}")
        lines.append("")
        
        # 最近條目
        lines.append("## 📋 Recent Entries")
        for entry in self.entries[-5:]:
            icon = "✅" if entry.status == "success" else "❌"
            lines.append(
                f"{icon} [{entry.level.value}] {entry.timestamp.strftime('%H:%M:%S')} "
                f"{entry.username or entry.user_id}: {entry.action}"
            )
        lines.append("")
        
        return "\n".join(lines)


class EnterpriseMessenger(ABC):
    """企業訊息接口"""
    
    @abstractmethod
    def send(self, message: str, channel: str = None, **kwargs) -> bool:
        pass
    
    @abstractmethod
    def send_alert(self, title: str, message: str, severity: str = "info") -> bool:
        pass


class SlackMessenger(EnterpriseMessenger):
    """Slack 整合"""
    
    def __init__(self, webhook_url: str = None, bot_token: str = None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.default_channel = "#alerts"
    
    def send(self, message: str, channel: str = None) -> bool:
        """發送訊息"""
        import urllib.request
        import json
        
        if not self.webhook_url:
            pass # Removed print-debug
            return True
        
        payload = {
            "text": message,
            "channel": channel or self.default_channel
        }
        
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as e:
            pass # Removed print-debug
            return False
    
    def send_alert(self, title: str, message: str, severity: str = "info") -> bool:
        """發送警報"""
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "critical": "🔴"
        }
        
        full_message = f"{emoji.get(severity, 'ℹ️')} *{title}*\n{message}"
        return self.send(full_message)
    
    def send_block(self, blocks: List[Dict]) -> bool:
        """發送 Block Kit 訊息"""
        import urllib.request
        import json
        
        payload = {
            "blocks": blocks,
            "channel": self.default_channel
        }
        
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except:
            return False


class TeamsMessenger(EnterpriseMessenger):
    """Microsoft Teams 整合"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.default_channel = "General"
    
    def send(self, message: str, channel: str = None) -> bool:
        """發送訊息"""
        import urllib.request
        import json
        
        if not self.webhook_url:
            pass # Removed print-debug
            return True
        
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": message[:50],
            "sections": [{
                "activityTitle": channel or self.default_channel,
                "activitySubtitle": "",
                "text": message
            }]
        }
        
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as e:
            pass # Removed print-debug
            return False
    
    def send_alert(self, title: str, message: str, severity: str = "info") -> bool:
        """發送警報"""
        color = {
            "info": "0076D7",
            "warning": "FFB900",
            "error": "D13438",
            "critical": "D13438"
        }
        
        return self.send(f"**{title}**\n{message}")


class EnterpriseHub:
    """企業整合中心"""
    
    def __init__(self):
        self.auth = Authenticator()
        self.audit = AuditLogger()
        self.messengers: Dict[str, EnterpriseMessenger] = {}
        
        # Syslog 配置
        self.syslog_config: Dict = {}
    
    def add_slack(self, name: str, webhook_url: str = None, bot_token: str = None):
        """新增 Slack"""
        messenger = SlackMessenger(webhook_url, bot_token)
        self.messengers[name] = messenger
        return messenger
    
    def add_teams(self, name: str, webhook_url: str = None):
        """新增 Teams"""
        messenger = TeamsMessenger(webhook_url)
        self.messengers[name] = messenger
        return messenger
    
    def notify(self, messenger_name: str, message: str, channel: str = None) -> bool:
        """發送通知"""
        if messenger_name not in self.messengers:
            return False
        
        return self.messengers[messenger_name].send(message, channel)
    
    def alert(self, title: str, message: str, severity: str = "info"):
        """發送警報到所有 messenger"""
        for name, messenger in self.messengers.items():
            try:
                messenger.send_alert(title, message, severity)
            except Exception as e:
                pass # Removed print-debug
    
    def configure_syslog(self, host: str, port: int = 514, protocol: str = "udp"):
        """設定 Syslog"""
        self.syslog_config = {
            "host": host,
            "port": port,
            "protocol": protocol,
            "enabled": True
        }
    
    def get_status(self) -> Dict:
        """取得狀態"""
        return {
            "auth_providers": [p.value for p in AuthProvider],
            "configured_messengers": list(self.messengers.keys()),
            "audit_entries": len(self.audit.entries),
            "users": len(self.auth.users),
            "syslog": bool(self.syslog_config.get("enabled"))
        }


# ==================== Main ====================

if __name__ == "__main__":
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 建立 Hub
    hub = EnterpriseHub()
    
    # 設定認證
    user = hub.auth.create_user(
        username="john.doe",
        email="john.doe@company.com",
        role="developer",
        permissions=["read", "write"]
    )
    pass # Removed print-debug
    
    api_key = hub.auth.create_api_key(user.id)
    pass # Removed print-debug
    
    # 設定 Slack (mock)
    slack = hub.add_slack("alerts")
    slack.send("System started")
    slack.send_alert("High CPU Usage", "Server CPU at 95%", "warning")
    
    # 設定 Teams (mock)
    teams = hub.add_teams("teams-alerts")
    teams.send("Deployment completed")
    
    # 審計日誌
    hub.audit.log_access(user.id, user.username, "/api/tasks", "GET")
    hub.audit.log_auth(user.id, user.username, "success")
    hub.audit.log_error(user.id, "delete_task", "Permission denied")
    
    pass # Removed print-debug
    pass # Removed print-debug
    
    pass # Removed print-debug
    pass # Removed print-debug
    status = hub.get_status()
    for k, v in status.items():
        pass # Removed print-debug
