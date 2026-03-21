"""Tests for auto_debugger module"""
import pytest
from auto_debugger import (
    ErrorClassifier, ErrorLevel, RootCauseAnalyzer, 
    AutoRecovery, DebugTrace, AutoDebugger
)

class TestErrorClassifier:
    """Test ErrorClassifier"""
    
    def test_classify_timeout(self):
        """Test timeout error classification"""
        classifier = ErrorClassifier()
        error = Exception("connection timeout")
        level = classifier.classify(error)
        assert level == ErrorLevel.L1_TRANSIENT
    
    def test_classify_prompt(self):
        """Test prompt error classification"""
        classifier = ErrorClassifier()
        error = Exception("ambiguous instruction")
        level = classifier.classify(error)
        assert level == ErrorLevel.L2_PROMPT
    
    def test_classify_tool(self):
        """Test tool error classification"""
        classifier = ErrorClassifier()
        error = Exception("tool not found")
        level = classifier.classify(error)
        assert level == ErrorLevel.L3_TOOL

class TestRootCauseAnalyzer:
    """Test RootCauseAnalyzer"""
    
    def test_find_cause_timeout(self):
        """Test timeout cause"""
        analyzer = RootCauseAnalyzer()
        cause = analyzer.find_cause("timeout error", [])
        assert cause == "timeout"

class TestDebugTrace:
    """Test DebugTrace"""
    
    def test_add(self):
        """Test adding trace"""
        trace = DebugTrace()
        trace.add("test_event", {"key": "value"})
        entries = trace.get_trace()
        assert len(entries) > 0
    
    def test_clear(self):
        """Test clearing trace"""
        trace = DebugTrace()
        trace.add("test", {})
        trace.clear()
        assert len(trace.get_trace()) == 0

class TestAutoDebugger:
    """Test AutoDebugger"""
    
    def test_analyze(self):
        """Test analyze"""
        debugger = AutoDebugger()
        error = Exception("timeout error")
        result = debugger.analyze(error, {})
        assert "level" in result
        assert "root_cause" in result
    
    def test_suggest_recovery(self):
        """Test recovery suggestion"""
        debugger = AutoDebugger()
        error = Exception("timeout")
        result = debugger.suggest_recovery(error)
        assert "actions" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
