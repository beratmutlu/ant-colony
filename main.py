from colony.core.simulation import Simulation
from rendering.pygame_renderer import PygameRenderer

if __name__ == "__main__":
    sim = Simulation()
    sim.load("configs/default.json")
    sim.build()
    PygameRenderer(sim).run()