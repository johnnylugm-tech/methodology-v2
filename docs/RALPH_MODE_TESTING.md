# Ralph Mode 測試方案

> **版本**: v1.0
> **日期**: 2026-04-15
> **Framework**: methodology-v2
> **狀態**: 待實作

---

## 1. 測試策略

### 1.1 測試金字塔

```
         ┌─────────────────┐
         │   E2E 測試      │  ← 完整流程，端到端
         │   (2 個)       │
         ├─────────────────┤
         │  整合測試       │  ← 多元件協作
         │   (7 個)       │
         ├─────────────────┤
         │   單元測試      │  ← 每個元件獨立
         │   (15 個)      │
         ├─────────────────┤
         │   Mock/Stub    │  ← 隔離外部依賴
         │   (必備)        │
         └─────────────────┘
```

### 1.2 測試檔案結構

```
ralph_mode/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures + mocks
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_schema_validator.py
│   │   ├── test_output_verifier.py
│   │   ├── test_task_parser.py
│   │   ├── test_alert_manager.py
│   │   └── test_lifecycle_manager.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_ralph_monitor.py
│   │   └── test_lifecycle_integration.py
│   └── e2e/
│       ├── __init__.py
│       └── test_ralph_e2e.sh
└── ...
```

---

## 2. Mock/Stub 層

### 2.1 外部依賴隔離

| 依賴 | Mock 方式 | 理由 |
|------|----------|------|
| `sessions_spawn.log` | 臨時檔案 + 任意內容 | 避免影響真實專案 |
| Telegram API | Log capture（只打印不發送）| 避免發送測試訊息 |
| 飛書 API | Log capture（只打印不發送）| 避免發送測試訊息 |
| `sessions_spawn` tool | Mock return 值 | 無法在單元測試中呼叫 |

### 2.2 conftest.py 範例

```python
"""
ralph_mode/tests/conftest.py

pytest fixtures 和 mocks
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def temp_repo():
    """建立臨時測試目錄"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_log_schema():
    """有效的 sessions_spawn.log schema v1.0"""
    return {
        "schema_version": "1.0",
        "schema_definition": {
            "required": ["timestamp", "session_id", "fr", "status"],
            "status_values": ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
        },
        "entries": []
    }


@pytest.fixture
def sample_log_entries():
    """範例 log entries"""
    return [
        {
            "timestamp": "2026-04-15T19:41:00",
            "session_id": "sess-abc123",
            "fr": "FR-01",
            "status": "COMPLETED"
        },
        {
            "timestamp": "2026-04-15T19:45:00",
            "session_id": "sess-def456",
            "fr": "FR-02",
            "status": "COMPLETED"
        },
        {
            "timestamp": "2026-04-15T19:50:00",
            "session_id": "sess-ghi789",
            "fr": "FR-03",
            "status": "PENDING"
        }
    ]


@pytest.fixture
def mock_alert_channels():
    """Mock Alert 頻道"""
    with patch('ralph_mode.alert_manager.telegram_send') as mock_telegram:
        with patch('ralph_mode.alert_manager.feishu_send') as mock_feishu:
            yield {
                'telegram': mock_telegram,
                'feishu': mock_feishu
            }


@pytest.fixture
def mock_time():
    """Mock 時間，用於 HR-13 超時測試"""
    with patch('ralph_mode.lifecycle.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2026, 4, 15, 20, 0, 0)
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt
```

---

## 3. 單元測試（15 個）

### 3.1 SessionsSpawnLogValidator（3 個測試）

