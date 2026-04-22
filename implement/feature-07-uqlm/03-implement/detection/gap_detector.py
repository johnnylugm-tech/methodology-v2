# detection/gap_detector.py
"""FR-U-5: Implementation Gap Detection.

This module implements AST-based implementation gap detection to identify
common code quality issues that can bypass automated quality checks.

Purpose:
    Detect implementation problems that indicate:
    - BASE64_VS_AES: Mixed cryptographic usage
    - TEST_TODO_FLOOD: Spammed test.todo() assertions
    - EMPTY_CATCH: Empty exception handlers
    - HARDCODED_SECRETS: Hardcoded credentials

Algorithm:
    1. Parse source code with ast
    2. Run specialized detectors for each gap type
    3. Return findings with location and severity

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional

from detection.data_models import (
    GapFinding,
    GapSeverity,
    GapSummary,
    GapType,
)
from detection.exceptions import GapDetectionError


# =============================================================================
# Section 1: Gap Rule Definitions
# =============================================================================


class GapRule:
    """Definition of a gap detection rule.

    Attributes:
        gap_type: Type of gap this rule detects
        severity: Severity level
        description: Human-readable description
        suggestion: Suggested fix
    """

    def __init__(
        self,
        gap_type: GapType,
        severity: GapSeverity,
        description: str,
        suggestion: str = "",
    ) -> None:
        """Initialize GapRule.

        Args:
            gap_type: Type of gap
            severity: Severity level
            description: Human-readable description
            suggestion: Suggested fix
        """
        self.gap_type = gap_type
        self.severity = severity
        self.description = description
        self.suggestion = suggestion

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"GapRule(type={self.gap_type.value}, "
            f"severity={self.severity.value})"
        )


# Predefined rules
GAP_RULES: Dict[GapType, GapRule] = {
    GapType.BASE64_VS_AES: GapRule(
        gap_type=GapType.BASE64_VS_AES,
        severity=GapSeverity.HIGH,
        description="Mixed use of Base64 encoding and AES encryption",
        suggestion="Choose one cryptographic method consistently. "
        "AES for encryption, Base64 only for encoding transport-safe data.",
    ),
    GapType.TEST_TODO_FLOOD: GapRule(
        gap_type=GapType.TEST_TODO_FLOOD,
        severity=GapSeverity.MEDIUM,
        description="Excessive test.todo() or unimplemented assertions",
        suggestion="Replace todo items with actual assertions or remove them. "
        "Todo spam masks incomplete test coverage.",
    ),
    GapType.EMPTY_CATCH: GapRule(
        gap_type=GapType.EMPTY_CATCH,
        severity=GapSeverity.HIGH,
        description="Empty exception handler (except block with no operations)",
        suggestion="Add meaningful exception handling or logging. "
        "Empty catches hide errors and make debugging difficult.",
    ),
    GapType.HARDCODED_SECRETS: GapRule(
        gap_type=GapType.HARDCODED_SECRETS,
        severity=GapSeverity.CRITICAL,
        description="Hardcoded credentials, API keys, or tokens found",
        suggestion="Move secrets to environment variables or a secrets manager. "
        "Never commit credentials to version control.",
    ),
}


# =============================================================================
# Section 2: AST Detectors
# =============================================================================


class Base64VsAESVisitor(ast.NodeVisitor):
    """AST visitor to detect Base64 and AES mixed usage."""

    def __init__(self) -> None:
        """Initialize visitor."""
        self.findings: List[GapFinding] = []
        self.file_path = ""
        self.has_base64 = False
        self.has_aes = False
        self.base64_nodes: List[int] = []
        self.aes_nodes: List[int] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call node to check for crypto usage."""
        # Check for Base64 usage
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in {"b64encode", "b64decode", "encode", "decode"}:
                if self._is_base64_context(node):
                    self.has_base64 = True
                    self.base64_nodes.append(node.lineno)

        # Check for AES usage (simplified detection)
        if isinstance(node.func, ast.Name):
            if "aes" in node.func.id.lower() or "crypto" in node.func.id.lower():
                self.has_aes = True
                self.aes_nodes.append(node.lineno)
        elif isinstance(node.func, ast.Attribute):
            if "aes" in node.func.attr.lower():
                self.has_aes = True
                self.aes_nodes.append(node.lineno)

        self.generic_visit(node)

    def _is_base64_context(self, node: ast.Call) -> bool:
        """Check if Call is Base64 related."""
        if isinstance(node.func.value, ast.Name):
            return node.func.value.id in {"base64", "b64"}
        return False

    def get_findings(self) -> List[GapFinding]:
        """Get findings from visited nodes."""
        if self.has_base64 and self.has_aes:
            # Find intersecting lines or nearby lines
            for line in self.base64_nodes:
                if any(abs(line - a) < 10 for a in self.aes_nodes):
                    return [
                        GapFinding(
                            gap_type=GapType.BASE64_VS_AES,
                            file_path=self.file_path,
                            line_number=line,
                            severity=GAP_RULES[GapType.BASE64_VS_AES].severity.value,
                            description=GAP_RULES[GapType.BASE64_VS_AES].description,
                            suggestion=GAP_RULES[GapType.BASE64_VS_AES].suggestion,
                        )
                    ]
        return []


