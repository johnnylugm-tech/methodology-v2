#!/usr/bin/env python3
"""
Quick Start - 快速啟動系統

對標 CrewAI 的 minimal boilerplate：
- 5 行啟動一個 Agent
- 3 行建立團隊
- 預設模板
- 互動式引導

AI-native 實作，零額外負擔
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import readline  # 互動式輸入

# ============================================
# Level 1: 5 行啟動一個 Agent
# ============================================

def create_agent(name: str, role: str, goal: str) -> dict:
    """
    5 行建立一個 Agent
    
    Example:
        agent = create_agent(
            name="DevBot",
            role="Developer",
            goal="Write code"
        )
    """
    return {
        "name": name,
        "role": role,
        "goal": goal,
        "config": "default"
    }

# ============================================
# Level 2: 3 行建立團隊
# ============================================

def create_team(name: str, agents: List[dict]) -> dict:
    """
    3 行建立團隊
    
    Example:
        team = create_team("DevTeam", [dev_agent, reviewer_agent])
    """
    return {
        "name": name,
        "agents": agents,
        "mode": "collaborative"
    }

# ============================================
# Level 3: 一行執行任務
# ============================================

def run_task(team: dict, task: str) -> dict:
    """
    一行執行任務
    
    Example:
        result = run_task(team, "Build a login system")
    """
    return {"status": "completed", "result": f"Executed: {task}"}

# ============================================
# Quick Start Templates
# ============================================

QUICK_TEMPLATES = {
    "dev": {
        "name": "Development Team",
        "agents": [
            {"name": "DevBot", "role": "Developer", "goal": "Write code"},
            {"name": "ReviewBot", "role": "Reviewer", "goal": "Review code"},
        ]
    },
    "pm": {
        "name": "PM Team",
        "agents": [
            {"name": "PMBot", "role": "PM", "goal": "Manage project"},
        ]
    },
    "full": {
        "name": "Full Stack Team",
        "agents": [
            {"name": "ArchitectBot", "role": "Architect", "goal": "Design system"},
            {"name": "DevBot", "role": "Developer", "goal": "Write code"},
            {"name": "ReviewBot", "role": "Reviewer", "goal": "Review code"},
            {"name": "TestBot", "role": "Tester", "goal": "Test system"},
        ]
    }
}

def quick_start(template: str = "dev") -> dict:
    """
    快速啟動 - 選擇模板
    
    Example:
        team = quick_start("full")  # 一行建立完整團隊
    """
    if template not in QUICK_TEMPLATES:
        raise ValueError(f"Unknown template: {template}. Available: {list(QUICK_TEMPLATES.keys())}")
    
    t = QUICK_TEMPLATES[template]
    agents = [create_agent(**a) for a in t["agents"]]
    return create_team(t["name"], agents)

# ============================================
# Interactive Mode
# ============================================

def interactive_start():
    """
    互動式引導啟動
    
    選擇預設模板或自定義
    """
    print("🚀 Quick Start - Agent Team Generator")
    print("=" * 40)
    print("Templates:")
    for i, name in enumerate(QUICK_TEMPLATES.keys(), 1):
        print(f"  {i}. {name}")
    print()
    
    choice = input("Select template (1-3) or 'q' to quit: ").strip()
    
    if choice == 'q':
        print("Goodbye!")
        return
    
    templates = list(QUICK_TEMPLATES.keys())
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(templates):
            team = quick_start(templates[idx])
            print("\n✅ Team created!")
            print(f"Name: {team['name']}")
            print(f"Agents: {len(team['agents'])}")
            return team
    except ValueError:
        pass
    
    print("Invalid choice")

# ============================================
# Mini CLI
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "interactive":
            interactive_start()
        elif cmd == "templates":
            print("Available templates:", list(QUICK_TEMPLATES.keys()))
        elif cmd == "quick":
            team = quick_start("full")
            print(f"Team: {team}")
        else:
            print(f"Unknown command: {cmd}")
    else:
        print("Quick Start CLI")
        print("Commands: interactive, templates, quick")
