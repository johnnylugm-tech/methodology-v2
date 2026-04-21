"""Pytest configuration and shared fixtures for Gap Detector tests."""

import tempfile
import shutil
from pathlib import Path
from typing import Generator

import sys
from pathlib import Path

# Add 03-implement to path so tests can import "from gap_detector.xxx"
sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory that is cleaned up after the test."""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def sample_spec_content() -> str:
    """Return a sample SPEC.md content for testing."""
    return """# Feature #8: Gap Detection Agent

**版本：** 1.0
**創建日期：** 2026-04-20

---

## 功能列表

### F1: SPEC 解析器
**描述：** 解析 Markdown 格式的 SPEC.md
**驗收標準：** 解析成功率 > 95%
**優先權：** P0
**依賴：** F3

### F2: 代碼掃描器
**描述：** 使用 AST 掃描 implement/ 目錄
**驗收標準：** 掃描覆蓋率 = 100%
**優先權：** P0
**依賴：** F3

### F3: Gap 檢測器
**描述：** 對比 SPEC 與代碼，識別 gap
**驗收標準：** Gap 檢測準確率 > 90%
**優先權：** P0

### F4: 報告生成器
**描述：** 生成 gap 報告
**驗收標準：** JSON + Markdown 輸出
**優先權：** P1
**依賴：** F1, F2

### F5: 邊界條件處理
**描述：** 處理錯誤情況
**驗收標準：** 錯誤日誌生成
**優先權：** P2
"""


@pytest.fixture
def sample_spec_file(temp_dir: Path, sample_spec_content: str) -> Path:
    """Create a temporary SPEC.md file with sample content."""
    spec_file = temp_dir / "SPEC.md"
    spec_file.write_text(sample_spec_content, encoding="utf-8")
    return spec_file


@pytest.fixture
def sample_implement_content() -> str:
    """Return sample Python implementation content."""
    return '''"""Sample implementation module."""

class SpecParser:
    """Parser for SPEC.md files."""

    def __init__(self, spec_path: str) -> None:
        self.spec_path = spec_path

    def parse(self):
        """Parse the SPEC.md file."""
        pass


def scan_directory(directory: str):
    """Scan a directory for Python files."""
    pass


class CodeScanner:
    """Scanner for Python code."""

    def __init__(self, implement_dir: str) -> None:
        self.implement_dir = implement_dir

    def scan(self):
        """Scan the implement directory."""
        pass
'''


@pytest.fixture
def sample_implement_dir(temp_dir: Path, sample_implement_content: str) -> Path:
    """Create a temporary implement directory with sample Python files."""
    impl_dir = temp_dir / "implement"
    impl_dir.mkdir()
    (impl_dir / "__init__.py").write_text("", encoding="utf-8")
    (impl_dir / "parser_module.py").write_text(sample_implement_content, encoding="utf-8")
    return impl_dir


@pytest.fixture
def complex_spec_content() -> str:
    """Return a more complex SPEC.md for edge case testing."""
    return """# Feature #99: Complex Test Feature

## Overview
This is a complex feature with many edge cases.

### F1: Feature With Dependencies
**描述：** Feature with P0 priority
**驗收標準：** Criterion 1; Criterion 2
**優先權：** P0
**依賴：** F2, F3

### F2: Another Feature
**描述：** Another feature description

### F3: Third Feature
**描述：** Third feature description
**優先權：** P1
**依賴：** F2

### F4: Orphan Feature
**描述：** This feature has no code counterpart
**優先權：** P2
"""


@pytest.fixture
def complex_implement_content() -> str:
    """Return complex Python implementation for edge case testing."""
    return '''"""Complex implementation module."""

class FeatureWithDependencies:
    """Feature with dependencies."""

    def execute(self, param1: str, param2: int):
        """Execute the feature with params."""
        pass


class AnotherFeature:
    """Another feature class."""

    def process(self):
        """Process something."""
        pass


# This is orphaned - no corresponding spec
class UnmatchedClass:
    """This class has no spec counterpart."""
    pass


def orphaned_function():
    """This function has no spec counterpart."""
    pass
'''


@pytest.fixture
def empty_spec_content() -> str:
    """Return an empty SPEC.md content."""
    return """# Empty Spec

No features here.
"""


@pytest.fixture
def syntax_error_python_content() -> str:
    """Return Python code with syntax errors."""
    return '''
class BrokenClass:
    def broken_method(self
        # Missing closing parenthesis and colon
        pass

def broken_function:
    # Missing parentheses
    pass
'''


@pytest.fixture
def multi_module_implement(temp_dir: Path) -> Path:
    """Create a multi-module implement directory structure."""
    impl_dir = temp_dir / "implement"
    impl_dir.mkdir()

    # Module 1
    (impl_dir / "__init__.py").write_text(
        '"""Implement package."""\n__all__ = ["module1", "module2"]\n',
        encoding="utf-8"
    )
    (impl_dir / "module1.py").write_text(
        '''"""Module 1."""\n\nclass Class1:\n    """Class 1."""\n    \n    def method1(self):\n        """Method 1."""\n        pass\n\ndef function1():\n    """Function 1."""\n    pass\n''',
        encoding="utf-8"
    )

    # Module 2
    (impl_dir / "module2.py").write_text(
        '''"""Module 2."""\n\nclass Class2:\n    """Class 2."""\n    \n    def method2(self):\n        """Method 2."""\n        pass\n\ndef function2():\n    """Function 2."""\n    pass\n''',
        encoding="utf-8"
    )

    # Private module (should be excluded from ORPHANED)
    (impl_dir / "_private.py").write_text(
        '''"""Private module."""\n\nclass _PrivateClass:\n    """Private class."""\n    \n    def _private_method(self):\n        """Private method."""\n        pass\n''',
        encoding="utf-8"
    )

    # __all__ test
    (impl_dir / "exports.py").write_text(
        '''"""Exports module."""\n\n__all__ = ["PublicClass", "public_function"]\n\nclass PublicClass:\n    """Public class."""\n    pass\n\nclass PrivateClass:\n    """Private class (not exported)."""  \n    pass\n\ndef public_function():\n    """Public function."""\n    pass\n\ndef _private_function():\n    """Private function (not exported)."""  \n    pass\n''',
        encoding="utf-8"
    )

    return impl_dir
