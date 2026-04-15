"""
Ralph Mode - SessionsSpawnLogValidator Tests
"""

import pytest
import json
import tempfile
from pathlib import Path
from ralph_mode.schema_validator import (
    SessionsSpawnLogValidator,
    ValidationResult,
    RalphSchemaError
)


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
    
    def test_parse_entry_valid(self, valid_log_schema):
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
    
    def test_create_empty_log(self):
        """create_empty_log() 應該產生正確結構"""
        validator = SessionsSpawnLogValidator()
        log = validator.create_empty_log()
        assert log["schema_version"] == "1.0"
        assert "schema_definition" in log
        assert log["entries"] == []
    
    def test_init_log_file_new(self, temp_repo):
        """init_log_file() 應該建立新檔案"""
        validator = SessionsSpawnLogValidator()
        log_path = temp_repo / ".methodology" / "sessions_spawn.log"
        
        created = validator.init_log_file(log_path)
        assert created is True
        assert log_path.exists()
    
    def test_init_log_file_exists(self, temp_repo, valid_log_schema):
        """init_log_file() 如果檔案已存在應該回傳 False"""
        validator = SessionsSpawnLogValidator()
        log_path = temp_repo / ".methodology" / "sessions_spawn.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(valid_log_schema))
        
        created = validator.init_log_file(log_path)
        assert created is False
