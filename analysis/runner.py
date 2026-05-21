import json
import statistics
import numpy as np

from dataclasses import dataclass, field
from pathlib import Path
from multiprocessing import Pool

from colony.core.simulation import Simulation
from analysis.experiment import ExperimentConfig, ExperimentResult
from analysis.convergence import OnlineConvergenceTracker, PostHocConvergenceDetector
from analysis.logger import Logger
from analysis.pheromone_visualizer import PheromoneVisualizer


@dataclass
class RunConfig:
    max_ticks: int = 50000
    convergence_window: int = 10
    epoch_size: int = 50
    convergence_epsilon: float = 0.15

    post_hoc_penalty_scale: float = 1.0
    post_hoc_max_relative_total_drift: float = 0.08
    post_hoc_min_relative_regime_step: float = 0.08

    log_dir: Path | None = Path("logs")
    pheromone_snapshot_dir: Path | None = None
    pheromone_snapshot_delay_ticks_by_event: dict[str, int] = field(default_factory=lambda: {
        "clear_pheromones": 200, "set_ant_capacity": 1000
    })


def _run_single(args: tuple[ExperimentConfig, RunConfig]) -> ExperimentResult:
    exp_cfg, run_cfg = args

    config = exp_cfg.build_config()
    sim = Simulation()
    sim.load_dict(config)
    sim.build()

    tracker = OnlineConvergenceTracker(
        window=run_cfg.convergence_window,
        epsilon=run_cfg.convergence_epsilon,
    )

    logger = Logger(
        label=exp_cfg.label,
        path=run_cfg.log_dir / f"{exp_cfg.label}.jsonl" if run_cfg.log_dir else None
    )

    pheromone_visualizer = None
    pheromone_snapshot_dir = None
    pending_comparisons: dict[int, list[tuple[int, str, int, dict, dict]]] = {}


    if run_cfg.pheromone_snapshot_dir:
        pheromone_visualizer = PheromoneVisualizer()
        pheromone_snapshot_dir = run_cfg.pheromone_snapshot_dir / exp_cfg.label


    delivery_history: list[int] = []
    epoch_delivery_history: list[int] = []

    food_amount_history: list[float] = []
    epoch_food_amount_history: list[float] = []

    ants_alive_history: list[int] = []
    avg_energy_history: list[float] = []
    carrying_ratio_history: list[float] = []

    logged_convergence = False
    convergence_tick: int | None = None

    epoch = 0
    epoch_deliveries = 0
    epoch_food_amount = 0.0

    for _ in range(run_cfg.max_ticks):

        next_tick = sim.manager.tick + 1

        if pheromone_visualizer and next_tick in sim.events_by_tick:
            before = pheromone_visualizer.snapshot(sim)
            
            for event in sim.events_by_tick[next_tick]:
                event_type = event["type"]
                delay = run_cfg.pheromone_snapshot_delay_ticks_by_event.get(event_type, 500)
                comparison_tick = next_tick + delay
                pending_comparisons.setdefault(comparison_tick, []).append((next_tick, event_type, delay, event, before))
        
        sim.step()
        tick = sim.manager.tick

        if pheromone_visualizer and tick in pending_comparisons:
            after = pheromone_visualizer.snapshot(sim)

            for event_tick, event_type, delay, event, before in pending_comparisons[tick]:
                path = pheromone_snapshot_dir / f"tick_{event_tick}_{event_type}_compare_after_{delay}.png"
                title = f"{exp_cfg.label} - {event_type} at tick {event_tick}, after {delay} ticks"
                pheromone_visualizer.save_comparison(before, after, event, path, title)

        deliveries = sim.manager.score_this_tick
        food_amount = sim.manager.food_delivered_this_tick

        delivery_history.append(deliveries)
        food_amount_history.append(food_amount)

        epoch_deliveries += deliveries
        epoch_food_amount += food_amount

        if tick % run_cfg.epoch_size == 0 and tick > 0:
            epoch += 1
            epoch_delivery_history.append(epoch_deliveries)
            epoch_food_amount_history.append(epoch_food_amount)

            previous_plateau_start = tracker.active_plateau_start
            tracker.update(epoch, epoch_deliveries)
            if previous_plateau_start is None and tracker.active_plateau_start is not None:
                logger.log(tick, "plateau_start", epoch=tracker.active_plateau_start)
            elif previous_plateau_start is not None and tracker.active_plateau_start is None:
                logger.log(tick, "plateau_end", epoch=tracker.plateau_ranges[-1][1])

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
                food_delivered=round(sim.manager.food_delivered, 4),
                ants_alive=n_alive,
                epoch_deliveries=epoch_deliveries,
                epoch_food_amount=round(epoch_food_amount, 4),
                avg_energy=round(avg_e, 2),
                carrying_count=n_carrying,
                carrying_ratio=round(carry_ratio, 4),
                stable=tracker.stable
            )
            epoch_deliveries = 0
            epoch_food_amount = 0.0

        if tracker.converged and not logged_convergence:
            convergence_tick = tick
            logger.log(tick, "convergence", epoch=tracker.convergence_epoch)
            logged_convergence = True

        if not sim.manager.ants:
            logger.log(tick, "extinction", epoch=epoch)
            break
    
    if pheromone_visualizer:
        tick = sim.manager.tick
        path = pheromone_snapshot_dir / f"final_tick_{tick}.png"
        title = f"{exp_cfg.label} - final pheromone field at tick {tick}"
        pheromone_visualizer.save_heatmap(sim, path, title)

    logger.close()

    post_hoc = PostHocConvergenceDetector(
        min_size=run_cfg.convergence_window,
        min_plateau_epochs=run_cfg.convergence_window,
        penalty_scale=run_cfg.post_hoc_penalty_scale,
        max_relative_total_drift=run_cfg.post_hoc_max_relative_total_drift,
        min_relative_regime_step=run_cfg.post_hoc_min_relative_regime_step
    ).detect(epoch_delivery_history)

    plateau_ranges = list(tracker.plateau_ranges)
    if tracker.active_plateau_start is not None:
        plateau_ranges.append((tracker.active_plateau_start, epoch))

    return ExperimentResult(
        label=exp_cfg.label,
        config=config,
        convergence_epoch=tracker.convergence_epoch,
        convergence_tick=convergence_tick,
        plateau_ranges=plateau_ranges,
        active_plateau_start=tracker.active_plateau_start,
        final_score=sim.manager.score,
        final_food_amount=round(sim.manager.food_delivered, 4),
        delivery_history=delivery_history,
        epoch_delivery_history=epoch_delivery_history,
        food_amount_history=food_amount_history,
        epoch_food_amount_history=epoch_food_amount_history,
        ants_alive_history=ants_alive_history,
        avg_energy_history=avg_energy_history,
        carrying_ratio_history=carrying_ratio_history,
        ticks_run=sim.manager.tick,
        epochs_run=epoch,
        epoch_size=run_cfg.epoch_size,
        post_hoc_convergence=post_hoc
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
