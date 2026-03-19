#!/usr/bin/env python3
"""
Doc Generator - 文檔自動生成

根據代碼自動生成文檔
"""

import os
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class DocItem:
    """文檔項目"""
    name: str
    type: str  # class, function, method
    docstring: str
    params: List[Dict] = field(default_factory=list)
    returns: Optional[Dict] = None
    examples: List[str] = field(default_factory=list)


class DocGenerator:
    """文檔生成器"""
    
    # 語言支持
    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
    }
    
    def __init__(self):
        """初始化"""
        self.items: List[DocItem] = []
        self.language = "python"
    
    def parse_file(self, file_path: str) -> List[DocItem]:
        """
        解析檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            文檔項目列表
        """
        ext = Path(file_path).suffix
        self.language = self.SUPPORTED_EXTENSIONS.get(ext, "python")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
        
        if self.language == "python":
            return self._parse_python(content)
        else:
            return []
    
    def _parse_python(self, content: str) -> List[DocItem]:
        """解析 Python 代碼"""
        items = []
        
        # 解析類別
        class_pattern = r'class (\w+)(?:\(([^)]+)\))?:'
        class_matches = re.finditer(class_pattern, content)
        
        for match in class_matches:
            name = match.group(1)
            items.append(DocItem(
                name=name,
                type="class",
                docstring=self._extract_docstring(content, match.end()),
                params=[]
            ))
        
        # 解析函數
        func_pattern = r'def (\w+)\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        func_matches = re.finditer(func_pattern, content)
        
        for match in func_matches:
            name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str:
                for p in params_str.split(','):
                    p = p.strip()
                    if p:
                        # 處理帶預設值的參數
                        p_name = p.split('=')[0].strip()
                        params.append({"name": p_name, "type": "any"})
            
            return_type = match.group(3)
            
            items.append(DocItem(
                name=name,
                type="function",
                docstring=self._extract_docstring(content, match.end()),
                params=params,
                returns={"type": return_type.strip() if return_type else "None"} if return_type else None
            ))
        
        return items
    
    def _extract_docstring(self, content: str, pos: int) -> str:
        """提取文檔字串"""
        # 找下一個非空行
        lines = content[pos:].split('\n')
        
        docstring = ""
        in_docstring = False
        quote_char = None
        
        for line in lines:
            stripped = line.strip()
            
            # 檢查開始
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    in_docstring = True
                    quote_char = stripped[:3]
                    if stripped.count(quote_char) >= 2:
                        # 單行 docstring
                        docstring = stripped[3:-3].strip()
                        break
                elif stripped and not stripped.startswith('#'):
                    break
            
            # 收集 docstring
            if in_docstring:
                if quote_char in stripped:
                    in_docstring = False
                    break
                docstring += line.strip() + " "
        
        return docstring.strip()
    
    def generate_markdown(self, items: List[DocItem], title: str = "API Documentation") -> str:
        """
        生成 Markdown 文檔
        
        Args:
            items: 文檔項目
            title: 標題
            
        Returns:
            Markdown 字串
        """
        lines = [
            f"# {title}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        # 按類型分組
        classes = [i for i in items if i.type == "class"]
        functions = [i for i in items if i.type == "function"]
        
        if classes:
            lines.append("## Classes\n")
            for item in classes:
                lines.extend(self._format_item(item))
                lines.append("")
        
        if functions:
            lines.append("## Functions\n")
            for item in functions:
                lines.extend(self._format_item(item))
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_item(self, item: DocItem) -> List[str]:
        """格式化項目"""
        lines = []
        
        # 標題
        lines.append(f"### {item.name}")
        lines.append("")
        
        # 描述
        if item.docstring:
            lines.append(f"{item.docstring}")
            lines.append("")
        
        # 參數
        if item.params:
            lines.append("**Parameters:**")
            lines.append("")
            lines.append("| Name | Type |")
            lines.append("|------|------|")
            for p in item.params:
                lines.append(f"| {p['name']} | {p.get('type', 'any')} |")
            lines.append("")
        
        # 返回值
        if item.returns:
            lines.append(f"**Returns:** `{item.returns.get('type', 'any')}`")
            lines.append("")
        
        return lines
    
    def generate_readme(self, file_paths: List[str], output_path: str = None) -> str:
        """
        生成 README
        
        Args:
            file_paths: 檔案路徑列表
            output_path: 輸出路徑
            
        Returns:
            README 字串
        """
        all_items = []
        
        for path in file_paths:
            items = self.parse_file(path)
            all_items.extend(items)
        
        # 生成
        readme = self.generate_markdown(all_items, "Documentation")
        
        # 寫入檔案
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(readme)
            print(f"Generated: {output_path}")
        
        return readme
    
    def scan_directory(self, directory: str, pattern: str = "*.py") -> List[DocItem]:
        """
        掃描目錄
        
        Args:
            directory: 目錄
            pattern: 檔案匹配
            
        Returns:
            文檔項目列表
        """
        items = []
        
        path = Path(directory)
        for file_path in path.rglob(pattern):
            if file_path.is_file():
                file_items = self.parse_file(str(file_path))
                items.extend(file_items)
        
        return items


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python doc_generator.py <file.py>")
        print("  python doc_generator.py <directory>")
        sys.exit(1)
    
    target = sys.argv[1]
    generator = DocGenerator()
    
    path = Path(target)
    
    if path.is_file():
        items = generator.parse_file(target)
        print(generator.generate_markdown(items, f"Documentation - {path.name}"))
    elif path.is_dir():
        items = generator.scan_directory(target)
        print(generator.generate_markdown(items, f"Documentation - {path.name}"))
