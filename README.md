# Ant Colony Simulation

This project simulates an ant colony collecting food in a grid world. It can run
single visualized simulations, batch experiment sets, convergence analysis, event
disturbance tests, and post-run plotting.

**Live demo:** https://beratmutlu.github.io/ant-colony/

## Project Layout

- `colony/`: simulation model, grid/cell state, ant behavior, and item types
- `rendering/`: pygame renderer for interactive visualization
- `analysis/`: batch runner, JSONL logging, convergence detection, plots, and
  pheromone snapshot generation
- `configs/experiments/`: small baseline comparison set
- `configs/experiments_with_events/`: event disturbance configs
- `configs/experiment-sets/`: assignment-oriented experiment groups
- `docs/`: diagrams and generated documentation assets
- `web/`: pygbag entry point for the browser build
- `results/`: generated run outputs

## Setup

Use Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The project dependencies are `pygame`, `matplotlib`, `numpy`, and `ruptures`.

## Run With Visualization

This opens the pygame visualization for the first loaded configuration:

```bash
python3 main.py --visualize
```

You can also visualize a different loaded config by zero-based index:

```bash
python3 main.py --config-dir configs/experiments --visualize 2 --no-show
```

When visualization is enabled, the selected simulation runs in pygame while the
batch experiments run in the background. Close the pygame window when you are
done.

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

The default config directory is `configs/experiments`.

```bash
python3 main.py --seed 42 --ticks 20000 --epoch 100 --no-show
```

Run the explicit baseline comparison set:

```bash
python3 main.py --config-dir configs/experiments --seed 42 --ticks 20000 --epoch 100 --no-show
```

Run the event disturbance set:

```bash
python3 main.py --config-dir configs/experiments_with_events --seed 42 --ticks 20000 --epoch 100 --no-show
```

Run the assignment experiment sets:

```bash
python3 main.py --config-dir configs/experiment-sets/experiment-1 --seed 42 --ticks 15000 --epoch 15 --no-show
python3 main.py --config-dir configs/experiment-sets/experiment-2 --seed 42 --ticks 30000 --epoch 100 --no-show
python3 main.py --config-dir configs/experiment-sets/experiment-3 --seed 42 --ticks 30000 --epoch 100 --no-show
```

`--no-show` saves the plots without opening matplotlib windows. Add `--run-id
output` if you want a stable output directory name instead of a timestamp.

## Experiment Sets

`configs/experiments/` contains the original small comparison group:

- `baseline`
- `low_det_30`
- `high_det_90`
- `strong_ph_100`
- `large_colony_80`

`configs/experiment-sets/experiment-1/` varies colony size on the same finite-food
18x18 map:

- `exp1_colony_12`
- `exp1_colony_24`
- `exp1_colony_36`

`configs/experiment-sets/experiment-2/` tests warmstarted trail recovery after an
interruption at tick `12000` and reopening at tick `16000`:

- `exp2_block_gap_ph30`
- `exp2_block_gap_ph70`
- `exp2_block_gap_ph110`

`configs/experiment-sets/experiment-3/` tests scalability on a larger 30x30 world:

- `exp3_fixed_budget`
- `exp3_energy_scaled`
- `exp3_colony_energy_scaled`

The event and assignment experiment folders also have short `README.md` files.

## Web Version

For the browser version, use `pygbag==0.9.2`. `pygbag` is not part of the normal
runtime requirements, so install it separately when building the web version.

```bash
pip install pygbag==0.9.2
cp -R colony rendering web/
python3 -m pygbag web
```

The browser entry point is `web/main.py` and currently uses an embedded demo
configuration. For the most reliable browser experience, use Chrome or Firefox.

## Config File Structure

Experiment files are JSON files. The comments below are only explanations; remove
them in real `.json` files.

