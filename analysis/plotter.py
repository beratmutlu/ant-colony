import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from analysis.experiment import ExperimentResult


# helpers
def load_logs(log_dir: Path) -> dict[str, list[dict]]:
    logs = {}
    for path in log_dir.glob("*.jsonl"):
        label = path.stem
        with open(path) as file:
            logs[label] = [json.loads(line) for line in file]
    return logs


# plotter
_PALETTE = [
    "#1976D2",  # blue
    "#E64A19",  # deep orange
    "#388E3C",  # green
    "#7B1FA2",  # purple
    "#F57C00",  # orange
    "#0097A7",  # cyan
    "#C2185B",  # pink
    "#5D4037",  # brown
]

class ExperimentPlotter:
    def __init__(
        self,
        results: list[ExperimentResult],
        output_dir: Path = Path("results"),
    ):
        self.results = results
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._colors = {
            r.label: _PALETTE[i % len(_PALETTE)]
            for i, r in enumerate(results)
        }

    # public API

    def plot_all(self, show: bool = True) -> None:
        """Generate all comparison plots, save PNGs and a text report."""
        self._plot_performance_dashboard()
        self._plot_convergence_summary()
        self._write_text_report()
        if show:
            plt.show()

    # performance dashboard (2×2)
    def _plot_performance_dashboard(self) -> None:
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(
            "Performance Dashboard — Config Comparison",
            fontsize=14, fontweight="bold", y=0.98,
        )
        self._style(axes)

        self._panel_cumulative_score(axes[0, 0])
        self._panel_food_per_epoch(axes[0, 1])
        self._panel_colony_size(axes[1, 0])
        self._panel_avg_energy(axes[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(
            self.output_dir / "performance_dashboard.png",
            dpi=150, bbox_inches="tight",
        )

    def _panel_cumulative_score(self, ax) -> None:
        for r in self.results:
            cum = list(np.cumsum(r.epoch_history))
            epochs = range(1, len(cum) + 1)
            ax.plot(epochs, cum, color=self._colors[r.label],
                    label=r.label, linewidth=1.8)
            if r.convergence_epoch:
                ax.axvline(r.convergence_epoch, color=self._colors[r.label],
                           linestyle="--", alpha=0.4)
        ax.set_title("Cumulative Score", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Total Food Delivered")
        ax.legend(fontsize=8, loc="upper left")

    def _panel_food_per_epoch(self, ax) -> None:
        for r in self.results:
            epochs = range(1, len(r.epoch_history) + 1)
            ax.plot(epochs, r.epoch_history, color=self._colors[r.label],
                    alpha=0.3, linewidth=0.8)
            # rolling mean (window=5)
            if len(r.epoch_history) >= 5:
                kernel = np.ones(5) / 5
                smooth = np.convolve(r.epoch_history, kernel, mode="valid")
                ax.plot(range(3, 3 + len(smooth)), smooth,
                        color=self._colors[r.label], label=r.label,
                        linewidth=1.8)
            else:
                ax.plot(epochs, r.epoch_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        ax.set_title("Food per Epoch (smoothed)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Food Delivered")
        ax.legend(fontsize=8)

    def _panel_colony_size(self, ax) -> None:
        for r in self.results:
            if r.ants_alive_history:
                ax.plot(range(1, len(r.ants_alive_history) + 1),
                        r.ants_alive_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        ax.set_title("Colony Size", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Ants Alive")
        ax.legend(fontsize=8)

    def _panel_avg_energy(self, ax) -> None:
        for r in self.results:
            if r.avg_energy_history:
                ax.plot(range(1, len(r.avg_energy_history) + 1),
                        r.avg_energy_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        ax.set_title("Average Ant Energy", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Energy")
        ax.legend(fontsize=8)

    # convergence / summary bars (1×3)
    def _plot_convergence_summary(self) -> None:
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle(
            "Convergence & Final Results",
            fontsize=14, fontweight="bold", y=1.02,
        )
        self._style(axes)

        labels = [r.label for r in self.results]
        colors = [self._colors[l] for l in labels]
        x = range(len(labels))

        # bar 1: convergence epoch
        ax = axes[0]
        conv = [
            r.convergence_epoch if r.convergence_epoch else r.epochs_run
            for r in self.results
        ]
        did_converge = [r.convergence_epoch is not None for r in self.results]
        bars = ax.bar(x, conv, color=colors, edgecolor="black", linewidth=0.8)
        for bar, ok, val in zip(bars, did_converge, conv):
            if not ok:
                bar.set_hatch("//")
            sym = "✓" if ok else "✗"
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{sym} {val}", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_title("Convergence Epoch", fontsize=11, fontweight="bold")
        ax.set_ylabel("Epoch")

        # bar 2: final score
        ax = axes[1]
        scores = [r.final_score for r in self.results]
        bars = ax.bar(x, scores, color=colors, edgecolor="black", linewidth=0.8)
        for bar, val in zip(bars, scores):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    str(val), ha="center", va="bottom",
                    fontsize=9, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_title("Final Score", fontsize=11, fontweight="bold")
        ax.set_ylabel("Total Food Delivered")

        # bar 3: efficiency
        ax = axes[2]
        eff = [r.final_score / max(r.ticks_run, 1) for r in self.results]
        bars = ax.bar(x, eff, color=colors, edgecolor="black", linewidth=0.8)
        for bar, val in zip(bars, eff):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.001,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=8)
        ax.set_title("Efficiency (Score / Tick)", fontsize=11, fontweight="bold")
        ax.set_ylabel("Food per Tick")

        plt.tight_layout()
        fig.savefig(
            self.output_dir / "convergence_summary.png",
            dpi=150, bbox_inches="tight",
        )

    # text report
    def _write_text_report(self) -> None:
        lines: list[str] = []
        sep = "=" * 80
        lines.append(sep)
        lines.append("EXPERIMENT COMPARISON REPORT")
        lines.append(sep)
        lines.append("")

        seed = self.results[0].config.get("seed", "?") if self.results else "?"
        lines.append(f"Seed:            {seed}")
        lines.append(f"Configurations:  {len(self.results)}")
        lines.append("")

        # summary table
        hdr = (f"{'Config':<25} {'Score':>8} {'Ticks':>8} {'Epochs':>8} "
               f"{'Conv@':>8} {'Eff':>10} {'Ants':>6}")
        lines.append(hdr)
        lines.append("-" * len(hdr))

        for r in self.results:
            conv = str(r.convergence_epoch) if r.convergence_epoch else "N/A"
            eff = f"{r.final_score / max(r.ticks_run, 1):.4f}"
            ants = str(r.ants_alive_history[-1]) if r.ants_alive_history else "?"
            lines.append(
                f"{r.label:<25} {r.final_score:>8} {r.ticks_run:>8} "
                f"{r.epochs_run:>8} {conv:>8} {eff:>10} {ants:>6}"
            )

        lines.append("")
        lines.append("--- Epoch Food Statistics ---")
        hdr2 = f"{'Config':<25} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}"
        lines.append(hdr2)
        lines.append("-" * len(hdr2))

        for r in self.results:
            if r.epoch_history:
                m = f"{statistics.mean(r.epoch_history):.1f}"
                s = (f"{statistics.stdev(r.epoch_history):.1f}"
                     if len(r.epoch_history) > 1 else "0.0")
                lines.append(
                    f"{r.label:<25} {m:>8} {s:>8} "
                    f"{min(r.epoch_history):>8} {max(r.epoch_history):>8}"
                )

        lines.append("")
        lines.append("--- Configuration Parameters ---")
        for r in self.results:
            a = r.config.get("ants", {})
            g = r.config.get("grid", {})
            lines.append(f"\n  [{r.label}]")
            lines.append(f"    ants.n           = {a.get('n', '?')}")
            lines.append(f"    ants.energy       = {a.get('energy', '?')}")
            lines.append(f"    ants.determinism  = {a.get('determinism', '?')}")
            lines.append(f"    ph_strength      = {r.config.get('ph_strength', '?')}")
            lines.append(f"    grid             = {g.get('width', '?')}x{g.get('height', '?')}")
            lines.append(f"    food_sources     = {len(r.config.get('food_sources', []))}")

        report = "\n".join(lines)
        path = self.output_dir / "report.txt"
        path.write_text(report)
        print(report)
        print(f"\n→ Report saved to {path}")
        print(f"→ Figures saved to {self.output_dir}/")

    # styling helper
    @staticmethod
    def _style(axes) -> None:
        flat = axes.flat if hasattr(axes, "flat") else [axes]
        for ax in flat:
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.tick_params(labelsize=9)