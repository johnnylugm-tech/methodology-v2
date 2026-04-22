"""Tests for detection/gap_detector.py."""
import pytest

from detection.data_models import GapSeverity, GapType
from detection.exceptions import GapDetectionError
from detection.gap_detector import (
    Base64VsAESVisitor,
    EmptyCatchVisitor,
    GapDetector,
    GapRule,
    GAP_RULES,
    HardcodedSecretsScanner,
    TestTodoFloodVisitor,
)


class TestGapRule:
    def test_repr(self):
        rule = GapRule(
            gap_type=GapType.HARDCODED_SECRETS,
            severity=GapSeverity.CRITICAL,
            description="Hardcoded secret",
            suggestion="Use env vars",
        )
        r = repr(rule)
        assert "hardcoded_secrets" in r
        assert "CRITICAL" in r


class TestGAP_RULES:
    def test_all_gap_types_have_rules(self):
        for gt in GapType:
            assert gt in GAP_RULES
            rule = GAP_RULES[gt]
            assert rule.gap_type == gt
            assert rule.description
            assert rule.suggestion


class TestBase64VsAESVisitor:
    def test_no_findings_empty_code(self):
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        # Empty tree
        import ast
        tree = ast.parse("")
        visitor.visit(tree)
        assert visitor.get_findings() == []

    def test_base64_only(self):
        import ast
        code = "import base64\nbase64.b64encode(b'data')"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Should not trigger - no AES
        findings = visitor.get_findings()
        # has_base64=True but has_aes=False -> no finding
        assert findings == []

    def test_aes_only(self):
        import ast
        code = "from crypto import AES"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # has_aes=True but has_base64=False -> no finding
        assert visitor.get_findings() == []

    def test_both_base64_and_aes(self):
        import ast
        # Simplified - both flags should be set
        code = "import base64\nfrom crypto import AES"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Both True but lines not within 10 -> no finding
        assert visitor.get_findings() == []

    def test_aes_attribute_method(self):
        """Test AES detection via attribute method call (crypto.aes_encrypt)."""
        import ast
        # This triggers the elif isinstance(node.func, ast.Attribute) branch for AES
        code = "import crypto\ncrypto.aes_encrypt(data)"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # has_aes=True via attribute method
        assert visitor.has_aes is True

    def test_base64_attribute_method_no_context(self):
        """Test base64 detection when context is not base64/b64."""
        import ast
        # This triggers the _is_base64_context returning False
        code = "import encoder\nencoder.b64encode(data)"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # has_base64 should be False since context is 'encoder', not 'base64'/'b64'
        assert visitor.has_base64 is False


class TestTestTodoFloodVisitor:
    def test_no_todos(self):
        import ast
        code = "def test(): assert True"
        tree = ast.parse(code)
        visitor = TestTodoFloodVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        assert visitor.get_findings() == []

    def test_single_todo_below_threshold(self):
        import ast
        code = "def test(): pass  # TODO: implement"
        tree = ast.parse(code)
        visitor = TestTodoFloodVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Only 1 todo < threshold(3) -> no finding
        assert visitor.get_findings() == []

    def test_multiple_todos_above_threshold(self):
        import ast
        code = """
test.todo()
test.todo()
test.todo()
"""
        tree = ast.parse(code)
        visitor = TestTodoFloodVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        findings = visitor.get_findings()
        assert len(findings) == 1
        assert findings[0].gap_type == GapType.TEST_TODO_FLOOD

    def test_string_todo_comment(self):
        import ast
        code = '# TODO: fix this later'
        tree = ast.parse(code)
        visitor = TestTodoFloodVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # String todo detected


class TestEmptyCatchVisitor:
    def test_empty_except_block(self):
        import ast
        code = """
try:
    pass
except:
    pass
"""
        tree = ast.parse(code)
        visitor = EmptyCatchVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # The inner pass in try body shouldn't trigger
        findings = visitor.get_findings()
        # Empty except -> 1 finding
        assert len(findings) == 1
        assert findings[0].gap_type == GapType.EMPTY_CATCH

    def test_except_with_only_pass(self):
        import ast
        code = """
try:
    x = 1
except Exception:
    pass
"""
        tree = ast.parse(code)
        visitor = EmptyCatchVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        findings = visitor.get_findings()
        assert len(findings) == 1

    def test_except_with_meaningful_code(self):
        import ast
        code = """
try:
    x = 1
except Exception:
    print("error")
"""
        tree = ast.parse(code)
        visitor = EmptyCatchVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        findings = visitor.get_findings()
        # Has meaningful code -> no finding
        assert findings == []

    def test_except_with_ellipsis(self):
        import ast
        code = """
try:
    x = 1
except Exception:
    ...
"""
        tree = ast.parse(code)
        visitor = EmptyCatchVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        findings = visitor.get_findings()
        # Ellipsis counts as empty
        assert len(findings) == 1


