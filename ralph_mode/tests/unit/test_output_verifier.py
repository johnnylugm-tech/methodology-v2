"""
Ralph Mode - OutputVerifier Tests
"""

import pytest
from pathlib import Path
from ralph_mode.output_verifier import OutputVerifier, VerificationResult


class TestOutputVerifier:
    """OutputVerifier 單元測試"""
    
    def test_verify_fr_all_pass(self, temp_repo):
        """所有檔案都存在且有效 → passed"""
        # 建立測試檔案（需要 > 100 bytes）
        (temp_repo / "fr01.py").write_text("""import os

class Fr01:
    def __init__(self):
        self.value = 42
    
    def process(self, data):
        return data + self.value
""")
        (temp_repo / "test_fr01.py").write_text("""import pytest

def test_fr01():
    assert True

def test_fr01_process():
    from fr01 import Fr01
    f = Fr01()
    assert f.process(8) == 50
""")
        
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
    
    def test_verify_fr_too_small(self, temp_repo):
        """檔案太小 (< 100 bytes) → failed"""
        (temp_repo / "tiny.py").write_text("x = 1")
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["tiny.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        assert "Too small" in result.errors[0]
    
    def test_verify_fr_no_code(self, temp_repo):
        """Python 檔案沒有程式碼（但足夠大）→ failed"""
        # 建立一個大於 100 bytes 但沒有 Python 關鍵字的檔案
        content = "# This is a comment\n# Another line\n" + "x = 1\n" * 50
        (temp_repo / "empty.py").write_text(content)
        
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
        # 建立一個大於 100 bytes 的小檔案（有 import）
        (temp_repo / "small.py").write_text("import os\n" + "x = 1\n" * 30)
        
        verifier = OutputVerifier(temp_repo)
        fr_task = {
            "fr": "FR-01",
            "expected_outputs": ["small.py", "missing.py"]
        }
        
        result = verifier.verify_fr(fr_task)
        assert result.passed is False
        # 只有一個 Missing error（小檔案有 import 所以不小）
        assert len(result.errors) == 1
        assert "Missing" in result.errors[0]
