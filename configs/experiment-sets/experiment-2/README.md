# Experiment 2: Warmstart Recovery After Trail Interruption

Purpose: demonstrate that a colony can recover stable food delivery after an established warmstart pheromone trail is interrupted.

The three simulations use the same clean 18x18 grid, nest, infinite food source, ant population, ant energy, determinism, warmstart pheromone trail, and scheduled disturbance. Only `ph_strength` changes:

- `exp2_block_gap_ph30`: weak pheromone reinforcement, expected to recover but with the lowest post-interruption delivery plateau.
- `exp2_block_gap_ph70`: medium pheromone reinforcement, expected to balance delivery performance and robustness after interruption.
- `exp2_block_gap_ph110`: strongest configured run label, using `ph_strength = 100.0`, expected to perform best before interruption but show stronger path dependency after the trail is blocked.

At tick `12000`, the established trail is blocked with `set_ant_capacity = 0` and cleared with `clear_pheromones`. At tick `16000`, the blocked cells are reopened.

Run:

```bash
python3 main.py --config-dir configs/experiment-sets/experiment-2 --seed 42 --ticks 30000 --epoch 100 --no-show
```
