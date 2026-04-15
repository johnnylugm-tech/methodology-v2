"""
Ralph Mode Tests - pytest configuration and fixtures
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
