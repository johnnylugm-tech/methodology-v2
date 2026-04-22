"""Tests for Python code scanner (scanner.py)."""

import pytest
from pathlib import Path

from gap_detector.scanner import (
    CodeScanner,
    ScannedCode,
    CodeFile,
    ScanError,
)


class TestCodeScannerInit:
    """Tests for CodeScanner initialization."""

    def test_init_with_valid_path(self, sample_implement_dir: Path):
        """Test initialization with a valid implement directory path."""
        scanner = CodeScanner(str(sample_implement_dir))
        assert scanner.implement_dir == str(sample_implement_dir)

    def test_init_with_pathlib_path(self, sample_implement_dir: Path):
        """Test initialization with a pathlib.Path object."""
        scanner = CodeScanner(sample_implement_dir)
        assert scanner.implement_dir == str(sample_implement_dir)

    def test_init_nonexistent_dir_raises(self, temp_dir: Path):
        """Test that initialization with non-existent directory raises error."""
        nonexistent = temp_dir / "nonexistent"
        with pytest.raises(ScanError) as exc_info:
            CodeScanner(str(nonexistent))
        assert exc_info.value.code == "E_FILE_NOT_FOUND"


class TestCodeScannerScan:
    """Tests for CodeScanner.scan() method."""

    def test_scan_finds_python_files(self, sample_implement_dir: Path):
        """Test that scan finds all .py files."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        assert isinstance(result, ScannedCode)
        assert result.scan_stats.total_files >= 2

    def test_scan_returns_modules(self, sample_implement_dir: Path):
        """Test that scan returns module information."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        assert len(result.modules) >= 1
        for module in result.modules:
            assert isinstance(module, CodeFile)

    def test_scan_extracts_classes(self, sample_implement_dir: Path):
        """Test that class definitions are extracted."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]
        class_items = [i for i in all_items if i.kind == "class"]
        assert len(class_items) >= 2
        class_names = [i.name for i in class_items]
        assert "SpecParser" in class_names
        assert "CodeScanner" in class_names

    def test_scan_extracts_functions(self, sample_implement_dir: Path):
        """Test that function definitions are extracted."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]
        function_items = [i for i in all_items if i.kind == "function"]
        assert len(function_items) >= 1
        function_names = [i.name for i in function_items]
        assert "scan_directory" in function_names

    def test_scan_extracts_methods(self, sample_implement_dir: Path):
        """Test that class methods are extracted."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]
        method_items = [i for i in all_items if i.kind == "method"]
        assert len(method_items) >= 2
        method_names = [i.name for i in method_items]
        assert "parse" in method_names
        assert "scan" in method_names

    def test_scan_extracts_module_name(self, sample_implement_dir: Path):
        """Test that module names are correctly extracted."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        module_names = [m.module_name for m in result.modules]
        assert "parser_module" in module_names

    def test_scan_calculates_coverage_rate(self, sample_implement_dir: Path):
        """Test that scan coverage rate is calculated."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        assert 0.0 <= result.scan_stats.scan_coverage_rate <= 1.0
        assert result.scan_stats.scan_coverage_rate == 1.0

    def test_scan_reports_total_files(self, sample_implement_dir: Path):
        """Test that total file count is reported."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        assert result.scan_stats.total_files >= 2

    def test_scan_reports_scanned_files(self, sample_implement_dir: Path):
        """Test that scanned file count is reported."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        assert result.scan_stats.scanned_files >= 2

    def test_scan_skips_pycache(self, temp_dir: Path):
        """Test that __pycache__ directories are skipped."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "module.py").write_text("def func(): pass", encoding="utf-8")

        pycache_dir = impl_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "module.cpython-310.pyc").write_bytes(b"fake bytecode")

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        scanned_names = [m.module_name for m in result.modules]
        assert "__pycache__" not in str(scanned_names)

    def test_scan_handles_syntax_error_gracefully(
        self, temp_dir: Path, syntax_error_python_content: str
    ):
        """Test that files with syntax errors are skipped gracefully."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "broken.py").write_text(syntax_error_python_content, encoding="utf-8")
        (impl_dir / "valid.py").write_text("def valid(): pass", encoding="utf-8")

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        assert result.scan_stats.skipped_files >= 1
        assert len(result.scan_stats.errors) >= 1

    def test_scan_empty_directory(self, temp_dir: Path):
        """Test scanning an empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        scanner = CodeScanner(str(empty_dir))
        result = scanner.scan()
        assert len(result.modules) == 0

    def test_scan_public_items_marked_correctly(self, temp_dir: Path):
        """Test that public items are correctly identified."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "public_test.py").write_text(
            '''"""Test module."""\n\nclass PublicClass:\n    """Public class."""\n    pass\n\nclass _PrivateClass:\n    """Private class."""\n    pass\n\ndef public_function():\n    """Public function."""\n    pass\n\ndef _private_function():\n    """Private function."""\n    pass\n''',
            encoding="utf-8"
        )

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]

        public_items = [i for i in all_items if i.is_public]
        private_items = [i for i in all_items if not i.is_public]

        assert len(public_items) >= 2
        assert len(private_items) >= 2

        public_names = [i.name for i in public_items]
        private_names = [i.name for i in private_items]

        assert "PublicClass" in public_names
        assert "_PrivateClass" in private_names
        assert "public_function" in public_names
        assert "_private_function" in private_names

    def test_scan_extracts_params(self, temp_dir: Path):
        """Test that function/method parameters are extracted."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "params.py").write_text(
            '''"""Test module."""\n\ndef func_with_params(a: int, b: str, c: float = 1.0):\n    """Function with parameters."""\n    pass\n\nclass ClassWithMethods:\n    def method_with_params(self, x: str, y: int = 0) -> bool:\n        """Method with parameters."""\n        pass\n''',
            encoding="utf-8"
        )

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]

        func = next(i for i in all_items if i.name == "func_with_params")
        assert len(func.params) >= 3
        assert "a" in func.params
        assert "b" in func.params

        method = next(i for i in all_items if i.name == "method_with_params")
        assert len(method.params) >= 2

    def test_scan_extracts_docstrings(self, temp_dir: Path):
        """Test that docstrings are extracted."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "docs.py").write_text(
            '''"""Test module."""\n\nclass DocstringClass:\n    """This is a class docstring."""\n    \n    def method_doc(self):\n        """This is a method docstring."""\n        pass\n\ndef function_doc():\n    """This is a function docstring."""\n    pass\n''',
            encoding="utf-8"
        )

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]

        class_item = next(i for i in all_items if i.kind == "class" and i.name == "DocstringClass")
        assert class_item.docstring == "This is a class docstring."

        func_item = next(i for i in all_items if i.kind == "function" and i.name == "function_doc")
        assert "function docstring" in func_item.docstring

    def test_scan_multi_module_structure(self, multi_module_implement: Path):
        """Test scanning a multi-module directory structure."""
        scanner = CodeScanner(str(multi_module_implement))
        result = scanner.scan()

        assert len(result.modules) >= 4
        module_names = [m.module_name for m in result.modules]
        assert "module1" in module_names
        assert "module2" in module_names

        all_items = [item for module in result.modules for item in module.items]
        assert len(all_items) >= 6

    def test_scan_ignores_test_files(self, temp_dir: Path):
        """Test that test files (test_*.py, conftest.py) are ignored."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "real_module.py").write_text("class RealClass: pass", encoding="utf-8")
        (impl_dir / "test_real_module.py").write_text("class TestClass: pass", encoding="utf-8")
        (impl_dir / "conftest.py").write_text("", encoding="utf-8")

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()

        module_names = [m.module_name for m in result.modules]
        assert "real_module" in module_names
        assert "test_real_module" not in module_names
        assert "conftest" not in module_names

    def test_scan_handles_empty_init(self, temp_dir: Path):
        """Test that __init__.py is handled properly."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()
        assert len(result.modules) >= 1

    def test_scan_extracts_line_numbers(self, temp_dir: Path):
        """Test that line numbers are correctly extracted."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "lines.py").write_text(
            '''"""Test module."""\n\n\nclass LineClass:\n    """Class on line 4."""\n    pass\n\n\ndef LineFunction():\n    """Function on line 9."""\n    pass\n''',
            encoding="utf-8"
        )

        scanner = CodeScanner(str(impl_dir))
        result = scanner.scan()

        lines_module = next(m for m in result.modules if m.module_name == "lines")
        class_item = next(i for i in lines_module.items if i.kind == "class")
        assert class_item.line_number == 4

        func_item = next(i for i in lines_module.items if i.kind == "function")
        assert func_item.line_number == 9

    def test_get_scan_error_log(self, temp_dir: Path, syntax_error_python_content: str):
        """Test that scan error log is accessible."""
        impl_dir = temp_dir / "implement"
        impl_dir.mkdir()
        (impl_dir / "__init__.py").write_text("", encoding="utf-8")
        (impl_dir / "broken.py").write_text(syntax_error_python_content, encoding="utf-8")

        scanner = CodeScanner(str(impl_dir))
        scanner.scan()
        errors = scanner.get_scan_error_log()
        assert isinstance(errors, list)
        assert len(errors) >= 1

    def test_scan_code_items_have_unique_ids(self, sample_implement_dir: Path):
        """Test that all code items have unique IDs."""
        scanner = CodeScanner(str(sample_implement_dir))
        result = scanner.scan()
        all_items = [item for module in result.modules for item in module.items]
        ids = [item.id for item in all_items]
        assert len(ids) == len(set(ids))
