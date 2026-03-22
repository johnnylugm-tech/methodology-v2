#!/usr/bin/env python3
"""
Markdown Checklist Generator
從 Verification Gates 輸出人類可讀的 Markdown 格式報告

使用方法:
    from checklist_generator import MarkdownChecklist, CheckStatus
    
    cl = MarkdownChecklist("Report")
    cl.add("Section", "Check", CheckStatus.PASS)
    print(cl.to_markdown())
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
from enum import Enum


class CheckStatus(Enum):
    """檢查狀態枚舉"""
    PASS = "✅"
    FAIL = "❌"
    WARNING = "⚠️"
    SKIP = "⏭️"


@dataclass
class CheckItem:
    """檢查項目"""
    name: str
    status: CheckStatus
    message: str = ""


class MarkdownChecklist:
    """Markdown 格式檢查清單生成器
    
    用於從驗證關卡輸出人類可讀的 Markdown 報告
    
    Example:
        cl = MarkdownChecklist("Pre-merge Report")
        cl.add("Code Quality", "Syntax", CheckStatus.PASS)
        print(cl.to_markdown())
    """
    
    def __init__(self, title: str = "Verification Report"):
        """初始化檢查清單
        
        Args:
            title: 報告標題
        """
        self.title = title
        self.sections: Dict[str, List[CheckItem]] = {}

    def add(self, section: str, name: str, status: CheckStatus, message: str = ""):
        """新增檢查項目
        
        Args:
            section: 所屬區塊
            name: 檢查項目名稱
            status: 檢查狀態
            message: 補充訊息
        """
        if section not in self.sections:
            self.sections[section] = []
        self.sections[section].append(CheckItem(name, status, message))

    def _count_by_status(self) -> Dict[str, int]:
        """計算各狀態數量"""
        counts = {"pass": 0, "fail": 0, "warning": 0, "skip": 0}
        for items in self.sections.values():
            for item in items:
                if item.status == CheckStatus.PASS:
                    counts["pass"] += 1
                elif item.status == CheckStatus.FAIL:
                    counts["fail"] += 1
                elif item.status == CheckStatus.WARNING:
                    counts["warning"] += 1
                elif item.status == CheckStatus.SKIP:
                    counts["skip"] += 1
        return counts

    def to_markdown(self) -> str:
        """轉換為 Markdown 格式
        
        Returns:
            Markdown 格式字串
        """
        lines = [f"# {self.title}", ""]
        lines.append(f"**時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        counts = self._count_by_status()
        total = sum(counts.values())
        passed = counts["pass"]
        pass_rate = round(passed / total * 100, 1) if total > 0 else 0
        
        lines.append(f"## 摘要")
        lines.append(f"- 總檢查項: {total}")
        lines.append(f"- ✅ 通過: {counts['pass']}")
        lines.append(f"- ❌ 失敗: {counts['fail']}")
        lines.append(f"- ⚠️ 警告: {counts['warning']}")
        lines.append(f"- 通過率: {pass_rate}%")
        lines.append("")
        
        # Details by section
        for section, items in self.sections.items():
            lines.append(f"## {section}")
            lines.append("")
            for item in items:
                lines.append(f"- {item.status.value} **{item.name}**")
                if item.message:
                    lines.append(f"  - {item.message}")
            lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    cl = MarkdownChecklist("Test Report")
    cl.add("Code Quality", "語法檢查", CheckStatus.PASS)
    cl.add("Testing", "單元測試", CheckStatus.PASS)
    cl.add("Testing", "整合測試", CheckStatus.FAIL, "2 tests failed")
    print(cl.to_markdown())
