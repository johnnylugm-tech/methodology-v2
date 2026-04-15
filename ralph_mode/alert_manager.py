"""
Ralph Mode - Alert Manager

統一的 Alert 發送介面，支援 Telegram、飛書、Console。

Author: methodology-v2
Version: 1.0.0
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable, List
from datetime import datetime


class AlertLevel(Enum):
    """Alert 等級"""
    SUCCESS = "success"      # ✅ 成功（可選發送）
    INFO = "info"          # ℹ️ 資訊（可選發送）
    WARNING = "warning"      # ⚠️ 警告（發送 Telegram）
    CRITICAL = "critical"   # 🔴 嚴重（發送 Telegram + 飛書）
    ERROR = "error"         # ❌ 錯誤（發送 Telegram + 飛書）


@dataclass
class AlertMessage:
    """Alert 訊息結構"""
    level: AlertLevel
    title: str
    message: str
    task_id: Optional[str] = None
    phase: Optional[int] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class AlertChannel:
    """Alert 頻道介面"""
    
    def send(self, alert: AlertMessage) -> bool:
        """發送 Alert"""
        raise NotImplementedError


class ConsoleChannel(AlertChannel):
    """Console 輸出頻道（測試用）"""
    
    def send(self, alert: AlertMessage) -> bool:
        formatted = self._format(alert)
        print(formatted)
        return True
    
    def _format(self, alert: AlertMessage) -> str:
        """格式化 Alert"""
        level_icons = {
            AlertLevel.SUCCESS: "✅",
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.ERROR: "❌",
        }
        
        icon = level_icons.get(alert.level, "📌")
        title = f"{icon} {alert.title}"
        
        lines = [
            "=" * 50,
            title,
            "=" * 50,
            alert.message,
        ]
        
        if alert.task_id:
            lines.append(f"Task: {alert.task_id}")
        if alert.phase:
            lines.append(f"Phase: {alert.phase}")
        if alert.timestamp:
            lines.append(f"Time: {alert.timestamp}")
        
        return "\n".join(lines)


class TelegramChannel(AlertChannel):
    """Telegram 頻道"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
    
    def send(self, alert: AlertMessage) -> bool:
        if not self.enabled:
            print(f"[Telegram] Alert: {alert.title} (Telegram not configured)")
            return False
        
        try:
            import urllib.request
            import urllib.parse
            
            text = self._format_telegram(alert)
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            req = urllib.request.Request(
                url,
                data=urllib.parse.urlencode(data).encode()
            )
            with urllib.request.urlopen(req) as response:
                return response.status == 200
            
        except Exception as e:
            print(f"[Telegram] Failed to send: {e}")
            return False
    
    def _format_telegram(self, alert: AlertMessage) -> str:
        level_prefixes = {
            AlertLevel.SUCCESS: "✅",
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.ERROR: "❌",
        }
        
        prefix = level_prefixes.get(alert.level, "📌")
        
        lines = [
            f"{prefix} *{alert.title}*",
            "",
            alert.message,
        ]
        
        if alert.phase:
            lines.append(f"Phase: {alert.phase}")
        
        return "\n".join(lines)


