#!/usr/bin/env python3
"""
Development Log Checker
======================
驗證 DEVELOPMENT_LOG.md 的格式是否符合規範。

使用方式：
    from scripts.dev_log_checker import DevLogChecker
    
    checker = DevLogChecker("/path/to/project")
    result = checker.check()
    print(result.passed)
    
    # 或使用命令列
    # python -m scripts.dev_log_checker /path/to/project
"""

import re
import sys
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple


@dataclass
class DecisionGateRecord:
    """Decision Gate 記錄"""
    decision: str
    session_id: Optional[str]
    confirmed: bool
    date: Optional[str]
    line_number: int


@dataclass
class CommandRecord:
    """命令執行記錄"""
    command: str
    output_present: bool  # 是否有實際輸出
    result: Optional[str]  # 執行結果
    line_number: int


@dataclass
class SessionIdRecord:
    """Session ID 記錄"""
    agent_role: str
    session_id: str
    line_number: int


@dataclass
class DevLogCheckResult:
    """DEVELOPMENT_LOG 檢查結果"""
    passed: bool
    file_exists: bool
    has_header: bool
    has_phase_records: bool
    decision_gates: List[DecisionGateRecord]
    session_ids: List[SessionIdRecord]
    commands: List[CommandRecord]
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    def print_summary(self) -> str:
        """產出摘要報告"""
        status = "✅ PASS" if self.passed else "❌ FAIL"
        
        lines = [
            f"{'='*60}",
            f"Development Log Checker Result",
            f"{'='*60}",
            f"Status: {status}",
            f"File Exists: {self.file_exists}",
            f"Has Header: {self.has_header}",
            f"Has Phase Records: {self.has_phase_records}",
            f"",
            f"Decision Gates: {len(self.decision_gates)}",
            f"Session IDs: {len(self.session_ids)}",
            f"Commands with Output: {sum(1 for c in self.commands if c.output_present)}",
            f"",
        ]
        
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  🚫 {error}")
            lines.append("")
        
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")
        
        lines.append(f"{'='*60}")
        return "\n".join(lines)


