"""Python Code Scanner Module.

Scans Python source code using the AST (Abstract Syntax Tree) to extract:
- Module information
- Class definitions
- Function definitions
- Method definitions
- Docstrings
- Parameters
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class ScanError(Exception):
    """Exception raised when code scanning fails.

    Attributes:
        code: Error code string (E_FILE_NOT_FOUND, E_SCAN_FAILED)
        message: Human-readable error message
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class ScanErrorRecord:
    """Record of a scanning error.

    Attributes:
        file_path: Path to file with error
        error_type: Type of error
        details: Additional error details
    """

    file_path: str
    error_type: str
    details: str


@dataclass
class CodeItem:
    """Represents a single code item (class, function, or method).

    Attributes:
        id: Unique identifier (module.name)
        kind: Type of item ("class", "function", "method")
        name: Item name
        module: Module name
        file_path: File path
        line_number: Line number in file
        docstring: First line of docstring
        params: List of parameter names
        is_public: Whether item is public (not starting with _)
        decorators: List of decorator names
    """

    id: str
    kind: str
    name: str
    module: str
    file_path: str
    line_number: int
    docstring: str = ""
    params: list[str] = field(default_factory=list)
    is_public: bool = True
    decorators: list[str] = field(default_factory=list)


@dataclass
class CodeFile:
    """Represents a scanned Python module/file.

    Attributes:
        module_name: Name of the module
        file_path: Full path to the file
        items: List of code items in this file
        line_count: Total number of lines
    """

    module_name: str
    file_path: str
    items: list[CodeItem] = field(default_factory=list)
    line_count: int = 0


@dataclass
class ScanStats:
    """Statistics from scanning operation.

    Attributes:
        total_files: Total number of .py files found
        scanned_files: Number of files successfully scanned
        skipped_files: Number of files skipped (errors)
        total_items: Total number of code items found
        scan_coverage_rate: Coverage rate as a float
        errors: List of scanning errors
    """

    total_files: int = 0
    scanned_files: int = 0
    skipped_files: int = 0
    total_items: int = 0
    scan_coverage_rate: float = 1.0
    errors: list[ScanErrorRecord] = field(default_factory=list)


@dataclass
class ScannedCode:
    """Result of scanning implement/ directory.

    Attributes:
        modules: List of scanned module files
        scan_stats: Scanning statistics
    """

    modules: list[CodeFile]
    scan_stats: ScanStats = field(default_factory=ScanStats)


