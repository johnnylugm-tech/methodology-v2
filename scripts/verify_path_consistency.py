#!/usr/bin/env python3
"""
Path Consistency Verifier
=========================
自動驗證 Phase Plan doc 路徑與 Framework Tool 路徑是否一致

Usage:
    python3 scripts/verify_path_consistency.py

Exit codes:
    0 = All consistent
    1 = Inconsistencies found
    2 = Error
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Framework tools to check
TOOL_FILES = [
    "quality_gate/phase_paths.py",
    "quality_gate/phase_artifact_enforcer.py",
    "quality_gate/phase_aware_constitution.py",
    "quality_gate/constitution/phase_prerequisite_checker.py",
    "quality_gate/constitution/__init__.py",
]

# Phase Plan WHERE patterns
PHASE_WHERE_PATTERNS = {
    5: "05-verify",
    6: "06-quality",
    7: "07-risk",
    8: "08-config",
}

# Expected artifacts per phase (from Phase Plans)
PHASE_ARTIFACTS = {
    5: ["BASELINE.md", "VERIFICATION_REPORT.md"],  # Only Phase 5 artifacts
    6: ["QUALITY_REPORT.md", "MONITORING_PLAN.md"],
    7: ["RISK_ASSESSMENT.md", "RISK_REGISTER.md"],
    8: ["CONFIG_RECORDS.md", "requirements.lock"],
}


def extract_paths_from_tool(filepath: str) -> Dict[int, Set[str]]:
    """Extract paths from a Framework tool file."""
    paths = {5: set(), 6: set(), 7: set(), 8: set()}
    
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        
        # Look for directory patterns like "05-verify/", "06-quality/", etc.
        for phase, pattern in PHASE_WHERE_PATTERNS.items():
            matches = re.findall(rf'"{pattern}/[^"]*"', content)
            for m in matches:
                paths[phase].add(m.strip('"'))
            
            # Also match output_dir: "05-verify"
            matches2 = re.findall(rf'output_dir["\s:]+["\']?{pattern}["\']?', content)
            for m in matches2:
                paths[phase].add(pattern)
        
    except Exception as e:
        print(f"WARNING: Error reading {filepath}: {e}")
    
    return paths


def extract_paths_from_plan(phase: int) -> Set[str]:
    """Extract WHERE path from Phase Plan doc."""
    plan_file = Path(f"docs/Phase{phase}_Plan_5W1H_AB.md")
    
    if not plan_file.exists():
        return set()
    
    content = plan_file.read_text(encoding="utf-8")
    
    # Find WHERE line
    where_match = re.search(r'\*\*WHERE\*\*\s*\|\s*`([^`]+)`', content)
    if where_match:
        path = where_match.group(1).strip()
        return {path.rstrip("/")}
    
    return set()


def main():
    print("=" * 60)
    print("PATH CONSISTENCY VERIFIER")
    print("=" * 60)
    print()
    
    inconsistencies = []
    
    # Check each phase
    for phase in [5, 6, 7, 8]:
        print(f"\nPhase {phase}")
        print("-" * 40)
        
        # Get plan path
        plan_paths = extract_paths_from_plan(phase)
        plan_path_str = list(plan_paths)[0] if plan_paths else "NOT FOUND"
        print(f"  Plan WHERE: {plan_path_str}")
        
        # Get artifacts
        artifacts = PHASE_ARTIFACTS.get(phase, [])
        
        # Check each tool
        all_tool_paths = {5: set(), 6: set(), 7: set(), 8: set()}
        for tool_file in TOOL_FILES:
            if not Path(tool_file).exists():
                continue
            tool_paths = extract_paths_from_tool(tool_file)
            for p in [5, 6, 7, 8]:
                all_tool_paths[p].update(tool_paths[p])
        
        # Show what tools know about this phase
        tool_phase_paths = all_tool_paths.get(phase, set())
        if tool_phase_paths:
            print(f"  Tool paths: {tool_phase_paths}")
        
        # Check if plan path is in tool paths
        plan_dir = plan_path_str.rstrip("/")
        if tool_phase_paths and plan_dir not in [p.rstrip("/") for p in tool_phase_paths]:
            inconsistencies.append({
                "phase": phase,
                "plan_path": plan_path_str,
                "tool_paths": tool_phase_paths,
                "issue": "Plan path not found in tool paths"
            })
            print(f"  STATUS: INCONSISTENT - Plan path not in tools")
        else:
            print(f"  STATUS: CONSISTENT")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not inconsistencies:
        print("\nALL PATHS CONSISTENT")
        return 0
    else:
        print(f"\n{len(inconsistencies)} INCONSISTENCIES FOUND:")
        for inc in inconsistencies:
            print(f"\n  Phase {inc['phase']}:")
            print(f"    Plan: {inc['plan_path']}")
            print(f"    Tools: {inc['tool_paths']}")
            print(f"    Issue: {inc['issue']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())