from dataclasses import dataclass, field
import statistics


@dataclass
class ConvergenceTracker:
    window: int = 50
    epsilon: float = 0.1
    history: list[int] = field(default_factory=list)
    convergence_tick: int | None = None

    def update(self, tick: int, food_delivered_this_tick: int) -> None:
        self.history.append(food_delivered_this_tick)

        if self.convergence_tick is not None:
            return

        if len(self.history) >= self.window:
            window_data = self.history[-self.window:]
            if statistics.variance(window_data) < self.epsilon and sum(window_data) > 0:
                self.convergence_tick = tick

    @property
    def converged(self) -> bool:
        return self.convergence_tick is not None

    @property
    def stable(self) -> bool:
        if not self.converged or len(self.history) < self.window:
            return False
        window_data = self.history[-self.window:]
        return statistics.variance(window_data) < self.epsilon and sum(window_data) > 0

    def reset(self) -> None:
        self.history.clear()
        self.convergence_tick = None