```python
"""
ralph_mode/tests/unit/test_schema_validator.py
"""

import pytest
from ralph_mode.schema_validator import SessionsSpawnLogValidator


class TestSessionsSpawnLogValidator:
    """SessionsSpawnLogValidator 單元測試"""
    
    def test_valid_schema_v1(self, valid_log_schema):
        """V1.0 schema 應該被接受"""
        validator = SessionsSpawnLogValidator()
        result = validator.validate_content(valid_log_schema)
        assert result.ok is True
        assert result.error is None
    
    def test_valid_schema_v09(self):
        """V0.9 schema 應該被接受（向後相容）"""
        validator = SessionsSpawnLogValidator()
        log_content = {
            "schema_version": "0.9",
            "entries": []
        }
        result = validator.validate_content(log_content)
        assert result.ok is True
    
    def test_unsupported_schema(self):
        """不支援的 schema 版本應該被拒絕"""
        validator = SessionsSpawnLogValidator()
        log_content = {
            "schema_version": "9.9",
            "entries": []
        }
        result = validator.validate_content(log_content)
        assert result.ok is False
        assert "Unsupported schema" in result.error
        assert "9.9" in result.error
    
    def test_missing_schema_version(self):
        """缺少 schema_version 應該被拒絕"""
        validator = SessionsSpawnLogValidator()
        log_content = {
            "entries": []
        }
        result = validator.validate_content(log_content)
        assert result.ok is False
        assert "No schema_version" in result.error
    
    def test_parse_entry_valid(self):
        """正確的 entry 應該被正確解析"""
        validator = SessionsSpawnLogValidator()
        entry = {
            "timestamp": "2026-04-15T19:41:00",
            "session_id": "sess-abc",
            "fr": "FR-01",
            "status": "COMPLETED"
        }
        parsed = validator.parse_entry(entry)
        assert parsed.fr == "FR-01"
        assert parsed.status == "COMPLETED"
        assert parsed.session_id == "sess-abc"
```

### 3.2 OutputVerifier（4 個測試）

```python
"""
ralph_mode/tests/unit/test_output_verifier.py
"""

import pytest
from pathlib import Path
from ralph_mode.output_verifier import OutputVerifier, VerificationResult


class TestOutputVerifier:
    """OutputVerifier 單元測試"""
    
    def test_verify_fr_all_pass(self, temp_repo):
        """所有檔案都存在且有效 → passed"""
        # 建立測試檔案
        (temp_repo / "fr01.py").write_text("import os\nclass Fr01:\n    pass\n")
        (temp_repo / "test_fr01.py").write_text("import pytest\ndef test_fr01():\n    pass\n")
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["fr01.py", "test_fr01.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is True
        assert len(result.errors) == 0
    
    def test_verify_fr_missing_file(self, temp_repo):
        """檔案缺失 → failed"""
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["nonexistent.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        assert "Missing" in result.errors[0]
        assert "nonexistent.py" in result.errors[0]
    
    def test_verify_fr_too_small(self, temp_repo):
        """檔案太小 (< 100 bytes) → failed"""
        (temp_repo / "tiny.py").write_text("x = 1")  # 不到 100 bytes
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["tiny.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        assert "Too small" in result.errors[0]
    
    def test_verify_fr_no_code(self, temp_repo):
        """Python 檔案沒有程式碼 → failed"""
        (temp_repo / "empty.py").write_text("# just a comment\n")  # 沒有 import/class/def
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["empty.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        assert "No code found" in result.errors[0]
    
    def test_verify_fr_multiple_errors(self, temp_repo):
        """多個錯誤 → 所有錯誤都被報告"""
        # 只建立一個小檔案
        (temp_repo / "small.py").write_text("x = 1")
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["small.py", "missing.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        assert len(result.errors) == 2  # 一個 Too small，一個 Missing
```

### 3.3 TaskOutputParser（2 個測試）

```python
"""
ralph_mode/tests/unit/test_task_parser.py
"""

import pytest
from ralph_mode.task_parser import TaskOutputParser


class TestTaskOutputParser:
    """TaskOutputParser 單元測試"""
    
    def test_parse_simple_output(self):
        """簡單的 OUTPUT 段落應該被正確解析"""
        task_text = """
TASK: FR-01 processing
OUTPUT:
- 03-development/src/fr01.py
- tests/test_fr01.py

## Other content
"""
        parser = TaskOutputParser()
        outputs = parser.parse(task_text)
        
        assert len(outputs) == 2
        assert "03-development/src/fr01.py" in outputs
        assert "tests/test_fr01.py" in outputs
    
    def test_parse_no_output_section(self):
        """沒有 OUTPUT 段落 → 返回空列表"""
        task_text = """
TASK: FR-01 processing
## No OUTPUT section
"""
        parser = TaskOutputParser()
        outputs = parser.parse(task_text)
        
        assert len(outputs) == 0
    
    def test_parse_malformed_output(self):
        """格式錯誤的 OUTPUT → 嘗試解析"""
        task_text = """
OUTPUT:
not a list
just text
"""
        parser = TaskOutputParser()
        outputs = parser.parse(task_text)
        
        # 應該返回空或盡量解析
        assert isinstance(outputs, list)
```

