from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from colony.core.simulation import Simulation
from colony.types.item_type import ItemType


class PheromoneVisualizer:
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        

    def save_heatmap(self, sim: Simulation, path: Path, title: str) -> None:
        fields = self.snapshot_fields(sim)

        path.parent.mkdir(parents=True, exist_ok=True)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(title, fontsize=13, fontweight="bold")

        self._draw_heatmap(axes[0], fields["food"], "Food pheromone", "Reds")
        self._draw_heatmap(axes[1], fields["nest"], "Nest pheromone", "Blues")
        self._draw_heatmap(axes[2], fields["combined"], "Combined pheromone", "magma")

        world = self.snapshot_world(sim)
        for ax in axes:
            self._mark_world_features(ax, world)

        plt.tight_layout()
        fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

    def save_comparison(self, before: dict, after: dict, event: dict, path: Path, title: str) -> None:        
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = [
            ("food", "Food pheromone", "Reds"),
            ("nest", "Nest pheromone", "Blues"),
            ("combined", "Combined pheromone", "magma")
        ]

        fig = plt.figure(figsize=(12, 13), constrained_layout=True)
        fig.suptitle(title, fontsize=13, fontweight="bold")

        grid = fig.add_gridspec(
            3,
            3,
            width_ratios=[1, 0.06, 1],
            hspace=0.18,
            wspace=0.08
        )
        for row_idx, (key, label, cmap) in enumerate(rows):

            before_ax = fig.add_subplot(grid[row_idx, 0])
            colorbar_ax = fig.add_subplot(grid[row_idx, 1])
            after_ax = fig.add_subplot(grid[row_idx, 2])

            before_values = before["fields"][key]
            after_values = after["fields"][key]
            
            vmax = max(float(np.max(before_values)), float(np.max(after_values)), 1.0)
            
            image = self._draw_heatmap(
                before_ax,
                before_values,
                f"{label} before",
                cmap,
                vmin=0.0,
                vmax=vmax,
                colorbar=False
            )
            self._draw_heatmap(
                after_ax,
                after_values,
                f"{label} after",
                cmap,
                vmin=0.0,
                vmax=vmax,
                colorbar=False
            )

            self._mark_world_features(before_ax, before["world"])
            self._mark_world_features(after_ax, after["world"])
            self._mark_event_footprint(before_ax, event)

            fig.colorbar(image, cax=colorbar_ax)

        fig.savefig(path, dpi=self.dpi, bbox_inches="tight")
        plt.close(fig)

    def snapshot(self, sim: Simulation) -> dict:
        return {
            "fields": self.snapshot_fields(sim),
            "world": self.snapshot_world(sim)
        }
    
    def snapshot_world(self, sim: Simulation) -> dict:
        manager = sim.manager
        if manager is None:
            raise ValueError("Simulation must be built before saving pheromone heatmaps")
        
        grid = manager.grid
        food_cells = []
        blocked_cells = []

        for (x, y), cell in grid.cells.items():
            if cell.items[ItemType.FOOD] > 0:
                food_cells.append((x, y))
            
            if cell.cap_ant <= 0:
                blocked_cells.append((x, y))
        
        return {
            "nest_pos": manager.nest_pos,
            "food_cells": food_cells,
            "blocked_cells": blocked_cells
        }
    
    def snapshot_fields(self, sim: Simulation) -> dict[str, np.ndarray]:
        manager = sim.manager
        if manager is None:
            raise ValueError("Simulation must be built before saving pheromone heatmaps")
        
        grid = manager.grid
        food_ph = np.zeros((grid.height, grid.width))
        nest_ph = np.zeros((grid.height, grid.width))

        for (x, y), cell in grid.cells.items():
            food_ph[y, x] = cell.items[ItemType.PHEROMONE_FOOD]
            nest_ph[y, x] = cell.items[ItemType.PHEROMONE_NEST]

        return {
            "food": food_ph,
            "nest": nest_ph,
            "combined": food_ph + nest_ph,
        }

    def _draw_heatmap(self, ax, values: np.ndarray, title: str, cmap: str, vmin: float | None = None, vmax: float | None = None, colorbar: bool = True):
        image = ax.imshow(values, origin="upper", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_title(title)
        ax.set_xticks([])
        ax.set_yticks([])
        
        if colorbar:
            plt.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

        return image

    def _mark_world_features(self, ax, world: dict) -> None:

        nest_x, nest_y = world["nest_pos"]
        ax.scatter(nest_x, nest_y, marker="*", s=120, c="yellow", edgecolors="black")

        for x, y in world["food_cells"]:
            ax.scatter(x, y, marker="s", s=45, c="lime", edgecolors="black")

        for x, y in world["blocked_cells"]:
            ax.scatter(x, y, marker="x", s=90, c="black", linewidths=3.0)
            ax.scatter(x, y, marker="x", s=60, c="cyan", linewidths=1.8)

    def _mark_event_footprint(self, ax, event: dict) -> None:
        cells = event.get("cells", [])
        if not cells:
            return
        
        xs = [cell[0] for cell in cells]
        ys = [cell[1] for cell in cells]

        ax.scatter(
            xs,
            ys,
            marker="s",
            s=70,
            facecolors="none",
            edgecolors="orange",
            linewidths=1.5
        )