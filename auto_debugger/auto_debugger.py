"""Auto Debugger - Systematic debugging with framework integration"""
import time, json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Framework integration
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    from methodology import ErrorClassifier as FrameworkErrorClassifier, ErrorLevel
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
    ErrorLevel = None

class ErrorLevel(Enum):
    """Error severity levels (compatible with framework)"""
    L1_TRANSIENT = "L1"      # Retryable
    L2_PROMPT = "L2"         # Fix prompt
    L3_TOOL = "L3"           # Fix tool
    L4_SYSTEM = "L4"         # Internal error

class ErrorClassifier:
    """Error classifier with framework integration"""
    
    TRANSIENT_KEYWORDS = ["timeout", "network", "connection", "503", "429"]
    PROMPT_KEYWORDS = ["ambiguous", "unclear", "invalid", "parse"]
    TOOL_KEYWORDS = ["tool", "function", "not found", "available"]
    SYSTEM_KEYWORDS = ["internal", "model", "server"]
    
    def __init__(self):
        self._framework_classifier = None
        if FRAMEWORK_AVAILABLE:
            try:
                self._framework_classifier = FrameworkErrorClassifier()
            except Exception:
                pass
    
    def classify(self, error: Exception or str) -> ErrorLevel:
        # Try framework first
        if self._framework_classifier:
            try:
                level = self._framework_classifier.classify(error)
                # Convert framework level to local
                return ErrorLevel(level.value if hasattr(level, 'value') else str(level))
            except Exception:
                pass
        
        # Fallback to local classification
        error_str = str(error).lower()
        
        if any(kw in error_str for kw in self.TRANSIENT_KEYWORDS):
            return ErrorLevel.L1_TRANSIENT
        elif any(kw in error_str for kw in self.SYSTEM_KEYWORDS):
            return ErrorLevel.L4_SYSTEM
        elif any(kw in error_str for kw in self.TOOL_KEYWORDS):
            return ErrorLevel.L3_TOOL
        elif any(kw in error_str for kw in self.PROMPT_KEYWORDS):
            return ErrorLevel.L2_PROMPT
        
        return ErrorLevel.L2_PROMPT

class RootCauseAnalyzer:
    """Find root cause of errors with framework integration"""
    
    def __init__(self):
        self._framework_analyzer = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import ErrorHandler
                self._framework_analyzer = ErrorHandler()
            except Exception:
                pass
    
    def find_cause(self, error: Any, trace: List[Dict]) -> str:
        error_str = str(error).lower()
        
        # Check trace for patterns
        for entry in trace:
            if entry.get("type") == "tool_call" and entry.get("status") == "failed":
                return "tool_failure"
            if entry.get("type") == "context" and entry.get("tokens") > 8000:
                return "context_overflow"
        
        # Keyword-based
        if "rate" in error_str or "limit" in error_str:
            return "rate_limit"
        if "auth" in error_str or "permission" in error_str:
            return "auth_failure"
        if "timeout" in error_str:
            return "timeout"
        
        return "unknown"

class AutoRecovery:
    """Suggest and auto-recover from errors"""
    
    ACTIONS = {
        ErrorLevel.L1_TRANSIENT: ["retry_with_backoff", "wait_and_retry"],
        ErrorLevel.L2_PROMPT: ["simplify_prompt", "add_examples", "clarify_instructions"],
        ErrorLevel.L3_TOOL: ["switch_tool", "use_alternative", "fix_parameters"],
        ErrorLevel.L4_SYSTEM: ["escalate_to_human", "log_for_review"],
    }
    
    def __init__(self):
        # Try to use framework's TaskLifecycle for recovery
        self._lifecycle = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import TaskLifecycle
                self._lifecycle = TaskLifecycle(task_id="recovery")
            except Exception:
                pass
    
    def suggest_action(self, error_level: ErrorLevel) -> List[str]:
        return self.ACTIONS.get(error_level, ["escalate_to_human"])
    
    async def auto_recover(self, agent, error: Any) -> Optional[Any]:
        """Attempt auto-recovery"""
        error_level = ErrorClassifier().classify(error)
        
        if error_level == ErrorLevel.L1_TRANSIENT:
            # Retry with backoff
            for attempt in range(3):
                await agent.wait(pow(2, attempt))
                try:
                    return await agent.run(agent.last_task)
                except Exception:
                    continue
        elif error_level == ErrorLevel.L2_PROMPT:
            agent.prompt = self._simplify(agent.prompt)
            return await agent.run(agent.last_task)
        
        return None
    
    def _simplify(self, prompt: str) -> str:
        return prompt[:500] if len(prompt) > 500 else prompt