class DevLogChecker:
    """DEVELOPMENT_LOG 格式檢查器"""
    
    # 必需的 Section 標題
    REQUIRED_SECTIONS = [
        "Phase",
        "Quality Gate",
    ]
    
    # session_id 格式正則表達式
    SESSION_ID_PATTERN = re.compile(r'session_id[:\s]+([a-zA-Z0-9_-]+)', re.IGNORECASE)
    
    # Decision Gate 標記
    DECISION_GATE_PATTERN = re.compile(
        r'(?:Decision Gate|DECISION GATE)[:\s]*(.+?)(?:\n|$)',
        re.IGNORECASE
    )
    
    # 命令執行正則表達式
    COMMAND_PATTERN = re.compile(
        r'(?:執行命令|Command|執行)[:\s]*```?(.+?)```?',
        re.IGNORECASE
    )
    
    # 結果正則表達式
    RESULT_PATTERN = re.compile(
        r'(?:結果|Result)[:\s]*(.+?)(?:\n\n|\n##|\Z)',
        re.IGNORECASE
    )
    
    # 檢查通過/失敗狀態
    STATUS_PATTERN = re.compile(
        r'(✅|❌|PASS|FAIL|APPROVE|REJECT|通過|不通過)',
        re.IGNORECASE
    )
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.dev_log_path = self.project_path / "DEVELOPMENT_LOG.md"
    
    def check(self) -> DevLogCheckResult:
        """
        執行 DEVELOPMENT_LOG 檢查
        
        Returns:
            DevLogCheckResult: 檢查結果
        """
        errors = []
        warnings = []
        
        # 檢查檔案是否存在
        file_exists = self.dev_log_path.exists()
        
        if not file_exists:
            errors.append("DEVELOPMENT_LOG.md not found")
            return DevLogCheckResult(
                passed=False,
                file_exists=False,
                has_header=False,
                has_phase_records=False,
                decision_gates=[],
                session_ids=[],
                commands=[],
                errors=errors,
                warnings=warnings,
                details={"file_path": str(self.dev_log_path)}
            )
        
        # 讀取檔案內容
        try:
            content = self.dev_log_path.read_text(encoding='utf-8')
            lines = content.split('\n')
        except Exception as e:
            errors.append(f"Failed to read file: {e}")
            return DevLogCheckResult(
                passed=False,
                file_exists=True,
                has_header=False,
                has_phase_records=False,
                decision_gates=[],
                session_ids=[],
                commands=[],
                errors=errors,
                warnings=warnings,
                details={"error": str(e)}
            )
        
        # 檢查 header
        has_header = self._check_header(content)
        if not has_header:
            warnings.append("Missing proper header (e.g., ## Development Log)")
        
        # 檢查 Phase 記錄
        has_phase_records = self._check_phase_records(content)
        if not has_phase_records:
            warnings.append("No Phase records found")
        
        # 解析 session_id
        session_ids = self._extract_session_ids(lines)
        if not session_ids:
            warnings.append("No session_id records found (required for Phase 1-8)")
        
        # 解析 Decision Gate
        decision_gates = self._extract_decision_gates(lines)
        if not decision_gates:
            warnings.append("No Decision Gate records found")
        
        # 解析命令執行記錄
        commands = self._extract_commands(lines, content)
        
        # 檢查空泛記錄
        self._check_empty_records(content, errors)
        
        # 計算最終結果
        passed = len(errors) == 0
        
        return DevLogCheckResult(
            passed=passed,
            file_exists=file_exists,
            has_header=has_header,
            has_phase_records=has_phase_records,
            decision_gates=decision_gates,
            session_ids=session_ids,
            commands=commands,
            errors=errors,
            warnings=warnings,
            details={
                "file_path": str(self.dev_log_path),
                "total_lines": len(lines),
                "content_length": len(content)
            }
        )
    
    def _check_header(self, content: str) -> bool:
        """檢查是否有適當的 header"""
        # 檢查是否有 ## 開頭的標題
        return bool(re.search(r'^##\s+\w+', content, re.MULTILINE))
    
    def _check_phase_records(self, content: str) -> bool:
        """檢查是否有 Phase 記錄"""
        return "Phase" in content and "Quality Gate" in content
    
    def _extract_session_ids(self, lines: List[str]) -> List[SessionIdRecord]:
        """提取 session_id 記錄"""
        session_ids = []
        
        for i, line in enumerate(lines, 1):
            match = self.SESSION_ID_PATTERN.search(line)
            if match:
                # 嘗試識別 Agent 角色
                role = "Unknown"
                if "Agent A" in line or "DevOps" in line:
                    role = "Agent A (DevOps)"
                elif "Agent B" in line or "Architect" in line:
                    role = "Agent B (Architect)"
                elif "Risk" in line:
                    role = "Risk Analyst"
                elif "PM" in line:
                    role = "PM"
                
                session_ids.append(SessionIdRecord(
                    agent_role=role,
                    session_id=match.group(1),
                    line_number=i
                ))
        
        return session_ids
    
    def _extract_decision_gates(self, lines: List[str]) -> List[DecisionGateRecord]:
        """提取 Decision Gate 記錄"""
        decision_gates = []
        
        for i, line in enumerate(lines, 1):
            match = self.DECISION_GATE_PATTERN.search(line)
            if match:
                decision_text = match.group(1).strip()
                
                # 檢查是否確認
                confirmed = "APPROVE" in decision_text.upper() or "確認" in decision_text
                
                # 嘗試提取日期
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                date = date_match.group(0) if date_match else None
                
                decision_gates.append(DecisionGateRecord(
                    decision=decision_text,
                    session_id=None,  # 需要進一步解析
                    confirmed=confirmed,
                    date=date,
                    line_number=i
                ))
        
        return decision_gates
    
    def _extract_commands(
        self, 
        lines: List[str], 
        content: str
    ) -> List[CommandRecord]:
        """提取命令執行記錄"""
        commands = []
        
        for i, line in enumerate(lines, 1):
            match = self.COMMAND_PATTERN.search(line)
            if match:
                command = match.group(1).strip()
                
                # 檢查是否有實際輸出
                output_present = False
                result = None
                
                # 查找後續行是否有結果
                for j in range(i, min(i + 10, len(lines))):
                    next_line = lines[j]
                    if self.RESULT_PATTERN.search(next_line):
                        output_present = True
                        result = self.RESULT_PATTERN.search(next_line).group(1).strip()
                        break
                    # 如果看到新的執行命令，停止搜索
                    if self.COMMAND_PATTERN.search(next_line):
                        break
                
                commands.append(CommandRecord(
                    command=command,
                    output_present=output_present,
                    result=result,
                    line_number=i
                ))
        
        return commands
    
    def _check_empty_records(self, content: str, errors: List[str]):
        """檢查空泛記錄"""
        # 檢查常見的空泛記錄模式
        empty_patterns = [
            r'✅\s*$',  # 只有 emoji
            r'基線建立完成\s*$',  # 沒有實際結果
            r'通過\s*$',  # 沒有具體說明
        ]
        
        for pattern in empty_patterns:
            if re.search(pattern, content, re.MULTILINE):
                # 這是一個警告，不是錯誤
                pass


def run_check(
    project_path: Optional[str] = None,
    verbose: bool = True
) -> DevLogCheckResult:
    """
    執行 DEVELOPMENT_LOG 檢查
    
    Args:
        project_path: 專案根目錄路徑
        verbose: 是否輸出詳細資訊
        
    Returns:
        DevLogCheckResult: 檢查結果
    """
    if project_path is None:
        project_path = str(Path(__file__).parent.parent)
    
    checker = DevLogChecker(project_path)
    result = checker.check()
    
    if verbose:
        print(result.print_summary())
    
    return result


def main():
    """命令列入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Development Log Checker"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=None,
        help="Project root path"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (no verbose output)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--detail", "-d",
        action="store_true",
        help="Show detailed information"
    )
    
    args = parser.parse_args()
    
    result = run_check(
        project_path=args.project_path,
        verbose=not args.quiet
    )
    
    if args.json:
        print(result.to_json())
    
    if args.detail:
        print("\nDetailed Session IDs:")
        print("-" * 40)
        for sid in result.session_ids:
            print(f"  {sid.agent_role}: {sid.session_id} (line {sid.line_number})")
        
        print("\nDetailed Commands:")
        print("-" * 40)
        for cmd in result.commands:
            status = "✅" if cmd.output_present else "❌"
            print(f"  {status} {cmd.command}")
            if cmd.result:
                print(f"     Result: {cmd.result[:50]}...")
    
    # 返回適當的 exit code
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
