#!/usr/bin/env python3
"""
Generate SAB - 從 SAD.md 生成 Software Architecture Baseline
====================================================

用途：Phase 2 完成後，從 SAD.md 生成 SAB

使用方式：
    python scripts/generate_sab.py --project /path/to/project

產出：
    .methodology/SAB.json - 結構化的 Architecture Baseline
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate SAB from SAD.md")
    parser.add_argument("--project", default=".", help="專案路徑")
    parser.add_argument("--output", default=".methodology/SAB.json", help="輸出路徑")
    args = parser.parse_args()
    
    project = Path(args.project)
    sad_file = project / "SAD.md"
    output_file = project / args.output
    
    if not sad_file.exists():
        print(f"❌ SAD.md not found: {sad_file}")
        return 1
    
    print(f"\n{'='*50}")
    print(f"SAB Generator")
    print(f"{'='*50}")
    print(f"Input: {sad_file}")
    print(f"Output: {output_file}")
    
    # Import SabParser
    sys.path.insert(0, str(project / "skills" / "methodology-v2"))
    try:
        from quality_gate.sab_parser import SabParser
    except ImportError:
        from sab_parser import SabParser
    
    # Parse SAD.md
    parser = SabParser()
    sab_spec = parser.parse(sad_file)
    
    if sab_spec is None:
        print(f"❌ Failed to parse SAD.md")
        return 1
    
    # Save SAB
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(sab_spec.to_dict(), f, indent=2, ensure_ascii=False)
    
    print(f"✅ SAB generated successfully")
    print(f"   Modules: {len(sab_spec.modules)}")
    print(f"   Layers: {len(sab_spec.layers)}")
    print(f"   File: {output_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