class _ASTVisitor(ast.NodeVisitor):
    """AST visitor for extracting code items.

    Attributes:
        file_path: Path to the source file
        module_name: Name of the module
        items: List of extracted code items
        in_class: Whether currently visiting inside a class
        current_class: Name of current class (if inside)
    """

    def __init__(self, file_path: str, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.items: list[CodeItem] = []
        self.in_class = False
        self.current_class = ""

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit a class definition node.

        Args:
            node: AST ClassDef node
        """
        self.in_class = True
        self.current_class = node.name

        docstring = ast.get_docstring(node) or ""
        first_doc_line = docstring.split("\n")[0].strip() if docstring else ""

        decorators = [d.attr if hasattr(d, "attr") else self._get_decorator_name(d)
                      for d in node.decorator_list]

        is_public = not node.name.startswith("_")

        code_item = CodeItem(
            id=f"{self.module_name}.{node.name}",
            kind="class",
            name=node.name,
            module=self.module_name,
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=first_doc_line,
            is_public=is_public,
            decorators=decorators
        )
        self.items.append(code_item)

        self.generic_visit(node)
        self.in_class = False
        self.current_class = ""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node.

        Args:
            node: AST FunctionDef node
        """
        self._visit_function(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an async function definition node.

        Args:
            node: AST AsyncFunctionDef node
        """
        self._visit_function(node, "function")

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef,
                        kind: str) -> None:
        """Visit a function definition node.

        Args:
            node: AST FunctionDef or AsyncFunctionDef node
            kind: Kind string ("function" or "method")
        """
        docstring = ast.get_docstring(node) or ""
        first_doc_line = docstring.split("\n")[0].strip() if docstring else ""

        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        params = [arg.arg for arg in node.args.args]
        is_public = not node.name.startswith("_")

        actual_kind = "method" if self.in_class else kind

        if self.in_class:
            item_id = f"{self.module_name}.{self.current_class}.{node.name}"
        else:
            item_id = f"{self.module_name}.{node.name}"

        code_item = CodeItem(
            id=item_id,
            kind=actual_kind,
            name=node.name,
            module=self.module_name,
            file_path=self.file_path,
            line_number=node.lineno,
            docstring=first_doc_line,
            params=params,
            is_public=is_public,
            decorators=decorators
        )
        self.items.append(code_item)

        self.generic_visit(node)

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extract decorator name from AST node.

        Args:
            node: AST decorator expression

        Returns:
            str: Decorator name
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"


class CodeScanner:
    """Scanner for Python implement/ directories.

    Uses Python AST to extract structured information about
    classes, functions, and methods.

    Attributes:
        implement_dir: Path to the implement/ directory
        _errors: Internal list of scanning errors
    """

    def __init__(self, implement_dir: str | Path) -> None:
        """Initialize the scanner with an implement/ directory path.

        Args:
            implement_dir: Path to the implement/ directory

        Raises:
            ScanError: If directory doesn't exist
        """
        self.implement_dir = str(implement_dir)
        self._errors: list[ScanErrorRecord] = []

        if not Path(self.implement_dir).exists():
            raise ScanError(
                code="E_FILE_NOT_FOUND",
                message=f"Implement directory not found: {self.implement_dir}"
            )

        if not Path(self.implement_dir).is_dir():
            raise ScanError(
                code="E_FILE_NOT_FOUND",
                message=f"Path is not a directory: {self.implement_dir}"
            )

    def scan(self) -> ScannedCode:
        """Scan the implement/ directory.

        Returns:
            ScannedCode: Structured representation of the code

        Raises:
            ScanError: If critical scanning error occurs
        """
        self._errors = []
        modules: list[CodeFile] = []

        files = self._discover_files()
        total_files = len(files)
        scanned_files = 0
        skipped_files = 0
        total_items = 0

        for file_path in files:
            try:
                code_file = self._scan_file(file_path)
                if code_file:
                    modules.append(code_file)
                    scanned_files += 1
                    total_items += len(code_file.items)
            except Exception as e:
                skipped_files += 1
                self._errors.append(ScanErrorRecord(
                    file_path=str(file_path),
                    error_type=type(e).__name__,
                    details=str(e)
                ))

        coverage_rate = (scanned_files / total_files) if total_files > 0 else 1.0

        scan_stats = ScanStats(
            total_files=total_files,
            scanned_files=scanned_files,
            skipped_files=skipped_files,
            total_items=total_items,
            scan_coverage_rate=coverage_rate,
            errors=self._errors.copy()
        )

        return ScannedCode(modules=modules, scan_stats=scan_stats)

    def get_scan_error_log(self) -> list[ScanErrorRecord]:
        """Get the list of errors encountered during scanning.

        Returns:
            list[ScanErrorRecord]: Copy of the error log
        """
        return self._errors.copy()

    def _discover_files(self) -> list[Path]:
        """Discover all Python files in implement/ directory.

        Excludes:
        - __pycache__ directories
        - .pyc files
        - test_*.py files
        - conftest.py files

        Returns:
            list[Path]: List of discovered .py file paths
        """
        files: list[Path] = []
        implement_path = Path(self.implement_dir)

        for root, dirs, filenames in os.walk(implement_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            root_path = Path(root)
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                if filename.startswith("test_"):
                    continue
                if filename == "conftest.py":
                    continue
                if filename.startswith("_") and filename != "__init__.py":
                    # Skip private modules except __init__.py
                    continue

                files.append(root_path / filename)

        return sorted(files)

    def _scan_file(self, file_path: Path) -> Optional[CodeFile]:
        """Scan a single Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Optional[CodeFile]: Scanned code file or None if skipped
        """
        module_name = self._get_module_name(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            raise ScanError(
                code="E_SCAN_FAILED",
                message=f"Syntax error in {file_path}: {e}"
            )

        visitor = _ASTVisitor(str(file_path), module_name)
        visitor.visit(tree)

        # Filter out __init__.py class items (module level only)
        items = visitor.items
        if file_path.name == "__init__.py":
            # For __init__.py, only keep module-level items (not nested classes)
            # but actually in __init__.py we want to report classes too for completeness
            pass

        line_count = len(content.split("\n"))

        return CodeFile(
            module_name=module_name,
            file_path=str(file_path),
            items=items,
            line_count=line_count
        )

    def _get_module_name(self, file_path: Path) -> str:
        """Derive module name from file path.

        Args:
            file_path: Path to the Python file

        Returns:
            str: Module name
        """
        try:
            rel_path = file_path.relative_to(Path(self.implement_dir))
        except ValueError:
            rel_path = file_path

        parts = list(rel_path.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        elif parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]

        return ".".join(parts) if parts else "root"