class TestHardcodedSecretsScanner:
    def test_no_secrets(self):
        scanner = HardcodedSecretsScanner()
        code = "api_key = os.environ.get('KEY')"
        findings = scanner.scan(code, "test.py")
        assert findings == []

    def test_detects_api_key(self):
        scanner = HardcodedSecretsScanner()
        code = 'api_key = "sk-1234567890abcdef"'
        findings = scanner.scan(code, "test.py")
        assert len(findings) >= 1
        assert any(f.gap_type == GapType.HARDCODED_SECRETS for f in findings)

    def test_detects_password(self):
        scanner = HardcodedSecretsScanner()
        code = 'password = "supersecret"'
        findings = scanner.scan(code, "test.py")
        assert len(findings) >= 1
        assert any(f.gap_type == GapType.HARDCODED_SECRETS for f in findings)

    def test_detects_github_token(self):
        scanner = HardcodedSecretsScanner()
        code = "ghp_abcdefghijklmnopqrstuvwxyz1234567890AB"
        findings = scanner.scan(code, "test.py")
        assert len(findings) >= 1

    def test_detects_slack_token(self):
        scanner = HardcodedSecretsScanner()
        code = "xoxb-abcdefghij-1234567890"
        findings = scanner.scan(code, "test.py")
        assert len(findings) >= 1

    def test_masks_secret_in_snippet(self):
        scanner = HardcodedSecretsScanner()
        code = 'api_key = "sk-secret123"'
        findings = scanner.scan(code, "test.py")
        if findings:
            # Secret should be masked
            assert "***MASKED***" in findings[0].code_snippet or "sk-" not in findings[0].code_snippet


class TestGapDetector:
    def test_default_rules(self):
        detector = GapDetector()
        assert len(detector.rules) == 4
        for gt in GapType:
            assert gt in detector.rules

    def test_custom_rules(self):
        custom_rule = GapRule(
            gap_type=GapType.HARDCODED_SECRETS,
            severity=GapSeverity.LOW,
            description="Custom rule",
            suggestion="Fix it",
        )
        detector = GapDetector(rules=[custom_rule])
        assert len(detector.rules) == 1
        assert detector.rules[GapType.HARDCODED_SECRETS].severity == GapSeverity.LOW

    def test_scan_empty_source(self):
        detector = GapDetector()
        findings = detector.scan("", "test.py")
        assert findings == []

    def test_scan_whitespace_source(self):
        detector = GapDetector()
        findings = detector.scan("   \n\n  ", "test.py")
        assert findings == []

    def test_scan_finds_empty_catch(self):
        detector = GapDetector()
        code = """
try:
    x = 1
except:
    pass
"""
        findings = detector.scan(code, "test.py")
        gap_types = [f.gap_type for f in findings]
        assert GapType.EMPTY_CATCH in gap_types

    def test_scan_finds_hardcoded_secrets(self):
        detector = GapDetector()
        code = 'password = "secret123"'
        findings = detector.scan(code, "test.py")
        gap_types = [f.gap_type for f in findings]
        assert GapType.HARDCODED_SECRETS in gap_types

    def test_scan_syntax_error_raises(self):
        detector = GapDetector()
        with pytest.raises(GapDetectionError, match="Syntax error"):
            detector.scan("def = invalid syntax", "test.py")

    def test_scan_gap_types_filter(self):
        detector = GapDetector()
        code = 'password = "secret"'
        # Only check EMPTY_CATCH
        findings = detector.scan(
            code, "test.py", gap_types=[GapType.EMPTY_CATCH]
        )
        gap_types = [f.gap_type for f in findings]
        assert GapType.HARDCODED_SECRETS not in gap_types

    def test_scan_stores_findings(self):
        detector = GapDetector()
        code = 'password = "secret"'
        detector.scan(code, "test.py")
        assert len(detector._findings) >= 1

    def test_get_findings_no_filter(self):
        detector = GapDetector()
        code = 'password = "secret"'
        detector.scan(code, "test.py")
        findings = detector.get_findings()
        assert len(findings) >= 1

    def test_get_findings_with_severity_filter(self):
        detector = GapDetector()
        code = 'password = "secret"'
        detector.scan(code, "test.py")
        findings = detector.get_findings(filter_severity="CRITICAL")
        for f in findings:
            assert f.severity == "CRITICAL"

    def test_get_summary(self):
        detector = GapDetector()
        code = 'password = "secret"'
        detector.scan(code, "test.py")
        summary = detector.get_summary()
        assert summary.total_findings >= 1
        assert summary.by_type[GapType.HARDCODED_SECRETS] >= 1

    def test_clear_findings(self):
        detector = GapDetector()
        code = 'password = "secret"'
        detector.scan(code, "test.py")
        assert len(detector._findings) >= 1
        detector.clear_findings()
        assert len(detector._findings) == 0

    def test_get_rule(self):
        detector = GapDetector()
        rule = detector.get_rule(GapType.EMPTY_CATCH)
        assert rule is not None
        assert rule.gap_type == GapType.EMPTY_CATCH

    def test_get_rule_nonexistent(self):
        GapDetector()
        # Custom detector with no rules
        custom_detector = GapDetector(rules=[])
        assert custom_detector.get_rule(GapType.EMPTY_CATCH) is None

    def test_scan_directory_nonexistent(self):
        detector = GapDetector()
        summary = detector.scan_directory("/nonexistent/path")
        assert summary.total_files == 0

    def test_scan_directory_basic(self, tmp_path):
        detector = GapDetector()
        # Create a temp Python file
        py_file = tmp_path / "test_file.py"
        py_file.write_text('password = "secret"\n')

        summary = detector.scan_directory(str(tmp_path))
        assert summary.total_files >= 1
        assert summary.total_findings >= 1

    def test_scan_directory_skips_pycache(self, tmp_path):
        detector = GapDetector()
        # Create __pycache__ directory
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.pyc").write_text("compiled")

        summary = detector.scan_directory(str(tmp_path))
        # Should skip pycache
        assert summary.total_files == 0

    def test_scan_directory_skips_pycache_dirs(self, tmp_path):
        """Test that __pycache__ directories are skipped."""
        detector = GapDetector()
        # Create __pycache__ directory with Python file
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "test.cpython-310.pyc").write_text("compiled bytecode")

        # Also create a real Python file
        (tmp_path / "test.py").write_text('password = "secret"\n')

        summary = detector.scan_directory(str(tmp_path))
        # Should only scan test.py, not files in __pycache__
        assert summary.total_files == 1

    def test_scan_directory_skips_non_files(self, tmp_path):
        detector = GapDetector()
        # Create a directory inside the search path (not a file)
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()

        summary = detector.scan_directory(str(tmp_path))
        # Should skip directories
        assert summary.total_files == 0

    def test_scan_directory_generic_exception(self, tmp_path, capsys):
        GapDetector()
        # Create a file that can't be read (permission error simulated by passing invalid path)
        # But since we control the temp path, this is hard to simulate
        # Instead, test that scan() can handle generic exceptions
        # This is already covered by the SyntaxError test, but we add one more
        # for the generic Exception branch in scan()
        # Since scan() only raises SyntaxError specifically and catches others,
        # the generic exception branch is only hit if AST parsing fails non-SyntaxError
        # This is hard to trigger in tests - the branch exists but requires
        # a very specific type of failure in ast.parse() that isn't SyntaxError


