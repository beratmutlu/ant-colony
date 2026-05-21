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
        self._plot_delivery_food_dashboard()
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
        self._panel_deliveries_per_epoch(axes[0, 1])
        self._panel_colony_size(axes[1, 0])
        self._panel_avg_energy(axes[1, 1])

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(
            self.output_dir / "performance_dashboard.png",
            dpi=150, bbox_inches="tight",
        )

    def _plot_delivery_food_dashboard(self) -> None:
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle(
            "Deliveries & Food Amount — Config Comparison",
            fontsize=14, fontweight="bold", y=0.98,
        )
        self._style(axes)

        self._panel_epoch_series(
            axes[0, 0],
            "Deliveries per Epoch",
            "Deliveries",
            lambda r: r.epoch_delivery_history,
        )
        self._panel_epoch_series(
            axes[0, 1],
            "Food Amount per Epoch",
            "Food Amount",
            lambda r: r.epoch_food_amount_history,
        )
        self._panel_epoch_efficiency_series(
            axes[1, 0],
            "Delivery Efficiency per Epoch",
            "Deliveries per Tick",
            lambda r: r.epoch_delivery_history,
        )
        self._panel_epoch_efficiency_series(
            axes[1, 1],
            "Food Amount Efficiency per Epoch",
            "Food Amount per Tick",
            lambda r: r.epoch_food_amount_history,
        )

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fig.savefig(
            self.output_dir / "delivery_food_dashboard.png",
            dpi=150, bbox_inches="tight",
        )

    def _panel_epoch_series(self, ax, title: str, ylabel: str, history_getter) -> None:
        for r in self.results:
            values = history_getter(r)
            epochs = range(1, len(values) + 1)

            ax.plot(epochs, values, color=self._colors[r.label], alpha=0.3, linewidth=0.8)

            if len(values) >= 5:
                kernel = np.ones(5) / 5
                smooth = np.convolve(values, kernel, mode="valid")
                ax.plot(range(3, 3 + len(smooth)), smooth, color=self._colors[r.label], label=r.label, linewidth=1.8)
            else:
                ax.plot(epochs, values, color=self._colors[r.label], label=r.label, linewidth=1.8)

        self._draw_event_markers(ax)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        self._add_event_legend(ax)
    
    def _panel_epoch_efficiency_series(self, ax, title: str, ylabel: str, history_getter) -> None:
        for r in self.results:
            values = np.asarray(history_getter(r), dtype=float)
            if len(values) == 0:
                continue

            epochs = np.arange(1, len(values) + 1)
            efficiency = values / max(r.epoch_size, 1)

            ax.plot(epochs, efficiency, color=self._colors[r.label],
                    alpha=0.3, linewidth=0.8)

            if len(efficiency) >= 5:
                kernel = np.ones(5) / 5
                smooth = np.convolve(efficiency, kernel, mode="valid")
                ax.plot(range(3, 3 + len(smooth)), smooth,
                        color=self._colors[r.label], label=r.label,
                        linewidth=1.8)
            else:
                ax.plot(epochs, efficiency, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)

        self._draw_event_markers(ax)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel(ylabel)
        ax.set_ylim(bottom=0)
        self._add_event_legend(ax)

    def _panel_cumulative_deviation(self, ax) -> None:
        for r in self.results:
            if not r.epoch_delivery_history:
                continue

            cum = np.cumsum(r.epoch_delivery_history)
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
        ax.set_ylabel("Deliveries Ahead/Behind Own Average Pace")
        self._add_event_legend(ax, loc="upper left")

    def _panel_deliveries_per_epoch(self, ax) -> None:
        for r in self.results:
            epochs = range(1, len(r.epoch_delivery_history) + 1)
            ax.plot(epochs, r.epoch_delivery_history, color=self._colors[r.label],
                    alpha=0.3, linewidth=0.8)
            # rolling mean (window=5)
            if len(r.epoch_delivery_history) >= 5:
                kernel = np.ones(5) / 5
                smooth = np.convolve(r.epoch_delivery_history, kernel, mode="valid")
                ax.plot(range(3, 3 + len(smooth)), smooth,
                        color=self._colors[r.label], label=r.label,
                        linewidth=1.8)
            else:
                ax.plot(epochs, r.epoch_delivery_history, color=self._colors[r.label],
                        label=r.label, linewidth=1.8)
        self._draw_event_markers(ax)
        ax.set_title("Deliveries per Epoch (smoothed)", fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Deliveries")
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

    def _plot_plateau_ranges(self) -> None:
        fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
        self._style(axes)
        
        online_ax, pelt_ax, post_hoc_ax = axes

        labels = [r.label for r in self.results]
        y_positions = range(len(self.results))


        max_epoch = max((r.epochs_run for r in self.results), default=1)

        self._draw_ranges_panel(
            online_ax,
            lambda r: r.plateau_ranges,
            "Online Stable Plateau Ranges",
            labels,
            y_positions,
            max_epoch
        )

        self._draw_ranges_panel(
            pelt_ax,
            lambda r: [(s.start_epoch, s.end_epoch) for s in r.post_hoc_convergence.segments],
            "Raw PELT Regime Segments",
            labels,
            y_positions,
            max_epoch,
            label_by_range=self._pelt_segment_label
        )

        self._draw_ranges_panel(
            post_hoc_ax,
            lambda r: r.post_hoc_convergence.plateau_ranges,
            "Post-Hoc Interpreted Plateaus",
            labels,
            y_positions,
            max_epoch
        )

        post_hoc_ax.set_xlabel("Epoch")

        plt.tight_layout()
        fig.savefig(
            self.output_dir / "plateau_ranges.png",
            dpi=150, bbox_inches="tight",
        )

    def _draw_ranges_panel(self, ax, ranges_by_result, title: str, labels, y_positions, max_epoch: int, label_by_range=None) -> None:
        for y, r in zip(y_positions, self.results):
            color = self._colors[r.label]
            for start, end in ranges_by_result(r):
                label = f"{start}-{end}"
                if label_by_range:
                    label = label_by_range(r, start, end)
                width = max(end - start, 1)
                ax.broken_barh(
                    [(start, width)],
                    (y - 0.35, 0.7),
                    facecolors=color,
                    edgecolors="black",
                    alpha=0.65,
                    linewidth=0.7
                )
                if width >= 40:
                    ax.text(
                        start + width / 2,
                        y,
                        label,
                        ha="center",
                        va="center",
                        fontsize=8,
                        color="white"
                    )

        self._draw_event_markers(ax)
        ax.set_xlim(0, max_epoch)
        ax.set_yticks(list(y_positions))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_title(title, fontsize=12, fontweight="bold")
        self._add_event_legend(ax, loc="upper right")

    def _pelt_segment_label(self, result: ExperimentResult, start: int, end: int) -> str:
        for segment in result.post_hoc_convergence.segments:
            if segment.start_epoch == start and segment.end_epoch == end:
                return (
                    f"{start}-{end}\nm={segment.mean:.0f} d={segment.relative_total_drift:.0%}"
                )
        return f"{start}-{end}"

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
        lines.append("--- Online Plateau Ranges ---")
        for r in self.results:
            if r.plateau_ranges:
                ranges = ", ".join(f"{start}-{end}" for start, end in r.plateau_ranges)
            else:
                ranges = "N/A"
            lines.append(f"{r.label:<25} {ranges}")

        lines.append("")
        lines.append("--- Post-Hoc Plateau Ranges ---")
        for r in self.results:
            post_hoc = r.post_hoc_convergence
            conv = post_hoc.convergence_epoch if post_hoc.convergence_epoch else "N/A"

            if post_hoc.plateau_ranges:
                ranges = ", ".join(f"{start}-{end}" for start, end in post_hoc.plateau_ranges)
            else:
                ranges = "N/A"

            lines.append(f"{r.label:<25} conv@={str(conv):>5}  {ranges}")

        lines.append("")
        lines.append("--- Raw PELT Regime Segments ---")
        for r in self.results:
            post_hoc = r.post_hoc_convergence
            lines.append(f"\n  [{r.label}]")
            if not post_hoc.segments:
                lines.append("    N/A")
                continue

            hdr = (
                f"    {'Epochs':<11} {'Len':>5} {'Mean':>8} {'Std':>8} "
                f"{'Slope':>9} {'Drift':>8} {'Plateau':>8}"
            )
            lines.append(hdr)
            lines.append("    " + "-" * (len(hdr) - 4))

            plateau_set = set(post_hoc.plateau_ranges)
            for segment in post_hoc.segments:
                epoch_range = f"{segment.start_epoch}-{segment.end_epoch}"
                plateau = "yes" if (segment.start_epoch, segment.end_epoch) in plateau_set else "no"
                lines.append(
                    f"    {epoch_range:<11} "
                    f"{segment.length:>5} "
                    f"{segment.mean:>8.2f} "
                    f"{segment.std:>8.2f} "
                    f"{segment.slope:>9.3f} "
                    f"{segment.relative_total_drift:>7.1%} "
                    f"{plateau:>8}"
                )

        lines.append("")
        lines.append("--- Epoch Delivery Statistics ---")
        hdr2 = f"{'Config':<25} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8}"
        lines.append(hdr2)
        lines.append("-" * len(hdr2))

        for r in self.results:
            values = r.epoch_delivery_history
            if values:
                m = f"{statistics.mean(values):.1f}"
                s = (f"{statistics.stdev(values):.1f}" if len(values) > 1 else "0.0")
                lines.append(
                    f"{r.label:<25} {m:>8} {s:>8} "
                    f"{min(values):>8} {max(values):>8}"
                )

        lines.append("")
        lines.append("--- Epoch Food Amount Statistics ---")
        lines.append(hdr2)
        lines.append("-" * len(hdr2))

        for r in self.results:
            values = r.epoch_food_amount_history
            if values:
                m = f"{statistics.mean(values):.4f}"
                s = f"{statistics.stdev(values):.4f}" if len(values) > 1 else "0.0000"
                lines.append(
                    f"{r.label:<25} {m:>8} {s:>8} "
                    f"{min(values):>8.4f} {max(values):>8.4f}"
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

    def _draw_event_markers(self, ax, *, scale: str = "epoch") -> None:
        for result in self.results:
            for event in result.config.get("events", []):
                tick = event.get("tick")
                if tick is None:
                    continue
                
                x = tick if scale == "tick" else self._event_epoch(result, tick)

                ax.axvline(
                    x,
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