### 3.4 AlertManager（3 個測試）

```python
"""
ralph_mode/tests/unit/test_alert_manager.py
"""

import pytest
from unittest.mock import Mock, patch
from ralph_mode.alert_manager import AlertManager, AlertLevel


class TestAlertManager:
    """AlertManager 單元測試"""
    
    def test_send_success_alert(self, mock_alert_channels):
        """SUCCESS 等級 → 只發 Telegram（可選）"""
        manager = AlertManager()
        manager.send(
            level=AlertLevel.SUCCESS,
            title="Phase 3 完成",
            message="FR 完成: 6/6"
        )
        
        # SUCCESS 不發送（可選），所以不應該呼叫
        # mock_alert_channels['telegram'].assert_not_called()
    
    def test_send_critical_alert(self, mock_alert_channels):
        """CRITICAL 等級 → 發 Telegram + 飛書"""
        manager = AlertManager()
        manager.send(
            level=AlertLevel.CRITICAL,
            title="HR-13 超時",
            message="已執行 180 分鐘"
        )
        
        mock_alert_channels['telegram'].assert_called_once()
        mock_alert_channels['feishu'].assert_called_once()
    
    def test_send_warning_alert(self, mock_alert_channels):
        """WARNING 等級 → 只發 Telegram"""
        manager = AlertManager()
        manager.send(
            level=AlertLevel.WARNING,
            title="L2 驗證失敗",
            message="FR-03 產出驗證失敗"
        )
        
        mock_alert_channels['telegram'].assert_called_once()
        mock_alert_channels['feishu'].assert_not_called()
    
    def test_format_alert_message(self):
        """Alert 格式化正確"""
        manager = AlertManager()
        formatted = manager.format(
            level=AlertLevel.CRITICAL,
            title="HR-13 超時",
            message="已執行 180 分鐘"
        )
        
        assert "🔴 CRITICAL" in formatted
        assert "HR-13 超時" in formatted
        assert "已執行 180 分鐘" in formatted
```

### 3.5 RalphLifecycleManager（3 個測試）

```python
"""
ralph_mode/tests/unit/test_lifecycle_manager.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ralph_mode.lifecycle import RalphLifecycleManager, TaskState


class TestRalphLifecycleManager:
    """RalphLifecycleManager 單元測試"""
    
    def test_start_creates_task_state(self, temp_repo):
        """start() 應該建立 TaskState"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager, '_save_state'):
            task_id = manager.start(phase=3, estimated_minutes=60)
        
        assert task_id.startswith("phase-3-")
        assert manager._current_task_id == task_id
    
    def test_stop_clears_task_state(self, temp_repo):
        """stop() 應該清除 TaskState"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager, '_save_state'):
            task_id = manager.start(phase=3, estimated_minutes=60)
        
        with patch.object(manager, '_delete_state'):
            manager.stop(reason="completed")
        
        assert manager._current_task_id is None
    
    def test_get_running_ralph_returns_task(self, temp_repo):
        """get_running_ralph() 應該返回運行中的 TaskState"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager, '_load_all_states') as mock_load:
            mock_load.return_value = {
                "phase-3-running": TaskState(
                    task_id="phase-3-running",
                    phase=3,
                    status="running"
                )
            }
            
            result = manager.get_running_ralph(phase=3)
            
            assert result is not None
            assert result.phase == 3
            assert result.status == "running"
    
    def test_get_running_ralph_returns_none_when_not_running(self, temp_repo):
        """沒有運行中的 Ralph → 返回 None"""
        manager = RalphLifecycleManager(temp_repo)
        
        with patch.object(manager, '_load_all_states') as mock_load:
            mock_load.return_value = {}
            
            result = manager.get_running_ralph(phase=3)
            
            assert result is None
```

---

## 4. 整合測試（7 個）

### 4.1 test_ralph_monitor.py

