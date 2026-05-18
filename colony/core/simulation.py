import json
import random
from colony.core.grid import Grid
from colony.core.manager import Manager
from colony.types.item_type import ItemType

class Simulation:
    def __init__(self):
        self.config = None
        self.manager: Manager | None = None
        self.events_by_tick: dict[int, list[dict]] = {}
    def load(self, path: str) -> None:
        with open(path) as file:
            self.config = json.load(file)

    def load_dict(self, config: dict) -> None:
        self.config = config

    def build(self) -> None:
        cfg = self.config
        random.seed(cfg["seed"])

        grid = Grid(cfg["grid"]["width"], cfg["grid"]["height"])

        for fs in cfg["food_sources"]:
            x, y = fs["pos"]
            grid.get_cell(x, y).add_item(ItemType.FOOD, fs["amount"])

        nest_pos = tuple(cfg["nest_pos"])
        
        events = cfg.get("events", [])
        self.events_by_tick = {}

        for event in events:
            tick = event["tick"]
            self.events_by_tick.setdefault(tick, []).append(event)

        self.manager = Manager(
            grid=grid,
            n_ants=cfg["ants"]["n"],
            nest_pos=nest_pos,
            ph_strength=cfg["ph_strength"],
            determinism=cfg["ants"]["determinism"],
            ant_energy=cfg["ants"]["energy"]
        )

    def step(self) -> None:
        next_tick = self.manager.tick + 1
        self._apply_events_for_tick(next_tick)
        self.manager.tick_clock()

    def _apply_events_for_tick(self, tick: int) -> None:
        for event in self.events_by_tick.get(tick, []):
            self._apply_event(event)
    
    def _apply_event(self, event: dict) -> None:
        event_type = event["type"]
        cells = event["cells"]

        if event_type == "set_ant_capacity":
            value = event["value"]
            self.manager.grid.set_ant_capacity(cells, value)
        
        elif event_type == "clear_pheromones":
            self.manager.grid.clear_pheromones(cells)
        
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
    def run(self, steps: int) -> None:
        for _ in range(steps):
            self.step()


if __name__ == '__main__':
    sim = Simulation()
    sim.load("config.json")
    sim.build()
    sim.run(1000)