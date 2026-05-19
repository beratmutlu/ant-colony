# Ant Colony Simulation

This project simulates an ant colony collecting food in a grid world. It is mainly used to run different experiment configurations and compare their results.

**Live demo:** https://beratmutlu.github.io/ant-colony/

## Setup

Use Python 3.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run With Visualization

This opens the pygame visualization for the first experiment configuration.

```bash
python3 main.py --visualize
```

Close the pygame window when you are done.

Controls:

- `Esc`: pause or resume the simulation
- `D`: toggle debug view; pheromones are hidden, blocked cells are marked with a red X
- `F`: show or hide food pheromones
- `N`: show or hide nest pheromones
- `G`: show or hide gradient arrows

Display:

- yellow cell: nest
- green cell: food source
- white ant: searching
- yellow ant: carrying food
- red pheromone: food pheromone
- blue pheromone: nest pheromone
- red X: blocked cell, for example an obstacle or a cell blocked by an event

## Run Batch Experiments

Run the normal experiment set:

```bash
python3 main.py --config-dir configs/experiments --seed 42 --ticks 20000 --epoch 100 --no-show
```

Run the event experiment set:

```bash
python3 main.py --config-dir configs/experiments_with_events --seed 42 --ticks 20000 --epoch 100 --no-show
```

`--no-show` saves the plots without opening plot windows.

## Web Version

For the browser version, use `pygbag==0.9.2`.

```bash
pip install pygbag==0.9.2
cp -R colony rendering web/
python3 -m pygbag web
```

For the most reliable browser experience, use Chrome or Firefox.

## Output

Results are written to:

```text
results/<config-folder>/seed<seed>/<run-id>/
```

Example:

```text
results/experiments/seed42/2026-05-19_20-13-58/
```

Each run directory contains:

- `logs/*.jsonl`: log files for each experiment configuration
- `performance_dashboard.png`: performance overview plot
- `convergence_summary.png`: final score and convergence overview
- `plateau_ranges.png`: plateau overview
- `report.txt`: text summary of the run

## Config File Structure

Experiment files are JSON files. The comments below are only explanations; remove them in real `.json` files.

```jsonc
{
  "label": "example_run",                     // Name used in logs, plots, and reports.
  "comment": "Short experiment description.", // Optional human-readable note.
  "seed": 42,                                 // Random seed for this config.

  "grid": {                                   // Grid size.
    "width": 20,                              // Number of columns.
    "height": 20                              // Number of rows.
  },

  "ants": {                                   // Ant population settings.
    "n": 50,                                  // Number of ants at the start.
    "energy": 150.0,                          // Starting energy per ant.
    "determinism": 70.0                       // Higher value means less random movement.
  },

  "nest_pos": [10, 10],                       // Nest position as [x, y].
  "ph_strength": 50.0,                        // Pheromone strength used by the run.

  "food": {                                   // Food behavior settings.
    "infinite": true,                         // If true, food sources do not run out.
    "pickup_fraction": 0.01,                  // Removed per pickup when food is finite.
    "depletion_threshold": 0.001              // Food below this amount counts as depleted.
  },

  "food_sources": [                           // Food source list.
    {"pos": [2, 2], "amount": 200.0},         // Food position and starting amount.
    {"pos": [18, 18], "amount": 200.0}        // Another food source.
  ],

  "events": [                                 // Optional scheduled changes during a run.
    {
      "tick": 1000,                           // Tick when this event is applied.
      "type": "set_ant_capacity",             // Event type: set_ant_capacity.
      "cells": [[16, 16], [15, 16]],          // Cells affected by the event.
      "value": 0                              // New capacity; 0 makes cells blocked.
    },
    {
      "tick": 2000,                           // Tick when this event is applied.
      "type": "clear_pheromones",             // Event type: clear_pheromones.
      "cells": [[10, 10], [10, 11]]           // Cells where pheromones are cleared.
    }
  ],

  "ant_capacity_overrides": [                 // Optional start-time capacity overrides.
    {
      "value": 0,                             // Capacity to set before the run starts.
      "cells": [[1, 1], [2, 1]]               // Cells affected by the override.
    }
  ],

  "initial_pheromones": [                     // Optional warmstart pheromones.
    {
      "type": "PHEROMONE_FOOD",               // Type: PHEROMONE_FOOD or PHEROMONE_NEST.
      "amount": 50.0,                         // Amount placed on each listed cell.
      "cells": [[6, 6], [7, 7], [8, 8]]       // Cells receiving the pheromone.
    }
  ]
}
```

The optional blocks `events`, `ant_capacity_overrides`, and `initial_pheromones` can be left out when they are not needed.

## Command Line Options

Show all available options:

```bash
python3 main.py --help
```

| Option | Default | Description |
| --- | --- | --- |
| `--seed` | `42` | Random seed for the run. |
| `--ticks` | `20000` | Maximum number of ticks per experiment. |
| `--epoch` | `100` | Number of ticks grouped into one reporting epoch. |
| `--convergence-window` | `10` | Number of epochs used for convergence checks. |
| `--convergence-epsilon` | `0.15` | Sensitivity value for convergence checks. |
| `--no-show` | off | Saves plots without opening plot windows. |
| `--sequential` | off | Runs experiments one after another. Useful for debugging. |
| `--visualize` | off | Opens the pygame visualization for the first loaded experiment. |
| `--config-dir` | `configs/experiments` | Folder containing experiment JSON files. |
| `--run-id` | current timestamp | Custom name for the output folder. |
| `--post-hoc-penalty-scale` | `1.0` | Adjusts post-run plateau detection. |
| `--post-hoc-max-relative-total-drift` | `0.08` | Maximum drift allowed for post-run plateau labeling. |
| `--post-hoc-min-relative-regime-step` | `0.08` | Minimum step size used when separating post-run result phases. |