```python
"""
ralph_mode/tests/integration/test_ralph_monitor.py

RalphScheduler 和 sessions_spawn.log 的整合測試
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from ralph_mode.lifecycle import RalphLifecycleManager
from ralph_mode.schema_validator import SessionsSpawnLogValidator


class TestRalphMonitor:
    """Ralph 監控邏輯整合測試"""
    
    def test_check_detects_all_completed(self, temp_repo, valid_log_schema, sample_log_entries):
        """所有 FR COMPLETED → check() 返回 completed"""
        # Setup: 所有 FR 都 COMPLETED
        all_completed = sample_log_entries.copy()
        for entry in all_completed:
            entry["status"] = "COMPLETED"
        
        valid_log_schema["entries"] = all_completed
        log_path = temp_repo / ".methodology" / "sessions_spawn.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(valid_log_schema))
        
        # Execute
        manager = RalphLifecycleManager(temp_repo)
        with patch.object(manager, '_load_state', return_value=None):
            manager.start(phase=3, estimated_minutes=60)
        
        with patch.object(manager, '_read_log', return_value=valid_log_schema):
            result = manager.check()
        
        # Verify
        assert result["status"] == "completed"
        assert result["progress"] == 100
    
    def test_check_detects_pending(self, temp_repo, valid_log_schema, sample_log_entries):
        """有 PENDING → check() 返回 running"""
        valid_log_schema["entries"] = sample_log_entries
        
        log_path = temp_repo / ".methodology" / "sessions_spawn.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(valid_log_schema))
        
        manager = RalphLifecycleManager(temp_repo)
        with patch.object(manager, '_load_state', return_value=None):
            manager.start(phase=3, estimated_minutes=60)
        
        with patch.object(manager, '_read_log', return_value=valid_log_schema):
            result = manager.check()
        
        assert result["status"] == "running"
        assert result["progress"] < 100
        assert result["pending"] > 0
    
    def test_check_hr13_timeout(self, temp_repo, valid_log_schema):
        """HR-13 超時 → check() 返回 timeout"""
        # Setup: 60 分鐘前啟動的 task
        old_entries = [{
            "timestamp": "2026-04-15T18:00:00",  # 2 小時前
            "fr": "FR-01",
            "status": "COMPLETED"
        }]
        valid_log_schema["entries"] = old_entries
        
        log_path = temp_repo / ".methodology" / "sessions_spawn.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(valid_log_schema))
        
        manager = RalphLifecycleManager(temp_repo)
        
        # Mock 任務在 2 小時前啟動
        mock_state = MagicMock()
        mock_state.created_at = "2026-04-15T18:00:00"  # 2 小時前
        mock_state.metadata = {"estimated_minutes": 30}  # 估計 30 分鐘
        
        with patch.object(manager, '_load_state', return_value=mock_state):
            with patch.object(manager, '_read_log', return_value=valid_log_schema):
                with patch('ralph_mode.lifecycle.datetime') as mock_dt:
                    from datetime import datetime
                    mock_dt.now.return_value = datetime(2026, 4, 15, 20, 0, 0)
                    mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
                    
                    result = manager.check()
        
        # 120 分鐘 > 30 * 3 = 90 分鐘 → 應該超時
        assert result["hr13_triggered"] is True
```

### 4.2 test_lifecycle_integration.py

