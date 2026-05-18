import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

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
        self._plot_plateau_ranges()
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

        self._panel_cumulative_deviation(axes[0, 0])
        self._panel_food_per_epoch(axes[0, 1])
        self._panel_colony_size(axes[1, 0])
        self._panel_avg_energy(axes[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(
            self.output_dir / "performance_dashboard.png",
            dpi=150, bbox_inches="tight",
        )

    def _panel_cumulative_deviation(self, ax) -> None:
        for r in self.results:
            if not r.epoch_history:
                continue

            cum = np.cumsum(r.epoch_history)
            epochs = np.arange(1, len(cum) + 1)
            expected = epochs * (cum[-1] / len(cum))
            deviation = cum - expected

            ax.plot(epochs, deviation, color=self._colors[r.label],
                    label=r.label, linewidth=1.8)
            if r.convergence_epoch:
                ax.axvline(r.convergence_epoch, color=self._colors[r.label],
                           linestyle="--", alpha=0.4)
        ax.axhline(0, color="black", linewidth=1.1, alpha=0.75)
        self._draw_event_markers(ax)
        ax.set_title("Deviation From Average Cumulative Trend", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Food Ahead/Behind Own Average Pace")
        self._add_event_legend(ax, loc="upper left")

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
        self._draw_event_markers(ax)
        ax.set_title("Food per Epoch (smoothed)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Food Delivered")
        self._add_event_legend(ax)

    def _panel_colony_size(self, ax) -> None:
        for r in self.results:
            if r.ants_alive_history:
                ax.plot(range(1, len(r.ants_alive_history) + 1),
                        r.ants_alive_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        self._draw_event_markers(ax)
        ax.set_title("Colony Size", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Ants Alive")
        self._add_event_legend(ax)

    def _panel_avg_energy(self, ax) -> None:
        for r in self.results:
            if r.avg_energy_history:
                ax.plot(range(1, len(r.avg_energy_history) + 1),
                        r.avg_energy_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        self._draw_event_markers(ax)
        ax.set_title("Average Ant Energy", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Energy")
        self._add_event_legend(ax)

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

    def _plot_plateau_ranges(self) -> None:
        fig, ax = plt.subplots(figsize=(16, 4))
        self._style(ax)

        labels = [r.label for r in self.results]
        y_positions = range(len(self.results))

        for y, r in zip(y_positions, self.results):
            color = self._colors[r.label]
            for start, end in r.plateau_ranges:
                width = max(end - start, 1)
                ax.broken_barh(
                    [(start, width)],
                    (y - 0.35, 0.7),
                    facecolors=color,
                    edgecolors="black",
                    alpha=0.65,
                    linewidth=0.7,
                )
                ax.text(
                    start + width / 2,
                    y,
                    f"{start}-{end}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="white",
                )

        max_epoch = max((r.epochs_run for r in self.results), default=1)
        self._draw_event_markers(ax)
        ax.set_xlim(0, max_epoch)
        ax.set_yticks(list(y_positions))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Epoch")
        ax.set_title("Detected Stable Plateau Ranges", fontsize=12, fontweight="bold")
        self._add_event_legend(ax, loc="upper right")

        plt.tight_layout()
        fig.savefig(
            self.output_dir / "plateau_ranges.png",
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
        lines.append("--- Detected Plateau Ranges ---")
        for r in self.results:
            if r.plateau_ranges:
                ranges = ", ".join(f"{start}-{end}" for start, end in r.plateau_ranges)
            else:
                ranges = "N/A"
            lines.append(f"{r.label:<25} {ranges}")

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

    def _shade_plateau_ranges(self, ax, result: ExperimentResult) -> None:
        color = self._colors[result.label]
        for start, end in result.plateau_ranges:
            ax.axvspan(start, end, color=color, alpha=0.06, linewidth=0)

    def _draw_event_markers(self, ax) -> None:
        for result in self.results:
            for event in result.config.get("events", []):
                tick = event.get("tick")
                if tick is None:
                    continue

                epoch = self._event_epoch(result, tick)

                ax.axvline(
                    epoch,
                    color=self._colors[result.label],
                    linestyle=self._event_line_style(event),
                    linewidth=1.4,
                    alpha=0.75,
                )

    def _event_epoch(self, result: ExperimentResult, tick: int) -> float:
        epoch_size = result.epoch_size
        if epoch_size <= 0 and result.epochs_run > 0:
            epoch_size = max(result.ticks_run / result.epochs_run, 1)
        return tick / max(epoch_size, 1)

    def _event_line_style(self, event: dict) -> str:
        event_type = event.get("type")
        if event_type == "set_ant_capacity":
            return "--"
        if event_type == "clear_pheromones":
            return ":"
        return "-."

    def _add_event_legend(self, ax, loc: str | None = None) -> None:
        handles, labels = ax.get_legend_handles_labels()

        if not self._has_events():
            if handles:
                ax.legend(handles, labels, fontsize=8, loc=loc)
            return

        event_handles = [
            Line2D([0], [0], color="black", linestyle="--", linewidth=1.4),
            Line2D([0], [0], color="black", linestyle=":", linewidth=1.4),
        ]
        event_labels = ["-- set_ant_capacity", ": clear_pheromones"]

        existing = set(labels)
        for handle, label in zip(event_handles, event_labels):
            if label not in existing:
                handles.append(handle)
                labels.append(label)

        ax.legend(handles, labels, fontsize=8, loc=loc)

    def _has_events(self) -> bool:
        return any(r.config.get("events") for r in self.results)
