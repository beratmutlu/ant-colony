import asyncio

async def main():
    # Embedded config
    CONFIG = {
        "seed": 42,
        "grid": {"width": 20, "height": 20},
        "ants": {"n": 50, "energy": 300.0, "determinism": 70.0},
        "nest_pos": [10, 10],
        "ph_strength": 50.0,
        "food_sources": [
            {"pos": [2, 2], "amount": 200.0},
            {"pos": [18, 18], "amount": 200.0}
        ]
    }

    from colony.core.simulation import Simulation
    from rendering.pygame_renderer import PygameRenderer

    sim = Simulation()
    sim.load_dict(CONFIG)
    sim.build()
    await PygameRenderer(sim).run()

asyncio.run(main())