class TestTodoFloodVisitor(ast.NodeVisitor):
    """AST visitor to detect test.todo() spam."""

    # Patterns that indicate test todos
    TODO_PATTERNS = [
        r"test\.todo",
        r"describe\.todo",
        r"it\.todo",
        r"case\.todo",
        r"@todo",
        r"# todo",
        r"// todo",
        r"TODO",
        r"assert\.true\s*\(\s*false",
    ]

    def __init__(self) -> None:
        """Initialize visitor."""
        self.findings: List[GapFinding] = []
        self.file_path = ""
        self.todo_count = 0
        self.todo_lines: List[int] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Visit Call node to check for todo patterns."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in {"todo", "skip", "pending"}:
                self.todo_count += 1
                self.todo_lines.append(node.lineno)

        self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> None:
        """Visit Expr node for string todos."""
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            text = node.value.value.lower()
            for pattern in self.TODO_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    self.todo_count += 1
                    self.todo_lines.append(node.lineno)
                    break

        self.generic_visit(node)

    def get_findings(self) -> List[GapFinding]:
        """Get findings if todo count exceeds threshold."""
        threshold = 3
        if self.todo_count >= threshold:
            # Report all todo lines as a single finding
            return [
                GapFinding(
                    gap_type=GapType.TEST_TODO_FLOOD,
                    file_path=self.file_path,
                    line_number=self.todo_lines[0] if self.todo_lines else 0,
                    severity=GAP_RULES[GapType.TEST_TODO_FLOOD].severity.value,
                    description=(
                        f"Found {self.todo_count} test todo/pending assertions. "
                        f"This may indicate incomplete test suite."
                    ),
                    suggestion=GAP_RULES[GapType.TEST_TODO_FLOOD].suggestion,
                    code_snippet=f"// {self.todo_count} TODOs found",
                )
            ]
        return []


