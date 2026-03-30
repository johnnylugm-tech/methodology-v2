#!/usr/bin/env python3
"""
Claims Verifier - 聲稱 vs 實際 測量系統

功能：
1. 測量 Sub-agent 使用數量
2. 測量代碼行數
3. 測量 Quality Gate 執行與否
4. 比對聲稱值 vs 實際值

使用方式：
    from quality_gate.claims_verifier import ClaimsVerifier
    
    verifier = ClaimsVerifier("/path/to/project")
    result = verifier.verify_code_lines(claimed=1000)
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ClaimsVerifier:
    """
    聲稱 vs 實際 測量系統
    
    用於驗證 DEVELOPMENT_LOG 中聲稱的數值是否與實際測量值匹配。
    這是防止 Phase 3 摻假問題的核心機制。
    """
    
    def __init__(self, project_path: str):
        """
        初始化 ClaimsVerifier
        
        Args:
            project_path: 專案根目錄路徑
        """
        self.project_path = Path(project_path)
        self.development_log_path = self.project_path / "DEVELOPMENT_LOG.md"
    
    def verify_subagent_usage(self) -> Dict:
        """
        驗證 Sub-agent 使用數量
        
        讀取 DEVELOPMENT_LOG 中聲稱的 Sub-agent 數量，
        驗證是否真的有使用（需從 sessions_history 或 log 驗證）
        
        Returns:
            Dict: {
                "match": bool,           # 聲稱數量與實際是否匹配
                "claimed": int,          # 聲稱的 Sub-agent 數量
                "actual": int,          # 實際測量的 Sub-agent 數量
                "details": Dict         # 詳細資訊
            }
        """
        if not self.development_log_path.exists():
            return {
                "match": False,
                "claimed": 0,
                "actual": 0,
                "error": "DEVELOPMENT_LOG.md not found"
            }
        
        content = self.development_log_path.read_text(encoding="utf-8")
        
        # 1. 找出聲稱的 Sub-agent 數量
        # 查找模式："使用 X 個 Sub-agent" 或 "發動 N 個 Sub-agent"
        claimed_patterns = [
            r"使用\s*(\d+)\s*個?[Ss]ub[-]?[Aa]gent",
            r"發動\s*(\d+)\s*個?[Ss]ub[-]?[Aa]gent",
            r"啟動\s*(\d+)\s*個?[Ss]ub[-]?[Aa]gent",
            r"[Ss]ub[-]?[Aa]gent.*?數量[：:]\s*(\d+)",
        ]
        
        claimed_count = 0
        for pattern in claimed_patterns:
            matches = re.findall(pattern, content)
            if matches:
                claimed_count = max(claimed_count, int(matches[-1]))
        
        # 2. 驗證是否為 Sub-agent（runtime=subagent）
        # 查找 "session_id: xxx" 或 "runtime: subagent" 等標記
        actual_count = 0
        
        # 查找 session 相關標記
        session_patterns = [
            r"[Ss]ession.*?[Ii][Dd][：:]\s*([a-zA-Z0-9-]+)",
            r"[Rr]untime[：:]\s*[Ss]ub[-]?[Aa]gent",
            r"Sub[-]?[Aa]gent.*?[Ss]ession",
        ]
        
        unique_sessions = set()
        for pattern in session_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # 如果是 session_id，檢查是否有 Sub-agent 標記
                if re.match(r'^[a-zA-Z0-9-]+$', match) and len(match) > 10:
                    # 這可能是 session_id
                    # 檢查上下文是否有 Sub-agent 標記
                    session_pattern = re.escape(match)
                    context = re.search(rf'.{{0,100}}{session_pattern}.{{0,100}}', content, re.DOTALL)
                    if context and ('subagent' in context.group(0).lower() or 'sub-agent' in context.group(0).lower()):
                        unique_sessions.add(match)
        
        actual_count = len(unique_sessions) if unique_sessions else 0
        
        # 如果沒有找到明確的 session_id，嘗試計數 Sub-agent 相關段落
        if actual_count == 0:
            # 計算 Developer/Reviewer/Tester 等角色的出現次數
            role_patterns = [
                r"[Dd]eveloper.*?[Ss]ession",
                r"[Rr]eviewer.*?[Ss]ession",
                r"[Tt]ester.*?[Ss]ession",
            ]
            for pattern in role_patterns:
                matches = re.findall(pattern, content)
                actual_count += len(matches)
        
        # 3. 判斷是否匹配（允許 20% 誤差）
        diff = abs(claimed_count - actual_count)
        tolerance = max(1, claimed_count * 0.2) if claimed_count > 0 else 1
        match = diff <= tolerance
        
        return {
            "match": match,
            "claimed": claimed_count,
            "actual": actual_count,
            "details": {
                "unique_sessions": list(unique_sessions),
                "difference": diff,
                "tolerance": tolerance
            }
        }
    
    def verify_code_lines(self, claimed: Optional[int] = None) -> Dict:
        """
        驗證代碼行數
        
        測量實際代碼行數，並與聲稱值比對。
        
        Args:
            claimed: 聲稱的代碼行數（可選，如果不提供則從 DEVELOPMENT_LOG 讀取）
            
        Returns:
            Dict: {
                "match": bool,           # 聲稱數量與實際是否匹配
                "claimed": int,          # 聲稱的代碼行數
                "actual": int,          # 實際測量的代碼行數
                "diff_percent": float,  # 差異百分比
                "details": Dict         # 詳細資訊
            }
        """
        # 如果沒有提供 claimed，嘗試從 DEVELOPMENT_LOG 讀取
        if claimed is None:
            if self.development_log_path.exists():
                content = self.development_log_path.read_text(encoding="utf-8")
                patterns = [
                    r"代碼行數[：:]\s*(\d+)",
                    r"程式碼[：:]\s*(\d+)\s*行",
                    r"[Cc]ode.*?[Ll]ines[：:]\s*(\d+)",
                    r"lines.*?of.*?code[：:]\s*(\d+)",
                ]
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        claimed = int(matches[-1])
                        break
        
        # 測量實際代碼行數
        actual, details = self._measure_code_lines()
        
        # 計算差異百分比
        if claimed and actual:
            diff_percent = abs(claimed - actual) / claimed * 100
        else:
            diff_percent = 0.0
        
        # 判斷是否匹配（允許 5% 誤差）
        match = diff_percent <= 5.0
        
        return {
            "match": match,
            "claimed": claimed or 0,
            "actual": actual,
            "diff_percent": diff_percent,
            "details": details
        }
    
    def _measure_code_lines(self) -> Tuple[int, Dict]:
        """
        測量實際代碼行數
        
        Returns:
            Tuple[int, Dict]: (總行數, 詳細資訊)
        """
        total_lines = 0
        file_counts = {}
        
        # 測量多個可能的代碼目錄
        code_dirs = [
            "03-development",
            "src",
            "app",
            "lib",
        ]
        
        for code_dir in code_dirs:
            dir_path = self.project_path / code_dir
            if dir_path.exists():
                py_files = list(dir_path.rglob("*.py"))
                py_files = [f for f in py_files if "__pycache__" not in str(f)]
                
                dir_total = 0
                for py_file in py_files:
                    try:
                        lines = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
                        dir_total += lines
                        rel_path = str(py_file.relative_to(self.project_path))
                        file_counts[rel_path] = lines
                    except Exception:
                        pass
                
                if dir_total > 0:
                    total_lines += dir_total
        
        # 如果沒有找到任何代碼，嘗試測量根目錄
        if total_lines == 0:
            py_files = [f for f in self.project_path.glob("*.py") if "__pycache__" not in str(f.name)]
            for py_file in py_files:
                try:
                    lines = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
                    total_lines += lines
                    file_counts[py_file.name] = lines
                except Exception:
                    pass
        
        return total_lines, {
            "files_count": len(file_counts),
            "files": file_counts
        }
    
    def verify_quality_gate_executed(self) -> Dict:
        """
        驗證 Quality Gate 是否執行
        
        檢查 DEVELOPMENT_LOG 是否有實際命令輸出，
        不是只有「已通過」，而是有 python3 quality_gate/... 輸出。
        
        Returns:
            Dict: {
                "executed": bool,               # 是否執行
                "command_outputs": List[str],   # 實際命令輸出
                "commands_found": List[str],    # 找到的命令
                "details": Dict                 # 詳細資訊
            }
        """
        if not self.development_log_path.exists():
            return {
                "executed": False,
                "command_outputs": [],
                "commands_found": [],
                "error": "DEVELOPMENT_LOG.md not found"
            }
        
        content = self.development_log_path.read_text(encoding="utf-8")
        
        # 1. 查找 Quality Gate 命令
        qg_patterns = [
            r"python3\s+quality_gate/\S+\.py",
            r"python\s+quality_gate/\S+\.py",
            r"pytest.*?quality_gate",
            r"quality_gate.*?(?:run|check|enforce)",
        ]
        
        commands_found = []
        for pattern in qg_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            commands_found.extend(matches)
        
        # 2. 查找命令輸出（不是只有「通過」，而是有實際結果）
        # 尋找像是分數、錯誤、警告等實際輸出
        output_patterns = [
            r"分數[：:]\s*\d+",
            r"[Ss]core[：:]\s*\d+",
            r"passed",
            r"failed",
            r"error",
            r"warning",
            r"✓|✅|✗|❌",
            r"Compliance.*?\d+%",
            r"\d+\.\d+%",
        ]
        
        command_outputs = []
        for pattern in output_patterns:
            matches = re.findall(pattern, content)
            command_outputs.extend(matches)
        
        # 3. 判斷是否真正執行
        # 標準：
        # - 有找到 Quality Gate 命令
        # - 有找到實際輸出（非「已通過」這種模糊描述）
        executed = len(commands_found) > 0 and len(command_outputs) >= 2
        
        return {
            "executed": executed,
            "command_outputs": list(set(command_outputs)),
            "commands_found": list(set(commands_found)),
            "details": {
                "command_count": len(commands_found),
                "output_count": len(command_outputs)
            }
        }
    
    def verify_stage_pass_exists(self, phase: int) -> Dict:
        """
        驗證 STAGE_PASS 是否存在
        
        檢查特定 Phase 的 STAGE_PASS 是否存在。
        
        Args:
            phase: Phase 編號
            
        Returns:
            Dict: {
                "exists": bool,           # STAGE_PASS 是否存在
                "path": str,             # 路徑
                "content_valid": bool,   # 內容是否有效
                "details": Dict          # 詳細資訊
            }
        """
        # 可能的 STAGE_PASS 檔案位置
        possible_paths = [
            self.project_path / f"STAGE_PASS_PHASE{phase}.md",
            self.project_path / f"Phase{phase}_STAGE_PASS.md",
            self.project_path / "STAGE_PASS.md",
            self.project_path / ".methodology" / f"stage_pass_phase{phase}.md",
        ]
        
        found_path = None
        for path in possible_paths:
            if path.exists():
                found_path = path
                break
        
        if not found_path:
            return {
                "exists": False,
                "path": None,
                "content_valid": False,
                "details": {"searched_paths": [str(p) for p in possible_paths]}
            }
        
        # 檢查內容是否有效
        try:
            content = found_path.read_text(encoding="utf-8")
            # 有效的 STAGE_PASS 應該包含 Phase 編號和通過狀態
            content_valid = f"Phase {phase}" in content or f"Phase{phase}" in content.lower()
        except Exception as e:
            content_valid = False
        
        return {
            "exists": True,
            "path": str(found_path),
            "content_valid": content_valid,
            "details": {"file_size": found_path.stat().st_size if found_path.exists() else 0}
        }
    
    def verify_all(self, phase: int) -> Dict:
        """
        執行所有驗證檢查
        
        這是主要入口點，執行所有 Claims 驗證。
        
        Args:
            phase: Phase 編號
            
        Returns:
            Dict: 包含所有驗證結果的綜合報告
        """
        return {
            "subagent_usage": self.verify_subagent_usage(),
            "code_lines": self.verify_code_lines(),
            "quality_gate_executed": self.verify_quality_gate_executed(),
            "stage_pass": self.verify_stage_pass_exists(phase)
        }


# ===== 快速函式入口 =====

def verify_claims(project_path: str, phase: int) -> Dict:
    """
    快速執行所有 Claims 驗證
    
    Args:
        project_path: 專案根目錄路徑
        phase: Phase 編號
        
    Returns:
        Dict: 驗證結果
    """
    verifier = ClaimsVerifier(project_path)
    return verifier.verify_all(phase)


def verify_code_lines(project_path: str, claimed: Optional[int] = None) -> Dict:
    """
    快速驗證代碼行數
    
    Args:
        project_path: 專案根目錄路徑
        claimed: 聲稱的代碼行數
        
    Returns:
        Dict: 驗證結果
    """
    verifier = ClaimsVerifier(project_path)
    return verifier.verify_code_lines(claimed)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python claims_verifier.py <project_path> [phase]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    phase = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    result = verify_claims(project_path, phase)
    print(f"Claims Verification Results for Phase {phase}:")
    print(f"  Sub-agent Usage Match: {result['subagent_usage']['match']}")
    print(f"    Claimed: {result['subagent_usage']['claimed']}, Actual: {result['subagent_usage']['actual']}")
    print(f"  Code Lines Match: {result['code_lines']['match']}")
    print(f"    Claimed: {result['code_lines']['claimed']}, Actual: {result['code_lines']['actual']} ({result['code_lines']['diff_percent']:.1f}%)")
    print(f"  Quality Gate Executed: {result['quality_gate_executed']['executed']}")
    print(f"  STAGE_PASS Exists: {result['stage_pass']['exists']}")