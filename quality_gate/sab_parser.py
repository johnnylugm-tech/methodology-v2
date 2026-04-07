"""
SabParser — 從 SAD.md 解析出 SabSpec
====================================
支援從 Phase 2 的 SAD.md 自動生成結構化的 SAB
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
try:
    from .sab_spec import SabSpec
except ImportError:
    from sab_spec import SabSpec  # fallback for standalone CLI
from datetime import datetime


class SabParser:
    """
    從 SAD.md 解析出 SabSpec

    支援的 SAD 格式：
    1. ## Module: xxx / ### xxx (module definition)
    2. - Responsibility: xxx
    3. - Public API: method1, method2
    4. - Dependencies: dep1, dep2
    5. - Type: core|api|utils|...

    ## Architecture Layers
    ### Layer: core
    - modules: [module1, module2]

    ## Architecture Rules
    - Rule 1: xxx
    """

    def __init__(self, sad_path: Path):
        self.sad_path = sad_path
        self.content = sad_path.read_text() if sad_path.exists() else ""
        self.lines = self.content.split("\n")
        self._warnings: List[str] = []

    def parse(self) -> SabSpec:
        """解析 SAD.md → SabSpec"""
        sab = SabSpec()
        sab.created_at = datetime.now().isoformat()
        sab.phase = self._detect_phase()
        sab.project = self._detect_project()

        # 解析 modules
        sab.modules = self._extract_modules()

        # 解析 layers
        sab.layers = self._extract_layers()

        # 解析 architecture rules
        sab.architecture_rules = self._extract_rules()

        # 解析 quality targets
        sab.quality_targets = self._extract_quality_targets()

        # 加入 warnings
        if self._warnings:
            sab._parse_warnings = self._warnings

        return sab

    def _detect_phase(self) -> int:
        """從 SAD.md 內容推斷 Phase"""
        if "Phase 2" in self.content or "SWE.5" in self.content:
            return 2
        elif "Phase 3" in self.content or "SWE.6" in self.content:
            return 3
        elif "Phase 4" in self.content or "SWE.7" in self.content:
            return 4
        return 2  # 預設 Phase 2

    def _detect_project(self) -> str:
        """從 SAD.md 推斷專案名"""
        # 找第一個 H1 或 H2
        for line in self.lines:
            line = line.strip()
            if line.startswith("# ") and not line.startswith("## "):
                return line[2:].strip()
        return self.sad_path.parent.name

    def _extract_modules(self) -> Dict[str, Dict[str, Any]]:
        """提取所有模組"""
        modules = {}
        current_module = None

        for i, line in enumerate(self.lines):
            # 偵測新模組（## Module: xxx 或 ### xxx）
            module_match = re.match(r"(?:## Module:|###)\s+(.+)", line.strip())
            if module_match:
                current_module = module_match.group(1).strip()
                modules[current_module] = {
                    "responsibility": "",
                    "public_api": [],
                    "dependencies": [],
                    "type": self._infer_module_type(current_module),
                    "stability": "unknown",
                    "line_number": i + 1
                }
                continue

            if current_module:
                ls = line.strip()

                # Responsibility
                if ls.startswith("- Responsibility:") or ls.startswith("Responsibility:"):
                    modules[current_module]["responsibility"] = line.split(":", 1)[1].strip()

                # Public API
                elif ls.startswith("- Public API:") or ls.startswith("Public API:"):
                    api_str = line.split(":", 1)[1].strip()
                    modules[current_module]["public_api"] = [a.strip() for a in api_str.split(",")]

                # Dependencies
                elif ls.startswith("- Dependencies:") or ls.startswith("Dependencies:"):
                    dep_str = line.split(":", 1)[1].strip()
                    modules[current_module]["dependencies"] = [d.strip() for d in dep_str.split(",")]

                # Type
                elif ls.startswith("- Type:") or ls.startswith("Type:"):
                    modules[current_module]["type"] = line.split(":", 1)[1].strip()

                # Stability
                elif ls.startswith("- Stability:") or ls.startswith("Stability:"):
                    modules[current_module]["stability"] = line.split(":", 1)[1].strip()

        # 清理空的 module 定義
        modules = {k: v for k, v in modules.items() if v["responsibility"] or v["public_api"]}

        return modules

    def _infer_module_type(self, module_name: str) -> str:
        """從名稱推斷模組類型"""
        name_lower = module_name.lower()
        if "api" in name_lower or "controller" in name_lower or "endpoint" in name_lower:
            return "api"
        elif "service" in name_lower or "business" in name_lower:
            return "service"
        elif "repository" in name_lower or "dao" in name_lower or "db" in name_lower:
            return "data"
        elif "adapter" in name_lower or "driver" in name_lower:
            return "adapter"
        elif "util" in name_lower or "helper" in name_lower:
            return "utils"
        elif "model" in name_lower or "entity" in name_lower or "domain" in name_lower:
            return "domain"
        elif "test" in name_lower:
            return "test"
        return "unknown"

    def _extract_layers(self) -> List[Dict[str, Any]]:
        """提取 Architecture Layers"""
        layers = []
        in_layers_section = False
        current_layer = None

        for line in self.lines:
            line_stripped = line.strip()

            if "Architecture Layers" in line_stripped or "Layer Architecture" in line_stripped:
                in_layers_section = True
                continue

            if in_layers_section:
                # 新 layer
                layer_match = re.match(r"(?:### Layer:|###)\s+(.+)", line_stripped)
                if layer_match:
                    if current_layer:
                        layers.append(current_layer)
                    current_layer = {"name": layer_match.group(1).strip(), "modules": [], "allowed_dependencies": []}
                    continue

                if current_layer:
                    # 模組列表
                    if "- modules:" in line_stripped or "modules:" in line_stripped:
                        mods_str = line.split(":", 1)[1].strip().strip("[]")
                        current_layer["modules"] = [m.strip() for m in mods_str.split(",") if m.strip()]

                    # 允許的依賴
                    elif "- allowed_dependencies:" in line_stripped or "allowed_dependencies:" in line_stripped:
                        deps_str = line.split(":", 1)[1].strip().strip("[]")
                        current_layer["allowed_dependencies"] = [d.strip() for d in deps_str.split(",") if d.strip()]

                    # 遇到新大標題就結束
                    elif line_stripped.startswith("# ") and current_layer and current_layer.get("modules"):
                        layers.append(current_layer)
                        in_layers_section = False
                        current_layer = None

        if current_layer:
            layers.append(current_layer)

        return layers

    def _extract_rules(self) -> List[str]:
        """提取 Architecture Rules"""
        rules = []
        in_rules_section = False

        for line in self.lines:
            line_stripped = line.strip()

            if "Architecture Rules" in line_stripped or "Design Rules" in line_stripped:
                in_rules_section = True
                continue

            if in_rules_section:
                # 規則項目
                if line_stripped.startswith("- "):
                    rule = line_stripped[2:].strip()
                    if rule and not rule.startswith("Layer"):
                        rules.append(rule)
                elif line_stripped.startswith("###") or (line_stripped.startswith("# ") and not line_stripped.startswith("##")):
                    in_rules_section = False

        return rules

    def _extract_quality_targets(self) -> Dict[str, Any]:
        """提取 Quality Targets"""
        targets = {}
        in_targets_section = False

        for line in self.lines:
            line_stripped = line.strip()

            if "Quality Target" in line_stripped or "Quality Attribute" in line_stripped:
                in_targets_section = True
                continue

            if in_targets_section:
                if line_stripped.startswith("- "):
                    try:
                        key_val = line_stripped[2:].split(":")
                        if len(key_val) == 2:
                            key = key_val[0].strip().lower().replace(" ", "_")
                            match = re.search(r'[\d.]+', key_val[1])
                            if match:
                                targets[key] = float(match.group())
                    except Exception:
                        pass
                elif line_stripped.startswith("# ") and not line_stripped.startswith("##"):
                    in_targets_section = False

        return targets


def parse_sad(sad_path: Path) -> SabSpec:
    """便利函數：直接解析 SAD.md"""
    parser = SabParser(sad_path)
    sab = parser.parse()

    errors = sab.validate()
    if errors:
        sab._parse_errors = errors

    return sab


# ===== CLI 測試入口 =====
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SabParser CLI — Parse SAD.md to SabSpec")
    parser.add_argument("--path", type=str, required=True, help="Path to SAD.md")
    parser.add_argument("--output", type=str, help="Output JSON path (optional)")
    args = parser.parse_args()

    sad_path = Path(args.path)
    if not sad_path.exists():
        print(f"ERROR: SAD.md not found at {sad_path}")
        exit(1)

    print(f"Parsing: {sad_path}")
    sab = parse_sad(sad_path)

    print(f"\n=== SabSpec Result ===")
    print(f"Project: {sab.project}")
    print(f"Phase: {sab.phase}")
    print(f"Created: {sab.created_at}")
    print(f"Modules ({len(sab.modules)}):")
    for name, mod in sab.modules.items():
        print(f"  - {name}: {mod.get('type', '?')} | {mod.get('responsibility', '')[:60]}")
    print(f"Layers ({len(sab.layers)}):")
    for layer in sab.layers:
        print(f"  - {layer['name']}: {layer.get('modules', [])}")
    print(f"Rules ({len(sab.architecture_rules)}):")
    for rule in sab.architecture_rules[:5]:
        print(f"  - {rule}")
    print(f"Quality Targets: {sab.quality_targets}")

    errors = sab.validate()
    if errors:
        print(f"\nValidation Errors: {errors}")
    else:
        print(f"\nValidation: OK")

    if args.output:
        sab.save(Path(args.output))
        print(f"Saved to: {args.output}")
