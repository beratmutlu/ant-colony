"""
Usage:
    python main.py                  # seed 42
    python main.py --seed 123       # custom seed
    python main.py --visualize      # also launch first config in pygame
    python main.py --visualize 2    # launch third loaded config in pygame
"""

import argparse
import asyncio
from pathlib import Path
from datetime import datetime

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
    parser.add_argument(
        "--visualize",
        nargs="?",
        const=0,
        default=None,
        type=int,
        metavar="INDEX",
        help="Launch selected loaded config in pygame by zero-based index (default: 0 when flag is present)"
    )
    parser.add_argument("--config-dir", type=str, default="configs/experiments", help="Select the set of experiment configurations to simulate")
    parser.add_argument("--run-id", type=str, default=None, help="Optional output run id")
    parser.add_argument("--post-hoc-penalty-scale", type=float, default=1.0, help="PELT penalty scale for post-hoc regime detection")
    parser.add_argument("--post-hoc-max-relative-total-drift", type=float, default=0.08, help="Max relative total drift for post-hoc plateau labeling")
    parser.add_argument("--post-hoc-min-relative-regime-step", type=float, default=0.08, help="Min relative mean step for rejecting stair-step regimes")

    args = parser.parse_args()

    seed = args.seed

    config_dir = Path(args.config_dir)
    run_id = args.run_id or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = Path("results") / config_dir.name / f"seed{seed}" / run_id

    print(f"═══ Ant Colony Experiment Runner ═══")
    print(f"  Seed:       {seed}")
    print(f"  Max ticks:  {args.ticks}")
    print(f"  Epoch size: {args.epoch}")
    print(f"  Convergence window: {args.convergence_window}")
    print(f"  Convergence epsilon: {args.convergence_epsilon}")
    print(f"  Post-hoc penalty scale: {args.post_hoc_penalty_scale}")
    print(f"  Post-hoc max drift:     {args.post_hoc_max_relative_total_drift}")
    print(f"  Post-hoc stair step:    {args.post_hoc_min_relative_regime_step}")
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
        snapshot_dir=output_dir / "snapshots",
        post_hoc_penalty_scale=args.post_hoc_penalty_scale,
        post_hoc_max_relative_total_drift=args.post_hoc_max_relative_total_drift,
        post_hoc_min_relative_regime_step=args.post_hoc_min_relative_regime_step
    )

    runner = BatchRunner(run_config=run_cfg, experiments=experiments)

    # run experiments
    if args.visualize is not None:
        if args.visualize < 0 or args.visualize >= len(experiments):
            raise SystemExit(
                f"--visualize index {args.visualize} is out of range "
                f"for {len(experiments)} loaded config(s)"
            )

        from colony.core.simulation import Simulation
        from rendering.pygame_renderer import PygameRenderer

        print("Running experiments in background …")
        future = runner.run()

        # Launch selected sim in pygame while experiments run.
        selected_exp = experiments[args.visualize]
        selected_cfg = selected_exp.build_config()
        sim = Simulation()
        sim.load_dict(selected_cfg)
        sim.build()
        print(f"Launching pygame visualizer (config: {selected_exp.label}) …\n")
        asyncio.run(PygameRenderer(sim).run())

        results = future.get()
    else:
        print("Running experiments …")
        if args.sequential:
            results = runner.run_sequential()
        else:
            results = runner.run_sync()

    # quick console summary
    print(f"\n{'Label':<25} {'Deliveries':>10} {'Food':>10} {'Conv@':>6} {'Ticks':>8}")
    print("-" * 68)
    for r in results:
        conv = str(r.convergence_epoch) if r.convergence_epoch else "—"
        print(
            f"{r.label:<25} {r.final_score:>10} "
            f"{r.final_food_amount:>10.4f} {conv:>6} {r.ticks_run:>8}"
        )
    print()

    # plot
    plotter = ExperimentPlotter(results, output_dir=output_dir)
    plotter.plot_all(show=not args.no_show)


if __name__ == "__main__":
    main()