class FeishuChannel(AlertChannel):
    """飛書頻道"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url)
    
    def send(self, alert: AlertMessage) -> bool:
        if not self.enabled:
            print(f"[Feishu] Alert: {alert.title} (Feishu not configured)")
            return False
        
        try:
            import urllib.request
            import json
            
            payload = self._build_payload(alert)
            
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req) as response:
                return response.status == 200
            
        except Exception as e:
            print(f"[Feishu] Failed to send: {e}")
            return False
    
    def _build_payload(self, alert: AlertMessage) -> dict:
        level_colors = {
            AlertLevel.SUCCESS: "green",
            AlertLevel.INFO: "blue",
            AlertLevel.WARNING: "yellow",
            AlertLevel.CRITICAL: "red",
            AlertLevel.ERROR: "red",
        }
        
        return {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"{alert.title}"
                    },
                    "color": level_colors.get(alert.level, "blue")
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": alert.message
                        }
                    }
                ]
            }
        }


class AlertManager:
    """
    統一 Alert 管理器
    
    支援多頻道發送，根據 Alert 等級決定發送哪些頻道。
    
    Example:
        >>> manager = AlertManager()
        >>> manager.send(
        ...     level=AlertLevel.CRITICAL,
        ...     title="HR-13 Timeout",
        ...     message="Phase 3 exceeded 3x estimated time"
        ... )
    """
    
    def __init__(
        self,
        channels: List[AlertChannel] = None,
        console_enabled: bool = True,
        telegram_enabled: bool = True,
        feishu_enabled: bool = True
    ):
        """
        初始化 AlertManager
        
        Args:
            channels: 自定義頻道列表
            console_enabled: 啟用 Console 頻道
            telegram_enabled: 啟用 Telegram 頻道
            feishu_enabled: 啟用 飛書 頻道
        """
        self.channels: List[AlertChannel] = []
        
        if channels:
            self.channels.extend(channels)
        else:
            if console_enabled:
                self.channels.append(ConsoleChannel())
            if telegram_enabled:
                self.channels.append(TelegramChannel())
            if feishu_enabled:
                self.channels.append(FeishuChannel())
    
    def send(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        task_id: Optional[str] = None,
        phase: Optional[int] = None
    ) -> bool:
        """
        發送 Alert
        
        Args:
            level: Alert 等級
            title: 標題
            message: 訊息內容
            task_id: 任務 ID
            phase: Phase 編號
            
        Returns:
            True if any channel succeeded
        """
        alert = AlertMessage(
            level=level,
            title=title,
            message=message,
            task_id=task_id,
            phase=phase
        )
        
        # 根據等級決定發送哪些頻道
        channels_to_send = self._get_channels_for_level(level)
        
        results = []
        for channel in channels_to_send:
            try:
                result = channel.send(alert)
                results.append(result)
            except Exception as e:
                print(f"[AlertManager] Channel {channel.__class__.__name__} failed: {e}")
                results.append(False)
        
        return any(results)
    
    def _get_channels_for_level(self, level: AlertLevel) -> List[AlertChannel]:
        """
        根據 Alert 等級取得應該發送的頻道
        
        等級規則：
        - SUCCESS / INFO: 只發 Console（可選）
        - WARNING: 發 Telegram
        - CRITICAL / ERROR: 發 Telegram + 飛書
        """
        telegram_channel = None
        feishu_channel = None
        console_channel = None
        
        for channel in self.channels:
            if isinstance(channel, TelegramChannel):
                telegram_channel = channel
            elif isinstance(channel, FeishuChannel):
                feishu_channel = channel
            elif isinstance(channel, ConsoleChannel):
                console_channel = channel
        
        if level in (AlertLevel.CRITICAL, AlertLevel.ERROR):
            return [c for c in [telegram_channel, feishu_channel] if c]
        elif level == AlertLevel.WARNING:
            return [c for c in [telegram_channel, console_channel] if c]
        else:
            # SUCCESS / INFO: 只發 Console
            return [console_channel] if console_channel else []
    
    def format_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str
    ) -> str:
        """格式化 Alert（用於 Console 輸出）"""
        console = ConsoleChannel()
        alert = AlertMessage(level=level, title=title, message=message)
        return console._format(alert)


# ============== Convenience Functions ==============

# 全域 AlertManager 實例
_default_manager: Optional[AlertManager] = None


def get_default_manager() -> AlertManager:
    """取得全域 AlertManager"""
    global _default_manager
    if _default_manager is None:
        _default_manager = AlertManager()
    return _default_manager


def send_alert(
    level: AlertLevel,
    title: str,
    message: str,
    task_id: Optional[str] = None,
    phase: Optional[int] = None
) -> bool:
    """發送 Alert（方便函數）"""
    return get_default_manager().send(level, title, message, task_id, phase)
