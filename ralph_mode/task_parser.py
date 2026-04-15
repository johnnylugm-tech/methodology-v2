"""
Ralph Mode - Task Output Parser

從 sub-agent task description 解析預期輸出檔案列表。

Author: methodology-v2
Version: 1.0.0
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any


class TaskOutputParser:
    """
    Task Output 解析器
    
    解析 task description 中的 OUTPUT 段落，提取預期檔案列表。
    
    Task Description 格式：
    ```
    TASK: FR-01 processing
    OUTPUT:
    - 03-development/src/processing/fr01.py
    - tests/test_fr01.py
    
    ## Other content
    ```
    
    Example:
        >>> parser = TaskOutputParser()
        >>> outputs = parser.parse(task_text)
        >>> print(outputs)
        ['03-development/src/processing/fr01.py', 'tests/test_fr01.py']
    """
    
    OUTPUT_PATTERN = re.compile(
        r'^OUTPUT:\s*\n((?:[-\s].+\n)+)',
        re.MULTILINE
    )
    
    FILE_PATH_PATTERN = re.compile(
        r'^\s*[-*]\s*(.+?)\s*$',
        re.MULTILINE
    )
    
    def parse(self, task_text: str) -> List[str]:
        """
        解析 task text，提取 OUTPUT 段落中的檔案列表
        
        Args:
            task_text: task description 文字
            
        Returns:
            檔案路徑列表（可能是相對路徑）
        """
        if not task_text:
            return []
        
        # 找 OUTPUT 段落
        match = self.OUTPUT_PATTERN.search(task_text)
        if not match:
            return []
        
        output_block = match.group(1)
        
        # 解析每個檔案路徑
        paths = []
        for line in output_block.split('\n'):
            file_match = self.FILE_PATH_PATTERN.match(line)
            if file_match:
                path = file_match.group(1).strip()
                if path:
                    paths.append(path)
        
        return paths
    
    def parse_to_absolute(self, task_text: str, repo_path: Path) -> List[Path]:
        """
        解析並轉換為絕對路徑
        
        Args:
            task_text: task description
            repo_path: 專案根目錄
            
        Returns:
            絕對路徑列表
        """
        relative_paths = self.parse(task_text)
        
        absolute_paths = []
        for rel_path in relative_paths:
            # 如果是相對路徑，相對於 repo_path
            if not Path(rel_path).is_absolute():
                abs_path = repo_path / rel_path
            else:
                abs_path = Path(rel_path)
            absolute_paths.append(abs_path)
        
        return absolute_paths
    
    def validate_outputs_exist(self, task_text: str, repo_path: Path) -> Dict[str, Any]:
        """
        驗證 OUTPUT 中列出的檔案是否存在
        
        Args:
            task_text: task description
            repo_path: 專案根目錄
            
        Returns:
            {
                "all_exist": bool,
                "missing": List[str],
                "existing": List[str]
            }
        """
        relative_paths = self.parse(task_text)
        
        missing = []
        existing = []
        
        for rel_path in relative_paths:
            if not Path(rel_path).is_absolute():
                abs_path = repo_path / rel_path
            else:
                abs_path = Path(rel_path)
            
            if abs_path.exists():
                existing.append(str(abs_path))
            else:
                missing.append(str(abs_path))
        
        return {
            "all_exist": len(missing) == 0,
            "missing": missing,
            "existing": existing,
            "total": len(relative_paths),
            "found": len(existing)
        }