```jsonc
{
  "label": "example_run",                     // Name used in logs, plots, reports, and snapshot folders.
  "comment": "Short experiment description.", // Optional note, ignored by the simulation.
  "hypothesis": "Expected behavior.",         // Optional note, ignored by the simulation.
  "seed": 42,                                 // Overridden by the CLI --seed value when loaded by main.py.

  "grid": {                                   // Grid size.
    "width": 20,                              // Number of columns.
    "height": 20                              // Number of rows.
  },

  "ants": {                                   // Ant population settings.
    "n": 50,                                  // Number of ants at the start.
    "energy": 150.0,                          // Starting energy per ant; pickups and drops reset energy.
    "determinism": 70.0                       // Higher value means stronger pheromone-following behavior.
  },

  "nest_pos": [10, 10],                       // Nest position as [x, y].
  "ph_strength": 50.0,                        // Pheromone amount deposited on movement, scaled by route length.

  "food": {                                   // Food behavior settings.
    "infinite": false,                        // If true, food sources are not depleted.
    "pickup_fraction": 0.01,                  // Fraction removed from finite food on each pickup.
    "depletion_threshold": 0.001              // Food below this amount is removed and logged as depleted.
  },

  "food_sources": [                           // Food source list.
    {"pos": [2, 2], "amount": 200.0},
    {"pos": [18, 18], "amount": 200.0}
  ],

  "events": [                                 // Optional scheduled changes during a run.
    {
      "tick": 1000,
      "type": "set_ant_capacity",             // Changes cell capacity; value 0 blocks cells.
      "cells": [[16, 16], [15, 16]],
      "value": 0
    },
    {
      "tick": 2000,
      "type": "clear_pheromones",             // Clears food and nest pheromones on listed cells.
      "cells": [[10, 10], [10, 11]]
    }
  ],

  "ant_capacity_overrides": [                 // Optional start-time capacity overrides.
    {
      "value": 0,
      "cells": [[1, 1], [2, 1]]
    }
  ],

  "initial_pheromones": [                     // Optional warmstart pheromones.
    {
      "type": "PHEROMONE_FOOD",               // Type: PHEROMONE_FOOD or PHEROMONE_NEST.
      "amount": 50.0,
      "cells": [[6, 6], [7, 7], [8, 8]]
    }
  ]
}
```

The optional blocks `food`, `events`, `ant_capacity_overrides`, and
`initial_pheromones` can be left out when they are not needed. `label`, `comment`,
and `hypothesis` are useful metadata; only `label` is consumed by the batch loader.

## Output

Results are written to:

```text
results/<config-directory-name>/seed<seed>/<run-id>/
```

Examples:

```text
results/experiments/seed42/2026-05-19_20-13-58/
results/experiment-1/seed42/output/
```

Each run directory contains:

- `logs/*.jsonl`: one JSONL log per experiment configuration
- `snapshots/final/<config-label>/final_tick_<tick>.png`: final pheromone heatmaps
- `snapshots/events/<config-label>/*.png`: before/after event comparison heatmaps
- `snapshots/depletions/<config-label>/*.png`: heatmaps saved when finite food sources deplete
- `performance_dashboard.png`: score trend, deliveries, colony size, and energy plots
- `delivery_food_dashboard.png`: deliveries, food amount, and per-tick efficiency plots
- `plateau_ranges.png`: online plateau, raw PELT segments, and post-hoc plateau ranges
- `report.txt`: text summary with scores, convergence, plateau ranges, statistics, and config parameters

Event comparison snapshots are taken before the event and after a configured delay.
The current delays are `200` ticks for `clear_pheromones` and `1000` ticks for
`set_ant_capacity`. Comparison images use one shared color scale per row, so trail
strength before and after the event can be compared directly.

Example event output:

```text
results/experiment-2/seed42/output/snapshots/events/exp2_block_gap_ph70/
  tick_12000_clear_pheromones_compare_after_200.png
  tick_12000_set_ant_capacity_compare_after_1000.png
  tick_16000_set_ant_capacity_compare_after_1000.png
```

Final heatmaps show food pheromone, nest pheromone, and the combined pheromone
field. Yellow stars mark nests, green squares mark remaining food, and cyan/black X
markers show blocked cells.

For finite-food configs, both delivery count and delivered food amount are useful.
For infinite-food configs, delivery count is the main performance score.

## Command Line Options

Show all available options:

```bash
python3 main.py --help
```

| Option | Default | Description |
| --- | --- | --- |
| `--seed` | `42` | Random seed applied to every loaded config. |
| `--ticks` | `20000` | Maximum number of ticks per experiment. |
| `--epoch` | `100` | Number of ticks grouped into one reporting epoch. |
| `--convergence-window` | `10` | Number of epochs used by convergence checks. |
| `--convergence-epsilon` | `0.15` | Sensitivity value for online convergence checks. |
| `--no-show` | off | Saves plots without opening matplotlib windows. |
| `--sequential` | off | Runs experiments one after another. Useful for debugging. |
| `--visualize [INDEX]` | off | Opens pygame for the selected loaded config. With no index, uses config `0`. |
| `--config-dir` | `configs/experiments` | Folder containing experiment JSON files. |
| `--run-id` | current timestamp | Custom name for the output folder. |
| `--post-hoc-penalty-scale` | `1.0` | PELT penalty scale for post-hoc regime detection. |
| `--post-hoc-max-relative-total-drift` | `0.08` | Maximum drift allowed for post-hoc plateau labeling. |
| `--post-hoc-min-relative-regime-step` | `0.08` | Minimum mean step used when rejecting stair-step regimes. |
