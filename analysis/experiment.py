import copy
from dataclasses import dataclass, field

@dataclass
class ExperimentConfig:
    base_config: dict
    overrides: dict = field(default_factory=dict)
    label: str = ""

    def build_config(self) -> dict:
        cfg = copy.deepcopy(self.base_config)
        for key, value in self.overrides.items():
            parts = key.split(".")
            target = cfg
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = value
        return cfg


@dataclass
class ExperimentResult:
    label: str
    config: dict
    convergence_tick: int | None
    final_score: int
    score_history: list[int] = field(default_factory=list)
    ticks_run: int = 0