```python
"""
ralph_mode/tests/integration/test_lifecycle_integration.py

RalphLifecycleManager 和 AlertManager 的整合測試
"""

import pytest
from unittest.mock import patch, MagicMock
from ralph_mode.lifecycle import RalphLifecycleManager
from ralph_mode.alert_manager import AlertManager, AlertLevel


class TestLifecycleIntegration:
    """Lifecycle + Alert 整合測試"""
    
    def test_ralph_alerts_on_verification_failure(self, temp_repo, mock_alert_channels):
        """L2 驗證失敗 → Ralph 發 Alert"""
        manager = RalphLifecycleManager(temp_repo)
        alert_mgr = AlertManager()
        
        # Mock L2 驗證失敗
        verification_result = MagicMock()
        verification_result.passed = False
        verification_result.errors = ["Missing: tests/test_fr03.py"]
        verification_result.fr = "FR-03"
        
        with patch.object(alert_mgr, 'send') as mock_send:
            manager.alert_verification_failed(verification_result, alert_mgr)
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['level'] == AlertLevel.WARNING
            assert "FR-03" in call_args[1]['title']
    
    def test_ralph_stops_and_alerts_on_completion(self, temp_repo, mock_alert_channels):
        """M1: 所有 FR 完成 → Ralph STOP + SUCCESS Alert"""
        manager = RalphLifecycleManager(temp_repo)
        alert_mgr = AlertManager()
        
        with patch.object(manager, '_load_state', return_value=None):
            with patch.object(manager, '_save_state'):
                task_id = manager.start(phase=3, estimated_minutes=60)
        
        with patch.object(manager, '_read_log') as mock_read:
            mock_read.return_value = {
                "entries": [
                    {"fr": "FR-01", "status": "COMPLETED"},
                    {"fr": "FR-02", "status": "COMPLETED"},
                ]
            }
            
            with patch.object(alert_mgr, 'send') as mock_send:
                with patch.object(manager, '_delete_state') as mock_delete:
                    result = manager.handle_completion(alert_mgr)
        
        assert result["status"] == "completed"
        mock_delete.assert_called_once()
        mock_send.assert_called_once()
    
    def test_ralph_alerts_critical_on_hr13_timeout(self, temp_repo, mock_alert_channels):
        """M2: HR-13 超時 → Ralph 發 Alert CRITICAL"""
        manager = RalphLifecycleManager(temp_repo)
        alert_mgr = AlertManager()
        
        with patch.object(manager, '_load_state', return_value=None):
            with patch.object(manager, '_save_state'):
                manager.start(phase=3, estimated_minutes=60)
        
        with patch.object(alert_mgr, 'send') as mock_send:
            manager.alert_hr13_timeout(
                elapsed_minutes=180,
                estimated_minutes=60,
                alert_mgr=alert_mgr
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['level'] == AlertLevel.CRITICAL
            assert "HR-13" in call_args[1]['title']
```

---

## 5. E2E 測試（2 個）

### 5.1 test_ralph_e2e.sh

```bash
#!/bin/bash
# ralph_mode/tests/e2e/test_ralph_e2e.sh
# E2E 測試：Ralph Mode 完整流程

set -e

TEST_DIR="/tmp/ralph_e2e_test_$$"
mkdir -p $TEST_DIR/.methodology

echo "============================================"
echo "E2E Test: Ralph Mode Complete Flow"
echo "============================================"
echo "Test dir: $TEST_DIR"
echo ""

# 初始化 sessions_spawn.log
cat > $TEST_DIR/.methodology/sessions_spawn.log << 'EOF'
{
    "schema_version": "1.0",
    "schema_definition": {
        "required": ["timestamp", "session_id", "fr", "status"],
        "status_values": ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
    },
    "entries": []
}
EOF

echo "[1/5] Initialized sessions_spawn.log with schema v1.0"

# 啟動 Ralph（使用 Python API）
python3 << PYEOF
import sys
sys.path.insert(0, '$TEST_DIR/../../..')

from ralph_mode.lifecycle import RalphLifecycleManager
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)
task_id = manager.start(phase=3, estimated_minutes=1)
print(f"[2/5] Ralph started: {task_id}")
PYEOF

# 寫入第一個 FR COMPLETED
python3 << PYEOF
import json
from pathlib import Path

log_path = Path('$TEST_DIR/.methodology/sessions_spawn.log')
content = json.loads(log_path.read_text())
content['entries'].append({
    "timestamp": "2026-04-15T20:00:00",
    "session_id": "sess-001",
    "fr": "FR-01",
    "status": "COMPLETED"
})
log_path.write_text(json.dumps(content, indent=2))
print("[3/5] Wrote FR-01 COMPLETED")
PYEOF

# 等待 Ralph 檢查（1 分鐘後，但我們 mock 時間）
echo "[4/5] Waiting for Ralph check cycle..."

# 驗證結果
python3 << PYEOF
import json
from pathlib import Path

repo = Path('$TEST_DIR')

# 檢查 Ralph 狀態
from ralph_mode.lifecycle import RalphLifecycleManager
manager = RalphLifecycleManager(repo)

# 讀取 log
log_path = repo / ".methodology" / "sessions_spawn.log"
content = json.loads(log_path.read_text())

print(f"[5/5] Log entries: {len(content['entries'])}")
for entry in content['entries']:
    print(f"  - {entry['fr']}: {entry['status']}")

# 驗證 schema 版本
assert content['schema_version'] == '1.0', f"Schema version mismatch: {content['schema_version']}"
print("[PASS] Schema version correct")

# 驗證有 COMPLETED 項目
completed = [e for e in content['entries'] if e['status'] == 'COMPLETED']
assert len(completed) == 1, f"Expected 1 COMPLETED, got {len(completed)}"
print(f"[PASS] FR-01 is COMPLETED")

print("")
echo "============================================"
echo "E2E Test: PASSED"
echo "============================================"
PYEOF

# 清理
rm -rf $TEST_DIR
echo "Cleaned up: $TEST_DIR"
```

