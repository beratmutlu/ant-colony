from colony.core.grid import Grid
from colony.agents.ant import Ant, MEMORY_SIZE
from colony.agents.action import Action, ActionType
from colony.agents.percept import Percept
from colony.types.item_type import ItemType

import random

class Manager:
    def __init__(self, grid: Grid, n_ants: int, nest_pos: tuple[int, int] = (0, 0), ph_strength=100.0, determinism: float = 50.0, ant_energy: float = 100.0):
        self.grid = grid
        self.nest_pos = nest_pos
        self.ph_strength = ph_strength
        self.tick = 0
        self.determinism = determinism
        self.ant_energy = ant_energy
        self.score = 0
        self.food_delivered_this_tick = 0
        self.ants: list[Ant] = [
            Ant(grid.get_cell(*nest_pos), energy=self.ant_energy, determinism=determinism) for _ in range(n_ants)
        ]
        self.score = 0
    def tick_clock(self) -> None:
        self.tick += 1
        self.food_delivered_this_tick = 0

        percepts = {ant: self._build_percept(ant) for ant in self.ants}

        for ant, percept in percepts.items():
            ant.sense(percept)
            ant.energy -= 1

        actions = {ant: ant.reason() for ant in self.ants}

        self._process_action(actions)
        self.ants = [ant for ant in self.ants if ant.energy > 0]
        self.grid.tick_decay()


    def _build_percept(self, ant: Ant) -> Percept:
        cell = ant.cell
        neighbors = self.grid.get_neighbours(cell) # dict[Direction, Cell | None]

        return Percept(
            carrying=ant.carrying,
            energy=ant.energy,
            last_action_ok=ant.last_action_ok,

            food_present=cell.get_food() > 0.0,

            nest_present=self.nest_pos == cell.pos,

            neighbors_passable={d: n_cell is not None for d, n_cell in neighbors.items()},
            neighbor_pheromones={
                d: n_cell.get_pheromones() if n_cell else {}
                for d, n_cell in neighbors.items()
            },

            nest_adjacent={
                d: (n_cell is not None and n_cell.pos == self.nest_pos)
                for d, n_cell in neighbors.items()
            },

            food_adjacent={
                d: (n_cell is not None and n_cell.get_food() > 0.0)
                for d, n_cell in neighbors.items()
            }
        )




    def _process_action(self, actions: dict[Ant, Action]) -> None:
        moves: dict[tuple[int, int], list[Ant]] = {}

        for ant, action in actions.items():
            if action.type == ActionType.MOVE and action.direction:
                target = action.direction.apply(ant.cell.pos)
                moves.setdefault(target, []).append(ant)
            elif action.type == ActionType.PICK_UP:
                self._pick_up(ant)
                ant.memory.clear()
                ant.energy = self.ant_energy
            elif action.type == ActionType.DROP:
                self._drop(ant)
                ant.memory.clear()
                ant.energy = self.ant_energy

        for target_pos, competing in moves.items():
            cap = self.grid.get_cell(*target_pos).cap_ant
            winners = random.sample(competing, min(cap, len(competing)))

            for ant in competing:
                if ant in winners:
                    self._move(ant, target_pos)
                else:
                    ant.last_action_ok = False

    def _move(self, ant: Ant, target_pos: tuple[int, int]) -> None:
        target_cell = self.grid.get_cell(*target_pos)
        if target_cell.cap_ant <= 0:
            ant.last_action_ok = False
            return

        ant.route_len += 1

        ph_type = ItemType.PHEROMONE_FOOD if ant.carrying else ItemType.PHEROMONE_NEST
        self.grid.get_cell(*target_pos).add_item(ph_type, self.ph_strength / ant.route_len)

        ant.memory.append(target_pos)
        if len(ant.memory) > MEMORY_SIZE:
            ant.memory.pop(0)

        ant.cell = target_cell
        ant.last_action_ok = True
        

    def _pick_up(self, ant: Ant) -> None:
        if ant.cell.items[ItemType.FOOD] > 0:
            ant.cell.remove_item(ItemType.FOOD, 0.0) # amount
            ant.carrying = True
            ant.last_action_ok = True
            ant.route_len = 0
        else:
            ant.last_action_ok = False

    def _drop(self, ant: Ant) -> None:
        if ant.carrying:
            ant.score += 1
            self.score += 1
            self.food_delivered_this_tick += 1
            ant.carrying = False
            ant.route_len = 0
            ant.last_action_ok = True
        else:
            ant.last_action_ok = False
