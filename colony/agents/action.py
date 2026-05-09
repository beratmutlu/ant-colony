from enum import Enum
from dataclasses import dataclass

class ActionType(Enum):
    MOVE = 1
    PICK_UP = 2
    DROP = 3
    IDLE = 4

class Direction(Enum):
    NORTH = (0, 1)
    NORTHEAST = (1, 1)
    EAST  = (1, 0)
    SOUTHEAST = (1, -1)
    SOUTH = (0, -1)
    SOUTHWEST = (-1, -1)
    WEST  = (-1, 0)
    NORTHWEST = (-1, 1)

    def apply(self, pos: tuple[int, int]) -> tuple[int, int]:
        return pos[0] + self.value[0], pos[1] + self.value[1]

@dataclass(frozen=True)
class Action:
    type: ActionType
    direction: Direction | None = None
