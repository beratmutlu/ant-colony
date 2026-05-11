import asyncio

from colony.core.simulation import Simulation
from rendering.pygame_renderer import PygameRenderer
from analysis.runner import BatchRunner
from analysis.plotter import Plotter
from pathlib import Path

if __name__ == "__main__":
    base = Simulation()
    base.load("configs/default.json")

    future = (
        BatchRunner(base.config)
        .add_sweep("seed", [42, 123, 7, 99])
        .run()
    )

    sim = Simulation()
    sim.load_dict(base.config)
    sim.build()
    asyncio.run(PygameRenderer(sim).run())

    results = future.get()
    for r in results:
        print(f"{r.label}  score={r.final_score}  converged@{r.convergence_tick}")

    plotter = Plotter(results)
    plotter.plot()
    plotter.plot_summaries(Path("logs"))