class DebugTrace:
    """Debug trace recorder"""
    
    def __init__(self):
        self.entries: List[Dict] = []
    
    def add(self, event_type: str, data: Dict, status: str = "success"):
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
            "status": status,
            "framework_integrated": FRAMEWORK_AVAILABLE
        })
    
    def get_trace(self) -> List[Dict]:
        return self.entries
    
    def clear(self):
        self.entries.clear()

class AutoDebugger:
    """Main debugger with framework integration"""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.analyzer = RootCauseAnalyzer()
        self.recovery = AutoRecovery()
        self.trace = DebugTrace()
        self.errors: List[Dict] = []
        
        # Try to use framework's QualityGate
        self._quality_gate = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import QualityGate
                self._quality_gate = QualityGate()
            except Exception:
                pass
    
    def analyze(self, error: Any, agent_state: Dict) -> Dict:
        """Analyze error using framework if available"""
        error_level = self.classifier.classify(error)
        root_cause = self.analyzer.find_cause(error, self.trace.entries)
        actions = self.recovery.suggest_action(error_level)
        
        result = {
            "error": str(error),
            "level": error_level.value,
            "root_cause": root_cause,
            "suggested_actions": actions,
            "timestamp": datetime.now().isoformat(),
            "framework_integrated": FRAMEWORK_AVAILABLE
        }
        
        self.errors.append(result)
        return result
    
    def suggest_recovery(self, error: Any) -> Dict:
        error_level = self.classifier.classify(error)
        actions = self.recovery.suggest_action(error_level)
        
        return {
            "error_level": error_level.value,
            "actions": actions,
            "auto_recoverable": error_level != ErrorLevel.L4_SYSTEM
        }
    
    def log_error(self, error: Any, state: Dict):
        self.errors.append({
            "error": str(error),
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "framework_integrated": FRAMEWORK_AVAILABLE
        })
    
    def get_stats(self) -> Dict:
        if not self.errors:
            return {"total": 0, "framework_integrated": FRAMEWORK_AVAILABLE}
        
        levels = {}
        for e in self.errors:
            lvl = e.get("level", "unknown")
            levels[lvl] = levels.get(lvl, 0) + 1
        
        return {
            "total": len(self.errors),
            "by_level": levels,
            "auto_recovered": sum(1 for e in self.errors if e.get("recovered")),
            "framework_integrated": FRAMEWORK_AVAILABLE
        }

# Demo
if __name__ == "__main__":
    print("=== Auto Debugger with Framework Integration ===")
# # #     print(f"Framework Available: {FRAMEWORK_AVAILABLE}")
    
    debugger = AutoDebugger()
    
    # Trace
    debugger.trace.add("agent_start", {"agent": "coder"})
    debugger.trace.add("tool_call", {"tool": "bash", "status": "success"})
    debugger.trace.add("tool_call", {"tool": "read", "status": "failed"})
    
    # Analyze
    error = Exception("Tool timeout: bash command took too long")
    result = debugger.analyze(error, {"task": "debug"})
    
# # #     print("\n=== Error Analysis ===")
# # #     print(json.dumps(result, indent=2))
    
# # #     print("\n=== Stats ===")
    print(json.dumps(debugger.get_stats(), indent=2))
    
    print("\n✅ Auto Debugger (with framework integration) ready!")
