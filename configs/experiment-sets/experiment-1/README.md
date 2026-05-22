# Experiment 1: Food Supply Under Different Colony Sizes

Purpose: demonstrate that the colony can establish food supply on a non-trivial grid, while varying the ant population as required by the assignment.

The three simulations use the same 18x18 grid, nest, finite food sources, pheromone strength, ant energy, and static obstacles. Only `ants.n` changes:

- `exp1_colony_12`: small colony, expected to discover and reinforce trails slowly.
- `exp1_colony_24`: medium colony, expected to improve delivery and convergence.
- `exp1_colony_36`: largest colony below the assignment limit of 40 ants, expected to deliver most food but possibly with sublinear efficiency gains because of obstacles and capacity limits.

Run:

```bash
python3 main.py --config-dir configs/experiment-sets/experiment-1 --seed 42 --ticks 15000 --epoch 15 --no-show
```