class EmptyCatchVisitor(ast.NodeVisitor):
    """AST visitor to detect empty exception handlers."""

    def __init__(self) -> None:
        """Initialize visitor."""
        self.findings: List[GapFinding] = []
        self.file_path = ""

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Visit ExceptHandler node to check if empty."""
        # Check if body is empty or only contains pass/ellipsis
        if not node.body:
            self.findings.append(
                self._create_finding(node.lineno if node.lineno else 0)
            )
        elif len(node.body) == 1:
            first_stmt = node.body[0]
            if isinstance(first_stmt, ast.Pass):
                self.findings.append(
                    self._create_finding(node.lineno if node.lineno else 0)
                )
            elif isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and first_stmt.value.value is ...:
                # Ellipsis case: Expr(value=Constant(value=Ellipsis))
                self.findings.append(
                    self._create_finding(node.lineno if node.lineno else 0)
                )
        else:
            # Check if body is only comments/docstrings
            meaningful_stmts = [
                s for s in node.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
            ]
            if not meaningful_stmts:
                self.findings.append(
                    self._create_finding(node.lineno if node.lineno else 0)
                )

        self.generic_visit(node)

    def _create_finding(self, line_number: int) -> GapFinding:
        """Create a GapFinding for empty catch."""
        return GapFinding(
            gap_type=GapType.EMPTY_CATCH,
            file_path=self.file_path,
            line_number=line_number,
            severity=GAP_RULES[GapType.EMPTY_CATCH].severity.value,
            description=GAP_RULES[GapType.EMPTY_CATCH].description,
            suggestion=GAP_RULES[GapType.EMPTY_CATCH].suggestion,
        )

    def get_findings(self) -> List[GapFinding]:
        """Get all findings."""
        return self.findings


class HardcodedSecretsScanner:
    """Scanner for hardcoded secrets in source code."""

    # Patterns for secret detection
    SECRET_PATTERNS = [
        (r'api[_-]?key\s*[:=]\s*["\'].{5,}', "API key"),
        (r'password\s*[:=]\s*["\'].{5,}', "password"),
        (r'secret\s*[:=]\s*["\'].{5,}', "secret"),
        (r'token\s*[:=]\s*["\'].{5,}', "token"),
        (r'auth\s*[:=]\s*["\'].{5,}', "auth credential"),
        (r'private[_-]?key\s*[:=]\s*["\'].{5,}', "private key"),
        (r'aws[_-]?access[_-]?key', "AWS access key"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token"),
        (r'xox[baprs]-[a-zA-Z0-9]{10,}', "Slack token"),
    ]

    def __init__(self) -> None:
        """Initialize scanner."""
        self.findings: List[GapFinding] = []
        self.file_path = ""

    def scan(self, source_code: str, file_path: str) -> List[GapFinding]:
        """Scan source code for hardcoded secrets.

        Args:
            source_code: Source code string
            file_path: File path for reporting

        Returns:
            List of GapFinding objects
        """
        self.findings = []
        self.file_path = file_path

        for line_num, line in enumerate(source_code.split("\n"), start=1):
            for pattern, secret_type in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Mask the secret in the snippet
                    masked_line = self._mask_secret(line)
                    self.findings.append(
                        GapFinding(
                            gap_type=GapType.HARDCODED_SECRETS,
                            file_path=file_path,
                            line_number=line_num,
                            severity=GAP_RULES[GapType.HARDCODED_SECRETS].severity.value,
                            description=f"Potential hardcoded {secret_type} detected",
                            code_snippet=masked_line[:100],
                            suggestion=GAP_RULES[GapType.HARDCODED_SECRETS].suggestion,
                        )
                    )

        return self.findings

    def _mask_secret(self, line: str) -> str:
        """Mask secret values in a line."""
        # Replace visible secrets with masked version
        masked = re.sub(
            r'(=[:\s]*["\'])(.{5,})(["\'])',
            r'\1***MASKED***\3',
            line,
        )
        return masked


# =============================================================================
# Section 3: Gap Detector
# =============================================================================


class GapDetector:
    """Implementation Gap Detector.

    Scans source code for various implementation gaps using AST analysis
    and pattern matching.

    Attributes:
        rules: Dict of GapType -> GapRule mappings
        _findings: Internal list of all findings

    Example:
        >>> detector = GapDetector()
        >>> findings = detector.scan(source_code, file_path)
        >>> summary = detector.get_summary()
    """

    def __init__(
        self,
        rules: Optional[List[GapRule]] = None,
    ) -> None:
        """Initialize GapDetector with optional custom rules.

        Args:
            rules: List of GapRule objects to use
        """
        if rules is not None:
            self.rules = {rule.gap_type: rule for rule in rules}
        else:
            # Use default rules
            self.rules = GAP_RULES.copy()
        self._findings: List[GapFinding] = []

    def scan(
        self,
        source_code: str,
        file_path: str,
        gap_types: Optional[List[GapType]] = None,
    ) -> List[GapFinding]:
        """Scan source code for implementation gaps.

        Args:
            source_code: Source code string to analyze
            file_path: File path for error reporting
            gap_types: List of GapTypes to detect (None = all)

        Returns:
            List of GapFinding objects

        Raises:
            GapDetectionError: If source code has syntax errors
        """
        findings: List[GapFinding] = []
        gap_types = gap_types or list(GapType)

        # Empty source
        if not source_code or not source_code.strip():
            return findings

        # Scan for hardcoded secrets (regex-based, always runs)
        if GapType.HARDCODED_SECRETS in gap_types:
            secret_scanner = HardcodedSecretsScanner()
            findings.extend(secret_scanner.scan(source_code, file_path))

        # Try AST parsing for other detectors
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise GapDetectionError(
                message=f"Syntax error in source: {e}",
                file_path=file_path,
                line_number=e.lineno or 0,
                error_type="syntax",
            )
        except Exception as e:
            raise GapDetectionError(
                message=f"AST parsing failed: {e}",
                file_path=file_path,
                error_type="parse",
            )

        # Run AST-based detectors
        if GapType.BASE64_VS_AES in gap_types:
            visitor = Base64VsAESVisitor()
            visitor.file_path = file_path
            visitor.visit(tree)
            findings.extend(visitor.get_findings())

        if GapType.TEST_TODO_FLOOD in gap_types:
            visitor = TestTodoFloodVisitor()
            visitor.file_path = file_path
            visitor.visit(tree)
            findings.extend(visitor.get_findings())

        if GapType.EMPTY_CATCH in gap_types:
            visitor = EmptyCatchVisitor()
            visitor.file_path = file_path
            visitor.visit(tree)
            findings.extend(visitor.get_findings())

        # Store findings
        self._findings.extend(findings)
        return findings

    def scan_directory(
        self,
        directory: str,
        patterns: Optional[List[str]] = None,
        gap_types: Optional[List[GapType]] = None,
    ) -> GapSummary:
        """Scan entire directory recursively.

        Args:
            directory: Directory path to scan
            patterns: Glob patterns for file matching (default: ["*.py"])
            gap_types: List of GapTypes to detect (None = all)

        Returns:
            GapSummary with all findings
        """
        patterns = patterns or ["*.py"]
        gap_types = gap_types or list(GapType)

        findings: List[GapFinding] = []
        files_scanned = 0

        directory = Path(directory)
        if not directory.exists():
            return GapSummary(
                total_files=0,
                total_findings=0,
                by_type={},
                by_severity={},
                findings=[],
            )

        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                # Skip __pycache__ and hidden directories
                if "__pycache__" in str(file_path) or file_path.name.startswith("."):
                    continue

                # Check if it's a file (not directory)
                if not file_path.is_file():
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        source_code = f.read()
                    files_scanned += 1

                    file_findings = self.scan(
                        source_code,
                        str(file_path),
                        gap_types,
                    )
                    findings.extend(file_findings)

                except Exception as e:
                    # Skip files that can't be read
                    print(f"Warning: Could not scan {file_path}: {e}")
                    continue

        # Build summary
        by_type: Dict[GapType, int] = {}
        by_severity: Dict[str, int] = {}

        for finding in findings:
            by_type[finding.gap_type] = by_type.get(finding.gap_type, 0) + 1
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1

        return GapSummary(
            total_files=files_scanned,
            total_findings=len(findings),
            by_type=by_type,
            by_severity=by_severity,
            findings=findings,
        )

    def get_findings(
        self,
        filter_severity: Optional[str] = None,
    ) -> List[GapFinding]:
        """Get findings with optional severity filter.

        Args:
            filter_severity: Filter by severity (e.g., "HIGH", "CRITICAL")

        Returns:
            Filtered list of GapFinding objects
        """
        if filter_severity is None:
            return self._findings.copy()

        return [
            f for f in self._findings
            if f.severity.upper() == filter_severity.upper()
        ]

    def get_summary(self) -> GapSummary:
        """Get summary of all findings.

        Returns:
            GapSummary with aggregated statistics
        """
        by_type: Dict[GapType, int] = {}
        by_severity: Dict[str, int] = {}

        for finding in self._findings:
            by_type[finding.gap_type] = by_type.get(finding.gap_type, 0) + 1
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1

        return GapSummary(
            total_files=0,  # Unknown in this context
            total_findings=len(self._findings),
            by_type=by_type,
            by_severity=by_severity,
            findings=self._findings.copy(),
        )

    def clear_findings(self) -> None:
        """Clear all stored findings."""
        self._findings = []

    def get_rule(self, gap_type: GapType) -> Optional[GapRule]:
        """Get rule for a gap type.

        Args:
            gap_type: Gap type to look up

        Returns:
            GapRule or None if not found
        """
        return self.rules.get(gap_type)