### 5.2 test_ralph_schema_e2e.sh

```bash
#!/bin/bash
# ralph_mode/tests/e2e/test_ralph_schema_e2e.sh
# E2E 測試：Schema 不相容時 Ralph 應該拒絕啟動

set -e

TEST_DIR="/tmp/ralph_schema_test_$$"
mkdir -p $TEST_DIR/.methodology

echo "============================================"
echo "E2E Test: Ralph rejects incompatible schema"
echo "============================================"

# 建立不相容的 schema
cat > $TEST_DIR/.methodology/sessions_spawn.log << 'EOF'
{
    "schema_version": "9.9",
    "entries": []
}
EOF

echo "[1/3] Created sessions_spawn.log with schema v9.9"

# 嘗試啟動 Ralph（應該失敗）
python3 << PYEOF
import sys
sys.path.insert(0, '$TEST_DIR/../../..')

from ralph_mode.lifecycle import RalphLifecycleManager
from ralph_mode.schema_validator import RalphSchemaError
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)

try:
    manager.start(phase=3, estimated_minutes=60)
    print("[FAIL] Ralph should have rejected incompatible schema")
    sys.exit(1)
except RalphSchemaError as e:
    print(f"[2/3] Ralph correctly rejected: {e}")
    assert "Unsupported schema" in str(e)
    print("[PASS] Error message contains 'Unsupported schema'")

# 修復 schema
import json
log_path = repo / ".methodology" / "sessions_spawn.log"
content = json.loads(log_path.read_text())
content['schema_version'] = '1.0'
log_path.write_text(json.dumps(content))
print("[3/3] Fixed schema to v1.0")
PYEOF

# 再次啟動（應該成功）
python3 << PYEOF
import sys
sys.path.insert(0, '$TEST_DIR/../../..')

from ralph_mode.lifecycle import RalphLifecycleManager
from pathlib import Path

repo = Path('$TEST_DIR')
manager = RalphLifecycleManager(repo)
task_id = manager.start(phase=3, estimated_minutes=60)
print(f"[PASS] Ralph started with v1.0: {task_id}")
PYEOF

echo ""
echo "============================================"
echo "Schema E2E Test: PASSED"
echo "============================================"

rm -rf $TEST_DIR
```

---

## 6. 測試執行

### 6.1 執行命令

```bash
# 單元測試
cd skills/methodology-v2
python3 -m pytest ralph_mode/tests/unit/ -v

# 整合測試
python3 -m pytest ralph_mode/tests/integration/ -v

# E2E 測試
bash ralph_mode/tests/e2e/test_ralph_e2e.sh
bash ralph_mode/tests/e2e/test_ralph_schema_e2e.sh

# 全部執行（CI 模式）
python3 -m pytest ralph_mode/tests/ -v --cov=ralph_mode --cov-report=html
```

### 6.2 預期結果

| 測試類別 | 數量 | 通過率目標 |
|---------|------|-----------|
| 單元測試 | 15 | 100% |
| 整合測試 | 7 | 100% |
| E2E 測試 | 2 | 100% |
| **總計** | **24** | **100%** |

### 6.3 覆蓋率目標

| 元件 | 覆蓋率目標 |
|------|-----------|
| SessionsSpawnLogValidator | > 90% |
| OutputVerifier | > 85% |
| TaskOutputParser | > 80% |
| AlertManager | > 85% |
| RalphLifecycleManager | > 80% |

---

## 7. 測試覆蓋矩陣

