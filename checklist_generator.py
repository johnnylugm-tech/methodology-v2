#!/usr/bin/env python3
"""
Markdown Checklist Generator
從 Verification Gates 輸出人類可讀的 Markdown 格式報告
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class CheckStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    WARNING = "⚠️"
    SKIP = "⏭️"


@dataclass
class CheckItem:
    name: str
    status: CheckStatus
    message: str = ""


class MarkdownChecklist:
    """Markdown 格式檢查清單生成器"""

    def __init__(self, title: str = "Verification Report"):
        self.title = title
        self.sections: Dict[str, List[CheckItem]] = {}

    def add(self, section: str, name: str, status: CheckStatus, message: str = ""):
        if section not in self.sections:
            self.sections[section] = []
        self.sections[section].append(CheckItem(name, status, message))

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", ""]
        lines.append(f"**時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

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
    cl = MarkdownChecklist("Test Report")
    cl.add("Code Quality", "語法檢查", CheckStatus.PASS)
    cl.add("Testing", "單元測試", CheckStatus.PASS)
    cl.add("Testing", "整合測試", CheckStatus.FAIL, "2 tests failed")
    print(cl.to_markdown())