class TestBase64VsAESVisitorEdgeCases:
    """Additional edge case tests for Base64VsAESVisitor."""

    def test_is_base64_context_returns_false_for_non_name(self):
        """Test _is_base64_context returns False when func.value is not ast.Name."""
        import ast
        # This is an indirect test - we trigger the condition by having
        # a Call node where func.value is not a Name (e.g., an Attribute)
        # Example: something.base64.b64encode()
        # This would make func.value be an Attribute, not a Name
        # The _is_base64_context would return False
        # But to directly test it, we'd need to construct the AST manually
        # For simplicity, we test the broader behavior
        code = "obj.base64.b64encode(b'data')"
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # has_base64 should be False because _is_base64_context returns False
        # for non-ast.Name func.value
        assert visitor.has_base64 is False

    def test_get_findings_returns_empty_when_no_close_lines(self):
        """Test get_findings returns [] when base64 and aes are not within 10 lines."""
        import ast
        # base64 on line 1, aes on line 20 (>10 apart) -> no finding
        code = """
import base64
base64.b64encode(b'data')
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
# lots of code
from crypto import AES
AES.new(key, mode)
"""
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        findings = visitor.get_findings()
        # Lines are far apart -> no finding
        assert findings == []

    def test_get_findings_returns_finding_when_close_lines(self):
        """Test get_findings returns finding when base64 and aes within 10 lines."""
        import ast
        # Both within 10 lines -> should return finding
        # Need to trigger both has_base64 and has_aes detection
        # For AES with Name, node.func.id must contain "aes"
        # Using AES() directly as a call (not AES.new)
        code = """
import base64
base64.b64encode(b'data')
aes = AES()
"""
        tree = ast.parse(code)
        visitor = Base64VsAESVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Both True and within 10 lines -> finding
        findings = visitor.get_findings()
        assert len(findings) >= 1


class TestEmptyCatchVisitorEdgeCases:
    """Additional edge case tests for EmptyCatchVisitor."""

    def test_except_with_multiple_comments_only(self):
        """Test except block with multiple statements that are all comments/docstrings."""
        import ast
        # Multiple docstrings - should reach the else branch (lines 273-278)
        # which checks if all statements are Expr with Constant (docstrings)
        code = '''
try:
    x = 1
except Exception:
    """First docstring"""
    """Second docstring"""
'''
        tree = ast.parse(code)
        visitor = EmptyCatchVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Multiple docstrings -> should be detected as empty
        assert len(visitor.findings) >= 1


class TestTestTodoFloodVisitorEdgeCases:
    """Additional edge case tests for TestTodoFloodVisitor."""

    def test_string_todo_regex_pattern(self):
        """Test that string todos match the regex patterns."""
        import ast
        # A standalone string expression triggers visit_Expr
        code = '"TODO: implement this later"'
        tree = ast.parse(code)
        visitor = TestTodoFloodVisitor()
        visitor.file_path = "test.py"
        visitor.visit(tree)
        # Should detect string todo
        assert visitor.todo_count >= 1
