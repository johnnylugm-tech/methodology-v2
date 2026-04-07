"""
Linter Adapter — 統一多語言 linter 輸出
=======================================
支援：pylint (Python), eslint (JS/TS), golangci-lint (Go)

使用方式：
    python linter_adapter.py --path /path/to/project
    from linter_adapter import LinterAdapter
    adapter = LinterAdapter("/path/to/project")
    result = adapter.run()
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class LinterResult:
    """標準化 linter 輸出"""
    language: str
    tool: str
    score: float  # 0-100
    errors: List[Dict[str, Any]]   # [{file, line, message, severity}]
    warnings: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]  # [{file, line, message, rule, severity}]
    raw_output: str


class LinterAdapter:
    """統一多語言 linter 輸出介面"""
    
    LINTERS = {
        ".py": {"tool": "pylint", "args": ["--output-format=json"]},
        ".js": {"tool": "eslint", "args": ["--format=json"]},
        ".ts": {"tool": "eslint", "args": ["--format=json"]},
        ".go": {"tool": "golangci-lint", "args": ["out-format=json"]},
    }
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def detect_language(self) -> Optional[str]:
        """偵測專案主要語言"""
        extensions = {".py": "python", ".js": "javascript", ".ts": "typescript", ".go": "go"}
        for ext, lang in extensions.items():
            if list(self.project_path.rglob(f"*{ext}")):
                return lang
        return None
    
    def run(self) -> LinterResult:
        """執行 linter 並標準化輸出"""
        lang = self.detect_language()
        if not lang:
            return LinterResult(
                language="unknown", tool="none", score=100,
                errors=[], warnings=[], violations=[], raw_output=""
            )
        
        config = self.LINTERS.get(f".{lang}")
        if not config:
            return LinterResult(
                language=lang, tool="none", score=100,
                errors=[], warnings=[], violations=[], raw_output=""
            )
        
        try:
            result = subprocess.run(
                [config["tool"]] + config["args"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            raw = result.stdout + result.stderr
            violations = self._parse_output(raw, lang, config["tool"])
            score = self._calc_score(violations)
            
            # 分離 errors 和 warnings
            errors = [v for v in violations if v["severity"] == "ERROR"]
            warnings = [v for v in violations if v["severity"] == "WARNING"]
            
            return LinterResult(
                language=lang, tool=config["tool"], score=score,
                errors=errors, warnings=warnings, violations=violations, raw_output=raw
            )
        except FileNotFoundError:
            return LinterResult(
                language=lang, tool=config["tool"], score=100,
                errors=[], warnings=[], violations=[],
                raw_output=f"{config['tool']} not installed"
            )
        except Exception as e:
            return LinterResult(
                language=lang, tool=config["tool"], score=100,
                errors=[], warnings=[], violations=[], raw_output=str(e)
            )
    
    def _parse_output(self, raw: str, lang: str, tool: str) -> List[Dict]:
        """解析 linter 輸出為標準格式"""
        violations = []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for item in data:
                    violations.append({
                        "file": item.get("path", item.get("filename", "")),
                        "line": item.get("line", 0),
                        "message": item.get("message", ""),
                        "rule": item.get("rule", item.get("messageId", "")),
                        "severity": self._normalize_severity(item.get("severity", "WARNING"), tool)
                    })
            elif isinstance(data, dict) and "messages" in data:
                for msg in data["messages"]:
                    violations.append({
                        "file": msg.get("path", ""),
                        "line": msg.get("line", 0),
                        "message": msg.get("message", ""),
                        "rule": msg.get("rule", ""),
                        "severity": self._normalize_severity(msg.get("severity", "WARNING"), tool)
                    })
        except json.JSONDecodeError:
            # 非 JSON 輸出，按行解析
            for line in raw.split("\n"):
                if not line.strip():
                    continue
                violations.append({
                    "file": "", "line": 0,
                    "message": line.strip(), "rule": "unknown",
                    "severity": "WARNING"
                })
        return violations
    
    def _normalize_severity(self, severity: str, tool: str) -> str:
        """將不同 linter 的 severity 統一"""
        tool = tool.lower()
        sev = str(severity).lower()
        if tool == "pylint":
            if sev in ("error", "fatal"): return "ERROR"
            if sev in ("warning", "convention", "refactor"): return "WARNING"
            return "INFO"
        elif tool == "eslint":
            if sev in ("2", "error"): return "ERROR"
            if sev in ("1", "warn"): return "WARNING"
            return "INFO"
        return "WARNING"
    
    def _calc_score(self, violations: List[Dict]) -> float:
        """基於違規計算分數"""
        if not violations:
            return 100
        error_count = sum(1 for v in violations if v["severity"] == "ERROR")
        warning_count = sum(1 for v in violations if v["severity"] == "WARNING")
        # ERROR: -2, WARNING: -1
        score = 100 - error_count * 2 - warning_count * 1
        return max(0, score)
    
    def to_json(self) -> str:
        """將結果序列化為 JSON"""
        result = self.run()
        return json.dumps(asdict(result), indent=2, ensure_ascii=False)


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description="Linter Adapter - 統一多語言 linter 輸出")
    parser.add_argument("--path", required=True, help="專案路徑")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()
    
    adapter = LinterAdapter(args.path)
    result = adapter.run()
    
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(f"Language: {result.language}")
        print(f"Tool: {result.tool}")
        print(f"Score: {result.score}/100")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"Total Violations: {len(result.violations)}")
        if result.raw_output and "not installed" in result.raw_output:
            print(f"\n⚠️ {result.raw_output}")
        elif result.violations:
            print("\n--- Top Violations ---")
            for v in result.violations[:10]:
                print(f"  [{v['severity']}] {v['file']}:{v['line']} - {v['message'][:80]}")


if __name__ == "__main__":
    main()
