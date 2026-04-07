"""
SabSpec — Software Architecture Baseline Specification
=======================================================
Software Architecture Baseline 的標準化格式

目的：
- 將 Phase 2 SAD.md 轉換為結構化、可度量的基線
- 支援 Phase-Gate 時自動建立 SAB snapshot
- 支援 Drift Detection（與 SAB 比對）

格式：
{
    "version": "1.0",
    "created_at": "ISO timestamp",
    "phase": 2,
    "project": "專案名",
    "modules": {
        "module_name": {
            "type": "core|api|utils|adapter|...",
            "responsibility": "職責描述",
            "public_api": ["method1", "method2"],
            "dependencies": ["other_module"],
            "stability": "stable|unstable|abstract",
            "quality_attributes": ["reusable", "testable"]
        }
    },
    "layers": [
        {"name": "core", "modules": ["module1"], "allowed_dependencies": ["utils"]},
        {"name": "api", "modules": ["module2"], "allowed_dependencies": ["core", "utils"]},
    ],
    "architecture_rules": [
        "core 不能依賴 api",
        "adapter 不能依賴 adapter",
        ...
    ],
    "quality_targets": {
        "max_complexity": 15,
        "min_coverage": 80,
        "max_coupling": 0.3
    }
}
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


@dataclass
class SabSpec:
    """Software Architecture Baseline"""
    version: str = "1.0"
    created_at: str = ""
    phase: int = 2
    project: str = ""
    modules: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    layers: List[Dict[str, Any]] = field(default_factory=list)
    architecture_rules: List[str] = field(default_factory=list)
    quality_targets: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "phase": self.phase,
            "project": self.project,
            "modules": self.modules,
            "layers": self.layers,
            "architecture_rules": self.architecture_rules,
            "quality_targets": self.quality_targets
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SabSpec":
        return cls(
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", ""),
            phase=data.get("phase", 2),
            project=data.get("project", ""),
            modules=data.get("modules", {}),
            layers=data.get("layers", []),
            architecture_rules=data.get("architecture_rules", []),
            quality_targets=data.get("quality_targets", {})
        )

    def validate(self) -> List[str]:
        """驗證 SAB 格式，返回錯誤列表"""
        errors = []

        if not self.modules:
            errors.append("SAB must have at least one module")

        for name, mod in self.modules.items():
            if "responsibility" not in mod:
                errors.append(f"Module '{name}' missing 'responsibility'")

        for layer in self.layers:
            if "name" not in layer:
                errors.append("Layer missing 'name'")

        return errors

    def save(self, path: Path):
        """儲存 SAB 到檔案"""
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))

    @classmethod
    def load(cls, path: Path) -> "SabSpec":
        """從檔案載入 SAB"""
        return cls.from_dict(json.loads(path.read_text()))


# ===== CLI 測試入口 =====
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SabSpec CLI")
    parser.add_argument("--validate", type=str, help="Validate a SAB JSON file")
    parser.add_argument("--create", action="store_true", help="Create empty SAB")
    args = parser.parse_args()

    if args.validate:
        path = Path(args.validate)
        sab = SabSpec.load(path)
        errors = sab.validate()
        print(f"Loaded SAB: {sab.project} (Phase {sab.phase})")
        print(f"Modules: {len(sab.modules)}")
        print(f"Layers: {len(sab.layers)}")
        print(f"Rules: {len(sab.architecture_rules)}")
        if errors:
            print(f"Errors: {errors}")
        else:
            print("Validation: OK")

    elif args.create:
        sab = SabSpec(
            project="example",
            phase=2,
            modules={},
            layers=[],
            architecture_rules=["core cannot depend on api"],
            quality_targets={"max_complexity": 15}
        )
        print(json.dumps(sab.to_dict(), ensure_ascii=False, indent=2))

    else:
        # 預設：測試 SabSpec dataclass
        sab = SabSpec(
            project="TestProject",
            phase=2,
            modules={
                "UserService": {
                    "type": "service",
                    "responsibility": "Handle user business logic",
                    "public_api": ["create_user", "get_user"],
                    "dependencies": ["UserRepository"],
                    "stability": "stable"
                },
                "UserRepository": {
                    "type": "data",
                    "responsibility": "Database access for users",
                    "public_api": ["save", "find_by_id"],
                    "dependencies": [],
                    "stability": "stable"
                }
            },
            layers=[
                {"name": "core", "modules": ["UserService"], "allowed_dependencies": ["UserRepository"]},
                {"name": "data", "modules": ["UserRepository"], "allowed_dependencies": []}
            ],
            architecture_rules=["core cannot depend on api"],
            quality_targets={"max_complexity": 15, "min_coverage": 80}
        )

        print("=== SabSpec Test ===")
        print(f"Project: {sab.project}")
        print(f"Phase: {sab.phase}")
        print(f"Modules: {list(sab.modules.keys())}")
        print(f"Layers: {[l['name'] for l in sab.layers]}")
        print(f"Rules: {sab.architecture_rules}")
        print(f"Quality Targets: {sab.quality_targets}")
        print(f"Errors: {sab.validate()}")

        # 測試序列化
        d = sab.to_dict()
        sab2 = SabSpec.from_dict(d)
        print(f"\nRoundtrip test: {sab2.project == sab.project}")
