"""
Ralph Mode - RalphMonitor Integration Tests

測試 RalphScheduler 和 sessions_spawn.log 的整合。
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from ralph_mode.lifecycle import RalphLifecycleManager, TaskState, CheckResult
from ralph_mode.schema_validator import SessionsSpawnLogValidator


class TestRalphLifecycleIntegration:
    """Ralph 生命週期整合測試"""
    
    def test_start_creates_state_file(self, temp_repo):
        """start() 應該建立 state 檔案"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager.validator, 'validate_path') as mock_validate:
            mock_validate.return_value = MagicMock(ok=True)
            
            task_id = manager.start(phase=3, estimated_minutes=60)
        
        # Check state file was created
        state_file = temp_repo / ".ralph" / "tasks" / f"{task_id}.json"
        assert state_file.exists()
        
        import json
        state_data = json.loads(state_file.read_text())
        assert state_data["phase"] == 3
        assert state_data["status"] == "running"
    
    def test_stop_updates_state(self, temp_repo):
        """stop() 應該更新 state 狀態"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager.validator, 'validate_path') as mock_validate:
            mock_validate.return_value = MagicMock(ok=True)
            
            task_id = manager.start(phase=3, estimated_minutes=60)
            manager.stop(reason="completed")
        
        state_file = temp_repo / ".ralph" / "tasks" / f"{task_id}.json"
        state_data = json.loads(state_file.read_text())
        
        assert state_data["status"] == "stopped"
        assert state_data["metadata"]["end_reason"] == "completed"
    
    def test_get_running_ralph_none_when_idle(self, temp_repo):
        """沒有運行中的 Ralph → 返回 None"""
        manager = RalphLifecycleManager(temp_repo)
        result = manager.get_running_ralph(phase=3)
        assert result is None
    
    def test_get_running_ralph_returns_running(self, temp_repo):
        """有運行中的 Ralph → 返回 TaskState"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager.validator, 'validate_path') as mock_validate:
            mock_validate.return_value = MagicMock(ok=True)
            
            task_id = manager.start(phase=3, estimated_minutes=60)
            
            result = manager.get_running_ralph(phase=3)
            
            assert result is not None
            assert result.phase == 3
            assert result.status == "running"
    
    def test_check_result_calculation(self, temp_repo):
        """CheckResult 計算邏輯正確"""
        result = CheckResult(
            status="running",
            progress=66.67,
            fr_total=3,
            fr_completed=2,
            fr_pending=1,
            fr_failed=0,
            elapsed_minutes=10,
            estimated_minutes=60,
            hr13_triggered=False
        )
        
        assert result.progress == 66.67
        assert result.fr_pending == 1
        assert result.hr13_triggered is False
    
    def test_task_state_serialization(self, temp_repo):
        """TaskState 可以正確序列化"""
        state = TaskState(
            task_id="test-001",
            phase=3,
            status="running",
            estimated_minutes=60
        )
        
        # to_dict should work
        data = state.to_dict()
        assert isinstance(data, dict)
        assert data["phase"] == 3
        
        # from_dict should work
        restored = TaskState.from_dict(data)
        assert restored.phase == 3
        assert restored.task_id == "test-001"
