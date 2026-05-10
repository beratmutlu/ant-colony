import copy
import multiprocessing as mp
from colony.core.simulation import Simulation
from rendering.pygame_renderer import PygameRenderer

def run_headless(config: dict) -> dict:
    sim = Simulation()
    sim.load_dict(config)
    sim.build()
    sim.run(1000)
    return {"seed": config["seed"], "score": sim.manager.score}

if __name__ == "__main__":
    base = Simulation()
    base.load("configs/default.json")
    base_config = base.config

    seeds = [123, 7, 99]

    headless_configs = []
    for seed in seeds:
        cfg = copy.deepcopy(base_config)
        cfg["seed"] = seed
        headless_configs.append(cfg)

    with mp.Pool() as pool:
        future = pool.map_async(run_headless, headless_configs)

        sim = Simulation()
        sim.load_dict(base_config)
        sim.build()
        PygameRenderer(sim).run()

        results = future.get()

    for r in results:
        print(f"seed={r['seed']}  score={r['score']}")
