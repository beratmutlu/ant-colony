import asyncio
from colony.core.simulation import Simulation
from rendering.pygame_renderer import PygameRenderer

async def main():
    sim = Simulation()
    sim.load("configs/default.json")
    sim.build()
    await PygameRenderer(sim).run()

asyncio.run(main())