"""
Usage:
    python main.py                  # seed 42
    python main.py --seed 123       # custom seed
    python main.py --visualize      # also launch baseline in pygame
"""

import argparse
import asyncio
from pathlib import Path

from analysis.runner import BatchRunner, RunConfig, load_experiment_configs
from analysis.plotter import ExperimentPlotter


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ant colony experiments")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--ticks", type=int, default=20_000, help="Max ticks per run")
    parser.add_argument("--epoch", type=int, default=100, help="Epoch size in ticks")
    parser.add_argument("--convergence-window", type=int, default=10, help="Convergence window size in epochs")
    parser.add_argument("--convergence-epsilon", type=float, default=0.15, help="Convergence epsilon value")
    parser.add_argument("--no-show", action="store_true", help="Save plots without showing")
    parser.add_argument("--sequential", action="store_true", help="Run sequentially (debug)")
    parser.add_argument("--visualize", action="store_true", help="Launch baseline sim in pygame")
    parser.add_argument("--config-dir", type=str, default="configs/experiments", help="Select the set of experiment configurations to simulate")
    args = parser.parse_args()

    seed = args.seed

    config_dir = Path(args.config_dir)
    output_dir = Path(f"results/seed_{seed}")

    print(f"═══ Ant Colony Experiment Runner ═══")
    print(f"  Seed:       {seed}")
    print(f"  Max ticks:  {args.ticks}")
    print(f"  Epoch size: {args.epoch}")
    print(f"  Convergence window: {args.convergence_window}")
    print(f"  Convergence epsilon: {args.convergence_epsilon}")
    print(f"  Configs:    {config_dir}")
    print(f"  Output:     {output_dir}")
    print()

    # load configs
    experiments = load_experiment_configs(config_dir, seed=seed)
    print(f"Loaded {len(experiments)} experiment config(s):")
    for e in experiments:
        print(f"  • {e.label}")
    print()

    # run configuration
    run_cfg = RunConfig(
        max_ticks=args.ticks,
        epoch_size=args.epoch,
        convergence_window=args.convergence_window,
        convergence_epsilon=args.convergence_epsilon,
        log_dir=output_dir / "logs",
    )

    runner = BatchRunner(run_config=run_cfg, experiments=experiments)

    # run experiments
    if args.visualize:
        from colony.core.simulation import Simulation
        from rendering.pygame_renderer import PygameRenderer

        print("Running experiments in background …")
        future = runner.run()

        # Launch baseline sim in pygame while experiments run
        baseline_cfg = experiments[0].build_config()
        sim = Simulation()
        sim.load_dict(baseline_cfg)
        sim.build()
        print(f"Launching pygame visualizer (config: {experiments[0].label}) …\n")
        asyncio.run(PygameRenderer(sim).run())

        results = future.get()
    else:
        print("Running experiments …")
        if args.sequential:
            results = runner.run_sequential()
        else:
            results = runner.run_sync()

    # quick console summary
    print(f"\n{'Label':<25} {'Score':>8}  {'Conv@':>6}  {'Ticks':>8}")
    print("-" * 55)
    for r in results:
        conv = str(r.convergence_epoch) if r.convergence_epoch else "—"
        print(f"{r.label:<25} {r.final_score:>8}  {conv:>6}  {r.ticks_run:>8}")
    print()

    # plot
    plotter = ExperimentPlotter(results, output_dir=output_dir)
    plotter.plot_all(show=not args.no_show)


if __name__ == "__main__":
    main()