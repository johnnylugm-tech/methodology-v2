"""Tests for SPEC.md parser (parser.py)."""

import pytest
from pathlib import Path

from gap_detector.parser import (
    SpecParser,
    ParsedSpec,
    FeatureItem,
    SpecParseError,
)


class TestSpecParserInit:
    """Tests for SpecParser initialization."""

    def test_init_with_valid_path(self, sample_spec_file: Path):
        """Test initialization with a valid SPEC.md path."""
        parser = SpecParser(str(sample_spec_file))
        assert parser.spec_path == str(sample_spec_file)

    def test_init_with_pathlib_path(self, sample_spec_file: Path):
        """Test initialization with a pathlib.Path object."""
        parser = SpecParser(sample_spec_file)
        assert parser.spec_path == str(sample_spec_file)

    def test_init_nonexistent_file_raises(self, temp_dir: Path):
        """Test that initialization with non-existent file raises error."""
        nonexistent = temp_dir / "nonexistent.md"
        with pytest.raises(SpecParseError) as exc_info:
            SpecParser(str(nonexistent))
        assert exc_info.value.code == "E_FILE_NOT_FOUND"

    def test_init_non_markdown_file_raises(self, temp_dir: Path):
        """Test that non-markdown file raises appropriate error."""
        txt_file = temp_dir / "file.txt"
        txt_file.write_text("Just a text file", encoding="utf-8")
        with pytest.raises(SpecParseError) as exc_info:
            SpecParser(str(txt_file))
        assert exc_info.value.code == "E_NOT_MARKDOWN"


class TestSpecParserParse:
    """Tests for SpecParser.parse() method."""

    def test_parse_valid_spec(self, sample_spec_file: Path):
        """Test parsing a valid SPEC.md file."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        assert isinstance(result, ParsedSpec)
        assert len(result.feature_items) == 5
        assert result.parse_stats.total_lines > 0

    def test_parse_empty_spec(self, temp_dir: Path, empty_spec_content: str):
        """Test parsing an empty SPEC.md file."""
        spec_file = temp_dir / "empty.md"
        spec_file.write_text(empty_spec_content, encoding="utf-8")
        parser = SpecParser(str(spec_file))
        result = parser.parse()
        assert len(result.feature_items) == 0

    def test_parse_extracts_feature_ids(self, sample_spec_file: Path):
        """Test that feature IDs are correctly extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        feature_ids = [f.id for f in result.feature_items]
        assert "F1" in feature_ids
        assert "F2" in feature_ids
        assert "F3" in feature_ids
        assert "F4" in feature_ids
        assert "F5" in feature_ids

    def test_parse_extracts_feature_names(self, sample_spec_file: Path):
        """Test that feature names are correctly extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        name_map = {f.id: f.name for f in result.feature_items}
        assert "SPEC 解析器" in name_map["F1"]
        assert "代碼掃描器" in name_map["F2"]
        assert "Gap 檢測器" in name_map["F3"]

    def test_parse_extracts_priorities(self, sample_spec_file: Path):
        """Test that priorities are correctly extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        priority_map = {f.id: f.priority for f in result.feature_items}
        assert priority_map["F1"] == "P0"
        assert priority_map["F2"] == "P0"
        assert priority_map["F3"] == "P0"
        assert priority_map["F4"] == "P1"
        assert priority_map["F5"] == "P2"

    def test_parse_extracts_dependencies(self, sample_spec_file: Path):
        """Test that dependencies are correctly extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        dep_map = {f.id: f.depends_on for f in result.feature_items}
        assert "F3" in dep_map["F1"]
        assert "F3" in dep_map["F2"]
        assert dep_map["F3"] == []
        assert "F1" in dep_map["F4"]
        assert "F2" in dep_map["F4"]

    def test_parse_extracts_acceptance_criteria(self, sample_spec_file: Path):
        """Test that acceptance criteria are correctly extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        criteria_map = {f.id: f.acceptance_criteria for f in result.feature_items}
        assert len(criteria_map["F1"]) > 0
        assert any("95%" in c for c in criteria_map["F1"])

    def test_parse_extracts_descriptions(self, sample_spec_file: Path):
        """Test that feature descriptions are extracted."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        desc_map = {f.id: f.description for f in result.feature_items}
        assert "Markdown" in desc_map["F1"]
        assert "AST" in desc_map["F2"]

    def test_parse_preserves_line_numbers(self, sample_spec_file: Path):
        """Test that line numbers are correctly preserved."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        for feature in result.feature_items:
            assert feature.line_number > 0

    def test_parse_calculates_success_rate(self, sample_spec_file: Path):
        """Test that parse success rate is calculated."""
        parser = SpecParser(str(sample_spec_file))
        result = parser.parse()
        assert 0.0 <= result.parse_stats.parse_success_rate <= 1.0

    def test_parse_complex_spec(self, temp_dir: Path, complex_spec_content: str):
        """Test parsing a complex SPEC.md with edge cases."""
        spec_file = temp_dir / "complex.md"
        spec_file.write_text(complex_spec_content, encoding="utf-8")
        parser = SpecParser(str(spec_file))
        result = parser.parse()
        assert len(result.feature_items) == 4
        feature_ids = [f.id for f in result.feature_items]
        assert "F1" in feature_ids
        assert "F2" in feature_ids
        assert "F3" in feature_ids
        assert "F4" in feature_ids

    def test_parse_continues_after_errors(self, temp_dir: Path):
        """Test that parsing continues after non-critical errors."""
        content = """# Feature #1: Test

### F1: Valid Feature
**描述：** Valid feature
**優先權：** P0

### F2: Invalid @#$ Feature
**描述：** Invalid header
**優先權：** P1

### F3: Another Valid Feature
**描述：** Another valid feature
**優先權：** P0
"""
        spec_file = temp_dir / "partial.md"
        spec_file.write_text(content, encoding="utf-8")
        parser = SpecParser(str(spec_file))
        result = parser.parse()
        assert len(result.feature_items) >= 2

    def test_parse_normalizes_line_endings(self, temp_dir: Path):
        """Test that CRLF line endings are handled correctly."""
        content = "### F1: Test\r\n**描述：** Test\r\n**優先權：** P0\r\n"
        spec_file = temp_dir / "crlf.md"
        spec_file.write_bytes(content.encode("utf-8"))
        parser = SpecParser(str(spec_file))
        result = parser.parse()
        assert len(result.feature_items) >= 1

    def test_get_error_log(self, temp_dir: Path):
        """Test that error log is accessible after parsing."""
        content = """### F1: Test
**描述：** Test description
**優先權：** P0
"""
        spec_file = temp_dir / "test.md"
        spec_file.write_text(content, encoding="utf-8")
        parser = SpecParser(str(spec_file))
        parser.parse()
        errors = parser.get_error_log()
        assert isinstance(errors, list)

    def test_parse_with_chinese_characters(self, temp_dir: Path):
        """Test parsing SPEC.md with Chinese characters."""
        content = """# Feature #1: 中文測試

### F1: 中文功能名稱
**描述：** 這是一個中文描述
**驗收標準：** 標準1; 標準2
**優先權：** P0
**依賴：** F1
"""
        spec_file = temp_dir / "chinese.md"
        spec_file.write_text(content, encoding="utf-8")
        parser = SpecParser(str(spec_file))
        result = parser.parse()
        assert len(result.feature_items) == 1
        assert "中文" in result.feature_items[0].name
