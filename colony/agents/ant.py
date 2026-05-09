from colony.core.cell import Cell
from colony.agents.action import Action, ActionType, Direction
from colony.agents.percept import Percept
from colony.types.item_type import ItemType
import random

MEMORY_SIZE = 8

class Ant:
    def __init__(self, cell: Cell, energy: float = 100.0, determinism: float = 50.0):
        self.cell = cell
        self.energy = energy
        self.carrying: bool = False
        self.last_action_ok: bool = True
        self.memory: list[tuple[int ,int]] = []
        self.determinism = determinism
        self._last_percept = None

    def sense(self, percept: Percept) -> None:
        self._last_percept = percept

    def reason(self) -> Action:
        p = self._last_percept

        if p.food_present and not p.carrying:
            return Action(ActionType.PICK_UP)

        if p.nest_present and p.carrying:
            return Action(ActionType.DROP)

        if p.carrying:
            direction = self._follow_gradient(p, ItemType.PHEROMONE_NEST)
            return Action(ActionType.MOVE, direction)

        direction = self._follow_gradient(p, ItemType.PHEROMONE_FOOD)
        return Action(ActionType.MOVE, direction)

    def _follow_gradient(self, percept: Percept, pheromone: ItemType) -> Direction:
        passable = [d for d, ok in percept.neighbors_passable.items()
                    if ok and d.apply(self.cell.pos) not in self.memory]
        if not passable:
            return Direction.NORTH

        alpha = (self.determinism / 100) ** 2 * 5.0

        weights = []
        for d in passable:
            ph = percept.neighbor_pheromones.get(d, {}).get(pheromone, 0.0)
            weights.append(max(ph, 1e-6) ** alpha)

        return random.choices(passable, weights=weights)[0]




