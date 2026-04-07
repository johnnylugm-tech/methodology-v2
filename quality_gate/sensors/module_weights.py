from dataclasses import dataclass, field, asdict


@dataclass
class ModuleWeights:
    """
    模組加權配置。
    用於計算綜合 quality score。
    """
    complexity: float = 0.30
    coupling: float = 0.25
    coverage: float = 0.25
    maintainability: float = 0.20

    def __post_init__(self):
        total = self.complexity + self.coupling + self.coverage + self.maintainability
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    @classmethod
    def from_config(cls, config: dict) -> "ModuleWeights":
        return cls(
            complexity=config.get("complexity", 0.30),
            coupling=config.get("coupling", 0.25),
            coverage=config.get("coverage", 0.25),
            maintainability=config.get("maintainability", 0.20),
        )

    def to_dict(self) -> dict:
        return asdict(self)
