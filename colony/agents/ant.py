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
        self.score = 0
        self.carrying: bool = False
        self.last_action_ok: bool = True
        self.memory: list[tuple[int ,int]] = []
        self.determinism = determinism
        self._last_percept = None
        self.route_len = 0

    def sense(self, percept: Percept) -> None:
        self._last_percept = percept

    def reason(self) -> Action:
        p = self._last_percept

        if p.food_present and not p.carrying:
            return Action(ActionType.PICK_UP)

        if p.nest_present and p.carrying:
            return Action(ActionType.DROP)

        if p.carrying:
            for d, ok in p.neighbors_passable.items():
                if ok and p.nest_adjacent.get(d):
                    if random.random() < 0.95:
                        return Action(ActionType.MOVE, d)

            direction = self._follow_gradient(p, ItemType.PHEROMONE_NEST)
            return Action(ActionType.MOVE, direction)

        for d, ok in p.food_adjacent.items():
            if ok:
                if random.random() < 0.95:
                    return Action(ActionType.MOVE, d)
        
        direction = self._follow_gradient(p, ItemType.PHEROMONE_FOOD)
        return Action(ActionType.MOVE, direction)

    def _follow_gradient(self, percept: Percept, attract: ItemType) -> Direction:
        passable = [d for d, ok in percept.neighbors_passable.items()
                    if ok and d.apply(self.cell.pos) not in self.memory]
        if not passable:
            passable = [d for d, ok in percept.neighbors_passable.items() if ok]
        if not passable:
            return None

        alpha = (self.determinism / 100) ** 2 * 5.0

        weights = []
        for d in passable:
            ph = percept.neighbor_pheromones.get(d, {})
            attraction = max(ph.get(attract, 0.0), 1e-6) ** alpha
            weights.append(attraction)

        return random.choices(passable, weights=weights)[0]
