#!/usr/bin/env python3
"""
KnowledgeCurator — 知識管理模組

功能：
- 按需載入 SKILL.md（Lazy Load）
- 知識版本追蹤
- 領域知識搜尋
- 自動注入 Context

用法：
    from knowledge_curator import KnowledgeCurator

    kc = KnowledgeCurator(skills_dir="skills")
    skill = kc.load_skill("methodology-v2")
    kc.inject_context(skill)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class SkillStatus(Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class Skill:
    """Skill 知識單元"""
    name: str
    version: str
    path: Path
    status: SkillStatus = SkillStatus.ACTIVE
    description: str = ""
    tags: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    coverage: float = 1.0  # 覆蓋率 0-1


@dataclass
class KnowledgeEntry:
    """知識條目"""
    skill_name: str
    section: str  # e.g., "Phase 1", "A/B 協作"
    content: str
    keywords: List[str] = field(default_factory=list)
    fr_ids: List[str] = field(default_factory=list)  # 對應的 FR-ID


class KnowledgeCurator:
    """
    知識管理器

    職責：
    - 維護 SKILL 知識庫
    - 按需載入知識（Lazy Load）
    - 知識版本追蹤
    - 領域知識搜尋
    """

    DEFAULT_SKILL_PATH = Path(__file__).parent / "SKILL.md"
    SKILL_TEMPLATES_PATH = Path(__file__).parent / "SKILL_TEMPLATES.md"

    def __init__(self, skill_path: str = None, state_path: str = None):
        """
        初始化 KnowledgeCurator

        Args:
            skill_path: SKILL.md 路徑（預設使用內建路徑）
            state_path: state.json 路徑（用於追蹤已載入的知識）
        """
        self.skill_path = Path(skill_path) if skill_path else self.DEFAULT_SKILL_PATH
        self.state_path = Path(state_path) if state_path else Path(".methodology/state.json")
        self._cache = {}  # 知識緩存
        self._loaded_skills = []  # 已載入的技能

    def load_skill(self, skill_name: str = "methodology-v2", force_reload: bool = False) -> str:
        """
        按需載入 SKILL 知識

        Args:
            skill_name: 技能名稱
            force_reload: 是否強制重新載入

        Returns:
            str: SKILL 內容
        """
        if skill_name in self._cache and not force_reload:
            return self._cache[skill_name]

        skill_path = self._find_skill_path(skill_name)
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")

        content = skill_path.read_text(encoding="utf-8")
        self._cache[skill_name] = content
        self._loaded_skills.append(skill_name)

        # 更新 state.json
        self._update_knowledge_state(skill_name, skill_path)

        return content

    def _find_skill_path(self, skill_name: str) -> Path:
        """查找 Skill 路徑"""
        # 先查找專案目錄
        if Path(skill_name).exists():
            return Path(skill_name)

        # 查找 skills/ 目錄
        skills_dir = Path("skills")
        if skills_dir.exists():
            skill_path = skills_dir / skill_name / "SKILL.md"
            if skill_path.exists():
                return skill_path

        # 回退到預設路徑
        return self.skill_path

    def _update_knowledge_state(self, skill_name: str, skill_path: Path):
        """更新 state.json 中的知識狀態"""
        if not self.state_path.exists():
            return

        try:
            state = json.loads(self.state_path.read_text())
            knowledge_state = state.get("knowledge_state", {})

            knowledge_state[skill_name] = {
                "path": str(skill_path),
                "loaded_at": datetime.now().isoformat(),
                "version": self._extract_version(skill_path)
            }

            state["knowledge_state"] = knowledge_state
            self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        except Exception:
            pass  # 不影響主流程

    def _extract_version(self, path: Path) -> str:
        """從 SKILL.md 提取版本"""
        try:
            first_line = path.read_text(encoding="utf-8").split("\n")[0]
            match = re.search(r"v(\d+\.\d+)", first_line)
            return match.group(0) if match else "unknown"
        except:
            return "unknown"

    def search_skills(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        搜尋相關 Skills

        Args:
            query: 搜尋關鍵字
            max_results: 最大回傳數量

        Returns:
            List[Dict]: 符合的技能列表
        """
        results = []
        keywords = query.lower().split()

        # 搜尋 SKILL.md 中的標題和關鍵字
        try:
            content = self.load_skill("methodology-v2")
            lines = content.split("\n")

            current_section = ""
            for line in lines:
                if line.startswith("## "):
                    current_section = line.replace("## ", "").strip()

                if any(kw in line.lower() for kw in keywords):
                    results.append({
                        "section": current_section,
                        "line": line.strip(),
                        "match": query
                    })

        except Exception:
            pass

        return results[:max_results]

    def extract_section(self, skill_name: str, section_name: str) -> str:
        """
        提取特定章節

        Args:
            skill_name: 技能名稱
            section_name: 章節名（如 "Phase 3", "A/B 協作"）

        Returns:
            str: 章節內容
        """
        content = self.load_skill(skill_name)
        lines = content.split("\n")

        result_lines = []
        in_section = False

        for line in lines:
            if line.startswith("## ") and section_name.lower() in line.lower():
                in_section = True
                result_lines.append(line)
            elif line.startswith("## ") and in_section:
                break  # 到下一章節
            elif in_section:
                result_lines.append(line)

        return "\n".join(result_lines)

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """
        取得知識庫摘要

        Returns:
            Dict: 知識狀態摘要
        """
        return {
            "loaded_skills": list(set(self._loaded_skills)),
            "cache_size": len(self._cache),
            "skill_path": str(self.skill_path),
            "last_updated": datetime.now().isoformat()
        }

    def inject_to_messages(self, skill_name: str, role: str = "system") -> List[Dict]:
        """
        將知識轉為 messages 格式（用於 LLM 上下文）

        Args:
            skill_name: 技能名稱
            role: message role（system/user/assistant）

        Returns:
            List[Dict]: 可直接傳入 LLM 的 messages
        """
        content = self.load_skill(skill_name)

        return [{
            "role": role,
            "content": f"[Knowledge: {skill_name}]\n\n{content}"
        }]

    def verify_coverage(self, required_frs: List[str], skill_name: str = "methodology-v2") -> Dict:
        """
        驗證知識覆蓋率

        Args:
            required_frs: 需要覆蓋的 FR-ID 列表
            skill_name: 技能名稱

        Returns:
            Dict: {covered: [...], missing: [...], coverage: float}
        """
        content = self.load_skill(skill_name)

        covered = []
        missing = []

        for fr in required_frs:
            if f"FR-{fr}" in content or f"FR-{fr.zfill(2)}" in content:
                covered.append(fr)
            else:
                missing.append(fr)

        coverage = len(covered) / len(required_frs) if required_frs else 1.0

        return {
            "covered": covered,
            "missing": missing,
            "coverage": coverage,
            "status": "PASS" if coverage >= 0.9 else "FAIL"
        }


# CLI 介面
def main():
    import argparse

    parser = argparse.ArgumentParser(description="KnowledgeCurator CLI")
    parser.add_argument("command", choices=["load", "search", "verify", "summary"])
    parser.add_argument("--skill", default="methodology-v2")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--section", help="Extract section")
    parser.add_argument("--frs", help="Comma-separated FR IDs")

    args = parser.parse_args()

    kc = KnowledgeCurator()

    if args.command == "load":
        content = kc.load_skill(args.skill)
        print(f"Loaded {args.skill} ({len(content)} chars)")

    elif args.command == "search":
        results = kc.search_skills(args.query)
        for r in results:
            print(f"[{r['section']}] {r['line']}")

    elif args.command == "verify":
        frs = args.frs.split(",") if args.frs else []
        result = kc.verify_coverage(frs)
        print(f"Coverage: {result['coverage']:.1%}")
        print(f"Missing: {result['missing']}")

    elif args.command == "summary":
        print(json.dumps(kc.get_knowledge_summary(), indent=2))


if __name__ == "__main__":
    main()