| 元件 | 單元 | 整合 | E2E | 總計 |
|------|------|------|------|------|
| SessionsSpawnLogValidator | 3 | 1 | 1 | 5 |
| OutputVerifier | 4 | 1 | - | 5 |
| TaskOutputParser | 2 | 1 | - | 3 |
| AlertManager | 3 | 1 | - | 4 |
| RalphLifecycleManager | 3 | 2 | 1 | 6 |
| cmd_run_phase 整合 | - | 1 | 2 | 3 |
| **總計** | **15** | **7** | **4** | **26** |

---

## 8. 驗證檢查清單

### 8.1 功能檢查

| # | 檢查項 | 測試方式 | 標準 |
|---|--------|---------|------|
| 1 | Schema v1.0 被接受 | UT | ✅ |
| 2 | Schema v0.9 被接受（向後相容）| UT | ✅ |
| 3 | Schema v9.9 被拒絕 | UT | ✅ |
| 4 | 缺少 schema_version 被拒絕 | UT | ✅ |
| 5 | L2a: 檔案缺失 → failed | UT | ✅ |
| 6 | L2b: 檔案太小 → failed | UT | ✅ |
| 7 | L2c: 無程式碼 → failed | UT | ✅ |
| 8 | 所有檔案有效 → passed | UT | ✅ |
| 9 | SUCCESS Alert 不發送 | UT | ✅ |
| 10 | WARNING Alert → Telegram | UT | ✅ |
| 11 | CRITICAL Alert → Telegram + 飛書 | UT | ✅ |
| 12 | Ralph 啟動建立 TaskState | UT | ✅ |
| 13 | Ralph 停止清除 TaskState | UT | ✅ |
| 14 | get_running_ralph() 正確返回 | UT | ✅ |
| 15 | check() 偵測所有 FR 完成 | IT | ✅ |
| 16 | check() 偵測有 PENDING | IT | ✅ |
| 17 | check() 偵測 HR-13 超時 | IT | ✅ |
| 18 | L2 驗證失敗 → WARNING Alert | IT | ✅ |
| 19 | M1: 完成 → STOP + SUCCESS | IT | ✅ |
| 20 | M2: 超時 → CRITICAL Alert | IT | ✅ |
| 21 | Schema 不相容 → E2E 失敗 | E2E | ✅ |
| 22 | Schema 修復 → E2E 成功 | E2E | ✅ |

### 8.2 非功能檢查

| # | 檢查項 | 標準 |
|---|--------|------|
| 1 | 單元測試執行時間 | < 10s |
| 2 | 整合測試執行時間 | < 30s |
| 3 | E2E 測試執行時間 | < 60s |
| 4 | 程式碼覆蓋率 | > 80% |

---

## 9. CI/CD 整合

### 9.1 GitHub Actions（範例）

```yaml
# .github/workflows/ralph_mode_test.yml
name: Ralph Mode Tests

on:
  push:
    paths:
      - 'ralph_mode/**'
  pull_request:
    paths:
      - 'ralph_mode/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: |
          python3 -m pytest ralph_mode/tests/unit/ -v --cov=ralph_mode
      
      - name: Run integration tests
        run: |
          python3 -m pytest ralph_mode/tests/integration/ -v
      
      - name: Run E2E tests
        run: |
          bash ralph_mode/tests/e2e/test_ralph_e2e.sh
          bash ralph_mode/tests/e2e/test_ralph_schema_e2e.sh
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./coverage
```

---

## 10. 疑難排解

### 10.1 常見問題

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| ImportError: No module named 'ralph_mode' | 路徑問題 | `sys.path.insert(0, ...)` |
| AssertionError: mock not called | 非預期執行 | 檢查 mock 參數 |
| FileNotFoundError | temp_repo 未 cleanup | 使用 fixture 而非手動 cleanup |
| Schema validation failed | schema 版本問題 | 確保測試使用 v1.0 |

### 10.2 Debug 技巧

```python
# 加入 verbose logging
@pytest.fixture
def debug_log():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield

# 使用 --pdb 停在錯誤處
python3 -m pytest tests/ -v --pdb

# 只執行特定測試
python3 -m pytest tests/unit/test_schema_validator.py::TestSessionsSpawnLogValidator::test_valid_schema_v1 -v
```
