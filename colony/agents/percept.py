from dataclasses import dataclass
from colony.agents.action import Direction
from colony.types.item_type import ItemType


@dataclass(frozen=True)
class Percept:
    carrying: bool
    energy: float
    last_action_ok: bool

    food_present: bool
    nest_present: bool

    neighbor_pheromones: dict[Direction, dict[ItemType, float]]
    neighbors_passable: dict[Direction, bool]

    nest_adjacent: dict[Direction, bool]
