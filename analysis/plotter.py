import json
from pathlib import Path
import statistics


import matplotlib.pyplot as plt

from analysis.experiment import ExperimentResult

def load_logs(log_dir: Path) -> dict[str, list[dict]]:
    logs = {}
    for path in log_dir.glob("*.jsonl"):
        label = path.stem
        with open(path) as file:
            logs[label] = [json.loads(line) for line in file]
    return logs

class Plotter:
    def __init__(self, results: list[ExperimentResult]):
        self.results = results

    def plot(self) -> None:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        self._plot_individual(axes[0])
        self._plot_merged(axes[1])
        plt.tight_layout()
        plt.show()

    def _plot_individual(self, ax) -> None:
        for r in self.results:
            cumulative = self._cumulative(r.score_history)
            ax.plot(cumulative, alpha=0.5, label=r.label)
            if r.convergence_tick:
                ax.axvline(r.convergence_tick, linestyle="--", color="gray", alpha=0.3)

        ax.set_title("Cumulative Score per Seed")
        ax.set_xlabel("Tick")
        ax.set_ylabel("Score")
        ax.legend(fontsize=7)

    def _plot_merged(self, ax) -> None:
        min_len = min(len(r.score_history) for r in self.results)
        trimmed = [r.score_history[:min_len] for r in self.results]

        means = [statistics.mean(tick_vals) for tick_vals in zip(*trimmed)]
        stds = [statistics.stdev(tick_vals) if len(self.results) > 1 else 0 for tick_vals in zip(*trimmed)]

        cumulative_mean = self._cumulative(means)
        cumulative_upper = [m + s for m, s in zip(cumulative_mean, stds)]
        cumulative_lower = [m - s for m, s in zip(cumulative_mean, stds)]

        ticks = list(range(min_len))
        ax.plot(ticks, cumulative_mean, color="blue", label="mean")
        ax.fill_between(ticks, cumulative_lower, cumulative_upper, alpha=0.2, color="blue", label="±1 std")

        conv_tick = [r.convergence_tick for r in self.results if r.convergence_tick]
        if conv_tick:
            avg_conv = statistics.mean(conv_tick)
            ax.axvline(avg_conv, linestyle="--", color="red", label=f"avg convergence@{avg_conv: .0f}")

        ax.set_title("Merged Score (mean ± std")
        ax.set_xlabel("Tick")
        ax.set_ylabel("Cumulative Score")
        ax.legend()

    def plot_summaries(self, log_dir: Path) -> None:
        logs = load_logs(log_dir)
        summaries = {
            label: [e for e in entries if e["event"] == "summary"]
            for label, entries in logs.items()
        }

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))


        for label, entries in summaries.items():
            ticks = [e["tick"] for e in entries]
            ants = [e["ants_alive"] for e in entries]
            axes[0].plot(ticks, ants, alpha=0.6, label=label)

        axes[0].set_title("Ants Alive per Seed")
        axes[0].set_xlabel("Tick")
        axes[0].set_ylabel("Ants Alive")
        axes[0].legend(fontsize=7)


        for label, entries in summaries.items():
            ticks = [e["tick"] for e in entries]
            delivered = [e["delivered_last_window"] for e in entries]
            conv = next((e for e in logs[label] if e["event"] == "convergence"), None)

            axes[1].plot(ticks, delivered, alpha=0.6, label=label)
            if conv:
                axes[1].axvline(conv["convergence_tick"], color="gray", linestyle="--", alpha=0.3)

        axes[1].set_title("Delivered per Window per Seed")
        axes[1].set_xlabel("Tick")
        axes[1].set_ylabel("Food Delivered")
        axes[1].legend(fontsize=7)

        plt.tight_layout()
        plt.show()

    @staticmethod
    def _cumulative(values: list) -> list:
        total = 0
        result = []
        for v in values:
            total += v
            result.append(total)
        return result