from dataclasses import dataclass, field
from pathlib import Path
from multiprocessing import Pool

from colony.core.simulation import Simulation
from analysis.experiment import ExperimentConfig, ExperimentResult
from analysis.convergence import ConvergenceTracker
from analysis.logger import Logger

@dataclass
class RunConfig:
    max_ticks: int = 50000
    convergence_window: int = 10
    convergence_epsilon: float = 0.15
    log_dir: Path | None = Path("logs")


def _run_single(args: tuple[ExperimentConfig, RunConfig]) -> ExperimentResult:
    exp_cfg, run_cfg = args

    config = exp_cfg.build_config()
    sim = Simulation()
    sim.load_dict(config)
    sim.build()

    tracker = ConvergenceTracker(
        window=run_cfg.convergence_window,
        epsilon=run_cfg.convergence_epsilon,
    )

    logger = Logger(
        label=exp_cfg.label,
        path=run_cfg.log_dir / f"{exp_cfg.label}.jsonl" if run_cfg.log_dir else None
    )

    score_history = []

    logged_convergence = False

    epoch_size = 50
    epoch_food = 0

    for _ in range(run_cfg.max_ticks):
        sim.step()
        tick = sim.manager.tick
        delivered = sim.manager.food_delivered_this_tick
        score_history.append(delivered)
        epoch_food += delivered


        if tick % epoch_size == 0 and tick > 0:
            tracker.update(tick, epoch_food)

            logger.log(tick, "summary",
                score=sim.manager.score,
                ants_alive=len(sim.manager.ants),
                delivered_last_window=sum(score_history[-tracker.window:]),
                stable=tracker.stable
            )
            epoch_food = 0

        if tracker.converged and not logged_convergence:
            logger.log(tick, "convergence", convergence_tick=tracker.convergence_tick)
            logged_convergence = True

        if not sim.manager.ants:
            logger.log(tick, "extinction")
            break

    logger.close()

    return ExperimentResult(
        label=exp_cfg.label,
        config=config,
        convergence_tick=tracker.convergence_tick,
        final_score=sim.manager.score,
        score_history=score_history,
        ticks_run=sim.manager.tick
    )

@dataclass
class BatchRunner:
    base_config: dict
    run_config: RunConfig = field(default_factory=RunConfig)
    experiments:list[ExperimentConfig] = field(default_factory=list)

    def add(self, overrides: dict, label: str = "") -> "BatchRunner":
        if not label:
            label = "_".join(f"{k}={v}" for k, v in overrides.items())
        self.experiments.append(ExperimentConfig(
            base_config=self.base_config,
            overrides=overrides,
            label=label
        ))
        return self

    def add_sweep(self, key: str, values: list) -> "BatchRunner":
        for v in values:
            self.add({key: v})
        return self

    def run(self) -> "AsyncResult":
        args = [(exp, self.run_config) for exp in self.experiments]
        pool = Pool()
        future = pool.map_async(_run_single, args)
        pool.close()
        return future