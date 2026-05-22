# Experiment 3: Scalability on a Larger World

Purpose: show chances and problems of scalability when the colony has to exploit multiple distant finite food sources on a larger grid.

The three simulations use the same 30x30 grid, nest, four finite food sources, pheromone strength, determinism, and static obstacle corridors. The variants scale ant energy and colony size:

- `exp3_fixed_budget`: 24 ants with energy 180, expected to show whether the Experiment 1-style medium budget still works on the larger map.
- `exp3_energy_scaled`: 24 ants with energy 300, expected to improve survival and source coverage by giving ants more time to explore and return.
- `exp3_colony_energy_scaled`: 36 ants with energy 300, expected to test whether more workers improve throughput or mainly reinforce early successful paths.

Run:

```bash
python3 main.py --config-dir configs/experiment-sets/experiment-3 --seed 42 --ticks 30000 --epoch 100 --no-show
```
