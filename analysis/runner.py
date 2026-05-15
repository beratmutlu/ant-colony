import json
import statistics
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
    epoch_size: int = 50
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

    score_history: list[int] = []
    epoch_history: list[int] = []
    ants_alive_history: list[int] = []
    avg_energy_history: list[float] = []
    carrying_ratio_history: list[float] = []

    logged_convergence = False
    convergence_tick: int | None = None

    epoch = 0
    epoch_food = 0

    for _ in range(run_cfg.max_ticks):
        sim.step()
        tick = sim.manager.tick
        delivered = sim.manager.food_delivered_this_tick
        score_history.append(delivered)
        epoch_food += delivered


        if tick % run_cfg.epoch_size == 0 and tick > 0:
            epoch += 1
            epoch_history.append(epoch_food)

            tracker.update(epoch, epoch_food)

            ants = sim.manager.ants
            n_alive = len(ants)
            avg_e = statistics.mean(a.energy for a in ants) if ants else 0.0
            n_carrying = sum(1 for a in ants if a.carrying)
            carry_ratio = n_carrying / n_alive if n_alive else 0.0

            ants_alive_history.append(n_alive)
            avg_energy_history.append(round(avg_e, 2))
            carrying_ratio_history.append(round(carry_ratio, 4))

            logger.log(tick, "summary",
                epoch=epoch,
                score=sim.manager.score,
                ants_alive=n_alive,
                epoch_food=epoch_food,
                avg_energy=round(avg_e, 2),
                carrying_count=n_carrying,
                carrying_ratio=round(carry_ratio, 4),
                stable=tracker.stable
            )
            epoch_food = 0

        if tracker.converged and not logged_convergence:
            convergence_tick = tick
            logger.log(tick, "convergence", epoch=tracker.convergence_epoch)
            logged_convergence = True

        if not sim.manager.ants:
            logger.log(tick, "extinction", epoch=epoch)
            break

    logger.close()

    return ExperimentResult(
        label=exp_cfg.label,
        config=config,
        convergence_epoch=tracker.convergence_epoch,
        convergence_tick=convergence_tick,
        final_score=sim.manager.score,
        score_history=score_history,
        epoch_history=epoch_history,
        ants_alive_history=ants_alive_history,
        avg_energy_history=avg_energy_history,
        carrying_ratio_history=carrying_ratio_history,
        ticks_run=sim.manager.tick,
        epochs_run=epoch
    )


def load_experiment_configs(
    config_dir: str | Path,
    seed: int,
) -> list[ExperimentConfig]:
    config_dir = Path(config_dir)
    configs = []
    for path in sorted(config_dir.glob("*.json")):
        with open(path) as f:
            cfg = json.load(f)
        label = cfg.pop("label", path.stem)
        configs.append(ExperimentConfig(
            base_config=cfg,
            overrides={"seed": seed},
            label=label,
        ))
    return configs


@dataclass
class BatchRunner:
    run_config: RunConfig = field(default_factory=RunConfig)
    experiments: list[ExperimentConfig] = field(default_factory=list)

    def add(self, base_config: dict, overrides: dict | None = None, label: str = "") -> "BatchRunner":
        if not label:
            label = "_".join(f"{k}={v}" for k, v in (overrides or {}).items())
        self.experiments.append(ExperimentConfig(
            base_config=base_config,
            overrides=overrides or {},
            label=label
        ))
        return self

    def run(self):
        """Run all experiments asynchronously. Returns an AsyncResult (call .get() to block)."""
        args = [(exp, self.run_config) for exp in self.experiments]
        pool = Pool()
        future = pool.map_async(_run_single, args)
        pool.close()
        return future

    def run_sync(self) -> list[ExperimentResult]:
        """Run all experiments (using multiprocessing) and return results."""
        args = [(exp, self.run_config) for exp in self.experiments]
        with Pool() as pool:
            return pool.map(_run_single, args)

    def run_sequential(self) -> list[ExperimentResult]:
        """Run experiments one by one."""
        return [_run_single((exp, self.run_config)) for exp in self.experiments]