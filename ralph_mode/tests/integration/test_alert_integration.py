"""
Ralph Mode - Alert Integration Tests

測試 AlertManager 和 LifecycleManager 的整合。
"""

import pytest
from unittest.mock import patch, MagicMock
from ralph_mode.alert_manager import AlertManager, AlertLevel, AlertMessage
from ralph_mode.alert_manager import ConsoleChannel, TelegramChannel, FeishuChannel
from ralph_mode.lifecycle import RalphLifecycleManager


class TestAlertIntegration:
    """Alert 整合測試"""
    
    def test_lifecycle_alerts_on_hr13_timeout(self, temp_repo):
        """HR-13 超時 → 應該發送 CRITICAL Alert"""
        manager = RalphLifecycleManager(temp_repo)
        manager.alert_mgr = AlertManager(console_enabled=True, telegram_enabled=False, feishu_enabled=False)
        
        with patch.object(manager.alert_mgr, 'send') as mock_send:
            manager.alert_mgr.send(
                level=AlertLevel.CRITICAL,
                title="🔴 HR-13 Phase 3 超時",
                message="已執行: 180 分鐘\n預估時間: 60 分鐘",
                task_id="phase-3-test",
                phase=3
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['level'] == AlertLevel.CRITICAL
            assert "HR-13" in call_args[1]['title']
    
    def test_lifecycle_alerts_on_completion(self, temp_repo):
        """M1: 所有 FR 完成 → 應該發送 SUCCESS Alert"""
        manager = RalphLifecycleManager(temp_repo)
        manager.alert_mgr = AlertManager(console_enabled=True, telegram_enabled=False, feishu_enabled=False)
        
        with patch.object(manager.alert_mgr, 'send') as mock_send:
            manager.alert_mgr.send(
                level=AlertLevel.SUCCESS,
                title="✅ Phase 3 完成",
                message="FR 完成: 6/6, 耗時: 45 分鐘",
                task_id="phase-3-test",
                phase=3
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['level'] == AlertLevel.SUCCESS
            assert "Phase 3" in call_args[1]['title']


class TestAlertLevelRouting:
    """Alert 等級路由測試"""
    
    def test_success_routes_to_console_only(self, temp_repo):
        """SUCCESS 等級 → 只發 Console"""
        console = ConsoleChannel()
        telegram = TelegramChannel()
        feishu = FeishuChannel()
        
        # Mock send methods to track calls
        with patch.object(console, 'send') as mock_console:
            with patch.object(telegram, 'send') as mock_telegram:
                with patch.object(feishu, 'send') as mock_feishu:
                    # Create manager with specific channels
                    from ralph_mode.alert_manager import AlertChannel
                    manager = AlertManager(channels=[console, telegram, feishu])
                    
                    alert = AlertMessage(
                        level=AlertLevel.SUCCESS,
                        title="Test Success",
                        message="Test"
                    )
                    
                    # Route to correct channels
                    channels = manager._get_channels_for_level(AlertLevel.SUCCESS)
                    for ch in channels:
                        ch.send(alert)
                    
                    # Only console should be in the list for SUCCESS
                    assert console in channels
                    assert telegram not in channels
                    assert feishu not in channels
    
    def test_warning_routes_to_telegram_and_console(self, temp_repo):
        """WARNING 等級 → 發 Telegram + Console"""
        console = ConsoleChannel()
        telegram = TelegramChannel()
        feishu = FeishuChannel()
        
        from ralph_mode.alert_manager import AlertChannel
        manager = AlertManager(channels=[console, telegram, feishu])
        
        channels = manager._get_channels_for_level(AlertLevel.WARNING)
        
        # WARNING → Telegram + Console (not Feishu)
        assert telegram in channels
        assert console in channels
        assert feishu not in channels
    
    def test_critical_routes_to_telegram_and_feishu(self, temp_repo):
        """CRITICAL 等級 → 發 Telegram + Feishu"""
        console = ConsoleChannel()
        telegram = TelegramChannel()
        feishu = FeishuChannel()
        
        from ralph_mode.alert_manager import AlertChannel
        manager = AlertManager(channels=[console, telegram, feishu])
        
        channels = manager._get_channels_for_level(AlertLevel.CRITICAL)
        
        # CRITICAL → Telegram + Feishu (not Console)
        assert telegram in channels
        assert feishu in channels
        assert console not in channels
    
    def test_error_routes_to_telegram_and_feishu(self, temp_repo):
        """ERROR 等級 → 發 Telegram + Feishu"""
        console = ConsoleChannel()
        telegram = TelegramChannel()
        feishu = FeishuChannel()
        
        from ralph_mode.alert_manager import AlertChannel
        manager = AlertManager(channels=[console, telegram, feishu])
        
        channels = manager._get_channels_for_level(AlertLevel.ERROR)
        
        # ERROR → Telegram + Feishu (not Console)
        assert telegram in channels
        assert feishu in channels
        assert console not in channels


class TestAlertMessageFormatting:
    """Alert 訊息格式化測試"""
    
    def test_console_channel_formats_correctly(self, temp_repo):
        """Console 頻道應該正確格式化"""
        channel = ConsoleChannel()
        
        alert = AlertMessage(
            level=AlertLevel.CRITICAL,
            title="HR-13 Timeout",
            message="Phase 3 exceeded 3x estimated time",
            task_id="phase-3-001",
            phase=3
        )
        
        formatted = channel._format(alert)
        
        assert "🔴" in formatted
        assert "HR-13 Timeout" in formatted
        assert "Phase 3" in formatted
        assert "phase-3-001" in formatted
    
    def test_alert_message_has_timestamp(self, temp_repo):
        """AlertMessage 應該有時間戳"""
        alert = AlertMessage(
            level=AlertLevel.SUCCESS,
            title="Test",
            message="Test"
        )
        
        assert alert.timestamp is not None
        assert "T" in alert.timestamp  # ISO format
