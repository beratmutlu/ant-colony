import json
import random
from colony.core.grid import Grid
from colony.core.manager import Manager
from colony.types.item_type import ItemType

class Simulation:
    def __init__(self):
        self.config = None
        self.manager: Manager | None = None

    def load(self, path: str) -> None:
        with open(path) as file:
            self.config = json.load(file)

    def build(self) -> None:
        cfg = self.config
        random.seed(cfg["seed"])

        grid = Grid(cfg["grid"]["width"], cfg["grid"]["height"])

        for fs in cfg["food_sources"]:
            x, y = fs["pos"]
            grid.get_cell(x, y).add_item(ItemType.FOOD, fs["amount"])

        nest_pos = tuple(cfg["nest_pos"])

        self.manager = Manager(
            grid=grid,
            n_ants=cfg["ants"]["n"],
            nest_pos=nest_pos,
            ph_strength=cfg["ph_strength"],
            determinism=cfg["ants"]["determinism"],
            ant_energy=cfg["ants"]["energy"]
        )

    def step(self) -> None:
        self.manager.tick_clock()

    def run(self, steps: int) -> None:
        for _ in range(steps):
            self.step()


if __name__ == '__main__':
    sim = Simulation()
    sim.load("config.json")
    sim.build()
    sim.run(1000)